#!/usr/bin/env bash
#
# restore.sh — verify and restore a local backup, rejecting corrupt content
# (B1-LOCAL, A-003). Every entry in BACKUP_MANIFEST.sha256 must exist with
# matching size and hash before anything is touched (fail closed).
#
# Restores:
#   * var/ working set always;
#   * PostgreSQL logical dump (postgres/dump.sql) when present — applied via
#     the pinned postgres image; BLOCKED if the container is unavailable;
#   * artifact volume contents (artifacts/artifacts.tar.gz) when present —
#     extracted and copied into the running artifact container; BLOCKED if
#     the container is unavailable.
#
# Redis is deliberately NOT restored: it is disposable transport state, never
# authoritative truth.
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

PG_USER="${POSTGRES_USER:-oce_local_admin}"
PG_DB="${POSTGRES_DB:-oce_local}"
have_docker() { command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; }

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

# ── var/ working set (postgres/ and artifacts/ handled separately below) ───
mkdir -p "$VAR_DIR"
(cd "$CONTENT" && find . -type f | sort) | while read -r rel; do
  rel="${rel#./}"
  case "$rel" in postgres/*|artifacts/*) continue ;; esac
  dest="$VAR_DIR/$rel"
  mkdir -p "$(dirname "$dest")"
  cp "$CONTENT/$rel" "$dest"
done

# ── PostgreSQL logical restore (authoritative truth) ───────────────────────
if [ -f "$CONTENT/postgres/dump.sql" ]; then
  if ! have_docker || ! docker inspect oce-local-postgresql >/dev/null 2>&1; then
    echo "BLOCKED: backup contains a postgres dump but the postgres container is unavailable" >&2
    exit 3
  fi
  if ! docker exec -i oce-local-postgresql psql -U "$PG_USER" -d "$PG_DB" < "$CONTENT/postgres/dump.sql"; then
    echo "BLOCKED: postgres restore failed" >&2
    exit 3
  fi
  echo "postgres restore applied"
fi

# ── artifact volume restore (replaceable storage adapter) ──────────────────
if [ -f "$CONTENT/artifacts/artifacts.tar.gz" ]; then
  if ! have_docker || ! docker inspect oce-local-artifact >/dev/null 2>&1; then
    echo "BLOCKED: backup contains artifacts but the artifact container is unavailable" >&2
    exit 3
  fi
  TMP_X="$(mktemp -d)"
  if ! tar xzf "$CONTENT/artifacts/artifacts.tar.gz" -C "$TMP_X"; then
    echo "BLOCKED: artifact extraction failed" >&2
    rm -rf "$TMP_X"
    exit 3
  fi
  if ! docker cp "$TMP_X/." oce-local-artifact:/data/; then
    echo "BLOCKED: artifact copy into container failed" >&2
    rm -rf "$TMP_X"
    exit 3
  fi
  rm -rf "$TMP_X"
  echo "artifact restore applied"
fi

echo "restore complete -> $VAR_DIR"
exit 0
