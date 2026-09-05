"""G2-A — generic evidence adjudicator mechanics (G2 §3-§6).

Proves: determinism, non-scalar gating, frozen-contract requirement, fail-closed
grades, persistence, dependency-centrality rigour (not immunity), hysteresis
(self-transition skip), hold_when blockers, and patch-pressure matching.
No S01-S24 scenario-ID logic and no expected-trace knowledge here.
"""
from pathlib import Path

import pytest

from engine.adjudicate import (
    AdjudicatorPolicy, EvidenceAdjudicator, EvidenceObservation, PolicyError,
)
from engine.evalcontract import PhaseEvaluationContract


def _policy(rules):
    return AdjudicatorPolicy.from_data({
        "policy_id": "g2a-test",
        "version_tag": "V1",
        "rules": rules,
    })


def _contract(frozen=True):
    c = PhaseEvaluationContract.make(1, version_tag="G2A-V1")
    if frozen:
        c.freeze()
    return c


def _obs(seq, vector, **kw):
    return EvidenceObservation(seq=seq, vector=vector, **kw)


MINI_RULES = [
    {"rule_id": "enter.watch", "to_state": "WATCH",
     "any_of": [{"reliability_degradation": "MEDIUM"},
                {"independent_contradiction": "MEDIUM"}]},
    {"rule_id": "escalate.persist", "to_state": "ESCALATION_REVIEW",
     "all_of": [{"independent_contradiction": "MEDIUM"}],
     "persistence": {"channel": "independent_contradiction", "grade": "MEDIUM",
                     "minimum_observations": 3}},
]


def test_deterministic_same_inputs():
    a = EvidenceAdjudicator(_policy(MINI_RULES), _contract())
    b = EvidenceAdjudicator(_policy(MINI_RULES), _contract())
    vs = [{"reliability_degradation": "MEDIUM"},
          {"independent_contradiction": "MEDIUM"},
          {"independent_contradiction": "MEDIUM"},
          {"independent_contradiction": "MEDIUM"}]
    for v in vs:
        a.observe(_obs(len(a._observations) + 1, v))
        b.observe(_obs(len(b._observations) + 1, v))
    for i in range(1, 5):
        current = "STABLE" if i == 1 else ("WATCH" if i < 4 else "ESCALATION_REVIEW")
        pa = a.propose(current_phase=current)
        pb = b.propose(current_phase=current)
        assert (pa.rule_id, pa.action, pa.to_state) == (pb.rule_id, pb.action, pb.to_state)


def test_non_scalar_all_of_requires_every_channel():
    p = _policy([{"rule_id": "double", "to_state": "WATCH",
                  "all_of": [{"reliability_degradation": "HIGH"},
                             {"independent_contradiction": "HIGH"}]}])
    a = EvidenceAdjudicator(p, _contract())
    a.observe(_obs(1, {"reliability_degradation": "HIGH", "independent_contradiction": "LOW"}))
    # both HIGH required: only one channel high is NOT enough (no scalar collapose)
    assert a.propose(current_phase="STABLE").action == "HOLD"
    a.observe(_obs(2, {"reliability_degradation": "HIGH", "independent_contradiction": "HIGH"}))
    prop = a.propose(current_phase="STABLE")
    assert prop.action == "TRANSITION" and prop.to_state == "WATCH"


def test_unfrozen_contract_rejected():
    with pytest.raises(PolicyError):
        EvidenceAdjudicator(_policy(MINI_RULES), _contract(frozen=False))


def test_unknown_grade_in_rule_fails_closed():
    with pytest.raises(PolicyError):
        _policy([{"rule_id": "x", "to_state": "WATCH",
                  "all_of": [{"reliability_degradation": "SKY_HIGH"}]}])


def test_unknown_grade_in_observation_fails_closed():
    a = EvidenceAdjudicator(_policy(MINI_RULES), _contract())
    with pytest.raises(PolicyError):
        a.observe(_obs(1, {"reliability_degradation": "MEGA"}))


def test_persistence_window():
    p = _policy([{"rule_id": "persist", "to_state": "ESCALATION_REVIEW",
                  "persistence": {"channel": "independent_contradiction", "grade": "MEDIUM",
                                  "minimum_observations": 3}}])
    a = EvidenceAdjudicator(p, _contract())
    a.observe(_obs(1, {"independent_contradiction": "MEDIUM"}))
    a.observe(_obs(2, {"independent_contradiction": "MEDIUM"}))
    assert a.propose(current_phase="WATCH").action == "HOLD"  # only 2 of 3
    a.observe(_obs(3, {"independent_contradiction": "MEDIUM"}))
    assert a.propose(current_phase="WATCH").action == "TRANSITION"


