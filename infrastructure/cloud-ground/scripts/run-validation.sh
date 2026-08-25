#!/usr/bin/env bash
#
# OCE Cloud Ground — Shared Validation Runner
# B1-I1R3F — External RUN_ID and Shared-Runner Truth Repair
#
# The sole authoritative orchestration. Both local validation and CI invoke
# this script. It performs the exact execution order a–q.
#
# Environment:
#   OCE_RUN_ID      — MUST be set by caller (single authoritative ID)
#   GITHUB_REF_NAME — Set by GitHub Actions for branch identity
#   OCE_CI_MODE     — "true" when running in CI
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENGINE="$BASE_DIR/scripts/validate_engine.py"
ADVERSARIAL="$BASE_DIR/tests/adversarial-tests.sh"
CONTRACT="$BASE_DIR/contracts/checkpoint-identity-data.json"
PROJ_ROOT="$(cd "$BASE_DIR/../.." && pwd)"

# ═══════════════════════════════════════════════════════════════════
# RUN_ID — single source of truth, generated externally
# ═══════════════════════════════════════════════════════════════════
if [ -z "${OCE_RUN_ID:-}" ]; then
    echo "FATAL: OCE_RUN_ID is not set. The shared runner must receive exactly one RUN_ID from the caller." >&2
    exit 1
fi

# Validate RUN_ID format (12+ hex chars)
if ! echo "$OCE_RUN_ID" | grep -qE '^[0-9a-f]{12,}$'; then
    echo "FATAL: OCE_RUN_ID '$OCE_RUN_ID' is malformed. Expected 12+ hex characters." >&2
    exit 1
fi

export OCE_RUN_ID

# ═══════════════════════════════════════════════════════════════════
# Resolve repo root and set up trap-based cleanup
# ═══════════════════════════════════════════════════════════════════
ADV_WORKTREE=""
FINAL_EVIDENCE=""
CLEANUP_DONE=false

cleanup() {
    if [ "$CLEANUP_DONE" = true ]; then return; fi
    CLEANUP_DONE=true
    echo ""
    echo "[CLEANUP] Removing disposable worktree and temp artifacts..."
    if [ -n "$ADV_WORKTREE" ] && [ -d "$ADV_WORKTREE" ]; then
        # Use git worktree remove for proper cleanup
        git -C "$PROJ_ROOT" worktree remove --force "$ADV_WORKTREE" 2>/dev/null || rm -rf "$ADV_WORKTREE"
    fi
    # Prune worktree metadata
    git -C "$PROJ_ROOT" worktree prune 2>/dev/null || true
    echo "[CLEANUP] Done."
}
trap cleanup EXIT INT TERM

echo "════════════════════════════════════════════════════════════════"
echo "  OCE B1-I1R3F Shared Validation Runner"
echo "════════════════════════════════════════════════════════════════"
echo "  OCE_RUN_ID:  $OCE_RUN_ID"
echo "  PROJ_ROOT:   $PROJ_ROOT"
echo "════════════════════════════════════════════════════════════════"
echo ""

# ═══════════════════════════════════════════════════════════════════
# Step a: Assert authoritative worktree is clean
# ═══════════════════════════════════════════════════════════════════
echo "[STEP a] Assert clean authoritative worktree..."
DIRTY=$(git -C "$PROJ_ROOT" status --porcelain | wc -l)
if [ "$DIRTY" -ne 0 ]; then
    echo "  FAIL: Worktree is not clean ($DIRTY dirty entries):"
    git -C "$PROJ_ROOT" status --porcelain
    exit 1
fi
echo "  CLEAN"
echo ""

# ═══════════════════════════════════════════════════════════════════
# Step b: Capture repository, commit, tree, branch/ref, checkout state
# ═══════════════════════════════════════════════════════════════════
echo "[STEP b] Capture identity..."

COMMIT=$(git -C "$PROJ_ROOT" rev-parse HEAD)
TREE=$(git -C "$PROJ_ROOT" rev-parse "HEAD^{tree}")

# Determine observed branch — CI vs local
if [ "${OCE_CI_MODE:-false}" = "true" ] && [ -n "${GITHUB_REF_NAME:-}" ]; then
    OBSERVED_BRANCH="$GITHUB_REF_NAME"
    CHECKOUT_STATE="detached"
    echo "  CI mode: observed branch from GITHUB_REF_NAME=$GITHUB_REF_NAME"
