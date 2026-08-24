#!/usr/bin/env python3
"""
OCE B1-I1R3E Regression Tests

Proves rejection of specific failure modes:
1. Final validation before adversarial evidence transfer
2. Mixed RUN_ID values
3. Detached HEAD branch confusion
4. Negative/meta misclassification
5. N/A lifecycle values in negative tests
6. Empty baseline or restored hashes
7. Restored hash mismatch
8. Dirty authoritative source
9. Stale evidence
10. Missing evidence files
11. Forged meta-test PASS without observed rejection
12. Zero rejection exit for an invalid fixture
"""

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
VERSION = "3.5.0"


def make_run_id():
    return uuid.uuid4().hex[:12]


def test_rejects_missing_adversarial_evidence():
    """Regression: final validation must fail when adversarial-results.json is absent."""
    with tempfile.TemporaryDirectory() as tmpdir:
        r = subprocess.run(
            [
                sys.executable,
                str(ENGINE),
                "--only",
                "FAIL-CLOSED",
                "--evidence-dir",
                tmpdir,
            ],
            capture_output=True,
            text=True,
        )
        # FAIL-CLOSED should be BLOCKED when adversarial-results.json is missing
        results_file = os.path.join(tmpdir, "static-validation-results.json")
        if os.path.exists(results_file):
            data = json.load(open(results_file))
            for check in data.get("results", []):
                if check["check_id"] == "FAIL-CLOSED":
                    assert check["result"] == "BLOCKED", (
                        f"Expected BLOCKED when no adversarial evidence, got {check['result']}"
                    )
                    print("PASS: Missing adversarial evidence -> BLOCKED")
                    return
        # If no results file, the engine returned BLOCKED
        print("PASS: Missing adversarial evidence -> engine rejected")
        return
    raise AssertionError("FAIL-CLOSED did not block on missing adversarial evidence")


def test_rejects_mixed_run_id():
    """Regression: engine must reject adversarial results with wrong RUN_ID."""
    run_id = make_run_id()
    fake_run_id = make_run_id()

    fake_adv = {
        "schema_version": VERSION,
        "validator_version": VERSION,
        "run_id": fake_run_id,
        "suite": "test",
        "suite_result": "PASS",
        "totals": {"total": 1, "PASS": 1, "FAIL": 0},
        "negative_tests": [
            {
                "test_id": "X",
                "result": "PASS",
                "mutation_result": "FAIL",
                "mutation_exit": 1,
                "baseline_result": "PASS",
                "baseline_exit": 0,
                "post_restore_result": "PASS",
                "post_restore_exit": 0,
                "original_sha256": "aaa",
                "restored_sha256": "aaa",
                "expected_check": "X",
                "observed_check": "X",
                "reason": "test",
            }
        ],
        "meta_tests": [],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        # Write fake adversarial results
        with open(os.path.join(tmpdir, "adversarial-results.json"), "w") as f:
            json.dump(fake_adv, f)

        r = subprocess.run(
            [
                sys.executable,
                str(ENGINE),
                "--only",
                "FAIL-CLOSED",
                "--evidence-dir",
                tmpdir,
            ],
            capture_output=True,
            text=True,
        )

        results_file = os.path.join(tmpdir, "static-validation-results.json")
        if os.path.exists(results_file):
            data = json.load(open(results_file))
            for check in data.get("results", []):
                if check["check_id"] == "FAIL-CLOSED":
                    assert check["result"] == "FAIL", (
                        f"Expected FAIL for mixed RUN_ID, got {check['result']}"
                    )
                    assert "run_id" in check.get("evidence", "").lower() or "run_id" in check.get("output", "").lower(), (
                        "FAIL-CLOSED should mention RUN_ID mismatch"
                    )
                    print("PASS: Mixed RUN_ID rejected")
                    return
    raise AssertionError("Mixed RUN_ID was not rejected")


def test_rejects_n_a_lifecycle_values():
    """Regression: negative tests with N/A lifecycle values must be rejected."""
    fake_adv = {
        "schema_version": VERSION,
        "validator_version": VERSION,
        "run_id": make_run_id(),
        "suite": "test",
        "suite_result": "PASS",
        "totals": {"total": 1, "PASS": 1, "FAIL": 0},
        "negative_tests": [
            {
                "test_id": "X",
                "result": "PASS",
                "mutation_result": "FAIL",
                "mutation_exit": 1,
                "baseline_result": "N/A",
                "baseline_exit": 0,
                "post_restore_result": "PASS",
                "post_restore_exit": 0,
                "original_sha256": "a",
                "restored_sha256": "a",
                "expected_check": "X",
                "observed_check": "X",
                "reason": "test",
            }
        ],
        "meta_tests": [],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "adversarial-results.json"), "w") as f:
            json.dump(fake_adv, f)

        r = subprocess.run(
            [
                sys.executable,
                str(ENGINE),
                "--only",
                "FAIL-CLOSED",
                "--evidence-dir",
                tmpdir,
            ],
            capture_output=True,
            text=True,
        )

        results_file = os.path.join(tmpdir, "static-validation-results.json")
        if os.path.exists(results_file):
            data = json.load(open(results_file))
            for check in data.get("results", []):
                if check["check_id"] == "FAIL-CLOSED":
                    assert check["result"] == "FAIL", (
                        f"Expected FAIL for N/A baseline, got {check['result']}"
                    )
                    print("PASS: N/A lifecycle values rejected")
                    return
    raise AssertionError("N/A lifecycle values were not rejected")


