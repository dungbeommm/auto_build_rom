#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
: "${ROM_URL:?ROM_URL required}"
PROFILE="${PROFILE:-$ROOT/profiles/all.env}"
[[ -f "$PROFILE" ]] || { echo "Profile not found: $PROFILE" >&2; exit 2; }
set -a
# shellcheck disable=SC1090
source "$PROFILE"
set +a
: "${TARGET_PARTITIONS:=system,system_ext,product,vendor,mi_ext}"

WORK="${RUNNER_TEMP:-/tmp}/rommod"
ROM="$WORK/source.tgz"
TREE="$WORK/tree"
AIT="$ROOT/vendor/android-image-tools"
OUT="$ROOT/output"
REPORT="$WORK/patch-report.json"
rm -rf "$WORK" "$OUT"
mkdir -p "$TREE" "$OUT" "$WORK/extracted"

python3 "$ROOT/scripts/validate_url.py" "$ROM_URL"
HEADERS="$WORK/headers.txt"
EFFECTIVE_URL="$(curl --proto '=https' --proto-redir '=https' -fsSIL --max-time 60 -D "$HEADERS" -o /dev/null -w '%{url_effective}' "$ROM_URL")"
python3 "$ROOT/scripts/validate_url.py" "$EFFECTIVE_URL"
CONTENT_LENGTH="$(awk 'BEGIN{IGNORECASE=1}/^content-length:/{gsub("\r",""); value=$2}END{print value+0}' "$HEADERS")"
FREE_BYTES="$(df -PB1 "$WORK" | awk 'NR==2{print $4}')"
if (( CONTENT_LENGTH > 0 )); then
    MINIMUM=$((CONTENT_LENGTH * 2 + 8 * 1024 * 1024 * 1024))
    (( FREE_BYTES >= MINIMUM )) || {
        echo "Insufficient disk: free=$FREE_BYTES, estimated minimum=$MINIMUM" >&2
        exit 3
    }
fi

echo "[1/7] Download ($CONTENT_LENGTH bytes)"
curl --proto '=https' --proto-redir '=https' -fL --retry 5 --retry-all-errors -C - -o "$ROM" "$ROM_URL"
ACTUAL_SIZE="$(stat -c %s "$ROM")"
if (( CONTENT_LENGTH > 0 && ACTUAL_SIZE != CONTENT_LENGTH )); then
    echo "Downloaded size mismatch: expected=$CONTENT_LENGTH actual=$ACTUAL_SIZE" >&2
    exit 4
fi

echo '[2/7] Validate and extract archive'
python3 "$ROOT/scripts/safe_tar.py" "$ROM"
tar -xzf "$ROM" -C "$TREE"
rm -f "$ROM"
IMGDIR="$(find "$TREE" -type d -name images -print -quit)"
[[ -n "$IMGDIR" ]] || { echo 'No images/ directory found in ROM' >&2; exit 5; }
printf '{"schema":1,"runs":[],"unsupported":[]}\n' > "$REPORT"
export PATH="$AIT/.bin:$PATH"

process_image() {
    local image="$1" partition="$2"
    local extracted="$WORK/extracted/$partition" config="$WORK/$partition.conf"
    rm -rf "$extracted" "$image.new" "$image.sparse.new"
    mkdir -p "$(dirname "$extracted")"
    cat > "$config" <<EOF
ACTION=unpack
INPUT_IMAGE=$image
EXTRACT_DIR=$extracted
EOF
    echo "[unpack] $partition"
    sudo -E bash "$AIT/.bin/unpack-erofs.sh" "$image" "$extracted" --no-banner --quiet
    [[ -f "$extracted/.repack_info/metadata.txt" ]] || {
        echo "Missing repack metadata for $partition" >&2
        exit 6
    }
    python3 "$ROOT/scripts/patch_engine.py" \
        --root "$extracted" \
        --partition "$partition" \
        --apps "$ROOT/assets/apps" \
        --plugins "$ROOT/plugins/app-patches" \
        --report "$REPORT"
    local filesystem
    filesystem="$(awk -F= '$1=="FILESYSTEM_TYPE"{print $2}' "$extracted/.repack_info/metadata.txt" | tail -1)"
    [[ "$filesystem" =~ ^(erofs|ext4)$ ]] || {
        echo "Unsupported filesystem for $partition: $filesystem" >&2
        exit 7
    }
    cat > "$config" <<EOF
ACTION=repack
SOURCE_DIR=$extracted
OUTPUT_IMAGE=$image.new
FILESYSTEM=$filesystem
COMPRESSION_MODE=lz4hc
COMPRESSION_LEVEL=9
CREATE_SPARSE_IMAGE=false
MODE=flexible
EXT4_OVERHEAD_PERCENT=5
EOF
    echo "[repack] $partition ($filesystem)"
    repack_args=(--fs "$filesystem" --no-banner --quiet)
    if [[ "$filesystem" == erofs ]]; then
        repack_args+=(--erofs-compression lz4hc --erofs-level 9)
    else
        repack_args+=(--ext4-mode flexible --ext4-overhead-percent 5)
    fi
    sudo -E bash "$AIT/.bin/repack-erofs.sh" "$extracted" "$image.new" "${repack_args[@]}"
    [[ -s "$image.new" ]] || { echo "Repack did not create $image.new" >&2; exit 8; }
    mv -f "$image.new" "$image"
    rm -rf "$extracted"
}

