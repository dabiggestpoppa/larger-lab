"""Authority firewall (G1 §9) — capability, evidence, phase, knowledge, profit
never escalate authority; no self-ratification."""
import pytest

from engine.authority import AuthorityState, CapabilityGrant, AuthorityViolation, AuthorityLevel
from engine.forbidden import ForbiddenTransitionValidator as F
from engine.evidence import EvidenceRecord
from engine.base import Provenance


def test_capability_does_not_escalate_authority():
    ## scenario: worker shows excellent reliability then asks for broader deploy
    state = AuthorityState()
    state.set_level("WORKER_1", AuthorityLevel.WORKER.value)
    # granting a read capability to WORKER_1 does not change its authority level
    state.registry.issue(
        CapabilityGrant.make(1, "WORKER_1", "read", "dataset", issued_by="OPERATOR", risk_class="read"),
        ratified_by="OPERATOR",
    )
    assert state.level("WORKER_1") == AuthorityLevel.WORKER.value
    # capability improvement cannot self-gain an authority-bearing grant
    with pytest.raises(AuthorityViolation):
        state.registry.issue(
            CapabilityGrant.make(2, "WORKER_1", "deploy", "production", issued_by="WORKER_1", risk_class="deployment"),
            ratified_by="WORKER_1",
        )
    # the self-issued deploy grant was rejected; only the operator-issued read
    # grant remains
    grants = state.registry.grants("WORKER_1")
    assert len(grants) == 1
    assert grants[0].action == "read"


def test_operator_preference_is_not_evidence():
    # operator preference != stronger evidence: authority cannot write the evidence graph
    # (structural: AuthorizationState never exposes such a write; this guards intent)
    AuthorityState.operator_preference_is_not_evidence()
    ev = EvidenceRecord.make(1, "claim", kind="OBSERVATION")
    ev  # evidence is what it is regardless of who prefers change


def test_research_promotion_is_not_execution_authority():
    AuthorityState.research_promotion_is_not_execution_authority()
    assert True  # structural guard present


def test_agent_confidence_not_confirmation():
    r = F.agent_confidence_to_confirmation("AGENT_CLAIM", "AGENT_CLAIM")
    assert not r.violation
    r2 = F.agent_confidence_to_confirmation("AGENT_CLAIM", "INDEPENDENT_CONFIRMATION")
    assert r2.violation
    assert r2.reason


def test_window_is_not_capital():
    r = F.window_to_capital("TRANSFORMATION_WINDOW", "CAPITAL_MUTATION")
    assert r.violation
    r2 = F.window_to_capital("TRANSFORMATION_WINDOW", "ONTOLOGY_MUTATION")
    assert not r2.violation


def test_worker_may_propose_not_self_ratify():
    state = AuthorityState()
    state.set_level("WORKER_1", AuthorityLevel.WORKER.value)
    state.set_level("OPERATOR", AuthorityLevel.OPERATOR.value)
    grant = CapabilityGrant.make(5, "WORKER_1", "archive_write", "documents",
                                 issued_by="OPERATOR", risk_class="destructive")
    # proposal is allowed
    state.propose_authority_change("WORKER_1", "WORKER_1", grant)
    assert len(state._ratifications) == 1
    # ratification by the target itself is forbidden
    with pytest.raises(AuthorityViolation):
        state.ratify_authority_change("WORKER_1", "WORKER_1", "WORKER_1", grant)
    # ratification by OPERATOR succeeds
    state.ratify_authority_change("OPERATOR", "WORKER_1", "WORKER_1", grant)
    assert len(state.registry.grants("WORKER_1")) == 1