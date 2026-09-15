#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.."&&pwd)"; : "${ROM_URL:?ROM_URL required}"; PROFILE="${PROFILE:-$ROOT/profiles/all.env}"; source "$PROFILE"; export $(grep -E '^[A-Z0-9_]+=' "$PROFILE"|cut -d= -f1)
WORK="${RUNNER_TEMP:-/tmp}/rommod"; ROM="$WORK/source.tgz"; TREE="$WORK/tree"; AIT="$ROOT/vendor/android-image-tools"; OUT="$ROOT/output"; mkdir -p "$TREE" "$OUT"
python3 "$ROOT/scripts/validate_url.py" "$ROM_URL"
echo '[1/7] Download'; curl -fL --retry 5 --retry-all-errors -C - -o "$ROM" "$ROM_URL"
echo '[2/7] Verify/extract'; tar -tzf "$ROM">/dev/null; tar -xzf "$ROM" -C "$TREE"; rm -f "$ROM"
IMGDIR="$(find "$TREE" -type d -name images -print -quit)"; test -n "$IMGDIR" || { echo 'Không thấy images/' >&2;exit 4; }
REPORT="$WORK/patch-report.json"; echo '{"changes":[],"unsupported":[]}' > "$REPORT"
export PATH="$AIT/.bin:$PATH"
process_image(){ local img="$1" name="$2" ext="$WORK/extracted/$name" conf="$WORK/$name.conf"; mkdir -p "$(dirname "$ext")"; cat > "$conf" <<EOF
ACTION=unpack
INPUT_IMAGE=$img
EXTRACT_DIR=$ext
EOF
sudo -E bash "$AIT/android_image_tools.sh" --conf="$conf" --quiet
python3 "$ROOT/scripts/patch_engine.py" --root "$ext" --apps "$ROOT/assets/apps" --report "$REPORT"
local fs; fs="$(awk -F= '$1=="FILESYSTEM_TYPE"{print $2}' "$ext/.repack_info/metadata.txt"|tail -1)"; [[ "$fs" =~ ^(erofs|ext4)$ ]]||fs=erofs
cat > "$conf" <<EOF
ACTION=repack
SOURCE_DIR=$ext
OUTPUT_IMAGE=$img.new
FILESYSTEM=$fs
COMPRESSION_MODE=lz4hc
COMPRESSION_LEVEL=9
CREATE_SPARSE_IMAGE=false
MODE=flexible
EXT4_OVERHEAD_PERCENT=5
EOF
sudo -E bash "$AIT/android_image_tools.sh" --conf="$conf" --quiet; mv "$img.new" "$img"; rm -rf "$ext"; }
if [[ -f "$IMGDIR/super.img" ]];then
 echo '[3/7] Unpack super'; SESSION="$WORK/super"; mkdir -p "$SESSION/logical"; sudo -E bash "$AIT/.bin/super-tools.sh" unpack "$IMGDIR/super.img" "$SESSION/logical" --no-banner
 IFS=, read -ra parts<<<"$TARGET_PARTITIONS"; for p in "${parts[@]}";do [[ -f "$SESSION/logical/$p.img" ]]&&process_image "$SESSION/logical/$p.img" "$p";done
 echo '[5/7] Repack super'; sudo -E bash "$AIT/.bin/super-tools.sh" repack "$SESSION/logical" "$IMGDIR/super.img.new" --no-banner; mv "$IMGDIR/super.img.new" "$IMGDIR/super.img"
else
 echo '[3/7] Individual images'; IFS=, read -ra parts<<<"$TARGET_PARTITIONS";for p in "${parts[@]}";do [[ -f "$IMGDIR/$p.img" ]]&&process_image "$IMGDIR/$p.img" "$p";done
fi
cp "$REPORT" "$OUT/patch-report.json"; top="$(find "$TREE" -mindepth 1 -maxdepth 1 -type d -print -quit)"; name="$(basename "${ROM_URL%%\?*}")";name="${name%.tgz}";name="${name%.tar.gz}_MODDED.tgz"
echo '[6/7] Package'; tar -C "$TREE" -czf "$OUT/$name" "$(basename "$top")"; (cd "$OUT"&&sha256sum "$name")>"$OUT/$name.sha256"
echo '[7/7] Done'; ls -lh "$OUT/$name"
