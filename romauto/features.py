from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

from .bootpatch import BootPatcher
from .patch_engine import PatchEngine, PatchError
from .plan import FeaturePlan


class FeatureEngine:
    """Maps Tool-Tree-like ROM functions to reproducible Python operations."""

    def __init__(self, ctx: Any, repo_root: Path, logger: logging.Logger | None = None):
        self.ctx = ctx
        self.repo_root = repo_root
        self.logger = logger or logging.getLogger("FeatureEngine")
        self.target = Path(ctx.target_dir)
        self.patch = PatchEngine(self.target, repo_root, self.logger)
        self.results: list[dict[str, Any]] = []

    def run(self, features: list[FeaturePlan]) -> bool:
        ok = True
        for f in features:
            if not f.enabled:
                self.results.append({"feature": f.name, "status": "disabled"})
                continue
            try:
                result = self._run_feature(f)
                self.results.append({"feature": f.name, "status": "ok", "result": result})
            except Exception as exc:
                ok = False
                self.results.append({"feature": f.name, "status": "failed", "error": str(exc)})
                self.logger.exception("Feature %s failed", f.name)
                if f.required:
                    raise
        return ok

    def _run_feature(self, f: FeaturePlan) -> dict[str, Any]:
        name = f.name
        o = f.options
        if name in {"rom_cn_patch", "cn_global_patch", "framework_patch_rules", "other_patches"}:
            rule = self.repo_root / o["rule_file"]
            return self.patch.apply_rule_file(name, rule)
        if name in {"add_apps", "app_patches"}:
            source = self.repo_root / o["source_dir"]
            return {"copied": self.patch.copy_tree(name, source, o["dest"])}
        if name == "delete_apps":
            return {"deleted": self.patch.delete_glob(name, o["glob"])}
        if name == "keyboard_unlock":
            # Tool-Tree stores keyboard/IME presentation tweaks as resource/property rules.
            return self.patch.apply_rule_file(name, self.repo_root / o["rule_file"])
        if name in {"boot_patch", "vendor_boot_patch"}:
            img = self.target / "repack_images" / o.get("image", "boot.img" if name == "boot_patch" else "vendor_boot.img")
            overlay = self.repo_root / o["overlay_dir"]
            tool = Path(o.get("magiskboot", str(self.repo_root / ".tool-tree/.github/module/bin/magiskboot")))
            BootPatcher(tool, self.logger).patch(img, overlay)
            return {"image": str(img), "overlay": str(overlay)}
        raise PatchError(f"Unknown feature: {name}")

    def write_report(self, path: Path) -> None:
        import json
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"results": self.results, "changes": self.patch.changes}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
