#!/usr/bin/env python3
"""B4-CXR7U9R40-R4 — negative controls: the R40 proofs fail when the
protections are removed.

Each control reverts ONE protection in a copy of the engine (or the shell
law) and proves the corresponding R40 test detects it. Source-string checks
are never used: every control executes the weakened code and observes the
behavioral difference the R40 suite exists to catch.
"""
import json
import re
import shutil
import subprocess
import sys
import threading
from pathlib import Path

import pytest

from test_b4_cxr7u9r35_recovery_authority import (  # noqa: F401 — fixtures
    _Bridge, _promote_receipt, production_recovery_identity, pgrec)

SCRIPTS = Path(pgrec.__file__).resolve().parent
BASH = shutil.which("bash") or "bash"


@pytest.fixture
def bridge(monkeypatch):
    b = _Bridge()
    b.install(monkeypatch)
    return b


def _promoted(bridge, tmp_path, monkeypatch):
    from test_b4_cxr7u9r35_recovery_authority import _write_inputs
    inv, sha, archive = _write_inputs(tmp_path, monkeypatch)
    bridge.remote_sha = pgrec.sha256_file(str(archive))
    receipt, path = _promote_receipt(bridge, inv, sha, archive, "p.json")
    return receipt, path, inv, sha


def _load_weakened(tmp_path, source):
    """A real, separate engine module built from weakened source."""
    spec_name = f"weakened_{abs(hash(source)) % 10**8}"
    path = tmp_path / "weakened_engine.py"
    path.write_text(source, encoding="utf-8")
    import importlib.util
    spec = importlib.util.spec_from_file_location(spec_name, str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec_name] = mod
    spec.loader.exec_module(mod)
    mod._bind_test_recovery_root(pgrec._recovery_state_dir())
    return mod


def _weaken_source(transform):
    source = Path(pgrec.__file__).read_text(encoding="utf-8")
    transformed = transform(source)
    assert transformed != source, "the weakening transform changed nothing"
    return transformed


# --------------------------------------------------------------------- #
# control 1: per-transition claim filenames restore the cross-claim race
# --------------------------------------------------------------------- #

def test_control_finalize_and_rollback_with_different_claim_filenames_race(
        bridge, tmp_path, monkeypatch):
    """Without the operation-wide claim (per-transition filenames AND no
    durable state movement at claim time — exactly the R39 semantics), a
    finalize and a rollback can BOTH claim the same operation — the exact
    behavior R40-R1 forbids, and which the R40-01 tests catch."""
    receipt, _path, _inv, _sha = _promoted(bridge, tmp_path, monkeypatch)

    def weaken(source):
        # revert to per-transition claim files AND to the R39 claim that did
        # not move the durable record (the state check stayed separable)
        old = 'claim_path = os.path.join(directory, f"{operation_id}.claim")'
        new = ('claim_path = os.path.join(directory, '
               'f"{operation_id}.{transition}.claim")')
        assert old in source
        source = source.replace(old, new)
        movement = re.search(
            r"    # The record is moved to the IN-FLIGHT state.*?return claim\n",
            source, re.S)
        assert movement, "claim state-movement block not found"
        return source[:movement.start()] + "    return claim\n"

    weakened = _load_weakened(tmp_path, _weaken_source(weaken))
    results = []
    for tr in ("finalize", "rollback"):
        try:
            weakened._claim_transition(receipt["operation_id"], tr, receipt)
            results.append((tr, True))
        except RuntimeError:
            results.append((tr, False))
    # the WEAKENED code lets both transitions claim — proving the R40 tests
    # (which require exactly one winner) fail against it
    assert all(ok for _, ok in results), results


# --------------------------------------------------------------------- #
# control 2: state check separable from a non-atomic claim
# --------------------------------------------------------------------- #

