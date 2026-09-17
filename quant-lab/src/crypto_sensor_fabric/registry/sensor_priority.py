"""Sensor priority registry (02 §14).

Config: `config/crypto_sensor_fabric/sensor_priority.yaml`.

Priority means preferred evidence ordering, NOT fallback substitution without
venue identity.  The registry is the single source of ordering truth: provider
order is never hard-coded in application logic (B1-T33).
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

from .._paths import CONFIG_DIR

DEFAULT_SENSOR_PRIORITY_PATH = CONFIG_DIR / "sensor_priority.yaml"

#: Critical sensor states in the frozen registry (map to T2 state families).
CRITICAL_SENSOR_STATES: tuple[str, ...] = (
    "LIQUIDATION_STATE",
    "OPEN_INTEREST_STATE",
    "FUNDING_STATE",
    "ORDER_FLOW_STATE",
    "LIQUIDITY_STATE",
)


class PriorityEntry(BaseModel):
    """Preferred evidence ordering for one critical sensor state."""

    model_config = ConfigDict(extra="forbid")

    min_preferred_sources: int = 2
    source_priority: list[str] = Field(min_length=1)


class SensorPriorityRegistry(BaseModel):
    """Full sensor priority registry."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"
    critical: dict[str, PriorityEntry]


def load_sensor_priority(path: Path | None = None) -> SensorPriorityRegistry:
    """Load and validate the sensor priority registry from YAML."""
    config_path = path or DEFAULT_SENSOR_PRIORITY_PATH
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    return SensorPriorityRegistry.model_validate(data)


def critical_states_with_redundancy_intent(
    registry: SensorPriorityRegistry,
) -> dict[str, PriorityEntry]:
    """Critical states whose planning redundancy intent is satisfied.

    A critical state satisfies the planning invariant (B1-T32) when it lists at
    least two preferred sources.  This is a planning invariant, not proof the
    sources will pass Bloc 2.
    """
    return {
        name: entry
        for name, entry in registry.critical.items()
        if entry.min_preferred_sources >= 2 and len(entry.source_priority) >= 2
    }
