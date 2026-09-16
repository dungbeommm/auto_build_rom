from __future__ import annotations
import os, shutil, tempfile
from pathlib import Path
from ..exec import run, require, ToolError

class ImageManager:
    def __init__(self, logger): self.log=logger
    def fstype(self, image: Path) -> str:
        with image.open('rb') as f: head=f.read(4096)
        if b'EROFS' in head or head[0:4] in (b'\xe2\xe1\xf5\xe0',): return 'erofs'
        if b'EXT4' in head or head[0x438:0x43a] in (b'\x53\xef',): return 'ext4'
        # ext4 magic is little endian 0xEF53 at offset 0x438.
        try:
            if head[0x438:0x43a] == b'\x53\xef': return 'ext4'
        except Exception: pass
        return 'unknown'
    def extract(self, image: Path, out: Path):
        out.mkdir(parents=True,exist_ok=True); fs=self.fstype(image); self.log.info('%s: filesystem=%s',image,fs)
        if fs=='ext4':
            mount=require('mount','mount'); umount=require('umount','umount')
            # Root is normally required on Linux CI. Use a temporary loop mount.
            run(['sudo',mount,'-o','ro,loop',str(image),str(out)],logger=self.log)
            return ('mount',umount)
        if fs=='erofs':
            dump=shutil.which('extract.erofs') or shutil.which('dump.erofs')
            if not dump: raise ToolError('ERoFS image detected but extract.erofs/dump.erofs is missing')
            run([dump,str(image),str(out)],logger=self.log); return ('tool',None)
        raise ToolError(f'Unsupported filesystem in {image}')
    def inject_ext4(self, image: Path, root: Path, files: list[tuple[Path,Path]]):
        mount=require('mount','mount'); umount=require('umount','umount')
        mnt=Path(tempfile.mkdtemp(prefix='rom-mnt-'))
        try:
            run(['sudo',mount,'-o','loop,rw',str(image),str(mnt)],logger=self.log)
            for src,rel in files:
                dst=mnt/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
        finally:
            run(['sudo',umount,str(mnt)],logger=self.log,check=False); shutil.rmtree(mnt,ignore_errors=True)
