"""SENSOR-B4-I09B — storage estimation and non-destructive retention policy.

The estimator is a pure dry-run calculation over measured sample bytes.  It
uses integer arithmetic, keeps T0A and T0B components separate, and labels
confidence by sample coverage rather than inventing a statistical interval.
Retention policy is storage policy only; it never changes evidence semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from .._paths import CONFIG_DIR
from ..contracts.enums import SensorFamily
from .enums import StoragePriority

DEFAULT_RETENTION_CONFIG_PATH = CONFIG_DIR / "retention.yaml"
_SECONDS_PER_DAY = 86_400
_MAX_ESTIMATE_BYTES = (1 << 63) - 1
_LARGE_T0A_THRESHOLD_BYTES = 1024**4


class RetentionError(ValueError):
    """Base typed failure for retention policy or estimation input."""


class RetentionConfigurationError(RetentionError):
    """The retention configuration is not coherent."""


class RetentionPolicyError(RetentionError):
    """A retention request cannot be evaluated safely."""


class StorageEstimationError(RetentionError):
    """A dry-run estimate is invalid or exceeds a configured bound."""


@dataclass(frozen=True)
class RetentionConfig:
    """Operator-configurable retention switches and estimator bounds."""

    schema_version: str = "1.0"
    u2_full_depth_books_enabled: bool = False
    automatic_t0a_destructive_actions: bool = False
    max_estimate_bytes: int = _MAX_ESTIMATE_BYTES
    high_confidence_sample_seconds: int = _SECONDS_PER_DAY
    medium_confidence_sample_seconds: int = 3_600

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise RetentionConfigurationError("schema_version must be nonempty")
        if self.automatic_t0a_destructive_actions:
            raise RetentionConfigurationError(
                "automatic T0A destructive actions are forbidden in v1"
            )
        for name in ("max_estimate_bytes", "high_confidence_sample_seconds", "medium_confidence_sample_seconds"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise RetentionConfigurationError(f"{name} must be a positive integer")
        if self.medium_confidence_sample_seconds > self.high_confidence_sample_seconds:
            raise RetentionConfigurationError(
                "medium confidence sample seconds cannot exceed high confidence sample seconds"
            )

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> RetentionConfig:
        allowed = {
            "schema_version",
            "u2_full_depth_books_enabled",
            "automatic_t0a_destructive_actions",
            "max_estimate_bytes",
            "high_confidence_sample_seconds",
            "medium_confidence_sample_seconds",
        }
        unknown = set(value) - allowed
        if unknown:
            raise RetentionConfigurationError(f"unknown retention config fields: {sorted(unknown)}")
        return cls(**value)


def load_retention_config(path: Path | None = None) -> RetentionConfig:
    """Load and validate the operator-owned retention YAML."""
    config_path = path or DEFAULT_RETENTION_CONFIG_PATH
    value = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RetentionConfigurationError("retention config must be a mapping")
    return RetentionConfig.from_mapping(value)


class UniverseTier(str, Enum):
    """Local storage-policy universe tier, not a market-quality ranking."""

    U0 = "U0"
    U1 = "U1"
    U2 = "U2"


class RetentionPolicy(str, Enum):
    """Non-destructive storage handling policy."""

    PERMANENT = "PERMANENT"
    LOSSLESS_COMPRESS = "LOSSLESS_COMPRESS"
    SELECTIVE = "SELECTIVE"
    COARSE_OR_METRICS = "COARSE_OR_METRICS"
    DISABLED_DEFAULT = "DISABLED_DEFAULT"
    REBUILDABLE = "REBUILDABLE"
    REFUSE_DESTRUCTIVE_T0A = "REFUSE_DESTRUCTIVE_T0A"


@dataclass(frozen=True)
class RetentionDecision:
    """Storage disposition with explicit preservation semantics."""

    sensor_family: SensorFamily | None
    universe_tier: UniverseTier | None
    priority: StoragePriority
    policy: RetentionPolicy
    preserve_t0a: bool
    reason: str
    evidence_flags: tuple[str, ...] = ()


def _priority_for_sensor(sensor_family: SensorFamily) -> StoragePriority:
    if sensor_family in {
        SensorFamily.MECHANICAL_LIQUIDATION,
        SensorFamily.MECHANICAL_OPEN_INTEREST,
        SensorFamily.MECHANICAL_FUNDING,
        SensorFamily.MECHANICAL_POSITIONING,
        SensorFamily.MECHANICAL_BASIS,
    }:
        return StoragePriority.P0
    if sensor_family in {SensorFamily.MECHANICAL_TRADE, SensorFamily.MECHANICAL_BOOK_METRIC}:
        return StoragePriority.P1
    if sensor_family is SensorFamily.MECHANICAL_BOOK_SNAPSHOT:
        return StoragePriority.P2
    raise RetentionPolicyError(f"unmapped sensor family: {sensor_family}")


def retention_policy(
    sensor_family: SensorFamily,
    universe_tier: UniverseTier,
    *,
    config: RetentionConfig | None = None,
) -> RetentionDecision:
    """Return universe-aware handling policy without mutating evidence."""
    policy_config = config or load_retention_config()
    priority = _priority_for_sensor(sensor_family)
    if priority is StoragePriority.P0:
        policy = RetentionPolicy.PERMANENT
        reason = "P0 critical mechanical evidence is permanent"
    elif sensor_family is SensorFamily.MECHANICAL_BOOK_SNAPSHOT:
        if universe_tier is UniverseTier.U0:
            policy = RetentionPolicy.SELECTIVE
            reason = "U0 retains richest feasible book evidence subject to quota"
        elif universe_tier is UniverseTier.U1:
            policy = RetentionPolicy.COARSE_OR_METRICS
            reason = "U1 defaults to coarse book snapshots or metrics"
        elif not policy_config.u2_full_depth_books_enabled:
            policy = RetentionPolicy.DISABLED_DEFAULT
            reason = "U2 full-depth high-frequency books are disabled by default"
        else:
            policy = RetentionPolicy.SELECTIVE
            reason = "U2 full-depth books require an explicit operator promotion"
    elif sensor_family is SensorFamily.MECHANICAL_TRADE:
        policy = (
            RetentionPolicy.PERMANENT
            if universe_tier is UniverseTier.U0
            else RetentionPolicy.SELECTIVE
        )
        reason = "trade raw is permanent in U0 and selective outside U0"
    else:
        policy = RetentionPolicy.PERMANENT
        reason = "P1 source-native metrics are retained permanently"
    return RetentionDecision(
        sensor_family=sensor_family,
        universe_tier=universe_tier,
        priority=priority,
        policy=policy,
        preserve_t0a=True,
        reason=reason,
    )


@dataclass(frozen=True)
class DestructiveRetentionDecision:
    """Result of an attempted destructive retention request."""

    priority: StoragePriority
    allowed: bool
    preserve_t0a: bool
    reason: str
    evidence_flags: tuple[str, ...]


def assess_destructive_retention(
    *,
    priority: StoragePriority,
    is_t0a: bool,
    age_days: int = 0,
    size_bytes: int = 0,
    duplicate_looking: bool = False,
    revised: bool = False,
) -> DestructiveRetentionDecision:
    """Refuse automatic T0A destruction; only rebuildable non-T0A may be evicted."""
    try:
        priority = StoragePriority(priority)
    except ValueError as exc:
        raise RetentionPolicyError(f"unknown storage priority: {priority!r}") from exc
    for name, value in (("age_days", age_days), ("size_bytes", size_bytes)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise RetentionPolicyError(f"{name} must be a nonnegative integer")
    flags: list[str] = []
    if age_days:
        flags.append("OLD")
    if size_bytes >= _LARGE_T0A_THRESHOLD_BYTES:
        flags.append("LARGE")
    if duplicate_looking:
        flags.append("DUPLICATE_LOOKING")
    if revised:
        flags.append("REVISION")
    if is_t0a:
        return DestructiveRetentionDecision(
            priority=priority,
            allowed=False,
            preserve_t0a=True,
            reason="T0A is authoritative; age, duplicate appearance, size, and revision never authorize deletion",
            evidence_flags=tuple(flags),
        )
    if priority is StoragePriority.P3:
        return DestructiveRetentionDecision(
            priority=priority,
            allowed=True,
            preserve_t0a=False,
            reason="P3 rebuildable cache/projection may be compacted or evicted under policy",
            evidence_flags=tuple(flags),
        )
    return DestructiveRetentionDecision(
        priority=priority,
        allowed=False,
        preserve_t0a=True,
        reason="only P3 rebuildable non-T0A data may be automatically evicted",
        evidence_flags=tuple(flags),
    )


class ConfidenceBand(str, Enum):
    """Evidence-quality labels, not statistically calibrated intervals."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass(frozen=True)
