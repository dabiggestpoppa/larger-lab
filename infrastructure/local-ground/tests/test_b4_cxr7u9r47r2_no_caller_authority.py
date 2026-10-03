#!/usr/bin/env python3
"""B4-CXR7U9R47R2 - NO public CLI argument can declare its own authority root.

R46 shipped `--classify-state <arbitrary path>`, which opened whatever file it
was handed and passed `os.path.dirname(path)` down as the transition authority
root: a caller could create a CREATED-shaped record inside a directory it owned,
name that directory, and be told it held FRESH rollback authority (exit 0) --
against an authority root it had itself manufactured. `--transition-dir` then
let the same caller name ANY directory as the authority root for an otherwise
ordinary `--classify-rollback`.

Both surfaces are gone. These proofs show the absence is real, not advisory:

* the two arguments are no longer parsed at all (usage error, exit 2);
* an attacker-authored record AND a matching attacker-authored selector in an
  attacker-authored directory are invisible to the engine, which derives its
  own root and therefore finds nothing;
* no classification entry point accepts a directory, at any call depth;
* the valid canonical production route still succeeds;
* every denial leaves the durable world byte-identical -- no receipt, no
  container call, no authority mutation, no mutation outside the governed tree.
"""
import ast
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from test_b4_cxr7u9r47r1_authority_snapshot import (  # noqa: F401
    CLI, OPID, _build, _claim_doc, _census, _publish, pgrec)

ENGINE = Path(pgrec.__file__).resolve()


def _cli(*args, env_root=None):
    return subprocess.run([sys.executable, str(CLI), *args],
                          capture_output=True, text=True, timeout=60,
                          env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})


ATTACKER_OPID = "f" * 32



def _attacker_tree(tmp_path, name, transition=None):
    """A complete, internally CONSISTENT operation tree an attacker owns."""
    root = tmp_path / name
    transitions = root / "transitions"
    transitions.mkdir(parents=True)
    promote = {
        "format": pgrec.RECEIPT_FORMAT, "operation_phase": "promote",
        "exit_status": 0, "promoted": True, "operation_id": ATTACKER_OPID,
        "database": pgrec.DB, "user": pgrec.USER, "container": pgrec.CONTAINER,
        "source_commit": "a" * 40, "source_tree": "b" * 40,
        "run_id": "0123456789abcdef", "stamp": "0123456789ab",
        "quarantine_database": pgrec.QUARANTINE_PREFIX + "0123456789ab",
        "staging_database": pgrec.STAGING_PREFIX + "0123456789ab",
        "source_archive_sha256": "c" * 64, "inventory_sha256": "d" * 64,
    }
    record = {
        "format": pgrec.TRANSITION_FORMAT, "state": "PROMOTED",
        "operation_id": ATTACKER_OPID, "selected_transition": None,
        "receipt_sha256": pgrec._receipt_digest(promote),
    }
    for key in ("database", "user", "container", "source_commit", "source_tree",
                "run_id", "stamp", "quarantine_database", "staging_database",
                "source_archive_sha256", "inventory_sha256"):
        record[key] = promote[key]
    (transitions / f"{ATTACKER_OPID}.json").write_text(
        json.dumps(record), encoding="utf-8")
    os.chmod(transitions / f"{ATTACKER_OPID}.json", 0o600)
    receipt = root / "promote-receipt.json"
    receipt.write_text(json.dumps(promote), encoding="utf-8")
    os.chmod(receipt, 0o600)
    if transition:
        # written under the ATTACKER's own operation id, in the
        # attacker's own directory: a complete, self-consistent world
        claim = transitions / f"{ATTACKER_OPID}.claim"
        claim.write_text(json.dumps({
            "format": pgrec._CLAIM_FORMAT,
            "operation_id": ATTACKER_OPID, "transition": transition,
            "receipt_sha256": pgrec._receipt_digest(promote),
            "claimed_at": "2026-09-24T00:00:00Z"}), encoding="utf-8")
        os.chmod(claim, 0o600)
    return root, transitions, record, promote, receipt


