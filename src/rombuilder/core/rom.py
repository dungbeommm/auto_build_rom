from __future__ import annotations
import shutil, zipfile, struct
from pathlib import Path
from .exec import run, require

class RomWorkspace:
    def __init__(self, paths, logger): self.p=paths; self.log=logger
    def import_input(self, src: Path) -> Path:
        dst=self.p.source / src.name
        if src.resolve()!=dst.resolve(): shutil.copy2(src,dst)
        self.log.info('Imported input: %s', dst)
        return dst
    def extract_zip(self, rom: Path) -> Path:
        out=self.p.source/'rom_zip'; out.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(rom) as z: z.extractall(out)
        return out
    def discover_super(self, tree: Path) -> Path|None:
        for p in tree.rglob('super.img'):
            if p.is_file(): return p
        return None
    def _is_sparse_image(self, image: Path) -> bool:
        with image.open('rb') as f:
            header = f.read(4)
        return len(header) == 4 and struct.unpack('<I', header)[0] == 0xED26FF3A

    def _unsparse_image(self, image: Path) -> Path:
        tool = require('simg2img', 'simg2img')
        out = self.p.partitions / 'super.unsparse.img'
        out.parent.mkdir(parents=True, exist_ok=True)
        self.log.info('Sparse super.img detected; converting with simg2img')
        run([tool, str(image), str(out)], logger=self.log)
        if not out.is_file() or out.stat().st_size == 0:
            raise RuntimeError(f'simg2img did not produce a valid image: {out}')
        return out

    def extract_super(self, super_img: Path) -> Path:
        tool = require('lpunpack', 'lpunpack')
        out = self.p.partitions/'super'; out.mkdir(parents=True,exist_ok=True)
        source = self._unsparse_image(super_img) if self._is_sparse_image(super_img) else super_img
        run([tool,str(source),str(out)],logger=self.log)
        return out
    def copy_image_partitions(self, tree: Path):
        out=self.p.partitions/'flat'; out.mkdir(parents=True,exist_ok=True)
        for name in ('system','system_ext','product','vendor','odm','mi_ext','system_dlkm','vendor_dlkm'):
            for p in tree.rglob(name+'.img'):
                shutil.copy2(p,out/p.name)
        return out
    def partition_roots(self) -> list[Path]:
        roots=[]
        for base in (self.p.partitions/'super', self.p.partitions/'flat'):
            if base.exists(): roots += [x for x in base.iterdir() if x.is_dir()]
        return roots
