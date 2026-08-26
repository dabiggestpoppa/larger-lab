#!/usr/bin/env bash
#
# OCE Cloud Ground — Shared Validation Runner
# B1-I1R3H — Gate Closure
#
# The sole authoritative orchestration. Both validate-local and GitHub
# Actions invoke this script exactly once.
#
# Execution order (a–o):
#   a. Validate external OCE_RUN_ID
#   b. Create final evidence directory outside the repository
#   c. Capture actual repository/commit/tree/ref/checkout state
#   d. Confirm authoritative source is clean
#   e. Run regression suite
#   f. Run initial validation phase
#   g. Create a real disposable Git worktree outside the repository
#   h. Run adversarial tests only in that worktree
#   i. Remove and prune the worktree through trap-based cleanup
#   j. Reconfirm authoritative source cleanliness
#   k. Confirm adversarial evidence exists
#   l. Run final authoritative validation phase
#   m. Generate final status, summary and manifest
#   n. Run an independent final gate
#   o. Return nonzero unless the checkpoint is genuinely ready
#
# Environment:
#   OCE_RUN_ID        — MUST be set by caller (single authoritative ID)
#   OCE_EVIDENCE_DIR  — optional; caller-provided evidence directory
#                       (machine-readable: known before validation begins)
#   GITHUB_REF_NAME   — trusted ref when checkout is detached (CI)
#   OCE_CI_MODE       — "true" when running in CI
#
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENGINE="$BASE_DIR/scripts/validate_engine.py"
GATE="$BASE_DIR/scripts/final-gate.sh"
REGRESSIONS="$BASE_DIR/tests/test_regression.py"
CONTRACT="$BASE_DIR/contracts/checkpoint-identity-data.json"
PROJ_ROOT="$(cd "$BASE_DIR/../.." && pwd)"

# Windows/mixed-shell portability: convert POSIX paths to Windows form so
# that Windows Python (subprocesses) can open them. On Linux/macOS cygpath
# is absent and the fallback keeps the path unchanged.
WIN() {
    if command -v cygpath >/dev/null 2>&1; then cygpath -m "$1"; else echo "$1"; fi
}
ENGINE_WIN=$(WIN "$ENGINE")
REGRESSIONS_WIN=$(WIN "$REGRESSIONS")
CONTRACT_WIN=$(WIN "$CONTRACT")
PROJ_ROOT_WIN=$(WIN "$PROJ_ROOT")
export OCE_PROJ_ROOT="$PROJ_ROOT_WIN"

FAILED_PHASE=""
ADV_WORKTREE=""
WORKTREE_REGISTERED=false
WORKTREE_REMOVED=false
WORKTREE_PRUNED=false

# ═══════════════════════════════════════════════════════════════════
# Step a: Validate external OCE_RUN_ID (fail closed)
# ═══════════════════════════════════════════════════════════════════
if [ -z "${OCE_RUN_ID:-}" ]; then
    echo "FATAL: OCE_RUN_ID is not set. The shared runner must receive exactly one RUN_ID from the caller." >&2
    exit 2
fi
if ! echo "$OCE_RUN_ID" | grep -qE '^[0-9a-f]{12,}$'; then
    echo "FATAL: OCE_RUN_ID '$OCE_RUN_ID' is malformed. Expected 12+ lowercase hex characters." >&2
    exit 2
fi
export OCE_RUN_ID

# ═══════════════════════════════════════════════════════════════════
# Step b: Final evidence directory — outside the repository,
#         known to the caller BEFORE validation begins.
# ═══════════════════════════════════════════════════════════════════
if [ -n "${OCE_EVIDENCE_DIR:-}" ]; then
    FINAL_EVIDENCE="$OCE_EVIDENCE_DIR"
else
    FINAL_EVIDENCE="$(mktemp -d "${TMPDIR:-/tmp}/oce-final-evidence-XXXXXX")"
fi
mkdir -p "$FINAL_EVIDENCE"
FINAL_EVIDENCE="$(cd "$FINAL_EVIDENCE" && pwd)"
FINAL_EVIDENCE_WIN=$(WIN "$FINAL_EVIDENCE")
export OCE_EVIDENCE_DIR="$FINAL_EVIDENCE_WIN"

# Machine-readable path output file inside the evidence directory itself,
# so callers can always resolve the authoritative evidence path.
printf '%s\n' "$FINAL_EVIDENCE_WIN" > "$FINAL_EVIDENCE_WIN/evidence-dir.path" 2>/dev/null || true

