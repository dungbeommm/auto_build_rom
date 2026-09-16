from __future__ import annotations
import shutil, zipfile
from pathlib import Path
from .paths import Paths
from .state import State
from .rom import RomWorkspace
from .verify import Verify
from ..mods.manager import ModManager
class Pipeline:
    def __init__(self, root, logger):
        self.root=Path(root); self.paths=Paths(self.root); self.paths.ensure(); self.state=State(self.paths.state/'pipeline.json'); self.log=logger; self.rom=RomWorkspace(self.paths,logger); self.mods=ModManager(self.root,self.paths,logger)
    def analyze(self, source: Path, features):
        tree=source
        if source.is_file() and source.suffix.lower()=='.zip': tree=self.rom.extract_zip(source)
        super_img=self.rom.discover_super(tree)
        roots=[]
        if super_img:
            out=self.rom.extract_super(super_img); roots += [p for p in out.rglob('*') if p.is_dir()]
        else:
            roots += [tree]
            flat=self.rom.copy_image_partitions(tree)
            if flat.exists(): roots += [flat]
        req,found,missing=self.mods.plan(roots,features)
        return {'tree':str(tree),'super':str(super_img) if super_img else None,'requirements':[r.__dict__ for r in req],'found':[(r.__dict__,str(p)) for r,p in found],'missing':[r.__dict__ for r,p in missing]}
    def patch_from_tree(self, roots, features, strict=True):
        result=self.mods.run(roots,features,strict=strict); self.state.mark('patch',features=features,count=len(result)); return result
