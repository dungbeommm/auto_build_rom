#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 "$ROOT/main.py" doctor || true
for x in lpunpack lpmake lpdump apktool; do command -v "$x" || true; done
