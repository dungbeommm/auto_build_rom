#!/usr/bin/env bash
set -e; f="$1";o="$2";mkdir -p "$o";b="$(basename "$f")";split -b 1900m -d -a3 "$f" "$o/$b.part-";sha256sum "$o"/*>"$o/SHA256SUMS";cp "$f.sha256" "$o/";cat >"$o/JOIN.sh" <<EOF
#!/usr/bin/env bash
cat '$b.part-'*>'$b'; sha256sum -c '$b.sha256'
EOF
chmod +x "$o/JOIN.sh"
