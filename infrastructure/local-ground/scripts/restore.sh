#!/usr/bin/env bash
#
# restore.sh — restore a local backup under an explicit, non-ambiguous mode
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
#                        via verified staging promotion. Redis is never
#                        restored from backup.
#
# PostgreSQL recovery (R25) is an explicit phase-safe state machine:
#   promote   -> staging restore+verify, canonical->quarantine, promote,
#                canonical verify; QUARANTINE IS HELD
#   [external restore-boundary verification]
#   finalize  -> final canonical re-verification, then quarantine dropped,
#                removal verified; receipt committed atomically
#   rollback  -> on any failure after quarantine begins, the ORIGINAL
#                canonical is restored from quarantine and verified.
# Quarantine remains available until every fallible verification passes.
#
# Full-replace is a STAGED TWO-RESOURCE RECOVERY (R39-R1), not one atomic
# commit: PostgreSQL and the artifact volume cannot commit together. Both
# stores are staged with a held rollback source (PostgreSQL quarantine, and a
# byte-for-byte copy of the live artifact volume taken before replacement),
# both are verified against the selected backup, and only then is the
# transaction committed by finalizing PostgreSQL and releasing the artifact
# rollback source. Any failure before commitment restores BOTH stores from
# those sources, leaves Redis untouched, writes a transaction rollback receipt
# and exits nonzero. A failure AFTER commitment (Redis invalidation) is a
# cleanup failure: it reports nonzero but does not roll the stores back.
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
while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode) MODE="${2:-}"; shift 2 ;;
    --from) FROM="${2:-}"; shift 2 ;;
    --confirm-local-target) CONFIRM_TARGET="${2:-}"; shift 2 ;;
    *) echo "USAGE_ERROR: unknown argument '$1'" >&2; exit 2 ;;
  esac
done
if [[ -z "$MODE" ]]; then echo "USAGE_ERROR: --mode <state-only|full-replace> required" >&2; exit 2; fi
MODE="$(printf '%s' "$MODE" | tr '[:upper:]' '[:lower:]')"
case "$MODE" in state-only|full-replace) ;; *) echo "USAGE_ERROR: unknown --mode '$MODE'" >&2; exit 2 ;; esac
if [[ -z "$FROM" || ! -d "$FROM" ]]; then
  echo "BLOCKED: restore requires --from <backup-dir>" >&2
  exit 3
fi
FROM="$(cd "$FROM" && pwd)"
MANIFEST="$FROM/BACKUP_MANIFEST.sha256"
CONTENT="$FROM/.backup-content"
if [[ ! -f "$MANIFEST" || ! -d "$CONTENT" ]]; then
  echo "CORRUPT: backup missing content or manifest" >&2
  exit 3
fi

PG_USER="${POSTGRES_USER:-oce_local_admin}"
PG_DB="${POSTGRES_DB:-oce_local}"
have_docker() {
  command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1
  return $?
}

echo "verifying backup integrity (fail closed)..."
rc=0
count=0
declare -A seen
while IFS=' ' read -r sha size rel extra; do
  if [[ -z "$sha" && -z "$size" && -z "$rel" && -z "$extra" ]]; then
    continue
  fi
  if [[ -z "$rel" || -z "$size" || -n "$extra" || "$rel" == "$sha" ]]; then
    echo "CORRUPT: malformed manifest line (expected 'sha256 size relpath')" >&2
    rc=1
    continue
  fi
  case "$rel" in
    /*|*\"/../\"*|\"..\"|*/\"..\"|\"../\"*|*'/..'*) echo "CORRUPT: unsafe manifest path '$rel'" >&2; rc=1; continue ;;
  esac
  case "$rel" in
    *\\\\*) echo "CORRUPT: backslash in manifest path '$rel'" >&2; rc=1; continue ;;
    *) : ;;  # single backslash is a legal POSIX filename character (S3923 default)
  esac
  if [[ -n "${seen[$rel]:-}" ]]; then echo "CORRUPT: duplicate manifest path '$rel'" >&2; rc=1; continue; fi
  seen[$rel]=1
  count=$((count+1))
  f="$CONTENT/$rel"
  if [[ ! -f "$f" ]]; then
    echo "CORRUPT: missing '$rel'" >&2; rc=1; continue
  fi
  actual_size=$(stat -c %s "$f" 2>/dev/null || wc -c < "$f")
  actual=$(sha256sum "$f" | awk '{print $1}')
  if [[ "$actual" != "$sha" || "$actual_size" != "$size" ]]; then
    echo "CORRUPT: hash/size mismatch '$rel'" >&2; rc=1
  fi
