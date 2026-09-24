"""SENSOR-B4-I09B — estimator, priority, and retention policy."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.storage.enums import DiskPressure, StoragePriority
from crypto_sensor_fabric.storage.quota import (
    QuotaConfig,
    QuotaFacts,
    WriteDisposition,
    classify_storage,
    decide_storage_write,
)
from crypto_sensor_fabric.storage.retention import (
    ConfidenceBand,
    RetentionConfig,
    RetentionPolicy,
    StorageEstimateInput,
    StorageEstimationError,
    UniverseTier,
    RetentionConfigurationError,
    assess_destructive_retention,
    estimate_storage,
    load_retention_config,
    retention_policy,
)


def _sample(**overrides: object) -> StorageEstimateInput:
    values: dict[str, object] = {
        "provider": "KRAKEN_FUTURES",
        "sensor_family": SensorFamily.MECHANICAL_TRADE,
        "universe_tier": UniverseTier.U0,
        "instrument": "BTC-PERP",
        "expected_days": 10,
        "sample_raw_bytes": 86_400,
        "sample_projection_bytes": 8_640,
        "sample_duration": 86_400,
        "available_budget_bytes": 2_000_000,
    }
    values.update(overrides)
    return StorageEstimateInput(**values)  # type: ignore[arg-type]


def test_estimator_is_deterministic_and_components_reconcile() -> None:
    sample = _sample()
    first = estimate_storage(sample)
    second = estimate_storage(sample)
    assert first == second
    assert first.bytes_per_day_raw == 86_400
    assert first.bytes_per_day_projection == 8_640
    assert first.estimated_total == (
        first.bytes_per_day_raw * sample.expected_days
        + first.bytes_per_day_projection * sample.expected_days
    )
    assert first.estimated_total == 950_400
    assert first.within_budget is True


def test_increasing_expected_days_never_reduces_estimate() -> None:
    short = estimate_storage(_sample(expected_days=1))
    long = estimate_storage(_sample(expected_days=1000))
    assert long.estimated_total > short.estimated_total


def test_budget_overrun_is_visible_before_execution() -> None:
    estimate = estimate_storage(_sample(available_budget_bytes=100))
    assert estimate.within_budget is False
    assert estimate.budget_excess_bytes == estimate.estimated_total - 100


def test_confidence_is_sample_coverage_not_fake_numeric_precision() -> None:
    low = estimate_storage(_sample(sample_duration=60, sample_raw_bytes=1))
    medium = estimate_storage(_sample(sample_duration=3_600))
    high = estimate_storage(_sample(sample_duration=86_400))
    empty = estimate_storage(_sample(sample_raw_bytes=0, sample_projection_bytes=0))
    assert low.confidence_band is ConfidenceBand.LOW
    assert medium.confidence_band is ConfidenceBand.MEDIUM
    assert high.confidence_band is ConfidenceBand.HIGH
    assert empty.confidence_band is ConfidenceBand.LOW
    assert all(
        isinstance(band.value, str)
        for band in (low.confidence_band, medium.confidence_band, high.confidence_band)
    )


@pytest.mark.parametrize(
    "overrides",
    [
        {"sample_duration": 0},
        {"sample_duration": -1},
        {"sample_raw_bytes": -1},
        {"sample_projection_bytes": -1},
        {"expected_days": 0},
        {"available_budget_bytes": -1},
    ],
)
def test_invalid_estimator_inputs_fail_typed(overrides: dict[str, int]) -> None:
    with pytest.raises(StorageEstimationError):
        estimate_storage(_sample(**overrides))


def test_absurd_estimate_fails_safely() -> None:
    tiny_max = RetentionConfig(max_estimate_bytes=10)
    with pytest.raises(StorageEstimationError, match="exceeds"):
        estimate_storage(
            _sample(
                sample_raw_bytes=1_000_000_000,
                sample_projection_bytes=1_000_000_000,
                sample_duration=1,
            ),
            config=tiny_max,
        )


def test_estimator_never_mutates_storage(tmp_path: Path) -> None:
    root = tmp_path / "lake"
    root.mkdir()
    sentinel = root / "T0A"
    sentinel.write_bytes(b"authoritative")
    before = sentinel.read_bytes()
    estimate_storage(_sample())
    assert sentinel.read_bytes() == before
    assert list(root.iterdir()) == [sentinel]


def test_universe_policy_is_explicit_and_u2_books_off_by_default() -> None:
    config = RetentionConfig()
    u0 = retention_policy(
        SensorFamily.MECHANICAL_BOOK_SNAPSHOT, UniverseTier.U0, config=config
    )
    u1 = retention_policy(
        SensorFamily.MECHANICAL_BOOK_SNAPSHOT, UniverseTier.U1, config=config
    )
    u2 = retention_policy(
        SensorFamily.MECHANICAL_BOOK_SNAPSHOT, UniverseTier.U2, config=config
    )
    assert u0.policy is RetentionPolicy.SELECTIVE
    assert u1.policy is RetentionPolicy.COARSE_OR_METRICS
    assert u2.policy is RetentionPolicy.DISABLED_DEFAULT
    assert u1.policy is not u0.policy
    assert u2.preserve_t0a is True


def test_u0_richness_does_not_bypass_quota_safety() -> None:
    state = classify_storage(
        QuotaFacts(capacity_bytes=1000, used_bytes=960, free_bytes=40),
        config=QuotaConfig(absolute_free_floor_bytes=50),
        observed_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert state.pressure_state is DiskPressure.CRITICAL
    decision = decide_storage_write(
        state,
        projected_write_bytes=0,
        priority=StoragePriority.P0,
        config=QuotaConfig(absolute_free_floor_bytes=50),
    )
    assert decision.disposition is WriteDisposition.BLOCK


def test_storage_priority_does_not_change_evidence_semantics() -> None:
    decision = retention_policy(
        SensorFamily.MECHANICAL_LIQUIDATION, UniverseTier.U2
    )
    assert decision.priority is StoragePriority.P0
    assert decision.policy is RetentionPolicy.PERMANENT
    assert decision.preserve_t0a is True


@pytest.mark.parametrize(
    "overrides",
    [
        {"age_days": 3650},
        {"size_bytes": 5 * 1024**4},
        {"duplicate_looking": True},
        {"revised": True},
        {"age_days": 3650, "size_bytes": 5 * 1024**4, "duplicate_looking": True, "revised": True},
    ],
)
def test_t0a_is_never_automatically_deleted(overrides: dict[str, int | bool]) -> None:
    decision = assess_destructive_retention(
        priority=StoragePriority.P0, is_t0a=True, **overrides
    )
    assert decision.allowed is False
    assert decision.preserve_t0a is True
    assert "T0A is authoritative" in decision.reason


def test_only_rebuildable_non_t0a_is_evictable() -> None:
    p3 = assess_destructive_retention(priority=StoragePriority.P3, is_t0a=False)
    p2 = assess_destructive_retention(priority=StoragePriority.P2, is_t0a=False)
    assert p3.allowed is True
    assert p2.allowed is False


def test_config_cannot_enable_automatic_t0a_destruction() -> None:
    with pytest.raises(RetentionConfigurationError, match="forbidden"):
        RetentionConfig(automatic_t0a_destructive_actions=True)


def test_retention_config_loads_with_safe_defaults() -> None:
    config = load_retention_config(
        Path(__file__).parents[3] / "config/crypto_sensor_fabric/retention.yaml"
    )
    assert config.automatic_t0a_destructive_actions is False
    assert config.u2_full_depth_books_enabled is False
    assert config.max_estimate_bytes == (1 << 63) - 1
