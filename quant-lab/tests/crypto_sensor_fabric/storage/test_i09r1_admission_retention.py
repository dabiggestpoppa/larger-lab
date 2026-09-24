"""SENSOR-B4-I09R1B — admission boundary and retention configuration safety."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.storage.enums import StoragePriority
from crypto_sensor_fabric.storage.quota import (
    STORAGE_CAPACITY_BLOCKED,
    QuotaConfig,
    QuotaFacts,
    WriteDisposition,
    classify_storage,
)
from crypto_sensor_fabric.storage.retention import (
    ConfidenceBand,
    RetentionConfig,
    RetentionConfigurationError,
    StorageEstimateInput,
    UniverseTier,
    assess_destructive_retention,
    assess_storage_admission,
    estimate_storage,
)

_CONFIG = QuotaConfig(absolute_free_floor_bytes=20)
_OBSERVED_AT = datetime(2026, 1, 1, tzinfo=UTC)


def _state(used: int, *, capacity: int = 1000, floor: int = 20):
    return classify_storage(
        QuotaFacts(
            capacity_bytes=capacity,
            used_bytes=used,
            free_bytes=capacity - used,
            absolute_free_floor_bytes=floor,
        ),
        config=_CONFIG,
        observed_at=_OBSERVED_AT,
    )


def _estimate(
    *,
    total: int = 100,
    budget: int = 1_000,
    duration: int = 86_400,
):
    return estimate_storage(
        StorageEstimateInput(
            provider="KRAKEN_FUTURES",
            sensor_family=SensorFamily.MECHANICAL_TRADE,
            universe_tier=UniverseTier.U0,
            instrument="BTC-PERP",
            expected_days=1,
            sample_raw_bytes=total,
            sample_projection_bytes=0,
            sample_duration=duration,
            available_budget_bytes=budget,
        ),
        config=RetentionConfig(),
    )


def test_over_budget_planned_work_is_explicitly_blocked() -> None:
    decision = assess_storage_admission(
        _estimate(total=101, budget=100),
        _state(100),
        priority=StoragePriority.P0,
        quota_config=_CONFIG,
    )
    assert decision.disposition is WriteDisposition.BLOCK
    assert decision.blocked_code == STORAGE_CAPACITY_BLOCKED
    assert "exceeds configured available budget" in decision.reason


def test_budget_safe_estimate_that_breaches_floor_is_blocked() -> None:
    decision = assess_storage_admission(
        _estimate(total=81, budget=2_000),
        _state(900),
        priority=StoragePriority.P0,
        quota_config=_CONFIG,
    )
    assert decision.disposition is WriteDisposition.BLOCK
    assert decision.projected_free_bytes == 19
    assert decision.blocked_code == STORAGE_CAPACITY_BLOCKED


def test_budget_safe_and_quota_safe_work_is_admitted() -> None:
    decision = assess_storage_admission(
        _estimate(total=100),
        _state(100),
        priority=StoragePriority.P0,
        quota_config=_CONFIG,
    )
    assert decision.disposition is WriteDisposition.PROCEED


@pytest.mark.parametrize(
    ("used", "priority", "expected"),
    [
        (850, StoragePriority.P2, WriteDisposition.DEFER),
        (850, StoragePriority.P3, WriteDisposition.PAUSE),
        (950, StoragePriority.P1, WriteDisposition.BLOCK),
        (950, StoragePriority.P2, WriteDisposition.BLOCK),
        (950, StoragePriority.P3, WriteDisposition.BLOCK),
    ],
)
def test_admission_preserves_quota_priority_matrix(
    used: int, priority: StoragePriority, expected: WriteDisposition
) -> None:
    decision = assess_storage_admission(
        _estimate(total=10),
        _state(used),
        priority=priority,
        quota_config=_CONFIG,
    )
    assert decision.disposition is expected


@pytest.mark.parametrize("field", ["u2_full_depth_books_enabled", "automatic_t0a_destructive_actions"])
@pytest.mark.parametrize("value", ["false", "true", 0, 1, None, [], {}])
def test_retention_boolean_fields_reject_type_confusion(field: str, value: object) -> None:
    with pytest.raises(RetentionConfigurationError, match="exact bool"):
        RetentionConfig(**{field: value})


@pytest.mark.parametrize("value", ["", " ", 0, 1, None, [], {}])
def test_schema_version_requires_nonempty_string(value: object) -> None:
    with pytest.raises(RetentionConfigurationError, match="nonempty string"):
        RetentionConfig(schema_version=value)  # type: ignore[arg-type]


@pytest.mark.parametrize("priority", list(StoragePriority))
@pytest.mark.parametrize(
    "flags",
    [
        {"age_days": 10_000},
        {"size_bytes": 100 * 1024**4},
        {"duplicate_looking": True},
        {"revised": True},
        {
            "age_days": 10_000,
            "size_bytes": 100 * 1024**4,
            "duplicate_looking": True,
            "revised": True,
        },
    ],
)
def test_t0a_refusal_is_priority_independent(
    priority: StoragePriority, flags: dict[str, int | bool]
) -> None:
    decision = assess_destructive_retention(
        priority=priority, is_t0a=True, **flags
    )
    assert decision.allowed is False
    assert decision.preserve_t0a is True


def test_p3_t0a_cannot_inherit_p3_eviction_permission() -> None:
    t0a = assess_destructive_retention(priority=StoragePriority.P3, is_t0a=True)
    non_t0a = assess_destructive_retention(priority=StoragePriority.P3, is_t0a=False)
    assert t0a.allowed is False
    assert non_t0a.allowed is True


def test_high_label_is_duration_coverage_not_representativeness() -> None:
    estimate = _estimate(total=1, duration=86_400)
    assert estimate.confidence_band is ConfidenceBand.HIGH
    assert "not statistically calibrated" in (ConfidenceBand.HIGH.__doc__ or "").lower()
