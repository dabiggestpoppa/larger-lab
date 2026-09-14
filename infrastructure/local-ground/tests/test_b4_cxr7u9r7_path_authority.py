#!/usr/bin/env python3
"""B4-CXR7U9R7 - truthful filesystem path authority proofs.

Proves the authority model claimed for every path input:

* independent-gate.py _validated_subprocess_path enforces REAL
  containment inside the approved evidence root (traversal, absolute
  escape, symlink substitution, prefix collisions all rejected);
* pg-recovery.py / pg-verify.py _validated_open_path honestly classify
  their inputs as OPERATOR_TRUSTED_INPUT (no containment claim) and
  still refuse symlink indirection, non-regular files and missing
  paths; denial has zero durable side effects (pure predicates).
"""
import importlib.util
import os
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
SCRIPTS = BASE / "scripts"


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, str(SCRIPTS / filename))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


gate = _load("u9r7_gate", "independent-gate.py")
pgrec = _load("u9r7_pgrec", "pg-recovery.py")
pgver = _load("u9r7_pgver", "pg-verify.py")


def _symlink_creatable() -> bool:
    """Probe once whether THIS platform/privilege set can create symlinks.

    Windows without SeCreateSymbolicLinkPrivilege (or Developer Mode)
    raises OSError WinError 1314; Linux CI (where these adversarial
    proofs are mandatory) always can. The skip is TRUTHFUL: it names
    the missing capability, never hides a failure of the code under
    test (the containment logic itself is exercised on every platform
    through the traversal/absolute/prefix-collision cases).
    """
    import tempfile
    try:
        with tempfile.TemporaryDirectory() as td:
            target = os.path.join(td, "t")
            os.mkdir(target)
            link = os.path.join(td, "l")
            os.symlink(target, link)
            os.unlink(link)
        return True
    except (OSError, NotImplementedError):
        return False


SYMLINKS_OK = _symlink_creatable()
needs_symlink = pytest.mark.skipif(
    not SYMLINKS_OK,
    reason="symlink creation requires privilege on this platform "
           "(WinError 1314); mandatory in CI where symlinks work")


# --------------------------------------------------------------------- #
# independent-gate containment matrix
# --------------------------------------------------------------------- #

class TestGateOpsRootContainment:
    def test_exact_approved_root_accepted(self, tmp_path):
        ops = tmp_path / "operations"
        ops.mkdir()
        out = gate._validated_subprocess_path(str(ops), str(tmp_path))
        assert Path(out) == Path(os.path.realpath(str(ops)))

    def test_valid_descendant_accepted(self, tmp_path):
        sub = tmp_path / "operations" / "receipts"
        sub.mkdir(parents=True)
        out = gate._validated_subprocess_path(str(sub), str(tmp_path))
        assert os.path.realpath(str(sub)) == out

    def test_parent_traversal_escape_rejected(self, tmp_path):
        outside = tmp_path.parent / "outside-evidence"
        outside.mkdir(exist_ok=True)
        candidate = str(tmp_path / "operations" / ".." / ".." / "outside-evidence")
        with pytest.raises(RuntimeError, match="escapes approved root"):
            gate._validated_subprocess_path(candidate, str(tmp_path))

    def test_arbitrary_absolute_external_rejected(self, tmp_path):
        external = str(Path(os.environ.get("SYSTEMROOT", "/etc")))
        with pytest.raises(RuntimeError, match="escapes approved root"):
            gate._validated_subprocess_path(external, str(tmp_path))

    @needs_symlink
    def test_symlink_file_candidate_rejected(self, tmp_path):
        real_dir = tmp_path.parent / "real-ops-u9r7"
        real_dir.mkdir(exist_ok=True)
        link = tmp_path / "operations"
        os.symlink(str(real_dir), str(link))
        try:
            with pytest.raises(RuntimeError, match="escapes approved root"):
                gate._validated_subprocess_path(str(link), str(tmp_path))
        finally:
            link.unlink()

    @needs_symlink
    def test_symlink_parent_directory_rejected(self, tmp_path):
        real_ev = tmp_path.parent / "real-ev-u9r7"
        real_ev.mkdir(exist_ok=True)
        (real_ev / "operations").mkdir(exist_ok=True)
        link_ev = tmp_path / "evil-link"
        os.symlink(str(real_ev), str(link_ev))
        try:
            with pytest.raises(RuntimeError, match="escapes approved root"):
                gate._validated_subprocess_path(
                    str(link_ev / "operations"), str(tmp_path))
        finally:
            link_ev.unlink()

    def test_prefix_collision_rejected(self, tmp_path):
        evil = tmp_path.parent / (tmp_path.name + "-evil")
        evil.mkdir(exist_ok=True)
        try:
            with pytest.raises(RuntimeError, match="escapes approved root"):
                gate._validated_subprocess_path(evil, str(tmp_path))
        finally:
            evil.rmdir()

    def test_nonexistent_path_rejected(self, tmp_path):
        with pytest.raises(RuntimeError, match="not a directory"):
            gate._validated_subprocess_path(
                str(tmp_path / "operations" / "missing"), str(tmp_path))

    def test_wrong_type_file_rejected(self, tmp_path):
        f = tmp_path / "operations-file"
        f.write_text("x")
        with pytest.raises(RuntimeError, match="not a directory"):
            gate._validated_subprocess_path(str(f), str(tmp_path))

    def test_missing_approved_root_rejected(self, tmp_path):
        with pytest.raises(RuntimeError, match="approved root"):
            gate._validated_subprocess_path(
                str(tmp_path / "operations"), str(tmp_path / "no-such-root"))

    def test_denial_has_zero_durable_side_effects(self, tmp_path):
        before = sorted(p.name for p in tmp_path.rglob("*"))
        with pytest.raises(RuntimeError):
            gate._validated_subprocess_path(
                str(tmp_path / ".." / "x"), str(tmp_path))
        after = sorted(p.name for p in tmp_path.rglob("*"))
        assert before == after


