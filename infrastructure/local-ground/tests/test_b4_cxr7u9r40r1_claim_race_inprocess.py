#!/usr/bin/env python3
"""B4-CXR7U9R40-R1 — the operation-wide claim race, proven WITHOUT a container.

The guarantee lives in OS-level exclusive creation on ONE claim file per
operation, so the race is provable wherever the governed recovery boundary
exists on a real filesystem: real threads race real O_EXCL through the REAL
CLI bootstrap (recovery_cli's seam is not needed — the engine module itself
contends on the same directory). The container-backed suite
(test_b4_cxr7u9r40r1_operation_wide_claim.py) proves the same law through the
real CLI against the real stack; this module proves the filesystem mechanism
and the loser's zero-mutation guarantee deterministically.
"""
import importlib.util
import json
import sys
import threading
from pathlib import Path

import pytest

from test_b4_cxr7u9r35_recovery_authority import (  # noqa: F401 — fixtures
    _Bridge, _promote_receipt, production_recovery_identity, pgrec)


def _second_engine():
    """A genuinely separate engine module instance: its own module globals, so
    a claim it takes goes through its own code path into the SAME directory."""
    spec = importlib.util.spec_from_file_location(
        f"r40_engine_{next(iter(__import__('itertools').count()))}", str(Path(pgrec.__file__)))
    second = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = second
    spec.loader.exec_module(second)
    second._bind_test_recovery_root(pgrec._recovery_state_dir())
    return second


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


