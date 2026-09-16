from __future__ import annotations
import json
from pathlib import Path

class State:
    def __init__(self, path: Path):
        self.path = path; self.data = {}
        if path.exists():
            self.data = json.loads(path.read_text(encoding="utf-8"))
    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    def done(self, stage: str) -> bool: return self.data.get("stages", {}).get(stage) is True
    def mark(self, stage: str, **meta):
        self.data.setdefault("stages", {})[stage] = True
        if meta: self.data.setdefault("meta", {}).setdefault(stage, {}).update(meta)
        self.save()
    def clear(self): self.data = {}; self.save()
