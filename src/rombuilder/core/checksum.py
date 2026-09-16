from __future__ import annotations
import hashlib
from pathlib import Path

def sha256(path: Path, chunk=1024*1024):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while b:=f.read(chunk): h.update(b)
    return h.hexdigest()
