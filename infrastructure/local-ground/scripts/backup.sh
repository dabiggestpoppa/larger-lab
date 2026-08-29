#!/usr/bin/env bash
#
# backup.sh — create a deterministic, checksummed local backup of OCE Local
# Ground data (var/ artifacts, state, logs). Files are copied into the backup
# directory and a SHA-256 manifest is generated over exactly those files.
#
#   backup.sh [--out DIR]
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VAR_DIR="$BASE_DIR/var"

OUT=""
if [ "${1:-}" = "--out" ]; then OUT="${2:-}"; fi
OUT="${OUT:-$VAR_DIR/backups/$(date +%Y%m%d-%H%M%S)}"
mkdir -p "$OUT/.backup-content"
OUT="$(cd "$OUT" && pwd)"

# Copy var content (excluding nested backups) deterministically by rel path.
if [ -d "$VAR_DIR" ]; then
  (cd "$VAR_DIR" && find . -type f -not -path "./backups/*" -not -name "*.tmp" | sort) | while read -r rel; do
    rel="${rel#./}"
    dest="$OUT/.backup-content/$rel"
    mkdir -p "$(dirname "$dest")"
    cp "$VAR_DIR/$rel" "$dest"
  done
fi

cp "$VAR_DIR/state.json" "$OUT/.backup-content/state.json" 2>/dev/null || echo '{}' > "$OUT/.backup-content/state.json"

cat > "$OUT/backup-info.json" <<'JSON'
{ "format": "oce-local-ground-backup-v1", "hash_algorithm": "sha256" }
JSON
python3 - "$OUT/backup-info.json" <<'PY'
import json, sys, datetime
p = sys.argv[1]
d = json.load(open(p, encoding="utf-8"))
d["created_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
json.dump(d, open(p, "w", encoding="utf-8"), indent=2)
PY

# Manifest over .backup-content (sorted, deterministic; excludes manifest itself).
(cd "$OUT/.backup-content" && find . -type f | sort) | while read -r rel; do
  rel="${rel#./}"
  sha=$(sha256sum "$OUT/.backup-content/$rel" | awk '{print $1}')
  size=$(stat -c %s "$OUT/.backup-content/$rel" 2>/dev/null || wc -c < "$OUT/.backup-content/$rel")
  printf '%s  %s  %s\n' "$sha" "$size" "$rel"
done > "$OUT/BACKUP_MANIFEST.sha256"

echo "backup complete -> $OUT"
echo "tracked files: $(wc -l < "$OUT/BACKUP_MANIFEST.sha256")"
echo "manifest: $OUT/BACKUP_MANIFEST.sha256"