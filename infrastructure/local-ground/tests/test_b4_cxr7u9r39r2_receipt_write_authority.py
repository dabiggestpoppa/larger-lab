#!/usr/bin/env python3
"""B4-CXR7U9R39-R2 — receipt-WRITE authority and collision-safe persistence.

R37 contained `--receipt-out` to a directory the CALLER could name through
OCE_RECOVERY_STATE_DIR, so an ambient runtime environment could grant arbitrary
write authority merely by naming a directory, and the commit used a predictable
`target + ".tmp"` name and `os.replace`, so an existing receipt was silently
replaced. These proofs cover the authority and the persistence:

* AUTHORITY: the write root is PROGRAM IDENTITY (`<program root>/var/recovery`).
  A hostile environment cannot widen it; an arbitrary outside path, a dot-dot
  escape and a prefix sibling are all refused before any destructive step;
* the alternate-storage seam is CONSTRUCTED BY THE TEST in process, is not
  reachable from the CLI, and does not read any environment variable;
* PERSISTENCE: no symlink indirection in the target or in a parent component, a
  collision-resistant exclusively created temporary, restrictive permissions,
  flush before commit, exclusive commit (an existing receipt is REFUSED, never
  silently replaced), temporary and partial residue cleaned on every failure,
  and a previous receipt preserved byte-identical on denial;
* ALIASING: a receipt may not be both the transition authority and its own
  output.
"""
import importlib.util
import json
import os
import stat
import sys
from pathlib import Path

import pytest

import recovery_cli

TESTS = Path(__file__).resolve().parent
SCRIPTS = TESTS.parent / "scripts"
CLI = SCRIPTS / "pg-recovery.py"
GOVERNED_ROOT = SCRIPTS.parent / "var" / "recovery"

INVENTORY_DOC = ('{"format": "oce-pg-inventory-v1", "database": "oce_local",'
                 ' "table_count": 1, "tables": [{"name": "public.widgets",'
                 ' "row_count": 3, "fingerprint": "deadbeef"}]}')


def _load_engine():
    spec = importlib.util.spec_from_file_location("u39r2_pgrec", str(CLI))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["u39r2_pgrec"] = mod
    spec.loader.exec_module(mod)
    return mod


pgrec = _load_engine()

SYMLINKS_OK = True
try:
    _probe = Path(__file__).resolve().parent / ".symlink-probe"
    _probe.symlink_to(Path(__file__).resolve().parent)
    _probe.unlink()
except (OSError, NotImplementedError, AttributeError):  # pragma: no cover - platform
    SYMLINKS_OK = False


def _inputs(tmp_path):
    """An approved backup root holding a valid inventory, plus the exact
    spelling of an artifact that is NOT inside any approved root - so a promote
    refuses at the archive step, record the refusal, and needs no container."""
    roots = tmp_path / "roots"
    roots.mkdir()
    inv = roots / "inventory.json"
    inv.write_text(INVENTORY_DOC, encoding="utf-8")
    sha = roots / "inventory.sha256"
    import hashlib
    sha.write_text(hashlib.sha256(INVENTORY_DOC.encode()).hexdigest(), encoding="utf-8")
    hostile = tmp_path / "outside.dump"
    hostile.write_bytes(b"PGDMP")
    return roots, inv, sha, hostile


def _promote_argv(hostile, inv, sha, receipt):
    return ["--phase", "promote", "--archive", str(hostile),
            "--inventory", str(inv), "--inventory-sha", str(sha),
            "--receipt-out", str(receipt)]


def _residue(directory):
    return sorted(p.name for p in Path(directory).iterdir()
                  if p.name.endswith(".tmp") or p.name.startswith(".oce-receipt-"))


# --------------------------------------------------------------------- #
# AUTHORITY: the environment cannot grant the write root
# --------------------------------------------------------------------- #

def test_hostile_recovery_state_dir_cannot_grant_write_authority(tmp_path, monkeypatch):
    """The former escape hatch is gone: naming a directory in the environment
    neither moves the write root nor makes a write there succeed."""
    roots, inv, sha, hostile = _inputs(tmp_path)
    monkeypatch.setenv("OCE_BACKUP_ROOTS", str(roots))
    hostile_state = tmp_path / "hostile-state"
    hostile_state.mkdir()
    monkeypatch.setenv("OCE_RECOVERY_STATE_DIR", str(hostile_state))

    # the root the engine will actually use is program identity, unchanged
    assert pgrec._recovery_state_dir() == os.path.realpath(str(GOVERNED_ROOT))
    assert not hasattr(pgrec, "RECEIPT_STATE_ENV"), \
        "the ambient receipt-root escape hatch must not exist"

    target = hostile_state / "receipt.json"
    r = recovery_cli.run_cli(_promote_argv(hostile, inv, sha, target))
    assert r.returncode == 2, (r.returncode, r.stdout, r.stderr)
    assert "outside the recovery state directory" in r.stderr, r.stderr
    assert not target.exists(), "a hostile environment granted write authority"
    assert not _residue(hostile_state), _residue(hostile_state)


