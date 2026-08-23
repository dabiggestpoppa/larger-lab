#!/usr/bin/env bash
#
# OCE Cloud Ground - Adversarial Test Suite
# B1-I1R3D - Authoritative Evidence Pipeline Closure
#
# Mutations apply to REAL source files with backup/restore.
# Evidence is written to an isolated directory (not canonical evidence/).
# Every negative test must record mutation_result=FAIL and mutation_exit>0.
# Meta-tests prove the gate rejects malformed or forbidden evidence.
# Test results are written to individual files to avoid cascading failures.
#
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENGINE="$BASE_DIR/scripts/validate_engine.py"
PROJ_ROOT="$(cd "$BASE_DIR/../.." && pwd)"

# Isolated evidence dir
EVIDENCE_DIR="${OCE_EVIDENCE_DIR:-$PROJ_ROOT/.oce-adversarial-evidence}"
mkdir -p "$EVIDENCE_DIR"
EVIDENCE_DIR=$(cd "$EVIDENCE_DIR" && pwd)

# Temp dir for backups
BACKUP_DIR="$PROJ_ROOT/.oce-adversarial-backups"
rm -rf "$BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Temp dir for test result files
RESULTS_DIR=$(mktemp -d "${TMPDIR:-$PROJ_ROOT}/oce-results-XXXXXX")
trap 'rm -rf "$BACKUP_DIR" "$RESULTS_DIR"' EXIT

PASS_COUNT=0
FAIL_COUNT=0
TOTAL_COUNT=0

win_path() {
    if command -v cygpath &>/dev/null; then cygpath -m "$1"; else echo "$1"; fi
}
ENGINE_WIN=$(win_path "$ENGINE")
EVIDENCE_DIR_WIN=$(win_path "$EVIDENCE_DIR")
EVIDENCE_FILE="$EVIDENCE_DIR_WIN/static-validation-results.json"

run_check() {
    local check_id="$1"
    local rc=0
    python3 "$ENGINE_WIN" --only "$check_id" --evidence-dir "$EVIDENCE_DIR_WIN" >/dev/null 2>&1 || rc=$?
    _RUN_CHECK_EXIT=$rc
}

get_result() {
    local check_id="$1"
    python3 -c "import json,sys; d=json.load(open(sys.argv[1])); results=[r['result'] for r in d.get('results',[]) if r['check_id']==sys.argv[2]]; sys.stdout.buffer.write((results[0] if results else 'NOT_FOUND').encode())" "$EVIDENCE_FILE" "$check_id" 2>/dev/null || echo -n ERROR
}

# Write a single test result to a file
write_result() {
    local test_id="$1" result="$2" description="$3" expected_check="$4" observed_check="$5" \
          baseline_result="$6" baseline_exit="$7" mutation_result="$8" mutation_exit="$9" \
          post_restore_result="${10}" post_restore_exit="${11}" original_sha256="${12}" \
          restored_sha256="${13}" reason="${14}"
    python3 -c "
import json, sys
t = {
    'test_id': sys.argv[1], 'result': sys.argv[2], 'description': sys.argv[3],
    'expected_check': sys.argv[4], 'observed_check': sys.argv[5],
    'baseline_result': sys.argv[6], 'baseline_exit': int(sys.argv[7]),
    'mutation_result': sys.argv[8], 'mutation_exit': int(sys.argv[9]),
    'post_restore_result': sys.argv[10], 'post_restore_exit': int(sys.argv[11]),
    'original_sha256': sys.argv[12], 'restored_sha256': sys.argv[13],
    'reason': sys.argv[14]
}
with open(sys.argv[15], 'w') as f: json.dump(t, f, indent=2)
" "$test_id" "$result" "$description" "$expected_check" "$observed_check" \
  "$baseline_result" "$baseline_exit" "$mutation_result" "$mutation_exit" \
  "$post_restore_result" "$post_restore_exit" "$original_sha256" \
  "$restored_sha256" "$reason" "$RESULTS_DIR/$test_id.json"
}

