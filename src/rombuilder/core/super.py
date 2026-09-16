from __future__ import annotations
import json, re, subprocess, shutil
from pathlib import Path
from .exec import run, require, ToolError

class SuperBuilder:
    def __init__(self, root, logger): self.root=Path(root); self.log=logger
    def dump(self, super_img: Path):
        tool=shutil.which('lpdump') or str(self.root/'bin/linux-x86_64/lpdump')
        require(tool,'lpdump')
        cp=run([tool,'--json',str(super_img)],logger=self.log)
        try: return json.loads(cp.stdout)
        except json.JSONDecodeError as e: raise ToolError('lpdump did not return JSON; use a compatible lpdump build') from e
    def write_layout_template(self, super_img: Path, out: Path):
        data=self.dump(super_img); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(data,indent=2),encoding='utf-8'); return out
