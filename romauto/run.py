from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
from pathlib import Path

from .plan import RomPlan
from .toolchain import install_tool_tree, tool_tree_bin

ROOT = Path(__file__).resolve().parents[1]


def _cli(extra: list[str]) -> int:
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(ROOT))
    return subprocess.run(["python", "main.py", *extra], cwd=ROOT, env=env, check=False).returncode


def main() -> int:
    ap = argparse.ArgumentParser(description="GitHub-friendly HyperOS ROM automation wrapper")
    ap.add_argument("--config", default="config/profiles/default.json")
    ap.add_argument("--stock", required=False)
    ap.add_argument("--port", required=False)
    ap.add_argument("--work-dir", default="build")
    ap.add_argument("--device")
    ap.add_argument("--pack-type", choices=["super", "payload"])
    ap.add_argument("--fs-type", choices=["erofs", "ext4"])
    ap.add_argument("--tool-tree", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    logger = logging.getLogger("romauto")

    if args.tool_tree:
        install_tool_tree(ROOT, logger)
    tbin = tool_tree_bin(ROOT)
    env_path = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{tbin}:{env_path}" if str(tbin) not in env_path.split(":") else env_path
    stock = args.stock or None
    plan = RomPlan.load(args.config, stock=stock, port=args.port)
    if not args.port:
        plan.port = None
    if args.device:
        plan.device = args.device
    if args.pack_type:
        plan.pack_type = args.pack_type
    if args.fs_type:
        plan.fs_type = args.fs_type

    extra = [
        "--stock", plan.stock,
        "--work-dir", args.work_dir,
        "--clean",
        "--pack-type", plan.pack_type,
        "--fs-type", plan.fs_type,
        "--enable-diff-report",
        "--diff-report", f"{args.work_dir}/diff-report.json",
        "--preflight-report", f"{args.work_dir}/preflight-report.json",
    ]
    if plan.port:
        extra += ["--port", plan.port]
    code = _cli(extra)
    if code != 0:
        return code

    # The engine has already extracted/modified/repacked. Feature hooks that need
    # the final target run only when requested, then a second repack is executed.
    requested = [f for f in plan.features if f.enabled]
    if requested:
        hook = ROOT / "scripts" / "apply_features.py"
        payload = json.dumps({"features": [f.__dict__ for f in requested]})
        env = os.environ.copy()
        env["ROMAUTO_FEATURES"] = payload
        env["ROMAUTO_WORK_DIR"] = args.work_dir
        code = subprocess.run(["python", str(hook), "--config", args.config], cwd=ROOT, env=env, check=False).returncode
        if code != 0:
            return code
        # Re-run only repacking from checkpoint after feature mutations.
        code = _cli([
            "--stock", plan.stock,
            "--work-dir", args.work_dir,
            "--pack-type", plan.pack_type,
            "--fs-type", plan.fs_type,
            "--resume-from-packer",
        ])
    return code


if __name__ == "__main__":
    raise SystemExit(main())