# Run one mutation test: backup -> mutate -> detect -> restore -> verify
run_one() {
    local test_id="$1" desc="$2" target="$3" expect="$4" mut_code="$5"
    local target_win
    target_win=$(win_path "$target")
    TOTAL_COUNT=$((TOTAL_COUNT + 1))
    echo "  [$TOTAL_COUNT] $test_id: $desc"

    # Baseline
    run_check "$expect"
    local baseline_exit=$_RUN_CHECK_EXIT
    local baseline_result
    baseline_result=$(get_result "$expect")
    if [ "$baseline_result" != "PASS" ] || [ "$baseline_exit" -ne 0 ]; then
        echo "    FAIL: baseline $expect=$baseline_result (exit $baseline_exit)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        write_result "$test_id" "FAIL" "$desc" "$expect" "BASELINE_FAIL" \
            "$baseline_result" "$baseline_exit" "NOT_RUN" "0" "NOT_RUN" "0" "" "" "baseline failed"
        return
    fi

    # Ensure backup dir exists
    mkdir -p "$BACKUP_DIR"

    # Hash + backup real file
    local orig_hash
    orig_hash=$(sha256sum "$target" | cut -d' ' -f1)
    cp "$target" "$BACKUP_DIR/pre-${test_id}.bak"

    # Mutate
    local mut_rc=0
    python3 -c "$mut_code" "$target_win" || mut_rc=$?
    if [ "$mut_rc" -ne 0 ]; then
        echo "    FAIL: mutation code failed (exit $mut_rc)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        cp "$BACKUP_DIR/pre-${test_id}.bak" "$target"
        write_result "$test_id" "FAIL" "$desc" "$expect" "MUTATION_ERROR" \
            "PASS" "0" "MUTATION_ERROR" "$mut_rc" "NOT_RUN" "0" "" "" "mutation code failed"
        return
    fi

    # Detect mutation
    run_check "$expect"
    local mutation_exit=$_RUN_CHECK_EXIT
    local mutation_result
    mutation_result=$(get_result "$expect")

    # Restore
    cp "$BACKUP_DIR/pre-${test_id}.bak" "$target"
    local rest_hash
    rest_hash=$(sha256sum "$target" | cut -d' ' -f1)

    # Re-baseline
    run_check "$expect"
    local post_restore_exit=$_RUN_CHECK_EXIT
    local post_restore_result
    post_restore_result=$(get_result "$expect")

    # Evaluate — EXACT EQUALITY REQUIREMENTS
    local pass=true reason=""
    if [ "$baseline_result" != "PASS" ]; then pass=false; reason="baseline=$baseline_result (must be PASS)"
    elif [ "$baseline_exit" -ne 0 ]; then pass=false; reason="baseline_exit=$baseline_exit (must be 0)"
    elif [ "$mutation_result" != "FAIL" ]; then pass=false; reason="mutation_result=$mutation_result (must be exactly FAIL)"
    elif [ "$mutation_exit" -eq 0 ]; then pass=false; reason="mutation_exit=0 (must be nonzero)"
    elif [ "$post_restore_result" != "PASS" ]; then pass=false; reason="post_restore_result=$post_restore_result (must be PASS)"
    elif [ "$post_restore_exit" -ne 0 ]; then pass=false; reason="post_restore_exit=$post_restore_exit (must be 0)"
    elif [ "$orig_hash" != "$rest_hash" ]; then pass=false; reason="hash mismatch orig=$orig_hash rest=$rest_hash"
    fi

    if [ "$pass" = true ]; then
        echo "    PASS"; PASS_COUNT=$((PASS_COUNT + 1))
        write_result "$test_id" "PASS" "$desc" "$expect" "$mutation_result" \
            "PASS" "0" "$mutation_result" "$mutation_exit" "PASS" "0" "$orig_hash" "$rest_hash" "Mutation detected, restored, baseline clean"
    else
        echo "    FAIL: $reason"; FAIL_COUNT=$((FAIL_COUNT + 1))
        write_result "$test_id" "FAIL" "$desc" "$expect" "$mutation_result" \
            "$baseline_result" "$baseline_exit" "$mutation_result" "$mutation_exit" \
            "$post_restore_result" "$post_restore_exit" "$orig_hash" "$rest_hash" "$reason"
    fi
}

echo "=============================================="
echo "  OCE B1-I1R3D Adversarial Test Suite"
echo "=============================================="
echo "Engine: $ENGINE"
echo "Evidence: $EVIDENCE_DIR"
echo ""

IDENTITY="$BASE_DIR/contracts/checkpoint-identity-data.json"
COMPOSE="$BASE_DIR/compose/compose.foundation.yml"
POLICY="$BASE_DIR/policy/network-access.yml"
SCHEMA="$BASE_DIR/contracts/worker-task-envelope.schema.json"
ANSIBLE_CFG="$BASE_DIR/ansible/ansible.cfg"

