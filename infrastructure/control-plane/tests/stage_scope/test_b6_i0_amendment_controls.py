"""Non-vacuous negative controls for B6-I0-STAGE-SCOPE-AMENDMENT-001.

Each control mutates an isolated clone of the exact head and asserts that the amended validator
fails for the intended, named reason. A pristine run must pass, so no control can pass vacuously.
"""
from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[4]
VALIDATOR = ROOT / "infrastructure/control-plane/scripts/block_06_i0_validate.py"
WORKFLOW = ROOT / ".github/workflows/block-06-i0-validation.yml"
I0_MERGE = "6783bf7638f5ecd4e42ec2eb8141d1aa57dfaa3e"
DOCS_REL = "docs/oce-golden-system"
I1_SCOPE = f"{DOCS_REL}/OCE_BLOCK_06_I1_SCOPE_DERIVATION_v1.0.json"
AMENDMENT = f"{DOCS_REL}/OCE_BLOCK_06_I0_STAGE_SCOPE_AMENDMENT_001_v1.0.json"


def git(cwd, *args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)


def commit(wt: pathlib.Path) -> None:
    assert git(wt, "add", "-A").returncode == 0
    proc = git(wt, "-c", "user.email=ci@example.com", "-c", "user.name=ci",
               "commit", "-qm", "probe")
    assert proc.returncode == 0, proc.stdout + proc.stderr


def run(wt: pathlib.Path, mode: str = "auto") -> tuple[int, set[str], dict]:
    out = pathlib.Path(tempfile.mkdtemp(prefix="b6i0-out-")) / "validator.json"
    proc = subprocess.run([sys.executable, str(wt / "infrastructure/control-plane/scripts/"
                                               "block_06_i0_validate.py"),
                           "--root", str(wt), "--stage-scope", mode, "--json", str(out)],
                          cwd=str(wt), capture_output=True, text=True)
    doc = json.loads(out.read_text(encoding="utf-8"))
    shutil.rmtree(out.parent, ignore_errors=True)
    return proc.returncode, {f["check"] for f in doc["failure_detail"]}, doc


@pytest.fixture()
def probe():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="b6i0-amend-"))
    wt = tmp / "wt"
    assert git(ROOT, "clone", "-q", "--no-local", ".", str(wt)).returncode == 0
    head = git(ROOT, "rev-parse", "HEAD").stdout.strip()
    assert git(wt, "checkout", "-q", "--detach", head).returncode == 0
    assert git(wt, "update-ref", "refs/remotes/origin/main", I0_MERGE).returncode == 0
    try:
        yield wt
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_pristine_later_stage_head_passes(probe):
    rc, fails, doc = run(probe)
    assert doc["stage_scope"]["resolved"] == "later"
    assert rc == 0, sorted(fails)
    assert fails == set() and doc["status"] == "PASS"


def test_i0_mode_remains_strict_on_later_head(probe):
    rc, fails, doc = run(probe, "i0")
    assert doc["stage_scope"]["resolved"] == "i0"
    assert rc != 0
    assert "boundary/only_allowed_paths" in fails
    assert "boundary/no_prohibited_surface" in fails


def test_missing_identity_fails(probe):
    (probe / I1_SCOPE).unlink()
    commit(probe)
    _, fails, _ = run(probe)
    assert "stage/identity_missing" in fails


def test_unknown_stage_identity_fails(probe):
    path = probe / I1_SCOPE
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["stage"] = "B6-I9"
    path.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    commit(probe)
    _, fails, _ = run(probe)
    assert "stage/identity_unknown" in fails


def test_dirty_identity_fails(probe):
    path = probe / I1_SCOPE
    path.write_text(path.read_text(encoding="utf-8") + " ", encoding="utf-8")
    _, fails, _ = run(probe)
    assert "stage/identity_spoofed" in fails


def test_tampered_allowlist_fails(probe):
    path = probe / AMENDMENT
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["authorized_paths"].append("oce/rogue/")
    path.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    commit(probe)
    _, fails, _ = run(probe)
    assert "stage/identity_tampered" in fails


def test_unlisted_oce_path_fails(probe):
    rogue = probe / "oce" / "api" / "v1" / "rogue.py"
    rogue.parent.mkdir(parents=True, exist_ok=True)
    rogue.write_text("x = 1\n", encoding="utf-8")
    commit(probe)
    _, fails, _ = run(probe)
    assert "boundary/oce_within_i1_contract" in fails
    assert "boundary/only_allowed_paths" in fails


def test_later_stage_artifact_fails(probe):
    later = probe / DOCS_REL / "OCE_BLOCK_06_I2_SCOPE_DERIVATION_v1.0.json"
    later.write_text("{}\n", encoding="utf-8")
    commit(probe)
    _, fails, _ = run(probe)
    assert "stage/later_stage_absent" in fails


def test_p0_byte_change_fails(probe):
    path = probe / DOCS_REL / "OCE_BLOCK_06_P0_ACCEPTANCE_MATRIX_v1.0.md"
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    commit(probe)
    _, fails, _ = run(probe)
    assert "boundary/p0_packet_untouched" in fails


def test_i0_byte_change_fails(probe):
    path = probe / DOCS_REL / "OCE_BLOCK_06_I0_ACCEPTANCE_MATRIX_v1.0.json"
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    commit(probe)
    _, fails, _ = run(probe)
    assert "boundary/i0_packet_frozen" in fails


def test_package_path_fails(probe):
    pkg = probe / "packages" / "rogue.whl"
    pkg.parent.mkdir(parents=True, exist_ok=True)
    pkg.write_text("binary\n", encoding="utf-8")
    commit(probe)
    _, fails, _ = run(probe)
    assert "boundary/no_prohibited_surface" in fails


def test_moved_base_fails(probe):
    assert git(probe, "update-ref", "refs/remotes/origin/main", "HEAD").returncode == 0
    _, fails, _ = run(probe)
    assert "stage/base_moved" in fails


def test_workflow_has_no_waiver():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "--stage-scope auto" in text
    assert "stage-scope.json" in text
    assert "test_b6_i0_amendment_controls.py" in text
    assert "continue-on-error" not in text
    assert "|| true" not in text
