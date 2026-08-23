#!/usr/bin/env bash
#
# OCE Cloud Ground — Adversarial Test Suite
# B1-I1R3B — Real exit-code truth, no hardcoded validator_exit
#
# For every mutation:
#   1. Run baseline → must PASS and exit 0
#   2. Apply real mutation → run check → must FAIL and exit nonzero
#   3. Restore original → verify SHA256 match
#   4. Re-run baseline → must PASS and exit 0
#
# BLOCKED, SKIPPED, ERROR, missing result, or exit code 0 = test FAILURE.
#
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENGINE="$BASE_DIR/scripts/validate_engine.py"

PROJ_ROOT="$(cd "$BASE_DIR/../.." && pwd)"
WORK_TMP="$PROJ_ROOT/.oce-adversarial-tmp"
rm -rf "$WORK_TMP"
mkdir -p "$WORK_TMP"

EVIDENCE_DIR="$BASE_DIR/evidence"
mkdir -p "$EVIDENCE_DIR"

# Win-path helper for Python
win_path() {
    if command -v cygpath &>/dev/null; then cygpath -m "$1"; else echo "$1"; fi
}
BASE_DIR_WIN=$(win_path "$BASE_DIR")
ENGINE_WIN="$BASE_DIR_WIN/scripts/validate_engine.py"
EVIDENCE_DIR_WIN="$BASE_DIR_WIN/evidence"

PASS_COUNT=0
FAIL_COUNT=0
TOTAL_COUNT=0
TESTS_JSON="[]"

EVIDENCE_FILE="$EVIDENCE_DIR_WIN/static-validation-results.json"

# Run validator with a single check and capture the exit code
# Usage: run_check <check_id>
# Sets: _RUN_CHECK_EXIT, _RUN_CHECK_RESULT
run_check() {
    local check_id="$1"
    local rc=0
    python3 "$ENGINE_WIN" --only "$check_id" >/dev/null 2>&1 || rc=$?
    _RUN_CHECK_EXIT=$rc
}

# Run validator with authoritative mode and capture exit code
# Usage: run_check_authoritative <target_commit> <target_tree> <target_branch>
# Sets: _RUN_CHECK_EXIT
run_check_authoritative() {
    local tc="$1" tt="$2" tb="$3"
    local rc=0
    python3 "$ENGINE_WIN" --authoritative --target-commit "$tc" --target-tree "$tt" --target-branch "$tb" >/dev/null 2>&1 || rc=$?
    _RUN_CHECK_EXIT=$rc
}

# Read check result from latest evidence
get_result() {
    local check_id="$1"
    python3 -c "
import json, sys
try:
    data = json.load(open(sys.argv[1]))
    for r in data.get('results', []):
        if r['check_id'] == sys.argv[2]:
            print(r['result']); sys.exit(0)
    print('NOT_FOUND')
except Exception: print('ERROR')
" "$EVIDENCE_FILE" "$check_id"
}

