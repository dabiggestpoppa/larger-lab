#!/usr/bin/env python3
"""OCE Local Ground â€” independent gate and final-package regression tests.

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
    # Names the independent gate requires to have passed (all must be present;
    # container-backed ones are additionally required to EXECUTE in CI mode).
    container_names = ["test_03_services_reach_health_or_unknown",
                       "test_04_postgres_state_survives_service_restart",
                       "test_05_postgres_state_survives_compose_restart",
                       "test_06_isolated_redis_loss_preserves_postgres_truth",
                       "test_ctl_all_services_healthy",
                       "test_ctl_prometheus_readiness_endpoint",
                       "test_ctl_clean_room_database_artifact_restore",
                       "test_ctl_corrupt_backup_rejected_against_running_stack",
                       "test_ctl_structured_logs_use_json_file_driver",
                       "test_ctl_safe_shutdown_and_verified_cleanup",
                       "test_ctl_no_forbidden_public_ports"]
    non_container_names = ["test_07_artifact_round_trip_preserves_hashes",
                           "test_08_backup_completes",
                           "test_09_clean_room_local_restore_succeeds",
                           "test_10_restore_meets_declared_recovery_targets",
                           "test_11_corrupt_backup_is_rejected",
                           "test_full_backup_blocked_without_docker_or_services",
                           "test_full_backup_blocked_when_postgres_unavailable",
                           "test_full_backup_blocked_when_artifact_store_unavailable",
                           "test_state_only_backup_still_works_without_docker"]
    tests = []
    for n in container_names:
        tests.append({"name": n, "nodeid": n, "container_backed": True, "outcome": "passed", "duration_s": 0.1})
    for n in non_container_names:
        tests.append({"name": n, "nodeid": n, "container_backed": False, "outcome": "passed", "duration_s": 0.1})
    total = len(tests)
    cb = len(container_names)
    write_json(ev / "test-summary.json", {
        "format": "oce-test-summary-v1", "totals": {"collected": total, "executed": total,
                                                    "passed": total, "failed": 0, "errors": 0, "skipped": 0,
                                                    "mandatory_skipped": 0},
        "container_backed": {"collected": cb, "executed": cb, "passed": cb, "failed": 0, "skipped": 0},
        "mandatory_skipped": 0, "tests": tests})
    write_json(ev / "adversarial-results.json", {
        "format": "oce-adversarial-results-v1",
        "totals": {"PASS": 2, "FAIL": 0},
        "checks": [{"check": "a", "outcome": "PASS"}, {"check": "b", "outcome": "PASS"}]})
    (ev / "adversarial-output.txt").write_text("PASS: a\nPASS: b\n", encoding="utf-8")
    (ev / "cloud-plan.txt").write_text(
        "provider contacts: 0\nresources changed: 0\ncost incurred: ZERO\n", encoding="utf-8")
    (ev / "cloud-apply-denial.txt").write_text(
        "DENIED: cloud apply blocked â€” missing required field 'AUTHORIZED_STAGE' (fail-closed).\n", encoding="utf-8")
    write_json(ev / "cloud-apply-denial.json", {"exit_code": 5, "expected_nonzero": True})
    write_json(ev / "cloud-plan-deterministic.json", {"deterministic": True})
    write_json(ev / "local-after-denied.json", {"exit_code": 0})
    write_json(ev / "source-clean.json", {"pre": True, "post": True, "dirty_pre": 0, "dirty_post": 0})
    write_json(ev / "cleanup.json", {"cleanup": "ok", "disposable_removed": True})
    write_json(ev / "container-cleanup.json", {
        "cleanup": "ok", "containers_removed": True,
        "networks_removed": True, "volumes_removed": True, "disposable_removed": True})
    # Recovery evidence required in CI mode: verified postgres promotion receipt
    write_json(ev / "postgres-recovery-receipt.json", {
        "format": "oce-pg-recovery-receipt-v1", "database": "oce_local",
        "source_archive_sha256": "a" * 64, "source_commit": COMMIT, "run_id": RUN_ID,
        "staging_database": "oce_local_restore_abc", "promoted": True,
        "exit_status": 0, "redis_restored": False, "tables_verified": True})
    (ev / "stage-log.txt").write_text("identity captured\n", encoding="utf-8")
    write_json(ev / "stage-status.json", {
        "block": "B1", "stage": "B1-LOCAL-GROUND-CLOSURE", "run_id": RUN_ID,
        "gate_status": "PENDING_FINAL_GATE", "cloud_mutations": 0, "cloud_cost_state": "ZERO",
        "cloud_activation_state": "DEFERRED_BY_OPERATOR", "cloud_deployment_state": "NOT_DEPLOYED",
        "implementation_commit": COMMIT, "implementation_tree": TREE, "branch": BRANCH})
    _add_ops_index(ev)
    _refresh_manifest(ev)
    return ev


def _add_ops_index(ev):
    """Build the immutable operation index a valid CI evidence package must
    contain: one successful full-replace restore operation (promote+finalize
    with fingerprints, quarantine held-then-dropped, redis invalidated,
    artifact replaced) and one post-promotion rollback operation."""
    ops_root = ev / "operations"
    src_root = ev / "receipt-src"
    op_a = "a" * 16
    op_b = "b" * 16
    (src_root / op_a).mkdir(parents=True, exist_ok=True)
    (src_root / op_b).mkdir(parents=True, exist_ok=True)
    promote = {"format": "oce-pg-recovery-receipt-v1", "operation_phase": "promote",
               "quarantine_held": True, "quarantine_dropped": False, "promoted": True,
               "staging_verification": {"result": "ok",
                                         "fingerprints": {"public.backup_probe": "x" * 32}},
               "canonical_verification": {"result": "ok",
                                           "fingerprints": {"public.backup_probe": "x" * 32}},
               "phases": ["inventory_validated", "archive_validated", "staging_created",
                          "staging_restored", "staging_verified", "canonical_quarantined",
                          "promoted", "canonical_verified"], "exit_status": 0}
    finalize = {"format": "oce-pg-recovery-receipt-v1", "operation_phase": "finalize",
                "promoted": True, "exit_status": 0, "redis_restored": False,
                "final_verification": {"result": "ok",
                                        "fingerprints": {"public.backup_probe": "x" * 32}},
                "quarantine_dropped": True, "quarantine_removal_verified": True,
                "phases": ["final_canonical_verified", "quarantine_dropped",
                           "quarantine_removal_verified"]}
    redis = {"format": "oce-redis-invalidation-receipt-v1", "redis_restored": False,
             "redis_invalidation_required": True, "redis_invalidation_attempted": True,
             "redis_invalidated": True, "redis_verification": "ok"}
    artifact = {"format": "oce-artifact-recovery-receipt-v1", "artifact_replaced": True,
                "artifact_verify": "ok"}
    for name, data in (("promote-receipt.json", promote),
                       ("postgres-recovery-receipt.json", finalize),
                       ("redis-invalidation-receipt.json", redis),
                       ("artifact-recovery-receipt.json", artifact)):
        (src_root / op_a / name).write_text(json.dumps(data, indent=2), encoding="utf-8")
    rollback = {"format": "oce-pg-recovery-receipt-v1", "operation_phase": "finalize",
                "rollback_required": True, "rollback_attempted": True,
                "rollback_succeeded": True, "rollback_failed": False,
                "original_canonical_restored": True, "promoted_candidate_removed": True,
                "rollback_verification": {"result": "ok"}, "exit_status": 1}
    (src_root / op_b / "postgres-recovery-receipt.json").write_text(
        json.dumps(rollback, indent=2), encoding="utf-8")

    def add_op(opid, final, rb, receipts):
        cmd = [sys.executable, str(SCRIPTS / "recovery-ops.py"), "add",
               "--ops-root", str(ops_root), "--operation-id", opid,
               "--operation-type", "restore", "--run-id", RUN_ID,
               "--commit", COMMIT, "--tree", TREE,
               "--started-at", "2026-01-01T00:00:00Z", "--finished-at", "2026-01-01T00:00:01Z",
               "--backup-id", "b" * 32, "--backup-scope", "full", "--restore-mode", "full-replace",
               "--source-database", "oce_local", "--target-database", "oce_local",
               "--final-result", final, "--rollback-result", rb,
               "--cloud-mutations", "0", "--cloud-cost-state", "ZERO"]
        for rec in receipts:
            cmd += ["--receipt", str(rec)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        assert r.returncode == 0, r.stdout + r.stderr

    add_op(op_a, "success", "none",
           [src_root / op_a / n for n in
            ("promote-receipt.json", "postgres-recovery-receipt.json",
             "redis-invalidation-receipt.json", "artifact-recovery-receipt.json")])
    add_op(op_b, "failed", "ok",
           [src_root / op_b / "postgres-recovery-receipt.json"])


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


# â”€â”€ positive â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def test_gate_passes_on_valid_package(tmp_path):
    ev = build_valid_evidence(tmp_path)
    run_gate(ev)


def test_verify_passes_on_valid_package(tmp_path):
    ev = build_valid_evidence(tmp_path)
    run_gate(ev)  # gate writes independent-gate.json
    run_verify(ev)


# â”€â”€ identity / repository regressions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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


# â”€â”€ artifact / parse regressions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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


# â”€â”€ totals / container / adversarial regressions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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


# â”€â”€ cloud boundary regressions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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


# â”€â”€ source / cleanup regressions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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


# â”€â”€ final-package verifier regressions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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


# â”€â”€ CI workflow / dependency regressions â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def test_ci_workflow_uses_shared_runner():
    wf = (BASE_DIR.parents[1] / ".github" / "workflows" / "b1-local-ground.yml").read_text(encoding="utf-8")
    assert "run-validation.sh" in wf, "workflow must use the shared validation runner"


def test_ci_dependencies_are_pinned():
    req = (BASE_DIR / "requirements-ci.txt").read_text(encoding="utf-8")
    assert "pytest==" in req, "pytest must be pinned (==)"
    assert "latest" not in req
    wf = (BASE_DIR.parents[1] / ".github" / "workflows" / "b1-local-ground.yml").read_text(encoding="utf-8")
    assert "requirements-ci.txt" in wf, "workflow must install from the pinned requirements"


# ── R9: final recovery truth regressions (operation index + gate) ─────────
def test_gate_rejects_missing_operation_index(tmp_path):
    ev = build_valid_evidence(tmp_path)
    import shutil as _sh
    _sh.rmtree(ev / "operations")
    _refresh_manifest(ev)
    run_gate(ev, expect_fail=True)


def test_gate_rejects_latest_only_without_index(tmp_path):
    """A convenience latest.json cannot substitute for the authoritative
    indexed receipt sets: without index.json the gate must fail."""
    ev = build_valid_evidence(tmp_path)
    import shutil as _sh
    _sh.rmtree(ev / "operations")
    (ev / "operations").mkdir(parents=True)
    write_json(ev / "operations" / "latest.json", {"operation_id": "a" * 16})
    _refresh_manifest(ev)
    run_gate(ev, expect_fail=True)


def test_gate_rejects_tampered_indexed_receipt(tmp_path):
    """Modifying an indexed receipt file changes its hash: the gate must fail
    (receipt hash mismatch)."""
    ev = build_valid_evidence(tmp_path)
    p = ev / "operations" / "operations" / ("a" * 16) / "postgres-recovery-receipt.json"
    p.write_text('{"tampered": true}', encoding="utf-8")
    _refresh_manifest(ev)
    run_gate(ev, expect_fail=True)


def test_gate_rejects_missing_indexed_receipt(tmp_path):
    ev = build_valid_evidence(tmp_path)
    (ev / "operations" / "operations" / ("a" * 16) / "redis-invalidation-receipt.json").unlink()
    _refresh_manifest(ev)
    run_gate(ev, expect_fail=True)


def test_gate_rejects_missing_rollback_operation(tmp_path):
    """The post-promotion rollback regression must genuinely execute: without
    an indexed rollback_result=ok operation the gate fails."""
    ev = build_valid_evidence(tmp_path)
    import shutil as _sh
    _sh.rmtree(ev / "operations" / "operations" / ("b" * 16))
    idx = json.loads((ev / "operations" / "index.json").read_text(encoding="utf-8"))
    idx["operations"] = [o for o in idx["operations"] if o["operation_id"] != "b" * 16]
    write_json(ev / "operations" / "index.json", idx)
    _refresh_manifest(ev)
    run_gate(ev, expect_fail=True)


def test_gate_rejects_redis_not_invalidated(tmp_path):
    """A successful full replacement without Redis invalidation must fail the
    gate (stale cache must not survive replacement of PostgreSQL truth)."""
    ev = build_valid_evidence(tmp_path)
    p = ev / "operations" / "operations" / ("a" * 16) / "redis-invalidation-receipt.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    d["redis_invalidated"] = False
    d["redis_verification"] = "failed"
    p.write_text(json.dumps(d, indent=2), encoding="utf-8")
    _refresh_manifest(ev)
    run_gate(ev, expect_fail=True)


def test_gate_rejects_fingerprints_missing(tmp_path):
    """A successful recovery whose receipts carry no value fingerprints must
    fail the gate (row counts alone are not content proof)."""
    ev = build_valid_evidence(tmp_path)
    p = ev / "operations" / "operations" / ("a" * 16) / "postgres-recovery-receipt.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    d["final_verification"].pop("fingerprints", None)
    p.write_text(json.dumps(d, indent=2), encoding="utf-8")
    _refresh_manifest(ev)
    run_gate(ev, expect_fail=True)


def test_gate_rejects_unavailable_service_test_skipped(tmp_path):
    """If the unavailable-service negative test is skipped (not executed),
    the gate must fail even when every other total is green."""
    ev = build_valid_evidence(tmp_path)
    d = json.loads((ev / "test-summary.json").read_text(encoding="utf-8"))
    for t in d["tests"]:
        if t["name"] == "test_full_backup_blocked_without_docker_or_services":
            t["outcome"] = "skipped"
    d["totals"]["skipped"] = 1
    d["totals"]["passed"] = d["totals"]["passed"] - 1
    write_json(ev / "test-summary.json", d)
    _refresh_manifest(ev)
    run_gate(ev, expect_fail=True)


def test_gate_rejects_invalid_rollback_syntax(tmp_path):
    """If invalid PostgreSQL rollback syntax reappears in the recovery
    engine, the gate must fail (source scan)."""
    ev = build_valid_evidence(tmp_path)
    fake_src = tmp_path / "pg-recovery.py"
    fake_src.write_text('ALTER DATABASE IF EXISTS "x" RENAME TO "y";\n', encoding="utf-8")
    _refresh_manifest(ev)
    run_gate(ev, expect_fail=True, env={"OCE_PG_RECOVERY_SRC": str(fake_src)})


def test_gate_rejects_ci_skips_even_with_green_totals(tmp_path):
    """A green test count cannot override a recovery invariant: any skipped
    test in CI (skipped > 0) fails the gate."""
    ev = build_valid_evidence(tmp_path)
    d = json.loads((ev / "test-summary.json").read_text(encoding="utf-8"))
    d["totals"]["skipped"] = 1
    d["totals"]["passed"] = d["totals"]["passed"] - 1
    write_json(ev / "test-summary.json", d)
    _refresh_manifest(ev)
    run_gate(ev, expect_fail=True)