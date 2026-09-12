"""Generic fixture system (G1 §16). No scenario outcome logic — only mechanics."""
import pytest

from engine.fixtures import StressScenarioSpec, load_spec, run_smoke, build_seed_records, add_seed_record
from engine.replay import ReplayInputError


def test_decision_grade_seals_ground_truth():
    spec = StressScenarioSpec(scenario_id="s", hidden_ground_truth={"leakage": True})
    dg = spec.decision_grade()
    # the decision-grade projection drops the sealed payload entirely
    assert dg.hidden_ground_truth is None
    assert spec.hidden_ground_truth == {"leakage": True}
    assert dg.to_dict()["hidden_ground_truth"] is None


def test_load_spec_roundtrip(fixtures_smoke_dir):
    spec = load_spec(fixtures_smoke_dir / "legal_transition_smoke.json")
    assert spec.scenario_id == "legal_transition_smoke"
    assert spec.initial_phase == "STABLE"


def test_build_seed_records():
    spec = StressScenarioSpec(scenario_id="s", initial_knowledge=[
        {"record_id": "@K", "state": "DORMANT", "claim": "c"},
    ])
    recs = build_seed_records(spec)
    assert len(recs) == 1
    assert recs[0].state == "DORMANT"


def test_add_seed_record_returns_copy():
    spec = StressScenarioSpec(scenario_id="s")
    spec2 = add_seed_record(spec, "@K", "DORMANT", "c")
    assert spec2.initial_knowledge  # copy has the seed
    assert not spec.initial_knowledge  # original untouched (immutability of spec logic)


def test_malformed_spec_rejected():
    with pytest.raises(TypeError):
        StressScenarioSpec()  # missing required scenario_id