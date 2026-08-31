"""NegativeKnowledge reopen semantics (A-009 §10, Book S11, G1 §12)."""
import pytest

from engine.negative import NegativeKnowledgeRecord, NegativeKnowledgeError


def test_reopenable_negative_knowledge_valid():
    nk = NegativeKnowledgeRecord.make(1, "family-X alpha", "FX EURUSD", "lookahead leakage",
                                      reopen_conditions=["clean-estimator sensor becomes available"])
    nk.validate_for_suppression()  # passes because reopen_conditions present


def test_no_reopen_condition_blocks_suppression():
    nk = NegativeKnowledgeRecord.make(2, "family-X alpha", "FX EURUSD", "failure")
    with pytest.raises(NegativeKnowledgeError):
        nk.validate_for_suppression()


def test_agent_cannot_make_permanent():
    nk = NegativeKnowledgeRecord.make(3, "family-X", "FX", "failure")
    with pytest.raises(NegativeKnowledgeError):
        nk.make_permanent("agent-self", "WORKER")


def test_operator_can_make_permanent():
    nk = NegativeKnowledgeRecord.make(4, "family-X", "FX", "failure")
    nk.make_permanent("operator-rationale-rt", "OPERATOR")
    assert nk.is_permanent
    nk.validate_for_suppression()  # permanent is valid without reopen conditions