# --------------------------------------------------------------------- #
# pg-recovery / pg-verify APPROVED-ROOT CONTAINMENT (B4-CXR7U9R12)
# --------------------------------------------------------------------- #

class TestApprovedRootArtifactInputs:
    """Artifact paths are contained: the approved roots are the program
    identity (engine directory plus the engine's own var/recovery state
    directory) plus operator-declared OCE_BACKUP_ROOTS. A CLI argument
    can never approve its own containment root."""

    @pytest.fixture(autouse=True)
    def _approve_tmp_root(self, tmp_path, monkeypatch):
        monkeypatch.setenv("OCE_BACKUP_ROOTS", str(tmp_path))
        self.root = tmp_path

    def test_regular_file_accepted_and_canonical(self, tmp_path):
        f = tmp_path / "inventory.json"
        f.write_text("{}")
        for mod in (pgrec, pgver):
            out = mod._validated_open_path(str(f))
            assert Path(out) == Path(os.path.realpath(str(f)))

    @needs_symlink
    def test_symlink_file_rejected(self, tmp_path):
        real = tmp_path.parent / "real-inv-u9r7.json"
        real.write_text("{}")
        link = tmp_path / "inventory.json"
        os.symlink(str(real), str(link))
        try:
            for mod in (pgrec, pgver):
                with pytest.raises(RuntimeError, match="symlink indirection"):
                    mod._validated_open_path(str(link))
        finally:
            link.unlink()

    def test_missing_path_rejected(self, tmp_path):
        for mod in (pgrec, pgver):
            with pytest.raises(RuntimeError, match="not a regular file"):
                mod._validated_open_path(str(tmp_path / "nope.json"))

    def test_wrong_type_directory_rejected(self, tmp_path):
        d = tmp_path / "adir"
        d.mkdir()
        for mod in (pgrec, pgver):
            with pytest.raises(RuntimeError, match="not a regular file"):
                mod._validated_open_path(str(d))

    def test_path_outside_every_approved_root_rejected(self, tmp_path):
        f = tmp_path.parent / "outside-approved-roots.json"
        f.write_text("{}")
        try:
            for mod in (pgrec, pgver):
                with pytest.raises(RuntimeError, match="approved backup root"):
                    mod._validated_open_path(str(f))
        finally:
            f.unlink()

    def test_empty_roots_reject_everything(self, tmp_path, monkeypatch):
        monkeypatch.setenv("OCE_BACKUP_ROOTS", "")
        f = tmp_path / "inventory.json"
        f.write_text("{}")
        for mod in (pgrec, pgver):
            with pytest.raises(RuntimeError, match="approved backup root"):
                mod._validated_open_path(str(f))

    def test_cli_argument_cannot_approve_its_own_root(self, tmp_path, monkeypatch):
        # A root named in the artifact's own path (or any argv channel)
        # grants nothing: only the engine directory and OCE_BACKUP_ROOTS
        # are consulted. A rogue directory outside both is rejected even
        # when the artifact path "looks" absolute and canonical.
        rogue = tmp_path.parent / "rogue-u9r12"
        rogue.mkdir(exist_ok=True)
        f = rogue / "inventory.json"
        f.write_text("{}")
        monkeypatch.setenv("OCE_BACKUP_ROOTS", str(tmp_path))
        for mod in (pgrec, pgver):
            with pytest.raises(RuntimeError, match="approved backup root"):
                mod._validated_open_path(str(f))