def test_seam_is_explicit_and_cannot_change_the_production_default(tmp_path):
    """The alternate-storage seam exists, but only for a caller that constructs
    it in process; unbinding restores program identity."""
    default = os.path.realpath(str(GOVERNED_ROOT))
    assert pgrec._recovery_state_dir() == default
    pgrec._bind_test_recovery_root(str(tmp_path))
    try:
        assert pgrec._recovery_state_dir() == os.path.realpath(str(tmp_path))
    finally:
        pgrec._unbind_test_recovery_root()
    assert pgrec._recovery_state_dir() == default


@pytest.mark.parametrize("kind", ["outside", "dot-dot", "prefix-sibling"])
def test_receipt_output_outside_the_governed_root_is_refused(tmp_path, kind):
    roots, inv, sha, hostile = _inputs(tmp_path)
    state = tmp_path / "state"
    state.mkdir()
    sibling = tmp_path / "state-evil"
    sibling.mkdir()
    if kind == "outside":
        target = tmp_path / "outside.json"
    elif kind == "dot-dot":
        target = state / ".." / ".." / "escape.json"
    else:
        target = sibling / "receipt.json"
    r = recovery_cli.run_cli(_promote_argv(hostile, inv, sha, target),
                             write_root=state,
                             env_extra={"OCE_BACKUP_ROOTS": str(roots)})
    assert r.returncode == 2, (r.returncode, r.stdout, r.stderr)
    assert "outside the recovery state directory" in r.stderr, r.stderr
    assert not os.path.exists(target), target


def test_symlinked_directory_component_is_refused(tmp_path):
    if not SYMLINKS_OK:
        pytest.skip("symlink creation requires privilege on this platform")
    roots, inv, sha, hostile = _inputs(tmp_path)
    state = tmp_path / "state"
    state.mkdir()
    real = tmp_path / "real-sub"
    real.mkdir()
    link = state / "sub"
    os.symlink(str(real), str(link))
    target = link / "receipt.json"
    r = recovery_cli.run_cli(_promote_argv(hostile, inv, sha, target),
                             write_root=state,
                             env_extra={"OCE_BACKUP_ROOTS": str(roots)})
    assert r.returncode == 2, (r.returncode, r.stdout, r.stderr)
    assert "symlink indirection" in r.stderr, r.stderr
    assert not (real / "receipt.json").exists()
    assert not _residue(real) and not _residue(state)


def test_symlinked_target_is_refused_and_its_pointee_untouched(tmp_path):
    if not SYMLINKS_OK:
        pytest.skip("symlink creation requires privilege on this platform")
    roots, inv, sha, hostile = _inputs(tmp_path)
    state = tmp_path / "state"
    state.mkdir()
    outside = tmp_path / "outside-target.json"
    outside.write_text('{"authoritative": true}', encoding="utf-8")
    link = state / "receipt.json"
    os.symlink(str(outside), str(link))
    r = recovery_cli.run_cli(_promote_argv(hostile, inv, sha, link),
                             write_root=state,
                             env_extra={"OCE_BACKUP_ROOTS": str(roots)})
    assert r.returncode == 2, (r.returncode, r.stdout, r.stderr)
    assert outside.read_text(encoding="utf-8") == '{"authoritative": true}'


