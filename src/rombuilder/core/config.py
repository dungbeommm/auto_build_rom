from __future__ import annotations
import json
from pathlib import Path
class Config:
    def __init__(self, root: Path):
        self.root=root
        self.targets=json.loads((root/'config/targets.json').read_text(encoding='utf-8'))
        self.mods=json.loads((root/'config/mods.json').read_text(encoding='utf-8'))
        self.recipes=json.loads((root/'config/recipes.json').read_text(encoding='utf-8'))
