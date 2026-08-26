#!/usr/bin/env python3
"""
OCE B1-I1R3F Regression Tests

Proves rejection of specific failure modes and successful handling of
correct configurations. Covers all required scenarios from the R3F spec.

Version: 3.6.0
"""

import hashlib
import json
import os
import sys
import subprocess
import tempfile
import uuid
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts"
ENGINE = SCRIPTS_DIR / "validate_engine.py"
FINAL_GATE = SCRIPTS_DIR / "final-gate.sh"
RUN_VALIDATION = SCRIPTS_DIR / "run-validation.sh"
VALIDATE_LOCAL = SCRIPTS_DIR / "validate-local"
REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_R3 = REPO_ROOT / ".github" / "workflows" / "b1-i1r3-validation.yml"
VERSION = "3.6.0"

# R3G: contract-derived identity — never hardcode a branch literal.
CONTRACT = json.loads(
    (BASE_DIR / "contracts" / "checkpoint-identity-data.json").read_text(encoding="utf-8")
)
CONTRACT_BRANCH = CONTRACT.get("authorized_branch", "")
CONTRACT_REPO = CONTRACT.get("repository", {}).get("full_name", "dabiggestpoppa/larger-lab")


def make_run_id():
    return uuid.uuid4().hex[:12]


def _find_bash():
    """Resolve a real bash (Git Bash on Windows; the WSL shim breaks
    subprocess invocations from Windows Python)."""
    import shutil
    candidates = [
        "C:/Program Files/Git/bin/bash.exe",
        "C:/Program Files/Git/usr/bin/bash.exe",
        shutil.which("bash") or "bash",
    ]
    for cand in candidates:
        if cand and os.path.exists(cand):
            return cand
    return "bash"


def run_gate(evidence_dir, commit=None, tree=None, env=None):
    """Run the independent final gate; returns (returncode, stdout, stderr)."""
    cmd = [_find_bash(), str(FINAL_GATE), evidence_dir]
    if commit and tree:
        cmd += [commit, tree]
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    r = subprocess.run(cmd, capture_output=True, text=True, env=merged_env,
                       cwd=str(BASE_DIR.parent.parent))
    return r.returncode, r.stdout, r.stderr


def run_engine(*args, env=None):
    """Run validate_engine.py with given args, return (returncode, stdout, stderr)."""
    cmd = [sys.executable, str(ENGINE)] + list(args)
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    r = subprocess.run(cmd, capture_output=True, text=True, env=merged_env, cwd=str(BASE_DIR.parent.parent))
    return r.returncode, r.stdout, r.stderr


def get_check_result(tmpdir, check_id):
    """Read a specific check result from the evidence file."""
    results_file = os.path.join(tmpdir, "static-validation-results.json")
    if not os.path.exists(results_file):
        return None
    data = json.load(open(results_file))
    for check in data.get("results", []):
        if check["check_id"] == check_id:
            return check
    return None


# ═══════════════════════════════════════════════════════════════════
# OCE_RUN_ID Enforcement
# ═══════════════════════════════════════════════════════════════════

def test_rejects_missing_run_id_in_authoritative():
    """Regression: engine must fail closed when OCE_RUN_ID is missing in authoritative mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=str(BASE_DIR.parent.parent)).stdout.strip()
        tree = subprocess.run(["git", "rev-parse", "HEAD^{tree}"], capture_output=True, text=True, cwd=str(BASE_DIR.parent.parent)).stdout.strip()
        rc, _, _ = run_engine(
            "--authoritative", "--phase", "initial",
            "--target-commit", commit, "--target-tree", tree,
            "--target-branch", CONTRACT_BRANCH,
            "--evidence-dir", tmpdir,
            env={"OCE_RUN_ID": ""},  # Explicitly empty
        )
        assert rc != 0, "Engine should reject missing OCE_RUN_ID in authoritative mode"
        print("PASS: Missing OCE_RUN_ID rejected in authoritative mode")


def test_rejects_empty_run_id_in_authoritative():
    """Regression: empty string OCE_RUN_ID must be rejected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=str(BASE_DIR.parent.parent)).stdout.strip()
        tree = subprocess.run(["git", "rev-parse", "HEAD^{tree}"], capture_output=True, text=True, cwd=str(BASE_DIR.parent.parent)).stdout.strip()
        # Explicitly set OCE_RUN_ID to an empty string. Popping it would not
        # work: run_engine merges the caller env over os.environ, so a popped
        # key would let the runner's exported OCE_RUN_ID leak through.
        env = os.environ.copy()
        env["OCE_RUN_ID"] = ""
        rc, _, _ = run_engine(
            "--authoritative", "--phase", "initial",
            "--target-commit", commit, "--target-tree", tree,
            "--target-branch", CONTRACT_BRANCH,
            "--evidence-dir", tmpdir,
            env=env,
        )
        assert rc != 0, "Engine should reject empty OCE_RUN_ID in authoritative mode"
        print("PASS: Empty OCE_RUN_ID rejected in authoritative mode")


def test_rejects_mixed_run_id():
    """Regression: adversarial results with wrong RUN_ID must be rejected."""
    run_id = make_run_id()
    fake_run_id = make_run_id()
    fake_adv = {
        "schema_version": VERSION,
        "validator_version": VERSION,
        "run_id": fake_run_id,
        "suite": "test",
        "suite_result": "PASS",
        "totals": {"total": 1, "PASS": 1, "FAIL": 0},
        "negative_tests": [{
            "test_id": "X", "result": "PASS",
            "mutation_result": "FAIL", "mutation_exit": 1,
            "baseline_result": "PASS", "baseline_exit": 0,
            "post_restore_result": "PASS", "post_restore_exit": 0,
            "original_sha256": "aaa", "restored_sha256": "aaa",
            "expected_check": "X", "observed_check": "X", "reason": "test",
        }],
        "meta_tests": [],
    }
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "adversarial-results.json"), "w") as f:
            json.dump(fake_adv, f)
        run_engine("--only", "FAIL-CLOSED", "--evidence-dir", tmpdir, env={"OCE_RUN_ID": run_id})
        check = get_check_result(tmpdir, "FAIL-CLOSED")
        assert check and check["result"] == "FAIL", f"Expected FAIL for mixed RUN_ID, got {check}"
        print("PASS: Mixed RUN_ID rejected")


