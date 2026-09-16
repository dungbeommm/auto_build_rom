#!/usr/bin/env bash
set -Eeuo pipefail

URL="${1:?ROM URL required}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INPUT="$ROOT/workspace/input"
EXTRACTED="$ROOT/workspace/extracted"
mkdir -p "$INPUT" "$EXTRACTED" "$ROOT/workspace/logs" "$ROOT/workspace/state"

case "${URL%%\?*}" in
  *.tgz|*.tar.gz) OUT="$INPUT/rom.tgz"; FORMAT=tgz ;;
  *.zip)          OUT="$INPUT/rom.zip"; FORMAT=zip ;;
  *)              OUT="$INPUT/rom.bin"; FORMAT=unknown ;;
esac

curl --location --fail --show-error --retry 4 --retry-delay 5 --retry-all-errors --continue-at - --output "$OUT" "$URL"
test -s "$OUT"

case "$FORMAT" in
  tgz)
    rm -rf "$EXTRACTED"
    mkdir -p "$EXTRACTED"
    tar -xzf "$OUT" -C "$EXTRACTED"
    printf '%s\n' "$EXTRACTED"
    ;;
  zip)
    printf '%s\n' "$OUT"
    ;;
  *)
    echo "Unsupported ROM archive: $URL" >&2
    exit 2
    ;;
esac
