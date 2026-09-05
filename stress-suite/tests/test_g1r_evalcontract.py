"""G1R-02 — PhaseEvaluationContract deep freeze + version isolation."""
import pytest

from engine.evalcontract import PhaseEvaluationContract, FrozenContractError, FreezeViolation


def _frozen_contract():
    c = PhaseEvaluationContract.make(1, version_tag="V1")
    c.freeze()
    assert c.is_frozen()
    return c


def test_frozen_contract_blocks_direct_channel_rule_mutation():
    c = _frozen_contract()
    # attack nested structure directly, not via mutate()
    with pytest.raises(Exception):
        c.channel_rules["independent_contradiction"]["threshold"] = "LOL"
    # reading still works and is value-preserving
    assert c.channel_rules["independent_contradiction"]["threshold"] == "MEDIUM"


def test_next_version_does_not_alias_channel_rules():
    c = _frozen_contract()
    nxt = c.next_version(2)
    # mutating the descendant's nested structure must not change the frozen parent
    nxt.channel_rules["independent_contradiction"]["threshold"] = "HIGH"
    assert c.channel_rules["independent_contradiction"]["threshold"] == "MEDIUM"


def test_next_version_does_not_alias_hysteresis_rules():
    c = PhaseEvaluationContract.make(3, version_tag="V1", hysteresis_rules={"enter_watch": "one"})
    nxt = c.next_version(4)
    nxt.hysteresis_rules["enter_watch"] = "zero"
    assert c.hysteresis_rules["enter_watch"] == "one"


def test_next_version_does_not_alias_transition_list():
    c = PhaseEvaluationContract.make(5, version_tag="V1", admissible_phase_transitions=[("STABLE", "WATCH")])
    nxt = c.next_version(6)
    nxt.admissible_phase_transitions.append(("WATCH", "STABLE"))
    assert c.admissible_phase_transitions == [("STABLE", "WATCH")]


def test_frozen_contract_fingerprint_stable_after_future_version_changes():
    c = _frozen_contract()
    fp_before = c.fingerprint()
    # create a descendant and mutate IT — parent fingerprint must be byte-stable
    n = c.next_version(7)
    n.channel_rules["exception_burden"]["threshold"] = "HIGH"
    n.freeze()
    assert c.fingerprint() == fp_before
    assert n.fingerprint() != fp_before    # descendant has own identity/fingerprint


def test_mutate_on_frozen_still_rejected():
    c = _frozen_contract()
    with pytest.raises(FreezeViolation):
        c.mutate({"version_tag": "V2"})