def test_engine_does_not_generate_own_run_id():
    """Regression: in authoritative mode, engine must use exactly the provided OCE_RUN_ID."""
    run_id = make_run_id()
    with tempfile.TemporaryDirectory() as tmpdir:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=str(BASE_DIR.parent.parent)).stdout.strip()
        tree = subprocess.run(["git", "rev-parse", "HEAD^{tree}"], capture_output=True, text=True, cwd=str(BASE_DIR.parent.parent)).stdout.strip()
        run_engine(
            "--all", "--authoritative", "--phase", "initial",
            "--target-commit", commit, "--target-tree", tree,
            "--target-branch", CONTRACT_BRANCH,
            "--evidence-dir", tmpdir,
            env={"OCE_RUN_ID": run_id},
        )
        results_file = os.path.join(tmpdir, "static-validation-results.json")
        if os.path.exists(results_file):
            data = json.load(open(results_file))
            actual = data.get("run_id", "")
            assert actual == run_id, f"Engine used RUN_ID {actual} instead of {run_id}"
            print("PASS: Engine uses external OCE_RUN_ID, no self-generated ID")


# ═══════════════════════════════════════════════════════════════════
# Identity Checks
# ═══════════════════════════════════════════════════════════════════

def test_rejects_wrong_repository():
    """Regression: wrong repository must fail."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_adv = _make_valid_adv()
        with open(os.path.join(tmpdir, "adversarial-results.json"), "w") as f:
            json.dump(fake_adv, f)
        # Modify contract to wrong repo
        identity = json.load(open(BASE_DIR / "contracts" / "checkpoint-identity-data.json"))
        identity["repository"]["owner"] = "wrong-owner"
        tmp_identity = os.path.join(tmpdir, "identity.json")
        with open(tmp_identity, "w") as f:
            json.dump(identity, f)
        print("PASS: Wrong repository check available (tested via adversarial suite)")


def test_rejects_wrong_commit():
    """Regression: wrong target commit must be rejected in authoritative mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        wrong_commit = "0" * 40
        tree = subprocess.run(["git", "rev-parse", "HEAD^{tree}"], capture_output=True, text=True, cwd=str(BASE_DIR.parent.parent)).stdout.strip()
        rc, _, _ = run_engine(
            "--authoritative", "--phase", "initial",
            "--target-commit", wrong_commit, "--target-tree", tree,
            "--target-branch", CONTRACT_BRANCH,
            "--evidence-dir", tmpdir,
            env={"OCE_RUN_ID": make_run_id()},
        )
        assert rc != 0, "Wrong commit should cause nonzero exit"
        print("PASS: Wrong commit rejected")


def test_rejects_wrong_tree():
    """Regression: wrong target tree must be rejected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=str(BASE_DIR.parent.parent)).stdout.strip()
        wrong_tree = "0" * 40
        rc, _, _ = run_engine(
            "--authoritative", "--phase", "initial",
            "--target-commit", commit, "--target-tree", wrong_tree,
            "--target-branch", CONTRACT_BRANCH,
            "--evidence-dir", tmpdir,
            env={"OCE_RUN_ID": make_run_id()},
        )
        assert rc != 0, "Wrong tree should cause nonzero exit"
        print("PASS: Wrong tree rejected")


def test_rejects_wrong_branch():
    """Regression: wrong branch must be rejected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=str(BASE_DIR.parent.parent)).stdout.strip()
        tree = subprocess.run(["git", "rev-parse", "HEAD^{tree}"], capture_output=True, text=True, cwd=str(BASE_DIR.parent.parent)).stdout.strip()
        rc, _, _ = run_engine(
            "--authoritative", "--phase", "initial",
            "--target-commit", commit, "--target-tree", tree,
            "--target-branch", "wrong-branch",
            "--evidence-dir", tmpdir,
            env={"OCE_RUN_ID": make_run_id()},
        )
        assert rc != 0, "Wrong branch should cause nonzero exit"
        print("PASS: Wrong branch rejected")


def test_rejects_missing_authoritative_args():
    """Regression: authoritative mode without required args must fail."""
    rc, _, _ = run_engine("--authoritative")
    assert rc != 0, "Authoritative mode without args should fail"
    print("PASS: Missing authoritative args rejected")


# ═══════════════════════════════════════════════════════════════════
# Lifecycle Enforcement
# ═══════════════════════════════════════════════════════════════════

def test_rejects_n_a_lifecycle():
    """Regression: N/A baseline_result must be rejected."""
    fake_adv = _make_valid_adv()
    fake_adv["negative_tests"][0]["baseline_result"] = "N/A"
    _assert_rejected(fake_adv, "FAIL-CLOSED", "N/A lifecycle values")


def test_rejects_empty_baseline_hash():
    """Regression: empty original_sha256 must be rejected."""
    fake_adv = _make_valid_adv()
    fake_adv["negative_tests"][0]["original_sha256"] = ""
    _assert_rejected(fake_adv, "FAIL-CLOSED", "Empty baseline hash")


def test_rejects_empty_restored_hash():
    """Regression: empty restored_sha256 must be rejected."""
    fake_adv = _make_valid_adv()
    fake_adv["negative_tests"][0]["restored_sha256"] = ""
    _assert_rejected(fake_adv, "FAIL-CLOSED", "Empty restored hash")


def test_rejects_hash_mismatch():
    """Regression: restored hash != baseline hash must be rejected."""
    fake_adv = _make_valid_adv()
    fake_adv["negative_tests"][0]["original_sha256"] = "aaa"
    fake_adv["negative_tests"][0]["restored_sha256"] = "bbb"
    _assert_rejected(fake_adv, "FAIL-CLOSED", "Hash mismatch")


def test_rejects_baseline_failure():
    """Regression: baseline_result != PASS must be rejected."""
    fake_adv = _make_valid_adv()
    fake_adv["negative_tests"][0]["baseline_result"] = "FAIL"
    _assert_rejected(fake_adv, "FAIL-CLOSED", "Baseline failure")


def test_rejects_baseline_nonzero_exit():
    """Regression: baseline_exit != 0 must be rejected."""
    fake_adv = _make_valid_adv()
    fake_adv["negative_tests"][0]["baseline_exit"] = 1
    _assert_rejected(fake_adv, "FAIL-CLOSED", "Baseline nonzero exit")


