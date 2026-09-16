from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from romauto.detect import inspect, save as save_inventory
from romauto.pipeline import download, package_outputs, push_release
from romauto.plan import RomPlan
from src.core.apk import ApkModEngine
from src.core.tooling import resolve_tooling


def env_for_repo() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    tool_bin = ROOT / ".tool-tree" / ".github" / "module" / "bin"
    if tool_bin.exists():
        env["TOOL_TREE_BIN"] = str(tool_bin)
        env["PATH"] = f"{tool_bin}:{env.get('PATH', '')}"
    return env


def run_base_engine(args: argparse.Namespace) -> int:
    cmd = [sys.executable, "-m", "romauto.run", "--config", args.profile,
           "--stock", str(args.rom_path), "--work-dir", str(args.work_dir),
           "--pack-type", args.pack_type, "--fs-type", args.fs_type,
           "--phases", "system", "framework", "firmware",
           "--enable-diff-report", "--diff-report", str(Path(args.work_dir) / "diff-report.json"),
           "--preflight-report", str(Path(args.work_dir) / "preflight-report.json")]
    if args.port_path:
        cmd += ["--port", str(args.port_path)]
    if args.strict:
        cmd += ["--preflight-strict"]
    return subprocess.run(cmd, cwd=ROOT, env=env_for_repo()).returncode


def run_apk_engine(args: argparse.Namespace) -> int:
    profile = Path(args.apk_profile)
    report = Path(args.work_dir) / "apk-report.json"
    if not profile.exists():
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps({"results": [], "success": True, "skipped": True,
                                      "reason": f"APK profile not found: {profile}"}, indent=2), encoding="utf-8")
        print(f"[APK] No APK profile: {profile}; skipping")
        return 0
    data = json.loads(profile.read_text(encoding="utf-8"))
    jobs = data.get("apps", []) if isinstance(data, dict) else []
    if not jobs:
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps({"results": [], "success": True, "skipped": True,
                                      "reason": "No APK jobs enabled"}, indent=2), encoding="utf-8")
        print("[APK] No jobs enabled; skipping")
        return 0
    class Context: pass
    logger = logging.getLogger("ROM-Auto-APK")
    ctx = Context()
    ctx.target_dir = (ROOT / args.work_dir / "target").resolve()
    ctx.tools = resolve_tooling(ROOT, logger).tools
    result = ApkModEngine(ctx, logger).run_profile(profile)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if result.get("success") else 3


def run_feature_engine(args: argparse.Namespace) -> int:
    from romauto.features import FeatureEngine
    from types import SimpleNamespace
    plan = RomPlan.load(args.profile, stock=str(args.rom_path), port=str(args.port_path) if args.port_path else None)
    requested = [f for f in plan.features if f.enabled]
    report = Path(args.work_dir) / "feature-report.json"
    if not requested:
        report.write_text(json.dumps({"results": [], "changes": [], "success": True}, indent=2), encoding="utf-8")
        return 0
    checkpoint = Path(args.work_dir) / "repack-context.json"
    data = json.loads(checkpoint.read_text(encoding="utf-8")) if checkpoint.exists() else {}
    ctx = SimpleNamespace(target_dir=(ROOT / args.work_dir / "target").resolve(),
                          device_config=data.get("device_config", {}),
                          stock_rom_code=data.get("stock_rom_code", "unknown"))
    engine = FeatureEngine(ctx, ROOT)
    ok = engine.run(requested)
    engine.write_report(report)
    return 0 if ok else 4


def repack(args: argparse.Namespace) -> int:
    cmd = [sys.executable, "-m", "romauto.run", "--config", args.profile,
           "--stock", str(args.rom_path), "--work-dir", str(args.work_dir),
           "--pack-type", args.pack_type, "--fs-type", args.fs_type,
           "--resume-from-packer"]
    return subprocess.run(cmd, cwd=ROOT, env=env_for_repo()).returncode


def main() -> int:
    ap = argparse.ArgumentParser(description="ROM-Auto-Builder complete pipeline")
    ap.add_argument("--rom-url", required=True)
    ap.add_argument("--port-url")
    ap.add_argument("--profile", default="config/profiles/default.json")
    ap.add_argument("--apk-profile", default="config/apk_patches/active.json")
    ap.add_argument("--pack-type", choices=["super", "payload"], default="super")
    ap.add_argument("--fs-type", choices=["erofs", "ext4"], default="erofs")
    ap.add_argument("--work-dir", default="build")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--tag")
    ap.add_argument("--name")
    args = ap.parse_args()
    work = ROOT / args.work_dir
    if work.exists():
        import shutil
        shutil.rmtree(work)
    (work / "input").mkdir(parents=True, exist_ok=True)
    rom_name = Path(args.rom_url.split("?", 1)[0]).name or "rom.zip"
    args.rom_path = download(args.rom_url, work / "input" / rom_name)
    args.port_path = None
    if args.port_url:
        port_name = Path(args.port_url.split("?", 1)[0]).name or "port.zip"
        args.port_path = download(args.port_url, work / "input" / port_name)
    inv = inspect(args.rom_path)
    save_inventory(inv, work / "input-inventory.json")
    if inv.kind == "unknown":
        raise SystemExit("Unsupported/unknown ROM input format")
    print("[1/7] Download: OK")
    print(f"[2/7] Detect: {inv.kind} / {inv.details}")
    print("[3/7] Unpack + initialize")
    if run_base_engine(args) != 0:
        return 2
    print("[4/7] Modify: system + framework + firmware")
    if run_apk_engine(args) != 0:
        return 3
    if run_feature_engine(args) != 0:
        return 4
    print("[5/7] Pack: filesystem + super/payload")
    if repack(args) != 0:
        return 5
    print("[6/7] Archive + SHA256")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    archive = package_outputs(work, args.rom_path, args.name or f"ROM-Auto-{stamp}")
    print("[7/7] Publish")
    if args.push:
        push_release(archive, args.tag or f"rom-auto-{stamp}")
    else:
        print("Push disabled; GitHub Actions artifact will contain release/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
