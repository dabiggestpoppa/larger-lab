"""B6-I0 must not weaken the amended B5-I9 law: 41/41 plus discriminating mutations.

A single sparse throwaway worktree keeps the disk cost small; every mutation is committed there,
observed on the real node, then reset. Nothing touches the working repository.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

import pytest

import pathlib as _p
import sys as _s

_s.path.insert(0, str(_p.Path(__file__).resolve().parent))
import block_06_i0_support as S  # noqa: E402

NODE = ("infrastructure/control-plane/tests/test_b5_i9_stage_identity_and_scope.py"
        "::TestLocks::test_changed_file_boundary")
B5_FILES = (
    "test_b5_i9_stage_identity_and_scope.py",
    "test_b5_i9_extraction_classification.py",
    "test_b5_i9_no_platform_extraction.py",
    "test_b5_i9_packet_packaging_and_provenance.py",
    "test_b5_i9_book6_handoff.py",
)


def _run(args, cwd):
    return subprocess.run(args, cwd=str(cwd), capture_output=True, text=True)


def _commit(wt, base):
    _run(["git", "-c", "user.email=ci@example.com", "-c", "user.name=ci",
          "commit", "-qam", "probe"], wt)
    return _run(["git", "rev-parse", "HEAD"], wt).stdout.strip() != base


def _sync(wt):
    """Place the current B6-I0 working files into the probe so the validator can read them."""
    for name in S.I0_MODULES:
        (wt / "infrastructure/control-plane/tests" / name).write_bytes(
            (S.TESTS / name).read_bytes())
    for name in S.SCRIPTS_I0:
        (wt / "infrastructure/control-plane/scripts" / name).write_bytes(
            (S.SCRIPTS / name).read_bytes())
    for doc in (S.DOCS).glob("OCE_BLOCK_06_I0_*"):
        (wt / "docs/oce-golden-system" / doc.name).write_bytes(doc.read_bytes())
    _run(["git", "add", "-A"], wt)
    _run(["git", "-c", "user.email=ci@example.com", "-c", "user.name=ci",
          "commit", "-qm", "sync"], wt)


@pytest.fixture(scope="module")
def probe(tmp_path_factory):
    wt = pathlib.Path(tmp_path_factory.mktemp("b5i9")) / "wt"
    add = _run(["git", "worktree", "add", "--detach", "--no-checkout", str(wt), "HEAD"], S.ROOT)
    if add.returncode != 0:
        pytest.skip(f"worktree unavailable: {add.stderr.strip()[:200]}")
    _run(["git", "sparse-checkout", "init", "--cone"], wt)
    _run(["git", "sparse-checkout", "set", "docs/oce-golden-system",
          "infrastructure/control-plane/tests", "infrastructure/control-plane/scripts",
          "infrastructure/control-plane/evidence"], wt)
    _run(["git", "checkout", "-q", "--detach", "HEAD"], wt)
    base = _run(["git", "rev-parse", "HEAD"], wt).stdout.strip()
    yield wt, base
    _run(["git", "worktree", "remove", "--force", str(wt)], S.ROOT)


def _reset(wt, base):
    _run(["git", "reset", "-q", "--hard", base], wt)
    _run(["git", "clean", "-qfdx"], wt)


def test_b5_i9_41_nodes():
    files = [str(S.TESTS / name) for name in B5_FILES]
    out = _run([sys.executable, "-m", "pytest", *files, "-q", "--no-header",
                "-p", "no:cacheprovider"], S.ROOT)
    assert out.returncode == 0, out.stdout[-2000:]
    assert "41 passed" in out.stdout, out.stdout[-800:]


def test_authorized_paths_pass():
    out = _run([sys.executable, "-m", "pytest", NODE, "-q", "--no-header",
                "-p", "no:cacheprovider"], S.ROOT)
    assert out.returncode == 0, out.stdout[-2000:]


def test_unauthorized_mutation_fails(probe):
    wt, base = probe
    target = wt / "infrastructure/control-plane/scripts/b5_i9_gate.py"
    target.write_text(target.read_text(encoding="utf-8") + "\n# probe\n", encoding="utf-8")
    assert _commit(wt, base)
    out = _run([sys.executable, "-m", "pytest", NODE, "-q", "--no-header",
                "-p", "no:cacheprovider"], wt)
    _reset(wt, base)
    assert out.returncode != 0, "unauthorized protected change was accepted"


def test_post_anchor_change_fails(probe):
    wt, base = probe
    target = wt / "infrastructure/control-plane/evidence/b5-i9/g16-limitation.json"
    target.write_text(target.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert _commit(wt, base)
    out = _run([sys.executable, "-m", "pytest", NODE, "-q", "--no-header",
                "-p", "no:cacheprovider"], wt)
    _reset(wt, base)
    assert out.returncode != 0, "post-anchor protected change was accepted"


def test_fake_amendment_fails(probe):
    wt, base = probe
    target = wt / "docs/oce-golden-system" / (
        "OCE_B5_I9_AMENDMENT_001_FUTURE_STAGE_BOUNDARY_COMPATIBILITY_v1.0.md")
    text = target.read_text(encoding="utf-8")
    forged = text.replace('"no_waiver": true', '"no_waiver": true', 1)
    forged = forged.replace("B5-I9-AMEND-001", "B5-I9-AMEND-999", 1)
    target.write_text(forged, encoding="utf-8")
    assert _commit(wt, base)
    out = _run([sys.executable, "-m", "pytest", NODE, "-q", "--no-header",
                "-p", "no:cacheprovider"], wt)
    _reset(wt, base)
    assert out.returncode != 0, "a forged amendment was accepted"


def test_tracked_cache_name_fails(probe):
    wt, base = probe
    hidden = wt / "infrastructure/control-plane/tests/.pytest_cache/b6_evil.py"
    hidden.parent.mkdir(parents=True, exist_ok=True)
    hidden.write_text("x = 1\n", encoding="utf-8")
    _run(["git", "add", "-f", str(hidden.relative_to(wt))], wt)
    _run(["git", "-c", "user.email=ci@example.com", "-c", "user.name=ci",
          "commit", "-qm", "probe"], wt)
    _sync(wt)
    out = _run([sys.executable, str(wt / "infrastructure/control-plane/scripts/"
                                    "block_06_i0_validate.py"), "--root", str(wt)], wt)
    _reset(wt, base)
    assert out.returncode != 0, "a tracked file under a cache-like name was invisible"
    assert "boundary/only_allowed_paths" in out.stdout


def test_untracked_residue_passes(probe):
    wt, base = probe
    residue = wt / "infrastructure/control-plane/tests/.pytest_cache/junk.txt"
    residue.parent.mkdir(parents=True, exist_ok=True)
    residue.write_text("residue\n", encoding="utf-8")
    _sync(wt)
    out = _run([sys.executable, str(wt / "infrastructure/control-plane/scripts/"
                                    "block_06_i0_validate.py"), "--root", str(wt)], wt)
    _reset(wt, base)
    assert out.returncode == 0, out.stdout[-1500:]
    assert "status PASS" in out.stdout