done < <(tr -d '\r' < "$MANIFEST")

# R25: no undeclared files under .backup-content
declared_count=$count
content_files=$(find "$CONTENT" -type f -printf '%P\n' | sort | tr -d '\r')
count_content=$(printf '%s\n' "$content_files" | grep -c . || true)
if [[ "$declared_count" -ne "$count_content" ]]; then
  echo "CORRUPT: undeclared files or missing manifest entries (declared=$declared_count content=$count_content)" >&2
  rc=1
fi

if [[ $rc -ne 0 ]]; then
  echo "BLOCKED: corrupt backup NOT restored" >&2
  exit 3
fi
echo "integrity OK: $count files verified"

# backup metadata must be present and hash-protected (inside content)
if [[ ! -f "$CONTENT/backup-info.json" ]]; then
  echo "CORRUPT: backup-info.json missing (unprotected metadata)" >&2
  exit 3
fi
INFO="$CONTENT/backup-info.json"
SCOPE="$(python3 -c "import json,sys;d=json.load(open(sys.argv[1],encoding='utf-8'));print(d.get('scope',''))" "$INFO")"
DCR="$(python3 -c "import json,sys;d=json.load(open(sys.argv[1],encoding='utf-8'));print(d.get('disaster_recovery_capable',False))" "$INFO")"

# ── state-only restore ─────────────────────────────────────────────────────
if [[ "$MODE" == "state-only" ]]; then
  if [[ "$SCOPE" != "state-only" ]]; then
    echo "BLOCKED: state-only mode accepts only a state-only backup (got scope=$SCOPE)." >&2
    echo "         Use --mode full-replace for a full backup." >&2
    exit 3
  fi
  if [[ "$DCR" != "False" && "$DCR" != "false" ]]; then
    echo "BLOCKED: state-only backup must claim disaster_recovery_capable=false." >&2
    exit 3
  fi
  # restore only declared state files; never touch containers
  mkdir -p "$VAR_DIR"
  (cd "$CONTENT" && find . -type f | sort) | while read -r rel; do
    rel="${rel#./}"
    case "$rel" in backup-info.json) continue ;; *) ;; esac
    dest="$VAR_DIR/$rel"
    mkdir -p "$(dirname "$dest")"
    cp "$CONTENT/$rel" "$dest"
  done
  echo "state-only restore complete -> $VAR_DIR"
  echo "  (containers untouched; no PostgreSQL/Redis/artifact volumes modified)"
  exit 0
fi

# ── full-replace restore ───────────────────────────────────────────────────
if [[ "$SCOPE" != "full" ]]; then
  echo "BLOCKED: full-replace mode requires a 'full' backup (got scope=$SCOPE)." >&2
  echo "         A state-only backup cannot be restored with full-replace." >&2
  exit 3
fi
if [[ "$DCR" != "True" && "$DCR" != "true" ]]; then
  echo "BLOCKED: full backup must claim disaster_recovery_capable=true." >&2
  exit 3
fi
[[ -z "$CONFIRM_TARGET" ]] && { echo "BLOCKED: full-replace requires --confirm-local-target <db>." >&2; exit 3; }
[[ "$CONFIRM_TARGET" != "$PG_DB" ]] && { echo "BLOCKED: --confirm-local-target must equal the local recovery database ($PG_DB)." >&2; exit 3; }