def _race_claims(receipt, transitions):
    """N real threads contend for the ONE operation-wide claim through their
    own engine instances; returns the list of (transition, ok, error)."""
    results = []
    lock = threading.Lock()
    start = threading.Barrier(len(transitions))

    def attempt(engine, transition):
        start.wait()
        try:
            engine._claim_transition(receipt["operation_id"], transition, receipt)
            ok, err = True, None
        except RuntimeError as e:
            ok, err = False, str(e)
        with lock:
            results.append((transition, ok, err))

    engines = [_second_engine() for _ in transitions]
    threads = [threading.Thread(target=attempt, args=(e, t))
               for e, t in zip(engines, transitions)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(60)
    return results


# --------------------------------------------------------------------- #

def test_finalize_vs_rollback_exactly_one_thread_wins(
        bridge, tmp_path, monkeypatch):
    receipt, _path, _inv, _sha = _promoted(bridge, tmp_path, monkeypatch)
    results = _race_claims(receipt, ["finalize", "rollback"])
    winners = [tr for tr, ok, _ in results if ok]
    assert len(winners) == 1, results
    winner = winners[0]
    # exactly one durable claim file, naming the winner
    governed = Path(pgrec._recovery_state_dir()) / "transitions"
    claims = list(governed.glob("*.claim"))
    assert len(claims) == 1, claims
    claim = json.loads(claims[0].read_text(encoding="utf-8"))
    assert claim["transition"] == winner
    assert claim["receipt_sha256"] == pgrec._receipt_digest(receipt)
    # the record moved to the winner's in-flight state, forward-only
    record = pgrec._load_transition_record(receipt["operation_id"])
    assert record["selected_transition"] == winner
    assert record["state"] == (pgrec.TRANSITION_STATE_FINALIZING
                               if winner == "finalize"
                               else pgrec.TRANSITION_STATE_ROLLING_BACK)


def test_finalize_vs_finalize_and_rollback_vs_rollback_exactly_one_wins(
        bridge, tmp_path, monkeypatch):
    from test_b4_cxr7u9r35_recovery_authority import _write_inputs
    inv, sha, archive = _write_inputs(tmp_path, monkeypatch)
    bridge.remote_sha = pgrec.sha256_file(str(archive))
    for pair in (["finalize", "finalize"], ["rollback", "rollback"]):
        receipt2, _p = _promote_receipt(bridge, inv, sha, archive,
                                        f"{'f' if pair[0] == 'finalize' else 'r'}.json")
        results = _race_claims(receipt2, pair)
        assert sum(1 for _, ok, _ in results if ok) == 1, results


def test_three_way_race_exactly_one_wins(bridge, tmp_path, monkeypatch):
    receipt, _path, _inv, _sha = _promoted(bridge, tmp_path, monkeypatch)
    results = _race_claims(receipt, ["finalize", "rollback", "finalize"])
    assert sum(1 for _, ok, _ in results if ok) == 1, results


def test_the_loser_reports_the_winner_and_writes_nothing(
        bridge, tmp_path, monkeypatch):
    receipt, _path, _inv, _sha = _promoted(bridge, tmp_path, monkeypatch)
    governed = Path(pgrec._recovery_state_dir()) / "transitions"
    before = {str(p): p.read_bytes() for p in sorted(governed.rglob("*")) if p.is_file()}
    results = _race_claims(receipt, ["finalize", "rollback"])
    winner = [tr for tr, ok, _ in results if ok][0]
    loser = [err for tr, ok, err in results if not ok][0]
    assert "already claimed" in loser, loser
    assert winner in loser, loser  # the refusal NAMES the winning transition
    after = {str(p): p.read_bytes() for p in sorted(governed.rglob("*")) if p.is_file()}
    # the loser added no file and changed no file beyond the winner's own
    # claim+record writes (both attributable to the WINNER's state change)
    assert set(after) <= set(before) | {
        str(governed / f"{receipt['operation_id']}.claim")}, sorted(set(after) - set(before))
    for name in before:
        if name in after and f"{receipt['operation_id']}.json" not in name:
            assert after[name] == before[name], name


def test_interrupted_claim_cannot_reopen_as_fresh_authority(
        bridge, tmp_path, monkeypatch):
    """§2 proof 5: a crash after the claim leaves an attributable durable
    state, and the OPPOSITE transition cannot execute as fresh authority."""
    receipt, path, inv, sha = _promoted(bridge, tmp_path, monkeypatch)
    from test_b4_cxr7u9r39r3_transition_authority import _transition, \
        _assert_refused_without_mutation
    pgrec._claim_transition(receipt["operation_id"], "finalize", receipt)
    bridge.reset()
    # opposite transition after an interrupted claim: refused, zero mutation
    _assert_refused_without_mutation(
        bridge, _transition(bridge, "rollback", path, inv, sha),
        "no longer available")
    assert pgrec._load_transition_record(receipt["operation_id"])["state"] == \
        pgrec.TRANSITION_STATE_FINALIZING
    # and a restart (fresh engine instance) still sees the durable selection
    second = _second_engine()
    claim = second._load_claim(receipt["operation_id"])
    assert claim["transition"] == "finalize"


def test_durable_selected_transition_cannot_be_replaced(
        bridge, tmp_path, monkeypatch):
    """§2 proof 6: after restart, the durable selection remains visible and
    cannot be replaced by a new claim of the other transition."""
    receipt, _path, _inv, _sha = _promoted(bridge, tmp_path, monkeypatch)
    second = _second_engine()
    second._claim_transition(receipt["operation_id"], "rollback", receipt)
    # a later process (the original module) cannot re-claim either transition
    for tr in ("rollback", "finalize"):
        with pytest.raises(RuntimeError, match="already claimed"):
            pgrec._claim_transition(receipt["operation_id"], tr, receipt)
    assert second._load_claim(receipt["operation_id"])["transition"] == "rollback"


def test_forward_only_ladder_refuses_regressions(bridge, tmp_path, monkeypatch):
    """State can never regress: FINALIZING -> PROMOTED (and every other
    backward move) is refused, so a crashed in-flight record cannot be
    re-opened into re-usable PROMOTED authority by any process."""
    receipt, _path, _inv, _sha = _promoted(bridge, tmp_path, monkeypatch)
    opid = receipt["operation_id"]
    pgrec._claim_transition(opid, "finalize", receipt)
    with pytest.raises(RuntimeError, match="refusing to move recovery operation"):
        pgrec._record_transition(opid, pgrec.TRANSITION_STATE_PROMOTED, receipt)
    # same-state rewrite is idempotent; the ladder allows FINALIZING ->
    # ROLLED_BACK but no terminal -> anything
    pgrec._record_transition(opid, pgrec.TRANSITION_STATE_FINALIZING, receipt)
    pgrec._record_transition(opid, "ROLLED_BACK", receipt)
    with pytest.raises(RuntimeError, match="refusing to move recovery operation"):
        pgrec._record_transition(opid, "FINALIZED", receipt)