# === A: Source Identity ===
echo "--- Block A: Source Identity ---"
run_one "ID-01" "Wrong repo owner" "$IDENTITY" "SOURCE-IDENTITY" "import json,sys;p=sys.argv[1];d=json.load(open(p));d['repository']['owner']='wrong';json.dump(d,open(p,'w'),indent=2)"
run_one "ID-02" "Wrong repo name" "$IDENTITY" "SOURCE-IDENTITY" "import json,sys;p=sys.argv[1];d=json.load(open(p));d['repository']['name']='other';json.dump(d,open(p,'w'),indent=2)"
run_one "ID-03" "Wrong branch" "$IDENTITY" "SOURCE-IDENTITY" "import json,sys;p=sys.argv[1];d=json.load(open(p));d['authorized_branch']='main';json.dump(d,open(p,'w'),indent=2)"
run_one "ID-04" "Wrong base SHA" "$IDENTITY" "SOURCE-IDENTITY" "import json,sys;p=sys.argv[1];d=json.load(open(p));d['authoritative_base_sha']='0'*40;json.dump(d,open(p,'w'),indent=2)"
run_one "ID-05" "Wrong project root" "$IDENTITY" "SOURCE-IDENTITY" "import json,sys;p=sys.argv[1];d=json.load(open(p));d['expected_project_root']='wrong';json.dump(d,open(p,'w'),indent=2)"
run_one "ID-06" "Wrong origins" "$IDENTITY" "SOURCE-IDENTITY" "import json,sys;p=sys.argv[1];d=json.load(open(p));d['accepted_origins']=['https://evil.com/r.git'];json.dump(d,open(p,'w'),indent=2)"
run_one "ID-07" "Wrong expected commit" "$IDENTITY" "SOURCE-IDENTITY" "import json,sys;p=sys.argv[1];d=json.load(open(p));d['expected_implementation_commit_source']='f41e9c09';json.dump(d,open(p,'w'),indent=2)"
run_one "ID-08" "Wrong full_name" "$IDENTITY" "SOURCE-IDENTITY" "import json,sys;p=sys.argv[1];d=json.load(open(p));d['repository']['full_name']='wrong/repo';json.dump(d,open(p,'w'),indent=2)"
run_one "ID-09" "Wrong tree SHA" "$IDENTITY" "SOURCE-IDENTITY" "import json,sys;p=sys.argv[1];d=json.load(open(p));d['expected_tree_sha']='0'*40;json.dump(d,open(p,'w'),indent=2)"
echo ""

# === B: Compose / Image ===
echo "--- Block B: Compose / Image ---"
run_one "CM-01" "PostgreSQL tag-only" "$COMPOSE" "DIGEST-LOCK" "import sys,re;p=sys.argv[1];c=open(p).read();c=re.sub(r'image: postgres@sha256:[a-f0-9]+','image: postgres:16.4-alpine',c);open(p,'w').write(c)"
run_one "CM-02" "Redis tag-only" "$COMPOSE" "DIGEST-LOCK" "import sys,re;p=sys.argv[1];c=open(p).read();c=re.sub(r'image: redis@sha256:[a-f0-9]+','image: redis:7.4-alpine',c);open(p,'w').write(c)"
run_one "CM-03" "Remove healthcheck" "$COMPOSE" "HEALTH-CHECKS" "import sys;p=sys.argv[1];c=open(p).read();c=c.replace('healthcheck:','_hc_DISABLED:');open(p,'w').write(c)"
run_one "CM-04" "Add :latest PostgreSQL" "$COMPOSE" "NO-LATEST-TAGS" "import sys,re;p=sys.argv[1];c=open(p).read();c=re.sub(r'image: postgres@sha256:[a-f0-9]+','image: postgres:latest',c);open(p,'w').write(c)"
run_one "CM-05" "Remove security_opt" "$COMPOSE" "SECURITY-OPTS" "import sys;p=sys.argv[1];c=open(p).read();c=c.replace('no-new-privileges','_REMOVED');open(p,'w').write(c)"
echo ""

# === C: Policy ===
echo "--- Block C: Policy ---"
run_one "PL-01" "Remove DENY rules" "$POLICY" "WORKER-NO-DB" "import sys;p=sys.argv[1];lines=open(p).readlines();open(p,'w').writelines([l for l in lines if 'action: DENY' not in l])"
run_one "PL-02" "Remove worker-local->postgresql" "$POLICY" "WORKER-NO-DB" "import sys;p=sys.argv[1];lines=open(p).readlines();out=[];s=0
for i,l in enumerate(lines):
 if s>0:s-=1;continue
 if 'from: worker-local' in l and i+2<len(lines) and 'to: postgresql' in lines[i+1] and 'action: DENY' in lines[i+2]:s=2;continue
 out.append(l)
open(p,'w').writelines(out)"
run_one "PL-03" "Remove SSH denials" "$POLICY" "WORKER-NO-DB" "import sys;p=sys.argv[1];lines=open(p).readlines();out=[];s=0
for i,l in enumerate(lines):
 if s>0:s-=1;continue
 if i+1<len(lines) and 'action: DENY' in lines[i+1] and 'to: ssh' in l:s=1;continue
 out.append(l)
open(p,'w').writelines(out)"
run_one "PL-04" "Remove Docker denials" "$POLICY" "WORKER-NO-DB" "import sys;p=sys.argv[1];lines=open(p).readlines();out=[];s=0
for i,l in enumerate(lines):
 if s>0:s-=1;continue
 if i+1<len(lines) and 'action: DENY' in lines[i+1] and 'to: docker' in l:s=1;continue
 out.append(l)
