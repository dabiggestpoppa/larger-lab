#!/usr/bin/env python3
"""B4-CXR7U9R47R3 - ANCHOR the governed directory BEFORE resolving any path.

R46's `_derive_claim_coordinate` ran `os.path.isdir(directory)` -- which FOLLOWS
a symlink -- and then `os.path.realpath(directory)`, and only afterwards called
`_open_governed_directory`. The no-follow proof was therefore applied to the
TARGET of a redirection rather than to the coordinate that was supplied: a
symlinked transition directory resolved to a perfectly ordinary real path and
was accepted.

R47 reverses the order. `_derive_claim_coordinate` performs no resolution at
all, and `_open_governed_directory` opens the ORIGINAL coordinate with
O_DIRECTORY|O_CLOEXEC|O_NOFOLLOW (POSIX) or refuses a reparse point against a
no-follow stat (Windows). These proofs include an executable red-green control:
the shipped form refuses the redirected directory, and restoring the R46
realpath-first form in a copy of the engine accepts exactly the same attack.
"""
import ast
import importlib.util
import os
from pathlib import Path

import pytest

from test_b4_cxr7u9r47r1_authority_snapshot import (  # noqa: F401
    CLI, OPID, _build, _claim_doc, _census, _publish, pgrec)

ENGINE = Path(pgrec.__file__).resolve()

DERIVE_SHIPPED = r'''    if not isinstance(operation_id, str) \
            or not OPERATION_ID_RE.match(operation_id):
        raise _ExecutionAuthorityConflict(
            "malformed operation id; refusing to derive a claim coordinate")
    return _transitions_dir(), f"{operation_id}.claim"
'''

DERIVE_REALPATH_FIRST_R46 = r'''    if not isinstance(operation_id, str) \
            or not OPERATION_ID_RE.match(operation_id):
        raise _ExecutionAuthorityConflict(
            "malformed operation id; refusing to derive a claim coordinate")
    directory = _transitions_dir()
    if not os.path.isdir(directory):
        raise _ExecutionAuthorityConflict(
            f"operation {operation_id} has no governed transition directory")
    return os.path.realpath(directory), f"{operation_id}.claim"
'''


def _load_engine(path=None):
    spec = importlib.util.spec_from_file_location(
        "pg_recovery_r47r3", str(path or CLI))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _realpath_first_engine(tmp_path):
    source = ENGINE.read_text(encoding="utf-8")
    assert DERIVE_SHIPPED in source, "the shipped coordinate derivation changed"
    changed = source.replace(DERIVE_SHIPPED, DERIVE_REALPATH_FIRST_R46)
    assert changed != source
    path = tmp_path / "realpath-first-pg-recovery.py"
    path.write_text(changed, encoding="utf-8")
    return path


def _redirect(transitions):
    """Replace the governed directory with a symlink to the real one."""
    root = transitions.parent
    real = root / "real-transitions"
    transitions.rename(real)
    try:
        os.symlink(str(real), str(transitions), target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory symlinks unavailable on this platform")
    return real


# --------------------------------------------------------------------- #
# the order itself
# --------------------------------------------------------------------- #

def test_coordinate_derivation_performs_no_path_resolution():
    """A collection proof over the shipped source: the function that derives
    the governed coordinate contains no realpath/isdir/abspath call at all, so
    there is no resolution a redirection could ride in on before admission."""
    tree = ast.parse(ENGINE.read_text(encoding="utf-8"))
    node = next(n for n in ast.walk(tree)
                if isinstance(n, ast.FunctionDef)
                and n.name == "_derive_claim_coordinate")
    called = {n.func.attr for n in ast.walk(node)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
    assert not called & {"realpath", "abspath", "isdir", "islink", "readlink"}, (
        "the coordinate must be returned unresolved; found", called)


def test_admission_opens_the_coordinate_without_following_a_redirection(
        tmp_path):
    """The shipped admission returns the identity of the directory it actually
    opened, and refuses a coordinate that is not that directory."""
    transitions, _record, _promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    governed, name = pgrec._derive_claim_coordinate(OPID)
    assert name == f"{OPID}.claim"
    assert governed == str(transitions), "the coordinate is returned as-is"
    dir_fd, identity = pgrec._open_governed_directory(governed, OPID)
    try:
        info = os.stat(transitions)
        assert identity == (info.st_dev, info.st_ino)
    finally:
        if dir_fd is not None:
            os.close(dir_fd)
    # the snapshot carries that same admitted identity
    authority = pgrec._acquire_recovery_authority(OPID)
    assert (authority.governed_device, authority.governed_inode) == identity


@pytest.mark.skipif(os.name == "nt",
                    reason="Windows requires elevation for directory symlinks; "
                           "the POSIX CI run exercises this exact window")
def test_realpath_first_form_accepts_the_redirected_directory_and_the_repair_refuses_it(
        tmp_path):
    """The red-green control. Restoring R46's realpath-first derivation makes the
    SAME symlinked coordinate admissible; the shipped form refuses it."""
    transitions, _record, _promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    real = _redirect(transitions)
    before = _census(real)

    weak = _load_engine(_realpath_first_engine(tmp_path))
    weak._bind_test_recovery_root(str(transitions.parent))
    laundered, _name = weak._derive_claim_coordinate(OPID)
    assert os.path.realpath(str(transitions)) == laundered, (
        "the weakened control must resolve the symlink to its target")
    dir_fd, _identity = weak._open_governed_directory(laundered, OPID)
    if dir_fd is not None:
        os.close(dir_fd)
    assert weak._read_selector_snapshot(OPID).present, (
        "the R46 form accepted the redirected directory and read through it")

    # the shipped form hands the redirection to the admission, which refuses it
    governed, _name = pgrec._derive_claim_coordinate(OPID)
    assert governed == str(transitions)
    assert os.path.islink(governed), "the coordinate really is a symlink"
    with pytest.raises(pgrec._ExecutionAuthorityConflict):
        pgrec._open_governed_directory(governed, OPID)
    assert _census(real) == before, (
        "neither form may mutate the redirected-to directory")


def test_a_non_directory_coordinate_is_refused(tmp_path):
    transitions, _record, _promote, _receipt = _build(
        tmp_path, "PROMOTED", "rollback")
    regular = transitions.parent / "not-a-directory"
    regular.write_text("plain", encoding="utf-8")
    with pytest.raises(pgrec._ExecutionAuthorityConflict):
        pgrec._open_governed_directory(str(regular), OPID)
    with pytest.raises(pgrec._ExecutionAuthorityConflict):
        pgrec._open_governed_directory(str(transitions.parent / "absent"), OPID)


def test_a_malformed_operation_id_is_refused_before_any_admission(tmp_path):
    _build(tmp_path, "PROMOTED", "rollback")
    for bad in ("", "not-hex", "A" * 32, "a" * 31, "a" * 33, None, 7):
        with pytest.raises(pgrec._ExecutionAuthorityConflict):
            pgrec._derive_claim_coordinate(bad)
