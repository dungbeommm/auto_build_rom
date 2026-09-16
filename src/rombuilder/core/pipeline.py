from __future__ import annotations
import json, shutil, re
from pathlib import Path
from .paths import Paths
from .state import State
from .rom import RomWorkspace
from .super import SuperBuilder
from .imagefs.manager import ImageManager
from ..mods.manager import ModManager

PARTITION_HINTS={
 'framework.jar':['system','system_ext'], 'services.jar':['system'], 'miui-framework.jar':['system','system_ext'], 'miui-services.jar':['system','system_ext'],
 'MiuiSystemUI.apk':['system','system_ext','product'], 'Settings.apk':['system','product'], 'PowerKeeper.apk':['system','product'],
 'FrequentPhrase.apk':['product','system'], 'ExternalStorageProvider.apk':['system','system_ext'], '*ThemeManager.apk':['product','system'],
 '*PersonalAssistant*.apk':['product','system'], '*Weather.apk':['product','system'], 'Joyose.apk':['system','product'], '*Gallery.apk':['product','system'],
 '*Provision.apk':['product','system'], '*SecurityCenter.apk':['system','product']}

class Pipeline:
    def __init__(self,root,logger):
        self.root=Path(root); self.paths=Paths(self.root); self.paths.ensure(); self.state=State(self.paths.state/'pipeline.json'); self.log=logger; self.last_tree=None
        self.rom=RomWorkspace(self.paths,logger); self.imagefs=ImageManager(logger,self.root); self.super=SuperBuilder(self.root,logger); self.mods=ModManager(self.root,self.paths,logger)
    def _needed_partitions(self,features):
        req,_,_=self.mods.plan([],features)
        names=set()
        for r in req:
            for pat in r.patterns:
                names.update(PARTITION_HINTS.get(pat, ['system','system_ext','product']))
        return sorted(names)
    def prepare_roots(self,source:Path,features=None):
        source=Path(source); tree=source
        if source.is_file() and source.suffix.lower()=='.zip': tree=self.rom.extract_zip(source)
        super_img=self.rom.discover_super(tree)
        if super_img:
            unpacked=self.rom.extract_super(super_img)
            bases=self._needed_partitions(features or [])
            candidates=self.rom.logical_candidates(unpacked,bases)
            decoded_root=self.paths.workspace/'decoded_partitions'; decoded_root.mkdir(parents=True,exist_ok=True)
            roots=[]
            for img in candidates:
                base=re.sub(r'_[ab]$','',img.stem); out=decoded_root/base
                marker=out/'.complete'
                if not marker.exists(): self.imagefs.extract(img,out); marker.touch()
                roots.append(out)
            return tree,super_img,roots
        flat=self.rom.copy_image_partitions(tree)
        roots=[]
        for img in flat.glob('*.img'):
            base=re.sub(r'_[ab]$','',img.stem); out=self.paths.workspace/'decoded_partitions'/base; marker=out/'.complete'
            if not marker.exists(): self.imagefs.extract(img,out); marker.touch()
            roots.append(out)
        return tree,None,roots
    def analyze(self,source,features):
        tree,super_img,roots=self.prepare_roots(Path(source),features); req,found,missing=self.mods.plan(roots,features)
        return {'tree':str(tree),'super':str(super_img) if super_img else None,'roots':[str(x) for x in roots],'requirements':[r.__dict__ for r in req],'found':[(r.__dict__,str(p)) for r,p in found],'missing':[r.__dict__ for r,p in missing]}
    def patch(self,source,features,strict=True):
        source=Path(source); tree,super_img,roots=self.prepare_roots(source,features); self.last_tree=tree
        result=self.mods.run(roots,features,strict=strict)
        self.state.mark('patch',source=str(source),features=features,count=len(result))
        return result

    def rebuild(self, source, features, strict=True):
        source=Path(source); tree,super_img,roots=self.prepare_roots(source,features); self.last_tree=tree
        result=self.mods.run(roots,features,strict=strict)
        if not result: raise RuntimeError('Nothing was modified; refusing to rebuild an unchanged ROM')
        changed={Path(x['partition_root']).resolve() for x in result}
        image_map={}
        if super_img:
            unpacked=self.rom.extract_super(super_img)
            rebuilt_dir=self.paths.workspace/'rebuilt_partitions'; rebuilt_dir.mkdir(parents=True,exist_ok=True)
            for root in changed:
                base=root.name
                srcs=list(unpacked.glob(base+'_a.img'))+list(unpacked.glob(base+'_b.img'))+list(unpacked.glob(base+'.img'))
                if not srcs: raise RuntimeError(f'Cannot map decoded partition back to logical image: {base}')
                for src_img in srcs:
                    fs=self.imagefs.fstype(src_img); out=rebuilt_dir/src_img.name
                    self.imagefs.repack(root,out,fs,src_img); image_map[src_img.name]=out
            # Keep all original logical images, replacing only changed ones.
            for p in unpacked.glob('*.img'):
                image_map.setdefault(p.name,p)
            out_super=self.paths.release/'super.img'; self.super.rebuild(super_img,image_map,out_super,sparse=True)
            # Replace super.img inside the original ROM tree.
            for p in tree.rglob('super.img'):
                if p != out_super: shutil.copy2(out_super,p)
        else:
            for root in changed:
                candidates=list(tree.rglob(root.name+'.img'))
                if not candidates: continue
                src=candidates[0]; fs=self.imagefs.fstype(src); out=self.paths.release/src.name; self.imagefs.repack(root,out,fs,src); shutil.copy2(out,src)
        self.state.mark('rebuild',count=len(result),release=str(self.paths.release))
        return result

    def package(self, tree, output):
        tree=Path(tree); output=Path(output); output.parent.mkdir(parents=True,exist_ok=True)
        base=output.with_suffix(''); shutil.make_archive(str(base),'zip',root_dir=tree)
        built=base.with_suffix('.zip')
        if built != output: shutil.move(built,output)
        return output
