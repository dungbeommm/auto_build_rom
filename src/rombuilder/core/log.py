from __future__ import annotations
import logging
from pathlib import Path

def setup_logging(path: Path, verbose: bool = False) -> logging.Logger:
    path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("rombuilder")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    fh = logging.FileHandler(path, encoding="utf-8")
    fh.setFormatter(fmt); fh.setLevel(logging.DEBUG); logger.addHandler(fh)
    sh = logging.StreamHandler(); sh.setFormatter(fmt); sh.setLevel(logging.DEBUG if verbose else logging.INFO); logger.addHandler(sh)
    return logger
