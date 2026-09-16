from __future__ import annotations
import json
from pathlib import Path
class State:
    def __init__(self,path):
        self.path=Path(path); self.data={}
        if self.path.exists():
            try: self.data=json.loads(self.path.read_text(encoding='utf-8'))
            except Exception: self.data={}
    def save(self): self.path.parent.mkdir(parents=True,exist_ok=True); tmp=self.path.with_suffix('.tmp'); tmp.write_text(json.dumps(self.data,indent=2,ensure_ascii=False,sort_keys=True),encoding='utf-8'); tmp.replace(self.path)
    def done(self,stage): return bool(self.data.get('stages',{}).get(stage,False))
    def mark(self,stage,**meta): self.data.setdefault('stages',{})[stage]=True; self.data.setdefault('meta',{}).setdefault(stage,{}).update(meta); self.save()
    def clear(self): self.data={}; self.save()
