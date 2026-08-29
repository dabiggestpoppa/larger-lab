"""Quality-state contract tests (B1-T53 and conservative aggregation)."""

from __future__ import annotations

from crypto_sensor_fabric.contracts.enums import QualityFlag, QualityState
from crypto_sensor_fabric.contracts.quality import (
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
