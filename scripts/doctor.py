from __future__ import annotations
import shutil
from pathlib import Path
from romauto.toolchain import TOOL_TREE_REF

ROOT=Path(__file__).resolve().parents[1]
print(f"Project: {ROOT}")
print(f"Tool-Tree pin: {TOOL_TREE_REF}")
for name in ['git','aria2c','java','openssl','zstd','lz4','rsync']:
    print(f"{name:10} -> {shutil.which(name) or 'MISSING'}")
for p in [ROOT/'.tool-tree'/' .github']:
    pass
print('Tool-Tree checkout:', 'OK' if (ROOT/'.tool-tree').exists() else 'not installed')
