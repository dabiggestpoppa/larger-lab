#!/usr/bin/env python3
"""B4-CXR7U9R44X2 - the claim temporary lifecycle is adversary-proof.

The R44R1 sweep proved the claim publication crash boundaries, and the
R40R1 suite proved the two-thread claim race - but only with a discarder
that could not exist before R44R1 introduced private temporaries. When
CI raced two threads through the REAL engine (b1 run 36243225760), the
loser's discard deleted the winner's in-flight temporary: the winner
died with FileNotFoundError, the loser died with IndexError, and the
race produced NO winner at all.

These proofs drive the same interference with the real primitives, on
the real filesystem, and prove the strengthened protocol:

  * a live writer's temporary (its liveness lock held by a real,
    separate process) survives a real discarder sweep;
  * the discarder's own temporarily-held probe lock is never mistaken
    for a live writer's lock, and a free-lock temporary is removed;
  * a writer whose temporary is removed in the released window
    retreats and publishes anyway;
  * the R40R1 race still yields exactly one winner with a complete
    claim, and no private temporary or sidecar file survives it.
"""
import importlib.util
import json
import sys
import threading
import time
from pathlib import Path

import pytest

from test_b4_cxr7u9r35_recovery_authority import (  # noqa: F401 - fixtures
    _Bridge, _promote_receipt, production_recovery_identity, pgrec)

CLAIM_TEMP_LIVENESS_ATTEMPTS = 4

# A real, separate writer process: it creates one claim temporary through
# the REAL engine primitives, announces its path, then stays alive holding
# the liveness lock - exactly the state a racing attempt must respect.
_WRITER_SCRIPT = r'''
import json, sys, time
import importlib.util

spec = importlib.util.spec_from_file_location("r44x2_writer", sys.argv[1])
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
mod._bind_test_recovery_root(sys.argv[2])

fd, tmp, lockfd = mod._open_claim_temporary(sys.argv[4], mod._transitions_dir())
with open(sys.argv[3], "w", encoding="utf-8") as f:
    json.dump({"tmp": tmp}, f)
# Hold the liveness lock; the test process decides when this life ends.
time.sleep(60)
'''


@pytest.fixture
def bridge(monkeypatch):
    b = _Bridge()
    b.install(monkeypatch)
    return b


def _second_engine():
    """A genuinely separate engine module instance contending on the SAME
    directory through its own code path (mirrors the R40R1 harness)."""
    spec = importlib.util.spec_from_file_location(
        f"r44x2_engine_{next(iter(__import__('itertools').count()))}",
        str(Path(pgrec.__file__)))
    second = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = second
    spec.loader.exec_module(second)
    second._bind_test_recovery_root(pgrec._recovery_state_dir())
    return second


def _promoted(bridge, tmp_path, monkeypatch):
    from test_b4_cxr7u9r35_recovery_authority import _write_inputs
    inv, sha, archive = _write_inputs(tmp_path, monkeypatch)
    bridge.remote_sha = pgrec.sha256_file(str(archive))
    receipt, path = _promote_receipt(bridge, inv, sha, archive, "p.json")
    return receipt, path, inv, sha


def _transitions_dir():
    return Path(pgrec._recovery_state_dir()) / "transitions"


def _temp_names(receipt):
    prefix = f".{receipt['operation_id']}.claim."
    return sorted(p.name for p in _transitions_dir().glob(prefix + "*"))


def _sweep(receipt):
    """One real discarder sweep through the real engine."""
    pgrec._discard_abandoned_claim_temporaries(
        receipt["operation_id"], str(_transitions_dir()))


