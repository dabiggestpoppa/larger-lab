"""SENSOR-B4-I09 — storage pressure classification and safe write policy.

The frozen I01 types remain authoritative: :class:`StorageQuotaState`,
:class:`DiskPressure`, and :class:`StoragePriority` are reused rather than
replaced.  This module only supplies config-driven classification and a
side-effect-free decision result.  It never deletes, mutates, or opens storage.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from .._paths import CONFIG_DIR
from .enums import DiskPressure, StoragePriority
from .models import StorageQuotaState

DEFAULT_QUOTA_CONFIG_PATH = CONFIG_DIR / "quota.yaml"
STORAGE_CAPACITY_BLOCKED = "STORAGE_CAPACITY_BLOCKED"
_GIB = 1024**3


class QuotaError(ValueError):
    """Base typed failure for invalid quota policy or contradictory facts."""


class QuotaConfigurationError(QuotaError):
    """The quota configuration is not internally coherent."""


class QuotaFactsError(QuotaError):
    """The supplied filesystem facts are invalid or contradictory."""


class QuotaWritePolicyError(QuotaError):
    """A write request cannot be evaluated safely."""


@dataclass(frozen=True)
class QuotaConfig:
    """Config-driven percentage and absolute storage safety policy."""

    watch_percent: int = 70
    constrained_percent: int = 85
    critical_percent: int = 95
    absolute_free_floor_bytes: int = 10 * _GIB
    capacity_reconciliation_tolerance_bytes: int = 0
    utilization_ratio_tolerance: float = 0.01

    def __post_init__(self) -> None:
        for name in (
            "watch_percent",
            "constrained_percent",
            "critical_percent",
            "absolute_free_floor_bytes",
            "capacity_reconciliation_tolerance_bytes",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise QuotaConfigurationError(f"{name} must be an integer")
            if value < 0:
                raise QuotaConfigurationError(f"{name} must be >= 0")
        if not 0 < self.watch_percent < self.constrained_percent < self.critical_percent <= 100:
            raise QuotaConfigurationError(
                "watermarks must satisfy 0 < watch < constrained < critical <= 100"
            )
        if not math.isfinite(self.utilization_ratio_tolerance) or self.utilization_ratio_tolerance < 0:
            raise QuotaConfigurationError("utilization_ratio_tolerance must be finite and >= 0")

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> QuotaConfig:
        allowed = {
            "watch_percent",
            "constrained_percent",
            "critical_percent",
            "absolute_free_floor_bytes",
            "capacity_reconciliation_tolerance_bytes",
            "utilization_ratio_tolerance",
        }
        unknown = set(value) - allowed
        if unknown:
            raise QuotaConfigurationError(f"unknown quota config fields: {sorted(unknown)}")
        return cls(**value)


def load_quota_config(path: Path | None = None) -> QuotaConfig:
    """Load and validate the operator-owned quota YAML."""
    config_path = path or DEFAULT_QUOTA_CONFIG_PATH
    value = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise QuotaConfigurationError("quota config must be a mapping")
    return QuotaConfig.from_mapping(value)


@dataclass(frozen=True)
class QuotaFacts:
    """Filesystem facts supplied to the deterministic classifier."""

    capacity_bytes: int
    used_bytes: int
    free_bytes: int
    utilization_ratio: float | None = None
    absolute_free_floor_bytes: int | None = None

    def __post_init__(self) -> None:
        for name in ("capacity_bytes", "used_bytes", "free_bytes"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise QuotaFactsError(f"{name} must be an integer")
            if value < 0:
                raise QuotaFactsError(f"{name} must be >= 0")
        if self.capacity_bytes == 0:
            raise QuotaFactsError("capacity_bytes must be > 0")
        if self.used_bytes > self.capacity_bytes:
            raise QuotaFactsError("used_bytes cannot exceed capacity_bytes")
        if self.free_bytes > self.capacity_bytes:
            raise QuotaFactsError("free_bytes cannot exceed capacity_bytes")
        if self.utilization_ratio is not None and (
            not isinstance(self.utilization_ratio, (int, float))
            or isinstance(self.utilization_ratio, bool)
            or not math.isfinite(float(self.utilization_ratio))
            or not 0.0 <= float(self.utilization_ratio) <= 1.0
        ):
            raise QuotaFactsError("utilization_ratio must be finite and in [0, 1]")
        if self.absolute_free_floor_bytes is not None and (
            isinstance(self.absolute_free_floor_bytes, bool)
            or not isinstance(self.absolute_free_floor_bytes, int)
            or self.absolute_free_floor_bytes < 0
        ):
            raise QuotaFactsError("absolute_free_floor_bytes must be a nonnegative integer")


def _derived_ratio(facts: QuotaFacts) -> float:
    return facts.used_bytes / facts.capacity_bytes


def _pressure_from_ratio(used: int, capacity: int, config: QuotaConfig) -> DiskPressure:
    # Integer cross-products keep threshold decisions independent of binary
    # float rounding.  Equality belongs to the higher pressure state.
    if used * 100 >= capacity * config.critical_percent:
        return DiskPressure.CRITICAL
    if used * 100 >= capacity * config.constrained_percent:
        return DiskPressure.CONSTRAINED
    if used * 100 >= capacity * config.watch_percent:
        return DiskPressure.WATCH
    return DiskPressure.NORMAL


def classify_storage(
    facts: QuotaFacts,
    *,
    config: QuotaConfig | None = None,
    observed_at: datetime | None = None,
) -> StorageQuotaState:
    """Classify facts using byte-derived utilization and configured floors.

    ``used + free`` must equal capacity within the configured reconciliation
    tolerance.  A supplied utilization ratio is checked against the derived
    value but never replaces it.
    """
    policy = config or load_quota_config()
    tolerance = policy.capacity_reconciliation_tolerance_bytes
    if abs(facts.used_bytes + facts.free_bytes - facts.capacity_bytes) > tolerance:
        raise QuotaFactsError("used_bytes + free_bytes contradicts capacity_bytes")
    derived = _derived_ratio(facts)
    if facts.utilization_ratio is not None and not math.isclose(
        float(facts.utilization_ratio), derived, abs_tol=policy.utilization_ratio_tolerance
    ):
        raise QuotaFactsError("supplied utilization_ratio contradicts byte-derived utilization")
    floor = (
        policy.absolute_free_floor_bytes
        if facts.absolute_free_floor_bytes is None
        else facts.absolute_free_floor_bytes
    )
    return StorageQuotaState(
        pressure_state=_pressure_from_ratio(facts.used_bytes, facts.capacity_bytes, policy),
        priority_class=None,
        used_bytes=facts.used_bytes,
        capacity_bytes=facts.capacity_bytes,
        free_bytes=facts.free_bytes,
        utilization_ratio=derived,
        absolute_free_floor_bytes=floor,
        observed_at=observed_at or datetime.now(UTC),
    )


class WriteDisposition(str, Enum):
    """Local side-effect-free disposition vocabulary for a write request."""

    PROCEED = "PROCEED"
    WARN = "WARN"
    DEFER = "DEFER"
    PAUSE = "PAUSE"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class QuotaWriteDecision:
    """Explainable result; it carries no filesystem operation."""

    disposition: WriteDisposition
    reason: str
    projected_free_bytes: int
    absolute_free_floor_bytes: int
    pressure_state: DiskPressure
    priority: StoragePriority
    warning: bool = False
    blocked_code: str | None = None


def _verified_storage_state(
    state: StorageQuotaState,
    config: QuotaConfig,
) -> StorageQuotaState:
    """Reconcile a supplied snapshot and rederive its pressure from bytes."""
    for name in ("used_bytes", "capacity_bytes", "free_bytes"):
        value = getattr(state, name)
        if isinstance(value, bool) or not isinstance(value, int):
            raise QuotaWritePolicyError(f"state {name} must be an integer")
    if state.absolute_free_floor_bytes is not None and (
        isinstance(state.absolute_free_floor_bytes, bool)
        or not isinstance(state.absolute_free_floor_bytes, int)
        or state.absolute_free_floor_bytes < 0
    ):
        raise QuotaWritePolicyError("state absolute_free_floor_bytes must be a nonnegative integer")
    if (
        isinstance(state.utilization_ratio, bool)
        or not isinstance(state.utilization_ratio, (int, float))
        or not math.isfinite(float(state.utilization_ratio))
    ):
        raise QuotaWritePolicyError("state utilization_ratio must be finite")
    try:
        verified = classify_storage(
            QuotaFacts(
                capacity_bytes=state.capacity_bytes,
                used_bytes=state.used_bytes,
                free_bytes=state.free_bytes,
                utilization_ratio=float(state.utilization_ratio),
                absolute_free_floor_bytes=state.absolute_free_floor_bytes,
            ),
            config=config,
            observed_at=state.observed_at,
        )
    except QuotaFactsError as exc:
        raise QuotaWritePolicyError(f"untrusted quota state: {exc}") from exc
    if verified.pressure_state is not state.pressure_state:
        raise QuotaWritePolicyError(
            "state pressure_state contradicts byte-derived pressure under the applicable quota config"
        )
    return verified


def decide_storage_write(
    state: StorageQuotaState,
    *,
    projected_write_bytes: int,
    priority: StoragePriority,
    config: QuotaConfig | None = None,
) -> QuotaWriteDecision:
    """Return a deterministic write decision without touching storage.

    The incoming snapshot is untrusted. Its byte facts are reconciled and its
    pressure is rederived with the same applicable config before policy runs.
    Equality at the absolute floor is safe; P0 is the only priority with
    critical-pressure continuation, and no priority bypasses the hard floor.
    """
    if isinstance(projected_write_bytes, bool) or not isinstance(projected_write_bytes, int):
        raise QuotaWritePolicyError("projected_write_bytes must be an integer")
    if projected_write_bytes < 0:
        raise QuotaWritePolicyError("projected_write_bytes must be >= 0")
    try:
        priority = StoragePriority(priority)
    except ValueError as exc:
        raise QuotaWritePolicyError(f"unknown storage priority: {priority!r}") from exc
    policy = config or load_quota_config()
    verified_state = _verified_storage_state(state, policy)
    floor = verified_state.absolute_free_floor_bytes or 0
    projected_free = verified_state.free_bytes - projected_write_bytes
    is_essential = priority is StoragePriority.P0
    if projected_free < floor:
        return QuotaWriteDecision(
            WriteDisposition.BLOCK,
            "projected write would cross the absolute free-space floor",
            projected_free,
            floor,
            verified_state.pressure_state,
            priority,
            blocked_code=STORAGE_CAPACITY_BLOCKED,
        )
    if verified_state.pressure_state is DiskPressure.CRITICAL and not is_essential:
        return QuotaWriteDecision(
            WriteDisposition.BLOCK,
            "critical pressure pauses every non-essential write before exhaustion",
            projected_free,
            floor,
            verified_state.pressure_state,
            priority,
            blocked_code=STORAGE_CAPACITY_BLOCKED,
        )
    if verified_state.pressure_state is DiskPressure.CONSTRAINED:
        if priority is StoragePriority.P2:
            return QuotaWriteDecision(
                WriteDisposition.DEFER,
                "constrained pressure defers optional high-volume P2 writes before P0",
                projected_free,
                floor,
                verified_state.pressure_state,
                priority,
            )
        if priority is StoragePriority.P3:
            return QuotaWriteDecision(
                WriteDisposition.PAUSE,
                "constrained pressure pauses rebuildable P3 work first",
                projected_free,
                floor,
                verified_state.pressure_state,
                priority,
            )
    if verified_state.pressure_state is DiskPressure.WATCH:
        return QuotaWriteDecision(
            WriteDisposition.WARN,
            "watch pressure permits a safe write with projected-growth warning",
            projected_free,
            floor,
            verified_state.pressure_state,
            priority,
            warning=True,
        )
    if verified_state.pressure_state is DiskPressure.CRITICAL:
        return QuotaWriteDecision(
            WriteDisposition.WARN,
            "critical P0 evidence may proceed only while the absolute floor remains intact",
            projected_free,
            floor,
            verified_state.pressure_state,
            priority,
            warning=True,
        )
    return QuotaWriteDecision(
        WriteDisposition.PROCEED,
        "normal pressure and absolute floor permit the write",
        projected_free,
        floor,
        state.pressure_state,
        priority,
    )


__all__ = [
    "DEFAULT_QUOTA_CONFIG_PATH",
    "QuotaConfig",
    "QuotaConfigurationError",
    "QuotaError",
    "QuotaFacts",
    "QuotaFactsError",
    "QuotaWriteDecision",
    "QuotaWritePolicyError",
    "STORAGE_CAPACITY_BLOCKED",
    "WriteDisposition",
    "classify_storage",
    "decide_storage_write",
    "load_quota_config",
]