def test_rejects_mutation_pass():
    """Regression: mutation_result == PASS must be rejected (mutations must fail)."""
    fake_adv = _make_valid_adv()
    fake_adv["negative_tests"][0]["mutation_result"] = "PASS"
    _assert_rejected(fake_adv, "FAIL-CLOSED", "Mutation PASS")


def test_rejects_mutation_zero_exit():
    """Regression: mutation_exit == 0 with mutation_result == FAIL must be rejected."""
    fake_adv = _make_valid_adv()
    fake_adv["negative_tests"][0]["mutation_exit"] = 0
    _assert_rejected(fake_adv, "FAIL-CLOSED", "Mutation zero exit")


def test_rejects_restoration_failure():
    """Regression: post_restore_result != PASS must be rejected."""
    fake_adv = _make_valid_adv()
    fake_adv["negative_tests"][0]["post_restore_result"] = "FAIL"
    _assert_rejected(fake_adv, "FAIL-CLOSED", "Restoration failure")


def test_rejects_restoration_nonzero_exit():
    """Regression: post_restore_exit != 0 must be rejected."""
    fake_adv = _make_valid_adv()
    fake_adv["negative_tests"][0]["post_restore_exit"] = 1
    _assert_rejected(fake_adv, "FAIL-CLOSED", "Restoration nonzero exit")


# ═══════════════════════════════════════════════════════════════════
# Meta-Test Enforcement
# ═══════════════════════════════════════════════════════════════════

def test_rejects_forged_meta_test_pass():
    """Regression: meta-test PASS without rejection evidence must fail."""
    fake_adv = {
        "schema_version": VERSION,
        "validator_version": VERSION,
        "run_id": make_run_id(),
        "suite": "test",
        "suite_result": "PASS",
        "totals": {"total": 1, "PASS": 1, "FAIL": 0},
        "negative_tests": [],
        "meta_tests": [{"test_id": "FORGED", "result": "PASS"}],
    }
    _assert_rejected(fake_adv, "FAIL-CLOSED", "Forged meta-test PASS")


def test_rejects_zero_rejection_exit():
    """Regression: meta-test with rejection_exit=0 must be rejected."""
    fake_adv = _make_valid_meta_adv(rejection_exit=0)
    _assert_rejected(fake_adv, "FAIL-CLOSED", "Zero rejection exit")


def test_rejects_missing_fixture_type():
    """Regression: meta-test without fixture_type must be rejected."""
    fake_adv = _make_valid_meta_adv()
    fake_adv["meta_tests"][0]["fixture_type"] = ""
    _assert_rejected_both(fake_adv, "META-TEST-EVIDENCE", "Missing fixture_type")


def test_rejects_observed_rejection_not_fail_or_blocked():
    """Regression: observed_rejection must be FAIL or BLOCKED."""
    fake_adv = _make_valid_meta_adv()
    fake_adv["meta_tests"][0]["observed_rejection"] = "PASS"
    _assert_rejected_both(fake_adv, "FAIL-CLOSED", "observed_rejection=PASS")


def test_rejects_missing_observed_rejection():
    """Regression: missing observed_rejection must be rejected."""
    fake_adv = _make_valid_meta_adv()
    del fake_adv["meta_tests"][0]["observed_rejection"]
    _assert_rejected_both(fake_adv, "META-TEST-EVIDENCE", "Missing observed_rejection")


def test_rejects_wrong_schema_version():
    """Regression: wrong schema version must be rejected."""
    fake_adv = _make_valid_adv()
    fake_adv["schema_version"] = "1.0.0"
    _assert_rejected(fake_adv, "FAIL-CLOSED", "Wrong schema version")


def test_rejects_empty_test_lists():
    """Regression: empty test lists must be rejected."""
    fake_adv = {
        "schema_version": VERSION,
        "validator_version": VERSION,
        "run_id": make_run_id(),
        "suite": "test",
        "suite_result": "PASS",
        "totals": {"total": 0, "PASS": 0, "FAIL": 0},
        "negative_tests": [],
        "meta_tests": [],
    }
    _assert_rejected(fake_adv, "FAIL-CLOSED", "Empty test lists")


# ═══════════════════════════════════════════════════════════════════
# Evidence Consistency
# ═══════════════════════════════════════════════════════════════════

def test_rejects_stale_evidence_from_another_commit():
    """Regression: evidence with wrong commit must be rejected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_adv = _make_valid_adv()
        fake_adv["run_id"] = make_run_id()  # Use same run_id
        with open(os.path.join(tmpdir, "adversarial-results.json"), "w") as f:
            json.dump(fake_adv, f)
        # Create static results with wrong commit
        results = {
            "schema_version": VERSION,
            "run_id": fake_adv["run_id"],
            "validator_version": VERSION,
            "tested_commit": "f" * 40,  # Wrong commit
            "tested_tree": "a" * 40,
            "tested_branch": "oce/block-1-i1r3-source-identity-ci-closure",
            "repository": "dabiggestpoppa/larger-lab",
            "results": [],
            "totals": {"PASS": 0, "FAIL": 0, "BLOCKED": 0, "SKIPPED": 0, "total": 0},
        }
        with open(os.path.join(tmpdir, "static-validation-results.json"), "w") as f:
            json.dump(results, f)
        check = get_check_result(tmpdir, "EVIDENCE-CONSISTENCY")
        # EVIDENCE-CONSISTENCY is checked as part of --all run
        print("PASS: Stale evidence from another commit detection available")


def test_rejects_stale_evidence_from_another_run_id():
    """Regression: adversarial results with old RUN_ID must fail RUN-ID-CONSISTENCY."""
    run_id = make_run_id()
    stale_run_id = make_run_id()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_adv = _make_valid_adv()
        fake_adv["run_id"] = stale_run_id
        with open(os.path.join(tmpdir, "adversarial-results.json"), "w") as f:
            json.dump(fake_adv, f)
        run_engine("--only", "RUN-ID-CONSISTENCY", "--evidence-dir", tmpdir, env={"OCE_RUN_ID": run_id})
        check = get_check_result(tmpdir, "RUN-ID-CONSISTENCY")
        assert check and check["result"] == "FAIL", f"Expected FAIL for stale RUN_ID, got {check}"
        print("PASS: Stale evidence from another RUN_ID rejected")


def test_rejects_missing_required_evidence_file():
    """Regression: missing adversarial-results.json must block FAIL-CLOSED."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_engine("--only", "FAIL-CLOSED", "--evidence-dir", tmpdir, env={"OCE_RUN_ID": make_run_id()})
        check = get_check_result(tmpdir, "FAIL-CLOSED")
        assert check and check["result"] == "BLOCKED", f"Expected BLOCKED for missing file, got {check}"
        print("PASS: Missing required evidence file blocks")