open(p,'w').writelines(out)"
echo ""

# === D: Schema + Evidence ===
echo "--- Block D: Schema + Evidence ---"
run_one "ST-01" "Remove schema required" "$SCHEMA" "SCHEMA-FIXTURES" "import json,sys;p=sys.argv[1];d=json.load(open(p));d['required']=[];json.dump(d,open(p,'w'),indent=2)"
run_one "CF-01" "Disable host_key_checking" "$ANSIBLE_CFG" "HOST-KEY-CHECKING" "import sys;p=sys.argv[1];c=open(p).read();c=c.replace('host_key_checking = True','host_key_checking = False');open(p,'w').write(c)"
run_one "CF-02" "Add :latest Redis" "$COMPOSE" "NO-LATEST-TAGS" "import sys,re;p=sys.argv[1];c=open(p).read();c=re.sub(r'image: redis@sha256:[a-f0-9]+','image: redis:latest',c);open(p,'w').write(c)"

# EV-01: wrong repository in identity (inline, not using run_one for clarity)
TOTAL_COUNT=$((TOTAL_COUNT + 1))
echo "  [$TOTAL_COUNT] EV-01: Wrong repository rejected"
mkdir -p "$BACKUP_DIR"
run_check "SOURCE-IDENTITY"; be=$_RUN_CHECK_EXIT; br=$(get_result "SOURCE-IDENTITY")
cp "$IDENTITY" "$BACKUP_DIR/pre-EV-01.json"
orig_h=$(sha256sum "$IDENTITY"|cut -d' ' -f1)
python3 -c "import json,sys;p=sys.argv[1];d=json.load(open(p));d['repository']['owner']='bad';json.dump(d,open(p,'w'),indent=2)" "$(win_path "$IDENTITY")"
run_check "SOURCE-IDENTITY"; me=$_RUN_CHECK_EXIT; mr=$(get_result "SOURCE-IDENTITY")
cp "$BACKUP_DIR/pre-EV-01.json" "$IDENTITY"
rest_h=$(sha256sum "$IDENTITY"|cut -d' ' -f1)
run_check "SOURCE-IDENTITY"; pe=$_RUN_CHECK_EXIT; pr=$(get_result "SOURCE-IDENTITY")
if [ "$br" = "PASS" ] && [ "$be" -eq 0 ] && [ "$mr" = "FAIL" ] && [ "$me" -ne 0 ] && [ "$pr" = "PASS" ] && [ "$pe" -eq 0 ] && [ "$orig_h" = "$rest_h" ]; then
    echo "    PASS"; PASS_COUNT=$((PASS_COUNT + 1))
    write_result "EV-01" "PASS" "Wrong repository rejected" "SOURCE-IDENTITY" "FAIL" \
        "PASS" "0" "FAIL" "$me" "PASS" "0" "$orig_h" "$rest_h" "Correctly rejected"
else
    echo "    FAIL"; FAIL_COUNT=$((FAIL_COUNT + 1))
    write_result "EV-01" "FAIL" "Wrong repository rejected" "SOURCE-IDENTITY" "$mr" \
        "$br" "$be" "$mr" "$me" "$pr" "$pe" "$orig_h" "$rest_h" "Not rejected"
fi

# EV-02: evidence wrong commit
run_one "EV-02" "Evidence wrong commit" "$EVIDENCE_FILE" "EVIDENCE-CONSISTENCY" "import json,sys;p=sys.argv[1];d=json.load(open(p));d['tested_commit']='f41e9c09';json.dump(d,open(p,'w'),indent=2)"

# EV-03: evidence wrong tree
run_one "EV-03" "Evidence wrong tree" "$EVIDENCE_FILE" "EVIDENCE-CONSISTENCY" "import json,sys;p=sys.argv[1];d=json.load(open(p));d['tested_tree']='0'*40;json.dump(d,open(p,'w'),indent=2)"

# EV-04: evidence inconsistent totals
run_one "EV-04" "Evidence inconsistent totals" "$EVIDENCE_FILE" "EVIDENCE-CONSISTENCY" "import json,sys;p=sys.argv[1];d=json.load(open(p));d['totals']['total']=999;json.dump(d,open(p,'w'),indent=2)"
echo ""

# === E: Meta-Tests (Fake Result Proofs) ===
echo "--- Block E: Meta-Tests ---"

