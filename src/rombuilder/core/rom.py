from __future__ import annotations
import shutil, zipfile, struct, re, os
from pathlib import Path
from .exec import run, require

class RomWorkspace:
    def __init__(self, paths, logger): self.p=paths; self.log=logger
    def import_input(self,src:Path)->Path:
        dst=self.p.source/src.name; dst.parent.mkdir(parents=True,exist_ok=True)
        if src.resolve()!=dst.resolve(): shutil.copy2(src,dst)
        return dst
    def extract_zip(self,rom:Path)->Path:
        out=self.p.source/'rom_zip'; out.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(rom) as z:
            bad=z.testzip()
            if bad: raise RuntimeError(f'Corrupt ROM zip member: {bad}')
            for i in z.infolist():
                target=(out/i.filename).resolve()
                if not str(target).startswith(str(out.resolve())+os.sep): raise RuntimeError(f'Unsafe zip member: {i.filename}')
            z.extractall(out)
        return out
    def discover_super(self,tree:Path)->Path|None:
        for p in tree.rglob('super.img'):
            if p.is_file(): return p
        return None
    @staticmethod
    def is_sparse(image:Path)->bool:
        with image.open('rb') as f: h=f.read(4)
        return len(h)==4 and struct.unpack('<I',h)[0]==0xED26FF3A
    def unsparse(self,image:Path)->Path:
        tool=require('simg2img','simg2img'); out=self.p.partitions/'super.raw.img'; out.parent.mkdir(parents=True,exist_ok=True)
        if not out.exists(): run([tool,str(image),str(out)],logger=self.log)
        return out
    def extract_super(self,super_img:Path)->Path:
        tool=require('lpunpack','lpunpack'); out=self.p.partitions/'super'; out.mkdir(parents=True,exist_ok=True)
        source=self.unsparse(super_img) if self.is_sparse(super_img) else super_img
        marker=out/'.complete'
        if not marker.exists(): run([tool,str(source),str(out)],logger=self.log); marker.touch()
        return out
    def copy_image_partitions(self,tree:Path):
        out=self.p.partitions/'flat'; out.mkdir(parents=True,exist_ok=True)
        for p in tree.rglob('*.img'):
            if p.name=='super.img' or p.name.startswith('boot') or p.name.startswith('vendor_boot'): continue
            if p.stem.endswith(('_a','_b')) or p.stem in {'system','system_ext','product','vendor','odm','mi_ext','system_dlkm','vendor_dlkm'}:
                shutil.copy2(p,out/p.name)
        return out
    def logical_candidates(self,super_dir:Path,base_names:list[str]):
        out=[]
        for p in super_dir.glob('*.img'):
            n=p.stem
            base=re.sub(r'_[ab]$','',n)
            if base in base_names: out.append(p)
        return out
