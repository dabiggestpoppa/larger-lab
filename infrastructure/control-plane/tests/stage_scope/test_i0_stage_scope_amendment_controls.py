"""Non-vacuous negative controls for B6-I0-STAGE-SCOPE-AMENDMENT-001.

Every control mutates an isolated worktree of the exact head and asserts that the amended validator
fails for the intended, named reason. A pristine run must pass first, so no control can pass
vacuously. The worktree is reused and reset between controls; the base control calls the resolver
directly on a throwaway repository so no shared ref is ever moved.
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
WORKFLOW = ROOT / ".github/workflows/block-06-i0-validation.yml"
DOCS_REL = "docs/oce-golden-system"
I1_SCOPE = f"{DOCS_REL}/OCE_BLOCK_06_I1_SCOPE_DERIVATION_v1.0.json"
AMENDMENT = f"{DOCS_REL}/OCE_BLOCK_06_I0_STAGE_SCOPE_AMENDMENT_001_v1.0.json"

sys.path.insert(0, str(ROOT / "infrastructure/control-plane/scripts"))
import block_06_stage_scope as scope  # noqa: E402


def git(cwd, *args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)


def commit(wt: pathlib.Path) -> None:
    assert git(wt, "add", "-A").returncode == 0
    proc = git(wt, "-c", "user.email=ci@example.com", "-c", "user.name=ci",
               "commit", "-qm", "probe")
    assert proc.returncode == 0, proc.stdout + proc.stderr


def run(wt: pathlib.Path, mode: str = "auto") -> tuple[int, set[str], dict]:
    out_dir = pathlib.Path(tempfile.mkdtemp(prefix="b6i0-out-"))
    out = out_dir / "validator.json"
    proc = subprocess.run(
        [sys.executable, str(wt / "infrastructure/control-plane/scripts/block_06_i0_validate.py"),
         "--root", str(wt), "--stage-scope", mode, "--json", str(out)],
        cwd=str(wt), capture_output=True, text=True)
    doc = json.loads(out.read_text(encoding="utf-8"))
    shutil.rmtree(out_dir, ignore_errors=True)
    return proc.returncode, {f["check"] for f in doc["failure_detail"]}, doc


@pytest.fixture(scope="session")
def shared():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="b6i0-amend-"))
    wt = tmp / "wt"
    head = git(ROOT, "rev-parse", "HEAD").stdout.strip()
    add = git(ROOT, "worktree", "add", "--detach", str(wt), "HEAD")
    assert add.returncode == 0, add.stdout + add.stderr
    yield wt, head
    git(ROOT, "worktree", "remove", "--force", str(wt))
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture()
def probe(shared):
    wt, head = shared
    assert git(wt, "reset", "-q", "--hard", head).returncode == 0
    assert git(wt, "clean", "-qfdx").returncode == 0
    return wt


def test_pristine_later_stage_head_passes(probe):
    rc, fails, doc = run(probe)
    assert doc["stage_scope"]["resolved"] in ("later", "i2")
    assert rc == 0 and fails == set() and doc["status"] == "PASS"


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
    rogue = probe / "oce" / "rogue" / "new.py"
    rogue.parent.mkdir(parents=True, exist_ok=True)
    rogue.write_text("x = 1\n", encoding="utf-8")
    commit(probe)
    _, fails, _ = run(probe)
    assert "boundary/oce_within_i1_contract" in fails
    assert "boundary/only_allowed_paths" in fails


def test_later_stage_artifact_fails(probe):
    later = probe / DOCS_REL / "OCE_BLOCK_06_I3_SCOPE_DERIVATION_v1.0.json"
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


def test_moved_base_fails():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="b6i0-base-"))
    try:
        repo = tmp / "repo"
        repo.mkdir()
        assert git(repo, "init", "-q").returncode == 0
        (repo / "README.md").write_text("probe\n", encoding="utf-8")
        assert git(repo, "add", "-A").returncode == 0
        assert git(repo, "-c", "user.email=ci@example.com", "-c", "user.name=ci",
                   "commit", "-qm", "probe").returncode == 0
        assert git(repo, "update-ref", "refs/remotes/origin/main", "HEAD").returncode == 0
        with pytest.raises(scope.StageScopeError) as exc:
            scope.resolve(repo, "auto")
        assert exc.value.check == "stage/base_moved"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_workflow_has_no_waiver():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "--stage-scope auto" in text
    assert "stage-scope.json" in text
    assert "test_i0_stage_scope_amendment_controls.py" in text
    assert "continue-on-error" not in text
    assert "|| true" not in text
