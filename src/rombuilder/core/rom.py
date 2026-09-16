from __future__ import annotations
import shutil, zipfile
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
    def extract_super(self, super_img: Path) -> Path:
        tool=require(str(self.p.root/'bin/linux-x86_64/lpunpack'),'lpunpack')
        out=self.p.partitions/'super'; out.mkdir(parents=True,exist_ok=True)
        run([tool,str(super_img),str(out)],logger=self.log)
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
