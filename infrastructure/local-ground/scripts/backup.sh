#!/usr/bin/env bash
#
# backup.sh — create a deterministic, checksummed local backup of OCE Local
# Ground data (B1-LOCAL, A-003; recovery contract).
#
# Backup behavior NEVER depends silently on whether Docker is running. Callers
# request an explicit scope:
#
#   --scope state-only    local configuration + working-state files only; never
#                         includes PostgreSQL or artifact volumes; restore runs
#                         without Docker; metadata disaster_recovery_capable=false.
#   --scope full          the complete recoverable Local Ground state (the
#                         operator-facing default for `oce-ctl backup`); requires
#                         healthy local PostgreSQL and artifact-store services and
#                         BLOCKS (never silently degrades) if either is unavailable;
#                         includes PostgreSQL (custom-format archive + hash-protected
#                         inventory) and artifacts; disaster_recovery_capable=true.
#
# Every file under .backup-content is covered by a deterministic SHA-256
# manifest (sorted by relpath) with exactly three fields per line. backup-info.json
# is inside the content set and therefore hash-protected. Unknown scopes and
# incompatible arguments are rejected (fail closed). No secrets/passwords/tokens.
#
#   backup.sh --scope <state-only|full> [--out DIR]
set -uo pipefail

BIN="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$BIN/.." && pwd)"
VAR_DIR="$BASE_DIR/var"
PROJ_ROOT="$(cd "$BASE_DIR/../.." && pwd)"

SCOPE=""
OUT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --scope) SCOPE="${2:-}"; shift 2 ;;
    --out) OUT="${2:-}"; shift 2 ;;
    *) echo "USAGE_ERROR: unknown argument '$1'" >&2; exit 2 ;;
  esac
done
if [ -z "$SCOPE" ]; then echo "USAGE_ERROR: --scope <state-only|full> required" >&2; exit 2; fi
SCOPE="$(printf '%s' "$SCOPE" | tr '[:upper:]' '[:lower:]')"
case "$SCOPE" in state-only|full) ;; *) echo "USAGE_ERROR: unknown --scope '$SCOPE'" >&2; exit 2 ;; esac

OUT="${OUT:-$VAR_DIR/backups/$(date +%Y%m%d-%H%M%S)}"
mkdir -p "$OUT/.backup-content"
OUT="$(cd "$OUT" && pwd)"
CONTENT="$OUT/.backup-content"

PG_USER="${POSTGRES_USER:-oce_local_admin}"
PG_DB="${POSTGRES_DB:-oce_local}"
BACKUP_ID="$(python3 -c 'import uuid,sys;sys.stdout.write(uuid.uuid4().hex)')"
DCR=""
INCLUDES="state"

have_docker() { command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; }

# ── var/ working set (deterministic by relpath) ────────────────────────────
if [ -d "$VAR_DIR" ]; then
  (cd "$VAR_DIR" && find . -type f -not -path "./backups/*" -not -name "*.tmp" | sort) | while read -r rel; do
    rel="${rel#./}"
    dest="$CONTENT/$rel"
    mkdir -p "$(dirname "$dest")"
    cp "$VAR_DIR/$rel" "$dest"
  done
fi
cp "$VAR_DIR/state.json" "$CONTENT/state.json" 2>/dev/null || echo '{}' > "$CONTENT/state.json"

if [ "$SCOPE" = "state-only" ]; then
  DCR=false
  INCLUDES="state"
else
  # ── full scope: every authoritative service must be healthy or BLOCK ─────
  if ! have_docker; then
    echo "BLOCKED: full backup requires Docker; use --scope state-only without the runtime." >&2
    exit 3
  fi
  if ! docker inspect oce-local-postgresql >/dev/null 2>&1 \
     || ! docker exec oce-local-postgresql pg_isready -U "$PG_USER" -d "$PG_DB" -h localhost >/dev/null 2>&1; then
    echo "BLOCKED: full backup requires healthy local PostgreSQL (oce-local-postgresql)." >&2
    exit 3
  fi
  if ! docker inspect oce-local-artifact >/dev/null 2>&1 \
     || ! docker volume inspect oce_local_artifact_data >/dev/null 2>&1; then
    echo "BLOCKED: full backup requires the local artifact store (oce-local-artifact)." >&2
    exit 3
  fi
  DCR=true
  INCLUDES="state postgres artifacts"

  # PostgreSQL: custom-format archive via pinned postgres tooling
  mkdir -p "$CONTENT/postgres"
  ARCHIVE="$CONTENT/postgres/archive.dump"
  if ! docker exec oce-local-postgresql pg_dump --format=custom --no-owner --no-privileges \
       -U "$PG_USER" -d "$PG_DB" -f /tmp/oce_pg_backup_$BACKUP_ID.dump; then
    echo "BLOCKED: pg_dump (custom) failed" >&2; exit 3
  fi
  if ! docker cp "oce-local-postgresql:/tmp/oce_pg_backup_$BACKUP_ID.dump" "$ARCHIVE"; then
    echo "BLOCKED: cannot copy pg archive out" >&2; exit 3
  fi
  docker exec oce-local-postgresql rm -f "/tmp/oce_pg_backup_$BACKUP_ID.dump" 2>/dev/null || true
  [ -s "$ARCHIVE" ] || { echo "BLOCKED: empty postgres archive" >&2; exit 3; }

  # PostgreSQL: hash-protected database inventory (schemas/tables/counts)
  if ! python3 "$BIN/pg-inventory.py" --out "$CONTENT/postgres/inventory.json" \
       --container oce-local-postgresql --db "$PG_DB" --user "$PG_USER" \
       >> "$OUT/backup.log" 2>&1; then
    echo "BLOCKED: database inventory capture failed" >&2; exit 3
  fi

  # Artifacts: deterministic tar of the artifact volume
  mkdir -p "$CONTENT/artifacts"
  if ! docker run --rm -v oce_local_artifact_data:/data:ro \
       -v "$CONTENT/artifacts":/backup \
       postgres:16.2-alpine sh -c "tar czf /backup/artifacts.tar.gz -C /data ."; then
    echo "BLOCKED: artifact volume backup failed" >&2; exit 3
  fi
