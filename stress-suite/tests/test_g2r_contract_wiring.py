"""G2R-06 — PhaseEvaluationContract is FULLY semantically wired.

* admissible_phase_transitions, when non-empty, gates proposals BEFORE
  application even when M5 topology allows the edge.
* hysteresis_rules are STRUCTURED and machine-readable; prose as an allegedly
  executable rule fails closed; minimum-persistence floors participate.
* recovery.independent_exit_predicate demands equality exit predicates;
  transformation stronger_than_watch is validated, not decorative.
"""
import pytest

from engine.adjudicate import (
    AdjudicatorPolicy, EvidenceAdjudicator, EvidenceObservation, PolicyError,
)
from engine.evalcontract import PhaseEvaluationContract
from engine.fixtures import StressScenarioSpec
from engine.scenario import run_scenario

ALL_CHANNELS = ("reliability_degradation", "exception_burden",
                "independent_contradiction", "unresolved_pattern_density",
                "dependency_centrality", "external_environment_shift",
                "opportunity_cost_of_stability", "cost_and_reversibility")


def _policy(rules):
    return AdjudicatorPolicy.from_data({"policy_id": "g2r-wire", "version_tag": "V1",
                                        "rules": rules})


def _contract(admissible=None, hysteresis=None, **kw):
    return PhaseEvaluationContract(
        contract_id=kw.pop("contract_id", "WIRE-V1"),
        version_tag=kw.pop("version_tag", "V1"),
        channel_rules={c: {"threshold": "MEDIUM", "visibility_policy": "PUBLIC"} for c in ALL_CHANNELS},
        hysteresis_rules=dict(hysteresis or {}),
        admissible_phase_transitions=list(admissible or []),
        freeze_status="FROZEN",
    )


def _spec(events):
    return StressScenarioSpec(scenario_id="wire", stimulus_events=events,
                              initial_authority_state={"GOVERNOR": "GOVERNOR"})


WATCH_AND_ESCALATE = [
    {"rule_id": "enter.watch", "to_state": "WATCH",
     "any_of": [{"exception_burden": "MEDIUM"}]},
    {"rule_id": "escalate", "to_state": "ESCALATION_REVIEW",
     "all_of": [{"exception_burden": "MEDIUM"}],
     "persistence": {"channel": "exception_burden", "grade": "MEDIUM", "minimum_observations": 2}},
]


def test_contract_admissible_transition_enforced():
    """Only [STABLE -> WATCH] is admissible; the M5-legal WATCH ->
    ESCALATION_REVIEW proposal is blocked by the contract and recorded."""
    events = [{"seq": i, "evidence_vector": {"exception_burden": "MEDIUM"}, "evidence_refs": []}
              for i in (1, 2, 3)]
    res = run_scenario(_spec(events), _contract(admissible=[("STABLE", "WATCH")]),
                       _policy(WATCH_AND_ESCALATE))
    assert res.artifacts["actual_phase_trace"] == ["STABLE", "WATCH"]
    assert res.artifacts["terminal_phase"] == "WATCH"
    inadmissible = [h for h in res.artifacts["holds"]
                    if h["rule_id"] == "CONTRACT_INADMISSIBLE"]
    assert inadmissible, "the inadmissible escalation must be recorded, not silent"


def test_m5_legal_but_contract_forbidden_transition_rejected():
    """Same evidence, unrestricted contract -> escalation fires; restricted
    contract -> stay at WATCH. Proves the contract (not topology) is the gate."""
    events = [{"seq": i, "evidence_vector": {"exception_burden": "MEDIUM"}, "evidence_refs": []}
              for i in (1, 2)]
    open_res = run_scenario(_spec(events), _contract(), _policy(WATCH_AND_ESCALATE))
    assert open_res.artifacts["actual_phase_trace"][-1] == "ESCALATION_REVIEW"
    closed_res = run_scenario(_spec(events), _contract(admissible=[("STABLE", "WATCH")]),
                              _policy(WATCH_AND_ESCALATE))
    assert closed_res.artifacts["actual_phase_trace"][-1] == "WATCH"


