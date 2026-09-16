from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class FeaturePlan:
    name: str
    enabled: bool = True
    required: bool = False
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class RomPlan:
    stock: str
    port: str | None
    pack_type: str = "super"
    fs_type: str = "erofs"
    device: str | None = None
    features: list[FeaturePlan] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, path: str | Path, stock: str | None = None, port: str | None = None) -> "RomPlan":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        feats = [FeaturePlan(**item) for item in data.get("features", [])]
        return cls(
            stock=stock or data["stock"],
            port=port if port is not None else data.get("port"),
            pack_type=data.get("pack_type", "super"),
            fs_type=data.get("fs_type", "erofs"),
            device=data.get("device"),
            features=feats,
            extra=data.get("extra", {}),
        )