find_partition_image() {
    local directory="$1" partition="$2" candidate
    for candidate in "$directory/$partition.img" "$directory/${partition}_a.img"; do
        [[ -f "$candidate" ]] && { printf '%s\n' "$candidate"; return 0; }
    done
    return 1
}

IFS=',' read -r -a PARTITIONS <<< "$TARGET_PARTITIONS"
if [[ -f "$IMGDIR/super.img" ]]; then
    echo '[3/7] Unpack super image'
    SESSION="$WORK/super"
    mkdir -p "$SESSION/logical"
    sudo -E bash "$AIT/.bin/super-tools.sh" unpack "$IMGDIR/super.img" "$SESSION/logical" --no-banner
    PROCESSED=0
    for partition in "${PARTITIONS[@]}"; do
        partition="${partition//[[:space:]]/}"
        if image="$(find_partition_image "$SESSION/logical" "$partition")"; then
            process_image "$image" "$(basename "$image" .img)"
            PROCESSED=$((PROCESSED + 1))
        else
            echo "[skip] logical partition not found: $partition"
        fi
    done
    (( PROCESSED > 0 )) || { echo 'No requested logical partitions were found' >&2; exit 9; }
    echo '[5/7] Repack super image'
    sudo -E bash "$AIT/.bin/super-tools.sh" repack "$SESSION/logical" "$IMGDIR/super.img.new" --no-banner
    [[ -s "$IMGDIR/super.img.new" ]] || { echo 'super.img repack failed' >&2; exit 10; }
    mv -f "$IMGDIR/super.img.new" "$IMGDIR/super.img"
else
    echo '[3/7] Process individual images'
    PROCESSED=0
    for partition in "${PARTITIONS[@]}"; do
        partition="${partition//[[:space:]]/}"
        if image="$(find_partition_image "$IMGDIR" "$partition")"; then
            process_image "$image" "$(basename "$image" .img)"
            PROCESSED=$((PROCESSED + 1))
        else
            echo "[skip] image not found: $partition"
        fi
    done
    (( PROCESSED > 0 )) || { echo 'No requested partition images were found' >&2; exit 11; }
fi

cp "$REPORT" "$OUT/patch-report.json"
URL_PATH="${ROM_URL%%\?*}"
SOURCE_NAME="$(basename "$URL_PATH")"
case "$SOURCE_NAME" in
    *.tar.gz) BASE="${SOURCE_NAME%.tar.gz}" ;;
    *.tgz) BASE="${SOURCE_NAME%.tgz}" ;;
    *) BASE="$SOURCE_NAME" ;;
esac
OUTPUT_NAME="${BASE}_MODDED.tgz"
echo '[6/7] Package ROM'
mapfile -t TOP_ITEMS < <(find "$TREE" -mindepth 1 -maxdepth 1 -printf '%f\n')
if (( ${#TOP_ITEMS[@]} == 1 )); then
    tar -C "$TREE" -czf "$OUT/$OUTPUT_NAME" "${TOP_ITEMS[0]}"
else
    tar -C "$TREE" -czf "$OUT/$OUTPUT_NAME" .
fi
(
    cd "$OUT"
    sha256sum "$OUTPUT_NAME" > "$OUTPUT_NAME.sha256"
)
echo '[7/7] Done'
ls -lh "$OUT/$OUTPUT_NAME" "$OUT/$OUTPUT_NAME.sha256" "$OUT/patch-report.json"
