#!/usr/bin/env bash
#
# OCE Cloud Ground — Shared Validation Runner
# B1-I1R3E — Single-Run Local/CI Evidence Closure
#
# This script is the single authoritative runner invoked by both local
# validation and GitHub Actions CI. It performs the exact sequence:
#
#   a. Assert authoritative source checkout is clean
#   b. Capture repository, commit, tree, branch/ref, version, RUN_ID
#   c. Verify mandatory tools
#   d. Run static and runtime validations
#   e. Create a disposable adversarial worktree
#   f. Run adversarial tests only inside that worktree
#   g. Verify the authoritative source checkout remains clean
#   h. Copy adversarial-results.json into the final evidence directory
#   i. Run the final validator against that same directory
#   j. Run the final gate against that same directory
#   k. Upload exactly that directory
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENGINE="$BASE_DIR/scripts/validate_engine.py"
ADVERSARIAL="$BASE_DIR/tests/adversarial-tests.sh"
PROJ_ROOT="$(cd "$BASE_DIR/../.." && pwd)"

# === b. Capture identity and generate RUN_ID ===
COMMIT=$(git -C "$PROJ_ROOT" rev-parse HEAD)
TREE=$(git -C "$PROJ_ROOT" rev-parse "HEAD^{tree}")
# Use contract authorized_branch for branch identity (detached-CI safe)
BRANCH=$(python3 -c "import json;print(json.load(open('$BASE_DIR/contracts/checkpoint-identity-data.json'))['authorized_branch'])" 2>/dev/null || git -C "$PROJ_ROOT" branch --show-current)
RUN_ID=$(python3 -c "import uuid; print(uuid.uuid4().hex[:12])")

echo "=============================================="
echo "  OCE B1-I1R3E Shared Validation Runner"
echo "=============================================="
echo "  RUN_ID:    $RUN_ID"
echo "  COMMIT:    ${COMMIT:0:12}"
echo "  TREE:      ${TREE:0:12}"
echo "  BRANCH:    $BRANCH"
echo "=============================================="
echo ""

# === a. Assert clean authoritative worktree ===
echo "Step a: Assert clean authoritative worktree..."
DIRTY=$(git -C "$PROJ_ROOT" status --porcelain | wc -l)
if [ "$DIRTY" -ne 0 ]; then
    echo "ERROR: Worktree is not clean ($DIRTY dirty files)"
    git -C "$PROJ_ROOT" status --porcelain
    exit 1
fi
echo "  CLEAN"
echo ""

# === c. Verify mandatory tools ===
echo "Step c: Verify mandatory tools..."
MISSING=0
for cmd in python3; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "  MISSING: $cmd"
        MISSING=$((MISSING + 1))
    else
        echo "  OK: $cmd ($(python3 --version 2>&1))"
    fi
done
# Optional tools — warn but don't fail
for cmd in ansible-playbook ansible-lint shellcheck docker gitleaks; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "  WARN: $cmd not installed (some checks will be BLOCKED)"
    else
        echo "  OK: $cmd"
    fi
done
echo ""

# === Set up final evidence directory (one isolated temp dir) ===
FINAL_EVIDENCE=$(mktemp -d "${TMPDIR:-/tmp}/oce-final-evidence-XXXXXX")
export OCE_EVIDENCE_DIR="$FINAL_EVIDENCE"
echo "Final evidence directory: $FINAL_EVIDENCE"
echo ""

# === d. Run static and runtime validations ===
echo "Step d: Run static and runtime validations..."
python3 "$ENGINE" --all --authoritative \
    --target-commit "$COMMIT" \
    --target-tree "$TREE" \
    --target-branch "$BRANCH" \
    --evidence-dir "$FINAL_EVIDENCE"
echo ""

# === e. Create a disposable adversarial worktree ===
echo "Step e: Create disposable adversarial worktree..."
ADV_WORKTREE="$PROJ_ROOT/.oce-adversarial-worktree-$$"
rm -rf "$ADV_WORKTREE"
git -C "$PROJ_ROOT" worktree add "$ADV_WORKTREE" HEAD 2>/dev/null || {
    # Fallback: create manually if worktree add fails
    mkdir -p "$ADV_WORKTREE"
    cp -a "$PROJ_ROOT/." "$ADV_WORKTREE/"
}
echo "  Worktree: $ADV_WORKTREE"
echo ""

# === f. Run adversarial tests only inside that worktree ===
echo "Step f: Run adversarial tests (isolated worktree)..."
ADV_ENGINE="$ADV_WORKTREE/infrastructure/cloud-ground/scripts/validate_engine.py"
ADV_SH="$ADV_WORKTREE/infrastructure/cloud-ground/tests/adversarial-tests.sh"
# Run from the adversarial worktree
OCE_EVIDENCE_DIR="$FINAL_EVIDENCE" bash "$ADV_SH"
echo ""

# === g. Verify authoritative source checkout remains clean ===
echo "Step g: Verify authoritative source still clean..."
DIRTY=$(git -C "$PROJ_ROOT" status --porcelain | wc -l)
if [ "$DIRTY" -ne 0 ]; then
    echo "ERROR: Authoritative checkout dirty after adversarial tests ($DIRTY files)"
    git -C "$PROJ_ROOT" status --porcelain
    exit 1
