"""Deterministic replay (G1 §15) — same inputs + same contracts -> same output,
out-of-order rejected, illegal events recorded not applied."""
import json
from pathlib import Path

import pytest

from engine.replay import DeterministicReplay, ReplayEvent
from engine.fixtures import load_spec, spec_to_replay_events, run_smoke, StressScenarioSpec
from engine.replay import ReplayInputError


def _events():
    return [
        ReplayEvent(seq=1, event_type="phase_step", machine="phase", actor="SENTINEL",
                    target="@INST", payload={"to_state": "WATCH", "evidence_vector": {},
                                             "authority_level": "GOVERNOR", "mutation_class": "READ_ONLY",
                                             "reason": "r1"}),
        ReplayEvent(seq=2, event_type="phase_step", machine="phase", actor="GOVERNOR",
                    target="@INST", payload={"to_state": "ESCALATION_REVIEW", "evidence_vector": {},
                                             "authority_level": "GOVERNOR", "mutation_class": "READ_ONLY",
                                             "reason": "r2"}),
        ReplayEvent(seq=3, event_type="phase_step", machine="phase", actor="GOVERNOR",
                    target="@INST", payload={"to_state": "HOMEOSTATIC_REPAIR", "evidence_vector": {},
                                             "authority_level": "GOVERNOR", "mutation_class": "HOMEOSTATIC_REPAIR",
                                             "reason": "r3"}),
        ReplayEvent(seq=4, event_type="phase_step", machine="phase", actor="GOVERNOR",
                    target="@INST", payload={"to_state": "STABLE", "evidence_vector": {},
                                             "authority_level": "GOVERNOR", "mutation_class": "REVERSIBLE",
                                             "reason": "r4"}),
    ]


def test_same_inputs_same_output():
    a = DeterministicReplay().run(_events())
    b = DeterministicReplay().run(_events())
    assert a.fingerprint == b.fingerprint
    assert a.terminal_phase == "STABLE"
    assert len(a.trace) == 4


def test_out_of_order_rejected():
    evs = _events()
    evs[1], evs[2] = evs[2], evs[1]
    evs[2] = ReplayEvent(seq=-1, event_type="phase_step", machine="phase", actor="X",
                         target="@INST", payload={})
    with pytest.raises(ReplayInputError):
        DeterministicReplay().run(evs)


def test_illegal_events_recorded_not_applied():
    evs = [
        ReplayEvent(seq=1, event_type="phase_step", machine="phase", actor="X",
                    target="@INST", payload={"to_state": "NEW_STABLE", "evidence_vector": {},
                                             "authority_level": "PO", "mutation_class": "READ_ONLY", "reason": ""}),
        ReplayEvent(seq=2, event_type="phase_step", machine="phase", actor="X",
                    target="@INST", payload={"to_state": "WATCH", "evidence_vector": {},
                                             "authority_level": "GOVERNOR", "mutation_class": "READ_ONLY", "reason": ""}),
    ]
    res = DeterministicReplay().run(evs)
    assert res.trace[0]["allowed"] is False
    assert res.trace[1]["allowed"] is True
    assert res.terminal_phase == "WATCH"


def test_smoke_legal_fixture(fixtures_smoke_dir):
    spec = load_spec(fixtures_smoke_dir / "legal_transition_smoke.json")
    res = run_smoke(spec)
    assert res.terminal_phase == "STABLE"
    assert all(t["allowed"] for t in res.trace)


def test_smoke_illegal_fixture_blocks(fixtures_smoke_dir):
    spec = load_spec(fixtures_smoke_dir / "illegal_transition_smoke.json")
    res = run_smoke(spec)
    assert res.trace[0]["allowed"] is False  # stable->new stable
    assert res.trace[1]["allowed"] is False  # capital from worker
    assert res.trace[2]["allowed"] is False  # dormant->active
    assert res.terminal_phase == "STABLE"


def test_smoke_reactivation(fixtures_smoke_dir):
    spec = load_spec(fixtures_smoke_dir / "knowledge_reactivation_smoke.json")
    res = run_smoke(spec)
    assert res.terminal_lifecycle["@K"] == "CANDIDATE"
    # the DORMANT->ACTIVE attempt (seq 2) was recorded but not applied
    assert res.trace[1]["allowed"] is False