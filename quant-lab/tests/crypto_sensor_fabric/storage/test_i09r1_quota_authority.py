"""SENSOR-B4-I09R1A — quota authority and fail-closed state validation."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from crypto_sensor_fabric.storage.enums import DiskPressure, StoragePriority
from crypto_sensor_fabric.storage.models import StorageQuotaState
from crypto_sensor_fabric.storage.quota import (
    QuotaConfig,
    QuotaFacts,
    QuotaWritePolicyError,
    WriteDisposition,
    classify_storage,
    decide_storage_write,
)

_CONFIG = QuotaConfig(absolute_free_floor_bytes=20)
_OBSERVED_AT = datetime(2026, 1, 1, tzinfo=UTC)


def _raw_state(
    pressure: DiskPressure = DiskPressure.CRITICAL,
    *,
    used: int = 950,
    free: int = 50,
    ratio: float = 0.95,
    floor: int = 20,
) -> StorageQuotaState:
    return StorageQuotaState(
        pressure_state=pressure,
        priority_class=None,
        used_bytes=used,
        capacity_bytes=1000,
        free_bytes=free,
        utilization_ratio=ratio,
        absolute_free_floor_bytes=floor,
        observed_at=_OBSERVED_AT,
    )


def test_caller_controlled_essential_authority_is_removed() -> None:
    state = classify_storage(
        QuotaFacts(
            capacity_bytes=1000,
            used_bytes=950,
            free_bytes=50,
            absolute_free_floor_bytes=0,
        ),
        config=QuotaConfig(absolute_free_floor_bytes=0),
        observed_at=_OBSERVED_AT,
    )
    with pytest.raises(TypeError, match="essential"):
        decide_storage_write(  # type: ignore[call-arg]
            state,
            projected_write_bytes=0,
            priority=StoragePriority.P1,
            essential=True,
        )


@pytest.mark.parametrize(
    "priority", [StoragePriority.P1, StoragePriority.P2, StoragePriority.P3]
)
def test_critical_non_p0_priorities_always_block(priority: StoragePriority) -> None:
    state = classify_storage(
        QuotaFacts(
            capacity_bytes=1000,
            used_bytes=950,
            free_bytes=50,
            absolute_free_floor_bytes=0,
        ),
        config=QuotaConfig(absolute_free_floor_bytes=0),
        observed_at=_OBSERVED_AT,
    )
    assert (
        decide_storage_write(
            state, projected_write_bytes=0, priority=priority, config=QuotaConfig(absolute_free_floor_bytes=0)
        ).disposition
        is WriteDisposition.BLOCK
    )


def test_p0_critical_is_warn_only_while_floor_safe() -> None:
    state = _raw_state()
    safe = decide_storage_write(
        state, projected_write_bytes=0, priority=StoragePriority.P0, config=_CONFIG
    )
    blocked = decide_storage_write(
        state, projected_write_bytes=31, priority=StoragePriority.P0, config=_CONFIG
    )
    assert safe.disposition is WriteDisposition.WARN
    assert blocked.disposition is WriteDisposition.BLOCK
    assert blocked.projected_free_bytes == 19


@pytest.mark.parametrize(
    "state",
    [
        _raw_state(DiskPressure.NORMAL),
        _raw_state(DiskPressure.WATCH),
        _raw_state(DiskPressure.CRITICAL, used=100, free=900, ratio=0.1),
    ],
)
def test_forged_or_stale_pressure_label_fails_closed(state: StorageQuotaState) -> None:
    with pytest.raises(QuotaWritePolicyError, match="pressure_state contradicts"):
        decide_storage_write(
            state,
            projected_write_bytes=0,
            priority=StoragePriority.P2,
            config=_CONFIG,
        )


@pytest.mark.parametrize(
    "state",
    [
        _raw_state(used=600, free=300, ratio=0.6),
        _raw_state(used=950, free=50, ratio=0.5),
    ],
)
def test_inconsistent_used_free_capacity_or_ratio_fails_closed(
    state: StorageQuotaState,
) -> None:
    with pytest.raises(QuotaWritePolicyError, match="untrusted quota state"):
        decide_storage_write(
            state,
            projected_write_bytes=0,
            priority=StoragePriority.P2,
            config=_CONFIG,
        )


def test_custom_watermarks_remain_the_revalidation_authority() -> None:
    custom = QuotaConfig(
        watch_percent=50,
        constrained_percent=60,
        critical_percent=80,
        absolute_free_floor_bytes=20,
    )
    state = _raw_state(DiskPressure.CONSTRAINED, used=700, free=300, ratio=0.7)
    decision = decide_storage_write(
        state,
        projected_write_bytes=0,
        priority=StoragePriority.P2,
        config=custom,
    )
    assert decision.disposition is WriteDisposition.DEFER
    with pytest.raises(QuotaWritePolicyError):
        decide_storage_write(
            state,
            projected_write_bytes=0,
            priority=StoragePriority.P2,
            config=_CONFIG,
        )