def test_hysteresis_field_changes_behavior_when_semantically_defined():
    """A rule WITHOUT explicit persistence inherits the contract's structured
    escalation floor (history-length): floor 5 blocks early escalation. (The
    policy carries an enter.watch rule because STABLE -> ESCALATION_REVIEW is
    not an M5 edge; the escalation floor is a gate on HOW LONG the institution
    must have observed the episode, independent of the votes' strength.)"""
    rule = [
        {"rule_id": "enter.watch", "to_state": "WATCH",
         "any_of": [{"exception_burden": "MEDIUM"}]},
        {"rule_id": "escalate", "to_state": "ESCALATION_REVIEW",
         "all_of": [{"exception_burden": "MEDIUM"}]},
    ]
    events = [{"seq": i, "evidence_vector": {"exception_burden": "MEDIUM"}, "evidence_refs": []}
              for i in range(1, 4)]
    floor5 = _contract(hysteresis={"escalation": {"minimum_persistence": 5}})
    res = run_scenario(_spec(events), floor5, _policy(rule))
    # watch opens, but escalation needs a 5-period history: floor not reached
    assert res.artifacts["actual_phase_trace"] == ["STABLE", "WATCH"]
    no_floor = _contract()
    res2 = run_scenario(_spec(events), no_floor, _policy(rule))
    assert res2.artifacts["actual_phase_trace"] == ["STABLE", "WATCH", "ESCALATION_REVIEW"]


def test_frozen_unused_semantic_field_is_not_allowed():
    """Human prose as an allegedly-executable hysteresis rule fails closed."""
    with pytest.raises(PolicyError):
        EvidenceAdjudicator(
            _policy([{"rule_id": "r", "to_state": "WATCH",
                      "any_of": [{"exception_burden": "MEDIUM"}]}]),
            _contract(hysteresis={"watch": "any material tension opens WATCH"}),
        )


def test_frozen_unknown_hysteresis_family_rejected():
    with pytest.raises(PolicyError):
        EvidenceAdjudicator(
            _policy([{"rule_id": "r", "to_state": "WATCH",
                      "any_of": [{"exception_burden": "MEDIUM"}]}]),
            _contract(hysteresis={"novelty_bonus": {"minimum_persistence": 3}}),
        )


def test_recovery_requires_independent_exit_predicate():
    """recovery.independent_exit_predicate=true demands equality gates on every
    recovery-target rule; a gte-only STABLE rule fails closed at load time."""
    with pytest.raises(PolicyError):
        EvidenceAdjudicator(
            _policy([{"rule_id": "bad.exit", "to_state": "STABLE",
                      "all_of": [{"exception_burden": "LOW"}]}]),
            _contract(hysteresis={"recovery": {"independent_exit_predicate": True}}),
        )
    # equality gate satisfies the predicate
    EvidenceAdjudicator(
        _policy([{"rule_id": "good.exit", "to_state": "STABLE",
                  "all_of": [{"exception_burden": "LOW", "op": "eq"}]}]),
        _contract(hysteresis={"recovery": {"independent_exit_predicate": True}}),
    )


def test_transformation_not_weaker_than_escalation():
    with pytest.raises(PolicyError):
        EvidenceAdjudicator(
            _policy([{"rule_id": "t", "to_state": "TRANSFORMATION_CANDIDATE",
                      "all_of": [{"independent_contradiction": "HIGH"}]}]),
            _contract(hysteresis={"escalation": {"minimum_persistence": 3},
                                  "transformation": {"minimum_persistence": 1, "stronger_than_watch": True}}),
        )


def test_admissible_list_uses_frozen_pairs_and_never_mutates():
    c = _contract(admissible=[("STABLE", "WATCH")])
    res = run_scenario(_spec([{"seq": 1, "evidence_vector": {"exception_burden": "MEDIUM"}}]),
                       c, _policy(WATCH_AND_ESCALATE))
    assert c.is_frozen()
    assert [tuple(p) for p in c.admissible_phase_transitions] == [("STABLE", "WATCH")]