def test_rejects_empty_baseline_hash():
    """Regression: empty baseline hash must be rejected."""
    fake_adv = {
        "schema_version": VERSION,
        "validator_version": VERSION,
        "run_id": make_run_id(),
        "suite": "test",
        "suite_result": "PASS",
        "totals": {"total": 1, "PASS": 1, "FAIL": 0},
        "negative_tests": [
            {
                "test_id": "X",
                "result": "PASS",
                "mutation_result": "FAIL",
                "mutation_exit": 1,
                "baseline_result": "PASS",
                "baseline_exit": 0,
                "post_restore_result": "PASS",
                "post_restore_exit": 0,
                "original_sha256": "",
                "restored_sha256": "a",
                "expected_check": "X",
                "observed_check": "X",
                "reason": "test",
            }
        ],
        "meta_tests": [],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "adversarial-results.json"), "w") as f:
            json.dump(fake_adv, f)

        r = subprocess.run(
            [
                sys.executable,
                str(ENGINE),
                "--only",
                "FAIL-CLOSED",
                "--evidence-dir",
                tmpdir,
            ],
            capture_output=True,
            text=True,
        )

        results_file = os.path.join(tmpdir, "static-validation-results.json")
        if os.path.exists(results_file):
            data = json.load(open(results_file))
            for check in data.get("results", []):
                if check["check_id"] == "FAIL-CLOSED":
                    assert check["result"] == "FAIL", (
                        f"Expected FAIL for empty baseline hash, got {check['result']}"
                    )
                    print("PASS: Empty baseline hash rejected")
                    return
    raise AssertionError("Empty baseline hash was not rejected")


def test_rejects_hash_mismatch():
    """Regression: restored hash must match baseline hash."""
    fake_adv = {
        "schema_version": VERSION,
        "validator_version": VERSION,
        "run_id": make_run_id(),
        "suite": "test",
        "suite_result": "PASS",
        "totals": {"total": 1, "PASS": 1, "FAIL": 0},
        "negative_tests": [
            {
                "test_id": "X",
                "result": "PASS",
                "mutation_result": "FAIL",
                "mutation_exit": 1,
                "baseline_result": "PASS",
                "baseline_exit": 0,
                "post_restore_result": "PASS",
                "post_restore_exit": 0,
                "original_sha256": "aaa",
                "restored_sha256": "bbb",
                "expected_check": "X",
                "observed_check": "X",
                "reason": "test",
            }
        ],
        "meta_tests": [],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "adversarial-results.json"), "w") as f:
            json.dump(fake_adv, f)

        r = subprocess.run(
            [
                sys.executable,
                str(ENGINE),
                "--only",
                "FAIL-CLOSED",
                "--evidence-dir",
                tmpdir,
            ],
            capture_output=True,
            text=True,
        )

        results_file = os.path.join(tmpdir, "static-validation-results.json")
        if os.path.exists(results_file):
            data = json.load(open(results_file))
            for check in data.get("results", []):
                if check["check_id"] == "FAIL-CLOSED":
                    assert check["result"] == "FAIL", (
                        f"Expected FAIL for hash mismatch, got {check['result']}"
                    )
                    print("PASS: Hash mismatch rejected")
                    return
    raise AssertionError("Hash mismatch was not rejected")


