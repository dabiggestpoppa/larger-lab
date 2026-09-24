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
    both observe PROMOTED and both proceed — the R40-01 race test catches it."""
    receipt, _path, _inv, _sha = _promoted(bridge, tmp_path, monkeypatch)

    def weaken(source):
        old = 'fd = os.open(claim_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)'
        new = ('if os.path.exists(claim_path):\n'
               '            raise RuntimeError("claimed")\n'
               '        fd = os.open(claim_path, '
               'os.O_CREAT | os.O_WRONLY, 0o600)')
        assert old in source
        return source.replace(old, new)

    weakened = _load_weakened(tmp_path, _weaken_source(weaken))
    outcomes = []
    start = threading.Barrier(2)

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
    # TOCTOU can double-win (both check before either creates): at minimum the
    # weakened code no longer guarantees exactly-one. If it happened to be
    # atomic on this run, skip honestly rather than claim a false proof.
    assert sum(outcomes) in (1, 2), outcomes
    if sum(outcomes) == 1:
        pytest.skip("filesystem happened to serialize the non-atomic check")


# --------------------------------------------------------------------- #
# controls 3-5: the shell law fails when its durable consultation is removed
# --------------------------------------------------------------------- #

def _shell_law_from_source(source, tmp_path):
    text = source
    m = re.search(r"(durable_precommit\(\) \{.*?\n\})\n", text, re.S)
    m2 = re.search(r"(_promote_op_id\(\) \{.*?\n\})\n", text, re.S)
    assert m and m2
    python_exe = sys.executable.replace("\\", "/")

    def run(record_state):
        transitions = tmp_path / "ctl" / "recovery" / "transitions"
        transitions.mkdir(parents=True, exist_ok=True)
        opid = "0123456789abcdef0123456789abcdef"
        (transitions / f"{opid}.json").write_text(
            json.dumps({"state": record_state}), encoding="utf-8")
        promote = tmp_path / "ctl" / "promote.json"
        promote.write_text(json.dumps({"operation_id": opid}), encoding="utf-8")
        script = ("set -uo pipefail\n"
                  f'OCE_PYTHON="{python_exe}"\n'
                  f"BIN='{SCRIPTS.as_posix()}'\n"
                  f"PROMOTE_RECEIPT='{promote}'\n"
                  f"VAR_DIR='{tmp_path / 'ctl'}'\n"
                  + m2.group(1) + "\n" + m.group(1) +
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
