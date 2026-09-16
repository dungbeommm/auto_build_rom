from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from ..core.log import setup_logging
from ..core.paths import Paths
from ..core.pipeline import Pipeline
from ..core.config import Config
from ..core.dependency import requirements

def root_dir(): return Path(__file__).resolve().parents[3]

def main(argv=None):
    root=root_dir(); parser=argparse.ArgumentParser(prog='rom-builder')
    sub=parser.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('list-mods'); p.add_argument('--json',action='store_true')
    p=sub.add_parser('plan'); p.add_argument('source',type=Path); p.add_argument('--feature',action='append',required=True); p.add_argument('--verbose',action='store_true')
    p=sub.add_parser('patch'); p.add_argument('source',type=Path); p.add_argument('--feature',action='append',required=True); p.add_argument('--best-effort',action='store_true'); p.add_argument('--verbose',action='store_true')
    p=sub.add_parser('resume'); p.add_argument('--verbose',action='store_true')
    p=sub.add_parser('doctor'); p.add_argument('--verbose',action='store_true')
    a=parser.parse_args(argv)
    paths=Paths(root); paths.ensure(); log=setup_logging(paths.logs/'rom-builder.log',getattr(a,'verbose',False))
    if a.cmd=='list-mods':
        data=Config(root).mods['features']; print(json.dumps(data,indent=2,ensure_ascii=False) if a.json else '\n'.join(sorted(data))); return 0
    if a.cmd=='doctor':
        checks=['java','zipalign','apksigner','lpunpack','lpmake','lpdump','mount','umount']; import shutil
        ok=True
        for x in checks:
            found=shutil.which(x) or (str(root/'bin/linux-x86_64'/x) if (root/'bin/linux-x86_64'/x).exists() else None)
            print(f'{x}: {found or "MISSING"}'); ok &= bool(found)
        return 0 if ok else 2
    pipe=Pipeline(root,log)
    if a.cmd=='plan':
        print(json.dumps(pipe.analyze(a.source,a.feature),indent=2,ensure_ascii=False)); return 0
    if a.cmd=='patch':
        source=a.source
        if source.suffix.lower()=='.zip':
            tree=pipe.rom.extract_zip(source); super_img=pipe.rom.discover_super(tree)
            if super_img: out=pipe.rom.extract_super(super_img); roots=[p for p in out.rglob('*') if p.is_dir()]
            else: roots=[pipe.rom.copy_image_partitions(tree)]
        else: roots=[source]
        result=pipe.patch_from_tree(roots,a.feature,strict=not a.best_effort)
        print(json.dumps(result,indent=2,ensure_ascii=False)); return 0
    if a.cmd=='resume':
        print(json.dumps(pipe.state.data,indent=2,ensure_ascii=False)); return 0
    return 1
if __name__=='__main__': raise SystemExit(main())