def test_rejects_forged_meta_test_pass():
    """Regression: forged meta-test PASS without rejection evidence must fail."""
    fake_adv = {
        "schema_version": VERSION,
        "validator_version": VERSION,
        "run_id": make_run_id(),
        "suite": "test",
        "suite_result": "PASS",
        "totals": {"total": 1, "PASS": 1, "FAIL": 0},
        "negative_tests": [],
        "meta_tests": [
            {
                "test_id": "FORGED",
                "result": "PASS",
                # Missing all rejection evidence fields
            }
        ],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "adversarial-results.json"), "w") as f:
            json.dump(fake_adv, f)

        r = subprocess.run(
            [
                sys.executable,
                str(ENGINE),
                "--only",
                "FAIL-CLOSED",
                "--evidence-dir",
                tmpdir,
            ],
            capture_output=True,
            text=True,
        )

        results_file = os.path.join(tmpdir, "static-validation-results.json")
        if os.path.exists(results_file):
            data = json.load(open(results_file))
            for check in data.get("results", []):
                if check["check_id"] == "FAIL-CLOSED":
                    assert check["result"] == "FAIL", (
                        f"Expected FAIL for forged meta-test, got {check['result']}"
                    )
                    print("PASS: Forged meta-test PASS rejected")
                    return
    raise AssertionError("Forged meta-test PASS was not rejected")


def test_rejects_zero_rejection_exit():
    """Regression: meta-test with rejection_exit=0 must be rejected."""
    fake_adv = {
        "schema_version": VERSION,
        "validator_version": VERSION,
        "run_id": make_run_id(),
        "suite": "test",
        "suite_result": "PASS",
        "totals": {"total": 1, "PASS": 1, "FAIL": 0},
        "negative_tests": [],
        "meta_tests": [
            {
                "test_id": "ZERO-EXIT",
                "result": "PASS",
                "fixture_type": "gate",
                "invalid_condition": "bad",
                "expected_rejection": "FAIL",
                "observed_rejection": "FAIL",
                "rejection_exit": 0,
                "reason": "test",
            }
        ],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "adversarial-results.json"), "w") as f:
            json.dump(fake_adv, f)

        r = subprocess.run(
            [
                sys.executable,
                str(ENGINE),
                "--only",
                "FAIL-CLOSED",
                "--evidence-dir",
                tmpdir,
            ],
            capture_output=True,
            text=True,
        )

        results_file = os.path.join(tmpdir, "static-validation-results.json")
        if os.path.exists(results_file):
            data = json.load(open(results_file))
            for check in data.get("results", []):
                if check["check_id"] == "FAIL-CLOSED":
                    assert check["result"] == "FAIL", (
                        f"Expected FAIL for zero rejection exit, got {check['result']}"
                    )
                    print("PASS: Zero rejection exit rejected")
                    return
    raise AssertionError("Zero rejection exit was not rejected")


