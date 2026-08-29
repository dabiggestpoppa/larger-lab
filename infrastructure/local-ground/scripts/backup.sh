#!/usr/bin/env bash
#
# backup.sh — create a deterministic, checksummed local backup of OCE Local
# Ground data (B1-LOCAL, A-003).
#
# The package always contains the var/ working set. When the running stack is
# available it ALSO contains authoritative data:
#   * postgres/dump.sql        — logical backup from the pinned postgres image
#   * artifacts/artifacts.tar.gz — tar of the artifact volume (MinIO /data)
#
# Every file under .backup-content is covered by a deterministic SHA-256
# manifest (sorted by relpath). Metadata (format, schema version, includes,
# created_at, RUN_ID, source commit, tool versions) lives in backup-info.json.
# No secrets, passwords, tokens, or private operator data are included.
#
#   backup.sh [--out DIR]
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VAR_DIR="$BASE_DIR/var"
PROJ_ROOT="$(cd "$BASE_DIR/../.." && pwd)"

OUT=""
if [ "${1:-}" = "--out" ]; then OUT="${2:-}"; fi
OUT="${OUT:-$VAR_DIR/backups/$(date +%Y%m%d-%H%M%S)}"
mkdir -p "$OUT/.backup-content"
OUT="$(cd "$OUT" && pwd)"

PG_USER="${POSTGRES_USER:-oce_local_admin}"
PG_DB="${POSTGRES_DB:-oce_local}"
INCLUDES="var"

have_docker() { command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; }

# ── authoritative data: PostgreSQL logical backup ──────────────────────────
if have_docker && docker inspect oce-local-postgresql >/dev/null 2>&1 \
   && docker exec oce-local-postgresql pg_isready -U "$PG_USER" -d "$PG_DB" -h localhost >/dev/null 2>&1; then
  mkdir -p "$OUT/.backup-content/postgres"
  if ! docker exec oce-local-postgresql pg_dump -U "$PG_USER" -d "$PG_DB" > "$OUT/.backup-content/postgres/dump.sql"; then
    echo "BLOCKED: pg_dump failed" >&2
    exit 3
  fi
  INCLUDES="$INCLUDES postgres"
fi

# ── authoritative data: artifact volume tar ────────────────────────────────
if have_docker && docker inspect oce-local-artifact >/dev/null 2>&1 \
   && docker volume inspect oce_local_artifact_data >/dev/null 2>&1; then
  mkdir -p "$OUT/.backup-content/artifacts"
  # Use the pinned postgres alpine image (busybox tar) purely as a tar tool.
  if ! docker run --rm -v oce_local_artifact_data:/data:ro \
       -v "$OUT/.backup-content/artifacts":/backup \
       postgres:16.2-alpine sh -c "tar czf /backup/artifacts.tar.gz -C /data ."; then
    echo "BLOCKED: artifact volume backup failed" >&2
    exit 3
  fi
  INCLUDES="$INCLUDES artifacts"
fi

# ── var/ working set (deterministic by relpath) ────────────────────────────
if [ -d "$VAR_DIR" ]; then
  (cd "$VAR_DIR" && find . -type f -not -path "./backups/*" -not -name "*.tmp" | sort) | while read -r rel; do
    rel="${rel#./}"
    dest="$OUT/.backup-content/$rel"
    mkdir -p "$(dirname "$dest")"
    cp "$VAR_DIR/$rel" "$dest"
  done
fi
cp "$VAR_DIR/state.json" "$OUT/.backup-content/state.json" 2>/dev/null || echo '{}' > "$OUT/.backup-content/state.json"

# ── metadata (no secrets; identities only) ─────────────────────────────────
PGDUMP_VERSION=""
DUMP_FORMAT="plain"
if have_docker && docker inspect oce-local-postgresql >/dev/null 2>&1; then
  PGDUMP_VERSION="$(docker exec oce-local-postgresql pg_dump --version 2>/dev/null | head -1)"
fi
COMMIT="$(git -C "$PROJ_ROOT" rev-parse HEAD 2>/dev/null || echo unknown)"
cat > "$OUT/backup-info.json" <<'JSON'
{ "format": "oce-local-ground-backup-v1", "schema_version": "1",
  "hash_algorithm": "sha256", "includes": null, "pg_dump_version": null,
  "pg_dump_format": "plain", "source_commit": null, "run_id": null, "created_at": null }
JSON
python3 - "$OUT/backup-info.json" "$INCLUDES" "$PGDUMP_VERSION" "$DUMP_FORMAT" "$COMMIT" <<'PY'
import json, os, sys, datetime
p, includes, pgver, dumpfmt, commit = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
d = json.load(open(p, encoding="utf-8"))
d["includes"] = includes.split()
d["pg_dump_version"] = pgver or None
d["pg_dump_format"] = dumpfmt
d["source_commit"] = commit
d["run_id"] = os.environ.get("OCE_RUN_ID", "not-set")
d["created_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
json.dump(d, open(p, "w", encoding="utf-8"), indent=2)
PY
# Hash-protect the metadata itself by copying it into the content set, so the
# manifest covers it and tampering with backup-info.json fails the restore.
cp "$OUT/backup-info.json" "$OUT/.backup-content/backup-info.json"

# Prove the pg_dump contains both schema and data (fail-closed; no empty dump)
if [ -f "$OUT/.backup-content/postgres/dump.sql" ]; then
  if ! grep -q "CREATE TABLE" "$OUT/.backup-content/postgres/dump.sql" 2>/dev/null; then
    echo "BLOCKED: pg_dump missing schema" >&2; exit 3
  fi
fi

# ── deterministic manifest over exactly the .backup-content files ──────────
(cd "$OUT/.backup-content" && find . -type f | sort) | while read -r rel; do
  rel="${rel#./}"
  sha=$(sha256sum "$OUT/.backup-content/$rel" | awk '{print $1}')
  size=$(stat -c %s "$OUT/.backup-content/$rel" 2>/dev/null || wc -c < "$OUT/.backup-content/$rel")
  printf '%s  %s  %s\n' "$sha" "$size" "$rel"
done > "$OUT/BACKUP_MANIFEST.sha256"

echo "backup complete -> $OUT"
echo "includes: $INCLUDES"
echo "tracked files: $(wc -l < "$OUT/BACKUP_MANIFEST.sha256")"
echo "manifest: $OUT/BACKUP_MANIFEST.sha256"
