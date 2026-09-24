"""SENSOR-B4-I09A — quota classification and safe write policy."""

from __future__ import annotations

import math
from datetime import UTC, datetime
from pathlib import Path

import pytest

from crypto_sensor_fabric.storage.enums import DiskPressure, StoragePriority
from crypto_sensor_fabric.storage.quota import (
    QuotaConfig,
    QuotaFacts,
    QuotaFactsError,
    QuotaWritePolicyError,
    WriteDisposition,
    classify_storage,
    decide_storage_write,
    load_quota_config,
)

OBSERVED_AT = datetime(2026, 1, 1, tzinfo=UTC)


def _state(
    used: int,
    *,
    capacity: int = 1000,
    free: int | None = None,
    config: QuotaConfig | None = None,
):
    return classify_storage(
        QuotaFacts(
            capacity_bytes=capacity,
            used_bytes=used,
            free_bytes=capacity - used if free is None else free,
        ),
        config=config,
        observed_at=OBSERVED_AT,
    )


def test_watermark_exact_boundaries() -> None:
    assert _state(699).pressure_state is DiskPressure.NORMAL
    assert _state(700).pressure_state is DiskPressure.WATCH
    assert _state(849).pressure_state is DiskPressure.WATCH
    assert _state(850).pressure_state is DiskPressure.CONSTRAINED
    assert _state(949).pressure_state is DiskPressure.CONSTRAINED
    assert _state(950).pressure_state is DiskPressure.CRITICAL
    assert _state(1000).pressure_state is DiskPressure.CRITICAL


def test_absolute_floor_equality_is_safe_and_one_byte_below_blocks() -> None:
    state = classify_storage(
        QuotaFacts(
            capacity_bytes=1000,
            used_bytes=500,
            free_bytes=500,
            absolute_free_floor_bytes=400,
        ),
        observed_at=OBSERVED_AT,
    )
    safe = decide_storage_write(
        state, projected_write_bytes=100, priority=StoragePriority.P1
    )
    assert safe.disposition is WriteDisposition.PROCEED
    assert safe.projected_free_bytes == 400
    blocked = decide_storage_write(
        state, projected_write_bytes=101, priority=StoragePriority.P0
    )
    assert blocked.disposition is WriteDisposition.BLOCK
    assert blocked.blocked_code == "STORAGE_CAPACITY_BLOCKED"
    assert blocked.projected_free_bytes == 399


def test_normal_percent_can_still_be_blocked_by_absolute_floor() -> None:
    state = classify_storage(
        QuotaFacts(
            capacity_bytes=1000,
            used_bytes=500,
            free_bytes=500,
            absolute_free_floor_bytes=450,
        ),
        observed_at=OBSERVED_AT,
    )
    assert state.pressure_state is DiskPressure.NORMAL
    decision = decide_storage_write(
        state, projected_write_bytes=100, priority=StoragePriority.P0
    )
    assert decision.disposition is WriteDisposition.BLOCK


def test_watch_with_plenty_free_space_warns_but_proceeds() -> None:
    state = classify_storage(
        QuotaFacts(
            capacity_bytes=1000,
            used_bytes=700,
            free_bytes=300,
            absolute_free_floor_bytes=10,
        ),
        observed_at=OBSERVED_AT,
    )
    decision = decide_storage_write(
        state, projected_write_bytes=10, priority=StoragePriority.P1
    )
    assert decision.disposition is WriteDisposition.WARN
    assert decision.warning is True


def test_critical_blocks_nonessential_but_not_safe_p0() -> None:
    state = _state(950, free=50, config=QuotaConfig(absolute_free_floor_bytes=0))
    p2 = decide_storage_write(
        state, projected_write_bytes=1, priority=StoragePriority.P2
    )
    assert p2.disposition is WriteDisposition.BLOCK
    p0 = decide_storage_write(
        state, projected_write_bytes=1, priority=StoragePriority.P0
    )
    assert p0.disposition is WriteDisposition.WARN
    unsafe_p0 = decide_storage_write(
        state, projected_write_bytes=51, priority=StoragePriority.P0
    )
    assert unsafe_p0.disposition is WriteDisposition.BLOCK


def test_constrained_defers_p2_and_pauses_p3_before_p0() -> None:
    state = _state(850, free=150, config=QuotaConfig(absolute_free_floor_bytes=0))
    p0 = decide_storage_write(
        state, projected_write_bytes=10, priority=StoragePriority.P0
    )
    p2 = decide_storage_write(
        state, projected_write_bytes=10, priority=StoragePriority.P2
    )
    p3 = decide_storage_write(
        state, projected_write_bytes=10, priority=StoragePriority.P3
    )
    assert p0.disposition is WriteDisposition.PROCEED
    assert p2.disposition is WriteDisposition.DEFER
    assert p3.disposition is WriteDisposition.PAUSE


def test_zero_free_space_is_critical_and_floor_is_hard() -> None:
    state = _state(1000, free=0)
    decision = decide_storage_write(
        state, projected_write_bytes=0, priority=StoragePriority.P0
    )
    assert state.pressure_state is DiskPressure.CRITICAL
    assert decision.disposition is WriteDisposition.BLOCK


@pytest.mark.parametrize(
    "facts",
    [
        {"capacity_bytes": 0, "used_bytes": 0, "free_bytes": 0},
        {"capacity_bytes": 100, "used_bytes": -1, "free_bytes": 101},
        {"capacity_bytes": 100, "used_bytes": 101, "free_bytes": 0},
        {"capacity_bytes": 100, "used_bytes": 50, "free_bytes": 101},
        {"capacity_bytes": 100, "used_bytes": 60, "free_bytes": 60},
    ],
)
def test_invalid_or_contradictory_filesystem_facts_fail_typed(
    facts: dict[str, int],
) -> None:
    with pytest.raises(QuotaFactsError):
        classify_storage(QuotaFacts(**facts), observed_at=OBSERVED_AT)


@pytest.mark.parametrize("ratio", [math.nan, math.inf, -math.inf, -0.1, 1.1])
def test_invalid_supplied_utilization_fails_typed(ratio: float) -> None:
    with pytest.raises(QuotaFactsError):
        classify_storage(
            QuotaFacts(
                capacity_bytes=100,
                used_bytes=50,
                free_bytes=50,
                utilization_ratio=ratio,
            ),
            observed_at=OBSERVED_AT,
        )


def test_supplied_utilization_must_match_byte_derived_truth() -> None:
    with pytest.raises(QuotaFactsError, match="contradicts"):
        classify_storage(
            QuotaFacts(
                capacity_bytes=100,
                used_bytes=50,
                free_bytes=50,
                utilization_ratio=0.9,
            ),
            observed_at=OBSERVED_AT,
        )


def test_negative_projected_write_and_unknown_priority_fail_typed() -> None:
    state = _state(100)
    with pytest.raises(QuotaWritePolicyError):
        decide_storage_write(
            state, projected_write_bytes=-1, priority=StoragePriority.P0
        )
    with pytest.raises(QuotaWritePolicyError):
        decide_storage_write(state, projected_write_bytes=1, priority="P9")  # type: ignore[arg-type]


def test_loaded_config_is_operator_configurable() -> None:
    config = load_quota_config(Path(__file__).parents[3] / "config/crypto_sensor_fabric/quota.yaml")
    assert (config.watch_percent, config.constrained_percent, config.critical_percent) == (
        70,
        85,
        95,
    )
    assert config.absolute_free_floor_bytes == 10 * 1024**3