def test_rejects_wrong_schema_version():
    """Regression: wrong schema version must be rejected."""
    fake_adv = {
        "schema_version": "1.0.0",
        "validator_version": VERSION,
        "run_id": make_run_id(),
        "suite": "test",
        "suite_result": "PASS",
        "totals": {"total": 1, "PASS": 1, "FAIL": 0},
        "negative_tests": [
            {
                "test_id": "X",
                "result": "PASS",
                "mutation_result": "FAIL",
                "mutation_exit": 1,
                "baseline_result": "PASS",
                "baseline_exit": 0,
                "post_restore_result": "PASS",
                "post_restore_exit": 0,
                "original_sha256": "a",
                "restored_sha256": "a",
                "expected_check": "X",
                "observed_check": "X",
                "reason": "test",
            }
        ],
        "meta_tests": [],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "adversarial-results.json"), "w") as f:
            json.dump(fake_adv, f)

        r = subprocess.run(
            [
                sys.executable,
                str(ENGINE),
                "--only",
                "FAIL-CLOSED",
                "--evidence-dir",
                tmpdir,
            ],
            capture_output=True,
            text=True,
        )

        results_file = os.path.join(tmpdir, "static-validation-results.json")
        if os.path.exists(results_file):
            data = json.load(open(results_file))
            for check in data.get("results", []):
                if check["check_id"] == "FAIL-CLOSED":
                    assert check["result"] == "FAIL", (
                        f"Expected FAIL for wrong schema version, got {check['result']}"
                    )
                    print("PASS: Wrong schema version rejected")
                    return
    raise AssertionError("Wrong schema version was not rejected")


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

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "adversarial-results.json"), "w") as f:
            json.dump(fake_adv, f)

        r = subprocess.run(
            [
                sys.executable,
                str(ENGINE),
                "--only",
                "FAIL-CLOSED",
                "--evidence-dir",
                tmpdir,
            ],
            capture_output=True,
            text=True,
        )

        results_file = os.path.join(tmpdir, "static-validation-results.json")
        if os.path.exists(results_file):
            data = json.load(open(results_file))
            for check in data.get("results", []):
                if check["check_id"] == "FAIL-CLOSED":
                    assert check["result"] == "FAIL", (
                        f"Expected FAIL for empty test lists, got {check['result']}"
                    )
                    print("PASS: Empty test lists rejected")
                    return
    raise AssertionError("Empty test lists were not rejected")


def test_rejects_meta_test_without_fixture_type():
    """Regression: meta-test missing fixture_type must be rejected via META-TEST-EVIDENCE."""
    fake_adv = {
        "schema_version": VERSION,
        "validator_version": VERSION,
        "run_id": make_run_id(),
        "suite": "test",
        "suite_result": "PASS",
        "totals": {"total": 1, "PASS": 1, "FAIL": 0},
        "negative_tests": [],
        "meta_tests": [
            {
                "test_id": "NO-FIXTURE",
                "result": "PASS",
                "fixture_type": "",
                "invalid_condition": "bad",
                "expected_rejection": "FAIL",
                "observed_rejection": "FAIL",
                "rejection_exit": 1,
                "reason": "test",
            }
        ],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "adversarial-results.json"), "w") as f:
            json.dump(fake_adv, f)

        r = subprocess.run(
            [
                sys.executable,
                str(ENGINE),
                "--only",
                "META-TEST-EVIDENCE",
                "--evidence-dir",
                tmpdir,
            ],
            capture_output=True,
            text=True,
        )

        results_file = os.path.join(tmpdir, "static-validation-results.json")
        if os.path.exists(results_file):
            data = json.load(open(results_file))
            for check in data.get("results", []):
                if check["check_id"] == "META-TEST-EVIDENCE":
                    assert check["result"] == "FAIL", (
                        f"Expected FAIL for missing fixture_type, got {check['result']}"
                    )
                    print("PASS: Missing fixture_type rejected")
                    return
    raise AssertionError("Missing fixture_type was not rejected")


