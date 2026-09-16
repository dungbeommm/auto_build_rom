from __future__ import annotations

import argparse
import json
import os
import logging
from pathlib import Path
from types import SimpleNamespace

from romauto.features import FeatureEngine
from romauto.plan import FeaturePlan

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    raw = json.loads(os.environ.get("ROMAUTO_FEATURES", "{\"features\":[]}"))
    features = [FeaturePlan(**x) for x in raw.get("features", [])]
    work = Path(os.environ.get("ROMAUTO_WORK_DIR", "build"))
    checkpoint = work / "repack-context.json"
    if not checkpoint.exists():
        raise SystemExit("repack-context.json missing; base workflow did not finish")
    data = json.loads(checkpoint.read_text(encoding="utf-8"))
    ctx = SimpleNamespace(target_dir=work / "target", device_config=data.get("device_config", {}), stock_rom_code=data.get("stock_rom_code", "unknown"))
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    engine = FeatureEngine(ctx, ROOT)
    ok = engine.run(features)
    engine.write_report(work / "feature-report.json")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