# R24: validate artifact archive members BEFORE the docker gate, so an unsafe
# archive is rejected even where no runtime is available.
if [[ -f "$CONTENT/artifacts/artifacts.tar.gz" ]]    && ! python3 - "$CONTENT/artifacts/artifacts.tar.gz" <<'PY'
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

if ! have_docker; then
  echo "BLOCKED: full-replace restore requires Docker (local runtime)." >&2
  exit 3
fi

EV_DIR="${OCE_EVIDENCE_DIR:-}"
# every evidence copy below is best-effort (`cp ... || true`) - but a missing
# evidence directory would silently discard receipts, so create it up front
[[ -n "$EV_DIR" ]] && mkdir -p "$EV_DIR"
TS_FMT='%Y-%m-%dT%H:%M:%SZ'
START_TS=$(date -u +"$TS_FMT")

# R8: every restore is ONE immutable, indexed operation. Receipts are copied
# into operations/<operation-id>/ under the operations root and registered in
# the append-only index with their hashes; later operations cannot overwrite
# earlier evidence, and a convenience latest.json is never authoritative.
OPERATION_ID="$(python3 -c 'import uuid,sys;sys.stdout.write(uuid.uuid4().hex)')"
# R39-R2: this operation's receipts live in ITS OWN directory inside the
# governed recovery boundary. The engine refuses to overwrite an existing
# receipt (a receipt is evidence), so a repeated restore must never be pointed
# at the previous operation's files.
RECEIPT_DIR="$VAR_DIR/recovery/ops/$OPERATION_ID"
mkdir -p "$RECEIPT_DIR"
OPS_ROOT="${OCE_EVIDENCE_DIR:-$VAR_DIR}/operations"
BACKUP_ID="$(python3 -c "import json,sys;d=json.load(open(sys.argv[1],encoding='utf-8'));print(d.get('backup_id',''))" "$INFO" 2>/dev/null || echo unknown)"
register_op() { # EXIT trap: index this restore operation immutably (idempotent)
  local rc="$1"
  [[ "$MODE" == "full-replace" ]] || return 0
  local final="success" rollback="none"
  [ "$rc" -eq 0 ] || final="blocked"
  if [[ -f "$RECEIPT_DIR/rollback-receipt.json" ]]; then
    rollback="$(python3 -c "import json;d=json.load(open(r'$RECEIPT_DIR/rollback-receipt.json',encoding='utf-8'));print('ok' if d.get('rollback_succeeded') is True else 'failed')" 2>/dev/null || echo failed)"
  fi
  local op_receipts=()
  for f in "$RECEIPT_DIR/restore-receipt.json" "$RECEIPT_DIR/postgres-recovery-receipt.json" \
           "$RECEIPT_DIR/promote-receipt.json" "$RECEIPT_DIR/artifact-recovery-receipt.json" \
           "$RECEIPT_DIR/redis-invalidation-receipt.json" "$RECEIPT_DIR/rollback-receipt.json"; do
    [ -f "$f" ] && op_receipts+=(--receipt "$f")
  done
  [ "${#op_receipts[@]}" -gt 0 ] || return 0
  python3 "$BIN/recovery-ops.py" add --ops-root "$OPS_ROOT" \
    --operation-id "$OPERATION_ID" --operation-type restore \
    --run-id "${OCE_RUN_ID:-not-set}" --commit "${OCE_COMMIT:-unknown}" --tree "${OCE_TREE:-unknown}" \
    --started-at "$START_TS" --finished-at "$(date -u +"$TS_FMT")" \
    --backup-id "$BACKUP_ID" --backup-scope "$SCOPE" --restore-mode "$MODE" \
    --source-database "$PG_DB" --target-database "$PG_DB" \
    --final-result "$final" --rollback-result "$rollback" \
    --cloud-mutations 0 --cloud-cost-state ZERO \
    "${op_receipts[@]}" >/dev/null 2>&1 || echo "WARNING: restore operation registration failed" >&2
}
# ── staged two-resource recovery (R39-R1) ──────────────────────────────────
# A full replace covers TWO durable stores - PostgreSQL and the artifact
# volume - and they cannot be committed in one filesystem/database
# transaction. The protocol is therefore:
#   1. preflight: validate every input (nothing durable has changed yet);
#   2. STAGE the artifact snapshot in host temp space, then SNAPSHOT the live
#      artifact truth as this transaction's artifact rollback source;
#   3. promote PostgreSQL, retaining its quarantine (the PG rollback source);
#   4. SWITCH the staged artifact state, then verify BOTH stores against the
#      selected backup (independent PG verifier + staged-vs-restored identity);
#   5. only after both verifications pass, COMMIT: finalize PostgreSQL
#      (release the quarantine) and release the artifact rollback source.
# Redis is transient, is never restored, and is invalidated last.
# Any failure before commitment lands in rollback_precommit exactly once: the
# original artifact volume and the original PostgreSQL database are restored
# from their held sources, Redis is left untouched, a truthful rollback
# receipt is written, and the run exits nonzero. "Atomic" is deliberately NOT
# claimed for a cross-store commit that does not exist.
PG_PROMOTED=false
PG_FINALIZED=false
ARTIFACT_STAGED=false
ARTIFACT_LIVE_SNAPSHOT=false
ARTIFACT_SWITCHED=false
ARTIFACT_APPLIED=false
COMMITTED=false
STAGE_DIR=""
LIVE_SNAPSHOT_DIR=""
STAGED_SHA=""
ARTIFACT_BEFORE_SHA=""
ARTIFACT_AFTER_SHA=""
PG_COMMON=()
PROMOTE_RECEIPT="$RECEIPT_DIR/promote-receipt.json"
ROLLBACK_RECEIPT="$RECEIPT_DIR/rollback-receipt.json"
RECEIPT_OUT="$RECEIPT_DIR/postgres-recovery-receipt.json"  # finalize receipt
TRANSACTION_RECEIPT="$RECEIPT_DIR/transaction-rollback-receipt.json"
ARTIFACT_ARCHIVE="$CONTENT/artifacts/artifacts.tar.gz"