# Helper: write a fake adversarial-results.json and check FAIL-CLOSED rejects it
run_meta() {
    local meta_id="$1" desc="$2" fake_json="$3"
    TOTAL_COUNT=$((TOTAL_COUNT + 1))
    echo "  [$TOTAL_COUNT] $meta_id: $desc"
    mkdir -p "$BACKUP_DIR"
    echo "$fake_json" > "$BACKUP_DIR/$meta_id-fake.json"
    cp "$BACKUP_DIR/$meta_id-fake.json" "$EVIDENCE_DIR/adversarial-results.json"
    local rc=0
    python3 "$ENGINE_WIN" --only "FAIL-CLOSED" --evidence-dir "$EVIDENCE_DIR_WIN" >/dev/null 2>&1 || rc=$?
    local fr
    fr=$(get_result "FAIL-CLOSED")
    rm -f "$EVIDENCE_DIR/adversarial-results.json"
    if [ "$fr" = "FAIL" ] || [ "$fr" = "BLOCKED" ]; then
        echo "    PASS (FAIL-CLOSED=$fr)"; PASS_COUNT=$((PASS_COUNT + 1))
        write_result "$meta_id" "PASS" "$desc" "FAIL-CLOSED" "$fr" \
            "N/A" "0" "N/A" "0" "N/A" "0" "N/A" "N/A" "Invalid fixture correctly rejected"
    else
        echo "    FAIL: FAIL-CLOSED=$fr"; FAIL_COUNT=$((FAIL_COUNT + 1))
        write_result "$meta_id" "FAIL" "$desc" "FAIL-CLOSED" "$fr" \
            "N/A" "0" "N/A" "0" "N/A" "0" "N/A" "N/A" "Invalid fixture was not rejected"
    fi
}

mk_fake_neg() { python3 -c "import json,sys;print(json.dumps({'test_id':'X','result':'PASS','mutation_result':sys.argv[1],'mutation_exit':0,'baseline_result':'PASS','baseline_exit':0,'post_restore_result':'PASS','post_restore_exit':0,'original_sha256':'a','restored_sha256':'a','expected_check':'X','observed_check':'X','reason':'fake'}))" "$1"; }

# FAKE-01: BLOCKED mutation_result
FAKE_NEG=$(mk_fake_neg "BLOCKED")
FAKE_ADV=$(python3 -c "import json;print(json.dumps({'schema_version':'3.4.0','suite':'B1-I1R3D-adversarial','totals':{'total':1,'PASS':1,'FAIL':0},'suite_result':'PASS','negative_tests':[$FAKE_NEG],'meta_tests':[]}))")
run_meta "FAKE-01" "BLOCKED mutation_result rejected" "$FAKE_ADV"

# FAKE-02: SKIPPED mutation_result
FAKE_NEG=$(mk_fake_neg "SKIPPED")
FAKE_ADV=$(python3 -c "import json;print(json.dumps({'schema_version':'3.4.0','suite':'B1-I1R3D-adversarial','totals':{'total':1,'PASS':1,'FAIL':0},'suite_result':'PASS','negative_tests':[$FAKE_NEG],'meta_tests':[]}))")
run_meta "FAKE-02" "SKIPPED mutation_result rejected" "$FAKE_ADV"

# FAKE-03: ERROR mutation_result
FAKE_NEG=$(mk_fake_neg "ERROR")
FAKE_ADV=$(python3 -c "import json;print(json.dumps({'schema_version':'3.4.0','suite':'B1-I1R3D-adversarial','totals':{'total':1,'PASS':1,'FAIL':0},'suite_result':'PASS','negative_tests':[$FAKE_NEG],'meta_tests':[]}))")
run_meta "FAKE-03" "ERROR mutation_result rejected" "$FAKE_ADV"

# FAKE-04: NOT_FOUND mutation_result
FAKE_NEG=$(mk_fake_neg "NOT_FOUND")
FAKE_ADV=$(python3 -c "import json;print(json.dumps({'schema_version':'3.4.0','suite':'B1-I1R3D-adversarial','totals':{'total':1,'PASS':1,'FAIL':0},'suite_result':'PASS','negative_tests':[$FAKE_NEG],'meta_tests':[]}))")
run_meta "FAKE-04" "NOT_FOUND mutation_result rejected" "$FAKE_ADV"

# FAKE-05: PASS mutation_result
FAKE_NEG=$(mk_fake_neg "PASS")
FAKE_ADV=$(python3 -c "import json;print(json.dumps({'schema_version':'3.4.0','suite':'B1-I1R3D-adversarial','totals':{'total':1,'PASS':1,'FAIL':0},'suite_result':'PASS','negative_tests':[$FAKE_NEG],'meta_tests':[]}))")
run_meta "FAKE-05" "PASS mutation_result rejected" "$FAKE_ADV"

