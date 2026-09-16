"""Profile-driven APK modification engine."""
from __future__ import annotations
import hashlib, json, logging, os, re, shutil, subprocess, tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

@dataclass
class ApkJobResult:
    name: str
    source: str
    output: str
    status: str
    operations: int = 0
    sha256: str = ""
    error: str = ""

class ApkModEngine:
    def __init__(self, ctx, logger: logging.Logger | None = None):
        self.ctx = ctx; self.log = logger or logging.getLogger("ApkModEngine")
        self.root = Path(getattr(ctx, "target_dir", ".")); self.tools = getattr(ctx, "tools", None)
    def _tool(self, *names: str) -> Path | None:
        candidates=[]
        for n in names:
            if self.tools is not None:
                p=getattr(self.tools,n,None)
                if p: candidates.append(Path(p))
            d=os.environ.get("TOOL_TREE_BIN")
            if d: candidates.append(Path(d)/n)
            found=shutil.which(n)
            if found: candidates.append(Path(found))
        return next((p for p in candidates if p.exists()),None)
    def _java_jar(self, jar: Path, args: list[str]) -> None:
        subprocess.run(["java","-jar",str(jar),*args],check=True,cwd=str(self.root))
    @staticmethod
    def sha256(path: Path) -> str:
        h=hashlib.sha256()
        with path.open("rb") as f:
            for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
        return h.hexdigest()
    def find_apk(self,spec:dict[str,Any])->Path|None:
        p=spec.get("path")
        if p and (self.root/p).is_file(): return self.root/p
        matches=list(self.root.rglob("*.apk")); name=spec.get("name")
        if name:
            x=[p for p in matches if p.name.lower()==f"{name.lower()}.apk"]
            if x:return x[0]
        package=spec.get("package"); aapt2=self._tool("aapt2")
        if package and aapt2:
            for p in matches:
                try:
                    r=subprocess.run([str(aapt2),"dump","packagename",str(p)],capture_output=True,text=True,timeout=20)
                    if r.returncode==0 and package in r.stdout:return p
                except Exception:pass
        return matches[0] if len(matches)==1 else None
    def _decode(self,apk:Path,work:Path)->str:
        jar=getattr(self.tools,"apkeditor_jar",None) if self.tools else None
        if jar and Path(jar).exists(): self._java_jar(Path(jar),["d","-f","-i",str(apk),"-o",str(work)]); return "apkeditor"
        jar=getattr(self.tools,"apktool_jar",None) if self.tools else None
        if jar and Path(jar).exists(): self._java_jar(Path(jar),["d","-f",str(apk),"-o",str(work)]); return "apktool"
        tool=self._tool("apktool")
        if tool: subprocess.run([str(tool),"d","-f",str(apk),"-o",str(work)],check=True); return "apktool"
        raise RuntimeError("No APK decoder found")
    def _build(self,work:Path,out:Path,decoder:str)->None:
        if decoder=="apkeditor":
            jar=getattr(self.tools,"apkeditor_jar",None) if self.tools else None
            if jar and Path(jar).exists(): self._java_jar(Path(jar),["b","-f","-i",str(work),"-o",str(out)]); return
        jar=getattr(self.tools,"apktool_jar",None) if self.tools else None
        if jar and Path(jar).exists(): self._java_jar(Path(jar),["b",str(work),"-o",str(out)]); return
        tool=self._tool("apktool")
        if tool: subprocess.run([str(tool),"b",str(work),"-o",str(out)],check=True); return
        raise RuntimeError("No APK builder found")
    def _apply_ops(self,work:Path,ops:list[dict[str,Any]])->int:
        count=0
        for op in ops:
            typ=op.get("type"); rel=op.get("file") or op.get("path"); target=work/rel if rel else work
            if typ=="replace_text":
                t=target.read_text(encoding="utf-8"); u=t.replace(str(op["old"]),str(op["new"]))
                if u!=t: target.write_text(u,encoding="utf-8"); count+=1
            elif typ=="regex_replace":
                t=target.read_text(encoding="utf-8"); u=re.sub(op["pattern"],op.get("replacement",""),t,flags=re.MULTILINE)
                if u!=t: target.write_text(u,encoding="utf-8"); count+=1
            elif typ=="delete_file":
                if target.is_dir(): shutil.rmtree(target)
                elif target.exists(): target.unlink()
                count+=1
            elif typ in {"copy_file","add_file"}:
                src=Path(op["source"]); src=src if src.is_absolute() else Path.cwd()/src
                target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,target); count+=1
            elif typ=="append_text":
                with target.open("a",encoding="utf-8") as f:f.write(str(op.get("text","")))
                count+=1
            elif typ in {"smali_replace","smali_regex","regex_smali"}:
                files=[target] if target.is_file() else list(target.rglob("*.smali"))
                for f in files:
                    t=f.read_text(encoding="utf-8",errors="ignore")
                    u=(t.replace(str(op["old"]),str(op["new"])) if typ=="smali_replace" else re.sub(op["pattern"],op.get("replacement",""),t,flags=re.MULTILINE))
                    if u!=t:f.write_text(u,encoding="utf-8");count+=1
            else: raise ValueError(f"Unsupported APK operation: {typ}")
        return count
    def _align_sign_verify(self,unsigned:Path,final:Path,job:dict[str,Any])->None:
        align=self._tool("zipalign"); signer=self._tool("apksigner")
        if align:
            aligned=unsigned.with_name(unsigned.stem+".aligned.apk"); subprocess.run([str(align),"-p","4",str(unsigned),str(aligned)],check=True); unsigned=aligned
        sign=job.get("sign",{}) or {}
        if sign.get("enabled",False):
            if not signer:raise RuntimeError("Signing requested but apksigner was not found")
            if not sign.get("key") or not sign.get("cert"):raise ValueError("sign.key and sign.cert are required")
            subprocess.run([str(signer),"sign","--key",sign["key"],"--cert",sign["cert"],"--out",str(final),str(unsigned)],check=True)
        else: shutil.copy2(unsigned,final)
        if signer: subprocess.run([str(signer),"verify","--verbose",str(final)],check=True)
    def run_job(self,job:dict[str,Any])->ApkJobResult:
        name=job.get("name") or job.get("package") or "apk"; source=self.find_apk(job)
        if not source:return ApkJobResult(name,"","","skipped",error="APK not found")
        backup=source.with_suffix(source.suffix+".romauto-backup"); shutil.copy2(source,backup); work=Path(tempfile.mkdtemp(prefix=f"romauto-apk-{name}-"))
        try:
            dec=self._decode(source,work); ops=self._apply_ops(work,job.get("operations",[])); built=work.parent/f"{name}-built.apk"; self._build(work,built,dec); self._align_sign_verify(built,source,job)
            digest=self.sha256(source); backup.unlink(missing_ok=True); return ApkJobResult(name,str(source),str(source),"success",ops,digest)
        except Exception as exc:
            shutil.copy2(backup,source); return ApkJobResult(name,str(source),str(source),"failed",error=str(exc))
        finally:
            shutil.rmtree(work,ignore_errors=True); (work.parent/f"{name}-built.apk").unlink(missing_ok=True)
    def run_profile(self,profile:str|Path)->dict[str,Any]:
        data=json.loads(Path(profile).read_text(encoding="utf-8")); jobs=data.get("apps",[]) if isinstance(data,dict) else []
        results=[asdict(self.run_job(j)) for j in jobs]
        return {"results":results,"success":all(r["status"] in {"success","skipped"} for r in results)}
