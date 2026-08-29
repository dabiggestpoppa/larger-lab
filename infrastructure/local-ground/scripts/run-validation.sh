#!/usr/bin/env bash
#
# run-validation.sh — OCE Local Ground shared validation runner (B1-LOCAL).
# Sole authoritative orchestration for the Local Ground book gate. Both the
# local thin wrapper and GitHub Actions invoke this exactly once.
#
# Environment:
#   OCE_RUN_ID        — required, single authoritative run id (12+ hex)
#   OCE_EVIDENCE_DIR  — optional caller-provided evidence dir (outside repo)
#   OCE_CI_MODE       — "true" in CI
#   GITHUB_REF_NAME   — trusted ref in CI
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJ_ROOT="$(cd "$BASE_DIR/../.." && pwd)"
GATE="$BASE_DIR/scripts/final-gate-local.sh"
TEST_FILE="$BASE_DIR/tests/test_local_ground.py"

FAILED_PHASE=""
EVIDENCE=""

if [ -z "${OCE_RUN_ID:-}" ]; then echo "FATAL: OCE_RUN_ID not set" >&2; exit 2; fi
echo "$OCE_RUN_ID" | grep -qE '^[0-9a-f]{12,}$' || { echo "FATAL: malformed OCE_RUN_ID" >&2; exit 2; }
export OCE_RUN_ID

EVIDENCE="${OCE_EVIDENCE_DIR:-$(mktemp -d "${TMPDIR:-/tmp}/oce-localground-evidence-XXXXXX")}"
mkdir -p "$EVIDENCE"
EVIDENCE="$(cd "$EVIDENCE" && pwd)"
printf '%s\n' "$EVIDENCE" > "$EVIDENCE/evidence-dir.path"
export OCE_EVIDENCE_DIR="$EVIDENCE"

record() { printf '%s\n' "$*" >> "$EVIDENCE/stage-log.txt"; }

fail() { # phase rc
  FAILED_PHASE="$1"; rc="$2"
  echo "FAILED in phase '$FAILED_PHASE' (exit $rc)" >&2
  printf '{"block":"B1","stage":"B1-LOCAL","run_id":"%s","gate_status":"FAILED","failure_phase":"%s","exit_status":%s}\n' \
    "$OCE_RUN_ID" "$FAILED_PHASE" "$rc" > "$EVIDENCE/stage-status.json"
  exit "$rc"
}

echo "=== OCE Local Ground Shared Validation Runner ==="
echo "OCE_RUN_ID: $OCE_RUN_ID | evidence: $EVIDENCE"

# ── identity ──────────────────────────────────────────────────────────────
COMMIT=$(git -C "$PROJ_ROOT" rev-parse HEAD) || fail identity 1
TREE=$(git -C "$PROJ_ROOT" rev-parse "HEAD^{tree}") || fail identity 1
BRANCH=$(git -C "$PROJ_ROOT" branch --show-current 2>/dev/null || echo detached)
MAIN_SHA=$(git -C "$PROJ_ROOT" rev-parse origin/main 2>/dev/null || git -C "$PROJ_ROOT" rev-parse main 2>/dev/null || echo unknown)
python3 - "$EVIDENCE/identity.json" <<PY
import json, sys, os
json.dump({"commit": "$COMMIT", "tree": "$TREE", "branch": "$BRANCH",
           "main_sha": "$MAIN_SHA", "repository": "dabigestpoppa/larger-lab",
           "ci_ref": os.environ.get("GITHUB_REF_NAME"), "run_id": "$OCE_RUN_ID"},
          open(sys.argv[1], "w", encoding="utf-8"), indent=2)
PY
record "identity: $COMMIT"

# ── clean source ──────────────────────────────────────────────────────────
DIRTY=$(git -C "$PROJ_ROOT" status --porcelain | wc -l)
if [ "$DIRTY" -ne 0 ]; then
  echo "FATAL: source dirty ($DIRTY)"; git -C "$PROJ_ROOT" status --porcelain >&2
  fail clean-source-pre 1
fi
record "source clean (pre)"

# ── doctor fingerprint ────────────────────────────────────────────────────
bash "$SCRIPT_DIR/doctor.sh" "$EVIDENCE/environment-fingerprint.json" || fail doctor 1
record "doctor fingerprint captured"

# ── acceptance tests (container-backed tests skip without docker) ─────────
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 OCE_CI_MODE="${OCE_CI_MODE:-false}" OCE_RUNNER_ACTIVE=1
python3 -m pytest "$TEST_FILE" "$BASE_DIR/tests/test_contracts.py" -v --tb=short > "$EVIDENCE/acceptance-output.txt" 2>&1
RC=$?
tail -40 "$EVIDENCE/acceptance-output.txt"
if [ "$RC" -ne 0 ]; then fail acceptance-tests "$RC"; fi
record "acceptance + contract tests passed"

