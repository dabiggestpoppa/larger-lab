"""G2-A — scenario runner + sealed expectations (G2 §7, §15, §16).

Proves the runner: freezes the evaluation contract before the first adjudicated
decision; never lets expected_phase_trace or hidden_ground_truth inform
execution (metamorphic: flipping them changes NOTHING in the run); derives phase
changes from observable evidence via the generic policy; executes institutional
actions through the governed executor (identity-bound); records forbidden
attempts; applies expectations only post-hoc.
"""
import pytest

from engine.scenario import run_scenario, evaluate_expectation, decision_view
from engine.adjudicate import AdjudicatorPolicy
from engine.evalcontract import PhaseEvaluationContract
from engine.fixtures import StressScenarioSpec
from engine.base import EvidenceChannel


def _contract():
    c = PhaseEvaluationContract.make(1, version_tag="G2A-V1",
                                     channels=tuple(ch.value for ch in EvidenceChannel))
    return c  # runner must freeze BEFORE first decision


def _policy(rules):
    return AdjudicatorPolicy.from_data({"policy_id": "g2a-mini", "version_tag": "V1",
                                        "rules": rules})


MINI_POLICY = _policy([
    {"rule_id": "enter.watch", "to_state": "WATCH",
     "any_of": [{"reliability_degradation": "MEDIUM"},
                {"independent_contradiction": "MEDIUM"}]},
    {"rule_id": "escalate.persist", "to_state": "ESCALATION_REVIEW",
     "all_of": [{"independent_contradiction": "MEDIUM"}],
     "persistence": {"channel": "independent_contradiction", "grade": "MEDIUM",
                     "minimum_observations": 3}},
])


def _spec(vectors, expected=None, hgt=None, institutional=None, initial_authority=None,
          initial_knowledge=None, scenario_id="mini"):
    stimulus = []
    for i, v in enumerate(vectors):
        raw = {"seq": 10 + i, "evidence_vector": v, "evidence_refs": [f"E{10 + i}"]}
        if institutional and i in institutional:
            raw["institutional_action"] = institutional[i]
        stimulus.append(raw)
    return StressScenarioSpec(
        scenario_id=scenario_id,
        initial_phase="STABLE",
        initial_authority_state=initial_authority or {},
        initial_knowledge=initial_knowledge or [],
        stimulus_events=stimulus,
        expected_phase_path=expected if expected is not None else [],
        hidden_ground_truth=hgt,
    )


def _run(spec):
    return run_scenario(spec, _contract(), MINI_POLICY)


# --------------------------------------------------------------------------- #
def test_contract_frozen_and_meta_recorded_before_first_decision():
    contract = _contract()
    spec = _spec([{"reliability_degradation": "MEDIUM"}])
    assert contract.is_frozen() is False
    res = run_scenario(spec, contract, MINI_POLICY)
    assert contract.is_frozen() is True
    meta = res.artifacts["evaluation_contract"]
    assert meta["freeze_status"] == "FROZEN"
    assert meta["contract_id"] == contract.contract_id
    assert meta["version_tag"] == "G2A-V1"
    assert meta["fingerprint"] == contract.fingerprint()
    assert len(meta["fingerprint"]) > 0


def test_expected_trace_sealed_metamorphic():
    """Flipping the expected trace to a WRONG value must not change execution."""
    vectors = [{"reliability_degradation": "MEDIUM"}]
    right = _spec(vectors, expected=["STABLE", "WATCH"])
    wrong = _spec(vectors, expected=["STABLE", "NEW_STABLE", "ROLLBACK"])
    a = _run(right)
    b = _run(wrong)
    assert a.artifacts["fingerprint"] == b.artifacts["fingerprint"]
    assert a.artifacts["actual_phase_trace"] == b.artifacts["actual_phase_trace"]
    assert a.artifacts["expected_trace_accessed"] is False
    # only the post-hoc comparator disagrees
    ea = evaluate_expectation(a, right)
    eb = evaluate_expectation(b, wrong)
    assert ea["pass"] is True and eb["pass"] is False


def test_hidden_ground_truth_sealed_metamorphic():
    vectors = [{"reliability_degradation": "MEDIUM"}]
    a = _run(_spec(vectors, hgt={"leakage": True, "survivorship": True}))
    b = _run(_spec(vectors, hgt={"leakage": False, "survivorship": False}))
    assert a.artifacts["fingerprint"] == b.artifacts["fingerprint"]
    assert a.artifacts["actual_phase_trace"] == b.artifacts["actual_phase_trace"]
    assert a.artifacts["hidden_ground_truth_accessed"] is False


def test_decision_view_strips_expectations_and_ground_truth():
    spec = _spec([{"reliability_degradation": "MEDIUM"}], expected=["STABLE", "WATCH"],
                 hgt={"x": 1}, initial_knowledge=[{"record_id": "@K", "state": "ACTIVE", "claim": "c"}])
    view = decision_view(spec)
    assert "expected_phase_path" not in view
    assert "expected_terminal_knowledge" not in view
    assert "terminal_states" not in view
    assert "hidden_ground_truth" not in view
    assert "stimulus_events" in view
    assert "initial_knowledge" in view


