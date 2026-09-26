"""M5 phase machine — legal edges, illegal edges, no scalar authority."""
import pytest

from engine.phase import PhaseStateMachine, PhaseEdgeTable, PhaseDecisionError
from engine.evidence import EvidenceChannelVector


def _vec(**kw):
    return EvidenceChannelVector(kw).vector


def _attempt(m, seq, to, vec=None, level="GOVERNOR", mut="READ_ONLY", **kw):
    return m.attempt(
        seq=seq, actor="GOVERNOR", to_state=to,
        evidence_vector=vec or _vec(), authority_level=level,
        mutation_class=mut, **kw,
    )


def test_legal_escalation_chain():
    m = PhaseStateMachine()
    assert _attempt(m, 1, "WATCH").allowed
    assert _attempt(m, 2, "ESCALATION_REVIEW").allowed
    assert _attempt(m, 3, "HOMEOSTATIC_REPAIR").allowed
    assert _attempt(m, 4, "STABLE").allowed
    assert m.state == "STABLE"


def test_legal_transformation_episode_with_no_change():
    m = PhaseStateMachine()
    for to in ["WATCH", "ESCALATION_REVIEW", "TRANSFORMATION_CANDIDATE", "TRANSFORMATION_WINDOW"]:
        assert _attempt(m, m.decisions[-1].seq + 1 if m.decisions else 1, to).allowed
    # window may conclude NO_CHANGE (A-010 §15) and return to stable
    assert _attempt(m, 99, "NO_CHANGE").allowed
    assert _attempt(m, 100, "STABLE").allowed


def test_plural_model_state_reachable():
    m = PhaseStateMachine()
    for i, to in enumerate(["WATCH", "ESCALATION_REVIEW", "TRANSFORMATION_CANDIDATE",
                           "TRANSFORMATION_WINDOW", "RECONSOLIDATION"], start=1):
        assert _attempt(m, i, to).allowed
    assert _attempt(m, 60, "PLURAL_MODEL_STATE").allowed


def test_stable_to_new_stable_forbidden():
    m = PhaseStateMachine()
    d = _attempt(m, 1, "NEW_STABLE")
    assert not d.allowed
    assert m.state == "STABLE"


def test_escalation_review_to_window_forbidden():
    m = PhaseStateMachine()
    _attempt(m, 1, "WATCH")
    _attempt(m, 2, "ESCALATION_REVIEW")
    d = _attempt(m, 3, "TRANSFORMATION_WINDOW")
    assert not d.allowed
    assert m.state == "ESCALATION_REVIEW"


def test_watch_mutation_forbidden_by_rule_layer():
    m = PhaseStateMachine()
    _attempt(m, 1, "WATCH")
    # phase graph has no watch->ARCHITECTURE mutation, and forbidden validator rejects
    d = _attempt(m, 2, "NEW_STABLE", mut="ARCHITECTURE_MUTATION")
    assert not d.allowed


def test_capital_never_from_phase():
    m = PhaseStateMachine()
    _attempt(m, 1, "WATCH")
    _attempt(m, 2, "ESCALATION_REVIEW")
    _attempt(m, 3, "TRANSFORMATION_CANDIDATE")
    _attempt(m, 4, "TRANSFORMATION_WINDOW")
    d = _attempt(m, 5, "RECONSOLIDATION", mut="CAPITAL_MUTATION")
    assert not d.allowed
    assert m.state == "TRANSFORMATION_WINDOW"


def test_unknown_authority_rejected():
    m = PhaseStateMachine()
    with pytest.raises(PhaseDecisionError):
        _attempt(m, 1, "WATCH", level="SUPREME_OVERLORD")


def test_decision_preserves_channel_vector():
    m = PhaseStateMachine()
    v = _vec(independent_contradiction="HIGH", dependency_centrality="CORE")
    d = _attempt(m, 1, "WATCH", vec=v)
    assert d.evidence_vector["independent_contradiction"] == "HIGH"
    assert d.evidence_vector["dependency_centrality"] == "CORE"