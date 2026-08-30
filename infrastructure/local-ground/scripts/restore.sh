#!/usr/bin/env bash
#
# restore.sh â€” restore a local backup under an explicit, non-ambiguous mode
# (B1-LOCAL, A-003; recovery contract).
#
# Modes:
#   --mode state-only    accepts ONLY a `state-only` backup; restores only the
#                        declared local state files; NEVER touches PostgreSQL,
#                        Redis or artifact volumes; runs without Docker.
#   --mode full-replace  accepts ONLY a complete `full` backup; requires
#                        --confirm-local-target <db> (explicit local recovery
#                        authorization + target identity); REPLACES the local
#                        PostgreSQL and artifact state with the backup snapshot
#                        via verified staging promotion. Redis is never restored.
#
# Integrity is fail-closed: BACKUP_MANIFEST.sha256 must reference existing,
# hash/size-matching files; every manifest path must be safe (relative, no '..',
# no absolute, no duplicate, no missing); a state-only backup claims
# disaster_recovery_capable=false, a full backup claims true. A full backup
# cannot be restored with state-only mode, and vice-versa (fail closed).
#
#   restore.sh --mode <state-only|full-replace> --from <backup-dir>
#              [--confirm-local-target oce_local]
set -uo pipefail

BIN="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$BIN/.." && pwd)"
VAR_DIR="$BASE_DIR/var"
PROJ_ROOT="$(cd "$BASE_DIR/../.." && pwd)"

MODE=""
FROM=""
CONFIRM_TARGET=""
while [ $# -gt 0 ]; do
  case "$1" in
    --mode) MODE="${2:-}"; shift 2 ;;
    --from) FROM="${2:-}"; shift 2 ;;
    --confirm-local-target) CONFIRM_TARGET="${2:-}"; shift 2 ;;
    *) echo "USAGE_ERROR: unknown argument '$1'" >&2; exit 2 ;;
  esac
done
if [ -z "$MODE" ]; then echo "USAGE_ERROR: --mode <state-only|full-replace> required" >&2; exit 2; fi
MODE="$(printf '%s' "$MODE" | tr '[:upper:]' '[:lower:]')"
case "$MODE" in state-only|full-replace) ;; *) echo "USAGE_ERROR: unknown --mode '$MODE'" >&2; exit 2 ;; esac
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
while IFS=' ' read -r sha size rel extra; do
  if [ -z "$sha" ] && [ -z "$size" ] && [ -z "$rel" ] && [ -z "$extra" ]; then
    continue
  fi
  if [ -z "$rel" ] || [ -z "$size" ] || [ -n "$extra" ] || [ "$rel" = "$sha" ]; then
    echo "CORRUPT: malformed manifest line (expected 'sha256 size relpath')" >&2
    rc=1
    continue
  fi
  case "$rel" in
    /*|*\"/../\"*|\"..\"|*/\"..\"|\"../\"*|*'/..'*) echo "CORRUPT: unsafe manifest path '$rel'" >&2; rc=1; continue ;;
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

# R25: no undeclared files under .backup-content
declared_count=$count
content_files=$(find "$CONTENT" -type f -printf '%P\n' | sort | tr -d '\r')
count_content=$(printf '%s\n' "$content_files" | grep -c . || true)
if [ "$declared_count" -ne "$count_content" ]; then
  echo "CORRUPT: undeclared files or missing manifest entries (declared=$declared_count content=$count_content)" >&2
  rc=1
fi

if [ $rc -ne 0 ]; then
  echo "BLOCKED: corrupt backup NOT restored" >&2
  exit 3
fi
echo "integrity OK: $count files verified"

# backup metadata must be present and hash-protected (inside content)
if [ ! -f "$CONTENT/backup-info.json" ]; then
  echo "CORRUPT: backup-info.json missing (unprotected metadata)" >&2
  exit 3
fi
INFO="$CONTENT/backup-info.json"
SCOPE="$(python3 -c "import json,sys;d=json.load(open(sys.argv[1],encoding='utf-8'));print(d.get('scope',''))" "$INFO")"
DCR="$(python3 -c "import json,sys;d=json.load(open(sys.argv[1],encoding='utf-8'));print(d.get('disaster_recovery_capable',False))" "$INFO")"

