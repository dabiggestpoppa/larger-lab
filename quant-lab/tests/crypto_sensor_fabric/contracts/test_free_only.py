"""Free-only policy tests (B1-T20 .. B1-T24).

These exercise the frozen F9 gate at the policy level.  Registry-level
integration (required-runtime validation over a loaded registry) lives in
`registry/test_provider_registry.py` (B1-03).
"""

from __future__ import annotations

import pytest
from crypto_sensor_fabric.contracts.access import (
    FreeOnlyPolicy,
    free_only_violations,
    is_free_only_eligible,
)
from crypto_sensor_fabric.contracts.enums import AccessClass


def _policy(**overrides) -> FreeOnlyPolicy:
    base = {
        "access_class": AccessClass.FREE_AUTOMATED,
        "cost_usd_required": 0,
        "payment_method_required": False,
        "staking_required": False,
        "transaction_required": False,
    }
    base.update(overrides)
    return FreeOnlyPolicy.model_validate(base)


def test_t20_paid_source_blocked():
    policy = _policy(access_class=AccessClass.PAID_EXCLUDED)
    assert not is_free_only_eligible(policy)
    assert free_only_violations(policy)
    assert not policy.is_eligible_required_automated


def test_t21_reference_only_blocked():
    policy = _policy(access_class=AccessClass.FREE_REFERENCE_ONLY)
    assert not is_free_only_eligible(policy)


def test_t22_unverified_blocked():
    policy = _policy(access_class=AccessClass.UNVERIFIED)
    assert not is_free_only_eligible(policy)


@pytest.mark.parametrize(
    "overrides",
    [
        {"cost_usd_required": 1},
        {"payment_method_required": True},
        {"staking_required": True},
        {"transaction_required": True},
    ],
)
def test_t23_cost_invariant_each_violation_blocks(overrides: dict):
    policy = _policy(**overrides)
    assert not is_free_only_eligible(policy)
    assert free_only_violations(policy)


def test_t23_free_limited_automated_eligible():
    assert is_free_only_eligible(_policy(access_class=AccessClass.FREE_LIMITED_AUTOMATED))


def test_t24_free_api_key_does_not_imply_paid():
    policy = _policy(api_key_required=True)
    assert is_free_only_eligible(policy)
    assert policy.api_key_required is True


def test_eligible_when_all_free():
    assert is_free_only_eligible(_policy())
    assert free_only_violations(_policy()) == []
