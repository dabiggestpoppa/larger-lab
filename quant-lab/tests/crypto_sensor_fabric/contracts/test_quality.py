"""Quality-state contract tests (B1-T53 and conservative aggregation)."""

from __future__ import annotations

import pytest
from crypto_sensor_fabric.contracts.enums import QualityFlag, QualityState
from crypto_sensor_fabric.contracts.quality import (
    BLOCKING_QUALITY_FLAGS,
    derive_quality_state,
    has_blocking_flag,
)


def test_t53_stale_source_never_good():
    assert (
        derive_quality_state([QualityFlag.STALE_SOURCE])
        is not QualityState.GOOD
    )
    assert (
        derive_quality_state(
            [QualityFlag.SOURCE_NATIVE, QualityFlag.STALE_SOURCE]
        )
        is QualityState.STALE
    )


def test_t53_stale_with_other_flags_still_not_good():
    state = derive_quality_state(
        [QualityFlag.STALE_SOURCE, QualityFlag.SOURCE_NATIVE, QualityFlag.UNIT_NORMALIZED]
    )
    assert state is not QualityState.GOOD


def test_no_flags_is_good():
    assert derive_quality_state([]) is QualityState.GOOD


def test_degraded_flags_map_conservatively():
    assert (
        derive_quality_state([QualityFlag.PROVIDER_DEGRADED])
        is QualityState.DEGRADED
    )
    assert (
        derive_quality_state([QualityFlag.PARTIAL_INTERVAL])
        is QualityState.PARTIAL
    )
    assert (
        derive_quality_state([QualityFlag.ACCESS_CLASS_UNVERIFIED])
        is QualityState.UNVERIFIED
    )


def test_blocking_flags_detected():
    assert has_blocking_flag([QualityFlag.PIT_RISK])
    assert has_blocking_flag([QualityFlag.INSTRUMENT_ID_UNRESOLVED])
    assert has_blocking_flag([QualityFlag.UNIT_NORMALIZATION_UNAVAILABLE])
    assert not has_blocking_flag([QualityFlag.SOURCE_NATIVE])
    assert not has_blocking_flag([])


# ---------------------------------------------------------------------------
# SENSOR-B1-R03 — blocking flags resolve fail-closed to BLOCKED
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("flag", sorted(BLOCKING_QUALITY_FLAGS))
def test_r03_every_blocking_flag_resolves_to_blocked(flag: QualityFlag):
    assert derive_quality_state([flag]) is QualityState.BLOCKED


def test_r03_required_examples():
    assert derive_quality_state([QualityFlag.PIT_RISK]) is QualityState.BLOCKED
    assert (
        derive_quality_state([QualityFlag.INSTRUMENT_ID_UNRESOLVED])
        is QualityState.BLOCKED
    )
    assert (
        derive_quality_state([QualityFlag.UNIT_NORMALIZATION_UNAVAILABLE])
        is QualityState.BLOCKED
    )
    assert (
        derive_quality_state([QualityFlag.VENUE_NOT_DECOMPOSABLE])
        is QualityState.BLOCKED
    )


def test_r03_blocked_dominates_non_blocking_flags():
    assert (
        derive_quality_state([QualityFlag.PIT_RISK, QualityFlag.SOURCE_NATIVE])
        is QualityState.BLOCKED
    )
    assert (
        derive_quality_state([QualityFlag.PIT_RISK, QualityFlag.STALE_SOURCE])
        is QualityState.BLOCKED
    )
    assert (
        derive_quality_state([QualityFlag.STALE_SOURCE, QualityFlag.PIT_RISK])
        is QualityState.BLOCKED
    )


def test_r03_blocked_dominates_all_non_blocking_states():
    for downgrade_flag in (
        QualityFlag.STALE_SOURCE,
        QualityFlag.PROVIDER_DEGRADED,
        QualityFlag.PARTIAL_INTERVAL,
        QualityFlag.ACCESS_CLASS_UNVERIFIED,
        QualityFlag.HISTORICAL_DEPTH_UNVERIFIED,
    ):
        for blocking_flag in BLOCKING_QUALITY_FLAGS:
            assert (
                derive_quality_state([downgrade_flag, blocking_flag])
                is QualityState.BLOCKED
            )


def test_r03_has_blocking_flag_still_explicit_predicate():
    assert has_blocking_flag([QualityFlag.PIT_RISK]) is True
    assert has_blocking_flag([QualityFlag.STALE_SOURCE]) is False
    assert has_blocking_flag([]) is False
