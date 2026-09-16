from __future__ import annotations

import logging
import os
from pathlib import Path


TOOL_TREE_REPO = os.getenv("TOOL_TREE_REPO", "https://github.com/Kakathic/Tool-Tree.git")
TOOL_TREE_REF = os.getenv("TOOL_TREE_REF", "V1.6.0")


def install_tool_tree(root: Path, logger: logging.Logger | None = None) -> Path:
    logger = logger or logging.getLogger("ToolChain")
    checkout = root / ".tool-tree"
    if checkout.exists():
        logger.info("Tool-Tree already present: %s", checkout)
        return checkout
    import subprocess
    subprocess.run(["git", "clone", "--depth", "1", "--branch", TOOL_TREE_REF, TOOL_TREE_REPO, str(checkout)], check=True)
    src_bin = checkout / ".github" / "module" / "bin"
    project_bin = root / "bin" / "linux" / "x86_64"
    project_bin.mkdir(parents=True, exist_ok=True)
    for tool in src_bin.iterdir():
        if tool.is_file() and tool.name not in {"apktool", "apkeditor"}:
            dst = project_bin / tool.name
            if dst.exists() or dst.is_symlink():
                dst.unlink()
            dst.symlink_to(tool.resolve())
    lib = checkout / ".github" / "module" / "lib" / "apktool.jar"
    if lib.exists():
        home_lib = Path.home() / "lib"
        home_lib.mkdir(parents=True, exist_ok=True)
        apktool_link = home_lib / "apktool.jar"
        if apktool_link.exists() or apktool_link.is_symlink():
            apktool_link.unlink()
        apktool_link.symlink_to(lib.resolve())
    os.environ["TOOL_TREE_BIN"] = str(src_bin)
    current = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{src_bin}:{current}"
    logger.info("Tool-Tree %s installed", TOOL_TREE_REF)
    return checkout


def tool_tree_bin(root: Path) -> Path:
    override = os.getenv("TOOL_TREE_BIN")
    if override:
        return Path(override).resolve()
    return (root / ".tool-tree" / ".github" / "module" / "bin").resolve()
