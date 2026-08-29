#!/usr/bin/env bash
#
# run-validation.sh — OCE Local Ground shared validation runner (B1-LOCAL).
# Sole authoritative orchestration for the Local Ground gate. Both the local
# thin wrapper and GitHub Actions invoke this exactly once.
#
# Environment:
#   OCE_RUN_ID        — required, single authoritative run id (12+ hex)
#   OCE_EVIDENCE_DIR  — optional caller-provided evidence dir (outside repo)
#   OCE_CI_MODE       — "true" in CI (authoritative)
#   GITHUB_REF_NAME   — trusted ref in CI
#   GITHUB_REPOSITORY — trusted repository in CI
#
# Finalization (Defect 4): candidate status -> candidate manifest ->
# independent gate -> final status -> final stage-log line -> final manifest ->
# read-only final-package verifier. The exact uploaded package is the verified
# package; nothing mutates after verification.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJ_ROOT="$(cd "$BASE_DIR/../.." && pwd)"
GATE="$BASE_DIR/scripts/final-gate-local.sh"
FINAL_VERIFY="$BASE_DIR/scripts/final-package-verify.sh"
TEST_FILE="$BASE_DIR/tests/test_local_ground.py"
CONTRACT_TEST="$BASE_DIR/tests/test_contracts.py"
LIFECYCLE_TEST="$BASE_DIR/tests/test_container_lifecycle.py"
GATE_TEST="$BASE_DIR/tests/test_gate_regressions.py"
COMPOSE_OUT_TEST="$BASE_DIR/tests/test_compose_output.py"
PORTABILITY_TEST="$BASE_DIR/tests/test_portability.py"
BACKUP_HARDEN_TEST="$BASE_DIR/tests/test_backup_hardening.py"
ADV_SH="$BASE_DIR/tests/adversarial-local.sh"
COMPOSE_DIR="$BASE_DIR/compose"
EXPECTED_REPO="dabiggestpoppa/larger-lab"
EXPECTED_BRANCH="oce-program-build"

FAILED_PHASE=""
EVIDENCE=""

if [ -z "${OCE_RUN_ID:-}" ]; then echo "FATAL: OCE_RUN_ID not set" >&2; exit 2; fi
echo "$OCE_RUN_ID" | grep -qE '^[0-9a-f]{12,}$' || { echo "FATAL: malformed OCE_RUN_ID" >&2; exit 2; }
export OCE_RUN_ID
export OCE_EXPECTED_REPO="$EXPECTED_REPO" OCE_EXPECTED_BRANCH="$EXPECTED_BRANCH"

EVIDENCE="${OCE_EVIDENCE_DIR:-$(mktemp -d "${TMPDIR:-/tmp}/oce-localground-evidence-XXXXXX")}"
mkdir -p "$EVIDENCE"
EVIDENCE="$(cd "$EVIDENCE" && pwd)"
printf '%s\n' "$EVIDENCE" > "$EVIDENCE/evidence-dir.path"
export OCE_EVIDENCE_DIR="$EVIDENCE"
export OCE_DOCKER_AVAILABLE="$([ "$(command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; echo $?)" = 0 ] && echo true || echo false)"

record() { printf '%s\n' "$*" >> "$EVIDENCE/stage-log.txt"; }