elif git -C "$PROJ_ROOT" symbolic-ref -q HEAD >/dev/null 2>&1; then
    OBSERVED_BRANCH=$(git -C "$PROJ_ROOT" branch --show-current)
    CHECKOUT_STATE="attached"
    echo "  Local mode: observed branch from git=$OBSERVED_BRANCH"
else
    OBSERVED_BRANCH=""
    CHECKOUT_STATE="detached"
    echo "  FAIL: Local detached HEAD without trusted ref. Cannot determine branch."
    exit 1
fi

# Read expected branch from contract
EXPECTED_BRANCH=$(python3 -c "import json;print(json.load(open('$CONTRACT'))['authorized_branch'])" 2>/dev/null)

REPOSITORY=$(python3 -c "import json;print(json.load(open('$CONTRACT'))['repository']['full_name'])" 2>/dev/null)

echo "  COMMIT:         $COMMIT"
echo "  TREE:           $TREE"
echo "  OBSERVED_BRANCH: $OBSERVED_BRANCH"
echo "  EXPECTED_BRANCH: $EXPECTED_BRANCH"
echo "  CHECKOUT_STATE:  $CHECKOUT_STATE"
echo "  REPOSITORY:      $REPOSITORY"
echo ""

# Verify branch identity
if [ "$OBSERVED_BRANCH" != "$EXPECTED_BRANCH" ]; then
    echo "  FAIL: Observed branch '$OBSERVED_BRANCH' != expected '$EXPECTED_BRANCH'"
    exit 1
fi
echo "  Branch identity: OK"
echo ""

# ═══════════════════════════════════════════════════════════════════
# Step c: Verify mandatory tools
# ═══════════════════════════════════════════════════════════════════
echo "[STEP c] Verify mandatory tools..."
MISSING=0
for cmd in python3 git; do
    if command -v "$cmd" >/dev/null 2>&1; then
        echo "  OK: $cmd"
    else
        echo "  MISSING: $cmd (BLOCKED)"
        MISSING=$((MISSING + 1))
    fi
done
# Optional tools — warn only
for cmd in shellcheck ansible-playbook ansible-lint docker gitleaks; do
    if command -v "$cmd" >/dev/null 2>&1; then
        echo "  OK: $cmd"
    else
        echo "  NOT INSTALLED: $cmd (some checks BLOCKED)"
    fi
done
echo ""

# ═══════════════════════════════════════════════════════════════════
# Step d: Generate final evidence directory (outside repository)
# ═══════════════════════════════════════════════════════════════════
echo "[STEP d] Create isolated final evidence directory..."
FINAL_EVIDENCE=$(mktemp -d "${TMPDIR:-/tmp}/oce-final-evidence-XXXXXX")
export OCE_EVIDENCE_DIR="$FINAL_EVIDENCE"
echo "  FINAL_EVIDENCE=$FINAL_EVIDENCE"
echo ""

# ═══════════════════════════════════════════════════════════════════
# Step e: Run initial static/runtime validations
# ═══════════════════════════════════════════════════════════════════
echo "[STEP e] Run initial static/runtime validations..."
export OCE_VALIDATOR_MODE="initial"
python3 "$ENGINE" --all --authoritative \
    --target-commit "$COMMIT" \
    --target-tree "$TREE" \
    --target-branch "$OBSERVED_BRANCH" \
    --evidence-dir "$FINAL_EVIDENCE"
echo "  Initial validation complete."
echo ""

# ═══════════════════════════════════════════════════════════════════
# Step f: Create disposable Git worktree OUTSIDE repository
# ═══════════════════════════════════════════════════════════════════
echo "[STEP f] Create disposable adversarial worktree..."
ADV_WORKTREE=$(mktemp -d "${TMPDIR:-/tmp}/oce-adversarial-XXXXXX")
git -C "$PROJ_ROOT" worktree add --detach "$ADV_WORKTREE" HEAD >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "  FAIL: Could not create real Git worktree."
    echo "  Cannot run adversarial tests in isolation."
    exit 1
fi
echo "  ADV_WORKTREE=$ADV_WORKTREE"
echo ""