# â”€â”€ state-only restore â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if [ "$MODE" = "state-only" ]; then
  if [ "$SCOPE" != "state-only" ]; then
    echo "BLOCKED: state-only mode accepts only a state-only backup (got scope=$SCOPE)." >&2
    echo "         Use --mode full-replace for a full backup." >&2
    exit 3
  fi
  if [ "$DCR" != "False" ] && [ "$DCR" != "false" ]; then
    echo "BLOCKED: state-only backup must claim disaster_recovery_capable=false." >&2
    exit 3
  fi
  # restore only declared state files; never touch containers
  mkdir -p "$VAR_DIR"
  (cd "$CONTENT" && find . -type f | sort) | while read -r rel; do
    rel="${rel#./}"
    case "$rel" in backup-info.json) continue ;; esac
    dest="$VAR_DIR/$rel"
    mkdir -p "$(dirname "$dest")"
    cp "$CONTENT/$rel" "$dest"
  done
  echo "state-only restore complete -> $VAR_DIR"
  echo "  (containers untouched; no PostgreSQL/Redis/artifact volumes modified)"
  exit 0
fi

# â”€â”€ full-replace restore â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if [ "$SCOPE" != "full" ]; then
  echo "BLOCKED: full-replace mode requires a 'full' backup (got scope=$SCOPE)." >&2
  echo "         A state-only backup cannot be restored with full-replace." >&2
  exit 3
fi
if [ "$DCR" != "True" ] && [ "$DCR" != "true" ]; then
  echo "BLOCKED: full backup must claim disaster_recovery_capable=true." >&2
  exit 3
fi
[ -z "$CONFIRM_TARGET" ] && { echo "BLOCKED: full-replace requires --confirm-local-target <db>." >&2; exit 3; }
[ "$CONFIRM_TARGET" != "$PG_DB" ] && { echo "BLOCKED: --confirm-local-target must equal the local recovery database ($PG_DB)." >&2; exit 3; }

# R24: validate artifact archive members BEFORE the docker gate, so an unsafe
# archive is rejected even where no runtime is available.
if [ -f "$CONTENT/artifacts/artifacts.tar.gz" ]; then
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
    if nm.startswith("/") or ".." in nm.split("/") or m.isdev():
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
    exit 3
  fi
fi

if ! have_docker; then
  echo "BLOCKED: full-replace restore requires Docker (local runtime)." >&2
  exit 3
fi

RECEIPT_DIR="$VAR_DIR/recovery"
mkdir -p "$RECEIPT_DIR"
EV_DIR="${OCE_EVIDENCE_DIR:-}"
START_TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# â”€â”€ controlled artifact replacement (R24) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
ARTIFACT_APPLIED=false
if [ -f "$CONTENT/artifacts/artifacts.tar.gz" ]; then
  TMP_X="$(mktemp -d)"
  if ! docker inspect oce-local-artifact >/dev/null 2>&1; then
    echo "BLOCKED: artifact container unavailable" >&2
    rm -rf "$TMP_X"
    exit 3
  fi
  # quiesce: stop the artifact service so replacement is not a live merge
  docker stop oce-local-artifact >/dev/null 2>&1 || true
  if ! tar xzf "$CONTENT/artifacts/artifacts.tar.gz" -C "$TMP_X"; then
    echo "BLOCKED: artifact extraction failed" >&2
    docker start oce-local-artifact >/dev/null 2>&1 || true
    rm -rf "$TMP_X"
    exit 3
  fi
  # wipe the artifact data volume to a clean state, then restore from snapshot
  # (replace, never merge)
  if ! docker run --rm -v oce_local_artifact_data:/data \
       postgres:16.2-alpine sh -c "rm -rf /data/* /data/.[!.]* 2>/dev/null; true"; then
    echo "BLOCKED: cannot clear artifact volume" >&2
    docker start oce-local-artifact >/dev/null 2>&1 || true
    rm -rf "$TMP_X"
    exit 3
  fi
  if ! docker cp "$TMP_X/." oce-local-artifact:/data/; then
    echo "BLOCKED: artifact restore into container failed" >&2
    docker start oce-local-artifact >/dev/null 2>&1 || true
    rm -rf "$TMP_X"
    exit 3
  fi
  rm -rf "$TMP_X"
  docker start oce-local-artifact >/dev/null 2>&1 || true
  ARTIFACT_APPLIED=true
