from __future__ import annotations
import json, re, shutil
from dataclasses import dataclass
from pathlib import Path

class RecipeError(RuntimeError): pass
@dataclass
class Change:
    file: Path; description: str; count: int

class RecipeEngine:
    """Fail-closed patch engine. A recipe must prove its target pattern before changing bytes/text."""
    def __init__(self, config, logger): self.config=config; self.log=logger
    def apply_feature(self, feature: str, target: Path, decoded: Path|None):
        recipes=self.config.recipes.get('recipes',{}).get(feature)
        if not recipes: raise RecipeError(f'No exact recipe registered for {feature!r}; refusing to guess for {target.name}')
        if not decoded or not decoded.exists(): raise RecipeError(f'Decoded target required for {feature}: {target}')
        changes=[]
        for op in recipes.get('operations',[]):
            rel=op['file']; path=decoded/rel
            if not path.exists(): raise RecipeError(f'Recipe target missing: {feature}: {rel}')
            text=path.read_text(encoding='utf-8', errors='strict')
            before=text
            if op['type']=='replace_text':
                pattern=op['find']; replacement=op['replace']; count=int(op.get('count',1))
                n=len(re.findall(re.escape(pattern),text))
                if n < int(op.get('min_matches',1)): raise RecipeError(f'Recipe match failed for {feature}: {rel}; found {n}')
                text=text.replace(pattern,replacement,count)
                path.write_text(text,encoding='utf-8'); changes.append(Change(path,op.get('description',feature),n))
            elif op['type']=='replace_regex':
                pat=op['pattern']; n=len(re.findall(pat,text,flags=re.MULTILINE))
                if n < int(op.get('min_matches',1)): raise RecipeError(f'Recipe regex match failed for {feature}: {rel}; found {n}')
                text=re.sub(pat,op['replace'],text,count=int(op.get('count',0)),flags=re.MULTILINE)
                path.write_text(text,encoding='utf-8'); changes.append(Change(path,op.get('description',feature),n))
            else: raise RecipeError(f'Unsupported recipe op: {op.get("type")}')
        return changes