# ═══════════════════════════════════════════════════════════════════
# Step g: Run adversarial tests ONLY inside disposable worktree
# ═══════════════════════════════════════════════════════════════════
echo "[STEP g] Run adversarial tests in isolated worktree..."
ADV_SH="$ADV_WORKTREE/infrastructure/cloud-ground/tests/adversarial-tests.sh"
if [ ! -f "$ADV_SH" ]; then
    echo "  FAIL: adversarial-tests.sh not found in worktree."
    exit 1
fi
OCE_VALIDATOR_MODE="initial" bash "$ADV_SH"
echo "  Adversarial tests complete."
echo ""

# ═══════════════════════════════════════════════════════════════════
# Step h: Remove disposable worktree and prune
# ═══════════════════════════════════════════════════════════════════
echo "[STEP h] Remove disposable worktree..."
git -C "$PROJ_ROOT" worktree remove --force "$ADV_WORKTREE" 2>/dev/null || rm -rf "$ADV_WORKTREE"
ADV_WORKTREE=""
git -C "$PROJ_ROOT" worktree prune 2>/dev/null || true
echo "  Worktree removed and pruned."
echo ""

# ═══════════════════════════════════════════════════════════════════
# Step i: Confirm authoritative source remains clean
# ═══════════════════════════════════════════════════════════════════
echo "[STEP i] Confirm authoritative source still clean..."
DIRTY=$(git -C "$PROJ_ROOT" status --porcelain | wc -l)
if [ "$DIRTY" -ne 0 ]; then
    echo "  FAIL: Authoritative checkout is dirty after adversarial tests ($DIRTY entries)"
    git -C "$PROJ_ROOT" status --porcelain
    exit 1
fi
echo "  CLEAN"
echo ""

# ═══════════════════════════════════════════════════════════════════
# Step j: Confirm adversarial-results.json exists
# ═══════════════════════════════════════════════════════════════════
echo "[STEP j] Confirm adversarial-results.json present..."
if [ ! -f "$FINAL_EVIDENCE/adversarial-results.json" ]; then
    echo "  FAIL: adversarial-results.json not found in $FINAL_EVIDENCE"
    exit 1
fi
echo "  PRESENT"
echo ""

# ═══════════════════════════════════════════════════════════════════
# Step k: Run final authoritative validator
# ═══════════════════════════════════════════════════════════════════
echo "[STEP k] Run final authoritative validator..."
export OCE_VALIDATOR_MODE="final"
python3 "$ENGINE" --all --authoritative \
    --target-commit "$COMMIT" \
    --target-tree "$TREE" \
    --target-branch "$OBSERVED_BRANCH" \
    --evidence-dir "$FINAL_EVIDENCE"
echo "  Final validation complete."
echo ""

# ═══════════════════════════════════════════════════════════════════
# Step l: Run independent final gate
# ═══════════════════════════════════════════════════════════════════
echo "[STEP l] Run independent final gate..."
RESULTS="$FINAL_EVIDENCE/static-validation-results.json"
STAGE="$FINAL_EVIDENCE/stage-status.json"
ADV="$FINAL_EVIDENCE/adversarial-results.json"

# l1: Required files exist
echo "  l1: Check required evidence files..."
for f in "$RESULTS" "$STAGE" "$ADV"; do
    if [ ! -f "$f" ]; then
        echo "    FAIL: $f not found"
        exit 1
    fi
    echo "    OK: $(basename $f)"
done

# l2: Gate status
echo "  l2: Check gate status..."
GATE=$(python3 -c "import json; print(json.load(open('$STAGE'))['gate_status'])")
if [ "$GATE" != "READY_FOR_OPERATOR_REVIEW" ]; then
    echo "    FAIL: Gate=$GATE (expected READY_FOR_OPERATOR_REVIEW)"
    exit 1
fi
echo "    OK: $GATE"

# l3: Totals internally consistent
echo "  l3: Check totals consistency..."
python3 -c "
import json, sys
d = json.load(open('$RESULTS'))
t = d.get('totals', {})
errors = []
if t.get('FAIL', 0) != 0:
    errors.append(f'FAIL={t[\"FAIL\"]}')
if t.get('BLOCKED', 0) != 0:
    errors.append(f'BLOCKED={t[\"BLOCKED\"]}')
expected = t.get('PASS',0)+t.get('FAIL',0)+t.get('BLOCKED',0)+t.get('SKIPPED',0)
if t.get('total',0) != expected:
    errors.append(f'total mismatch: stated={t[\"total\"]} computed={expected}')
