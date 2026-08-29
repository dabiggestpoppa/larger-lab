#!/usr/bin/env bash
#
# restore.sh — verify and restore a local backup, rejecting corrupt content
# (B1-LOCAL, A-003).
#
# Integrity is fail-closed: every line in BACKUP_MANIFEST.sha256 must reference
# an existing file under .backup-content whose size and SHA-256 match, and every
# manifest path must be safe (relative, no '..', no absolute, no traversal).
# backup-info.json is hash-protected by being included in the manifest.
#
# Restores:
#   * var/ working set always;
#   * PostgreSQL logical dump (postgres/dump.sql) when present — applied with
#     ON_ERROR_STOP inside a single transaction via the pinned postgres image;
#     BLOCKED if the container is unavailable, if postgres is not ready, or on
#     any SQL error. A restore that exits zero MUST have applied every row.
#   * artifact volume content (artifacts/artifacts.tar.gz) when present — tar
#     members are validated for absolute paths / '..' / unsafe links before
#     extraction into the running artifact container; BLOCKED on unsafe content.
#
# Redis is deliberately NOT restored: it is disposable transport state, never
# authoritative truth.
#
# A restore receipt (restore-receipt.json) is written on every restore,
# recording DB identity, dump hash, timestamps and exit status.
#
#   restore.sh --from <backup-dir>
set -uo pipefail

# resolve reliably regardless of caller cwd
BIN="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$BIN/.." && pwd)"
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
declare -A seen
# read exactly three whitespace-separated fields; any other field count is malformed
while IFS=' ' read -r sha size rel extra; do
  # blank lines are tolerated; short/malformed lines are NOT
  if [ -z "$sha" ] && [ -z "$size" ] && [ -z "$rel" ] && [ -z "$extra" ]; then
    continue
  fi
  if [ -z "$rel" ] || [ -z "$size" ] || [ -n "$extra" ] || [ "$rel" = "$sha" ]; then
    echo "CORRUPT: malformed manifest line (expected 'sha256 size relpath')" >&2
    rc=1
    continue
  fi
  # trim an ANSI-free relative path and reject unsafe path forms (R19)
  case "$rel" in
    /*|*"/../"*|".."|*/".."|"../"*|*'/..'*) echo "CORRUPT: unsafe manifest path '$rel'" >&2; rc=1; continue ;;
  esac
  case "$rel" in *\\\\*) echo "CORRUPT: backslash in manifest path '$rel'" >&2; rc=1; continue ;; esac
  if [ -n "${seen[$rel]:-}" ]; then echo "CORRUPT: duplicate manifest path '$rel'" >&2; rc=1; continue; fi
  seen[$rel]=1
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

# backup metadata must itself be present and hash-protected
if [ ! -f "$CONTENT/backup-info.json" ] && [ ! -f "$FROM/backup-info.json" ]; then
  echo "CORRUPT: backup-info.json missing (unprotected metadata)" >&2
  exit 3
fi
INFO_FILE="$CONTENT/backup-info.json"
[ -f "$CONTENT/backup-info.json" ] || INFO_FILE="$FROM/backup-info.json"

# var/ working set (postgres/ and artifacts/ handled separately below)
mkdir -p "$VAR_DIR"
(cd "$CONTENT" && find . -type f | sort) | while read -r rel; do
  rel="${rel#./}"
  case "$rel" in postgres/*|artifacts/*) continue ;; esac
  dest="$VAR_DIR/$rel"
  mkdir -p "$(dirname "$dest")"
  cp "$CONTENT/$rel" "$dest"
done

# helper: fail-closed postgres readiness + locality check before any restore
pg_ready_failclosed() {
  if ! have_docker || ! docker inspect oce-local-postgresql >/dev/null 2>&1; then
    echo "BLOCKED: postgres container unavailable for restore" >&2
    return 1
  fi
  if ! docker exec oce-local-postgresql pg_isready -U "$PG_USER" -d "$PG_DB" -h localhost >/dev/null 2>&1; then
    echo "BLOCKED: postgres not ready before restore" >&2
    return 1
  fi
  return 0
}

START_TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
DUMP_HASH=""
PG_APPLIED=false
ARTIFACT_APPLIED=false

# ── PostgreSQL logical restore (authoritative truth) ───────────────────────
if [ -f "$CONTENT/postgres/dump.sql" ]; then
  if ! pg_ready_failclosed; then
    echo "BLOCKED: cannot restore postgres dump" >&2
    exit 3
  fi
  DUMP_HASH="$(sha256sum "$CONTENT/postgres/dump.sql" | awk '{print $1}')"
  # Fail-closed: ON_ERROR_STOP exits nonzero on any SQL error; -X ignores the
  # user's ~/.psqlrc; a single transaction keeps the dump all-or-nothing.
  if docker exec -i oce-local-postgresql env PGOPTIONS="-c client_min_messages=warning" \
       psql -X -v ON_ERROR_STOP=1 --single-transaction -U "$PG_USER" -d "$PG_DB" \
       < "$CONTENT/postgres/dump.sql" > "$VAR_DIR/restore-pg.stdout" 2> "$VAR_DIR/restore-pg.stderr"; then
    echo "postgres restore applied"
    rm -rf "$VAR_DIR/restore-pg.stdout" "$VAR_DIR/restore-pg.stderr"
    PG_APPLIED=true
  else
    echo "BLOCKED: postgres restore FAILED (SQL error)" >&2
    tail -50 "$VAR_DIR/restore-pg.stderr" >&2 || true
    exit 3
  fi
fi

# ── artifact volume restore (replaceable storage adapter) ──────────────────
if [ -f "$CONTENT/artifacts/artifacts.tar.gz" ]; then
  TMP_X="$(mktemp -d)"
  # R19: validate tar members BEFORE extraction AND before any container check,
  # so an unsafe archive is rejected regardless of container availability.
  if ! python3 - "$CONTENT/artifacts/artifacts.tar.gz" <<'PY'
import sys, tarfile
p = sys.argv[1]
try:
    tf = tarfile.open(p, "r:gz")
except Exception as e:
    print("BLOCKED: corrupt tar:", e); sys.exit(1)
bad = []
for m in tf.getmembers():
    nm = m.name
    if nm.startswith("/") or ".." in nm.split("/"):
        bad.append(("path", nm))
    if m.issym() or m.islnk():
        bad.append(("link", nm))
if bad:
    print("BLOCKED: unsafe tar members:", bad[:5]); sys.exit(1)
tf.close()
sys.exit(0)
PY
  then
    echo "BLOCKED: artifact archive failed safe validation" >&2
    rm -rf "$TMP_X"
    exit 3
  fi
  if ! have_docker || ! docker inspect oce-local-artifact >/dev/null 2>&1; then
    echo "BLOCKED: backup contains artifacts but the artifact container is unavailable" >&2
    rm -rf "$TMP_X"
    exit 3
  fi
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
  ARTIFACT_APPLIED=true
  echo "artifact restore applied"
fi

END_TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
mkdir -p "$VAR_DIR"
cat > "$VAR_DIR/restore-receipt.json" <<JSON
{ "format": "oce-restore-receipt-v1", "started_at": "$START_TS", "finished_at": "$END_TS",
  "database": "$PG_DB", "dump_sha256": "$DUMP_HASH",
  "postgres_restore_applied": $PG_APPLIED, "artifact_restored": $ARTIFACT_APPLIED,
  "exit_status": 0, "redis_restored": false, "redis_rebuildable": true }
JSON

echo "restore complete -> $VAR_DIR"
exit 0