def test_precreated_predictable_temporary_is_never_used(tmp_path):
    """A caller that pre-creates the OLD predictable temporary name (and a
    symlink to a victim) must not influence where bytes land."""
    if not SYMLINKS_OK:
        pytest.skip("symlink creation requires privilege on this platform")
    roots, inv, sha, hostile = _inputs(tmp_path)
    state = tmp_path / "state"
    state.mkdir()
    victim = tmp_path / "victim.json"
    victim.write_text('{"victim": true}', encoding="utf-8")
    target = state / "receipt.json"
    planted = state / "receipt.json.tmp"  # the ATTACK's own artifact
    os.symlink(str(victim), str(planted))
    r = recovery_cli.run_cli(_promote_argv(hostile, inv, sha, target),
                             write_root=state,
                             env_extra={"OCE_BACKUP_ROOTS": str(roots)})
    assert r.returncode == 1, (r.returncode, r.stdout, r.stderr)
    assert target.is_file() and not target.is_symlink(), "receipt not committed"
    assert json.loads(target.read_text(encoding="utf-8"))["format"] == pgrec.RECEIPT_FORMAT
    assert victim.read_text(encoding="utf-8") == '{"victim": true}'
    # the planted symlink is the test's own input, not engine residue: the
    # engine must have neither followed nor removed it
    assert planted.is_symlink()
    assert "receipt.json.tmp" in _residue(state), _residue(state)
    engine_residue = [name for name in _residue(state)
                      if name != "receipt.json.tmp"]
    assert not engine_residue, engine_residue


# --------------------------------------------------------------------- #
# PERSISTENCE: overwrite policy, atomicity, permissions, residue
# --------------------------------------------------------------------- #

def test_existing_receipt_is_refused_before_any_destructive_step(tmp_path):
    roots, inv, sha, hostile = _inputs(tmp_path)
    state = tmp_path / "state"
    state.mkdir()
    target = state / "receipt.json"
    target.write_bytes(b'{"prior": "authoritative"}')
    r = recovery_cli.run_cli(_promote_argv(hostile, inv, sha, target),
                             write_root=state,
                             env_extra={"OCE_BACKUP_ROOTS": str(roots)})
    assert r.returncode == 2, (r.returncode, r.stdout, r.stderr)
    assert "refusing to overwrite an existing receipt" in r.stderr, r.stderr
    assert target.read_bytes() == b'{"prior": "authoritative"}'
    assert not _residue(state), _residue(state)


def test_commit_refuses_an_existing_target_and_preserves_it(tmp_path):
    target = tmp_path / "receipt.json"
    target.write_text("prior", encoding="utf-8")
    with pytest.raises(RuntimeError, match="refusing to overwrite"):
        pgrec._commit_receipt(str(target), {"format": pgrec.RECEIPT_FORMAT})
    assert target.read_text(encoding="utf-8") == "prior"
    assert not _residue(tmp_path), _residue(tmp_path)


def test_interrupted_write_leaves_the_previous_receipt_intact(tmp_path):
    target = tmp_path / "receipt.json"
    target.write_text('{"previous": "complete"}', encoding="utf-8")
    with pytest.raises(TypeError):
        pgrec._commit_receipt(str(target), {"unserializable": object()})
    assert target.read_text(encoding="utf-8") == '{"previous": "complete"}'
    assert not _residue(tmp_path), _residue(tmp_path)


def test_interrupted_write_creates_nothing_when_nothing_was_there(tmp_path):
    target = tmp_path / "absent.json"
    with pytest.raises(TypeError):
        pgrec._commit_receipt(str(target), {"unserializable": object()})
    assert not target.exists()
    assert list(tmp_path.iterdir()) == []


def test_successful_commit_is_complete_restricted_and_residue_free(tmp_path):
    target = tmp_path / "receipt.json"
    pgrec._commit_receipt(str(target), {"format": pgrec.RECEIPT_FORMAT, "exit_status": 0})
    assert json.loads(target.read_text(encoding="utf-8")) == {
        "format": pgrec.RECEIPT_FORMAT, "exit_status": 0}
    assert list(tmp_path.iterdir()) == [target], "residue after a successful commit"
    if os.name == "posix":
        mode = stat.S_IMODE(target.stat().st_mode)
        assert mode & 0o077 == 0, oct(mode)


def test_receipt_in_and_receipt_out_aliasing_is_refused(tmp_path):
    roots, inv, sha, hostile = _inputs(tmp_path)
    state = tmp_path / "state"
    state.mkdir()
    same = state / "receipt.json"
    same.write_text(json.dumps({"format": pgrec.RECEIPT_FORMAT,
                                "operation_phase": "promote"}), encoding="utf-8")
    r = recovery_cli.run_cli(["--phase", "finalize", "--receipt-in", str(same),
                              "--inventory", str(inv), "--inventory-sha", str(sha),
                              "--receipt-out", str(same)],
                             write_root=state,
                             env_extra={"OCE_BACKUP_ROOTS": str(roots)})
    assert r.returncode == 2, (r.returncode, r.stdout, r.stderr)
    assert "same file" in r.stderr, r.stderr
    assert json.loads(same.read_text(encoding="utf-8"))["operation_phase"] == "promote"
