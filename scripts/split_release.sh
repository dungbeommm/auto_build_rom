#!/usr/bin/env bash
set -Eeuo pipefail
file="${1:?Usage: split_release.sh ROM.tgz OUTPUT_DIR}"
out="${2:?Usage: split_release.sh ROM.tgz OUTPUT_DIR}"
[[ -f "$file" ]] || { echo "ROM output not found: $file" >&2; exit 2; }
rm -rf "$out"
mkdir -p "$out"
base="$(basename "$file")"
split -b 1900m -d -a 3 "$file" "$out/$base.part-"
(
  cd "$out"
  sha256sum "$base.part-"* > SHA256SUMS
)
cp "$file.sha256" "$out/$base.sha256"
cat > "$out/JOIN.sh" <<EOF
#!/usr/bin/env bash
set -Eeuo pipefail
cd "\$(dirname "\$0")"
sha256sum -c SHA256SUMS
cat '$base.part-'* > '$base'
sha256sum -c '$base.sha256'
echo 'Created: $base'
EOF
chmod +x "$out/JOIN.sh"
