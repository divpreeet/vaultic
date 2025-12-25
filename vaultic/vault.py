import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from .stego import extract, embed

@dataclass
class VaultPaths:
    dir: Path
    vault_file: Path
    salt_file: Path

# storing vault data and salt for encryption and key derivation
def default() -> VaultPaths:
    base = Path.home() / ".vaultic"
    return VaultPaths(
        dir=base,
        vault_file=base / "vault.png",
        salt_file=base / "salt.bin",
    )

# create or load salt
def load_salt(path: Path) -> bytes:
    if path.exists():
        return path.read_bytes()
    salt = os.urandom(16)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(salt)
    return salt

#32 bytesx key
def derive_key(master_key: str, salt:bytes) -> bytes:
    kdf = Scrypt(
        salt=salt,
        length=32,
        n=2**14,
        r=8,
        p=1
    )
    return kdf.derive(master_key.encode("utf-8"))

def encrypt_json(data: Dict, key:bytes) -> bytes:
    aes=AESGCM(key)
    nonce=os.urandom(12)
    plaintext=json.dumps(data).encode("utf-8")
    ciphertext=aes.encrypt(nonce, plaintext, associated_data=None)
    return nonce +ciphertext


def decrypt_json(blob: bytes, key: bytes) -> Dict:
    if len(blob) < 13:
        raise ValueError("vault data is too small")
    nonce, ciphertext = blob[:12], blob[12:]
    aes=AESGCM(key)
    plaintext=aes.decrypt(nonce, ciphertext, associated_data=None)
    return json.loads(plaintext.decode("utf-8"))


# encrypted vault stored in single file
class Vault:

    def __init__(self, master_key: str, paths: Optional[VaultPaths] = None):
        self.paths = paths or default()
        self.paths.dir.mkdir(parents=True, exist_ok=True)

        salt = load_salt(self.paths.salt_file)
        self.key = derive_key(master_key, salt)

    def create_meme(self, cover_path: str | Path):
        if self.paths.vault_file.exists():
            raise FileExistsError(f"vault already exists at {self.paths.vault_file}, to overwrite this vault, manually delete the image at the provided path")
        data = {"entries": {}}
        blob = encrypt_json(data, self.key)
        embed(cover_path, blob, self.paths.vault_file)

    def _read(self) -> Dict:
        if not self.paths.vault_file.exists():
            raise FileNotFoundError("vailt.png was not found")
        blob = extract(self.paths.vault_file)
        if blob is None:
            raise ValueError("vault.png has no embedded vault data")
       
        return decrypt_json(blob, self.key)
    
    def _write(self, data: Dict) -> None:
        if not self.paths.vault_file.exists():
            raise FileNotFoundError("vault.png not found")

        blob = encrypt_json(data, self.key)
        embed(self.paths.vault_file, blob, self.paths.vault_file)

    def add_entry(self, service: str, password: str) -> None:
        service = service.strip().lower()
        data = self._read()
        data.setdefault("entries", {})
        data["entries"][service] = {"password": password}
        self._write(data)
    
    def update_entry(self, service: str, password: str):
        self.add_entry(service, password)
    
    def delete_entry(self, service: str) -> bool:
        service = service.strip().lower()
        data = self._read()
        entries = data.get("entries", {})
        if service not in entries:
            return False
        del entries[service]
        data["entries"] = entries
        self._write(data)
        return True

    def get_entry(self, service: str) -> Optional[Dict]:
        service = service.strip().lower()
        data = self._read()
        return data.get("entries", {}).get(service)
    
    def list_services(self) -> list[str]:
        data=self._read()
        return sorted(list(data.get("entries", {}).keys()))

    def verify_master(self) -> None:
        _ = self._read()