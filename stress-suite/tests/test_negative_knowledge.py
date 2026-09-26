"""NegativeKnowledge reopen semantics (A-009 §10, Book S11, G1 §12)."""
import pytest

from engine.authority import AuthorityState
from engine.negative import NegativeKnowledgeRecord, NegativeKnowledgeError


def test_reopenable_negative_knowledge_valid():
    nk = NegativeKnowledgeRecord.make(1, "family-X alpha", "FX EURUSD", "lookahead leakage",
                                      reopen_conditions=["clean-estimator sensor becomes available"])
    nk.validate_for_suppression()  # passes because reopen_conditions present


def test_no_reopen_condition_blocks_suppression():
    nk = NegativeKnowledgeRecord.make(2, "family-X alpha", "FX EURUSD", "failure")
    with pytest.raises(NegativeKnowledgeError):
        nk.validate_for_suppression()


def _auth(level_by_actor):
    a = AuthorityState()
    for actor, level in level_by_actor.items():
        a.seed_level(actor, level)
    a.freeze_initialization()
    return a


def test_agent_cannot_make_permanent():
    """G4-P0-C documented upgrade: permanence requires the ACTUAL AuthorityState
    level of the actor, never a payload string. Old assertion called
    make_permanent(\"agent-self\", \"WORKER\") and relied on the level string;
    replacement binds a WORKER actor to its real WORKER level and expects
    rejection."""
    nk = NegativeKnowledgeRecord.make(3, "family-X", "FX", "failure")
    auth = _auth({"agent-self": "WORKER"})
    with pytest.raises(NegativeKnowledgeError):
        nk.make_permanent("agent-self", auth, "agent-self-rationale")


def test_fake_operator_string_rejected():
    """A payload saying OPERATOR while the actor is WORKER fails closed."""
    nk = NegativeKnowledgeRecord.make(30, "family-X", "FX", "failure")
    auth = _auth({"worker": "WORKER"})
    with pytest.raises(NegativeKnowledgeError):
        nk.make_permanent("worker", auth, "payload-says-OPERATOR")
    assert not nk.is_permanent


def test_operator_can_make_permanent():
    nk = NegativeKnowledgeRecord.make(4, "family-X", "FX", "failure")
    auth = _auth({"operator": "OPERATOR"})
    nk.make_permanent("operator", auth, "operator-rationale-rt", ratification_ref="RAT-1")
    assert nk.is_permanent
    assert nk.permanence_authority["actor"] == "operator"
    assert nk.permanence_authority["actual_level"] == "OPERATOR"
    assert nk.permanence_authority["ratification_ref"] == "RAT-1"
    assert nk.permanence_authority["binding"] == "EXACT_AUTHORITY_STATE"
    nk.validate_for_suppression()  # permanent is valid without reopen conditions


def test_permanence_records_authority_reference():
    nk = NegativeKnowledgeRecord.make(5, "family-X", "FX", "failure")
    auth = _auth({"operator": "OPERATOR"})
    nk.make_permanent("operator", auth, "ratified-basis", ratification_ref="RAT-9")
    assert nk.permanent_by_operator_authority == "ratified-basis"
    assert nk.authority_basis == "ratified-basis"
    assert nk.permanence_authority["ratification_ref"] == "RAT-9"
