from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from fnmatch import fnmatch
from collections import defaultdict
@dataclass(frozen=True)
class Requirement:
    feature: str
    patterns: tuple[str,...]
    kind: str

def requirements(config, features: list[str]) -> list[Requirement]:
    out=[]
    catalog=config.mods['features']
    target_index=[]
    for kind,entries in config.targets.items():
        for _,meta in entries.items():
            target_index.append((kind,meta))
    for f in features:
        if f not in catalog: raise ValueError(f'Unknown feature: {f}')
        wanted=set(catalog[f].get('targets',[]))
        for kind,meta in target_index:
            if f in meta.get('features',[]):
                wanted.update(meta.get('patterns',[]))
        for target_name in wanted:
            matches=[]
            for kind,meta in target_index:
                for pat in meta.get('patterns',[]):
                    if target_name==pat or target_name.lower()==pat.lower(): matches.append(pat)
            if not matches: matches=[target_name]
            ext='apk' if any(p.lower().endswith('.apk') for p in matches) else 'jar'
            out.append(Requirement(f, tuple(dict.fromkeys(matches)), ext))
    dedup={ (r.kind,r.patterns):r for r in out }
    return list(dedup.values())

def locate(roots: list[Path], requirements_: list[Requirement]):
    found=[]; missing=[]
    files=[]
    for root in roots:
        if root.exists(): files += [p for p in root.rglob('*') if p.is_file()]
    for r in requirements_:
        hit=None
        for pat in r.patterns:
            for p in files:
                if fnmatch(p.name, pat) or fnmatch(p.name.lower(), pat.lower()): hit=p; break
            if hit: break
        (found if hit else missing).append((r,hit))
    return found,missing
