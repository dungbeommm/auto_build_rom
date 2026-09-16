from __future__ import annotations
import os, shutil, subprocess
from pathlib import Path
class ToolError(RuntimeError): pass

def which_or(path_or_name: str) -> str | None:
    p=Path(path_or_name)
    if p.exists(): return str(p)
    return shutil.which(path_or_name)

def run(cmd: list[str], *, cwd: Path|None=None, logger=None, check=True, timeout=None, env=None) -> subprocess.CompletedProcess:
    if logger: logger.info("$ %s", " ".join(map(str,cmd)))
    cp=subprocess.run(cmd, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    if logger and cp.stdout: logger.debug(cp.stdout.rstrip())
    if check and cp.returncode != 0: raise ToolError(f"Command failed ({cp.returncode}): {' '.join(cmd)}\n{cp.stdout}")
    return cp

def require(path_or_name: str, what: str) -> str:
    found=which_or(path_or_name)
    if not found: raise ToolError(f"Missing required tool: {what} ({path_or_name})")
    return found