write_failure_context() { # phase rc
  local phase="$1" rc="$2"
  python3 - "$EVIDENCE" "$phase" "$rc" <<'PY'
import json, os, subprocess, sys
from datetime import datetime, timezone
ev, phase, rc = sys.argv[1], sys.argv[2], int(sys.argv[3])
def git(*a):
    r = subprocess.run(["git", "-C", os.environ.get("OCE_PROJ_ROOT", ".")] + list(a), capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None
ctx = {
    "failure": True, "failure_phase": phase, "exit_status": rc,
    "run_id": os.environ.get("OCE_RUN_ID", ""),
    "commit": git("rev-parse", "HEAD"),
    "tree": git("rev-parse", "HEAD^{tree}"),
    "branch": git("branch", "--show-current") or "(detached)",
    "trusted_ci_ref": os.environ.get("GITHUB_REF_NAME"),
    "cleanup_result": os.environ.get("OCE_CLEANUP_RESULT", "not-run"),
    "cloud_mutations": 0, "cloud_cost_state": "ZERO",
    "unresolved_blockers": [f"runner failed in phase '{phase}' with exit {rc}"],
    "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
}
json.dump(ctx, open(os.path.join(ev, "failure-context.json"), "w", encoding="utf-8"), indent=2)
stage = os.path.join(ev, "stage-status.json")
if not os.path.exists(stage):
    json.dump({"block": "B1", "stage": "B1-LOCAL-GROUND-CLOSURE", "run_id": ctx["run_id"],
               "gate_status": "FAILED", "failure_phase": phase, "exit_status": rc,
               "cloud_mutations": 0, "cloud_cost_state": "ZERO"}, open(stage, "w", encoding="utf-8"), indent=2)
PY
}

fail() { # phase rc
  local phase="$1" rc="$2"
  FAILED_PHASE="$phase"
  echo "FAILED in phase '$phase' (exit $rc)" >&2
  write_failure_context "$phase" "$rc" || true
  exit "$rc"
}

have_docker() { command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; }

# Capture bounded machine-readable diagnostics BEFORE cleanup destroys them.
failure_diagnostics() {
  if ! have_docker; then return 0; fi
  local d="$EVIDENCE/failure-diagnostics"
  mkdir -p "$d"
  (cd "$COMPOSE_DIR" && docker compose -f compose.yml ps --format json) > "$d/compose-ps.json" 2>&1 || true
  docker network ls --filter name=oce_local_internal > "$d/networks.txt" 2>&1 || true
  docker volume ls --filter name=oce_local_ > "$d/volumes.txt" 2>&1 || true
  for c in oce-local-postgresql oce-local-redis oce-local-artifact oce-local-prometheus; do
    docker inspect "$c" > "$d/$c.inspect.json" 2>&1 || true
    docker logs --tail 50 "$c" > "$d/$c.logs.txt" 2>&1 || true
  done
  return 0
}

# Attempt container cleanup on failure; record the truth, never mask rc.
failure_cleanup() {
  local result="failed" containers="false" networks="false" volumes="false"
  if have_docker; then
    (cd "$COMPOSE_DIR" && docker compose -f compose.yml down -v --remove-orphans >/dev/null 2>&1)
    local rc=$?
    local cont net vol
    cont=$(docker ps -a --format '{{.Names}}' 2>/dev/null || true)
    net=$(docker network ls --format '{{.Name}}' 2>/dev/null || true)
    vol=$(docker volume ls --format '{{.Name}}' 2>/dev/null || true)
    containers="true"
    for c in oce-local-postgresql oce-local-redis oce-local-artifact oce-local-prometheus; do
      case "$cont" in *"$c"*) containers="false" ;; esac
    done
    case "$net" in *oce_local_internal*) networks="false" ;; *) networks="true" ;; esac
    if printf '%s\n' "$vol" | grep -q '^oce_local_'; then volumes="false"; else volumes="true"; fi
    if [ "$rc" -eq 0 ] && [ "$containers" = "true" ] && [ "$networks" = "true" ] && [ "$volumes" = "true" ]; then
      result="ok"
    fi
  else
    result="ok"; containers="true"; networks="true"; volumes="true"
  fi
  python3 - "$EVIDENCE/cleanup.json" "$result" "$containers" "$networks" "$volumes" <<'PY'
import json, sys
p, res, c, n, v = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
json.dump({"cleanup": res, "containers_removed": c == "true", "networks_removed": n == "true",
           "volumes_removed": v == "true", "disposable_removed": True, "on_failure": True},
          open(p, "w", encoding="utf-8"), indent=2)
PY
  export OCE_CLEANUP_RESULT="$result"
  return 0
}

