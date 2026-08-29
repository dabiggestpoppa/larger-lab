"""Bloc 1 registries: providers, sensor priority, equivalence, methodology."""

from __future__ import annotations

from .provider_registry import (
    CAPABILITY_KEYS,
    PROVIDER_IDS,
    ProviderCapability,
    ProviderEntry,
    ProviderRegistry,
    eligible_required_providers,
    is_required_runtime_allowed,
    load_provider_registry,
    validate_required_runtime,
)
from .sensor_priority import (
    CRITICAL_SENSOR_STATES,
    PriorityEntry,
    SensorPriorityRegistry,
    critical_states_with_redundancy_intent,
    load_sensor_priority,
)

__all__ = [
    "CAPABILITY_KEYS",
    "CRITICAL_SENSOR_STATES",
    "PROVIDER_IDS",
    "PriorityEntry",
    "ProviderCapability",
    "ProviderEntry",
    "ProviderRegistry",
    "SensorPriorityRegistry",
    "critical_states_with_redundancy_intent",
    "eligible_required_providers",
    "is_required_runtime_allowed",
    "load_provider_registry",
    "load_sensor_priority",
    "validate_required_runtime",
]