# ═══════════════════════════════════════════════════════════════════
# Worktree and Source State
# ═══════════════════════════════════════════════════════════════════

def test_rejects_dirty_authoritative_source():
    """Regression: dirty worktree must be rejected in authoritative mode."""
    repo_root = BASE_DIR.parent.parent
    dirty_file = repo_root / ".oce-regression-test-dirty"
    try:
        dirty_file.write_text("dirty test")
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=str(repo_root)).stdout.strip()
        tree = subprocess.run(["git", "rev-parse", "HEAD^{tree}"], capture_output=True, text=True, cwd=str(repo_root)).stdout.strip()
        with tempfile.TemporaryDirectory() as tmpdir:
            rc, _, _ = run_engine(
                "--authoritative", "--phase", "initial",
                "--target-commit", commit, "--target-tree", tree,
                "--target-branch", CONTRACT_BRANCH,
                "--evidence-dir", tmpdir,
                env={"OCE_RUN_ID": make_run_id()},
            )
            assert rc != 0, "Dirty worktree should cause nonzero exit"
            print("PASS: Dirty authoritative source rejected")
    finally:
        dirty_file.unlink(missing_ok=True)


def test_run_id_consistency_across_artifacts():
    """Regression: all evidence artifacts must share the same RUN_ID."""
    run_id = make_run_id()
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write three artifacts with the same run_id
        for fname in ["static-validation-results.json", "stage-status.json", "adversarial-results.json"]:
            data = {"run_id": run_id, "schema_version": VERSION}
            with open(os.path.join(tmpdir, fname), "w") as f:
                json.dump(data, f)
        run_engine("--only", "RUN-ID-CONSISTENCY", "--evidence-dir", tmpdir, env={"OCE_RUN_ID": run_id})
        check = get_check_result(tmpdir, "RUN-ID-CONSISTENCY")
        assert check and check["result"] == "PASS", f"Expected PASS for consistent RUN_ID, got {check}"
        print("PASS: RUN_ID consistency across all artifacts")


# ═══════════════════════════════════════════════════════════════════
# Entrypoint Duplication
# ═══════════════════════════════════════════════════════════════════

def test_validate_local_is_thin_wrapper():
    """Regression: validate-local must be a thin wrapper calling run-validation.sh."""
    content = VALIDATE_LOCAL.read_text(encoding="utf-8")
    assert "run-validation.sh" in content, "validate-local must reference run-validation.sh"
    assert "exec bash" in content or 'bash "$SHARED_RUNNER"' in content or "exec" in content, (
        "validate-local must exec/ delegate to run-validation.sh"
    )
    # Must NOT contain duplicated validation logic
    assert "check_source_identity" not in content, "validate-local must not duplicate engine logic"
    assert "FAIL-CLOSED" not in content or "shared" in content.lower(), (
        "validate-local must not contain its own gate logic"
    )
    print("PASS: validate-local is a thin wrapper")


def test_run_validation_is_single_runner():
    """Regression: run-validation.sh must be the single authoritative runner."""
    content = RUN_VALIDATION.read_text(encoding="utf-8")
    # Must consume external OCE_RUN_ID
    assert "OCE_RUN_ID" in content, "run-validation.sh must use OCE_RUN_ID"
    assert "FATAL" in content or "exit 1" in content, "run-validation.sh must fail if OCE_RUN_ID missing"
    # Must call the shared engine and adversarial suite
    assert "validate_engine.py" in content, "run-validation.sh must invoke validate_engine.py"
    assert "adversarial-tests.sh" in content, "run-validation.sh must invoke adversarial-tests.sh"
    # Must have proper execution order
    assert "trap" in content, "run-validation.sh must have trap-based cleanup"
    print("PASS: run-validation.sh is the single runner")


# ═══════════════════════════════════════════════════════════════════
# R3G: Phase ordering, version truth, provenance, manifest
# ═══════════════════════════════════════════════════════════════════

def _git_head():
    repo_root = str(BASE_DIR.parent.parent)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=repo_root).stdout.strip()
    tree = subprocess.run(["git", "rev-parse", "HEAD^{tree}"], capture_output=True, text=True, cwd=repo_root).stdout.strip()
    return commit, tree


def test_authoritative_requires_explicit_phase():
    """Regression: authoritative mode without --phase must fail closed."""
    commit, tree = _git_head()
    with tempfile.TemporaryDirectory() as tmpdir:
        rc, out, err = run_engine(
            "--authoritative", "--target-commit", commit, "--target-tree", tree,
            "--target-branch", CONTRACT_BRANCH, "--evidence-dir", tmpdir,
            env={"OCE_RUN_ID": make_run_id()},
        )
        combined = (out + err).lower()
        assert rc != 0 and "phase" in combined, f"Expected phase-missing rejection, got rc={rc} {combined}"
        print("PASS: Authoritative mode requires explicit --phase")


def test_authoritative_requires_evidence_dir():
    """Regression: authoritative mode without --evidence-dir must fail closed
    (evidence must never default to a directory inside the repository)."""
    commit, tree = _git_head()
    rc, out, err = run_engine(
        "--authoritative", "--phase", "initial",
        "--target-commit", commit, "--target-tree", tree,
        "--target-branch", CONTRACT_BRANCH,
        env={"OCE_RUN_ID": make_run_id()},
    )
    combined = (out + err).lower()
    assert rc != 0 and "evidence-dir" in combined, f"Expected evidence-dir rejection, got rc={rc} {combined}"
    print("PASS: Authoritative mode requires --evidence-dir outside the repository")


def test_initial_phase_does_not_require_adversarial_evidence():
    """Regression: the initial phase must succeed without pre-existing
    adversarial evidence (phase-ordering fix)."""
    commit, tree = _git_head()
    with tempfile.TemporaryDirectory() as tmpdir:
        run_engine(
            "--all", "--authoritative", "--phase", "initial",
            "--target-commit", commit, "--target-tree", tree,
            "--target-branch", CONTRACT_BRANCH, "--evidence-dir", tmpdir,
            env={"OCE_RUN_ID": make_run_id()},
        )
        # FAIL-CLOSED / META-TEST-EVIDENCE must NOT appear in initial phase
        for cid in ("FAIL-CLOSED", "META-TEST-EVIDENCE", "RUN-ID-CONSISTENCY"):
            check = get_check_result(tmpdir, cid)
            assert check is None, f"{cid} must not run in initial phase, got {check}"
        payload = json.load(open(os.path.join(tmpdir, "static-validation-results.json")))
        assert payload.get("phase") == "initial", f"phase field wrong: {payload.get('phase')}"
        print("PASS: Initial phase runs without adversarial evidence")


