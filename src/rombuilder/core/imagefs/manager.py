from __future__ import annotations
import shutil, struct, subprocess
from pathlib import Path
from ..exec import run, require

class ImageManager:
    def __init__(self, logger, root): self.log=logger; self.root=Path(root)
    def fstype(self,image:Path):
        with image.open('rb') as f:
            f.seek(0); head=f.read(4096)
        if len(head)>=0x43c and head[0x438:0x43a] == b'\x53\xef': return 'ext4'
        if head[:4] == b'\xe2\xe1\xf5\xe0' or head[1024:1028] == b'\xe2\xe1\xf5\xe0': return 'erofs'
        return 'unknown'
    def extract(self,image:Path,out:Path):
        fs=self.fstype(image); out.mkdir(parents=True,exist_ok=True)
        if fs=='ext4':
            debugfs=require('debugfs','debugfs')
            run([debugfs,'-R',f'rdump / {out}',str(image)],logger=self.log)
        elif fs=='erofs':
            fsck=shutil.which('fsck.erofs') or str(self.root/'bin/linux-x86_64/fsck.erofs')
            if not Path(fsck).exists() and not shutil.which('fsck.erofs'): raise RuntimeError('fsck.erofs is required for EROFS extraction')
            run([fsck,f'--extract={out}',str(image)],logger=self.log)
        else: raise RuntimeError(f'Unsupported filesystem for {image}: {fs}')
        return out
    def repack(self,root:Path,out:Path,fs:str,source_img:Path|None=None):
        out.parent.mkdir(parents=True,exist_ok=True)
        if fs=='erofs':
            tool=shutil.which('mkfs.erofs') or str(self.root/'bin/linux-x86_64/mkfs.erofs')
            if not shutil.which('mkfs.erofs') and not Path(tool).exists(): raise RuntimeError('mkfs.erofs is required')
            run([tool,str(out),str(root)],logger=self.log)
        elif fs=='ext4':
            # mke2fs -d is available on Ubuntu and produces a regular ext4 image.
            mke2fs=require('mke2fs','mke2fs')
            du=subprocess.check_output(['du','-sb',str(root)],text=True).split()[0]
            size=max(int(du)+64*1024*1024, 128*1024*1024)
            blocks=(size+4095)//4096
            run([mke2fs,'-t','ext4','-d',str(root),str(out),str(blocks)],logger=self.log)
        else: raise RuntimeError(f'Unsupported filesystem for repack: {fs}')
        return out