artifact_volume_sha() { # content identity of the LIVE artifact volume
  docker run --rm -v oce_local_artifact_data:/data postgres:16.2-alpine \
    sh -c 'cd /data 2>/dev/null || exit 0; find . -type f -exec sha256sum {} + 2>/dev/null' \
    2>/dev/null | LC_ALL=C sort | sha256sum | awk '{print $1}'
}
staged_tree_sha() { # the same identity for a staged snapshot on the host
  (cd "$1" && find . -type f -exec sha256sum {} + 2>/dev/null) \
    2>/dev/null | LC_ALL=C sort | sha256sum | awk '{print $1}'
}
artifact_wipe() {
  docker run --rm -v oce_local_artifact_data:/data postgres:16.2-alpine \
    sh -c "rm -rf /data/* /data/.[!.]* 2>/dev/null; true"
}
artifact_restore_from() { # host dir -> live volume (replace, never merge)
  artifact_wipe && docker cp "$1/." oce-local-artifact:/data/
}
artifact_stop() { docker stop oce-local-artifact >/dev/null 2>&1 || true; }
artifact_start() { docker start oce-local-artifact >/dev/null 2>&1 || true; }
# Volume identity is only meaningful while the artifact service is STOPPED:
# MinIO writes its own format metadata into /data on startup, so a hash taken
# after `docker start` describes MinIO's bookkeeping, not the restored truth.
# Every identity this transaction compares (staged vs restored, before vs
# after rollback) is therefore captured with the service stopped.
artifact_volume_sha_stopped() {
  artifact_stop
  artifact_volume_sha
}
pg_rollback_from_quarantine() { # explicit rollback of the held quarantine
  [ -n "$PROMOTE_RECEIPT" ] || return 1
  python3 "$BIN/pg-recovery.py" --phase rollback --receipt-in "$PROMOTE_RECEIPT" \
    "${PG_COMMON[@]}" --receipt-out "$ROLLBACK_RECEIPT"
}
write_transaction_rollback_receipt() { # truthful account of what was restored
  python3 - "$TRANSACTION_RECEIPT" "$1" "$ARTIFACT_BEFORE_SHA" "$2" "$3" \
           "$(date -u +"$TS_FMT")" <<'PY'
import json, sys
p, reason, before, after, pg_ok, ts = sys.argv[1:7]
json.dump({"format": "oce-restore-transaction-rollback-receipt-v1",
           "reason": reason,
           "committed": False,
           "artifact_switched": bool(before),
           "artifact_sha256_before": before or None,
           "artifact_sha256_after": after or None,
           "artifact_restored": bool(before) and after == before,
           "postgres_rolled_back": pg_ok == "true",
           "redis_untouched": True,
           "timestamp": ts},
          open(p, "w", encoding="utf-8"), indent=2)
PY
}
rollback_precommit() { # single owner of every pre-commit rollback
  local reason="${FAIL_NOTE:-$1}"
  [[ "$COMMITTED" == "true" ]] && return 0
  [[ "$ARTIFACT_SWITCHED" == "true" || "$PG_PROMOTED" == "true" ]] || return 0
  local art_after=""
  if [[ "$ARTIFACT_SWITCHED" == "true" && "$ARTIFACT_LIVE_SNAPSHOT" == "true" ]]; then
    echo "rollback: restoring the original artifact volume from its snapshot..." >&2
    # stopped-state restore + identity (see artifact_volume_sha_stopped)
    artifact_stop
    if artifact_restore_from "$LIVE_SNAPSHOT_DIR"; then
      ARTIFACT_SWITCHED=false
    else
      echo "WARNING: artifact rollback FAILED; the volume is not the original" >&2
    fi
    art_after="$(artifact_volume_sha)"
    artifact_start
  fi
  local pg_ok=false
  if [[ "$PG_PROMOTED" == "true" && "$PG_FINALIZED" != "true" ]]; then
    echo "rollback: restoring the original PostgreSQL database from quarantine..." >&2
    pg_rollback_from_quarantine && pg_ok=true
  fi
  write_transaction_rollback_receipt "$reason" "$art_after" "$pg_ok"
  if [[ -n "$EV_DIR" ]]; then
    cp "$TRANSACTION_RECEIPT" "$EV_DIR/transaction-rollback-receipt.json" 2>/dev/null || true
  fi
  if [[ "$ARTIFACT_LIVE_SNAPSHOT" == "true" && "$art_after" != "$ARTIFACT_BEFORE_SHA" ]]; then
    echo "BLOCKED: pre-commit rollback could not restore the artifact volume" >&2
  fi
}
trap 'rc=$?; if [ "$rc" -ne 0 ]; then rollback_precommit "${FAIL_NOTE:-restore exited $rc} before transaction commitment"; fi; register_op "$rc"; exit "$rc"' EXIT
FAIL_NOTE=""  # each BLOCKED exit names its own failure site
trap 'exit 130' INT
trap 'exit 143' TERM

