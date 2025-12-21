from __future__ import annotations
import base64
from pathlib import Path
from typing import Optional
from PIL import Image
from PIL.PngImagePlugin import PngInfo

VAULT_CHUNK_KEY = "vaultic"

def embed(cover_path: str | Path, blob: bytes, out_path: str | Path):
    cover_path = Path(cover_path)
    out_path = Path(out_path)

    img = Image.open(cover_path)
    if img.format != "PNG":
        img = img.convert("RGBA")
    
    meta = PngInfo()
    meta.add_text(VAULT_CHUNK_KEY, base64.b64encode(blob).decode("ascii"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG", pnginfo=meta)

def extract(vault_path: str | Path) -> Optional[bytes]:
    vault_path = Path(vault_path)
    img = Image.open(vault_path)
    info = getattr(img, "info", {}) or {}
    text = info.get(VAULT_CHUNK_KEY)

    if not text:
        return None

    try: 
        return base64.b64decode(text)
    except Exception:
        return None
