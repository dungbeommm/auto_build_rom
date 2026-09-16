from __future__ import annotations
import shutil, zipfile
from pathlib import Path
from .exec import run, require
class ApkJarTool:
    def __init__(self, root, logger): self.root=Path(root); self.log=logger
    def decode_apk(self, apk: Path, out: Path):
        out.parent.mkdir(parents=True,exist_ok=True); tool=self.root/'bin/linux-x86_64/apktool.jar'; java=require('java','Java')
        run([java,'-jar',str(tool),'d','-f','-o',str(out),str(apk)],logger=self.log)
    def build_apk(self, decoded: Path, apk: Path):
        tool=self.root/'bin/linux-x86_64/apktool.jar'; java=require('java','Java'); apk.parent.mkdir(parents=True,exist_ok=True)
        run([java,'-jar',str(tool),'b','-o',str(apk),str(decoded)],logger=self.log)
    def decode_jar(self, jar: Path, out: Path):
        out.mkdir(parents=True,exist_ok=True); bak=self.root/'bin/linux-x86_64/baksmali.jar'; java=require('java','Java')
        run([java,'-jar',str(bak),'d',str(jar),'-o',str(out)],logger=self.log)
    def build_jar(self, decoded: Path, jar: Path):
        sm=self.root/'bin/linux-x86_64/smali.jar'; java=require('java','Java'); tmp=jar.parent/'classes.dex'
        run([java,'-jar',str(sm),'a',str(decoded),'-o',str(tmp)],logger=self.log)
        with zipfile.ZipFile(jar,'w',compression=zipfile.ZIP_DEFLATED) as z: z.write(tmp,'classes.dex')
        tmp.unlink(missing_ok=True)
    def copy_apk(self, apk: Path, dst: Path): dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(apk,dst)
