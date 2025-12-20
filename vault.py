import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

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
        vault_file=base / "vault.bin",
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

    def _read(self) -> Dict:
        if not self.paths.vault_file.exists():
            return {"entries": {}}
        blob = self.paths.vault_file.read_bytes()
        return decrypt_json(blob, self.key)

    def _write(self, data: Dict) -> None:
        blob = encrypt_json(data, self.key)
        self.paths.vault_file.write_bytes(blob)

    def add_entry(self, service: str, password: str) -> None:
        service = service.strip().lower()
        data = self._read()
        data.setdefault("entries", {})
        data["entries"][service] = {"password": password}
        self._write(data)

    def get_entry(self, service: str) -> Optional[Dict]:
        service = service.strip().lower()
        data = self._read()
        return data.get("entries", {}).get(service)
    
    def list_services(self) -> list[str]:
        data=self._read()
        return sorted(list(data.get("entries", {}).keys()))

    def verify_master(self) -> None:
        _ = self._read()