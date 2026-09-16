from __future__ import annotations
from pathlib import Path
import shutil
from ..core.config import Config
from ..core.dependency import requirements, locate
from ..core.archive import ApkJarTool
from ..core.recipes import RecipeEngine, RecipeError
from ..core.verify import Verify
from ..core.exec import ToolError

class ModManager:
    def __init__(self,root,paths,logger):
        self.root=Path(root); self.paths=paths; self.log=logger; self.cfg=Config(self.root)
        self.archive=ApkJarTool(self.root,logger); self.recipes=RecipeEngine(self.cfg,logger)
    def plan(self,roots,features): return (*requirements(self.cfg,features),) if False else self._plan(roots,features)
    def _plan(self,roots,features):
        req=requirements(self.cfg,features); found,missing=locate(roots,req); return req,found,missing
    def run(self,roots,features,strict=True):
        req,found,missing=self._plan(roots,features)
        if missing:
            msg='Missing targets: '+', '.join(f'{r.feature}:{r.patterns}' for r,_ in missing)
            if strict: raise ToolError(msg)
            self.log.warning(msg)
        results=[]; changed_roots=set()
        # One target may be required by several features. Decode/build once and apply all recipes to it.
        grouped={}
        for r,path in found: grouped.setdefault(path,[]).append(r)
        for path,rs in grouped.items():
            target_work=self.paths.targets/path.name; target_work.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(path,target_work)
            decoded=self.paths.decoded/path.stem
            if decoded.exists(): shutil.rmtree(decoded)
            if rs[0].kind=='apk': self.archive.decode_apk(target_work,decoded)
            else: self.archive.decode_jar(target_work,decoded)
            all_changes=[]
            for r in rs:
                try: all_changes += self.recipes.apply_feature(r.feature,target_work,decoded)
                except RecipeError as e:
                    if strict: raise
                    self.log.warning(str(e))
            rebuilt=self.paths.repacked/path.name
            if rs[0].kind=='apk': self.archive.build_apk(decoded,rebuilt); Verify.apk(rebuilt)
            else: self.archive.build_jar(decoded,rebuilt,original=target_work); Verify.jar(rebuilt)
            # Replace the actual file in its decoded partition so filesystem repack sees it.
            shutil.copy2(rebuilt,path)
            changed_roots.add(self._root_for(path,roots))
            results.append({'features':[r.feature for r in rs],'target':str(path),'rebuilt':str(rebuilt),'changes':len(all_changes),'partition_root':str(self._root_for(path,roots))})
        return results
    @staticmethod
    def _root_for(path,roots):
        path=path.resolve()
        for root in roots:
            try:
                path.relative_to(Path(root).resolve()); return Path(root)
            except ValueError: pass
        raise ToolError(f'Target is outside known partition roots: {path}')
