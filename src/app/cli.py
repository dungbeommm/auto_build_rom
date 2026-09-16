"""Command-line interface for the single-ROM modification pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

VALID_PHASES = ("system", "apk", "framework", "firmware", "repack")

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="HyperOS ROM Modifier")
    parser.add_argument("--rom", required=True, help="Path/URL to the ROM (zip/payload/directory)")
    parser.add_argument("--ksu", action="store_true", help="Inject KernelSU when enabled by the device config")
    parser.add_argument("--work-dir", default="build", help="Working directory (default: build)")
    parser.add_argument("--clean", action="store_true", help="Clean working directory before starting")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--pack-type", choices=["super", "payload"], default=None, help="Output: super or payload")
    parser.add_argument("--fs-type", choices=["erofs", "ext4"], default=None, help="Filesystem type for repacking")
    parser.add_argument("--custom-avb-chain", action="store_true", help="Enable custom AVB chain generation")
    parser.add_argument("--avb-key", type=Path, help="Path to custom AVB signing key")
    parser.add_argument("--resume-from-packer", action="store_true", help="Resume from existing workspace and repack only")
    parser.add_argument("--eu-bundle", help="Optional EU localization bundle ZIP")
    parser.add_argument("--preflight-only", action="store_true", help="Run preflight checks only")
    parser.add_argument("--skip-preflight", action="store_true", help="Skip preflight checks")
    parser.add_argument("--preflight-strict", action="store_true", help="Treat risks as failures")
    parser.add_argument("--preflight-report", default="build/preflight-report.json")
    parser.add_argument("--enable-snapshots", action="store_true")
    parser.add_argument("--snapshot-dir", default=None)
    parser.add_argument("--rollback-to-snapshot", default=None)
    parser.add_argument("--enable-diff-report", action="store_true")
    parser.add_argument("--diff-report", default="build/diff-report.json")
    parser.add_argument("--phases", nargs="+", help="Phases: system, apk, framework, firmware, repack")
    parser.add_argument("--cache-dir", default=".cache/roms", help="ROM cache directory")
    parser.add_argument("--no-cache", action="store_true", help="Disable cache")
    parser.add_argument("--enable-partition-cache", action="store_true", help="Enable partition-level cache")
    parser.add_argument("--clear-cache", action="store_true", help="Clear cache before starting")
    parser.add_argument("--show-cache-stats", action="store_true", help="Show cache statistics and exit")
    return parser

def normalize_phases(phases: Sequence[str] | None) -> list[str] | None:
    if not phases:
        return None
    return [part.strip() for phase in phases for part in phase.split(",") if part.strip()]

def _is_remote_input(value: str | None) -> bool:
    return bool(value) and value.lower().startswith(("http://", "https://"))

def _validate_local_input_path(parser, value: str | None, label: str) -> None:
    if not value or _is_remote_input(value):
        return
    resolved=Path(value).expanduser().resolve()
    if not resolved.exists():
        parser.error(f"--{label} path does not exist: {resolved}")

def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser=build_parser(); args=parser.parse_args(argv); args.phases=normalize_phases(args.phases)
    if args.phases:
        invalid=[p for p in args.phases if p not in VALID_PHASES]
        if invalid:
            parser.error(f"invalid phase(s): {', '.join(invalid)}")
    _validate_local_input_path(parser,args.rom,"rom")
    _validate_local_input_path(parser,args.eu_bundle,"eu-bundle")
    return args