# FAKE-06: mutation_exit=0 with mutation_result=FAIL
FAKE_ADV=$(python3 -c "import json;print(json.dumps({'schema_version':'3.4.0','suite':'B1-I1R3D-adversarial','totals':{'total':1,'PASS':1,'FAIL':0},'suite_result':'PASS','negative_tests':[{'test_id':'X','result':'PASS','mutation_result':'FAIL','mutation_exit':0,'baseline_result':'PASS','baseline_exit':0,'post_restore_result':'PASS','post_restore_exit':0,'original_sha256':'a','restored_sha256':'a','expected_check':'X','observed_check':'X','reason':'fake'}],'meta_tests':[]}))")
run_meta "FAKE-06" "mutation_exit=0 rejected" "$FAKE_ADV"
# FAKE-07: empty mutation_result
FAKE_NEG=$(mk_fake_neg "")
FAKE_ADV=$(python3 -c "import json;print(json.dumps({'schema_version':'3.4.0','suite':'B1-I1R3D-adversarial','totals':{'total':1,'PASS':1,'FAIL':0},'suite_result':'PASS','negative_tests':[$FAKE_NEG],'meta_tests':[]}))")
run_meta "FAKE-07" "Empty mutation_result rejected" "$FAKE_ADV"

# FAKE-08: empty test lists
FAKE_ADV=$(python3 -c "import json;print(json.dumps({'schema_version':'3.4.0','suite':'B1-I1R3D-adversarial','totals':{'total':0,'PASS':0,'FAIL':0},'suite_result':'PASS','negative_tests':[],'meta_tests':[]}))")
run_meta "FAKE-08" "Empty test lists rejected" "$FAKE_ADV"
# FAKE-09: wrong schema version
FAKE_ADV=$(python3 -c "import json;print(json.dumps({'schema_version':'1.0.0','suite':'B1-I1R3D-adversarial','totals':{'total':1,'PASS':1,'FAIL':0},'suite_result':'PASS','negative_tests':[{'test_id':'X','result':'PASS','mutation_result':'FAIL','mutation_exit':1,'baseline_result':'PASS','baseline_exit':0,'post_restore_result':'PASS','post_restore_exit':0,'original_sha256':'a','restored_sha256':'a','expected_check':'X','observed_check':'X','reason':'fake'}],'meta_tests':[]}))")
run_meta "FAKE-09" "Wrong schema version rejected" "$FAKE_ADV"
# FAKE-10: suite_result=FAIL
FAKE_ADV=$(python3 -c "import json;print(json.dumps({'schema_version':'3.4.0','suite':'B1-I1R3D-adversarial','totals':{'total':1,'PASS':1,'FAIL':0},'suite_result':'FAIL','negative_tests':[{'test_id':'X','result':'PASS','mutation_result':'FAIL','mutation_exit':1,'baseline_result':'PASS','baseline_exit':0,'post_restore_result':'PASS','post_restore_exit':0,'original_sha256':'a','restored_sha256':'a','expected_check':'X','observed_check':'X','reason':'fake'}],'meta_tests':[]}))")
run_meta "FAKE-10" "suite_result=FAIL rejected" "$FAKE_ADV"
echo ""

IDENTITY="$BASE_DIR/contracts/checkpoint-identity-data.json"
COMPOSE="$BASE_DIR/compose/compose.foundation.yml"
POLICY="$BASE_DIR/policy/network-access.yml"
SCHEMA="$BASE_DIR/contracts/worker-task-envelope.schema.json"
ANSIBLE_CFG="$BASE_DIR/ansible/ansible.cfg"

# === A: Source Identity ===
echo "--- Block F: CLI Negative Tests ---"
TOTAL_COUNT=$((TOTAL_COUNT + 1))
echo "  [$TOTAL_COUNT] CLI-01: Missing authoritative inputs"
rc=0; python3 "$ENGINE_WIN" --authoritative >/dev/null 2>&1 || rc=$?
if [ "$rc" -ne 0 ]; then
    echo "    PASS"; PASS_COUNT=$((PASS_COUNT + 1))
    write_result "CLI-01" "PASS" "Missing authoritative inputs" "SOURCE-IDENTITY" "BLOCKED" \
        "N/A" "0" "BLOCKED" "$rc" "N/A" "0" "N/A" "N/A" "Rejected"
else
    echo "    FAIL"; FAIL_COUNT=$((FAIL_COUNT + 1))
    write_result "CLI-01" "FAIL" "Missing authoritative inputs" "SOURCE-IDENTITY" "PASS" \
        "N/A" "0" "PASS" "0" "N/A" "0" "N/A" "N/A" "Accepted"
fi

CC=$(git -C "$PROJ_ROOT" rev-parse HEAD); CT=$(git -C "$PROJ_ROOT" rev-parse "HEAD^{tree}"); CB=$(git -C "$PROJ_ROOT" branch --show-current)

# CLI-02: Wrong target commit
TOTAL_COUNT=$((TOTAL_COUNT + 1))
echo "  [$TOTAL_COUNT] CLI-02: Wrong target commit"
rc=0; python3 "$ENGINE_WIN" --authoritative --target-commit 0000000000000000000000000000000000000000 --target-tree "$CT" --target-branch "$CB" >/dev/null 2>&1 || rc=$?
if [ "$rc" -ne 0 ]; then
    echo "    PASS"; PASS_COUNT=$((PASS_COUNT + 1))
    write_result "CLI-02" "PASS" "Wrong target commit" "SOURCE-IDENTITY" "FAIL" \
        "N/A" "0" "FAIL" "$rc" "N/A" "0" "N/A" "N/A" "Rejected"