def _wait_for_marker(marker, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if marker.is_file():
            return json.loads(marker.read_text(encoding="utf-8"))
        time.sleep(0.02)
    raise AssertionError(f"writer never announced its temporary: {marker}")


def _spawn_writer(tmp_path, receipt):
    import subprocess
    script = tmp_path / "r44x2-writer.py"
    script.write_text(_WRITER_SCRIPT, encoding="utf-8")
    marker = tmp_path / "writer-marker.json"
    process = subprocess.Popen(
        [sys.executable, str(script), str(Path(pgrec.__file__)),
         str(pgrec._recovery_state_dir()), str(marker),
         receipt["operation_id"]],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return process, marker


# --------------------------------------------------------------------- #


def test_discarder_never_removes_a_live_writers_temporary(
        bridge, tmp_path, monkeypatch):
    """The CI defect, replayed against the strengthened engine: a real
    writer process holds the liveness lock on its in-flight temporary
    while a real discarder sweep runs. The temporary MUST survive."""
    receipt, _p, _i, _s = _promoted(bridge, tmp_path, monkeypatch)
    process, marker = _spawn_writer(tmp_path, receipt)
    live_path = None
    try:
        announced = _wait_for_marker(marker)
        live_path = Path(announced["tmp"])
        assert live_path.is_file(), announced
        assert live_path.parent == _transitions_dir()
        _sweep(receipt)
        assert live_path.is_file(), (
            "the discarder removed a LIVE writer's temporary")
        assert _temp_names(receipt) == [live_path.name]
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate(timeout=10)
        if live_path is not None:
            live_path.unlink(missing_ok=True)


def test_discarder_skips_probe_locked_temporary_and_removes_free_one(
        bridge, tmp_path, monkeypatch):
    """A discarder's probe lock is exclusive: a second sweep that finds the
    probe held must skip the candidate, and a sweep that finds it free
    must remove the abandoned temporary."""
    receipt, _p, _i, _s = _promoted(bridge, tmp_path, monkeypatch)
    governed = _transitions_dir()
    abandoned = governed / f".{receipt['operation_id']}.claim.deadbeef.tmp"
    abandoned.write_bytes(b"{}")
    probe = None
    try:
        probe = __import__("os").open(str(abandoned), __import__("os").O_RDWR)
        if sys.platform == "win32":
            import msvcrt
            msvcrt.locking(probe, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # The probe is held by THIS process: the sweep must not touch it.
        _sweep(receipt)
        assert abandoned.is_file(), (
            "a sweep deleted a temporary whose probe lock was held")
    finally:
        if probe is not None:
            __import__("os").close(probe)
    # The lock is now free: the next sweep removes the abandoned temporary.
    _sweep(receipt)
    assert not abandoned.exists()
    assert _temp_names(receipt) == []


def test_writer_retreats_and_publishes_after_released_window_removal(
        bridge, tmp_path, monkeypatch):
    """Windows-reachable interference: the temporary is removed AFTER the
    writer released its liveness lock but BEFORE publication. The real
    engine must retreat and publish from a fresh temporary anyway."""
    receipt, _p, _i, _s = _promoted(bridge, tmp_path, monkeypatch)
    governed = _transitions_dir()
    claim_path = governed / f"{receipt['operation_id']}.claim"

    original = pgrec._publish_no_replace

    class _InterferingOnce:
        """A discarder that deletes the writer's temporary in the released
        window (the real interference), then lets the retry succeed."""
        calls = 0

        def __call__(self, source, destination):
            if _InterferingOnce.calls == 0:
                _InterferingOnce.calls += 1
                try:
                    __import__("os").unlink(source)
                except OSError:
                    pass
                raise FileNotFoundError(2, "removed mid-window", source)
            return original(source, destination)

    pgrec._publish_no_replace = _InterferingOnce()
    try:
        pgrec._claim_transition(receipt["operation_id"], "finalize", receipt)
    finally:
        pgrec._publish_no_replace = original
    claim = json.loads(claim_path.read_text(encoding="utf-8"))
    assert claim["transition"] == "finalize"
    assert claim["operation_id"] == receipt["operation_id"]
    assert claim["receipt_sha256"] == pgrec._receipt_digest(receipt)
    assert _temp_names(receipt) == []
    record = pgrec._load_transition_record(receipt["operation_id"])
    assert record["selected_transition"] == "finalize"
    assert record["state"] == pgrec.TRANSITION_STATE_FINALIZING


def test_two_thread_race_still_has_exactly_one_winner_and_complete_claim(
        bridge, tmp_path, monkeypatch):
    """The exact CI-failing scenario, re-proven through the strengthened
    engine: two threads race through their own engine instances, exactly
    one wins, the canonical claim is complete, and no private temporary
    or sidecar file survives the race."""
    receipt, _p, _i, _s = _promoted(bridge, tmp_path, monkeypatch)
    results = []
    lock = threading.Lock()
    start = threading.Barrier(2)

    def attempt(engine, transition):
        start.wait()
        try:
            engine._claim_transition(receipt["operation_id"], transition,
                                     receipt)
            ok, err = True, None
        except RuntimeError as e:
            ok, err = False, str(e)
        with lock:
            results.append((transition, ok, err))

    engines = [_second_engine() for _ in range(2)]
    threads = [threading.Thread(target=attempt, args=(e, t))
               for e, t in zip(engines, ("finalize", "rollback"))]
    for t in threads:
        t.start()
    for t in threads:
        t.join(30)
        assert not t.is_alive(), "a racing attempt hung"
    winners = [tr for tr, ok, _ in results if ok]
    losers = [err for _, ok, err in results if not ok]
    assert len(winners) == 1, results
    assert len(losers) == 1 and "already claimed" in losers[0], results
    claim = json.loads(
        (_transitions_dir()
         / f"{receipt['operation_id']}.claim").read_text(encoding="utf-8"))
    assert claim["transition"] == winners[0]
    assert claim["receipt_sha256"] == pgrec._receipt_digest(receipt)
    # no leftover private temporaries, no sidecar files
    assert _temp_names(receipt) == [], _temp_names(receipt)
    record = pgrec._load_transition_record(receipt["operation_id"])
    assert record["selected_transition"] == winners[0]
    assert record["state"] == (
        pgrec.TRANSITION_STATE_FINALIZING if winners[0] == "finalize"
        else pgrec.TRANSITION_STATE_ROLLING_BACK)


def test_engine_liveness_retry_budget_is_the_proven_one():
    """The retreat loops are bounded by the budget these proofs assume; a
    silent change would invalidate the bounded-interference reasoning."""
    assert pgrec._CLAIM_TEMP_LIVENESS_ATTEMPTS == CLAIM_TEMP_LIVENESS_ATTEMPTS
