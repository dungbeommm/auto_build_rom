from __future__ import annotations
import zipfile, hashlib, subprocess
from pathlib import Path
class Verify:
    @staticmethod
    def zip(path):
        with zipfile.ZipFile(path) as z:
            bad=z.testzip()
            if bad: raise RuntimeError(f'Corrupt ZIP member: {bad}')
        return True
    apk=zip
    jar=zip
    rom_zip=zip
    @staticmethod
    def sha256(path):
        h=hashlib.sha256()
        with open(path,'rb') as f:
            for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
        return h.hexdigest()
