#!/usr/bin/env bash
set -Eeuo pipefail
file="${1:?Usage: split_release.sh ROM.tgz [output-dir]}"; out="${2:-release-parts}"
mkdir -p "$out"; base="$(basename "$file")"
split -b 1900m -d -a 3 "$file" "$out/$base.part-"
sha256sum "$out/$base.part-"* > "$out/SHA256SUMS"
cat > "$out/JOIN_ROM.sh" <<EOF
#!/usr/bin/env bash
set -e
cat '$base.part-'* > '$base'
sha256sum -c SHA256SUMS
echo 'Đã ghép: $base'
EOF
chmod +x "$out/JOIN_ROM.sh"; cp -f "$file.sha256" "$file.manifest.json" "$out/" 2>/dev/null || true
