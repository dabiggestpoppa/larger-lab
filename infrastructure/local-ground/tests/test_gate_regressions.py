#!/usr/bin/env python3
"""OCE Local Ground — independent gate and final-package regression tests.

Builds a synthetic-but-valid evidence package, proves the pristine package
passes the gate, then tampers one aspect at a time and proves each regression
is rejected. All rejection tests must actually FAIL the gate or verifier.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS = BASE_DIR / "scripts"
GATE = SCRIPTS / "independent-gate.py"
VERIFY = SCRIPTS / "final-package-verify.sh"
REPO = "dabiggestpoppa/larger-lab"
BRANCH = "oce-program-build"
RUN_ID = "aabbccddeeff"
COMMIT = "c" * 40
TREE = "t" * 40

ENV_OK = dict(os.environ,
              OCE_RUN_ID=RUN_ID,
              OCE_CI_MODE="true",
              OCE_EXPECTED_REPO=REPO,
              OCE_EXPECTED_BRANCH=BRANCH,
              GITHUB_REPOSITORY=REPO,
              GITHUB_REF_NAME=BRANCH,
              PYTHONDONTWRITEBYTECODE="1")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def build_valid_evidence(tmp):
    ev = tmp / "evidence"
    ev.mkdir(parents=True, exist_ok=True)
    write_json(ev / "identity.json", {
        "commit": COMMIT, "tree": TREE, "branch": BRANCH, "tested_commit": COMMIT,
        "repository": REPO, "observed_remote": REPO, "run_id": RUN_ID,
        "trusted_ci_ref": BRANCH, "trusted_ci_repository": REPO})
    write_json(ev / "environment-fingerprint.json", {"os": "Linux", "runtime_target": "local", "tools": {}})
    (ev / "junit.xml").write_text('<?xml version="1.0"?><testsuite tests="1"><testcase name="x"/></testsuite>', encoding="utf-8")
    (ev / "test-mode.txt").write_text("AUTHORITATIVE_CI\n", encoding="utf-8")
    container_names = ["test_04_postgres_state_survives_service_restart",
                       "test_05_postgres_state_survives_compose_restart",
                       "test_06_isolated_redis_loss_preserves_postgres_truth"]
    tests = []
    for n in container_names:
        tests.append({"name": n, "nodeid": n, "container_backed": True, "outcome": "passed", "duration_s": 0.1})
    for n in ["test_07_artifact_round_trip_preserves_hashes", "test_08_backup_completes",
              "test_09_clean_room_local_restore_succeeds", "test_10_restore_meets_declared_recovery_targets",
              "test_11_corrupt_backup_is_rejected", "test_ctl_all_services_healthy"]:
        tests.append({"name": n, "nodeid": n, "container_backed": n.startswith("test_ctl"), "outcome": "passed", "duration_s": 0.1})
    total = len(tests)
    write_json(ev / "test-summary.json", {
        "format": "oce-test-summary-v1", "totals": {"collected": total, "executed": total,
                                                    "passed": total, "failed": 0, "errors": 0, "skipped": 0,
                                                    "mandatory_skipped": 0},
        "container_backed": {"collected": 4, "executed": 4, "passed": 4, "failed": 0, "skipped": 0},
        "mandatory_skipped": 0, "tests": tests})
    write_json(ev / "adversarial-results.json", {
        "format": "oce-adversarial-results-v1",
        "totals": {"PASS": 2, "FAIL": 0},
        "checks": [{"check": "a", "outcome": "PASS"}, {"check": "b", "outcome": "PASS"}]})
    (ev / "adversarial-output.txt").write_text("PASS: a\nPASS: b\n", encoding="utf-8")
    (ev / "cloud-plan.txt").write_text(
        "provider contacts: 0\nresources changed: 0\ncost incurred: ZERO\n", encoding="utf-8")
    (ev / "cloud-apply-denial.txt").write_text(
        "DENIED: cloud apply blocked — missing required field 'AUTHORIZED_STAGE' (fail-closed).\n", encoding="utf-8")
    write_json(ev / "cloud-apply-denial.json", {"exit_code": 5, "expected_nonzero": True})
    write_json(ev / "cloud-plan-deterministic.json", {"deterministic": True})
    write_json(ev / "local-after-denied.json", {"exit_code": 0})
    write_json(ev / "source-clean.json", {"pre": True, "post": True, "dirty_pre": 0, "dirty_post": 0})
    write_json(ev / "cleanup.json", {"cleanup": "ok", "disposable_removed": True})
    write_json(ev / "container-cleanup.json", {
        "cleanup": "ok", "containers_removed": True,
        "networks_removed": True, "volumes_removed": True, "disposable_removed": True})
    (ev / "stage-log.txt").write_text("identity captured\n", encoding="utf-8")
    write_json(ev / "stage-status.json", {
        "block": "B1", "stage": "B1-LOCAL-GROUND-CLOSURE", "run_id": RUN_ID,
        "gate_status": "PENDING_FINAL_GATE", "cloud_mutations": 0, "cloud_cost_state": "ZERO",
        "cloud_activation_state": "DEFERRED_BY_OPERATOR", "cloud_deployment_state": "NOT_DEPLOYED",
        "implementation_commit": COMMIT, "implementation_tree": TREE, "branch": BRANCH})
    _refresh_manifest(ev)
    return ev


def _refresh_manifest(ev):
    artifacts = []
    for name in sorted(os.listdir(ev)):
        p = ev / name
        if p.is_file() and name != "evidence-manifest.json":
            artifacts.append({"path": name, "sha256": sha(p), "size": p.stat().st_size})
    write_json(ev / "evidence-manifest.json", {
        "block": "B1", "stage": "B1-LOCAL-GROUND-CLOSURE", "run_id": RUN_ID,
        "repository": REPO, "branch": BRANCH, "implementation_commit": COMMIT,
        "implementation_tree": TREE, "cloud_mutations": 0, "cloud_cost_state": "ZERO",
        "cloud_activation_state": "DEFERRED_BY_OPERATOR", "artifacts": artifacts})


def run_gate(ev, expect_fail=False, env=None):
    r = subprocess.run([sys.executable, str(GATE), str(ev), COMMIT, TREE],
                       env=dict(ENV_OK, **(env or {})), capture_output=True, text=True, timeout=60)
    if expect_fail:
        assert r.returncode != 0, f"gate should have failed\n{r.stdout}\n{r.stderr}"
    else:
        assert r.returncode == 0, f"gate should have passed\n{r.stdout}\n{r.stderr}"
    return r


_BASH = shutil.which("bash") or "bash"


def run_verify(ev, expect_fail=False):
    r = subprocess.run([_BASH, str(VERIFY), str(ev), COMMIT, TREE],
                       capture_output=True, text=True, timeout=60)
    if expect_fail:
        assert r.returncode != 0, f"verifier should have failed\n{r.stdout}\n{r.stderr}"
    else:
        assert r.returncode == 0, f"verifier should have passed\n{r.stdout}\n{r.stderr}"
    return r


# ── positive ─────────────────────────────────────────────────────────────
def test_gate_passes_on_valid_package(tmp_path):
    ev = build_valid_evidence(tmp_path)
    run_gate(ev)


def test_verify_passes_on_valid_package(tmp_path):
    ev = build_valid_evidence(tmp_path)
    run_gate(ev)  # gate writes independent-gate.json
    run_verify(ev)


# ── identity / repository regressions ────────────────────────────────────
def test_gate_rejects_wrong_repository(tmp_path):
    ev = build_valid_evidence(tmp_path)
    d = json.loads((ev / "identity.json").read_text())
    d["repository"] = "someone-else/repo"
    write_json(ev / "identity.json", d)
    _refresh_manifest(ev)
    run_gate(ev, expect_fail=True)


def test_gate_rejects_repository_typo(tmp_path):
    ev = build_valid_evidence(tmp_path)
    d = json.loads((ev / "identity.json").read_text())
    d["repository"] = "dabigestpoppa/larger-lab"  # one-g typo
    write_json(ev / "identity.json", d)
    _refresh_manifest(ev)
    run_gate(ev, expect_fail=True)


def test_gate_rejects_wrong_branch(tmp_path):
    ev = build_valid_evidence(tmp_path)
    d = json.loads((ev / "identity.json").read_text())
    d["branch"] = "wrong-branch"
    write_json(ev / "identity.json", d)
    _refresh_manifest(ev)
    run_gate(ev, expect_fail=True)


def test_gate_rejects_wrong_commit(tmp_path):
    ev = build_valid_evidence(tmp_path)
    # call gate with a commit argument that differs from the tested checkout
    r = subprocess.run([sys.executable, str(GATE), str(ev), "d" * 40, TREE],
                       env=ENV_OK, capture_output=True, text=True, timeout=60)
    assert r.returncode != 0


def test_gate_rejects_wrong_tree(tmp_path):
    ev = build_valid_evidence(tmp_path)
    r = subprocess.run([sys.executable, str(GATE), str(ev), COMMIT, "u" * 40],
                       env=ENV_OK, capture_output=True, text=True, timeout=60)
    assert r.returncode != 0


def test_gate_rejects_mixed_run_id(tmp_path):
    ev = build_valid_evidence(tmp_path)
    d = json.loads((ev / "identity.json").read_text())
    d["run_id"] = "deadbeefdead"
    write_json(ev / "identity.json", d)
    _refresh_manifest(ev)
    run_gate(ev, expect_fail=True)


def test_gate_rejects_missing_trusted_ci_identity(tmp_path):
    ev = build_valid_evidence(tmp_path)
    run_gate(ev, expect_fail=True, env={"GITHUB_REPOSITORY": "wrong/owner"})


# ── artifact / parse regressions ─────────────────────────────────────────
def test_gate_rejects_malformed_json(tmp_path):
    ev = build_valid_evidence(tmp_path)
    (ev / "identity.json").write_text("{not json", encoding="utf-8")
    run_gate(ev, expect_fail=True)


def test_gate_rejects_missing_required_artifact(tmp_path):
    ev = build_valid_evidence(tmp_path)
    (ev / "junit.xml").unlink()
    run_gate(ev, expect_fail=True)


def test_gate_rejects_stale_manifest(tmp_path):
    ev = build_valid_evidence(tmp_path)
    (ev / "stage-log.txt").write_text("tampered after manifest\n", encoding="utf-8")
    run_gate(ev, expect_fail=True)


def test_gate_rejects_tampered_hash(tmp_path):
    ev = build_valid_evidence(tmp_path)
    m = json.loads((ev / "evidence-manifest.json").read_text())
    m["artifacts"][0]["sha256"] = "0" * 64
    write_json(ev / "evidence-manifest.json", m)
    run_gate(ev, expect_fail=True)


def test_gate_rejects_incorrect_size(tmp_path):
    ev = build_valid_evidence(tmp_path)
    m = json.loads((ev / "evidence-manifest.json").read_text())
    m["artifacts"][0]["size"] = m["artifacts"][0]["size"] + 1
    write_json(ev / "evidence-manifest.json", m)
    run_gate(ev, expect_fail=True)


# ── totals / container / adversarial regressions ─────────────────────────
def test_gate_rejects_skipped_mandatory_test_in_ci(tmp_path):
    ev = build_valid_evidence(tmp_path)
    d = json.loads((ev / "test-summary.json").read_text())
    d["mandatory_skipped"] = 1
    d["totals"]["skipped"] = 1
    d["totals"]["executed"] = d["totals"]["executed"] - 1
    d["container_backed"]["skipped"] = 1
    write_json(ev / "test-summary.json", d)
    _refresh_manifest(ev)
    run_gate(ev, expect_fail=True)


def test_gate_rejects_unexecuted_container_test_in_ci(tmp_path):
    ev = build_valid_evidence(tmp_path)
    d = json.loads((ev / "test-summary.json").read_text())
    d["container_backed"]["executed"] = 3  # collected=4
    write_json(ev / "test-summary.json", d)
    _refresh_manifest(ev)
    run_gate(ev, expect_fail=True)


def test_gate_rejects_mismatched_test_totals(tmp_path):
    ev = build_valid_evidence(tmp_path)
    d = json.loads((ev / "test-summary.json").read_text())
    d["totals"]["passed"] = d["totals"]["passed"] + 5  # inconsistent
    write_json(ev / "test-summary.json", d)
    _refresh_manifest(ev)
    run_gate(ev, expect_fail=True)


def test_gate_rejects_false_adversarial_total(tmp_path):
    ev = build_valid_evidence(tmp_path)
    d = json.loads((ev / "adversarial-results.json").read_text())
    d["totals"]["PASS"] = 99  # entries say 2
    write_json(ev / "adversarial-results.json", d)
    _refresh_manifest(ev)
    run_gate(ev, expect_fail=True)


def test_gate_rejects_adversarial_failure(tmp_path):
    ev = build_valid_evidence(tmp_path)
    d = json.loads((ev / "adversarial-results.json").read_text())
    d["totals"] = {"PASS": 1, "FAIL": 1}
    d["checks"][1]["outcome"] = "FAIL"
    write_json(ev / "adversarial-results.json", d)
    _refresh_manifest(ev)
    run_gate(ev, expect_fail=True)


# ── cloud boundary regressions ───────────────────────────────────────────
def test_gate_rejects_cloud_apply_zero_exit(tmp_path):
    ev = build_valid_evidence(tmp_path)
    d = json.loads((ev / "cloud-apply-denial.json").read_text())
    d["exit_code"] = 0
    write_json(ev / "cloud-apply-denial.json", d)
    _refresh_manifest(ev)
    run_gate(ev, expect_fail=True)


def test_gate_rejects_wrong_cloud_denial_code(tmp_path):
    ev = build_valid_evidence(tmp_path)
    d = json.loads((ev / "cloud-apply-denial.json").read_text())
    d["exit_code"] = 3
    write_json(ev / "cloud-apply-denial.json", d)
    _refresh_manifest(ev)
    run_gate(ev, expect_fail=True)


def test_gate_rejects_cloud_plan_mutation(tmp_path):
    ev = build_valid_evidence(tmp_path)
    (ev / "cloud-plan.txt").write_text("provider contacts: 1\nresources changed: 1\ncost incurred: ZERO\n", encoding="utf-8")
    _refresh_manifest(ev)
    run_gate(ev, expect_fail=True)


def test_gate_rejects_cloud_cost_not_zero(tmp_path):
    ev = build_valid_evidence(tmp_path)
    d = json.loads((ev / "stage-status.json").read_text())
    d["cloud_cost_state"] = "PAID"
    write_json(ev / "stage-status.json", d)
    _refresh_manifest(ev)
    run_gate(ev, expect_fail=True)


def test_gate_rejects_cloud_not_deferred(tmp_path):
    ev = build_valid_evidence(tmp_path)
    d = json.loads((ev / "stage-status.json").read_text())
    d["cloud_activation_state"] = "DEPLOYED"
    write_json(ev / "stage-status.json", d)
    _refresh_manifest(ev)
    run_gate(ev, expect_fail=True)


# ── source / cleanup regressions ─────────────────────────────────────────
def test_gate_rejects_dirty_source_before(tmp_path):
    ev = build_valid_evidence(tmp_path)
    d = json.loads((ev / "source-clean.json").read_text())
    d["pre"] = False
    write_json(ev / "source-clean.json", d)
    _refresh_manifest(ev)
    run_gate(ev, expect_fail=True)


def test_gate_rejects_dirty_source_after(tmp_path):
    ev = build_valid_evidence(tmp_path)
    d = json.loads((ev / "source-clean.json").read_text())
    d["post"] = False
    write_json(ev / "source-clean.json", d)
    _refresh_manifest(ev)
    run_gate(ev, expect_fail=True)


def test_gate_rejects_cleanup_failure(tmp_path):
    ev = build_valid_evidence(tmp_path)
    write_json(ev / "cleanup.json", {"cleanup": "failed", "disposable_removed": False})
    _refresh_manifest(ev)
    run_gate(ev, expect_fail=True)


# ── final-package verifier regressions ───────────────────────────────────
def test_verify_rejects_post_gate_status_mutation(tmp_path):
    ev = build_valid_evidence(tmp_path)
    run_gate(ev)
    d = json.loads((ev / "stage-status.json").read_text())
    d["gate_status"] = "SOMETHING_ELSE"
    write_json(ev / "stage-status.json", d)
    run_verify(ev, expect_fail=True)


def test_verify_rejects_post_gate_log_mutation(tmp_path):
    ev = build_valid_evidence(tmp_path)
    run_gate(ev)
    (ev / "stage-log.txt").write_text("appended after verification\n", encoding="utf-8")
    run_verify(ev, expect_fail=True)


def test_verify_rejects_missing_independent_gate_artifact(tmp_path):
    ev = build_valid_evidence(tmp_path)
    run_gate(ev)
    (ev / "independent-gate.json").unlink()
    run_verify(ev, expect_fail=True)


def test_verify_rejects_tampered_final_artifact(tmp_path):
    ev = build_valid_evidence(tmp_path)
    run_gate(ev)
    (ev / "identity.json").write_text("{}", encoding="utf-8")
    run_verify(ev, expect_fail=True)


# ── CI workflow / dependency regressions ─────────────────────────────────
def test_ci_workflow_uses_shared_runner():
    wf = (BASE_DIR.parents[1] / ".github" / "workflows" / "b1-local-ground.yml").read_text(encoding="utf-8")
    assert "run-validation.sh" in wf, "workflow must use the shared validation runner"


def test_ci_dependencies_are_pinned():
    req = (BASE_DIR / "requirements-ci.txt").read_text(encoding="utf-8")
    assert "pytest==" in req, "pytest must be pinned (==)"
    assert "latest" not in req
    wf = (BASE_DIR.parents[1] / ".github" / "workflows" / "b1-local-ground.yml").read_text(encoding="utf-8")
    assert "requirements-ci.txt" in wf, "workflow must install from the pinned requirements"