if errors:
    print(f'    FAIL: {errors}', file=sys.stderr); sys.exit(1)
print(f'    OK: {t}')
"

# l4: Identity fields match
echo "  l4: Check identity fields..."
python3 -c "
import json, subprocess, sys
d = json.load(open('$RESULTS'))
errors = []
actual_commit = subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True,cwd='$PROJ_ROOT').stdout.strip()
actual_tree = subprocess.run(['git','rev-parse','HEAD^{tree}'],capture_output=True,text=True,cwd='$PROJ_ROOT').stdout.strip()
if d.get('tested_commit','') != actual_commit:
    errors.append(f'commit: {d.get(\"tested_commit\",\"\")[:12]} != {actual_commit[:12]}')
if d.get('tested_tree','') != actual_tree:
    errors.append(f'tree: {d.get(\"tested_tree\",\"\")[:12]} != {actual_tree[:12]}')
if d.get('repository','') != 'dabiggestpoppa/larger-lab':
    errors.append(f'repository={d.get(\"repository\",\"\")}')
if d.get('validator_version','') != '3.5.0':
    errors.append(f'version={d.get(\"validator_version\",\"\")}')
if d.get('run_id','') != '$OCE_RUN_ID':
    errors.append(f'run_id={d.get(\"run_id\",\"\")} != $OCE_RUN_ID')
if errors:
    print(f'    FAIL: {errors}', file=sys.stderr); sys.exit(1)
print('    OK')
"

# l5: Adversarial suite
echo "  l5: Check adversarial suite..."
python3 -c "
import json, sys
a = json.load(open('$ADV'))
errors = []
if a.get('suite_result','') != 'PASS':
    errors.append(f'suite_result={a.get(\"suite_result\",\"\")}')
if a.get('schema_version','') != '3.5.0':
    errors.append(f'schema={a.get(\"schema_version\",\"\")}')
if a.get('run_id','') != '$OCE_RUN_ID':
    errors.append(f'run_id={a.get(\"run_id\",\"\")} != $OCE_RUN_ID')
neg = a.get('negative_tests', [])
meta = a.get('meta_tests', [])
if not neg:
    errors.append('no negative tests')
if not meta:
    errors.append('no meta tests')
for t in neg:
    tid = t.get('test_id','?')
    mr = t.get('mutation_result','')
    me = t.get('mutation_exit', 0)
    if mr != 'FAIL':
        errors.append(f'{tid}: mutation_result={mr}')
    if me == 0 and mr not in ('N/A',''):
        errors.append(f'{tid}: mutation_exit=0')
for t in meta:
    tid = t.get('test_id','?')
    if t.get('result','') != 'PASS':
        errors.append(f'{tid}: result={t.get(\"result\",\"\")}')
if errors:
    print(f'    FAIL: {errors}', file=sys.stderr); sys.exit(1)
print(f'    OK: {len(neg)} negative + {len(meta)} meta')
"

# l6: RUN_ID consistency across all artifacts
echo "  l6: Check RUN_ID consistency across artifacts..."
python3 -c "
import json, sys
ids = {}
d = json.load(open('$RESULTS'))
ids['static-validation'] = d.get('run_id','')
a = json.load(open('$ADV'))
ids['adversarial'] = a.get('run_id','')
s = json.load(open('$STAGE'))
ids['stage-status'] = s.get('run_id','')
expected = '$OCE_RUN_ID'
mismatches = {k:v for k,v in ids.items() if v != expected}
if mismatches:
    print(f'    FAIL: RUN_ID mismatches: {mismatches}', file=sys.stderr); sys.exit(1)
print(f'    OK: all artifacts have RUN_ID={expected}')
"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  FINAL GATE: READY_FOR_OPERATOR_REVIEW"
echo "════════════════════════════════════════════════════════════════"
echo "  OCE_RUN_ID:  $OCE_RUN_ID"
echo "  COMMIT:      ${COMMIT:0:12}"
echo "  TREE:        ${TREE:0:12}"
echo "  BRANCH:      $OBSERVED_BRANCH"
echo "  EVIDENCE:    $FINAL_EVIDENCE"
echo "  GATE:        $GATE"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Evidence directory ready for upload: $FINAL_EVIDENCE"
ls -la "$FINAL_EVIDENCE/"
echo ""
echo "$FINAL_EVIDENCE"
