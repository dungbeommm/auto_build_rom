"""Bootstrap helpers for the HyperOS ROM modification workflow."""

from __future__ import annotations

import json
import logging
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from src.core.cache_manager import RomCacheManager


@dataclass
class CacheBootstrapResult:
    """Result of bootstrapping cache state from CLI arguments."""

    cache_manager: RomCacheManager | None
    exit_code: int | None = None


def setup_logging(level: int = logging.INFO) -> None:
    """Configure CLI logging for the ROM modification workflow."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("rom_modifier.log", mode="w"),
        ],
    )


def clean_work_dir(work_dir: Path, logger: logging.Logger) -> None:
    """Remove and recreate the working directory."""
    if work_dir.exists():
        logger.warning(f"Cleaning working directory: {work_dir}")
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)


def initialize_cache_manager(
    args, logger: logging.Logger
) -> CacheBootstrapResult:
    """Create and optionally operate on the cache manager from CLI flags."""
    if args.no_cache:
        return CacheBootstrapResult(cache_manager=None)

    cache_manager = RomCacheManager(
        args.cache_dir,
        cache_partitions=args.enable_partition_cache,
    )

    if args.show_cache_stats:
        print(json.dumps(cache_manager.get_cache_info(), indent=2))
        return CacheBootstrapResult(cache_manager=cache_manager, exit_code=0)

    if args.clear_cache:
        cache_manager.clear_all()
        logger.info("Cache cleared")

    return CacheBootstrapResult(cache_manager=cache_manager)