fi
echo "  CLEAN"
echo ""

# === h. Adversarial results already in final evidence dir ===
echo "Step h: Verify adversarial results in final evidence..."
if [ -f "$FINAL_EVIDENCE/adversarial-results.json" ]; then
    echo "  adversarial-results.json present"
else
    echo "  ERROR: adversarial-results.json not found in $FINAL_EVIDENCE"
    exit 1
fi
echo ""

# === i. Run final validator against same directory ===
echo "Step i: Run final validator..."
python3 "$ENGINE" --all --authoritative \
    --target-commit "$COMMIT" \
    --target-tree "$TREE" \
    --target-branch "$BRANCH" \
    --evidence-dir "$FINAL_EVIDENCE"
echo ""

# === j. Final gate assertion ===
echo "Step j: Final gate assertion..."
RESULTS="$FINAL_EVIDENCE/static-validation-results.json"
STAGE="$FINAL_EVIDENCE/stage-status.json"
ADV="$FINAL_EVIDENCE/adversarial-results.json"

# 1. Files exist
for f in "$RESULTS" "$STAGE" "$ADV"; do
    [ -f "$f" ] || { echo "ERROR: $f not found"; exit 1; }
done

# 2. Gate == READY_FOR_OPERATOR_REVIEW
GATE=$(python3 -c "import json; print(json.load(open('$STAGE'))['gate_status'])")
[ "$GATE" = "READY_FOR_OPERATOR_REVIEW" ] || { echo "ERROR: Gate=$GATE"; exit 1; }

# 3. Totals consistent
python3 -c "
import json, sys
d = json.load(open('$RESULTS'))
t = d['totals']
errors = []
if t.get('FAIL', 0) != 0: errors.append(f'FAIL={t[\"FAIL\"]}')
if t.get('BLOCKED', 0) != 0: errors.append(f'BLOCKED={t[\"BLOCKED\"]}')
expected = t.get('PASS',0)+t.get('FAIL',0)+t.get('BLOCKED',0)+t.get('SKIPPED',0)
if t.get('total',0) != expected: errors.append(f'total={t[\"total\"]} computed={expected}')
if errors: print(f'ERROR: {errors}', file=sys.stderr); sys.exit(1)
print(f'Totals OK: {t}')
"

# 4. Identity fields
python3 -c "
import json, subprocess, sys
d = json.load(open('$RESULTS'))
errors = []
actual_commit = subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True,cwd='$PROJ_ROOT').stdout.strip()
actual_tree = subprocess.run(['git','rev-parse','HEAD^{tree}'],capture_output=True,text=True,cwd='$PROJ_ROOT').stdout.strip()
if d.get('tested_commit','') != actual_commit: errors.append('commit mismatch')
if d.get('tested_tree','') != actual_tree: errors.append('tree mismatch')
if d.get('repository','') != 'dabiggestpoppa/larger-lab': errors.append('repository mismatch')
if d.get('validator_version','') != '3.5.0': errors.append(f'version mismatch: {d.get(\"validator_version\")}')
if d.get('run_id','') != '$RUN_ID': errors.append(f'run_id mismatch: {d.get(\"run_id\")} != $RUN_ID')
if errors: print(f'ERROR: {errors}', file=sys.stderr); sys.exit(1)
print('Identity fields OK')
"

# 5. Adversarial suite
python3 -c "
import json, sys
a = json.load(open('$ADV'))
errors = []
if a.get('suite_result','') != 'PASS': errors.append(f'suite_result={a.get(\"suite_result\")}')
if a.get('schema_version','') != '3.5.0': errors.append(f'schema_version={a.get(\"schema_version\")}')
if a.get('run_id','') != '$RUN_ID': errors.append(f'run_id mismatch: {a.get(\"run_id\")} != $RUN_ID')
neg = a.get('negative_tests', [])
meta = a.get('meta_tests', [])
if not neg: errors.append('no negative_tests')
if not meta: errors.append('no meta_tests')
for t in neg:
    tid = t.get('test_id','?')
    mr = t.get('mutation_result','')
    me = t.get('mutation_exit',0)
    if mr != 'FAIL': errors.append(f'{tid}: mutation_result={mr}')
    if me == 0 and mr not in ('N/A',''): errors.append(f'{tid}: mutation_exit=0')
for t in meta:
    tid = t.get('test_id','?')
    if t.get('result','') != 'PASS': errors.append(f'{tid}: result={t.get(\"result\")}')
if errors: print(f'ERRORS: {errors}', file=sys.stderr); sys.exit(1)
print(f'Adversarial OK: {len(neg)} negative + {len(meta)} meta')
"

echo "=== ALL GATE CHECKS PASSED ==="
echo ""

# === Cleanup worktree ===
rm -rf "$ADV_WORKTREE"

# === Output summary ===
echo "=============================================="
echo "  FINAL RESULT"
echo "=============================================="
echo "  RUN_ID:       $RUN_ID"
echo "  COMMIT:       ${COMMIT:0:12}"
echo "  Branch:       $BRANCH"
echo "  Evidence:     $FINAL_EVIDENCE"
echo "  Gate:         $GATE"
echo "=============================================="
echo ""
echo "Evidence directory ready for upload: $FINAL_EVIDENCE"
ls -la "$FINAL_EVIDENCE/"
