"""Bloc 1 registries: providers, sensor priority, equivalence, methodology."""

from __future__ import annotations

from .methodology_registry import (
    MethodologyEntry,
    MethodologyRegistry,
    load_methodology_registry,
    require_methodology_id,
)
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
from .semantic_equivalence import (
    EquivalenceMapping,
    SemanticEquivalenceRegistry,
    is_poolable,
    load_semantic_equivalence,
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
    "EquivalenceMapping",
    "MethodologyEntry",
    "MethodologyRegistry",
    "PriorityEntry",
    "ProviderCapability",
    "ProviderEntry",
    "ProviderRegistry",
    "SemanticEquivalenceRegistry",
    "SensorPriorityRegistry",
    "critical_states_with_redundancy_intent",
    "eligible_required_providers",
    "is_poolable",
    "is_required_runtime_allowed",
    "load_methodology_registry",
    "load_provider_registry",
    "load_semantic_equivalence",
    "load_sensor_priority",
    "require_methodology_id",
    "validate_required_runtime",
]