def test_weak_evidence_holds_stable():
    res = _run(_spec([{"reliability_degradation": "LOW"}]))
    assert res.artifacts["actual_phase_trace"] == ["STABLE"]
    assert res.artifacts["terminal_phase"] == "STABLE"
    assert len(res.artifacts["holds"]) == 1  # NO_MATCH hold recorded


def test_evidence_derives_watch_then_escalation():
    vectors = [{"independent_contradiction": "MEDIUM"},
               {"independent_contradiction": "MEDIUM"},
               {"independent_contradiction": "MEDIUM"}]
    res = _run(_spec(vectors, expected=["STABLE", "WATCH", "ESCALATION_REVIEW"]))
    assert res.artifacts["actual_phase_trace"] == ["STABLE", "WATCH", "ESCALATION_REVIEW"]
    assert res.artifacts["terminal_phase"] == "ESCALATION_REVIEW"
    # evidence refs recorded per transition
    assert res.artifacts["evidence_refs_by_transition"] == {10: ["E10"], 12: ["E12"]}
    # post-hoc comparison agrees
    assert evaluate_expectation(res, _spec(vectors, expected=["STABLE", "WATCH", "ESCALATION_REVIEW"]))["pass"]


def test_institutional_action_executed_through_governed_executor():
    vectors = [{"reliability_degradation": "MEDIUM"},
               {"independent_contradiction": "LOW"}]
    ia = {0: {"machine": "lifecycle", "actor": "PO", "target": "@K",
              "payload": {"to_state": "DEMOTED", "authority_level": "PO",
                          "authority_basis": "b", "reason": "demote"}}}
    spec = _spec(vectors, initial_authority={"PO": "PO"},
                 initial_knowledge=[{"record_id": "@K", "state": "ACTIVE", "claim": "c"}])
    spec.stimulus_events[0]["institutional_action"] = ia[0]
    res = _run(spec)
    assert res.artifacts["terminal_knowledge_states"]["@K"] == "DEMOTED"


def test_institutional_action_unknown_actor_fails_closed():
    spec = _spec([{"reliability_degradation": "MEDIUM"}])
    spec.stimulus_events[0]["institutional_action"] = {
        "machine": "lifecycle", "actor": "GHOST", "target": "@K",
        "payload": {"to_state": "DEMOTED", "authority_level": "PO", "reason": "x"}}
    res = _run(spec)
    entry = [t for t in res.artifacts["trace"] if t.get("institutional")]
    assert entry and entry[0]["allowed"] is False
    assert entry[0]["kind"] == "AUTHORITY_INVALID"


def test_forbidden_mutation_class_recorded_not_applied():
    bad = _policy([
        {"rule_id": "enter.watch", "to_state": "WATCH",
         "any_of": [{"reliability_degradation": "MEDIUM"}]},
        {"rule_id": "bad.mut", "to_state": "ESCALATION_REVIEW",
         "any_of": [{"exception_burden": "HIGH"}], "mutation_class": "ARCHITECTURE_MUTATION"},
    ])
    spec = _spec([{"reliability_degradation": "MEDIUM"}, {"exception_burden": "HIGH"}])
    res = run_scenario(spec, _contract(), bad)
    assert res.artifacts["actual_phase_trace"] == ["STABLE", "WATCH"]
    assert res.artifacts["terminal_phase"] == "WATCH"           # second NOT applied
    forbidden = res.artifacts["forbidden_attempts"]
    assert forbidden and forbidden[0]["allowed"] is False
    assert any("RULE-02" in f["rule_ids"] for f in forbidden)


def test_runner_phase_driver_bound_to_governor_role():
    """The runner drives every phase step as the seeded GOVERNOR actor; the
    authority projection is frozen and unchanged by the run (phase actions
    never mutate grants or levels, and identity binding always applies)."""
    bad = _policy([
        {"rule_id": "enter.watch", "to_state": "WATCH",
         "any_of": [{"reliability_degradation": "MEDIUM"}]},
    ])
    spec = _spec([{"reliability_degradation": "MEDIUM"}])
    res = run_scenario(spec, _contract(), bad, governor_actor="GOVERNOR")
    assert res.artifacts["terminal_phase"] == "WATCH"
    # the governing actor is bound to GOVERNOR level for every phase step
    assert res.artifacts["authority_state_before"]["GOVERNOR"]["level"] == "GOVERNOR"
    assert res.artifacts["authority_state_after"] == res.artifacts["authority_state_before"]


def test_run_is_deterministic():
    spec = _spec([{"reliability_degradation": "MEDIUM"},
                  {"independent_contradiction": "MEDIUM"},
                  {"independent_contradiction": "MEDIUM"}])
    a = _run(spec)
    b = _run(spec)
    assert a.artifacts["fingerprint"] == b.artifacts["fingerprint"]
    assert a.artifacts["actual_phase_trace"] == b.artifacts["actual_phase_trace"]