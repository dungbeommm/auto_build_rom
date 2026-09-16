from __future__ import annotations
from pathlib import Path
from .paths import Paths
from .state import State
from .rom import RomWorkspace
from .imagefs.manager import ImageManager
from ..mods.manager import ModManager

class Pipeline:
    def __init__(self, root, logger):
        self.root=Path(root)
        self.paths=Paths(self.root); self.paths.ensure()
        self.state=State(self.paths.state/'pipeline.json')
        self.log=logger
        self.rom=RomWorkspace(self.paths,logger)
        self.imagefs=ImageManager(logger,self.root)
        self.mods=ModManager(self.root,self.paths,logger)

    def prepare_roots(self, source: Path):
        source=Path(source)
        tree=source
        if source.is_file() and source.suffix.lower()=='.zip':
            tree=self.rom.extract_zip(source)
        super_img=self.rom.discover_super(tree)
        if super_img:
            unpacked=self.rom.extract_super(super_img)
            roots=self.imagefs.extract_partitions(unpacked, self.paths.workspace/'decoded_partitions')
            return tree, super_img, roots
        flat=self.rom.copy_image_partitions(tree)
        if flat.exists() and any(flat.glob('*.img')):
            roots=self.imagefs.extract_partitions(flat, self.paths.workspace/'decoded_partitions')
            return tree, None, roots
        return tree, None, [tree]

    def analyze(self, source: Path, features):
        tree,super_img,roots=self.prepare_roots(source)
        req,found,missing=self.mods.plan(roots,features)
        return {
            'tree':str(tree),
            'super':str(super_img) if super_img else None,
            'roots':[str(r) for r in roots],
            'requirements':[r.__dict__ for r in req],
            'found':[(r.__dict__,str(p)) for r,p in found],
            'missing':[r.__dict__ for r,p in missing]
        }

    def patch(self, source: Path, features, strict=True):
        tree,super_img,roots=self.prepare_roots(source)
        result=self.mods.run(roots,features,strict=strict)
        self.state.mark('patch',source=str(source),tree=str(tree),super=str(super_img) if super_img else None,features=features,count=len(result))
        return result