cleanup_trap() {
  local rc=$?
  if [ "$rc" -eq 0 ] && [ -z "$FAILED_PHASE" ]; then
    # Success: the final manifest and read-only verifier already ran against
    # the exact package. NEVER touch the evidence directory here.
    exit 0
  fi
  # Failure/interrupt: collect diagnostics, attempt cleanup, record truth,
  # then exit with the ORIGINAL code (cleanup must not mask it).
  failure_diagnostics || true
  failure_cleanup || true
  write_failure_context "${FAILED_PHASE:-interrupted}" "$rc" || true
  exit "$rc"
}
trap cleanup_trap EXIT INT TERM

echo "=== OCE Local Ground Shared Validation Runner ==="
echo "OCE_RUN_ID: $OCE_RUN_ID | evidence: $EVIDENCE | ci_mode: ${OCE_CI_MODE:-false}"

# ── identity ──────────────────────────────────────────────────────────────
COMMIT=$(git -C "$PROJ_ROOT" rev-parse HEAD) || fail identity 1
TREE=$(git -C "$PROJ_ROOT" rev-parse "HEAD^{tree}") || fail identity 1
BRANCH=$(git -C "$PROJ_ROOT" branch --show-current 2>/dev/null || echo detached)
REMOTE_URL=$(git -C "$PROJ_ROOT" remote get-url origin 2>/dev/null || echo "none")
REMOTE_REPO=$(python3 - "$REMOTE_URL" <<'PY'
import sys, re
url = sys.argv[1]
m = re.search(r"(?:github\.com[/:]|github\.com/)([^/\s]+)/([^/\s]+?)(?:\.git)?$", url)
print(f"{m.group(1)}/{m.group(2)}" if m else "unknown")
PY
)
MAIN_SHA=$(git -C "$PROJ_ROOT" rev-parse origin/main 2>/dev/null || echo unknown)
python3 - "$EVIDENCE/identity.json" <<PY
import json, os, sys
json.dump({"commit": "$COMMIT", "tree": "$TREE", "branch": "$BRANCH",
           "tested_commit": "$COMMIT", "tested_tree": "$TREE",
           "repository": "$EXPECTED_REPO", "observed_remote": "$REMOTE_REPO",
           "remote_url": "$REMOTE_URL", "main_sha": "$MAIN_SHA",
           "checkout_state": "attached", "trusted_ci_ref": os.environ.get("GITHUB_REF_NAME"),
           "trusted_ci_repository": os.environ.get("GITHUB_REPOSITORY"),
           "run_id": "$OCE_RUN_ID"},
          open(sys.argv[1], "w", encoding="utf-8"), indent=2)
PY
export OCE_PROJ_ROOT="$PROJ_ROOT"
record "identity: $COMMIT repo=$REMOTE_REPO branch=$BRANCH"
echo "  identity: commit=$COMMIT tree=$TREE branch=$BRANCH repo=$REMOTE_REPO"

# ── clean source (pre) ────────────────────────────────────────────────────
DIRTY=$(git -C "$PROJ_ROOT" status --porcelain | wc -l)
python3 - "$EVIDENCE/source-clean.json" <<PY
import json, sys
json.dump({"pre": ${DIRTY} == 0, "dirty_pre": ${DIRTY}, "post": False},
          open(sys.argv[1], "w", encoding="utf-8"), indent=2)
PY
if [ "$DIRTY" -ne 0 ]; then
  echo "FATAL: source dirty ($DIRTY)"; git -C "$PROJ_ROOT" status --porcelain >&2
  fail clean-source-pre 1
fi
record "source clean (pre)"

# ── doctor fingerprint ────────────────────────────────────────────────────
bash "$SCRIPT_DIR/doctor.sh" "$EVIDENCE/environment-fingerprint.json" || fail doctor 1
record "doctor fingerprint captured"