class StorageEstimateInput:
    """Measured sample inputs for a dry-run storage estimate."""

    provider: str
    sensor_family: SensorFamily
    universe_tier: UniverseTier
    instrument: str
    expected_days: int
    sample_raw_bytes: int
    sample_projection_bytes: int
    sample_duration: int
    available_budget_bytes: int

    def __post_init__(self) -> None:
        for name in ("provider", "instrument"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise StorageEstimationError(f"{name} must be a nonempty string")
        for name in (
            "expected_days",
            "sample_raw_bytes",
            "sample_projection_bytes",
            "sample_duration",
            "available_budget_bytes",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise StorageEstimationError(f"{name} must be an integer")
        if self.expected_days <= 0:
            raise StorageEstimationError("expected_days must be > 0")
        if self.sample_duration <= 0:
            raise StorageEstimationError("sample_duration must be > 0")
        if self.sample_raw_bytes < 0 or self.sample_projection_bytes < 0:
            raise StorageEstimationError("sample bytes must be >= 0")
        if self.available_budget_bytes < 0:
            raise StorageEstimationError("available_budget_bytes must be >= 0")


@dataclass(frozen=True)
class StorageEstimate:
    """Pure estimator output; totals are exact integer reconciliations."""

    provider: str
    sensor_family: SensorFamily
    universe_tier: UniverseTier
    instrument: str
    expected_days: int
    bytes_per_day_raw: int
    bytes_per_day_projection: int
    estimated_total: int
    confidence_band: ConfidenceBand
    available_budget_bytes: int
    budget_excess_bytes: int
    within_budget: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "sensor_family": self.sensor_family.value,
            "universe_tier": self.universe_tier.value,
            "instrument": self.instrument,
            "expected_days": self.expected_days,
            "bytes_per_day_raw": self.bytes_per_day_raw,
            "bytes_per_day_projection": self.bytes_per_day_projection,
            "estimated_total": self.estimated_total,
            "confidence_band": self.confidence_band.value,
            "available_budget_bytes": self.available_budget_bytes,
            "budget_excess_bytes": self.budget_excess_bytes,
            "within_budget": self.within_budget,
        }


def _ceil_div(numerator: int, denominator: int) -> int:
    return (numerator + denominator - 1) // denominator


def _confidence(sample: StorageEstimateInput, config: RetentionConfig) -> ConfidenceBand:
    if sample.sample_raw_bytes == 0 and sample.sample_projection_bytes == 0:
        return ConfidenceBand.LOW
    if sample.sample_duration >= config.high_confidence_sample_seconds:
        return ConfidenceBand.HIGH
    if sample.sample_duration >= config.medium_confidence_sample_seconds:
        return ConfidenceBand.MEDIUM
    return ConfidenceBand.LOW


def estimate_storage(
    sample: StorageEstimateInput,
    *,
    config: RetentionConfig | None = None,
) -> StorageEstimate:
    """Estimate raw and projection bytes separately with integer scaling."""
    policy = config or load_retention_config()
    raw_per_day = _ceil_div(sample.sample_raw_bytes * _SECONDS_PER_DAY, sample.sample_duration)
    projection_per_day = _ceil_div(
        sample.sample_projection_bytes * _SECONDS_PER_DAY, sample.sample_duration
    )
    estimated_total = raw_per_day * sample.expected_days + projection_per_day * sample.expected_days
    if estimated_total > policy.max_estimate_bytes or estimated_total < 0:
        raise StorageEstimationError("estimated total exceeds configured safe bound")
    budget_excess = max(0, estimated_total - sample.available_budget_bytes)
    return StorageEstimate(
        provider=sample.provider,
        sensor_family=sample.sensor_family,
        universe_tier=sample.universe_tier,
        instrument=sample.instrument,
        expected_days=sample.expected_days,
        bytes_per_day_raw=raw_per_day,
        bytes_per_day_projection=projection_per_day,
        estimated_total=estimated_total,
        confidence_band=_confidence(sample, policy),
        available_budget_bytes=sample.available_budget_bytes,
        budget_excess_bytes=budget_excess,
        within_budget=budget_excess == 0,
    )


__all__ = [
    "ConfidenceBand",
    "DEFAULT_RETENTION_CONFIG_PATH",
    "DestructiveRetentionDecision",
    "RetentionConfig",
    "RetentionConfigurationError",
    "RetentionDecision",
    "RetentionError",
    "RetentionPolicy",
    "RetentionPolicyError",
    "StorageEstimate",
    "StorageEstimateInput",
    "StorageEstimationError",
    "UniverseTier",
    "assess_destructive_retention",
    "estimate_storage",
    "load_retention_config",
    "retention_policy",
]