# ── preflight: every required input validated before ANY durable mutation ──
if [[ -f "$ARTIFACT_ARCHIVE" ]] && ! docker inspect oce-local-artifact >/dev/null 2>&1; then
  echo "BLOCKED: artifact container unavailable (nothing was replaced)" >&2
  exit 3
fi
if [[ "$SCOPE" == "full" && ( ! -f "$CONTENT/postgres/archive.dump" \
     || ! -f "$CONTENT/postgres/inventory.json" \
     || ! -f "$CONTENT/postgres/inventory.json.sha256" ) ]]; then
  echo "BLOCKED: full backup is missing required PostgreSQL archive/inventory" >&2
  exit 3
fi

# ── step 2: STAGE the artifact snapshot; SNAPSHOT the live truth ───────────
if [[ -f "$ARTIFACT_ARCHIVE" ]]; then
  STAGE_DIR="$(mktemp -d)"
  LIVE_SNAPSHOT_DIR="$(mktemp -d)"
  if ! tar xzf "$ARTIFACT_ARCHIVE" -C "$STAGE_DIR"; then
    echo "BLOCKED: artifact extraction failed (live artifacts untouched)" >&2
    rm -rf "$STAGE_DIR" "$LIVE_SNAPSHOT_DIR"
    exit 3
  fi
  STAGED_SHA="$(staged_tree_sha "$STAGE_DIR")"
  ARTIFACT_STAGED=true
  ARTIFACT_BEFORE_SHA="$(artifact_volume_sha_stopped)"
  # The artifact ROLLBACK SOURCE: the live truth, copied out BEFORE it is
  # replaced, so a later failure can put the volume back byte for byte.
  if ! docker cp oce-local-artifact:/data/. "$LIVE_SNAPSHOT_DIR/"; then
    echo "BLOCKED: cannot snapshot the live artifact volume (nothing was replaced)" >&2
    rm -rf "$STAGE_DIR" "$LIVE_SNAPSHOT_DIR"
    exit 3
  fi
  ARTIFACT_LIVE_SNAPSHOT=true
  artifact_start
  echo "  artifacts: staged ${STAGED_SHA:0:12} (live snapshot ${ARTIFACT_BEFORE_SHA:0:12})"