else
    echo "    FAIL"; FAIL_COUNT=$((FAIL_COUNT + 1))
    write_result "CLI-02" "FAIL" "Wrong target commit" "SOURCE-IDENTITY" "PASS" \
        "N/A" "0" "PASS" "0" "N/A" "0" "N/A" "N/A" "Accepted"
fi

# CLI-03: Wrong branch
TOTAL_COUNT=$((TOTAL_COUNT + 1))
echo "  [$TOTAL_COUNT] CLI-03: Wrong branch"
rc=0; python3 "$ENGINE_WIN" --authoritative --target-commit "$CC" --target-tree "$CT" --target-branch wrong-branch >/dev/null 2>&1 || rc=$?
if [ "$rc" -ne 0 ]; then
    echo "    PASS"; PASS_COUNT=$((PASS_COUNT + 1))
    write_result "CLI-03" "PASS" "Wrong branch" "SOURCE-IDENTITY" "FAIL" \
        "N/A" "0" "FAIL" "$rc" "N/A" "0" "N/A" "N/A" "Rejected"
else
    echo "    FAIL"; FAIL_COUNT=$((FAIL_COUNT + 1))
    write_result "CLI-03" "FAIL" "Wrong branch" "SOURCE-IDENTITY" "PASS" \
        "N/A" "0" "PASS" "0" "N/A" "0" "N/A" "N/A" "Accepted"
fi

# CLI-04: Wrong repository
TOTAL_COUNT=$((TOTAL_COUNT + 1))
echo "  [$TOTAL_COUNT] CLI-04: Wrong repository"
GR_ORIG="${GITHUB_REPOSITORY:-}"; export GITHUB_REPOSITORY="wrong/repo"
rc=0; python3 "$ENGINE_WIN" --authoritative --target-commit "$CC" --target-tree "$CT" --target-branch "$CB" >/dev/null 2>&1 || rc=$?
if [ -n "$GR_ORIG" ]; then export GITHUB_REPOSITORY="$GR_ORIG"; else unset GITHUB_REPOSITORY; fi
if [ "$rc" -ne 0 ]; then
    echo "    PASS"; PASS_COUNT=$((PASS_COUNT + 1))
    write_result "CLI-04" "PASS" "Wrong repository" "SOURCE-IDENTITY" "FAIL" \
        "N/A" "0" "FAIL" "$rc" "N/A" "0" "N/A" "N/A" "Rejected"
else
    echo "    FAIL"; FAIL_COUNT=$((FAIL_COUNT + 1))
    write_result "CLI-04" "FAIL" "Wrong repository" "SOURCE-IDENTITY" "PASS" \
        "N/A" "0" "PASS" "0" "N/A" "0" "N/A" "N/A" "Accepted"
fi

# CLI-05: FAIL with exit 0
TOTAL_COUNT=$((TOTAL_COUNT + 1))
echo "  [$TOTAL_COUNT] CLI-05: FAIL paired with nonzero exit"
mkdir -p "$BACKUP_DIR"
cp "$IDENTITY" "$BACKUP_DIR/pre-CLI-05.json"
python3 -c "import json,sys;p=sys.argv[1];d=json.load(open(p));d['repository']['owner']='bad';json.dump(d,open(p,'w'),indent=2)" "$(win_path "$IDENTITY")"
rc=0; python3 "$ENGINE_WIN" --only "SOURCE-IDENTITY" --evidence-dir "$EVIDENCE_DIR_WIN" >/dev/null 2>&1 || rc=$?
cp "$BACKUP_DIR/pre-CLI-05.json" "$IDENTITY"
res=$(get_result "SOURCE-IDENTITY")
if [ "$res" = "FAIL" ] && [ "$rc" -ne 0 ]; then
    echo "    PASS"; PASS_COUNT=$((PASS_COUNT + 1))
    write_result "CLI-05" "PASS" "FAIL+nonzero exit" "SOURCE-IDENTITY" "$res" \
        "N/A" "0" "$res" "$rc" "N/A" "0" "N/A" "N/A" "Correctly paired"
else
    echo "    FAIL: $res/$rc"; FAIL_COUNT=$((FAIL_COUNT + 1))
    write_result "CLI-05" "FAIL" "FAIL+nonzero exit" "SOURCE-IDENTITY" "$res" \
        "N/A" "0" "$res" "$rc" "N/A" "0" "N/A" "N/A" "Mismatch"
fi
echo ""