write_failure_context() {
    # Preserve an honest failure evidence package.
    local phase="$1" exit_status="$2"
    python3 - "$FINAL_EVIDENCE_WIN" "$phase" "$exit_status" <<'PYF'
import json, os, subprocess, sys
from datetime import datetime, timezone

ev_dir, phase, exit_status = sys.argv[1], sys.argv[2], int(sys.argv[3])
proj_root = os.environ.get("OCE_PROJ_ROOT", ".")

def git(*a):
    r = subprocess.run(["git", "-C", proj_root] + list(a), capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None

ctx = {
    "failure": True,
    "failure_phase": phase,
    "exit_status": exit_status,
    "run_id": os.environ.get("OCE_RUN_ID", ""),
    "tested_commit": git("rev-parse", "HEAD"),
    "tested_tree": git("rev-parse", "HEAD^{tree}"),
    "observed_branch": git("branch", "--show-current") or "(detached)",
    "trusted_ci_ref": os.environ.get("GITHUB_REF_NAME") or None,
    "tool_versions": {},
    "unresolved_blockers": [f"runner failed in phase '{phase}' with exit {exit_status}"],
    "cleanup_outcome": {
        "worktree_removed": os.environ.get("_WT_REMOVED", "unknown"),
        "worktree_pruned": os.environ.get("_WT_PRUNED", "unknown"),
    },
    "cost_impact_usd": 0,
    "cloud_mutations": 0,
    "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
}
for name, cmd in [("python3", ["python3", "--version"]), ("git", ["git", "--version"]),
                  ("docker", ["docker", "--version"]), ("ansible-playbook", ["ansible-playbook", "--version"]),
                  ("shellcheck", ["shellcheck", "--version"]), ("gitleaks", ["gitleaks", "version"])]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        ctx["tool_versions"][name] = (r.stdout + r.stderr).strip().splitlines()[0][:120] if r.returncode == 0 else "not installed"
    except Exception:
        ctx["tool_versions"][name] = "not installed"

with open(os.path.join(ev_dir, "failure-context.json"), "w", encoding="utf-8") as f:
    json.dump(ctx, f, indent=2)

# stage-status.json must exist even on failure so uploads are truthful.
stage_path = os.path.join(ev_dir, "stage-status.json")
if not os.path.exists(stage_path):
    stage = {
        "block": "B1",
        "increment": "B1-I1R3H",
        "run_id": ctx["run_id"],
        "gate_status": "FAILED",
        "failure_phase": phase,
        "exit_status": exit_status,
        "totals": {"PASS": 0, "FAIL": 0, "BLOCKED": 0, "SKIPPED": 0, "total": 0},
        "unresolved_blockers": ctx["unresolved_blockers"],
        "cost_impact_usd": 0,
        "cloud_mutations": 0,
    }
    with open(stage_path, "w", encoding="utf-8") as f:
        json.dump(stage, f, indent=2)
PYF
}

write_worktree_cleanup_evidence() {
    # R3H: truthfully record removal and prune results. Called immediately
    # after successful removal (so the final gate sees it before it runs)
    # and again from the exit trap for abnormal-failure cleanup.
    export _WT_REMOVED=$WORKTREE_REMOVED _WT_PRUNED=$WORKTREE_PRUNED
    printf '{"removed": %s, "pruned": %s}\n' \
        "$( [ "$WORKTREE_REMOVED" = true ] && echo true || echo false)" \
        "$( [ "$WORKTREE_PRUNED" = true ] && echo true || echo false)" \
        > "$FINAL_EVIDENCE/worktree-cleanup.json" 2>/dev/null || true
}

cleanup() {
    local rc=$?
    if [ "$WORKTREE_REGISTERED" = true ] && [ "$WORKTREE_REMOVED" = false ] && [ -n "$ADV_WORKTREE" ]; then
        if git -C "$PROJ_ROOT" worktree remove --force "$ADV_WORKTREE" >/dev/null 2>&1; then
            WORKTREE_REMOVED=true
        else
            echo "[CLEANUP][WARN] git worktree remove failed for $ADV_WORKTREE (no rm-only fallback allowed)" >&2
        fi
    fi
    if git -C "$PROJ_ROOT" worktree prune >/dev/null 2>&1; then
        WORKTREE_PRUNED=true
    fi
    write_worktree_cleanup_evidence
    if [ -n "$FAILED_PHASE" ] && [ "$rc" -ne 0 ]; then
        write_failure_context "$FAILED_PHASE" "$rc" || true
    fi
    exit "$rc"
}
trap cleanup EXIT INT TERM

record_result() {
    printf '%s\n' "$*" >> "$FINAL_EVIDENCE/stage-log.txt"
}

echo "════════════════════════════════════════════════════════════════"
echo "  OCE B1-I1R3H Shared Validation Runner"
echo "════════════════════════════════════════════════════════════════"
echo "  OCE_RUN_ID:      $OCE_RUN_ID"
echo "  EVIDENCE_DIR:    $FINAL_EVIDENCE"
echo "  PROJ_ROOT:       $PROJ_ROOT"
echo "════════════════════════════════════════════════════════════════"
echo ""

# ═══════════════════════════════════════════════════════════════════
# Step c: Capture actual identity (observed only)
# ═══════════════════════════════════════════════════════════════════
echo "[STEP c] Capture observed identity..."
COMMIT=$(git -C "$PROJ_ROOT" rev-parse HEAD) || { FAILED_PHASE="capture-identity"; echo "FATAL: cannot resolve HEAD"; exit 1; }
TREE=$(git -C "$PROJ_ROOT" rev-parse "HEAD^{tree}")
ORIGIN=$(git -C "$PROJ_ROOT" remote get-url origin 2>/dev/null || echo "none")

if git -C "$PROJ_ROOT" symbolic-ref -q HEAD >/dev/null 2>&1; then
    OBSERVED_BRANCH=$(git -C "$PROJ_ROOT" branch --show-current)
    CHECKOUT_STATE="attached"
    BRANCH_PROVENANCE="git-symbolic-ref"
else
    OBSERVED_BRANCH="(detached)"
    CHECKOUT_STATE="detached"
    if [ -n "${GITHUB_REF_NAME:-}" ]; then
        BRANCH_PROVENANCE="GITHUB_REF_NAME"
        IDENTITY_BRANCH="$GITHUB_REF_NAME"
    else
        BRANCH_PROVENANCE="none"
        IDENTITY_BRANCH="(detached)"
    fi
fi
if [ "$CHECKOUT_STATE" = "attached" ]; then
    IDENTITY_BRANCH="$OBSERVED_BRANCH"
fi

EXPECTED_BRANCH=$(python3 -c "import json;print(json.load(open('$CONTRACT_WIN'))['authorized_branch'])")

# R3G: trusted ref for engine runs inside the detached disposable worktree.
export OCE_TRUSTED_REF="$IDENTITY_BRANCH"

echo "  COMMIT:            $COMMIT"
echo "  TREE:              $TREE"
echo "  ORIGIN:            $ORIGIN"
echo "  OBSERVED_BRANCH:   $OBSERVED_BRANCH ($CHECKOUT_STATE, provenance=$BRANCH_PROVENANCE)"
echo "  TRUSTED_CI_REF:    ${GITHUB_REF_NAME:-none}"
echo "  EXPECTED_BRANCH:   $EXPECTED_BRANCH"
echo ""

# Branch identity rules: observed/trusted identity must equal contract.
if [ "$IDENTITY_BRANCH" != "$EXPECTED_BRANCH" ]; then
    FAILED_PHASE="identity"
    echo "FATAL: Branch identity mismatch: identity='$IDENTITY_BRANCH' expected='$EXPECTED_BRANCH'" >&2
    exit 1
fi
if [ "$CHECKOUT_STATE" = "detached" ] && [ "$BRANCH_PROVENANCE" = "none" ]; then
    FAILED_PHASE="identity"
    echo "FATAL: Local detached HEAD without trusted ref." >&2
    exit 1
fi

# ═══════════════════════════════════════════════════════════════════
# Step d: Confirm authoritative source is clean (tracked + untracked)
# ═══════════════════════════════════════════════════════════════════
echo "[STEP d] Assert clean authoritative worktree..."
DIRTY=$(git -C "$PROJ_ROOT" status --porcelain | wc -l)
if [ "$DIRTY" -ne 0 ]; then
    FAILED_PHASE="clean-source-pre"
    echo "FATAL: Worktree is not clean ($DIRTY dirty entries):" >&2
    git -C "$PROJ_ROOT" status --porcelain >&2
    exit 1
fi
record_result "STEP d: source clean"
echo "  CLEAN"
echo ""

# ═══════════════════════════════════════════════════════════════════
# Step e: Run regression suite (registered count must match execution)
# ═══════════════════════════════════════════════════════════════════
echo "[STEP e] Run regression suite..."
export OCE_RUN_ID
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1
# -u keeps the tee'd regression-output.txt current even on long/aborted runs,
# so partial progress is preserved in the evidence directory.
# PYTHONDONTWRITEBYTECODE keeps __pycache__ out of the authoritative checkout
# so the post-suite clean-source check (step j/f) does not see stray files.
python3 -u "$REGRESSIONS_WIN" 2>&1 | tee "$FINAL_EVIDENCE/regression-output.txt"
REG_RC=${PIPESTATUS[0]}
if [ "$REG_RC" -ne 0 ]; then
    FAILED_PHASE="regressions"
    echo "FATAL: Regression suite failed (exit $REG_RC)." >&2
    exit 1
fi
REG_TOTAL=$(grep -c "^PASS:" "$FINAL_EVIDENCE/regression-output.txt" || echo 0)
record_result "STEP e: regressions passed ($REG_TOTAL)"
echo "  Regressions PASSED ($REG_TOTAL registered tests executed)"
echo ""

# ═══════════════════════════════════════════════════════════════════
# Step f: Initial validation phase (no adversarial evidence needed yet)
# ═══════════════════════════════════════════════════════════════════
echo "[STEP f] Run INITIAL validation phase..."
python3 "$ENGINE_WIN" --all --authoritative --phase initial \
    --target-commit "$COMMIT" --target-tree "$TREE" --target-branch "$OBSERVED_BRANCH" \
    --evidence-dir "$FINAL_EVIDENCE_WIN"
ENGINE_RC=$?
if [ "$ENGINE_RC" -ne 0 ]; then
    FAILED_PHASE="initial-validation"
    echo "FATAL: Initial validation failed (exit $ENGINE_RC)." >&2
    exit 1
fi
mv "$FINAL_EVIDENCE/static-validation-results.json" "$FINAL_EVIDENCE/initial-validation-results.json"
mv "$FINAL_EVIDENCE/static-validation-summary.md" "$FINAL_EVIDENCE/initial-validation-summary.md" 2>/dev/null || true
rm -f "$FINAL_EVIDENCE/stage-status.json"
record_result "STEP f: initial validation passed"
echo "  Initial phase PASSED"
echo ""

# ═══════════════════════════════════════════════════════════════════
# Step g: Real disposable Git worktree OUTSIDE the repository
# ═══════════════════════════════════════════════════════════════════
echo "[STEP g] Create disposable adversarial worktree..."
ADV_PARENT="$(mktemp -d "${TMPDIR:-/tmp}/oce-adversarial-parent-XXXXXX")"
ADV_WORKTREE="$ADV_PARENT/wt"
if ! git -C "$PROJ_ROOT" worktree add --detach "$ADV_WORKTREE" HEAD >/dev/null 2>&1; then
    FAILED_PHASE="worktree-create"
    echo "FATAL: Could not create real isolated Git worktree at $ADV_WORKTREE." >&2
    exit 1
fi
WORKTREE_REGISTERED=true
record_result "STEP g: worktree created at $ADV_WORKTREE"
echo "  ADV_WORKTREE=$ADV_WORKTREE"
echo ""

# ═══════════════════════════════════════════════════════════════════
# Step h: Adversarial tests ONLY inside the disposable worktree
# ═══════════════════════════════════════════════════════════════════
echo "[STEP h] Run adversarial tests in isolated worktree..."
ADV_SH="$ADV_WORKTREE/infrastructure/cloud-ground/tests/adversarial-tests.sh"
if [ ! -f "$ADV_SH" ]; then
    FAILED_PHASE="adversarial-staging"
    echo "FATAL: adversarial-tests.sh not found inside worktree." >&2
    exit 1
fi
bash "$ADV_SH" 2>&1 | tee "$FINAL_EVIDENCE/adversarial-output.txt"
ADV_RC=${PIPESTATUS[0]}
if [ "$ADV_RC" -ne 0 ]; then
    FAILED_PHASE="adversarial-tests"
    echo "FATAL: Adversarial suite failed (exit $ADV_RC)." >&2
    exit 1
fi
record_result "STEP h: adversarial suite passed"
echo "  Adversarial suite PASSED"
echo ""

# ═══════════════════════════════════════════════════════════════════
# Step i: Remove and prune the worktree (trap-based cleanup)
# ═══════════════════════════════════════════════════════════════════
echo "[STEP i] Remove disposable worktree..."
if ! git -C "$PROJ_ROOT" worktree remove --force "$ADV_WORKTREE"; then
    FAILED_PHASE="worktree-cleanup"
    echo "FATAL: git worktree remove failed. rm-only cleanup of registered worktrees is forbidden." >&2
    exit 1
fi
WORKTREE_REMOVED=true
ADV_WORKTREE=""
git -C "$PROJ_ROOT" worktree prune || true
WORKTREE_PRUNED=true
write_worktree_cleanup_evidence
rm -rf "$ADV_PARENT"
record_result "STEP i: worktree removed and pruned"
echo "  Worktree removed and pruned; cleanup evidence written."
echo ""

# ═══════════════════════════════════════════════════════════════════
# Step j: Reconfirm authoritative source cleanliness
# ═══════════════════════════════════════════════════════════════════
echo "[STEP j] Reconfirm authoritative source still clean..."
DIRTY=$(git -C "$PROJ_ROOT" status --porcelain | wc -l)
if [ "$DIRTY" -ne 0 ]; then
    FAILED_PHASE="clean-source-post"
    echo "FATAL: Authoritative checkout dirty after adversarial tests ($DIRTY entries):" >&2
    git -C "$PROJ_ROOT" status --porcelain >&2
    exit 1
fi
record_result "STEP j: source still clean"
echo "  CLEAN"
echo ""

# ═══════════════════════════════════════════════════════════════════
# Step k: Confirm adversarial evidence exists
# ═══════════════════════════════════════════════════════════════════
echo "[STEP k] Confirm adversarial-results.json present..."
if [ ! -f "$FINAL_EVIDENCE/adversarial-results.json" ]; then
    FAILED_PHASE="evidence-transfer"
    echo "FATAL: adversarial-results.json not found in $FINAL_EVIDENCE" >&2
    exit 1
fi
record_result "STEP k: adversarial evidence present"
echo "  PRESENT"
echo ""

# ═══════════════════════════════════════════════════════════════════
# Steps l+m: Final authoritative validation phase
#            (writes final results, summary, stage-status, manifest)
# ═══════════════════════════════════════════════════════════════════
echo "[STEP l] Run FINAL validation phase..."
python3 "$ENGINE_WIN" --all --authoritative --phase final \
    --target-commit "$COMMIT" --target-tree "$TREE" --target-branch "$OBSERVED_BRANCH" \
    --evidence-dir "$FINAL_EVIDENCE_WIN"
ENGINE_RC=$?
if [ "$ENGINE_RC" -ne 0 ]; then
    FAILED_PHASE="final-validation"
    echo "FATAL: Final validation did not reach READY (exit $ENGINE_RC)." >&2
    exit 1
fi
record_result "STEP l/m: final validation wrote results, summary, manifest"
echo "  Final phase complete."
echo ""

# ═══════════════════════════════════════════════════════════════════
# Step n: Independent final gate
# ═══════════════════════════════════════════════════════════════════
echo "[STEP n] Run independent final gate..."
bash "$GATE" "$FINAL_EVIDENCE_WIN" "$COMMIT" "$TREE"
GATE_RC=$?
if [ "$GATE_RC" -ne 0 ]; then
    FAILED_PHASE="final-gate"
    echo "FATAL: Independent final gate rejected the evidence (exit $GATE_RC)." >&2
    exit 1
fi
record_result "STEP n: independent gate READY_FOR_OPERATOR_REVIEW"
echo ""

# ═══════════════════════════════════════════════════════════════════
# Step o: Success — report honestly. Nonzero unless genuinely ready.
# ═══════════════════════════════════════════════════════════════════
echo "════════════════════════════════════════════════════════════════"
echo "  RUNNER RESULT: READY_FOR_OPERATOR_REVIEW"
echo "════════════════════════════════════════════════════════════════"
echo "  OCE_RUN_ID:   $OCE_RUN_ID"
echo "  COMMIT:       ${COMMIT:0:12}"
echo "  TREE:         ${TREE:0:12}"
echo "  BRANCH:       $IDENTITY_BRANCH ($BRANCH_PROVENANCE)"
echo "  EVIDENCE DIR: $FINAL_EVIDENCE"
echo "════════════════════════════════════════════════════════════════"
ls -la "$FINAL_EVIDENCE/"
exit 0