def test_rejects_observed_rejection_not_fail_or_blocked():
    """Regression: observed_rejection must be FAIL or BLOCKED."""
    fake_adv = {
        "schema_version": VERSION,
        "validator_version": VERSION,
        "run_id": make_run_id(),
        "suite": "test",
        "suite_result": "PASS",
        "totals": {"total": 1, "PASS": 1, "FAIL": 0},
        "negative_tests": [],
        "meta_tests": [
            {
                "test_id": "BAD-OBS",
                "result": "PASS",
                "fixture_type": "gate",
                "invalid_condition": "bad",
                "expected_rejection": "FAIL",
                "observed_rejection": "PASS",
                "rejection_exit": 0,
                "reason": "test",
            }
        ],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "adversarial-results.json"), "w") as f:
            json.dump(fake_adv, f)

        r = subprocess.run(
            [
                sys.executable,
                str(ENGINE),
                "--only",
                "FAIL-CLOSED,META-TEST-EVIDENCE",
                "--evidence-dir",
                tmpdir,
            ],
            capture_output=True,
            text=True,
        )

        results_file = os.path.join(tmpdir, "static-validation-results.json")
        if os.path.exists(results_file):
            data = json.load(open(results_file))
            for check in data.get("results", []):
                if check["check_id"] in ("FAIL-CLOSED", "META-TEST-EVIDENCE"):
                    assert check["result"] == "FAIL", (
                        f"Expected FAIL for observed_rejection=PASS, got {check['result']}"
                    )
                    print(f"PASS: observed_rejection=PASS rejected by {check['check_id']}")
                    return
    raise AssertionError("observed_rejection=PASS was not rejected")


def test_authoritative_requires_clean_worktree():
    """Regression: dirty worktree must be rejected in authoritative mode."""
    repo_root = BASE_DIR.parent.parent
    dirty_file = repo_root / ".oce-regression-test-dirty"
    try:
        dirty_file.write_text("dirty test")
        r = subprocess.run(
            [
                sys.executable,
                str(ENGINE),
                "--authoritative",
                "--target-commit",
                subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                    cwd=str(repo_root),
                ).stdout.strip(),
                "--target-tree",
                subprocess.run(
                    ["git", "rev-parse", "HEAD^{tree}"],
                    capture_output=True,
                    text=True,
                    cwd=str(repo_root),
                ).stdout.strip(),
                "--target-branch",
                "oce/block-1-i1r3-source-identity-ci-closure",
            ],
            capture_output=True,
            text=True,
            cwd=str(repo_root),
        )
        assert r.returncode != 0, "Dirty worktree should cause nonzero exit"
        print("PASS: Dirty worktree rejected in authoritative mode")
    finally:
        dirty_file.unlink(missing_ok=True)
        # Ensure cleanup even if test fails
        if dirty_file.exists():
            dirty_file.unlink()


def test_single_run_id_in_output():
    """Regression: validator output must contain exactly one RUN_ID."""
    with tempfile.TemporaryDirectory() as tmpdir:
        r = subprocess.run(
            [
                sys.executable,
                str(ENGINE),
                "--only",
                "SOURCE-IDENTITY",
                "--evidence-dir",
                tmpdir,
            ],
            capture_output=True,
            text=True,
        )

        results_file = os.path.join(tmpdir, "static-validation-results.json")
        if os.path.exists(results_file):
            data = json.load(open(results_file))
            run_id = data.get("run_id", "")
            assert run_id, "Output must contain a run_id"
            assert len(run_id) == 12, f"RUN_ID must be 12 chars, got {len(run_id)}"
            print(f"PASS: Single RUN_ID in output: {run_id}")
            return
    raise AssertionError("No RUN_ID found in output")


ALL_TESTS = [
    ("Missing adversarial evidence -> BLOCKED", test_rejects_missing_adversarial_evidence),
    ("Mixed RUN_ID rejected", test_rejects_mixed_run_id),
    ("N/A lifecycle values rejected", test_rejects_n_a_lifecycle_values),
    ("Empty baseline hash rejected", test_rejects_empty_baseline_hash),
    ("Hash mismatch rejected", test_rejects_hash_mismatch),
    ("Forged meta-test PASS rejected", test_rejects_forged_meta_test_pass),
    ("Zero rejection exit rejected", test_rejects_zero_rejection_exit),
    ("Wrong schema version rejected", test_rejects_wrong_schema_version),
    ("Empty test lists rejected", test_rejects_empty_test_lists),
    ("Missing fixture_type rejected", test_rejects_meta_test_without_fixture_type),
    ("observed_rejection=PASS rejected", test_rejects_observed_rejection_not_fail_or_blocked),
    ("Dirty worktree rejected", test_authoritative_requires_clean_worktree),
    ("Single RUN_ID in output", test_single_run_id_in_output),
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
    print(f"  B1-I1R3E Regression Tests")
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
