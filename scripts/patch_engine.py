#!/usr/bin/env python3
import argparse
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path


def enabled(name: str) -> bool:
    return os.getenv(name, "0") == "1"


def set_property(path: Path, key: str, value: str) -> bool:
    try:
        source = path.read_text(encoding="utf-8", errors="surrogateescape")
    except (OSError, UnicodeError):
        return False
    expression = re.compile(rf"(?m)^[# ]*{re.escape(key)}=.*$")
    updated = expression.sub(f"{key}={value}", source) if expression.search(source) else source.rstrip() + f"\n{key}={value}\n"
    if updated == source:
        return False
    path.write_text(updated, encoding="utf-8", errors="surrogateescape")
    return True


def load_report(path: Path) -> dict:
    if path.exists():
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(report, dict):
                report.setdefault("runs", [])
                report.setdefault("unsupported", [])
                return report
        except (OSError, json.JSONDecodeError):
            pass
    return {"schema": 1, "created_at": time.strftime("%FT%TZ", time.gmtime()), "runs": [], "unsupported": []}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--partition", required=True)
    parser.add_argument("--apps", required=True)
    parser.add_argument("--plugins", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        raise SystemExit(f"Missing extracted partition: {root}")
    report_path = Path(args.report)
    report = load_report(report_path)
    changes = []
    unsupported = []
    properties = [p for p in root.rglob("*") if p.is_file() and p.name in {"build.prop", "default.prop", "system.prop"}]

    def prop(group: str, key: str, value: str) -> None:
        count = sum(set_property(path, key, value) for path in properties)
        changes.append({"group": group, "rule": f"{key}={value}", "files": count})

    if enabled("PATCH_FRAMEWORK"):
        prop("framework", "ro.control_privapp_permissions", os.getenv("PRIVAPP_MODE", "log"))
        unsupported.extend([
            "framework: APK signature verification needs a device-specific open smali rule",
            "framework: Kaorios Toolbox patch is not available as open Linux-native rules",
        ])
    if enabled("PATCH_CN_ROM"):
        prop("cn_rom", "ro.com.google.clientidbase", "android-xiaomi")
        prop("cn_rom", "persist.sys.miui_optimization", "false")
        prop("cn_rom", "ro.miui.region", "GLOBAL")
        for path in root.rglob("cn.google.services.xml"):
            destination = path.with_suffix(path.suffix + ".disabled")
            try:
                path.rename(destination)
                changes.append({"group": "cn_rom", "rule": "disable cn.google.services.xml", "files": 1})
            except OSError:
                pass
    if enabled("PATCH_KEYBOARD"):
        prop("keyboard", "ro.com.google.ime.theme_id", "5")
        prop("keyboard", "persist.sys.default_ime", os.getenv("KEYBOARD_PACKAGE", "com.google.android.inputmethod.latin"))
        unsupported.append("keyboard: MIUI SystemUI/JAR smali patch needs an explicit open rule")
    if enabled("PATCH_OTHERS"):
        prop("other", "persist.vendor.dfps.level", "0")
        prop("other", "persist.sys.display.refresh_rate", "120")
        prop("other", "persist.sys.allow_screenshot", "1")
        unsupported.append("other: window/FPS method patches vary by HyperOS build")
    if enabled("PATCH_APPS"):
        plugin_count = 0
        plugin_dir = Path(args.plugins)
        if plugin_dir.is_dir():
            for plugin in sorted(plugin_dir.glob("*.py")):
                subprocess.run(["python3", str(plugin), str(root), args.partition], check=True)
                plugin_count += 1
        changes.append({"group": "app_patches", "rule": "external app patch hooks", "files": plugin_count})
        if plugin_count == 0:
            unsupported.append("apps: no open per-version APK smali hooks installed")
    if enabled("ADD_APPS"):
        source = Path(args.apps) / args.partition.removesuffix("_a").removesuffix("_b")
        install_root = root / "app"
        if not install_root.parent.exists() and (root / "system").is_dir():
            install_root = root / "system" / "app"
        count = 0
        if source.is_dir():
            install_root.mkdir(parents=True, exist_ok=True)
            for app_dir in sorted(source.iterdir()):
                if app_dir.is_dir():
                    shutil.copytree(app_dir, install_root / app_dir.name, dirs_exist_ok=True)
                    count += 1
        changes.append({"group": "add_apps", "rule": "copy bundled system apps", "files": count})
    if enabled("PATCH_BOOT"):
        unsupported.append("boot/vendor_boot: disabled until a reproducible Linux boot-image rule is supplied")

    report["runs"].append({"partition": args.partition, "changes": changes})
    for item in unsupported:
        tagged = {"partition": args.partition, "reason": item}
        if tagged not in report["unsupported"]:
            report["unsupported"].append(tagged)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"partition": args.partition, "rules": len(changes), "unsupported": len(unsupported)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