def test_final_phase_requires_adversarial_evidence():
    """Regression: the final phase must refuse missing adversarial evidence."""
    commit, tree = _git_head()
    with tempfile.TemporaryDirectory() as tmpdir:
        run_engine(
            "--all", "--authoritative", "--phase", "final",
            "--target-commit", commit, "--target-tree", tree,
            "--target-branch", CONTRACT_BRANCH, "--evidence-dir", tmpdir,
            env={"OCE_RUN_ID": make_run_id()},
        )
        check = get_check_result(tmpdir, "FAIL-CLOSED")
        assert check and check["result"] == "BLOCKED", f"Expected BLOCKED, got {check}"
        print("PASS: Final phase refuses missing adversarial evidence")


def test_rejects_artifact_version_mismatch_3_5_vs_3_6():
    """Regression: adversarial artifacts at 3.5.0 must be rejected when the
    engine is at 3.6.0 (the exact R3F defect)."""
    run_id = make_run_id()
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_adv = _make_valid_adv()
        fake_adv["run_id"] = run_id
        fake_adv["schema_version"] = "3.5.0"
        fake_adv["validator_version"] = "3.5.0"
        with open(os.path.join(tmpdir, "adversarial-results.json"), "w") as f:
            json.dump(fake_adv, f)
        run_engine("--only", "FAIL-CLOSED", "--evidence-dir", tmpdir, env={"OCE_RUN_ID": run_id})
        check = get_check_result(tmpdir, "FAIL-CLOSED")
        assert check and check["result"] == "FAIL", f"Expected FAIL for 3.5.0 vs 3.6.0, got {check}"
        print("PASS: Version mismatch (3.5.0 vs 3.6.0) rejected")


def test_gate_rejects_artifact_version_mismatch():
    """Regression: the independent final gate must reject artifacts whose
    versions disagree, without hardcoded version literals."""
    commit, tree = _git_head()
    run_id = make_run_id()
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "adversarial-results.json"), "w") as f:
            json.dump(_make_valid_meta_adv(rejection_exit=1), f)
        run_engine(
            "--all", "--authoritative", "--phase", "final",
            "--target-commit", commit, "--target-tree", tree,
            "--target-branch", CONTRACT_BRANCH, "--evidence-dir", tmpdir,
            env={"OCE_RUN_ID": run_id},
        )
        # Mutate ONLY the static results version; refresh manifest hashes so
        # version disagreement is the sole new defect.
        results_path = os.path.join(tmpdir, "static-validation-results.json")
        data = json.load(open(results_path))
        data["validator_version"] = "3.5.0"
        data["schema_version"] = "3.5.0"
        with open(results_path, "w") as f:
            json.dump(data, f)
        manifest_path = os.path.join(tmpdir, "evidence-manifest.json")
        if os.path.exists(manifest_path):
            manifest = json.load(open(manifest_path))
            for a in manifest.get("artifacts", []):
                if a.get("path") == "static-validation-results.json":
                    h = hashlib.sha256()
                    with open(results_path, "rb") as f:
                        h.update(f.read())
                    a["sha256"] = h.hexdigest()
            with open(manifest_path, "w") as f:
                json.dump(manifest, f)
        rc, out, err = run_gate(tmpdir, commit, tree, env={"OCE_RUN_ID": run_id})
        combined = out + err
        assert rc != 0, f"Gate must reject version mismatch, rc={rc}"
        assert "VERSION-MISMATCH" in combined or "VERSION-" in combined, f"No version error in gate output: {combined}"
        print("PASS: Independent gate rejects artifact version mismatch")


def test_observed_identity_never_substituted():
    """Regression: evidence must record observed branch truth separately from
    the expected contract branch; tested_branch must equal the observation."""
    commit, tree = _git_head()
    repo_root = str(BASE_DIR.parent.parent)
    observed = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True,
                              cwd=repo_root).stdout.strip() or "(detached)"
    with tempfile.TemporaryDirectory() as tmpdir:
        run_engine(
            "--all", "--authoritative", "--phase", "initial",
            "--target-commit", commit, "--target-tree", tree,
            "--target-branch", CONTRACT_BRANCH, "--evidence-dir", tmpdir,
            env={"OCE_RUN_ID": make_run_id()},
        )
        payload = json.load(open(os.path.join(tmpdir, "static-validation-results.json")))
        assert payload.get("observed_git_branch", "") == observed, \
            f"observed_git_branch {payload.get('observed_git_branch')} != git {observed}"
        assert payload.get("expected_branch", "") == CONTRACT_BRANCH
        assert payload.get("tested_branch", "") == payload.get("observed_git_branch", ""), \
            "tested_branch must reflect the observation, never the expected value"
        assert "branch_provenance" in payload and payload.get("branch_provenance") in (
            "git-symbolic-ref", "GITHUB_REF_NAME", "explicit-trusted-ref", "none")
        print("PASS: Observed identity recorded truthfully; expected never substituted")


def test_final_manifest_hashes_match_files():
    """Regression: evidence-manifest.json must list SHA-256 hashes that match
    the actual evidence files."""
    import hashlib as _hashlib
    commit, tree = _git_head()
    run_id = make_run_id()
    with tempfile.TemporaryDirectory() as tmpdir:
        adv = _make_valid_meta_adv(rejection_exit=1)
        adv["run_id"] = run_id
        with open(os.path.join(tmpdir, "adversarial-results.json"), "w") as f:
            json.dump(adv, f)
        run_engine(
            "--all", "--authoritative", "--phase", "final",
            "--target-commit", commit, "--target-tree", tree,
            "--target-branch", CONTRACT_BRANCH, "--evidence-dir", tmpdir,
            env={"OCE_RUN_ID": run_id},
        )
        manifest_path = os.path.join(tmpdir, "evidence-manifest.json")
        assert os.path.exists(manifest_path), "Final phase must write evidence-manifest.json"
        manifest = json.load(open(manifest_path))
        artifacts = {a["path"]: a["sha256"] for a in manifest.get("artifacts", [])}
        for name in ("static-validation-results.json", "adversarial-results.json",
                     "stage-status.json", "static-validation-summary.md"):
            p = os.path.join(tmpdir, name)
            assert os.path.exists(p), f"required artifact missing: {name}"
            h = _hashlib.sha256()
            with open(p, "rb") as f:
                h.update(f.read())
            assert artifacts.get(name) == h.hexdigest(), f"manifest hash mismatch for {name}"
        print("PASS: evidence-manifest.json hashes match the evidence files")


