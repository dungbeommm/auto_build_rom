#!/usr/bin/env bash
set -Eeuo pipefail
umask 022
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
: "${ROM_URL:?Set ROM_URL}"
: "${PATCH_PROFILE:=$ROOT_DIR/profiles/all.env}"
: "${WORK_ROOT:=${RUNNER_TEMP:-/sdcard/TREE/auto-rom}}"
: "${OUTPUT_DIR:=$ROOT_DIR/output}"
: "${TOOLTREE_HOME:=/data/data/com.tool.tree/files/home}"
: "${MAX_ROM_BYTES:=15000000000}"
JOB_ID="${GITHUB_RUN_ID:-local}-$(date +%s)"
JOB="$WORK_ROOT/$JOB_ID"; DOWNLOAD="$JOB/download"; EXTRACT="$JOB/extract"; PROJECT="$JOB/project"; REPACK="$JOB/repacked"
mkdir -p "$DOWNLOAD" "$EXTRACT" "$PROJECT" "$REPACK" "$OUTPUT_DIR"
cleanup(){ [[ ${KEEP_WORK:-0} == 1 ]] || rm -rf "$JOB"; }
trap cleanup EXIT

validate_args=("$ROM_URL")
[[ -z ${EXTRA_ALLOWED_HOST:-} ]] || validate_args+=(--allow-host "$EXTRA_ALLOWED_HOST")
python3 "$ROOT_DIR/scripts/validate_url.py" "${validate_args[@]}"
headers="$(curl -fsSIL --max-time 45 "$ROM_URL")"
length="$(printf '%s' "$headers" | awk 'BEGIN{IGNORECASE=1}/^content-length:/{gsub("\\r","");v=$2}END{print v+0}')"
(( length == 0 || length <= MAX_ROM_BYTES )) || { echo "ROM vượt giới hạn $MAX_ROM_BYTES bytes" >&2; exit 10; }
free="$(df -Pk "$WORK_ROOT" | awk 'NR==2{print $4*1024}')"; need=$(( (length>0?length:10000000000)*4 ))
(( free >= need )) || { echo "Thiếu dung lượng: cần xấp xỉ $need bytes, còn $free" >&2; exit 11; }
name="$(python3 -c 'import sys,urllib.parse,os; print(os.path.basename(urllib.parse.urlparse(sys.argv[1]).path) or "rom.tgz")' "$ROM_URL")"
rom="$DOWNLOAD/$name"
echo "[1/7] Download $name ($length bytes)"; curl -fL --retry 5 --retry-all-errors -C - -o "$rom" "$ROM_URL"
echo "[2/7] Verify archive"; tar -tzf "$rom" >/dev/null
echo "[3/7] Extract fastboot ROM"; tar -xzf "$rom" -C "$EXTRACT"
images_dir="$(find "$EXTRACT" -type d -name images -print -quit)"; [[ -n "$images_dir" ]] || { echo 'Không thấy thư mục images trong ROM' >&2; exit 12; }

export HOME="$TOOLTREE_HOME" PATH="$TOOLTREE_HOME/bin:$TOOLTREE_HOME/termux/bin:$PATH"
UNPACK="$TOOLTREE_HOME/bin/unpack_img"; REPACK_BIN="$TOOLTREE_HOME/bin/repack_img"
[[ -x "$UNPACK" && -x "$REPACK_BIN" ]] || { echo 'Thiếu unpack_img/repack_img trong Tool-Tree' >&2; exit 13; }
partitions=(system system_ext product vendor mi_ext boot vendor_boot)
echo "[4/7] Unpack partitions"
for p in "${partitions[@]}"; do
  img="$images_dir/$p.img"; [[ -f "$img" ]] || continue
  echo "  unpack $p"; "$UNPACK" -i "$img" -p "$p" -o "$PROJECT"
done
PROJECT_DIR="$PROJECT" PATCH_PROFILE="$PATCH_PROFILE" TOOLTREE_HOME="$TOOLTREE_HOME" "$ROOT_DIR/scripts/tooltree_adapter.sh"

echo "[5/7] Repack partitions"
for p in "${partitions[@]}"; do
  [[ -d "$PROJECT/$p" ]] || continue
  "$REPACK_BIN" -i "$PROJECT/$p" -o "$REPACK"
  built="$(find "$REPACK" -maxdepth 1 -type f -name "$p.img" -print -quit)"
  [[ -n "$built" ]] || { echo "Không tạo được $p.img" >&2; exit 14; }
  cp -f "$built" "$images_dir/$p.img"
done

base="${name%.tar.gz}"; base="${base%.tgz}"; out="$OUTPUT_DIR/${base}_MODDED.tgz"
echo "[6/7] Package $out"; top="$(find "$EXTRACT" -mindepth 1 -maxdepth 1 -print -quit)"
if [[ -d "$top" && $(find "$EXTRACT" -mindepth 1 -maxdepth 1 | wc -l) -eq 1 ]]; then tar -C "$EXTRACT" -czf "$out" "$(basename "$top")"; else tar -C "$EXTRACT" -czf "$out" .; fi
(cd "$OUTPUT_DIR" && sha256sum "$(basename "$out")") > "$out.sha256"
python3 "$ROOT_DIR/scripts/write_manifest.py" --url "$ROM_URL" --input "$rom" --output "$out" --profile "$PATCH_PROFILE" > "$out.manifest.json"
echo "[7/7] Done"; ls -lh "$out" "$out.sha256" "$out.manifest.json"