fi

# â”€â”€ PostgreSQL verified staging promotion (R23) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export OCE_COMMIT="$(git -C "$PROJ_ROOT" rev-parse HEAD 2>/dev/null || echo unknown)"
export OCE_EVIDENCE_DIR="${OCE_EVIDENCE_DIR:-}"
RECEIPT_OUT="$RECEIPT_DIR/postgres-recovery-receipt.json"
if [ -f "$CONTENT/postgres/archive.dump" ] && [ -f "$CONTENT/postgres/inventory.json" ] \
   && [ -f "$CONTENT/postgres/inventory.json.sha256" ]; then
  python3 "$BIN/pg-recovery.py" \
    --archive "$CONTENT/postgres/archive.dump" \
    --inventory "$CONTENT/postgres/inventory.json" \
    --inventory-sha "$CONTENT/postgres/inventory.json.sha256" \
    --db "$PG_DB" --user "$PG_USER" --container oce-local-postgresql \
    --receipt-out "$RECEIPT_OUT"
  PG_RC=$?
  if [ -n "$EV_DIR" ] && [ -f "$RECEIPT_OUT" ]; then
    cp "$RECEIPT_OUT" "$EV_DIR/postgres-recovery-receipt.json" 2>/dev/null || true
    # preserve each restore's own receipt (a later restore must not clobber evidence)
    cp "$RECEIPT_OUT" "$EV_DIR/postgres-recovery-receipt-$(date +%s%N).json" 2>/dev/null || true
  fi
  if [ "$PG_RC" -ne 0 ]; then
    echo "BLOCKED: PostgreSQL verified recovery failed" >&2
    exit 1
  fi
elif [ "$SCOPE" = "full" ]; then
  echo "BLOCKED: full backup is missing required PostgreSQL archive/inventory" >&2
  exit 3
fi

# Fail-closed durable canonical verification (Repair-3 phase 8/10): the
# recovery engine verified the promoted target, but exit 0 must ALSO be
# independently confirmed against the live canonical right at the restore
# boundary with a fresh docker exec, and it must be stable (not flicker).
# If the canonical ever fails to match the protected inventory, BLOCK.
VERIFY_STABLE=0
for _pit in 1 2 3 4 5; do
  if python3 - "$PG_DB" "$PG_USER" "$CONTENT/postgres/inventory.json" <<'PY'
import json, subprocess, sys
inv = json.load(open(sys.argv[3], encoding="utf-8"))
expected = {t["name"]: t["row_count"] for t in inv.get("tables", [])}
if not expected:
    print("UNVERIFIED: inventory lists no tables"); sys.exit(1)
bad = []
for name, want in expected.items():
    schema, _, rel = name.partition(".")
    r = subprocess.run(["docker", "exec", "oce-local-postgresql", "psql", "-X", "-tAc",
                        "-U", sys.argv[2], "-d", sys.argv[1],
                        'SELECT count(*) FROM "%s"."%s";' % (schema, rel)],
                       capture_output=True, text=True)
    got = r.stdout.strip() if r.returncode == 0 else "-err-"
    if got != str(want):
        bad.append(f"{name}=got {got}, want {want}")
if bad:
    print("UNVERIFIED: " + "; ".join(bad), file=sys.stderr)
    sys.exit(1)
print("CANONICAL_VERIFIED")
sys.exit(0)
PY
  then
    VERIFY_STABLE=$((VERIFY_STABLE+1))
    [ "$VERIFY_STABLE" -ge 2 ] && break
  else
    VERIFY_STABLE=0
    echo "warning: canonical not yet verified (attempt $_pit)" >&2
  fi
  sleep 2
done
if [ "$VERIFY_STABLE" -lt 2 ]; then
  echo "BLOCKED: canonical target failed independent durable verification after restore" >&2
  exit 1
fi

END_TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
cp "$RECEIPT_OUT" "$RECEIPT_DIR/restore-receipt.json" 2>/dev/null || true
if [ -n "$EV_DIR" ]; then
  cp "$RECEIPT_DIR/restore-receipt.json" "$EV_DIR/restore-receipt.json" 2>/dev/null || true
fi
echo "full-replace restore complete <- $FROM"
echo "  postgres: verified staging promotion | artifacts: $ARTIFACT_APPLIED | redis: not restored"
exit 0