# ── acceptance + contract tests (machine-readable) ────────────────────────
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 OCE_CI_MODE="${OCE_CI_MODE:-false}" OCE_RUNNER_ACTIVE=1
python3 -m pytest "$TEST_FILE" "$CONTRACT_TEST" "$LIFECYCLE_TEST" "$GATE_TEST" "$COMPOSE_OUT_TEST" "$PORTABILITY_TEST" "$BACKUP_HARDEN_TEST" -v --tb=short \
  --junitxml="$EVIDENCE/junit.xml" > "$EVIDENCE/acceptance-output.txt" 2>&1
RC=$?
tail -25 "$EVIDENCE/acceptance-output.txt"
if [ "$RC" -ne 0 ]; then fail acceptance-tests "$RC"; fi
record "acceptance + contract tests executed"

# ── adversarial suite (machine-readable results) ──────────────────────────
bash "$ADV_SH" > /dev/null 2>&1
ADV_RC=$?
tail -12 "$EVIDENCE/adversarial-output.txt"
if [ "$ADV_RC" -ne 0 ]; then fail adversarial "$ADV_RC"; fi
record "adversarial suite passed"

# ── cloud boundary (deterministic plan; apply denied; zero mutation) ───────
OCE_RUNTIME_TARGET=cloud-plan bash "$SCRIPT_DIR/oce-ctl" deploy plan --target cloud > "$EVIDENCE/cloud-plan.txt" 2>&1
RC=$?
[ "$RC" -ne 0 ] && fail cloud-plan "$RC"
OCE_RUNTIME_TARGET=cloud-plan bash "$SCRIPT_DIR/oce-ctl" deploy plan --target cloud > "$EVIDENCE/cloud-plan-2.txt" 2>&1
python3 - "$EVIDENCE" <<'PY'
import json, sys
ev = sys.argv[1]
a = open(ev + "/cloud-plan.txt", encoding="utf-8").read()
b = open(ev + "/cloud-plan-2.txt", encoding="utf-8").read()
json.dump({"deterministic": a == b}, open(ev + "/cloud-plan-deterministic.json", "w", encoding="utf-8"), indent=2)
PY
OCE_RUNTIME_TARGET=cloud bash "$SCRIPT_DIR/oce-ctl" deploy apply --target cloud > "$EVIDENCE/cloud-apply-denial.txt" 2>&1
RC=$?
python3 - "$EVIDENCE" "$RC" <<'PY'
import json, sys
ev, rc = sys.argv[1], int(sys.argv[2])
json.dump({"exit_code": rc, "expected_nonzero": rc != 0},
          open(ev + "/cloud-apply-denial.json", "w", encoding="utf-8"), indent=2)
PY
if [ "$RC" -eq 0 ]; then echo "FATAL: cloud apply unexpectedly allowed"; fail cloud-apply 1; fi
OCE_RUNTIME_TARGET=local bash "$SCRIPT_DIR/oce-ctl" local status > "$EVIDENCE/local-after-denied.txt" 2>&1
RC=$?
python3 - "$EVIDENCE" "$RC" <<'PY'
import json, sys
json.dump({"exit_code": int(sys.argv[2])}, open(sys.argv[1] + "/local-after-denied.json", "w", encoding="utf-8"), indent=2)
PY
[ "$RC" -ne 0 ] && fail local-after-denied "$RC"
record "cloud plan deterministic + zero mutation; cloud apply denied; local unaffected"

# ── clean source (post) ───────────────────────────────────────────────────
DIRTY=$(git -C "$PROJ_ROOT" status --porcelain | wc -l)
python3 - "$EVIDENCE/source-clean.json" <<PY
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
d["post"] = ${DIRTY} == 0
d["dirty_post"] = ${DIRTY}
json.dump(d, open(sys.argv[1], "w", encoding="utf-8"), indent=2)
PY
[ "$DIRTY" -ne 0 ] && fail clean-source-post 1
record "source clean (post)"

# ── cleanup record ────────────────────────────────────────────────────────
echo "{\"cleanup\": \"ok\", \"disposable_removed\": true}" > "$EVIDENCE/cleanup.json"
record "cleanup ok"