fi


# ── step 3: PostgreSQL verified staging promotion (R25: phase-safe) ────────
export OCE_COMMIT="$(git -C "$PROJ_ROOT" rev-parse HEAD 2>/dev/null || echo unknown)"
export OCE_TREE="$(git -C "$PROJ_ROOT" rev-parse HEAD^{tree} 2>/dev/null || echo unknown)"
# R39-R3: a recovery TRANSITION needs an authoritative run identity, and one
# restore is ONE operation, so mint one when the caller has not supplied it.
# The same id then binds promote, finalize and rollback of this operation.
export OCE_RUN_ID="${OCE_RUN_ID:-$(python3 -c 'import uuid,sys;sys.stdout.write(uuid.uuid4().hex)')}"
export OCE_EVIDENCE_DIR="${OCE_EVIDENCE_DIR:-}"
export OCE_BACKUP_ROOTS="$FROM"
PG_COMMON=(--inventory "$CONTENT/postgres/inventory.json"
           --inventory-sha "$CONTENT/postgres/inventory.json.sha256"
           --db "$PG_DB" --user "$PG_USER" --container oce-local-postgresql)
save_pg_receipt() { # one or more receipt files -> evidence (never clobbered)
  local src
  for src in "$@"; do
    [[ -f "$src" ]] || continue
    if [[ -n "$EV_DIR" ]]; then
      cp "$src" "$EV_DIR/$(basename "$src")" 2>/dev/null || true
      cp "$src" "$EV_DIR/$(basename "$src" .json)-$(date +%s%N).json" 2>/dev/null || true
    fi
  done
  return 0
}
if [[ -f "$CONTENT/postgres/archive.dump" && -f "$CONTENT/postgres/inventory.json" \
   && -f "$CONTENT/postgres/inventory.json.sha256" ]]; then
  # promote: staging restore + verify, canonical->quarantine, promote,
  # canonical verify. The quarantine (this transaction's PG rollback source)
  # is HELD until every fallible check - including the artifact switch and its
  # verification - has passed.
  if ! python3 "$BIN/pg-recovery.py" --phase promote \
       --archive "$CONTENT/postgres/archive.dump" \
       "${PG_COMMON[@]}" --receipt-out "$PROMOTE_RECEIPT"; then
    save_pg_receipt "$PROMOTE_RECEIPT"
    echo "BLOCKED: PostgreSQL promotion failed (original preserved / rolled back)" >&2
    exit 1
  fi
  PG_PROMOTED=true
  save_pg_receipt "$PROMOTE_RECEIPT"

  # external restore-boundary verification: the canonical target is re-checked
  # by a FRESH, independent process (pg-verify.py) against the hash-protected
  # inventory - exact row counts AND value fingerprints.
  if ! python3 "$BIN/pg-verify.py" --inventory "$CONTENT/postgres/inventory.json" \
       --inventory-sha "$CONTENT/postgres/inventory.json.sha256" \
       --db "$PG_DB" --user "$PG_USER" --container oce-local-postgresql --stable 2; then
    echo "UNVERIFIED: canonical target failed independent durable verification (counts+fingerprints)" >&2
    echo "BLOCKED: PostgreSQL verification failed after promote" >&2
    exit 1  # the EXIT trap restores BOTH stores from their held sources
  fi
