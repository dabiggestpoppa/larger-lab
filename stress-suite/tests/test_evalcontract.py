"""PhaseEvaluationContract (CON-03 / AMB-05) — freeze + separate future version."""
import pytest

from engine.evalcontract import PhaseEvaluationContract, FreezeViolation


def test_freeze_blocks_inplace_mutation():
    c = PhaseEvaluationContract.make(1, version_tag="V1")
    c.freeze()
    assert c.is_frozen()
    with pytest.raises(FreezeViolation):
        c.mutate({"channel_rules": {}})


def test_unfrozen_contract_can_version():
    c = PhaseEvaluationContract.make(2, version_tag="V1")
    nxt = c.next_version(3)
    assert nxt.version_tag != c.version_tag
    assert nxt.supersedes == c.contract_id
    assert not nxt.is_frozen()          # new window governs by a fresh contract
    assert c.freeze_status == "UNFROZEN"


def test_frozen_governs_window_not_promoted():
    # S20 / T6: success criteria of an open window may not silently change
    c = PhaseEvaluationContract.make(4, version_tag="V1")
    c.freeze()
    with pytest.raises(FreezeViolation):
        c.mutate({"hysteresis_rules": {"x": "HIGH"}})


def test_visibility_policy_preserves_con03():
    c = PhaseEvaluationContract.make(5, version_tag="V1", visibility_policy="SEALED_TEST_PARAMETER")
    rule = c.channel_rules["independent_contradiction"]
    assert rule["visibility_policy"] == "SEALED_TEST_PARAMETER"