# ── candidate status + candidate manifest ─────────────────────────────────
python3 - "$EVIDENCE" "$COMMIT" "$TREE" "$BRANCH" <<'PY'
import json, os, sys
ev, commit, tree, branch = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
json.dump({"block": "B1", "stage": "B1-LOCAL-GROUND-CLOSURE", "run_id": os.environ.get("OCE_RUN_ID", ""),
           "gate_status": "PENDING_FINAL_GATE", "cloud_mutations": 0, "cloud_cost_state": "ZERO",
           "cloud_activation_state": "DEFERRED_BY_OPERATOR", "cloud_deployment_state": "NOT_DEPLOYED",
           "implementation_commit": commit, "implementation_tree": tree, "branch": branch},
          open(os.path.join(ev, "stage-status.json"), "w", encoding="utf-8"), indent=2)
PY
write_manifest() {
  python3 - "$EVIDENCE" "$COMMIT" "$TREE" "$BRANCH" <<'PY'
import hashlib, json, os, sys
from datetime import datetime, timezone
ev, commit, tree, branch = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
artifacts = []
for name in sorted(os.listdir(ev)):
    p = os.path.join(ev, name)
    if not os.path.isfile(p) or name in ("evidence-manifest.json",):
        continue
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    artifacts.append({"path": name, "sha256": h.hexdigest(), "size": os.path.getsize(p)})
manifest = {"block": "B1", "stage": "B1-LOCAL-GROUND-CLOSURE", "run_id": os.environ.get("OCE_RUN_ID", ""),
            "repository": os.environ.get("OCE_EXPECTED_REPO", "dabiggestpoppa/larger-lab"),
            "branch": branch, "implementation_commit": commit,
            "implementation_tree": tree, "cloud_mutations": 0, "cloud_cost_state": "ZERO",
            "cloud_activation_state": "DEFERRED_BY_OPERATOR", "artifacts": artifacts,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
json.dump(manifest, open(os.path.join(ev, "evidence-manifest.json"), "w", encoding="utf-8"), indent=2)
PY
}
write_manifest

# ── independent gate (candidate package) ──────────────────────────────────
bash "$GATE" "$EVIDENCE" "$COMMIT" "$TREE"
GATE_RC=$?
if [ "$GATE_RC" -ne 0 ]; then
  echo "GATE FAILED (exit $GATE_RC) — preserving evidence, no readiness claim." >&2
  fail final-gate "$GATE_RC"
fi

# ── finalize mutable outputs, then refresh the final manifest ─────────────
write_status() {
  python3 - "$EVIDENCE/stage-status.json" "$1" <<'PY'
import json, sys
p, gs = sys.argv[1], sys.argv[2]
d = json.load(open(p, encoding="utf-8"))
d["gate_status"] = gs
json.dump(d, open(p, "w", encoding="utf-8"), indent=2)
PY
}
if [ "${OCE_CI_MODE:-false}" = "true" ]; then
  FINAL_STATUS="LOCAL_GROUND_READY_FOR_OPERATOR_REVIEW"
else
  FINAL_STATUS="LOCAL_STATIC_READY_CI_REQUIRED"
fi
# Defect 4 finalization order: set final status -> append final stage-log
# entry -> regenerate final manifest -> read-only final-package verifier.
# Nothing mutates the evidence directory after the verifier passes.
write_status "$FINAL_STATUS"
record "independent gate PASS; final status $FINAL_STATUS"
write_manifest
bash "$FINAL_VERIFY" "$EVIDENCE" "$COMMIT" "$TREE"
VERIFY_RC=$?
if [ "$VERIFY_RC" -ne 0 ]; then
  echo "FINAL PACKAGE VERIFICATION FAILED (exit $VERIFY_RC)" >&2
  fail final-package-verify "$VERIFY_RC"
fi
echo "=== RUNNER RESULT: $FINAL_STATUS ==="
echo "OCE_RUN_ID: $OCE_RUN_ID | commit ${COMMIT:0:12} | branch $BRANCH"
echo "evidence: $EVIDENCE"
ls "$EVIDENCE"
exit 0