# --------------------------------------------------------------------- #
# the two authority-bearing arguments no longer exist
# --------------------------------------------------------------------- #

@pytest.mark.parametrize("argument", ["--classify-state", "--transition-dir"])
def test_authority_bearing_arguments_are_not_recognised(tmp_path, argument):
    """A caller that still tries to declare its own authority root gets a usage
    error, not a decision."""
    result = _cli(argument, str(tmp_path))
    assert result.returncode == 2, (result.returncode, result.stdout,
                                    result.stderr)
    assert "USAGE_ERROR" in result.stderr


def test_arbitrary_record_path_cannot_return_fresh_authority(tmp_path,
                                                             monkeypatch):
    """The attacker record + matching attacker selector, in an attacker
    directory: the engine derives its own governed root, so this whole tree is
    invisible and nothing about it is consumable."""
    monkeypatch.setenv("OCE_BACKUP_ROOTS", str(tmp_path))
    _root, transitions, _attacker_record, _promote, receipt = _attacker_tree(
        tmp_path, "attacker", transition="rollback")
    # bind the engine to a DIFFERENT, genuinely governed root
    _build(tmp_path / "engine", "PROMOTED", "rollback")
    before = _census(transitions)
    # The attacker's record names ITS OWN operation id, and the engine's
    # derived governed root holds no durable record for it. The production
    # route binds receipt-to-record before anything else, so the whole
    # attacker tree is unreachable.
    verdict = pgrec._classify_rollback_for_shell(str(receipt))
    assert verdict == 4, ("an attacker-authored operation in an "
                          "attacker-authored directory is not authority")
    assert _census(transitions) == before
    assert (transitions / f"{ATTACKER_OPID}.claim").exists(), (
        "the attacker selector really was published; the refusal above is "
        "therefore not the trivial 'nothing there' answer")


@pytest.mark.parametrize("shape", ["absolute", "prefix_sibling", "dotdot"])
def test_every_alternate_directory_shape_is_refused(tmp_path, monkeypatch,
                                                    shape):
    """An attacker-chosen root is refused in every shape it can be written in:
    an unrelated absolute directory, a PREFIX SIBLING of the real root
    (`.../transitions-evil` next to `.../transitions`), and a `..` escape out of
    the real root. None of them is a way to name an authority root, because
    there is no argument left to name one with."""
    monkeypatch.setenv("OCE_BACKUP_ROOTS", str(tmp_path))
    _build(tmp_path / "engine", "PROMOTED", "rollback")
    governed = Path(pgrec._transitions_dir())
    if shape == "absolute":
        attacker = tmp_path / "somewhere" / "else"
    elif shape == "prefix_sibling":
        attacker = Path(str(governed) + "-evil")
    else:
        attacker = governed.parent / ".." / "escaped"
    attacker.mkdir(parents=True, exist_ok=True)
    result = _cli("--classify-rollback",
                  str(tmp_path / "engine" / "governed-recovery"
                      / "promote-receipt.json"),
                  "--transition-dir", str(attacker))
    assert result.returncode == 2, (result.returncode, result.stdout,
                                    result.stderr)
    assert "USAGE_ERROR" in result.stderr


@pytest.mark.skipif(os.name == "nt",
                    reason="Windows requires elevation for directory symlinks; "
                           "the POSIX CI run exercises this exact window")
