#!/usr/bin/env bash
#
# run-b2-validation.sh — OCE Book 2 control-plane validation runner (B2-R5).
# Sole authoritative orchestration for the B2 gate. Both local invocation and
# GitHub Actions run this exactly once.
#
# Closes audit gaps 17/18: the 31 container-backed tests (PG store, Redis
# transport, worker, scheduler) MUST execute against the real compose stack
# in CI. A green run that skipped them is a FAILURE — exactly like run
# 33316972933, which succeeded without executing Book 2 tests.
#
# Environment:
#   OCE_RUN_ID        — required, single authoritative run id (12+ hex)
#   OCE_EVIDENCE_DIR  — optional caller-provided evidence dir (outside repo)
#   OCE_CI_MODE       — "true" in CI (authoritative; zero skips enforced)
#   GITHUB_REF_NAME   — trusted ref in CI
#   GITHUB_REPOSITORY — trusted repository in CI
#
# Phases: identity -> compose up + health wait -> pytest (full suite,
# junit.xml) -> independent gate -> teardown (durable volume preserved) ->
# stage status + evidence manifest. Exit nonzero on any gate violation.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
GATE="$BASE_DIR/scripts/independent-gate-b2.py"
EXPECTED_REPO="${OCE_EXPECTED_REPO:-dabiggestpoppa/larger-lab}"
EXPECTED_BRANCH="${OCE_EXPECTED_BRANCH:-oce-program-build}"

RUN_ID="${OCE_RUN_ID:-}"
if [ -z "$RUN_ID" ]; then echo "FATAL: OCE_RUN_ID not set" >&2; exit 2; fi
echo "$RUN_ID" | grep -qE '^[0-9a-f]{12,}$' || { echo "FATAL: malformed OCE_RUN_ID" >&2; exit 2; }
export OCE_RUN_ID

EVIDENCE="${OCE_EVIDENCE_DIR:-$(mktemp -d "${TMPDIR:-/tmp}/oce-b2-evidence-XXXXXX")}"
mkdir -p "$EVIDENCE"
EVIDENCE="$(cd "$EVIDENCE" && pwd)"
export OCE_EVIDENCE_DIR="$EVIDENCE"
echo "$EVIDENCE" > "$EVIDENCE/evidence-dir.path"

record() { printf '%s\n' "$*" >> "$EVIDENCE/stage-log.txt"; }
record "run_id=$RUN_ID ci_mode=${OCE_CI_MODE:-false} started $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 1. Identity — fail closed on wrong repository/branch.
if [ -n "${GITHUB_REPOSITORY:-}" ] && [ "$GITHUB_REPOSITORY" != "$EXPECTED_REPO" ]; then
  record "FAIL: identity — repo $GITHUB_REPOSITORY != $EXPECTED_REPO"
  echo "FAIL: identity — repo $GITHUB_REPOSITORY != $EXPECTED_REPO" >&2
  exit 1
fi
if [ -n "${GITHUB_REF_NAME:-}" ] && [ "$GITHUB_REF_NAME" != "$EXPECTED_BRANCH" ]; then
  record "FAIL: identity — branch $GITHUB_REF_NAME != $EXPECTED_BRANCH"
  echo "FAIL: identity — branch $GITHUB_REF_NAME != $EXPECTED_BRANCH" >&2
  exit 1
fi
record "identity: $EXPECTED_REPO @ $EXPECTED_BRANCH"

cleanup() {
  record "teardown: compose down (durable postgres volume preserved)"
  (cd "$BASE_DIR" && docker compose -f compose/compose.yml down >/dev/null 2>&1 || true)
}
trap cleanup EXIT

# 2. Compose up + wait for PostgreSQL/Redis health (idempotent; the suite
#    fixtures reuse the same stack).
record "compose: starting stack and waiting for health"
if ! (cd "$BASE_DIR" && python3 - "$EVIDENCE" <<'PY' >> "$EVIDENCE/stage-log.txt" 2>&1
import sys
sys.path.insert(0, "tests")
import oce_b2_compose as oc
oc.stack_up()
print("compose: postgres + redis healthy")
PY
); then
  record "FAIL: compose stack failed to become healthy"
  echo "FAIL: compose stack failed to become healthy — see evidence stage-log.txt" >&2
  exit 1
fi

# 3. Full control-plane suite. -rs reports skip reasons into the output so
#    the gate can prove WHICH tests skipped (and why) if any do.
record "pytest: running full control-plane suite (zero skips required in CI)"
(cd "$BASE_DIR" && python3 -m pytest tests/ -q -rs --tb=short -p no:cacheprovider \
    --junitxml="$EVIDENCE/junit.xml" > "$EVIDENCE/pytest-output.txt" 2>&1)
PYTEST_RC=$?

# 4. Independent gate — machine-readable evidence only.
record "gate: independent-gate-b2.py (rc=$PYTEST_RC)"
python3 "$GATE" "$EVIDENCE" "$PYTEST_RC" > "$EVIDENCE/gate-output.txt" 2>&1
GATE_RC=$?
cat "$EVIDENCE/gate-output.txt"

# 5. Stage status + evidence manifest.
python3 - "$EVIDENCE" "$GATE_RC" "$PYTEST_RC" <<'PY'
import hashlib, json, os, sys
from datetime import datetime, timezone
ev, gate_rc, pytest_rc = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
status = "PASS" if gate_rc == 0 else "FAIL"
stage = {
    "block": "B2", "stage": "B2-CONTROL-PLANE-CLOSURE",
    "run_id": os.environ.get("OCE_RUN_ID", ""),
    "gate_status": status, "pytest_exit": pytest_rc, "exit_status": gate_rc,
    "cloud_mutations": 0, "cloud_cost_state": "ZERO",
    "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
}
json.dump(stage, open(os.path.join(ev, "stage-status.json"), "w", encoding="utf-8"), indent=2)
manifest = {"manifest_version": "1.0.0", "run_id": stage["run_id"], "files": {}}
for name in sorted(os.listdir(ev)):
    p = os.path.join(ev, name)
    if os.path.isfile(p):
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        manifest["files"][name] = {"sha256": h.hexdigest(), "size": os.path.getsize(p)}
json.dump(manifest, open(os.path.join(ev, "evidence-manifest.json"), "w", encoding="utf-8"), indent=2)
print(f"stage: {status}")
PY

if [ "$GATE_RC" -ne 0 ]; then
  record "FAIL: gate rejected the run (rc=$GATE_RC)"
  echo "==================== pytest output ===================="
  cat "$EVIDENCE/pytest-output.txt"
  echo "======================================================="
  exit 1
fi

PASSED="$(grep -oE '[0-9]+ passed' "$EVIDENCE/pytest-output.txt" | head -1 || echo '0 passed')"
record "PASS: B2 control-plane suite executed ($PASSED), zero skips, gate accepted"
echo "GATE PASS: $PASSED, zero skips — B2 tests executed against the real compose stack"
exit 0