fi

# ── metadata (no secrets; identities only) ─────────────────────────────────
PGVERSION=""
DUMPFMT=""
PGVER_NUM=""
if [ "$SCOPE" = "full" ] && have_docker; then
  PGVERSION="$(docker exec oce-local-postgresql pg_dump --version 2>/dev/null | head -1)"
  DUMPFMT="custom"
  PGVER_NUM="$(docker exec oce-local-postgresql psql -X -A -t -U "$PG_USER" -d "$PG_DB" \
               -c 'SHOW server_version_num;' 2>/dev/null | tr -d '[:space:]')"
fi
COMMIT="$(git -C "$PROJ_ROOT" rev-parse HEAD 2>/dev/null || echo unknown)"
cat > "$CONTENT/backup-info.json" <<JSON
{ "format": "oce-local-ground-backup-v1", "schema_version": "2",
  "hash_algorithm": "sha256", "scope": "$SCOPE", "backup_id": "$BACKUP_ID",
  "disaster_recovery_capable": $DCR, "includes": "$INCLUDES",
  "database": "$PG_DB", "pg_dump_version": "$([ -n "$PGVERSION" ] && printf '%s' "$PGVERSION" || echo null)",
  "pg_dump_format": "$([ -n "$DUMPFMT" ] && printf '%s' "$DUMPFMT" || echo null)",
  "pg_version_num": "$([ -n "$PGVER_NUM" ] && printf '%s' "$PGVER_NUM" || echo null)",
  "source_commit": "$COMMIT", "run_id": "${OCE_RUN_ID:-not-set}",
  "created_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" }
JSON

# ── deterministic manifest over exactly the .backup-content files ──────────
(cd "$CONTENT" && find . -type f | sort) | while read -r rel; do
  rel="${rel#./}"
  sha=$(sha256sum "$CONTENT/$rel" | awk '{print $1}')
  size=$(stat -c %s "$CONTENT/$rel" 2>/dev/null || wc -c < "$CONTENT/$rel")
  printf '%s  %s  %s\n' "$sha" "$size" "$rel"
done > "$OUT/BACKUP_MANIFEST.sha256"

# R25: for full scope, refuse to produce an incomplete backup if either
# authoritative source silently produced nothing.
if [ "$SCOPE" = "full" ]; then
  [ -f "$CONTENT/postgres/archive.dump" ] && [ -s "$CONTENT/postgres/archive.dump" ] \
    || { echo "BLOCKED: full backup missing PostgreSQL archive" >&2; exit 3; }
  [ -f "$CONTENT/postgres/inventory.json" ] && [ -s "$CONTENT/postgres/inventory.json" ] \
    || { echo "BLOCKED: full backup missing database inventory" >&2; exit 3; }
  [ -f "$CONTENT/artifacts/artifacts.tar.gz" ] && [ -s "$CONTENT/artifacts/artifacts.tar.gz" ] \
    || { echo "BLOCKED: full backup missing artifact data" >&2; exit 3; }
  # manifest completeness: every content file is declared
  declared=$(wc -l < "$OUT/BACKUP_MANIFEST.sha256")
  actual=$(find "$CONTENT" -type f | wc -l)
  [ "$declared" -eq "$actual" ] || { echo "BLOCKED: manifest incomplete (declared=$declared actual=$actual)" >&2; exit 3; }
fi

echo "backup complete -> $OUT"
echo "scope: $SCOPE | backup_id: $BACKUP_ID | disaster_recovery_capable: $DCR"
echo "includes: $INCLUDES"
echo "tracked files: $(wc -l < "$OUT/BACKUP_MANIFEST.sha256")"
echo "manifest: $OUT/BACKUP_MANIFEST.sha256"
exit 0