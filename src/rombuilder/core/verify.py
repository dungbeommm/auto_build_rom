from __future__ import annotations
import zipfile
from pathlib import Path
class Verify:
    @staticmethod
    def apk(path: Path):
        with zipfile.ZipFile(path) as z: bad=z.testzip()
        if bad: raise RuntimeError(f'Corrupt APK archive: {bad}')
        return True
    @staticmethod
    def jar(path: Path):
        with zipfile.ZipFile(path) as z: bad=z.testzip()
        if bad: raise RuntimeError(f'Corrupt JAR archive: {bad}')
        return True
    @staticmethod
    def rom_zip(path: Path):
        with zipfile.ZipFile(path) as z: bad=z.testzip()
        if bad: raise RuntimeError(f'Corrupt ROM zip: {bad}')
        return True