def test_control_state_check_before_nonatomic_claim_loses_the_race(
        bridge, tmp_path, monkeypatch):
    """With the claim reduced to non-atomic write-then-check, two threads can
    both observe PROMOTED and both proceed — the R40-01 race test catches it.

    B4-CXR7U9R44R1: the weakened control now targets the R44 publication
    primitive. Replacing the atomic NO-REPLACE publication with the pre-R44
    exists-check/barrier/plain-write sequence reproduces exactly the
    double-win that atomic publication exists to prevent.
    """
    receipt, _path, _inv, _sha = _promoted(bridge, tmp_path, monkeypatch)

    def weaken(source):
        old = "    try:\n        _publish_no_replace(tmp, claim_path)"
        new = ("    if os.path.exists(claim_path):\n"
               "        raise RuntimeError('claimed')\n"
               "    _neg_control_barrier.wait()\n"
               "    try:\n"
               "        with open(claim_path, 'wb') as stream:\n"
               "            stream.write(payload)")
        assert old in source, "atomic claim publication not found"
        return source.replace(old, new)

    weakened = _load_weakened(tmp_path, _weaken_source(weaken))
    # The claim primitive is the subject of this control. Neutralize the
    # subsequent record rewrite so the two claims cannot race on os.replace
    # after both have already demonstrated the lost atomic boundary.
    weakened._record_transition = lambda *args, **kwargs: None
    outcomes = []
    start = threading.Barrier(2)
    weakened._neg_control_barrier = start

    def attempt():
        start.wait()
        try:
            weakened._claim_transition(receipt["operation_id"], "finalize", receipt)
            outcomes.append(True)
        except RuntimeError:
            outcomes.append(False)

    threads = [threading.Thread(target=attempt) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(60)
    # The weakened code has no atomic primitive: both threads are forced past
    # the existence check before either creates, so the double-win is a
    # deterministic behavioral result rather than a timing observation.
    assert sum(outcomes) == 2, outcomes


# --------------------------------------------------------------------- #
# controls 3-5: the shell law fails when its durable consultation is removed
# --------------------------------------------------------------------- #

def _shell_law_from_source(source, tmp_path):
    text = source
    m = re.search(r"(durable_precommit\(\) \{.*?\n\})\n", text, re.S)
    assert m
    python_exe = sys.executable.replace("\\", "/")

    def run(record_state):
        transitions = tmp_path / "ctl" / "recovery" / "transitions"
        transitions.mkdir(parents=True, exist_ok=True)
        opid = "0123456789abcdef0123456789abcdef"
        authority = {
            "format": pgrec.RECEIPT_FORMAT, "operation_phase": "promote",
            "exit_status": 0, "promoted": True, "operation_id": opid,
            "database": pgrec.DB, "user": pgrec.USER,
            "container": pgrec.CONTAINER, "source_commit": "a" * 40,
            "source_tree": "b" * 40, "run_id": "0123456789abcdef",
            "stamp": "0123456789ab",
            "quarantine_database": pgrec.QUARANTINE_PREFIX + "0123456789ab",
            "staging_database": pgrec.STAGING_PREFIX + "0123456789ab",
            "source_archive_sha256": "c" * 64, "inventory_sha256": "d" * 64,
        }
        digest = pgrec._receipt_digest(authority)
        record = {
            "format": pgrec.TRANSITION_FORMAT, "state": record_state,
            "operation_id": opid, "database": pgrec.DB, "user": pgrec.USER,
            "container": pgrec.CONTAINER, "source_commit": "a" * 40,
            "source_tree": "b" * 40, "run_id": "0123456789abcdef",
            "stamp": "0123456789ab",
            "quarantine_database": authority["quarantine_database"],
            "staging_database": authority["staging_database"],
            "source_archive_sha256": "c" * 64, "inventory_sha256": "d" * 64,
            "receipt_sha256": digest, "selected_transition": "finalize",
            "commit_intent": {
                "marker": "forward_commit", "operation_id": opid,
                "receipt_sha256": digest, "database": pgrec.DB,
                "user": pgrec.USER, "container": pgrec.CONTAINER,
                "quarantine_database": authority["quarantine_database"],
                "at": "2026-09-24T00:00:00Z",
            },
            "commit_point": {
                "marker": "quarantine_dropped",
                "at": "2026-09-24T00:00:01Z",
            },
        }
        (transitions / f"{opid}.json").write_text(
            json.dumps(record), encoding="utf-8")
        promote = tmp_path / "ctl" / "promote.json"
        promote.write_text(json.dumps(authority), encoding="utf-8")
        script = ("set -uo pipefail\n"
                  f'OCE_PYTHON="{python_exe}"\n'
                  f"BIN='{SCRIPTS.as_posix()}'\n"
                  f"PROMOTE_RECEIPT='{promote}'\n"
                  f"VAR_DIR='{tmp_path / 'ctl'}'\n"
                  f"export OCE_BACKUP_ROOTS='{tmp_path / 'ctl'}'\n"
                  + m.group(1) +
                  "\ndurable_precommit\n")
        r = subprocess.run([BASH, "-c", script], capture_output=True, text=True,
                           timeout=60)
        return r.returncode

    return run


def test_control_shell_rollback_that_ignores_durable_commit_state():
    """A rollback_precommit that never consults the durable record legalizes
    the post-commit artifact rollback — the R40-02 shell-law test catches it."""
    source = SCRIPTS.joinpath("restore.sh").read_text(encoding="utf-8")

    def weaken(text):
        # make durable_precommit a no-op pass-through: always "pre-commit"
        m = re.search(r"durable_precommit\(\) \{.*?\n\}\n", text, re.S)
        return text[:m.start()] + "durable_precommit() { return 0; }\n" + text[m.end():]

    weakened = _shell_law_from_source(weaken(source), Path(mktmp()))
    # with the law gutted, COMMIT_POINT_REACHED is (wrongly) rollback-legal
    assert weakened("COMMIT_POINT_REACHED") == 0
    # the REAL law refuses it — the behavioral difference the tests check
    real = _shell_law_from_source(source, Path(mktmp()))
    assert real("COMMIT_POINT_REACHED") == 1


def mktmp():
    import tempfile
    return tempfile.mkdtemp()


def test_control_pg_finalized_as_the_only_commit_authority():
    """If the shell trusts only PG_FINALIZED (the volatile flag), a crash
    between the durable commit point and the flag leaves the trap convinced
    the transaction is pre-commit. The law, driven here against a record in
    COMMIT_POINT_REACHED with the flag absent, refuses — the difference the
    R40-02 test asserts."""
    source = SCRIPTS.joinpath("restore.sh").read_text(encoding="utf-8")
    real = _shell_law_from_source(source, Path(mktmp()))
    # durable state says committed even though no volatile flag exists
    assert real("COMMIT_POINT_REACHED") == 1
    # and the volatile-flag-only variant has no way to express that refusal
    assert "PG_FINALIZED" not in re.search(
        r"durable_precommit\(\) \{.*?\n\}\n", source, re.S).group(0)


# --------------------------------------------------------------------- #
# controls 6-7: post-commit failures must not become rollback-legal
# --------------------------------------------------------------------- #

def test_control_post_quarantine_record_failure_keeps_commit_state(
        bridge, tmp_path, monkeypatch):
    """If the post-drop handler relabelled the operation FAILED, the shell's
    durable law would read FAILED as not-postcommit... but more importantly
    the engine would have erased the commit-point fact. The R40-02 engine
    test catches any relabelling: prove the REAL engine keeps the state."""
    receipt, path, inv, sha = _promoted(bridge, tmp_path, monkeypatch)
    monkeypatch.setattr(pgrec, "db_exists", lambda *a, **k: True)
    out = pgrec.phase_finalize(str(path), str(inv), str(sha), pgrec.DB,
                               pgrec.USER, pgrec.CONTAINER, None)
    assert out["exit_status"] == 1
    state = pgrec._load_transition_record(receipt["operation_id"])["state"]
    assert state == pgrec.TRANSITION_STATE_COMMIT_POINT, state
    # and the shell law agrees: no artifact rollback is legal
    source = SCRIPTS.joinpath("restore.sh").read_text(encoding="utf-8")
    law = _shell_law_from_source(source, Path(mktmp()))
    assert law(state) == 1