def test_dependency_centrality_adds_rigour_not_immunity():
    """CORE (HIGH) centrality demands an independent-contradiction gate; it
    never BLOCKS a legitimately evidenced transition and never auto-fires."""
    p = _policy([{"rule_id": "core.gate", "to_state": "TRANSFORMATION_CANDIDATE",
                  "all_of": [{"reliability_degradation": "MEDIUM"}],
                  "dependency": {"min_centrality": "HIGH", "requires_stronger_review": True}}])
    a = EvidenceAdjudicator(p, _contract())
    # CORE + HIGH contradiction + MEDIUM reliability -> fires
    a.observe(_obs(1, {"dependency_centrality": "HIGH", "independent_contradiction": "HIGH",
                       "reliability_degradation": "MEDIUM"}))
    assert a.propose(current_phase="ESCALATION_REVIEW").action == "TRANSITION"
    # CORE + only MEDIUM contradiction -> stronger review denies (rigour)
    b = EvidenceAdjudicator(p, _contract())
    b.observe(_obs(1, {"dependency_centrality": "HIGH", "independent_contradiction": "MEDIUM",
                       "reliability_degradation": "MEDIUM"}))
    assert b.propose(current_phase="ESCALATION_REVIEW").action == "HOLD"
    # LEAF + HIGH contradiction -> dependency gate itself denies (not immunity,
    # but the rule only applies to core surfaces)
    c = EvidenceAdjudicator(p, _contract())
    c.observe(_obs(1, {"dependency_centrality": "LOW", "independent_contradiction": "HIGH",
                       "reliability_degradation": "MEDIUM"}))
    assert c.propose(current_phase="ESCALATION_REVIEW").action == "HOLD"


def test_hysteresis_self_transition_skipped():
    """A rule targeting the CURRENT phase is skipped (no self-loop proposals)."""
    a = EvidenceAdjudicator(_policy(MINI_RULES), _contract())
    a.observe(_obs(1, {"reliability_degradation": "MEDIUM"}))
    # from STABLE the enter.watch rule fires
    assert a.propose(current_phase="STABLE").to_state == "WATCH"
    # once ALREADY in WATCH the same evidence no longer proposes WATCH
    assert a.propose(current_phase="WATCH").action == "HOLD"


def test_hold_when_blocks_transition():
    """A data-quality blocker HOLD is its own rule (pass 1); the escalation
    rule (pass 2) fires only when the blocker label is absent. Two explicit
    rules, never one rule playing both roles."""
    p = _policy([
        {"rule_id": "escalate", "to_state": "ESCALATION_REVIEW",
         "all_of": [{"independent_contradiction": "HIGH"}]},
        {"rule_id": "leak.hold", "hold": True,
         "hold_when": ["DATA_QUALITY_DEFECT"]},
    ])
    a = EvidenceAdjudicator(p, _contract())
    a.observe(_obs(1, {"independent_contradiction": "HIGH"}))
    prop = a.propose(current_phase="WATCH")
    assert prop.action == "TRANSITION" and prop.rule_id == "escalate"
    b = EvidenceAdjudicator(p, _contract())
    b.observe(_obs(1, {"independent_contradiction": "HIGH"}, holds=("DATA_QUALITY_DEFECT",)))
    prop = b.propose(current_phase="WATCH")
    assert prop.action == "HOLD" and prop.rule_id == "leak.hold"


def test_patch_recurrence_and_signature_matching():
    p = _policy([{"rule_id": "patch.l2", "to_state": "ESCALATION_REVIEW",
                  "patch": {"structural_level": "L2", "min_recurrence": 3,
                            "causal_signature": "SIG_B"}}])
    a = EvidenceAdjudicator(p, _contract())
    # unrelated signature -> no aggregation
    a.observe(_obs(1, {}, patch={"structural_level": "L3", "causal_signature": "SIG_A",
                                 "recurrence": 5}))
    assert a.propose(current_phase="WATCH").action == "HOLD"
    # same signature but low recurrence
    b = EvidenceAdjudicator(p, _contract())
    b.observe(_obs(1, {}, patch={"structural_level": "L3", "causal_signature": "SIG_B",
                                 "recurrence": 2}))
    assert b.propose(current_phase="WATCH").action == "HOLD"
    # matching signature + recurrence >= 3 + level >= L2 -> fires
    c = EvidenceAdjudicator(p, _contract())
    c.observe(_obs(1, {}, patch={"structural_level": "L2", "causal_signature": "SIG_B",
                                 "recurrence": 3}))
    prop = c.propose(current_phase="WATCH")
    assert prop.action == "TRANSITION" and prop.to_state == "ESCALATION_REVIEW"


def test_adjudicator_module_has_no_expected_or_ground_truth_tokens():
    """Static guard (G2 §15/§16): the adjudicator source cannot contain the
    verdict-shaped identifiers nor any S01-S24 scenario reference — expectations
    can only be applied post-hoc by the comparator."""
    src = (Path(__file__).resolve().parent.parent / "engine" / "adjudicate.py").read_text(
        encoding="utf-8"
    )
    for token in ("expected_phase_path", "expected_terminal_knowledge",
                  "hidden_ground_truth", "scenario_id"):
        assert token not in src, f"adjudicator must not reference {token}"
    for sid in (f"S{i}" for i in range(1, 25)):
        assert sid not in src, f"adjudicator must not reference {sid}"


def test_propose_is_pure():
    """Repeated proposals from an unchanged observation stream never change."""
    a = EvidenceAdjudicator(_policy(MINI_RULES), _contract())
    a.observe(_obs(1, {"independent_contradiction": "MEDIUM"}))
    first = (a.propose(current_phase="STABLE").rule_id,
             a.propose(current_phase="STABLE").action,
             a.observation_count)
    second = (a.propose(current_phase="STABLE").rule_id,
              a.propose(current_phase="STABLE").action,
              a.observation_count)
    assert first == second