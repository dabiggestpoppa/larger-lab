#!/usr/bin/env bash
#
# restore.sh — verify and restore a local backup, rejecting corrupt content.
# Every entry in BACKUP_MANIFEST.sha256 must exist with matching size and hash
# before restoration begins (fail closed, no partial touch).
#
#   restore.sh --from <backup-dir>
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VAR_DIR="$BASE_DIR/var"

FROM=""
[ "${1:-}" = "--from" ] && FROM="${2:-}"
if [ -z "$FROM" ] || [ ! -d "$FROM" ]; then
  echo "BLOCKED: restore requires --from <backup-dir>" >&2
  exit 3
fi
FROM="$(cd "$FROM" && pwd)"
MANIFEST="$FROM/BACKUP_MANIFEST.sha256"
CONTENT="$FROM/.backup-content"
if [ ! -f "$MANIFEST" ] || [ ! -d "$CONTENT" ]; then
  echo "CORRUPT: backup missing content or manifest" >&2
  exit 3
fi

echo "verifying backup integrity (fail closed)..."
rc=0
count=0
while read -r sha size rel; do
  [ -z "$rel" ] && continue
  count=$((count+1))
  f="$CONTENT/$rel"
  if [ ! -f "$f" ]; then
    echo "CORRUPT: missing '$rel'" >&2; rc=1; continue
  fi
  actual_size=$(stat -c %s "$f" 2>/dev/null || wc -c < "$f")
  actual=$(sha256sum "$f" | awk '{print $1}')
  if [ "$actual" != "$sha" ] || [ "$actual_size" != "$size" ]; then
    echo "CORRUPT: hash/size mismatch '$rel'" >&2; rc=1
  fi
done < <(tr -d '\r' < "$MANIFEST")

if [ $rc -ne 0 ]; then
  echo "BLOCKED: corrupt backup NOT restored" >&2
  exit 3
fi
echo "integrity OK: $count files verified"

# Restore into a fresh target (clean-room): write var/ from content.
mkdir -p "$VAR_DIR"
(cd "$CONTENT" && find . -type f | sort) | while read -r rel; do
  rel="${rel#./}"
  dest="$VAR_DIR/$rel"
  mkdir -p "$(dirname "$dest")"
  cp "$CONTENT/$rel" "$dest"
done
echo "restore complete -> $VAR_DIR"
exit 0