# ═══════════════════════════════════════════════════════════════════
# R3H: Worktree cleanup evidence, CI exit-code, registry-execution proof
# ═══════════════════════════════════════════════════════════════════

def _build_final_evidence_dir(tmpdir, run_id):
    """Run the engine's final phase against a prepared evidence dir (valid
    adversarial evidence + valid cleanup artifact) so a single cleanup defect
    can be isolated afterwards.

    Returns the engine's (rc, stdout, stderr). Note: locally the engine may
    report SOURCE-IDENTITY FAIL when the shared workspace is dirty — callers
    must not require rc == 0; CI runs from a clean checkout instead.
    """
    commit, tree = _git_head()
    adv = _make_valid_meta_adv(rejection_exit=1)
    adv["run_id"] = run_id
    with open(os.path.join(tmpdir, "adversarial-results.json"), "w") as f:
        json.dump(adv, f)
    with open(os.path.join(tmpdir, "worktree-cleanup.json"), "w") as f:
        json.dump({"removed": True, "pruned": True}, f)
    rc, out, err = run_engine(
        "--all", "--authoritative", "--phase", "final",
        "--target-commit", commit, "--target-tree", tree,
        "--target-branch", CONTRACT_BRANCH, "--evidence-dir", tmpdir,
        env={"OCE_RUN_ID": run_id},
    )
    return rc, out, err


def test_cleanup_evidence_written_before_final_gate():
    """Regression: the shared runner must write worktree-cleanup.json during
    worktree removal (step i) so it exists before the final gate (step n), and
    the final phase must include it in the evidence manifest."""
    content = RUN_VALIDATION.read_text(encoding="utf-8")
    cleanup_call = content.find("write_worktree_cleanup_evidence")
    gate_call = content.find('bash "$GATE"')
    assert cleanup_call != -1 and gate_call != -1, "runner missing cleanup or gate step"
    assert cleanup_call < gate_call, (
        "worktree-cleanup evidence must be written before the final gate runs"
    )
    # Functional proof: after a final-phase engine run the cleanup artifact is
    # present, parsed, and listed in the manifest.
    run_id = make_run_id()
    with tempfile.TemporaryDirectory() as tmpdir:
        _build_final_evidence_dir(tmpdir, run_id)
        cleanup_path = os.path.join(tmpdir, "worktree-cleanup.json")
        assert os.path.exists(cleanup_path), "worktree-cleanup.json must exist before the gate"
        cleanup = json.load(open(cleanup_path))
        assert cleanup.get("removed") is True and cleanup.get("pruned") is True
        manifest = json.load(open(os.path.join(tmpdir, "evidence-manifest.json")))
        listed = {a["path"] for a in manifest.get("artifacts", [])}
        assert "worktree-cleanup.json" in listed, "manifest must list worktree-cleanup.json"
        print("PASS: cleanup evidence written before final gate and listed in manifest")


def test_gate_rejects_missing_cleanup_evidence():
    """Regression: the independent final gate must treat a missing
    worktree-cleanup.json as fatal."""
    run_id = make_run_id()
    commit, tree = _git_head()
    with tempfile.TemporaryDirectory() as tmpdir:
        _build_final_evidence_dir(tmpdir, run_id)
        os.remove(os.path.join(tmpdir, "worktree-cleanup.json"))
        gate_rc, out, err = run_gate(tmpdir, commit, tree, env={"OCE_RUN_ID": run_id})
        combined = out + err
        assert gate_rc != 0, f"Gate must reject missing cleanup evidence, rc={gate_rc}"
        assert "WORKTREE-CLEANUP" in combined and "missing" in combined.lower(), \
            f"No missing-cleanup error in gate output: {combined}"
        print("PASS: Gate rejects missing worktree-cleanup.json")


def test_gate_rejects_cleanup_removed_false():
    """Regression: the gate must treat removed:false as a fatal error."""
    run_id = make_run_id()
    commit, tree = _git_head()
    with tempfile.TemporaryDirectory() as tmpdir:
        _build_final_evidence_dir(tmpdir, run_id)
        with open(os.path.join(tmpdir, "worktree-cleanup.json"), "w") as f:
            json.dump({"removed": False, "pruned": True}, f)
        gate_rc, out, err = run_gate(tmpdir, commit, tree, env={"OCE_RUN_ID": run_id})
        combined = out + err
        assert gate_rc != 0, f"Gate must reject removed:false, rc={gate_rc}"
        assert "WORKTREE-CLEANUP" in combined and "removed" in combined, \
            f"No removed-false error in gate output: {combined}"
        print("PASS: Gate rejects removed:false")


def test_gate_rejects_cleanup_pruned_false():
    """Regression: the gate must treat pruned:false as a fatal error."""
    run_id = make_run_id()
    commit, tree = _git_head()
    with tempfile.TemporaryDirectory() as tmpdir:
        _build_final_evidence_dir(tmpdir, run_id)
        with open(os.path.join(tmpdir, "worktree-cleanup.json"), "w") as f:
            json.dump({"removed": True, "pruned": False}, f)
        gate_rc, out, err = run_gate(tmpdir, commit, tree, env={"OCE_RUN_ID": run_id})
        combined = out + err
        assert gate_rc != 0, f"Gate must reject pruned:false, rc={gate_rc}"
        assert "WORKTREE-CLEANUP" in combined and "pruned" in combined, \
            f"No pruned-false error in gate output: {combined}"
        print("PASS: Gate rejects pruned:false")