def test_symlinked_transition_directory_is_refused(tmp_path, monkeypatch):
    """A symlinked governed directory is refused by the admission itself."""
    monkeypatch.setenv("OCE_BACKUP_ROOTS", str(tmp_path))
    transitions, _record, _promote, _receipt = _build(
        tmp_path / "engine", "PROMOTED", "rollback")
    root = transitions.parent
    elsewhere = tmp_path / "elsewhere" / "transitions"
    elsewhere.mkdir(parents=True)
    linked = root / "linked-transitions"
    try:
        os.symlink(str(elsewhere), str(linked), target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("directory symlinks unavailable on this platform")
    with pytest.raises(pgrec._ExecutionAuthorityConflict):
        pgrec._open_governed_directory(str(linked), OPID)
    assert pgrec._open_governed_directory(str(transitions), OPID) is not None


def test_the_canonical_production_route_still_succeeds(tmp_path, monkeypatch):
    """Removing the caller-declared root must not remove the real capability:
    the canonical, engine-derived route still returns its exact verdict."""
    monkeypatch.setenv("OCE_BACKUP_ROOTS", str(tmp_path))
    _transitions, _record, _promote, receipt = _build(
        tmp_path / "engine", "PROMOTED", "rollback")
    # the production route: receipt bound to the durable record, selector bound
    # to that receipt, branch selected -> explicit rollback resume (6)
    assert pgrec._classify_rollback_for_shell(str(receipt)) == 6
    # the private record seam, with NO receipt to bind against, must NOT call a
    # spent selector fresh -- it fails closed (4), exactly as before R47
    durable = json.loads(
        (Path(pgrec._transitions_dir()) / f"{OPID}.json").read_text(
            encoding="utf-8"))
    assert pgrec._test_classify_state_for_shell(durable) == 4


# --------------------------------------------------------------------- #
# no classification entry point accepts a directory, at any call depth
# --------------------------------------------------------------------- #

CLASSIFICATION_SURFACE = [
    "_classify_record_for_shell", "_test_classify_state_for_shell",
    "_classify_rollback_for_shell", "_classify_claim_content",
    "_valid_transition_claim", "_selector_agrees_with_finalizing",
    "_receiptless_selector_agrees", "_claim_state", "_load_claim",
    "_load_transition_record", "_read_selector_snapshot",
    "_read_selector_snapshot_admitted", "_acquire_recovery_authority",
    "_bound_operation", "_derive_claim_coordinate",
]


def test_no_classification_entry_point_accepts_a_directory():
    """A collection/static proof over the shipped source: not one function on
    the classification path takes a `transition_dir` (or any other) parameter,
    so no caller -- CLI, receipt or internal -- can supply an authority root."""
    tree = ast.parse(ENGINE.read_text(encoding="utf-8"))
    functions = {node.name: node for node in ast.walk(tree)
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert set(CLASSIFICATION_SURFACE) <= set(functions), (
        "a classification surface function disappeared; the proof must be "
        "re-pointed, not deleted")
    offenders = {}
    for name in CLASSIFICATION_SURFACE:
        node = functions[name]
        args = [a.arg for a in node.args.args + node.args.kwonlyargs]
        if "transition_dir" in args:
            offenders[name] = args
    assert not offenders, ("a classification surface still accepts a caller "
                          "authority root", offenders)
    # and the parsed CLI does not know the two arguments at all
    source = ENGINE.read_text(encoding="utf-8")
    assert '"--transition-dir"' not in source
    assert '"--classify-state"' not in source


def test_every_denial_leaves_the_durable_world_byte_identical(tmp_path,
                                                              monkeypatch):
    """Zero filesystem, database, container, receipt or authority mutation on
    the denial paths: the whole disposable tree hashes identically before and
    after, and no container call is even attempted."""
    monkeypatch.setenv("OCE_BACKUP_ROOTS", str(tmp_path))
    _root, attacker_transitions, attacker_record, _promote, attacker_receipt = \
        _attacker_tree(tmp_path, "attacker", transition="rollback")
    _build(tmp_path / "engine", "PROMOTED", "rollback")
    before = _census(tmp_path)

    def boom(*_a, **_k):
        raise AssertionError("a denial must not reach a container")

    for name in ("docker_exec", "psql", "psql_ok", "docker_exec_ok",
                 "_quarantine_present", "db_exists", "rename_db", "drop_db"):
        monkeypatch.setattr(pgrec, name, boom)

    assert pgrec._classify_rollback_for_shell(str(attacker_receipt)) == 4
    assert attacker_record["operation_id"] == ATTACKER_OPID
    for argument in ("--classify-state", "--transition-dir"):
        assert _cli(argument, str(attacker_transitions)).returncode == 2
    assert _census(tmp_path) == before