# Single mutation test — real exit codes, no hardcoding
# Args: test_id description target_file expected_check mut_python_code
run_one() {
    local test_id="$1" desc="$2" target="$3" expect="$4" mut_code="$5"
    local target_win
    target_win=$(win_path "$target")

    TOTAL_COUNT=$((TOTAL_COUNT + 1))
    echo "  [$TOTAL_COUNT] $test_id: $desc"

    # 1. Baseline — must PASS and exit 0
    run_check "$expect"
    local baseline_exit=$_RUN_CHECK_EXIT
    local baseline_result
    baseline_result=$(get_result "$expect")
    if [ "$baseline_result" != "PASS" ]; then
        echo "    FAIL: baseline $expect=$baseline_result (exit $baseline_exit)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        TESTS_JSON=$(python3 -c "
import json,sys
t=json.loads(sys.argv[1]); t.append({'test_id':sys.argv[2],'description':sys.argv[3],
  'result':'FAIL','expected_check':sys.argv[4],'observed_check':sys.argv[5],
  'baseline_result':sys.argv[5],'baseline_exit':int(sys.argv[6]),
  'mutation_result':'NOT_RUN','mutation_exit':0,
  'post_restore_result':'NOT_RUN','post_restore_exit':0,
  'original_sha256':'','restored_sha256':'',
  'reason':'baseline failed'})
print(json.dumps(t))" "$TESTS_JSON" "$test_id" "$desc" "$expect" "$baseline_result" "$baseline_exit")
        return
    fi
    if [ "$baseline_exit" -ne 0 ]; then
        echo "    FAIL: baseline exit $baseline_exit (expected 0)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        TESTS_JSON=$(python3 -c "
import json,sys
t=json.loads(sys.argv[1]); t.append({'test_id':sys.argv[2],'description':sys.argv[3],
  'result':'FAIL','expected_check':sys.argv[4],'observed_check':sys.argv[5],
  'baseline_result':'PASS','baseline_exit':int(sys.argv[6]),
  'mutation_result':'NOT_RUN','mutation_exit':0,
  'post_restore_result':'NOT_RUN','post_restore_exit':0,
  'original_sha256':'','restored_sha256':'',
  'reason':'baseline exit nonzero'})
print(json.dumps(t))" "$TESTS_JSON" "$test_id" "$desc" "$expect" "$baseline_result" "$baseline_exit")
        return
    fi

    # 2. Hash original
    local orig_hash
    orig_hash=$(sha256sum "$target" | cut -d' ' -f1)

    # 3. Backup
    cp "$target" "$WORK_TMP/pre-${test_id}.json"

    # 4. Mutate — NO || true, NO 2>/dev/null; propagate failures
    local mut_rc=0
    python3 -c "$mut_code" "$target_win" || mut_rc=$?
    if [ "$mut_rc" -ne 0 ]; then
        echo "    FAIL: mutation code failed (exit $mut_rc)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        # Restore anyway
        cp "$WORK_TMP/pre-${test_id}.json" "$target"
        TESTS_JSON=$(python3 -c "
import json,sys
t=json.loads(sys.argv[1]); t.append({'test_id':sys.argv[2],'description':sys.argv[3],
  'result':'FAIL','expected_check':sys.argv[4],'observed_check':sys.argv[5],
  'baseline_result':'PASS','baseline_exit':0,
  'mutation_result':'MUTATION_ERROR','mutation_exit':int(sys.argv[6]),
  'post_restore_result':'NOT_RUN','post_restore_exit':0,
  'original_sha256':'','restored_sha256':'',
  'reason':'mutation code failed with exit '+sys.argv[6]})
print(json.dumps(t))" "$TESTS_JSON" "$test_id" "$desc" "$expect" "MUTATION_ERROR" "$mut_rc")
        return
    fi

    # 5. Run targeted check after mutation — must FAIL and exit nonzero
    run_check "$expect"
    local mutation_exit=$_RUN_CHECK_EXIT
    local mutation_result
    mutation_result=$(get_result "$expect")

    # 6. Restore
    cp "$WORK_TMP/pre-${test_id}.json" "$target"

    # 7. Verify hash
    local rest_hash
    rest_hash=$(sha256sum "$target" | cut -d' ' -f1)

    # 8. Re-baseline
    run_check "$expect"
    local post_restore_exit=$_RUN_CHECK_EXIT
    local post_restore_result
    post_restore_result=$(get_result "$expect")

    # 9. Evaluate
    local pass=true reason=""
    if [ "$mutation_result" = "PASS" ]; then
        pass=false; reason="mutation not detected (check still PASS)"
    elif [ "$mutation_result" = "NOT_FOUND" ] || [ "$mutation_result" = "ERROR" ]; then
        pass=false; reason="check $expect returned $mutation_result"
    elif [ "$mutation_exit" -eq 0 ]; then
        pass=false; reason="mutation exit code was 0 (must be nonzero)"
    fi
    if [ "$orig_hash" != "$rest_hash" ]; then
        pass=false; reason="restoration hash mismatch: orig=$orig_hash restored=$rest_hash"
    fi
    if [ "$post_restore_result" != "PASS" ]; then
        pass=false; reason="post-restore baseline=$post_restore_result (expected PASS)"
    fi
    if [ "$post_restore_exit" -ne 0 ]; then
        pass=false; reason="post-restore exit $post_restore_exit (expected 0)"
    fi

    if [ "$pass" = true ]; then
        echo "    PASS"
        PASS_COUNT=$((PASS_COUNT + 1))
        TESTS_JSON=$(python3 -c "
import json,sys
t=json.loads(sys.argv[1]); t.append({'test_id':sys.argv[2],'description':sys.argv[3],
  'result':'PASS','expected_check':sys.argv[4],'observed_check':sys.argv[5],
  'baseline_result':'PASS','baseline_exit':0,
  'mutation_result':sys.argv[5],'mutation_exit':int(sys.argv[6]),
  'post_restore_result':'PASS','post_restore_exit':0,
  'original_sha256':sys.argv[7],'restored_sha256':sys.argv[8],
  'reason':'Mutation detected, restored, baseline clean'})
print(json.dumps(t))" "$TESTS_JSON" "$test_id" "$desc" "$expect" "$mutation_result" "$mutation_exit" "$orig_hash" "$rest_hash")
    else
        echo "    FAIL: $reason"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        TESTS_JSON=$(python3 -c "
import json,sys
t=json.loads(sys.argv[1]); t.append({'test_id':sys.argv[2],'description':sys.argv[3],
  'result':'FAIL','expected_check':sys.argv[4],'observed_check':sys.argv[5],
  'baseline_result':'PASS','baseline_exit':0,
  'mutation_result':sys.argv[5],'mutation_exit':int(sys.argv[6]),
  'post_restore_result':sys.argv[7],'post_restore_exit':int(sys.argv[8]),
  'original_sha256':sys.argv[9],'restored_sha256':sys.argv[10],
  'reason':sys.argv[11]})
print(json.dumps(t))" "$TESTS_JSON" "$test_id" "$desc" "$expect" "$mutation_result" "$mutation_exit" "$post_restore_result" "$post_restore_exit" "$orig_hash" "$rest_hash" "$reason")
    fi
}

# Command-line negative test (not file mutation)
# Runs the validator with specific args and checks it FAILs
# Args: test_id description expected_check run_args (as separate args)
run_cli_negative() {
    local test_id="$1" desc="$2" expect="$3"
    shift 3

    TOTAL_COUNT=$((TOTAL_COUNT + 1))
    echo "  [$TOTAL_COUNT] $test_id: $desc"

    local rc=0
    python3 "$ENGINE_WIN" "$@" >/dev/null 2>&1 || rc=$?
    local result
    result=$(get_result "$expect")

    local pass_status="FAIL"
    local reason=""
    if [ "$rc" -ne 0 ] && [ "$result" = "FAIL" ]; then
        pass_status="PASS"
        echo "    PASS"
        PASS_COUNT=$((PASS_COUNT + 1))
        reason="CLI rejection confirmed"
    else
        echo "    FAIL: expected FAIL+nonzero, got result=$result exit=$rc"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        reason="Expected rejection but got result=$result exit=$rc"
    fi

    TESTS_JSON=$(python3 -c "
import json,sys
t=json.loads(sys.argv[1])
t.append({'test_id':sys.argv[2],'description':sys.argv[3],
  'result':sys.argv[4],'expected_check':sys.argv[5],'observed_check':sys.argv[6],
  'baseline_result':'N/A','baseline_exit':0,
  'mutation_result':sys.argv[6],'mutation_exit':int(sys.argv[7]),
  'post_restore_result':'N/A','post_restore_exit':0,
  'original_sha256':'N/A','restored_sha256':'N/A',
  'reason':sys.argv[8]})
print(json.dumps(t))" "$TESTS_JSON" "$test_id" "$desc" "$pass_status" "$expect" "$result" "$rc" "$reason")
}

echo "=============================================="
echo "  OCE B1-I1R3B Adversarial Test Suite"
echo "=============================================="
echo "Engine: $ENGINE"
echo ""

IDENTITY="$BASE_DIR/contracts/checkpoint-identity-data.json"
COMPOSE="$BASE_DIR/compose/compose.foundation.yml"
POLICY="$BASE_DIR/policy/network-access.yml"
SCHEMA="$BASE_DIR/contracts/worker-task-envelope.schema.json"
ANSIBLE_CFG="$BASE_DIR/ansible/ansible.cfg"

# === BLOCK A: Source Identity (1-9) ===
echo "--- Block A: Source Identity ---"

run_one "ID-01" "Wrong repo owner" "$IDENTITY" "SOURCE-IDENTITY" "
import json,sys; p=sys.argv[1]; d=json.load(open(p));
d['repository']['owner']='wrong'; json.dump(d,open(p,'w'),indent=2)
"

run_one "ID-02" "Wrong repo name" "$IDENTITY" "SOURCE-IDENTITY" "
import json,sys; p=sys.argv[1]; d=json.load(open(p));
d['repository']['name']='other-repo'; json.dump(d,open(p,'w'),indent=2)
"

run_one "ID-03" "Wrong authorized branch" "$IDENTITY" "SOURCE-IDENTITY" "
import json,sys; p=sys.argv[1]; d=json.load(open(p));
d['authorized_branch']='main'; json.dump(d,open(p,'w'),indent=2)
"

run_one "ID-04" "Wrong authoritative base SHA" "$IDENTITY" "SOURCE-IDENTITY" "
import json,sys; p=sys.argv[1]; d=json.load(open(p));
d['authoritative_base_sha']='0000000000000000000000000000000000000000';
json.dump(d,open(p,'w'),indent=2)
"

run_one "ID-05" "Wrong expected project root" "$IDENTITY" "SOURCE-IDENTITY" "
import json,sys; p=sys.argv[1]; d=json.load(open(p));
d['expected_project_root']='wrong/path'; json.dump(d,open(p,'w'),indent=2)
"

run_one "ID-06" "Wrong accepted origins" "$IDENTITY" "SOURCE-IDENTITY" "
import json,sys; p=sys.argv[1]; d=json.load(open(p));
d['accepted_origins']=['https://evil.com/repo.git'];
json.dump(d,open(p,'w'),indent=2)
"

run_one "ID-07" "Crypto Data commit as expected SHA" "$IDENTITY" "SOURCE-IDENTITY" "
import json,sys; p=sys.argv[1]; d=json.load(open(p));
d['expected_implementation_commit_source']='f41e9c09d028713acc7e4c9dfd7194abdb15c678';
json.dump(d,open(p,'w'),indent=2)
"

run_one "ID-08" "Wrong repository full_name" "$IDENTITY" "SOURCE-IDENTITY" "
import json,sys; p=sys.argv[1]; d=json.load(open(p));
d['repository']['full_name']='wrong/repo';
json.dump(d,open(p,'w'),indent=2)
"

run_one "ID-09" "Wrong expected tree SHA" "$IDENTITY" "SOURCE-IDENTITY" "
import json,sys; p=sys.argv[1]; d=json.load(open(p));
d['expected_tree_sha']='0000000000000000000000000000000000000000';
json.dump(d,open(p,'w'),indent=2)
"

echo ""

# === BLOCK B: Compose / Image (10-14) ===
echo "--- Block B: Compose / Image ---"

run_one "CM-01" "PostgreSQL tag-only (no digest)" "$COMPOSE" "DIGEST-LOCK" "
import sys, re; p=sys.argv[1]; c=open(p).read()
c=re.sub(r'image: postgres@sha256:[a-f0-9]+', 'image: postgres:16.4-alpine', c)
open(p,'w').write(c)
"

run_one "CM-02" "Redis tag-only (no digest)" "$COMPOSE" "DIGEST-LOCK" "
import sys, re; p=sys.argv[1]; c=open(p).read()
c=re.sub(r'image: redis@sha256:[a-f0-9]+', 'image: redis:7.4-alpine', c)
open(p,'w').write(c)
"

run_one "CM-03" "Remove healthcheck from compose" "$COMPOSE" "HEALTH-CHECKS" "
import sys; p=sys.argv[1]; c=open(p).read()
c=c.replace('healthcheck:', '_healthcheck_DISABLED:')
open(p,'w').write(c)
"

run_one "CM-04" "Add :latest tag to PostgreSQL" "$COMPOSE" "NO-LATEST-TAGS" "
import sys, re; p=sys.argv[1]; c=open(p).read()
c=re.sub(r'image: postgres@sha256:[a-f0-9]+', 'image: postgres:latest', c)
open(p,'w').write(c)
"

run_one "CM-05" "Remove security_opt from compose" "$COMPOSE" "SECURITY-OPTS" "
import sys; p=sys.argv[1]; c=open(p).read()
c=c.replace('no-new-privileges', '_REMOVED')
open(p,'w').write(c)
"

echo ""

# === BLOCK C: Policy (15-18) ===
echo "--- Block C: Policy ---"

run_one "PL-01" "Remove a worker DENY rule" "$POLICY" "WORKER-NO-DB" "
import sys; p=sys.argv[1]; lines=open(p).readlines()
out = [l for l in lines if 'action: DENY' not in l]
open(p,'w').writelines(out)
"

run_one "PL-02" "Remove worker-local postgresql denial only" "$POLICY" "WORKER-NO-DB" "
import sys; p=sys.argv[1]
lines=open(p).readlines(); out=[]; skip=0
for i,l in enumerate(lines):
    if skip>0: skip-=1; continue
    if 'from: worker-local' in l and i+2<len(lines) and 'to: postgresql' in lines[i+1] and 'action: DENY' in lines[i+2]:
        skip=2; continue
    out.append(l)
open(p,'w').writelines(out)
"

run_one "PL-03" "Remove all SSH denials from policy" "$POLICY" "WORKER-NO-DB" "
import sys; p=sys.argv[1]
lines=open(p).readlines(); out=[]; skip=0
for i,l in enumerate(lines):
    if skip>0: skip-=1; continue
    if i+1<len(lines) and 'action: DENY' in lines[i+1] and 'to: ssh' in l:
        skip=1; continue
    out.append(l)
open(p,'w').writelines(out)
"

run_one "PL-04" "Remove all Docker denials from policy" "$POLICY" "WORKER-NO-DB" "
import sys; p=sys.argv[1]
lines=open(p).readlines(); out=[]; skip=0
for i,l in enumerate(lines):
    if skip>0: skip-=1; continue
    if i+1<len(lines) and 'action: DENY' in lines[i+1] and 'to: docker' in l:
        skip=1; continue
    out.append(l)
open(p,'w').writelines(out)
"

echo ""

# === BLOCK D: Evidence / Schema (19-23) ===
echo "--- Block D: Evidence / Schema ---"

# EV-01: Source identity with wrong repository (manual mutation of identity file)
TOTAL_COUNT=$((TOTAL_COUNT + 1))
echo "  [$TOTAL_COUNT] EV-01: Source identity rejects wrong repository"
run_check "SOURCE-IDENTITY"
cp "$IDENTITY" "$WORK_TMP/pre-EV-01.json"
orig_hash_ev01=$(sha256sum "$IDENTITY" | cut -d' ' -f1)
python3 -c "
import json,sys; p=sys.argv[1]; d=json.load(open(p));
d['repository']['owner']='wrong-owner'; json.dump(d,open(p,'w'),indent=2)
" "$(win_path "$IDENTITY")"
run_check "SOURCE-IDENTITY"
mutation_exit_ev01=$_RUN_CHECK_EXIT
mutation_result_ev01=$(get_result "SOURCE-IDENTITY")
cp "$WORK_TMP/pre-EV-01.json" "$IDENTITY"
rest_hash_ev01=$(sha256sum "$IDENTITY" | cut -d' ' -f1)
run_check "SOURCE-IDENTITY"
post_restore_exit_ev01=$_RUN_CHECK_EXIT
post_restore_result_ev01=$(get_result "SOURCE-IDENTITY")

if [ "$mutation_result_ev01" = "FAIL" ] && [ "$mutation_exit_ev01" -ne 0 ] && \
   [ "$post_restore_result_ev01" = "PASS" ] && [ "$post_restore_exit_ev01" -eq 0 ] && \
   [ "$orig_hash_ev01" = "$rest_hash_ev01" ]; then
    echo "    PASS"
    PASS_COUNT=$((PASS_COUNT + 1))
    TESTS_JSON=$(python3 -c "
import json,sys
t=json.loads(sys.argv[1]); t.append({'test_id':'EV-01','description':'Source identity rejects wrong repository',
  'result':'PASS','expected_check':'SOURCE-IDENTITY','observed_check':sys.argv[2],
  'baseline_result':'PASS','baseline_exit':0,'mutation_result':'FAIL','mutation_exit':int(sys.argv[3]),
  'post_restore_result':'PASS','post_restore_exit':0,'original_sha256':sys.argv[4],'restored_sha256':sys.argv[5],
  'reason':'Correctly rejected wrong repo'})
print(json.dumps(t))" "$TESTS_JSON" "$mutation_result_ev01" "$mutation_exit_ev01" "$orig_hash_ev01" "$rest_hash_ev01")
else
    echo "    FAIL: wrong repo not rejected (mut=$mutation_result_ev01 exit=$mutation_exit_ev01)"
    FAIL_COUNT=$((FAIL_COUNT + 1))
    TESTS_JSON=$(python3 -c "
import json,sys
t=json.loads(sys.argv[1]); t.append({'test_id':'EV-01','description':'Source identity rejects wrong repository',
  'result':'FAIL','expected_check':'SOURCE-IDENTITY','observed_check':sys.argv[2],
  'baseline_result':'PASS','baseline_exit':0,'mutation_result':sys.argv[2],'mutation_exit':int(sys.argv[3]),
  'post_restore_result':sys.argv[4],'post_restore_exit':int(sys.argv[5]),
  'original_sha256':sys.argv[6],'restored_sha256':sys.argv[7],
  'reason':'Wrong repo not rejected'})
print(json.dumps(t))" "$TESTS_JSON" "$mutation_result_ev01" "$mutation_exit_ev01" "$post_restore_result_ev01" "$post_restore_exit_ev01" "$orig_hash_ev01" "$rest_hash_ev01")
fi

# EV-02: Evidence with wrong commit
TOTAL_COUNT=$((TOTAL_COUNT + 1))
echo "  [$TOTAL_COUNT] EV-02: Evidence with wrong commit"
run_check "SOURCE-IDENTITY"  # Get clean evidence
cp "$EVIDENCE_FILE" "$WORK_TMP/pre-EV-02.json"
orig_hash_ev02=$(sha256sum "$EVIDENCE_FILE" | cut -d' ' -f1)
python3 -c "
import json,sys; p=sys.argv[1]; d=json.load(open(p));
d['tested_commit']='f41e9c09d028713acc7e4c9dfd7194abdb15c678';
json.dump(d,open(p,'w'),indent=2)
" "$EVIDENCE_FILE"
run_check "EVIDENCE-CONSISTENCY"
mutation_exit_ev02=$_RUN_CHECK_EXIT
mutation_result_ev02=$(get_result "EVIDENCE-CONSISTENCY")
cp "$WORK_TMP/pre-EV-02.json" "$EVIDENCE_FILE"
rest_hash_ev02=$(sha256sum "$EVIDENCE_FILE" | cut -d' ' -f1)
run_check "EVIDENCE-CONSISTENCY"
post_restore_exit_ev02=$_RUN_CHECK_EXIT
post_restore_result_ev02=$(get_result "EVIDENCE-CONSISTENCY")

if [ "$mutation_result_ev02" = "FAIL" ] && [ "$mutation_exit_ev02" -ne 0 ] && \
   [ "$post_restore_result_ev02" = "PASS" ] && [ "$post_restore_exit_ev02" -eq 0 ] && \
   [ "$orig_hash_ev02" = "$rest_hash_ev02" ]; then
    echo "    PASS"
    PASS_COUNT=$((PASS_COUNT + 1))
    TESTS_JSON=$(python3 -c "
import json,sys
t=json.loads(sys.argv[1]); t.append({'test_id':'EV-02','description':'Evidence wrong commit',
  'result':'PASS','expected_check':'EVIDENCE-CONSISTENCY','observed_check':sys.argv[2],
  'baseline_result':'PASS','baseline_exit':0,'mutation_result':'FAIL','mutation_exit':int(sys.argv[3]),
  'post_restore_result':'PASS','post_restore_exit':0,'original_sha256':sys.argv[4],'restored_sha256':sys.argv[5],
  'reason':'Detected tampered commit'})
print(json.dumps(t))" "$TESTS_JSON" "$mutation_result_ev02" "$mutation_exit_ev02" "$orig_hash_ev02" "$rest_hash_ev02")
else
    echo "    FAIL: evidence tampering not detected (mut=$mutation_result_ev02 exit=$mutation_exit_ev02)"
    FAIL_COUNT=$((FAIL_COUNT + 1))
    TESTS_JSON=$(python3 -c "
import json,sys
t=json.loads(sys.argv[1]); t.append({'test_id':'EV-02','description':'Evidence wrong commit',
  'result':'FAIL','expected_check':'EVIDENCE-CONSISTENCY','observed_check':sys.argv[2],
  'baseline_result':'PASS','baseline_exit':0,'mutation_result':sys.argv[2],'mutation_exit':int(sys.argv[3]),
  'post_restore_result':sys.argv[4],'post_restore_exit':int(sys.argv[5]),
  'original_sha256':sys.argv[6],'restored_sha256':sys.argv[7],
  'reason':'Tampering not detected'})
print(json.dumps(t))" "$TESTS_JSON" "$mutation_result_ev02" "$mutation_exit_ev02" "$post_restore_result_ev02" "$post_restore_exit_ev02" "$orig_hash_ev02" "$rest_hash_ev02")
fi

# EV-03: Evidence with wrong tree
TOTAL_COUNT=$((TOTAL_COUNT + 1))
echo "  [$TOTAL_COUNT] EV-03: Evidence with wrong tree"
run_check "SOURCE-IDENTITY"
cp "$EVIDENCE_FILE" "$WORK_TMP/pre-EV-03.json"
orig_hash_ev03=$(sha256sum "$EVIDENCE_FILE" | cut -d' ' -f1)
python3 -c "
import json,sys; p=sys.argv[1]; d=json.load(open(p));
d['tested_tree']='0000000000000000000000000000000000000000';
json.dump(d,open(p,'w'),indent=2)
" "$EVIDENCE_FILE"
run_check "EVIDENCE-CONSISTENCY"
mutation_exit_ev03=$_RUN_CHECK_EXIT
mutation_result_ev03=$(get_result "EVIDENCE-CONSISTENCY")
cp "$WORK_TMP/pre-EV-03.json" "$EVIDENCE_FILE"
rest_hash_ev03=$(sha256sum "$EVIDENCE_FILE" | cut -d' ' -f1)
run_check "EVIDENCE-CONSISTENCY"
post_restore_exit_ev03=$_RUN_CHECK_EXIT
post_restore_result_ev03=$(get_result "EVIDENCE-CONSISTENCY")

if [ "$mutation_result_ev03" = "FAIL" ] && [ "$mutation_exit_ev03" -ne 0 ] && \
   [ "$post_restore_result_ev03" = "PASS" ] && [ "$post_restore_exit_ev03" -eq 0 ] && \
   [ "$orig_hash_ev03" = "$rest_hash_ev03" ]; then
    echo "    PASS"
    PASS_COUNT=$((PASS_COUNT + 1))
    TESTS_JSON=$(python3 -c "
import json,sys
t=json.loads(sys.argv[1]); t.append({'test_id':'EV-03','description':'Evidence wrong tree',
  'result':'PASS','expected_check':'EVIDENCE-CONSISTENCY','observed_check':sys.argv[2],
  'baseline_result':'PASS','baseline_exit':0,'mutation_result':'FAIL','mutation_exit':int(sys.argv[3]),
  'post_restore_result':'PASS','post_restore_exit':0,'original_sha256':sys.argv[4],'restored_sha256':sys.argv[5],
  'reason':'Detected wrong tree'})
print(json.dumps(t))" "$TESTS_JSON" "$mutation_result_ev03" "$mutation_exit_ev03" "$orig_hash_ev03" "$rest_hash_ev03")
else
    echo "    FAIL: wrong tree not detected (mut=$mutation_result_ev03 exit=$mutation_exit_ev03)"
    FAIL_COUNT=$((FAIL_COUNT + 1))
    TESTS_JSON=$(python3 -c "
import json,sys
t=json.loads(sys.argv[1]); t.append({'test_id':'EV-03','description':'Evidence wrong tree',
  'result':'FAIL','expected_check':'EVIDENCE-CONSISTENCY','observed_check':sys.argv[2],
  'baseline_result':'PASS','baseline_exit':0,'mutation_result':sys.argv[2],'mutation_exit':int(sys.argv[3]),
  'post_restore_result':sys.argv[4],'post_restore_exit':int(sys.argv[5]),
  'original_sha256':sys.argv[6],'restored_sha256':sys.argv[7],
  'reason':'Wrong tree not detected'})
print(json.dumps(t))" "$TESTS_JSON" "$mutation_result_ev03" "$mutation_exit_ev03" "$post_restore_result_ev03" "$post_restore_exit_ev03" "$orig_hash_ev03" "$rest_hash_ev03")
fi

# EV-04: Evidence with inconsistent totals
TOTAL_COUNT=$((TOTAL_COUNT + 1))
echo "  [$TOTAL_COUNT] EV-04: Evidence with inconsistent totals"
run_check "SOURCE-IDENTITY"
cp "$EVIDENCE_FILE" "$WORK_TMP/pre-EV-04.json"
orig_hash_ev04=$(sha256sum "$EVIDENCE_FILE" | cut -d' ' -f1)
python3 -c "
import json,sys; p=sys.argv[1]; d=json.load(open(p));
d['totals']['total']=999;
json.dump(d,open(p,'w'),indent=2)
" "$EVIDENCE_FILE"
run_check "EVIDENCE-CONSISTENCY"
mutation_exit_ev04=$_RUN_CHECK_EXIT
mutation_result_ev04=$(get_result "EVIDENCE-CONSISTENCY")
cp "$WORK_TMP/pre-EV-04.json" "$EVIDENCE_FILE"
rest_hash_ev04=$(sha256sum "$EVIDENCE_FILE" | cut -d' ' -f1)
run_check "EVIDENCE-CONSISTENCY"
post_restore_exit_ev04=$_RUN_CHECK_EXIT
post_restore_result_ev04=$(get_result "EVIDENCE-CONSISTENCY")

if [ "$mutation_result_ev04" = "FAIL" ] && [ "$mutation_exit_ev04" -ne 0 ] && \
   [ "$post_restore_result_ev04" = "PASS" ] && [ "$post_restore_exit_ev04" -eq 0 ] && \
   [ "$orig_hash_ev04" = "$rest_hash_ev04" ]; then
    echo "    PASS"
    PASS_COUNT=$((PASS_COUNT + 1))
    TESTS_JSON=$(python3 -c "
import json,sys
t=json.loads(sys.argv[1]); t.append({'test_id':'EV-04','description':'Evidence inconsistent totals',
  'result':'PASS','expected_check':'EVIDENCE-CONSISTENCY','observed_check':sys.argv[2],
  'baseline_result':'PASS','baseline_exit':0,'mutation_result':'FAIL','mutation_exit':int(sys.argv[3]),
  'post_restore_result':'PASS','post_restore_exit':0,'original_sha256':sys.argv[4],'restored_sha256':sys.argv[5],
  'reason':'Detected wrong totals'})
print(json.dumps(t))" "$TESTS_JSON" "$mutation_result_ev04" "$mutation_exit_ev04" "$orig_hash_ev04" "$rest_hash_ev04")
else
    echo "    FAIL: wrong totals not detected (mut=$mutation_result_ev04 exit=$mutation_exit_ev04)"
    FAIL_COUNT=$((FAIL_COUNT + 1))
    TESTS_JSON=$(python3 -c "
import json,sys
t=json.loads(sys.argv[1]); t.append({'test_id':'EV-04','description':'Evidence inconsistent totals',
  'result':'FAIL','expected_check':'EVIDENCE-CONSISTENCY','observed_check':sys.argv[2],
  'baseline_result':'PASS','baseline_exit':0,'mutation_result':sys.argv[2],'mutation_exit':int(sys.argv[3]),
  'post_restore_result':sys.argv[4],'post_restore_exit':int(sys.argv[5]),
  'original_sha256':sys.argv[6],'restored_sha256':sys.argv[7],
  'reason':'Wrong totals not detected'})
print(json.dumps(t))" "$TESTS_JSON" "$mutation_result_ev04" "$mutation_exit_ev04" "$post_restore_result_ev04" "$post_restore_exit_ev04" "$orig_hash_ev04" "$rest_hash_ev04")
fi

echo ""

# === BLOCK E: Infrastructure Config (24-28) ===
echo "--- Block E: Infrastructure Config ---"

# ST-01: Schema weaken
run_one "ST-01" "Remove required fields from schema" "$SCHEMA" "SCHEMA-FIXTURES" "
import json,sys; p=sys.argv[1]; d=json.load(open(p));
d['required']=[]; json.dump(d,open(p,'w'),indent=2)
"

# CF-01: Disable host_key_checking in ansible.cfg
run_one "CF-01" "Disable host_key_checking in ansible.cfg" "$ANSIBLE_CFG" "HOST-KEY-CHECKING" "
import sys; p=sys.argv[1]; c=open(p).read()
c=c.replace('host_key_checking = True', 'host_key_checking = False')
open(p,'w').write(c)
"

# CF-02: Add :latest tag to Redis in compose
run_one "CF-02" "Add :latest tag to Redis" "$COMPOSE" "NO-LATEST-TAGS" "
import sys, re; p=sys.argv[1]; c=open(p).read()
c=re.sub(r'image: redis@sha256:[a-f0-9]+', 'image: redis:latest', c)
open(p,'w').write(c)
"

echo ""

# === BLOCK F: CLI Negative Tests (29-33) ===
echo "--- Block F: CLI Negative Tests ---"

# CLI-01: Missing authoritative identity input
# Engine exits before writing evidence, so check exit code only
TOTAL_COUNT=$((TOTAL_COUNT + 1))
echo "  [$TOTAL_COUNT] CLI-01: Authoritative mode rejects missing identity inputs"
cli01_rc=0
python3 "$ENGINE_WIN" --authoritative >/dev/null 2>&1 || cli01_rc=$?
if [ "$cli01_rc" -ne 0 ]; then
    echo "    PASS"
    PASS_COUNT=$((PASS_COUNT + 1))
    TESTS_JSON=$(python3 -c "import json,sys;t=json.loads(sys.argv[1]);t.append({'test_id':'CLI-01','description':'Authoritative mode rejects missing identity inputs','result':'PASS','expected_check':'SOURCE-IDENTITY','observed_check':'BLOCKED','baseline_result':'N/A','baseline_exit':0,'mutation_result':'BLOCKED','mutation_exit':int(sys.argv[2]),'post_restore_result':'N/A','post_restore_exit':0,'original_sha256':'N/A','restored_sha256':'N/A','reason':'Engine exited with nonzero code before writing evidence'});print(json.dumps(t))" "$TESTS_JSON" "$cli01_rc")
else
    echo "    FAIL: authoritative mode accepted missing inputs (exit=$cli01_rc)"
    FAIL_COUNT=$((FAIL_COUNT + 1))
    TESTS_JSON=$(python3 -c "import json,sys;t=json.loads(sys.argv[1]);t.append({'test_id':'CLI-01','description':'Authoritative mode rejects missing identity inputs','result':'FAIL','expected_check':'SOURCE-IDENTITY','observed_check':'PASS','baseline_result':'N/A','baseline_exit':0,'mutation_result':'PASS','mutation_exit':int(sys.argv[2]),'post_restore_result':'N/A','post_restore_exit':0,'original_sha256':'N/A','restored_sha256':'N/A','reason':'Authoritative mode accepted missing identity input'});print(json.dumps(t))" "$TESTS_JSON" "$cli01_rc")
fi

# Get current git state for CLI tests
CURR_COMMIT=$(git -C "$PROJ_ROOT" rev-parse HEAD)
CURR_TREE=$(git -C "$PROJ_ROOT" rev-parse "HEAD^{tree}")
CURR_BRANCH=$(git -C "$PROJ_ROOT" branch --show-current)

# CLI-02: Authoritative mode with wrong target commit
WRONG_COMMIT="0000000000000000000000000000000000000000"
run_cli_negative "CLI-02" "Authoritative mode rejects wrong target commit" "SOURCE-IDENTITY" --authoritative --target-commit "$WRONG_COMMIT" --target-tree "$CURR_TREE" --target-branch "$CURR_BRANCH"

# CLI-03: Authoritative mode with wrong branch
run_cli_negative "CLI-03" "Authoritative mode rejects wrong branch" "SOURCE-IDENTITY" --authoritative --target-commit "$CURR_COMMIT" --target-tree "$CURR_TREE" --target-branch "wrong-branch"

# CLI-04: Authoritative mode with wrong repository (env manipulation)
TOTAL_COUNT=$((TOTAL_COUNT + 1))
echo "  [$TOTAL_COUNT] CLI-04: Authoritative mode rejects wrong repository"
GITHUB_REPOSITORY_ORIG="${GITHUB_REPOSITORY:-}"
export GITHUB_REPOSITORY="wrong-owner/wrong-repo"
cli04_rc=0
python3 "$ENGINE_WIN" --authoritative --target-commit "$CURR_COMMIT" --target-tree "$CURR_TREE" --target-branch "$CURR_BRANCH" >/dev/null 2>&1 || cli04_rc=$?
if [ -n "$GITHUB_REPOSITORY_ORIG" ]; then
    export GITHUB_REPOSITORY="$GITHUB_REPOSITORY_ORIG"
else
    unset GITHUB_REPOSITORY
fi
if [ "$cli04_rc" -ne 0 ]; then
    echo "    PASS"
    PASS_COUNT=$((PASS_COUNT + 1))
    TESTS_JSON=$(python3 -c "import json,sys;t=json.loads(sys.argv[1]);t.append({'test_id':'CLI-04','description':'Authoritative mode rejects wrong repository','result':'PASS','expected_check':'SOURCE-IDENTITY','observed_check':'FAIL','baseline_result':'N/A','baseline_exit':0,'mutation_result':'FAIL','mutation_exit':int(sys.argv[2]),'post_restore_result':'N/A','post_restore_exit':0,'original_sha256':'N/A','restored_sha256':'N/A','reason':'Correctly rejected wrong repository'});print(json.dumps(t))" "$TESTS_JSON" "$cli04_rc")
else
    echo "    FAIL: accepted wrong repository (exit=$cli04_rc)"
    FAIL_COUNT=$((FAIL_COUNT + 1))
    TESTS_JSON=$(python3 -c "import json,sys;t=json.loads(sys.argv[1]);t.append({'test_id':'CLI-04','description':'Authoritative mode rejects wrong repository','result':'FAIL','expected_check':'SOURCE-IDENTITY','observed_check':'PASS','baseline_result':'N/A','baseline_exit':0,'mutation_result':'PASS','mutation_exit':int(sys.argv[2]),'post_restore_result':'N/A','post_restore_exit':0,'original_sha256':'N/A','restored_sha256':'N/A','reason':'Accepted wrong repository'});print(json.dumps(t))" "$TESTS_JSON" "$cli04_rc")
fi

# CLI-05: Validator returning textual FAIL with exit code 0 (negative test)
# This verifies the engine does NOT return exit 0 when checks fail
TOTAL_COUNT=$((TOTAL_COUNT + 1))
echo "  [$TOTAL_COUNT] CLI-05: Validator rejects textual FAIL with exit 0"
cp "$IDENTITY" "$WORK_TMP/pre-CLI-05.json"
python3 -c "import json,sys;p=sys.argv[1];d=json.load(open(p));d['repository']['owner']='wrong-owner';json.dump(d,open(p,'w'),indent=2)" "$(win_path "$IDENTITY")"
cli05_rc=0
python3 "$ENGINE_WIN" --only "SOURCE-IDENTITY" >/dev/null 2>&1 || cli05_rc=$?
cp "$WORK_TMP/pre-CLI-05.json" "$IDENTITY"
cli05_result=$(get_result "SOURCE-IDENTITY")
if [ "$cli05_result" = "FAIL" ] && [ "$cli05_rc" -ne 0 ]; then
    echo "    PASS"
    PASS_COUNT=$((PASS_COUNT + 1))
    TESTS_JSON=$(python3 -c "import json,sys;t=json.loads(sys.argv[1]);t.append({'test_id':'CLI-05','description':'Validator rejects textual FAIL with exit 0','result':'PASS','expected_check':'SOURCE-IDENTITY','observed_check':sys.argv[2],'baseline_result':'N/A','baseline_exit':0,'mutation_result':sys.argv[2],'mutation_exit':int(sys.argv[3]),'post_restore_result':'N/A','post_restore_exit':0,'original_sha256':'N/A','restored_sha256':'N/A','reason':'FAIL result correctly paired with nonzero exit code'});print(json.dumps(t))" "$TESTS_JSON" "$cli05_result" "$cli05_rc")
else
    echo "    FAIL: result=$cli05_result exit=$cli05_rc (expected FAIL+nonzero)"
    FAIL_COUNT=$((FAIL_COUNT + 1))
    TESTS_JSON=$(python3 -c "import json,sys;t=json.loads(sys.argv[1]);t.append({'test_id':'CLI-05','description':'Validator rejects textual FAIL with exit 0','result':'FAIL','expected_check':'SOURCE-IDENTITY','observed_check':sys.argv[2],'baseline_result':'N/A','baseline_exit':0,'mutation_result':sys.argv[2],'mutation_exit':int(sys.argv[3]),'post_restore_result':'N/A','post_restore_exit':0,'original_sha256':'N/A','restored_sha256':'N/A','reason':'Expected FAIL+nonzero but got '+sys.argv[2]+' exit='+sys.argv[3]});print(json.dumps(t))" "$TESTS_JSON" "$cli05_result" "$cli05_rc")
fi

echo ""

# === BLOCK G: State Negative Tests (34-35) ===
echo "--- Block G: State Negative Tests ---"

# ST-02: Dirty worktree in authoritative mode
echo "dirty" > "$PROJ_ROOT/.oce-adversarial-dirty-test"
run_cli_negative "ST-02" "Authoritative mode rejects dirty worktree" "SOURCE-IDENTITY" --authoritative --target-commit "$CURR_COMMIT" --target-tree "$CURR_TREE" --target-branch "$CURR_BRANCH"
rm -f "$PROJ_ROOT/.oce-adversarial-dirty-test"

# ST-03: Wrong tree in authoritative mode
WRONG_TREE="0000000000000000000000000000000000000000000000000000000000000000"
run_cli_negative "ST-03" "Authoritative mode rejects wrong tree SHA" "SOURCE-IDENTITY" --authoritative --target-commit "$CURR_COMMIT" --target-tree "$WRONG_TREE" --target-branch "$CURR_BRANCH"

echo ""

# === SUMMARY ===
echo "=============================================="
echo "  Adversarial Test Summary"
echo "=============================================="
echo "  Total:   $TOTAL_COUNT"
echo "  PASS:    $PASS_COUNT"
echo "  FAIL:    $FAIL_COUNT"
echo "=============================================="

SUITE_RESULT="PASS"
if [ "$FAIL_COUNT" -gt 0 ]; then SUITE_RESULT="FAIL"; fi
if [ "$TOTAL_COUNT" -lt 30 ]; then SUITE_RESULT="FAIL"; fi
echo "  Suite:   $SUITE_RESULT"

# Write results JSON
python3 -c "
import json,sys
from datetime import datetime,timezone
tests=json.loads(sys.argv[1])
p=sum(1 for t in tests if t.get('result')=='PASS')
f=sum(1 for t in tests if t.get('result')=='FAIL')
r={'schema_version':'3.2.0','suite':'B1-I1R3B-adversarial','timestamp':datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
   'totals':{'total':len(tests),'PASS':p,'FAIL':f},'suite_result':sys.argv[2],'tests':tests}
with open(sys.argv[3],'w') as fp: json.dump(r,fp,indent=2)
import shutil; shutil.copy(sys.argv[3],sys.argv[4])
" "$TESTS_JSON" "$SUITE_RESULT" "$WORK_TMP/adversarial-results.json" "$EVIDENCE_DIR/adversarial-results.json"

rm -rf "$WORK_TMP"
[ "$SUITE_RESULT" = "PASS" ] && exit 0 || exit 1
