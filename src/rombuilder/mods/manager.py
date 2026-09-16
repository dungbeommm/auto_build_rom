from __future__ import annotations
from pathlib import Path
from ..core.config import Config
from ..core.dependency import requirements, locate
from ..core.archive import ApkJarTool
from ..core.recipes import RecipeEngine, RecipeError
from ..core.verify import Verify
from ..core.exec import ToolError

class ModManager:
    def __init__(self, root, paths, logger):
        self.root=Path(root); self.paths=paths; self.log=logger; self.cfg=Config(self.root); self.archive=ApkJarTool(self.root,logger); self.recipes=RecipeEngine(self.cfg,logger)
    def plan(self, roots, features):
        req=requirements(self.cfg,features); found,missing=locate(roots,req)
        return req,found,missing
    def run(self, roots, features, strict=True):
        req,found,missing=self.plan(roots,features)
        if missing:
            msg='Missing targets: '+', '.join(f'{r.feature}:{r.patterns}' for r,_ in missing)
            if strict: raise ToolError(msg)
            self.log.warning(msg)
        if not found: return []
        results=[]
        for r,path in found:
            feature=r.feature
            target_work=self.paths.targets/path.name
            target_work.parent.mkdir(parents=True,exist_ok=True)
            self.archive.copy_apk(path,target_work) if r.kind=='apk' else self.archive.copy_apk(path,target_work)
            decoded=self.paths.decoded/path.stem
            if r.kind=='apk': self.archive.decode_apk(target_work,decoded)
            else: self.archive.decode_jar(target_work,decoded)
            try:
                changes=self.recipes.apply_feature(feature,target_work,decoded)
            except RecipeError as e:
                self.log.error(str(e));
                if strict: raise
                changes=[]
            rebuilt=self.paths.repacked/path.name
            if r.kind=='apk': self.archive.build_apk(decoded,rebuilt); Verify.apk(rebuilt)
            else: self.archive.build_jar(decoded,rebuilt); Verify.jar(rebuilt)
            results.append({'feature':feature,'target':str(path),'rebuilt':str(rebuilt),'changes':len(changes)})
        return results
