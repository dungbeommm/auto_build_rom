from __future__ import annotations
import shutil, subprocess, zipfile
from pathlib import Path
from .exec import run, require

class ApkJarTool:
    def __init__(self, root, logger): self.root=Path(root); self.log=logger
    def _tool(self, name):
        p=self.root/'bin/linux-x86_64'/name
        return str(p) if p.exists() else require(name, name)
    def decode_apk(self, apk: Path, out: Path):
        tool=self.root/'bin/linux-x86_64/apktool.jar'; java=require('java','Java')
        if not tool.exists(): raise RuntimeError('Missing apktool.jar. Install/provide it in bin/linux-x86_64.')
        out.parent.mkdir(parents=True,exist_ok=True)
        run([java,'-jar',str(tool),'d','-f','-o',str(out),str(apk)],logger=self.log)
    def build_apk(self, decoded: Path, apk: Path):
        tool=self.root/'bin/linux-x86_64/apktool.jar'; java=require('java','Java')
        if not tool.exists(): raise RuntimeError('Missing apktool.jar. Install/provide it in bin/linux-x86_64.')
        apk.parent.mkdir(parents=True,exist_ok=True)
        run([java,'-jar',str(tool),'b','-o',str(apk),str(decoded)],logger=self.log)
    def decode_jar(self, jar: Path, out: Path):
        bak=self.root/'bin/linux-x86_64/baksmali.jar'; java=require('java','Java')
        if not bak.exists(): raise RuntimeError('Missing baksmali.jar. Install/provide it in bin/linux-x86_64.')
        out.mkdir(parents=True,exist_ok=True)
        # baksmali supports multi-dex and preserves dex ordering by directory layout.
        run([java,'-jar',str(bak),'d',str(jar),'-o',str(out)],logger=self.log)
    def build_jar(self, decoded: Path, jar: Path, original: Path | None = None):
        sm=self.root/'bin/linux-x86_64/smali.jar'; java=require('java','Java')
        if not sm.exists(): raise RuntimeError('Missing smali.jar. Install/provide it in bin/linux-x86_64.')
        jar.parent.mkdir(parents=True,exist_ok=True)
        # Build dex into a temporary tree. smali accepts a directory containing smali files.
        tmp=jar.parent/'.dexbuild'; tmp.mkdir(parents=True,exist_ok=True)
        dex=tmp/'classes.dex'
        run([java,'-jar',str(sm),'a',str(decoded),'-o',str(dex)],logger=self.log)
        if not dex.exists(): raise RuntimeError('smali did not create classes.dex')
        # Preserve every non-dex entry from the original JAR. Never create a one-entry JAR.
        with zipfile.ZipFile(original or jar, 'r') as zin:
            entries=[(i, zin.read(i.filename)) for i in zin.infolist() if not (i.filename.startswith('classes') and i.filename.endswith('.dex'))]
            dex_names=sorted([i.filename for i in zin.infolist() if i.filename.startswith('classes') and i.filename.endswith('.dex')])
        tmpjar=jar.with_suffix('.tmp.jar')
        with zipfile.ZipFile(tmpjar,'w',compression=zipfile.ZIP_DEFLATED) as zout:
            for info,data in entries:
                # Drop signature files because the archive is modified and old signatures are invalid.
                if info.filename.upper().startswith('META-INF/') and info.filename.upper().split('/')[-1].endswith(('.SF','.RSA','.DSA','.EC')):
                    continue
                zout.writestr(info,data)
            zout.write(dex,'classes.dex')
            # The current smali CLI emits one dex. Keep additional original dex files intact.
            for name in dex_names:
                if name != 'classes.dex':
                    with zipfile.ZipFile(original or jar,'r') as zin: zout.writestr(name,zin.read(name))
        tmpjar.replace(jar); shutil.rmtree(tmp,ignore_errors=True)
    def copy_file(self, src: Path, dst: Path): dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
