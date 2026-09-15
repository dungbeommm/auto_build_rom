#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path

PART_SIZE = 1_900 * 1024 * 1024


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="out")
    parser.add_argument("--output", default="release")
    args = parser.parse_args()
    source, output = Path(args.source), Path(args.output)
    shutil.rmtree(output, ignore_errors=True)
    output.mkdir(parents=True)
    artifacts = sorted(p for p in source.glob("*.zip") if p.is_file())
    if not artifacts:
        raise SystemExit("No ROM ZIP found in out/")
    manifest = {"schema": 1, "artifacts": []}
    for artifact in artifacts:
        entry = {"name": artifact.name, "size": artifact.stat().st_size, "sha256": sha256(artifact), "parts": []}
        with artifact.open("rb") as handle:
            index = 0
            while True:
                data = handle.read(PART_SIZE)
                if not data:
                    break
                name = f"{artifact.name}.part-{index:03d}"
                part = output / name
                part.write_bytes(data)
                entry["parts"].append({"name": name, "size": len(data), "sha256": sha256(part)})
                index += 1
        manifest["artifacts"].append(entry)
    (output / "release-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (output / "JOIN.py").write_text('''#!/usr/bin/env python3\nimport hashlib,json,pathlib\nr=pathlib.Path(__file__).parent;m=json.loads((r/"release-manifest.json").read_text())\nfor a in m["artifacts"]:\n o=r/a["name"]\n with o.open("wb") as w:\n  for p in a["parts"]: w.write((r/p["name"]).read_bytes())\n h=hashlib.sha256(o.read_bytes()).hexdigest()\n if h!=a["sha256"]: raise SystemExit("checksum failed: "+a["name"])\n print("created",o)\n''', encoding="utf-8")
    os.chmod(output / "JOIN.py", 0o755)
    for report in ("build/preflight-report.json", "build/diff-report.json", "porting.log"):
        path = Path(report)
        if path.exists():
            shutil.copy2(path, output / path.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