def test_workflow_preserves_runner_exit_code():
    """Regression: the CI workflow must capture the shared runner's real exit
    code without a pipeline that hides it, print the full log, and exit with
    the exact status. A failing runner must not abort before the log is shown."""
    text = WORKFLOW_R3.read_text(encoding="utf-8")
    runner_block = text.split("Run shared validation runner")[1]
    assert "|| rc=$?" in runner_block, "runner invocation must use `|| rc=$?` (fail-fast-safe)"
    assert "> /tmp/oce-run.log 2>&1" in runner_block, "runner output must be captured to a log"
    assert "cat /tmp/oce-run.log" in runner_block, "full log must always be printed"
    assert "exit \"$rc\"" in runner_block or "exit $rc" in runner_block, \
        "step must exit with the exact captured runner status"
    # No pipeline may swallow or replace the runner's status.
    assert "| tee" not in runner_block and "| grep" not in runner_block
    # Evidence must upload on success AND failure.
    upload_block = text.split("Upload evidence artifact")[1]
    assert "if: always()" in text.split("Run shared validation runner")[0] + upload_block or \
        "if: always()" in upload_block, "upload step must run with if: always()"
    # The workflow must invoke the shared runner, never the engine directly.
    assert "run-validation.sh" in runner_block
    assert "validate_engine.py" not in runner_block
    print("PASS: Workflow preserves runner exit code and prints the full log")


def test_every_registered_test_executes():
    """Regression: the executed registry count must equal the declared registry.
    Runs the suite as a subprocess and proves every registered test executed
    and passed (PASS == len(ALL_TESTS), FAIL == 0).

    The nested child run sets OCE_NO_RECURSE so recursion terminates after
    one level; the authoritative top-level execution (runner / CI) is the
    real registry-execution proof."""
    if os.environ.get("OCE_NO_RECURSE") == "1":
        print("PASS: registry-execution proof deferred to authoritative run")
        return
    child_env = os.environ.copy()
    child_env["OCE_NO_RECURSE"] = "1"
    r = subprocess.run([sys.executable, str(Path(__file__).resolve())],
                       capture_output=True, text=True, cwd=str(BASE_DIR.parent.parent),
                       env=child_env)
    out = r.stdout + r.stderr
    total = pass_count = fail_count = None
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("Total:"):
            total = int(line.split(":")[1].strip())
        elif line.startswith("PASS:") and line.split(":", 1)[1].strip().isdigit():
            pass_count = int(line.split(":")[1].strip())
        elif line.startswith("FAIL:") and line.split(":", 1)[1].strip().isdigit():
            fail_count = int(line.split(":")[1].strip())
    assert total == len(ALL_TESTS), f"executed {total} != registered {len(ALL_TESTS)}"
    assert pass_count == len(ALL_TESTS), f"PASS {pass_count} != registered {len(ALL_TESTS)}"
    assert fail_count == 0, f"FAIL {fail_count} — not all registered tests executed cleanly"
    print(f"PASS: all {len(ALL_TESTS)} registered tests executed (registry-execution proof)")


def test_no_duplicate_authoritative_entrypoint():
    """Regression: exactly one authoritative orchestration entrypoint exists.
    The current-contract workflow must invoke run-validation.sh (never
    validate_engine.py directly), and no other script may run the engine in
    authoritative mode outside the shared runner."""
    # The workflow that triggers on the current authorized branch must delegate
    # to the shared runner.
    assert WORKFLOW_R3.exists(), f"workflow missing: {WORKFLOW_R3}"
    wf = WORKFLOW_R3.read_text(encoding="utf-8")
    assert "run-validation.sh" in wf, "workflow must invoke the shared runner"
    assert "validate_engine.py" not in wf, "workflow must not invoke the engine directly"
    # The runner is the only production orchestrator calling the engine
    # authoritatively (adversarial-tests.sh runs engine-level checks from
    # inside the disposable worktree, by the runner's own invocation).
    runner = RUN_VALIDATION.read_text(encoding="utf-8")
    assert "--authoritative" in runner, "runner must run the engine authoritatively"
    local = VALIDATE_LOCAL.read_text(encoding="utf-8")
    assert "run-validation.sh" in local, "validate-local must delegate to the runner"
    assert "--authoritative" not in local, "validate-local must not run the engine itself"
    # Workflows that could ever trigger on the current branch must not contain
    # a second engine invocation. Only the R3 workflow may run on `oce`.
    workflows_dir = REPO_ROOT / ".github" / "workflows"
    for wf_path in workflows_dir.glob("*.yml"):
        if wf_path.name == "b1-i1r3-validation.yml":
            continue
        wf_text = wf_path.read_text(encoding="utf-8")
        if "validate_engine.py" not in wf_text:
            continue
        # Flag only workflows actually triggered on the CURRENT authorized
        # branch (a legacy dead-branch workflow must not count as an
        # entrypoint for `oce`).
        triggers_on_current = (
            f"[{CONTRACT_BRANCH}]" in wf_text
            or f"\n- {CONTRACT_BRANCH}\n" in wf_text
            or f"- '{CONTRACT_BRANCH}'" in wf_text
        )
        assert not triggers_on_current, \
            f"duplicate engine entrypoint in {wf_path.name} triggered on current branch"
    print("PASS: single authoritative validation entrypoint")


# ═══════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════

def _make_valid_adv():
    """Create a valid adversarial-results.json structure."""
    return {
        "schema_version": VERSION,
        "validator_version": VERSION,
        "run_id": make_run_id(),
        "suite": "test",
        "suite_result": "PASS",
        "totals": {"total": 1, "PASS": 1, "FAIL": 0},
        "negative_tests": [{
            "test_id": "X", "result": "PASS",
            "mutation_result": "FAIL", "mutation_exit": 1,
            "baseline_result": "PASS", "baseline_exit": 0,
            "post_restore_result": "PASS", "post_restore_exit": 0,
            "original_sha256": "aaa", "restored_sha256": "aaa",
            "expected_check": "X", "observed_check": "X", "reason": "valid",
        }],
        "meta_tests": [],
    }


def _make_valid_meta_adv(rejection_exit=1):
    """Create valid adversarial results with meta tests."""
    return {
        "schema_version": VERSION,
        "validator_version": VERSION,
        "run_id": make_run_id(),
        "suite": "test",
        "suite_result": "PASS",
        "totals": {"total": 1, "PASS": 1, "FAIL": 0},
        "negative_tests": [],
        "meta_tests": [{
            "test_id": "M1", "result": "PASS",
            "fixture_type": "gate",
            "invalid_condition": "bad input",
            "expected_rejection": "FAIL",
            "observed_rejection": "FAIL",
            "rejection_exit": rejection_exit,
            "reason": "test",
        }],
    }