# === G: State Tests ===
echo "--- Block G: State Tests ---"
echo "dirty" > "$PROJ_ROOT/.oce-dirty-test"
TOTAL_COUNT=$((TOTAL_COUNT + 1))
echo "  [$TOTAL_COUNT] ST-02: Dirty worktree rejected"
rc=0; python3 "$ENGINE_WIN" --authoritative --target-commit "$CC" --target-tree "$CT" --target-branch "$CB" >/dev/null 2>&1 || rc=$?
rm -f "$PROJ_ROOT/.oce-dirty-test"
if [ "$rc" -ne 0 ]; then
    echo "    PASS"; PASS_COUNT=$((PASS_COUNT + 1))
    write_result "ST-02" "PASS" "Dirty worktree rejected" "SOURCE-IDENTITY" "FAIL" \
        "N/A" "0" "FAIL" "$rc" "N/A" "0" "N/A" "N/A" "Rejected"
else
    echo "    FAIL"; FAIL_COUNT=$((FAIL_COUNT + 1))
    write_result "ST-02" "FAIL" "Dirty worktree rejected" "SOURCE-IDENTITY" "PASS" \
        "N/A" "0" "PASS" "0" "N/A" "0" "N/A" "N/A" "Accepted"
fi

TOTAL_COUNT=$((TOTAL_COUNT + 1))
echo "  [$TOTAL_COUNT] ST-03: Wrong tree rejected"
rc=0; python3 "$ENGINE_WIN" --authoritative --target-commit "$CC" --target-tree "0000000000000000000000000000000000000000000000000000000000000000" --target-branch "$CB" >/dev/null 2>&1 || rc=$?
if [ "$rc" -ne 0 ]; then
    echo "    PASS"; PASS_COUNT=$((PASS_COUNT + 1))
    write_result "ST-03" "PASS" "Wrong tree rejected" "SOURCE-IDENTITY" "FAIL" \
        "N/A" "0" "FAIL" "$rc" "N/A" "0" "N/A" "N/A" "Rejected"
else
    echo "    FAIL"; FAIL_COUNT=$((FAIL_COUNT + 1))
    write_result "ST-03" "FAIL" "Wrong tree rejected" "SOURCE-IDENTITY" "PASS" \
        "N/A" "0" "PASS" "0" "N/A" "0" "N/A" "N/A" "Accepted"
fi

# === SUMMARY ===
echo ""
echo "=============================================="
echo "  Adversarial Test Summary"
echo "=============================================="
echo "  Total:   $TOTAL_COUNT"
echo "  PASS:    $PASS_COUNT"
echo "  FAIL:    $FAIL_COUNT"
echo "=============================================="

SUITE_RESULT="PASS"
[ "$FAIL_COUNT" -gt 0 ] && SUITE_RESULT="FAIL"
[ "$TOTAL_COUNT" -lt 30 ] && SUITE_RESULT="FAIL"
echo "  Suite:   $SUITE_RESULT"

# Aggregate all test result files into adversarial-results.json
python3 -c "
import json, sys, os, glob
from datetime import datetime, timezone

results_dir = sys.argv[1]
negative_tests = []
meta_tests = []
# Meta test IDs
meta_ids = {'FAKE-01','FAKE-02','FAKE-03','FAKE-04','FAKE-05','FAKE-06','FAKE-07','FAKE-08','FAKE-09','FAKE-10'}

for f in sorted(glob.glob(os.path.join(results_dir, '*.json'))):
    with open(f) as fp:
        t = json.load(fp)
    tid = t.get('test_id', '')
    if tid in meta_ids:
        meta_tests.append(t)
    else:
        negative_tests.append(t)

np = sum(1 for t in negative_tests if t.get('result') == 'PASS')
nf = sum(1 for t in negative_tests if t.get('result') == 'FAIL')
mp = sum(1 for t in meta_tests if t.get('result') == 'PASS')
mf = sum(1 for t in meta_tests if t.get('result') == 'FAIL')

r = {
    'schema_version': '3.4.0',
    'suite': 'B1-I1R3D-adversarial',
    'validator_version': '3.4.0',
    'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    'totals': {
        'total': len(negative_tests) + len(meta_tests),
        'PASS': np + mp, 'FAIL': nf + mf,
        'negative_total': len(negative_tests), 'negative_pass': np, 'negative_fail': nf,
        'meta_total': len(meta_tests), 'meta_pass': mp, 'meta_fail': mf
    },
    'suite_result': sys.argv[2],
    'negative_tests': negative_tests,
    'meta_tests': meta_tests
}

out_path = sys.argv[3]
with open(out_path, 'w') as fp:
    json.dump(r, fp, indent=2)
print(f'Written {len(negative_tests)} negative + {len(meta_tests)} meta tests to {out_path}')
" "$RESULTS_DIR" "$SUITE_RESULT" "$EVIDENCE_DIR/adversarial-results.json"

[ "$SUITE_RESULT" = "PASS" ] && exit 0 || exit 1