fi

# ── step 4: SWITCH the staged artifact state, then verify it ───────────────
if [[ "$ARTIFACT_STAGED" == "true" ]]; then
  # quiesce: stop the artifact service so replacement is not a live merge
  docker stop oce-local-artifact >/dev/null 2>&1 || true
  # The switch BEGINS with the first destructive step (the wipe), not with the
  # copy: if the copy fails the live volume is already empty, so the snapshot is
  # the only way back and the rollback must run for a HALF-switched volume too.
  ARTIFACT_SWITCHED=true
  if ! artifact_restore_from "$STAGE_DIR"; then
    FAIL_NOTE="artifact restore into the container failed"
    echo "BLOCKED: $FAIL_NOTE" >&2
    exit 1  # the EXIT trap restores BOTH stores from their held sources
  fi
  # identity is verified while the service is still stopped: the volume must
  # be byte-identical to the staged snapshot BEFORE MinIO touches it again
  ARTIFACT_AFTER_SHA="$(artifact_volume_sha)"
  if [[ "$ARTIFACT_AFTER_SHA" != "$STAGED_SHA" ]]; then
    FAIL_NOTE="the restored artifact volume is not the staged snapshot"
    echo "BLOCKED: $FAIL_NOTE" >&2
    exit 1  # the EXIT trap restores BOTH stores from their held sources
  fi
  artifact_start
  ARTIFACT_APPLIED=true
  # artifact-replacement evidence (R8): archive + staged/restored identities
  python3 - "$RECEIPT_DIR/artifact-recovery-receipt.json" "$ARTIFACT_ARCHIVE" \
           "$ARTIFACT_APPLIED" "$STAGED_SHA" "$ARTIFACT_BEFORE_SHA" "$ARTIFACT_AFTER_SHA" \
           "$(date -u +"$TS_FMT")" <<'PY'
import hashlib, json, os, sys
(p, archive, applied, staged, before, after, ts) = sys.argv[1:8]
h = hashlib.sha256()
with open(archive, "rb") as f:
    for chunk in iter(lambda: f.read(8192), b""):
        h.update(chunk)
json.dump({"format": "oce-artifact-recovery-receipt-v1",
           "artifact_archive_sha256": h.hexdigest(),
           "artifact_archive_size": os.path.getsize(archive),
           "artifact_staged_sha256": staged,
           "artifact_volume_sha256_before": before,
           "artifact_volume_sha256_after": after,
           "artifact_replaced": applied == "true",
           "artifact_verify": ("ok" if staged == after else "mismatch") if applied == "true" else "not-applied",
           "artifact_rollback_source_held": True,
           "timestamp": ts},
          open(p, "w", encoding="utf-8"), indent=2)
PY
  if [[ -n "$EV_DIR" ]]; then
    cp "$RECEIPT_DIR/artifact-recovery-receipt.json" "$EV_DIR/artifact-recovery-receipt.json" 2>/dev/null || true
  fi
fi

# ── step 5: finalize PostgreSQL (final re-verification, then quarantine) ───
if [[ "$PG_PROMOTED" == "true" ]]; then
  if ! python3 "$BIN/pg-recovery.py" --phase finalize \
       --receipt-in "$PROMOTE_RECEIPT" \
       "${PG_COMMON[@]}" --receipt-out "$RECEIPT_OUT"; then
    save_pg_receipt "$RECEIPT_OUT" "$ROLLBACK_RECEIPT"
    echo "BLOCKED: PostgreSQL finalization failed" >&2
    exit 1  # the EXIT trap restores BOTH stores from their held sources
  fi
  PG_FINALIZED=true
  save_pg_receipt "$RECEIPT_OUT"