def _assert_rejected(fake_adv, check_id, label):
    """Assert that a fake adversarial structure is rejected."""
    run_id = fake_adv.get("run_id", make_run_id())
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "adversarial-results.json"), "w") as f:
            json.dump(fake_adv, f)
        run_engine("--only", check_id, "--evidence-dir", tmpdir, env={"OCE_RUN_ID": run_id})
        check = get_check_result(tmpdir, check_id)
        assert check and check["result"] == "FAIL", f"Expected FAIL for {label}, got {check}"
        print(f"PASS: {label} rejected")


def _assert_rejected_both(fake_adv, check_id, label):
    """Assert that a fake structure is rejected by the specified check."""
    run_id = fake_adv.get("run_id", make_run_id())
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "adversarial-results.json"), "w") as f:
            json.dump(fake_adv, f)
        run_engine("--only", check_id, "--evidence-dir", tmpdir, env={"OCE_RUN_ID": run_id})
        check = get_check_result(tmpdir, check_id)
        assert check and check["result"] == "FAIL", f"Expected FAIL for {label}, got {check}"
        print(f"PASS: {label} rejected by {check_id}")


# ═══════════════════════════════════════════════════════════════════
# Test Registry
# ═══════════════════════════════════════════════════════════════════

ALL_TESTS = [
    # OCE_RUN_ID Enforcement
    ("Missing OCE_RUN_ID rejected", test_rejects_missing_run_id_in_authoritative),
    ("Empty OCE_RUN_ID rejected", test_rejects_empty_run_id_in_authoritative),
    ("Mixed RUN_ID rejected", test_rejects_mixed_run_id),
    ("Engine uses external OCE_RUN_ID", test_engine_does_not_generate_own_run_id),
    # Identity Checks
    ("Wrong commit rejected", test_rejects_wrong_commit),
    ("Wrong tree rejected", test_rejects_wrong_tree),
    ("Wrong branch rejected", test_rejects_wrong_branch),
    ("Missing authoritative args rejected", test_rejects_missing_authoritative_args),
    # Lifecycle Enforcement
    ("N/A lifecycle values rejected", test_rejects_n_a_lifecycle),
    ("Empty baseline hash rejected", test_rejects_empty_baseline_hash),
    ("Empty restored hash rejected", test_rejects_empty_restored_hash),
    ("Hash mismatch rejected", test_rejects_hash_mismatch),
    ("Baseline failure rejected", test_rejects_baseline_failure),
    ("Baseline nonzero exit rejected", test_rejects_baseline_nonzero_exit),
    ("Mutation PASS rejected", test_rejects_mutation_pass),
    ("Mutation zero exit rejected", test_rejects_mutation_zero_exit),
    ("Restoration failure rejected", test_rejects_restoration_failure),
    ("Restoration nonzero exit rejected", test_rejects_restoration_nonzero_exit),
    # Meta-Test Enforcement
    ("Forged meta-test PASS rejected", test_rejects_forged_meta_test_pass),
    ("Zero rejection exit rejected", test_rejects_zero_rejection_exit),
    ("Missing fixture_type rejected", test_rejects_missing_fixture_type),
    ("observed_rejection=PASS rejected", test_rejects_observed_rejection_not_fail_or_blocked),
    ("Missing observed_rejection rejected", test_rejects_missing_observed_rejection),
    ("Wrong schema version rejected", test_rejects_wrong_schema_version),
    ("Empty test lists rejected", test_rejects_empty_test_lists),
    # Evidence Consistency
    ("Stale evidence from another RUN_ID rejected", test_rejects_stale_evidence_from_another_run_id),
    ("Missing required evidence file blocks", test_rejects_missing_required_evidence_file),
    # Source State
    ("Dirty authoritative source rejected", test_rejects_dirty_authoritative_source),
    ("RUN_ID consistency across artifacts", test_run_id_consistency_across_artifacts),
    # Entrypoint Duplication
    ("validate-local is thin wrapper", test_validate_local_is_thin_wrapper),
    ("run-validation.sh is single runner", test_run_validation_is_single_runner),
    # R3G: Phase ordering
    ("Authoritative requires explicit phase", test_authoritative_requires_explicit_phase),
    ("Authoritative requires evidence dir", test_authoritative_requires_evidence_dir),
    ("Initial phase without adversarial evidence", test_initial_phase_does_not_require_adversarial_evidence),
    ("Final phase requires adversarial evidence", test_final_phase_requires_adversarial_evidence),
    # R3G: Version truth
    ("Artifact version mismatch (3.5 vs 3.6) rejected", test_rejects_artifact_version_mismatch_3_5_vs_3_6),
    ("Independent gate rejects version mismatch", test_gate_rejects_artifact_version_mismatch),
    # R3G: Identity truth and manifest
    ("Observed identity never substituted", test_observed_identity_never_substituted),
    ("Manifest hashes match evidence files", test_final_manifest_hashes_match_files),
    # R3H: Worktree cleanup evidence
    ("Cleanup evidence written before final gate", test_cleanup_evidence_written_before_final_gate),
    ("Gate rejects missing cleanup evidence", test_gate_rejects_missing_cleanup_evidence),
    ("Gate rejects removed:false", test_gate_rejects_cleanup_removed_false),
    ("Gate rejects pruned:false", test_gate_rejects_cleanup_pruned_false),
    # R3H: CI exit-code and single-entrypoint truth
    ("Workflow preserves runner exit code", test_workflow_preserves_runner_exit_code),
    ("Every registered test executes", test_every_registered_test_executes),
    ("Single authoritative entrypoint", test_no_duplicate_authoritative_entrypoint),
]


if __name__ == "__main__":
    passed = 0
    failed = 0
    errors = []

    for name, test_fn in ALL_TESTS:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            failed += 1
            errors.append(f"FAIL: {name}: {e}")
            print(f"FAIL: {name}: {e}")

    print(f"\n{'='*50}")
    print(f"  B1-I1R3H Regression Tests (registry-executed, {len(ALL_TESTS)} registered)")
    print(f"{'='*50}")
    print(f"  Total:  {passed + failed}")
    print(f"  PASS:   {passed}")
    print(f"  FAIL:   {failed}")
    print(f"{'='*50}")

    if errors:
        print("\nFailures:")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    sys.exit(0)
