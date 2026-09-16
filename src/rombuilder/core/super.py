from __future__ import annotations
import json, shutil
from pathlib import Path
from .exec import run, require, ToolError

class SuperBuilder:
    def __init__(self, root, logger): self.root=Path(root); self.log=logger
    def _lpdump(self): return shutil.which('lpdump') or str(self.root/'bin/linux-x86_64/lpdump')
    def dump(self, super_img:Path):
        tool=self._lpdump();
        if not Path(tool).exists() and not shutil.which('lpdump'): raise ToolError('lpdump is required')
        cp=run([tool,'--json',str(super_img)],logger=self.log)
        try: return json.loads(cp.stdout)
        except json.JSONDecodeError as e: raise ToolError('lpdump JSON parse failed') from e
    @staticmethod
    def _groups(data):
        groups={}
        for g in data.get('groups',[]):
            name=g.get('name') or g.get('group_name'); size=g.get('maximum_size',g.get('size'))
            if name and size is not None: groups[name]=int(size)
        return groups
    def rebuild(self, original_super:Path, images:dict[str,Path], out:Path, sparse=True):
        data=self.dump(original_super)
        meta_size=int(data.get('metadata_size',65536)); slots=int(data.get('metadata_slot_count',2))
        super_name=data.get('super_name','super'); blocks=data.get('block_devices',[])
        if not blocks: raise ToolError('lpdump JSON has no block_devices')
        bd=blocks[0]; device_size=int(bd.get('size',data.get('super_partition_size',0)))
        if device_size<=0: raise ToolError('Cannot determine super partition size')
        args=['lpmake','--metadata-size',str(meta_size),'--metadata-slots',str(slots),'--super-name',super_name,'--device',f'super:{device_size}','--output',str(out)]
        for g,size in self._groups(data).items(): args += ['--group',f'{g}:{size}']
        for p in data.get('partitions',[]):
            name=p.get('name'); group=p.get('group_name') or p.get('group');
            if not name or not group: continue
            path=images.get(name)
            size=int(p.get('size',0))
            # lpmake partition size is taken from the image for changed partitions; otherwise retain metadata size.
            if path and path.exists(): size=max(size,path.stat().st_size)
            attr=int(p.get('attributes',0))
            flags='readonly' if (attr & 1) else 'none'
            spec=f'{name}:{group}:{size}'
            if flags=='readonly': spec += ':readonly'
            args += ['--partition',spec]
        # Add image payloads after partition declarations.
        for p in data.get('partitions',[]):
            name=p.get('name'); path=images.get(name)
            if name and path and path.exists(): args += ['--image',f'{name}={path}']
        if sparse: args.append('--sparse')
        tool=shutil.which('lpmake') or str(self.root/'bin/linux-x86_64/lpmake')
        args[0]=tool
        out.parent.mkdir(parents=True,exist_ok=True)
        run(args,logger=self.log)
        if not out.exists() or out.stat().st_size==0: raise ToolError('lpmake produced no super image')
        return out
