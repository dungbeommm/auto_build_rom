from __future__ import annotations

import json
import logging
import re
import shutil
from pathlib import Path
from typing import Any


class PatchError(RuntimeError):
    pass


class PatchEngine:
    """Profile-driven file/property patcher for an extracted ROM tree.

    It intentionally uses declarative rules so a ROM-version-specific patch can
    be updated without changing the Python engine.
    """

    def __init__(self, target: Path, repo_root: Path, logger: logging.Logger | None = None):
        self.target = target
        self.repo_root = repo_root
        self.logger = logger or logging.getLogger("PatchEngine")
        self.changes: list[dict[str, Any]] = []

    def _record(self, feature: str, action: str, path: Path, detail: str = "") -> None:
        self.changes.append({"feature": feature, "action": action, "path": str(path.relative_to(self.target)), "detail": detail})

    def copy_tree(self, feature: str, source: Path, rel_dest: str, overwrite: bool = True) -> int:
        if not source.exists():
            raise PatchError(f"Patch source does not exist: {source}")
        dest = self.target / rel_dest
        count = 0
        if source.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
            for p in source.rglob("*"):
                rel = p.relative_to(source)
                out = dest / rel
                if p.is_dir():
                    out.mkdir(parents=True, exist_ok=True)
                else:
                    if overwrite or not out.exists():
                        out.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(p, out)
                        self._record(feature, "copy", out)
                        count += 1
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            if overwrite or not dest.exists():
                shutil.copy2(source, dest)
                self._record(feature, "copy", dest)
                count += 1
        return count

    def delete_glob(self, feature: str, pattern: str) -> int:
        count = 0
        for p in self.target.glob(pattern):
            if p.is_dir():
                shutil.rmtree(p)
            elif p.exists():
                p.unlink()
            self._record(feature, "delete", p)
            count += 1
        return count

    def replace_text(self, feature: str, rel_file: str, replacements: list[dict[str, str]], create: bool = False) -> int:
        p = self.target / rel_file
        if not p.exists():
            if not create:
                raise PatchError(f"File not found for text patch: {p}")
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("", encoding="utf-8")
        text = p.read_text(encoding="utf-8", errors="ignore")
        original = text
        for item in replacements:
            old, new = item["old"], item["new"]
            if item.get("regex"):
                text = re.sub(old, new, text, count=int(item.get("count", 0)))
            else:
                if item.get("count"):
                    text = text.replace(old, new, int(item["count"]))
                else:
                    text = text.replace(old, new)
        if text != original:
            p.write_text(text, encoding="utf-8")
            self._record(feature, "replace", p)
            return 1
        self.logger.warning("No replacement matched in %s", p)
        return 0

    def set_props(self, feature: str, partition: str, values: dict[str, str]) -> int:
        candidates = [
            self.target / partition / "build.prop",
            self.target / partition / "etc" / "build.prop",
            self.target / partition / "system" / "build.prop",
        ]
        prop = next((p for p in candidates if p.exists()), candidates[0])
        prop.parent.mkdir(parents=True, exist_ok=True)
        lines = prop.read_text(encoding="utf-8", errors="ignore").splitlines() if prop.exists() else []
        out = []
        seen: set[str] = set()
        for line in lines:
            if "=" not in line or line.lstrip().startswith("#"):
                out.append(line)
                continue
            k = line.split("=", 1)[0].strip()
            if k in values:
                out.append(f"{k}={values[k]}")
                seen.add(k)
            else:
                out.append(line)
        for k, v in values.items():
            if k not in seen:
                out.append(f"{k}={v}")
        prop.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
        self._record(feature, "set_props", prop, json.dumps(values, ensure_ascii=False, sort_keys=True))
        return len(values)

    def apply_rule_file(self, feature: str, path: Path) -> dict[str, int]:
        data = json.loads(path.read_text(encoding="utf-8"))
        result = {"copy": 0, "delete": 0, "replace": 0, "props": 0}
        for op in data.get("copy", []):
            src = (path.parent / op["source"]).resolve()
            result["copy"] += self.copy_tree(feature, src, op["dest"], op.get("overwrite", True))
        for op in data.get("delete", []):
            result["delete"] += self.delete_glob(feature, op["glob"])
        for op in data.get("replace", []):
            result["replace"] += self.replace_text(feature, op["file"], op["items"], op.get("create", False))
        for op in data.get("props", []):
            result["props"] += self.set_props(feature, op["partition"], op["values"])
        return result

    def write_report(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.changes, ensure_ascii=False, indent=2), encoding="utf-8")