fi

# ── step 6: COMMIT — both durable stores verified against the backup ──────
COMMITTED=true

# ── transient Redis invalidation (R27) ─────────────────────────────────────
# Redis is transient and non-authoritative: it is NEVER restored from backup,
# and stale cache must not survive a replacement of PostgreSQL truth. The
# cache was left untouched while recovery could still roll back; it is now
# invalidated ONLY after PostgreSQL and artifact replacement passed final
# verification. Invalidation failure BLOCKS a clean success (nonzero) while
# preserving evidence of PostgreSQL status and the cache-invalidation failure.
if [[ "$SCOPE" == "full" && "$MODE" == "full-replace" ]]; then
  REDIS_RECEIPT="$RECEIPT_DIR/redis-invalidation-receipt.json"
  REDIS_INVALIDATED=false
  REDIS_VERIFICATION="not-attempted"
  REDIS_FAILURE=""
  REDIS_START=$(date -u +"$TS_FMT")
  if docker inspect oce-local-redis >/dev/null 2>&1; then
    if docker exec oce-local-redis redis-cli FLUSHALL >/dev/null 2>&1; then
      DBSIZE=$(docker exec oce-local-redis redis-cli DBSIZE 2>/dev/null | tr -d '[:space:]')
      if [[ "$DBSIZE" == "0" ]]; then
        REDIS_INVALIDATED=true
        REDIS_VERIFICATION="ok"
      else
        REDIS_VERIFICATION="failed"
        REDIS_FAILURE="redis DBSIZE=$DBSIZE after FLUSHALL"
      fi
    else
      REDIS_VERIFICATION="failed"
      REDIS_FAILURE="redis-cli FLUSHALL failed (container not running?)"
    fi
  else
    REDIS_VERIFICATION="failed"
    REDIS_FAILURE="redis container unavailable"
  fi
  python3 - "$REDIS_RECEIPT" "$REDIS_START" "$REDIS_INVALIDATED" "$REDIS_VERIFICATION" "$REDIS_FAILURE" "$(date -u +"$TS_FMT")" <<'PY'
import json, sys
p, start, invalidated, ver, failure, finish = sys.argv[1:7]
json.dump({
  "format": "oce-redis-invalidation-receipt-v1",
  "redis_restored": False,
  "redis_invalidation_required": True,
  "redis_invalidation_attempted": True,
  "redis_invalidated": invalidated == "true",
  "redis_verification": ver,
  "redis_failure": failure or None,
  "postgres_promoted": True,
  "postgres_exit_status": 0,
  "started_at": start, "finished_at": finish,
}, open(p, "w", encoding="utf-8"), indent=2)
PY
  if [[ -n "$EV_DIR" ]]; then
    cp "$REDIS_RECEIPT" "$EV_DIR/redis-invalidation-receipt.json" 2>/dev/null || true
  fi
  if [[ "$REDIS_INVALIDATED" == "true" && "$REDIS_VERIFICATION" == "ok" ]]; then
    echo "  redis: invalidated (transient cache cleared; never restored from backup)"
  else
    echo "BLOCKED: redis invalidation failed (${REDIS_FAILURE:-unknown}) — postgres promoted but recovery NOT clean" >&2
    exit 1
  fi
fi

END_TS=$(date -u +"$TS_FMT")
cp "$RECEIPT_OUT" "$RECEIPT_DIR/restore-receipt.json" 2>/dev/null || true
if [[ -n "$EV_DIR" ]]; then
  cp "$RECEIPT_DIR/restore-receipt.json" "$EV_DIR/restore-receipt.json" 2>/dev/null || true
fi
# the transaction is committed: the rollback sources are released here and
# nowhere earlier (nothing fallible is left to run)
rm -rf "$STAGE_DIR" "$LIVE_SNAPSHOT_DIR"
echo "full-replace restore complete <- $FROM"
echo "  postgres: verified staging promotion | artifacts: $ARTIFACT_APPLIED | redis: invalidated (not restored)"
exit 0