# ── cloud boundary (deterministic plan; apply denied; zero mutation) ──────
OCE_RUNTIME_TARGET=cloud-plan bash "$SCRIPT_DIR/oce-ctl" deploy plan --target cloud > "$EVIDENCE/cloud-plan.txt" 2>&1
RC=$?
if [ "$RC" -ne 0 ]; then fail cloud-plan "$RC"; fi
# apply must be DENIED with no authorization envelope
OCE_RUNTIME_TARGET=cloud bash "$SCRIPT_DIR/oce-ctl" deploy apply --target cloud > "$EVIDENCE/cloud-apply-denial.txt" 2>&1
RC=$?
if [ "$RC" -eq 0 ]; then echo "FATAL: cloud apply unexpectedly allowed"; fail cloud-apply 1; fi
record "cloud-plan deterministic; cloud apply denied (fail-closed)"

# ── adversarial suite ─────────────────────────────────────────────────────
if [ -x "$BASE_DIR/tests/adversarial-local.sh" ]; then
  bash "$BASE_DIR/tests/adversarial-local.sh" > "$EVIDENCE/adversarial-output.txt" 2>&1
  RC=$?
  tail -20 "$EVIDENCE/adversarial-output.txt"
  if [ "$RC" -ne 0 ]; then fail adversarial "$RC"; fi
  record "adversarial suite passed"
else
  echo "WARN: no adversarial-local.sh; recording SKIPPED (not PASS)" >> "$EVIDENCE/stage-log.txt"
fi

# ── clean source after ────────────────────────────────────────────────────
DIRTY=$(git -C "$PROJ_ROOT" status --porcelain | wc -l)
[ "$DIRTY" -ne 0 ] && fail clean-source-post 1
record "source clean (post)"

# ── evidence: status + manifest ───────────────────────────────────────────
python3 - "$EVIDENCE" "$COMMIT" "$TREE" "$BRANCH" <<'PY'
import hashlib, json, os, sys
from datetime import datetime, timezone
ev, commit, tree, branch = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
artifacts = []
for name in sorted(os.listdir(ev)):
    p = os.path.join(ev, name)
    if not os.path.isfile(p) or name == "evidence-manifest.json":
        continue
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    artifacts.append({"path": name, "sha256": h.hexdigest(), "size": os.path.getsize(p)})
manifest = {
  "block": "B1", "stage": "B1-LOCAL-GROUND-CLOSURE", "run_id": os.environ.get("OCE_RUN_ID", ""),
  "repository": "dabigestpoppa/larger-lab", "branch": branch, "implementation_commit": commit,
  "implementation_tree": tree, "cloud_mutations": 0, "cloud_cost_state": "ZERO",
  "cloud_activation_state": "DEFERRED_BY_OPERATOR", "artifacts": artifacts,
  "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
}
json.dump(manifest, open(os.path.join(ev, "evidence-manifest.json"), "w", encoding="utf-8"), indent=2)
status = {
  "block": "B1", "stage": "B1-LOCAL-GROUND-CLOSURE", "run_id": manifest["run_id"],
  "gate_status": "PENDING_FINAL_GATE", "cloud_mutations": 0, "cloud_cost_state": "ZERO",
  "cloud_activation_state": "DEFERRED_BY_OPERATOR", "implementation_commit": commit,
  "implementation_tree": tree, "branch": branch,
}
json.dump(status, open(os.path.join(ev, "stage-status.json"), "w", encoding="utf-8"), indent=2)
PY

# ── independent final gate ────────────────────────────────────────────────
bash "$GATE" "$EVIDENCE" "$COMMIT" "$TREE"
RC=$?
[ "$RC" -ne 0 ] && fail final-gate "$RC"
python3 - "$EVIDENCE/stage-status.json" <<'PY'
import json, sys
p = sys.argv[1]
d = json.load(open(p, encoding="utf-8"))
d["gate_status"] = "LOCAL_GROUND_READY_FOR_OPERATOR_REVIEW"
json.dump(d, open(p, "w", encoding="utf-8"), indent=2)
PY
record "independent gate LOCAL_GROUND_READY_FOR_OPERATOR_REVIEW"
echo "=== RUNNER RESULT: LOCAL_GROUND_READY_FOR_OPERATOR_REVIEW ==="
echo "OCE_RUN_ID: $OCE_RUN_ID | commit ${COMMIT:0:12} | branch $BRANCH"
echo "evidence: $EVIDENCE"
ls "$EVIDENCE"
exit 0