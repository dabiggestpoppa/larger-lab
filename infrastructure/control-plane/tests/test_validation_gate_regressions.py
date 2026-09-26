"""OCE Book 2 — independent-gate regression tests (B2-R9).

Prove the fail-closed contract through fixtures and the LOCAL runner path
(no Docker, no CI): a failing test, a missing mandatory test, a skipped
container test, a wrong commit/tree, dirty source, missing cleanup
evidence, `removed: false`, an altered manifest, and a final stage-log
mutation each make the gate FAIL. Also proves failure evidence remains
uploadable. Deliberately never pushes a known-failing workflow.
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS = BASE_DIR / "scripts"


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


gate_mod = _load("independent_gate", "independent-gate-b2.py")
registry = _load("b2_registry", "b2_registry.py")

RUN_ID = "a1b2c3d4e5f6"
CI_ENV = {
    "OCE_RUN_ID": RUN_ID,
    "OCE_CI_MODE": "true",
    "GITHUB_REPOSITORY": registry.EXPECTED_REPO,
    "GITHUB_REF_NAME": registry.EXPECTED_BRANCH,
    "OCE_EXPECTED_COMMIT": subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(BASE_DIR.parent),
                                          capture_output=True, text=True).stdout.strip(),
    "OCE_EXPECTED_TREE": subprocess.run(["git", "rev-parse", "HEAD^{tree}"], cwd=str(BASE_DIR.parent),
                                        capture_output=True, text=True).stdout.strip(),
}

CATEGORY_FILES = {cat: registry.ARTIFACT_CATEGORY_FILE[cat]
                  for cat in registry.expected_counts()}


def _ctx(**extra):
    data = {"run_id": RUN_ID, "schema_version": registry.SCHEMA_VERSION,
            "validator_version": registry.VALIDATOR_VERSION,
            "repository": registry.EXPECTED_REPO, "branch": registry.EXPECTED_BRANCH,
            "ci_ref": registry.EXPECTED_BRANCH, "environment": "ci",
            "implementation_commit": CI_ENV["OCE_EXPECTED_COMMIT"],
            "implementation_tree": CI_ENV["OCE_EXPECTED_TREE"]}
    data.update(extra)
    return data


def build_evidence(tmp_path, *, skip_ids=(), fail_ids=(), error_ids=(), omit_ids=(),
                   duplicate=False, cleanup_removed=True, missing_cleanup=False,
                   dirty_before=False, dirty_after=False, migration_ok=True,
                   wrong_commit=False, tamper_after_manifest=None,
                   mutate_stage_log_after_manifest=False) -> Path:
    ev = tmp_path / "ev"
    ev.mkdir()
    ids = [n for n in registry.MANDATORY_TEST_IDS if n not in set(omit_ids)]
    if duplicate:
        ids = ids + [registry.MANDATORY_TEST_IDS[0]]
    skipped, failed, errors = set(skip_ids), set(fail_ids), set(error_ids)

    cases = []
    for nid in ids:
        cls, name = nid.rsplit("::", 1)
        inner = ""
        if nid in failed:
            inner = '<failure message="boom" />'
        elif nid in errors:
            inner = '<error message="boom" />'
        elif nid in skipped:
            inner = '<skipped message="container runtime unavailable" />'
        cases.append(f'<testcase classname="{cls}" name="{name}" time="0.001">{inner}</testcase>')
    xml = ('<?xml version="1.0" encoding="utf-8"?>'
           f'<testsuites name="pytest tests"><testsuite name="pytest" tests="{len(ids)}" '
           f'errors="{len(errors)}" failures="{len(failed)}" skipped="{len(skipped)}">'
           + "".join(cases) + "</testsuite></testsuites>")
    (ev / "junit.xml").write_text(xml, encoding="utf-8")
    (ev / "pytest-output.txt").write_text("153 passed in 1.0s\n", encoding="utf-8")

    (ev / "source-identity.json").write_text(json.dumps(_ctx(
        origin_url="https://github.com/dabiggestpoppa/larger-lab.git",
        expected_repository=registry.EXPECTED_REPO, expected_branch=registry.EXPECTED_BRANCH,
        observed_branch=registry.EXPECTED_BRANCH, trusted_ci_ref=registry.EXPECTED_BRANCH,
        captured_at="2026-08-30T00:00:00Z",
        implementation_commit=("0" * 40 if wrong_commit else CI_ENV["OCE_EXPECTED_COMMIT"]),
        implementation_tree=CI_ENV["OCE_EXPECTED_TREE"]), indent=2), encoding="utf-8")
    (ev / "tool-versions.json").write_text(json.dumps(_ctx(
        versions={"python": "3.12", "pytest": "9.0.3", "docker": "x", "docker-compose": "x"}),
        indent=2), encoding="utf-8")
    (ev / "migration-results.json").write_text(json.dumps(_ctx(
        ok=migration_ok, applied_versions=["0001", "0002", "0003"], output="ok"),
        indent=2), encoding="utf-8")
    (ev / "source-cleanliness.json").write_text(json.dumps(_ctx(
        before={"clean": not dirty_before, "dirty_files": ["x.txt"] if dirty_before else []},
        after={"clean": not dirty_after, "dirty_files": ["y.txt"] if dirty_after else []}),
        indent=2), encoding="utf-8")

    # per-category result files (executed = expected minus skips, as junit shows)
    executed_by_cat = {}
    for cat, n in registry.expected_counts().items():
        cat_ids = [i for i in registry.MANDATORY_TEST_IDS if registry.category_of(i) == cat]
        ran = [i for i in cat_ids if i not in set(omit_ids) and i not in set(skip_ids)]
        executed_by_cat[cat] = ran
        (ev / CATEGORY_FILES[cat]).write_text(json.dumps(_ctx(
            category=cat, expected=len(cat_ids), executed=len(ran),
            passed=len([i for i in ran if i not in set(fail_ids)]),
            skipped=[i for i in cat_ids if i in set(skip_ids)],
            failed=[i for i in ran if i in set(fail_ids)],
            missing=[i for i in cat_ids if i not in ran], ids=ran),
            indent=2), encoding="utf-8")

    skipped_total = len(set(skip_ids))
    executed = len(ids) - skipped_total
    failed_total = len(set(fail_ids))
    (ev / "test-registry.json").write_text(json.dumps(_ctx(
        expected_total=len(registry.MANDATORY_TEST_IDS), collected_total=len(ids),
        executed_total=executed, passed_total=executed - failed_total,
        failed_total=failed_total, error_total=len(error_ids), skipped_total=skipped_total,
        duplicate_ids=[], categories={}), indent=2), encoding="utf-8")

    if missing_cleanup:
        pass
    else:
        (ev / "cleanup-results.json").write_text(json.dumps(_ctx(
            compose_down_rc=0, containers_remaining=[],
            containers_removed=cleanup_removed, network_present=not cleanup_removed,
            networks_removed=cleanup_removed,
            durable_postgres_volume_preserved=True,
            redis_volume_state="present", removed=cleanup_removed,
            checked_at="2026-08-30T00:00:00Z"), indent=2), encoding="utf-8")

    # PASS-complete artifacts needed for a green run
    (ev / "stage-log.txt").write_text("run complete\n", encoding="utf-8")
    (ev / "validation-summary.md").write_text(
        "# OCE Book 2 — Validation Summary\n\n- Run: PASS\n", encoding="utf-8")
    return ev


def write_manifest_and_stage(ev, status="PASS"):
    # in the real runner flow: pass A of the gate writes independent-gate.json,
    # THEN stage-status.json, THEN the manifest (generated LAST) — mirror that
    if not (ev / "independent-gate.json").exists():
        (ev / "independent-gate.json").write_text(json.dumps(
            _ctx(gate="PASS", block="B2", stage="B2-CONTROL-PLANE-CLOSURE",
                 phase="independent", counts={}, checks=[], ci_mode=True),
            indent=2), encoding="utf-8")
    (ev / "stage-status.json").write_text(json.dumps(_ctx(
        block="B2", stage="B2-CONTROL-PLANE-CLOSURE", stage_status=status,
        gate_status=status, pytest_exit=0, exit_status=0 if status == "PASS" else 1,
        cloud_mutations=0, cloud_cost_state="ZERO", cloud_deployment_state="NOT_DEPLOYED",
        cloud_activation_state="DEFERRED_BY_OPERATOR", recorded_at="2026-08-30T00:00:00Z"),
        indent=2), encoding="utf-8")
    files = {}
    for name in sorted(p.name for p in ev.iterdir() if p.is_file()):
        if name == "evidence-manifest.json":
            continue
        files[name] = {"sha256": gate_mod.sha256_file(ev / name), "size": (ev / name).stat().st_size}
    (ev / "evidence-manifest.json").write_text(json.dumps(
        {"manifest_version": "1.0.0", "run_id": RUN_ID, "files": files}, indent=2),
        encoding="utf-8")


def run(ev, final=False):
    rc, result = gate_mod.run_gate(ev, 0, final=final, environ=dict(CI_ENV))
    return rc, result


# --------------------------------------------------------------------------
# Green baseline
# --------------------------------------------------------------------------

def test_gate_passes_on_clean_evidence(tmp_path):
    ev = build_evidence(tmp_path)
    rc, result = run(ev)
    assert rc == 0, [c for c in result["checks"] if not c["ok"]]
    assert result["counts"]["collected"] == len(registry.MANDATORY_TEST_IDS)


def test_final_verifier_passes_on_clean_evidence(tmp_path):
    ev = build_evidence(tmp_path)
    write_manifest_and_stage(ev)
    rc, result = run(ev, final=True)
    assert rc == 0, [c for c in result["checks"] if not c["ok"]]


# --------------------------------------------------------------------------
# Failure propagation regressions
# --------------------------------------------------------------------------

def test_failing_test_makes_gate_fail(tmp_path):
    ev = build_evidence(tmp_path, fail_ids={registry.MANDATORY_TEST_IDS[0]})
    rc, result = run(ev)
    assert rc == 1
    assert any(c["id"] == "failed-exact" and not c["ok"] for c in result["checks"])


def test_missing_mandatory_test_makes_gate_fail(tmp_path):
    ev = build_evidence(tmp_path, omit_ids={registry.MANDATORY_TEST_IDS[-1]})
    rc, result = run(ev)
    assert rc == 1
    assert any(c["id"] == "mandatory-present" and not c["ok"] for c in result["checks"])


def test_skipped_container_test_makes_gate_fail_in_ci(tmp_path):
    # a container-backed test (e.g. PG) that was skipped
    skip = next(n for n in registry.MANDATORY_TEST_IDS
                if registry.category_of(n) == "postgres")
    ev = build_evidence(tmp_path, skip_ids={skip})
    rc, result = run(ev)
    assert rc == 1
    assert any(c["id"] == "zero-skips-ci" and not c["ok"] for c in result["checks"])


def test_duplicate_test_id_makes_gate_fail(tmp_path):
    ev = build_evidence(tmp_path, duplicate=True)
    rc, result = run(ev)
    assert rc == 1
    assert any(c["id"] == "no-duplicates" and not c["ok"] for c in result["checks"])


def test_wrong_commit_makes_gate_fail(tmp_path):
    ev = build_evidence(tmp_path, wrong_commit=True)
    rc, result = run(ev)
    assert rc == 1
    assert any(c["id"] == "identity-commit" and not c["ok"] for c in result["checks"])


def test_dirty_source_makes_gate_fail(tmp_path):
    ev = build_evidence(tmp_path, dirty_before=True)
    rc, result = run(ev)
    assert rc == 1
    assert any(c["id"] == "source-clean-before" and not c["ok"] for c in result["checks"])


def test_dirty_source_after_makes_gate_fail(tmp_path):
    ev = build_evidence(tmp_path, dirty_after=True)
    rc, result = run(ev)
    assert rc == 1
    assert any(c["id"] == "source-clean-after" and not c["ok"] for c in result["checks"])


def test_missing_cleanup_evidence_makes_gate_fail(tmp_path):
    ev = build_evidence(tmp_path, missing_cleanup=True)
    rc, result = run(ev)
    assert rc == 1
    assert any(c["id"] == "cleanup-parses" and not c["ok"] for c in result["checks"])


def test_removed_false_makes_gate_fail(tmp_path):
    ev = build_evidence(tmp_path, cleanup_removed=False)
    rc, result = run(ev)
    assert rc == 1
    assert any(c["id"] == "cleanup-removed" and not c["ok"] for c in result["checks"])


def test_migration_failure_makes_gate_fail(tmp_path):
    ev = build_evidence(tmp_path, migration_ok=False)
    rc, result = run(ev)
    assert rc == 1
    assert any(c["id"] == "migrations-ok" and not c["ok"] for c in result["checks"])


def test_altered_manifest_content_fails_final_verify(tmp_path):
    ev = build_evidence(tmp_path)
    write_manifest_and_stage(ev)
    # tamper a hashed artifact AFTER the manifest was generated
    (ev / "tool-versions.json").write_text(json.dumps({}), encoding="utf-8")
    rc, result = run(ev, final=True)
    assert rc == 1
    assert any(c["id"] == "manifest-hashes" and not c["ok"] for c in result["checks"])


def test_stage_log_mutation_fails_final_verify(tmp_path):
    ev = build_evidence(tmp_path)
    write_manifest_and_stage(ev)
    # a post-manifest mutation of the frozen stage log
    with (ev / "stage-log.txt").open("a", encoding="utf-8") as f:
        f.write("late mutation\n")
    rc, result = run(ev, final=True)
    assert rc == 1
    assert any(c["id"] == "manifest-hashes" and not c["ok"] for c in result["checks"])


def test_stage_status_mismatch_fails_final_verify(tmp_path):
    ev = build_evidence(tmp_path, fail_ids={registry.MANDATORY_TEST_IDS[0]})
    write_manifest_and_stage(ev, status="PASS")  # claims PASS but evidence failed
    rc, result = run(ev, final=True)
    assert rc == 1
    assert any(c["id"] == "stage-status-match" and not c["ok"] for c in result["checks"])


# --------------------------------------------------------------------------
# Failure evidence must remain uploadable
# --------------------------------------------------------------------------

def test_failure_evidence_remains_uploadable(tmp_path):
    runner = _load("run_b2_validation", "run_b2_validation.py")
    ev = tmp_path / "fail-ev"
    (ev / "pytest-output.txt").parent.mkdir(parents=True, exist_ok=True)
    runner.write_failure_evidence(
        ev, RUN_ID, {"run_id": RUN_ID, "environment": "ci", "schema_version": "2.0.0",
                     "validator_version": "2.0.0", "repository": "r", "branch": "b",
                     "ci_ref": "b", "implementation_commit": "c", "implementation_tree": "t"},
        reason="BLOCKED: nothing ran", log=["[step_identity]"], rc=2)
    assert (ev / "stage-status.json").exists()
    assert (ev / "evidence-manifest.json").exists()
    stage = json.loads((ev / "stage-status.json").read_text())
    assert stage["stage_status"] == "BLOCKED"
    manifest = json.loads((ev / "evidence-manifest.json").read_text())
    assert "stage-status.json" in manifest["files"]
    # hashes in the failure manifest must match the files on disk
    for name, entry in manifest["files"].items():
        assert gate_mod.sha256_file(ev / name) == entry["sha256"]
