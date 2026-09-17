"""Crypto Mechanical Sensor Fabric — provider-independent canonical contracts.

Layer map:

    T0  raw provider evidence          (Bloc 4)
    T1  canonical PIT observations     (this package: schemas)
    T2  derived mechanical observables (Bloc 9)

This package currently implements the Bloc 1 contract freeze:

    contracts/   enums, base observation, access, quality, identity, missingness
    schemas/     canonical observation models + provider envelope
    registry/    provider / sensor-priority / equivalence / methodology registries

Doctrine (frozen, non-negotiable):

    - no single exchange is canonical truth; the sensor is canonical
    - provider identity is never erased by fallback
    - missingness is information; no zero-fill, no forward-fill
    - cross-venue synthesis begins only at T2
    - native provider values survive normalization
    - required automated sources must pass the free-only gate (F9)
    - research consumes canonical interfaces, never provider-native columns
"""

from __future__ import annotations

__version__ = "0.1.0"
__schema_version__ = "1.0.0"

from .contracts.enums import (
    AccessClass,
    AggregationType,
    AggressorSide,
    BookMetricName,
    BookSide,
    ContractType,
    EvidenceClass,
    FundingType,
    LiquidationEventShape,
    LiquidationRole,
    LiquidationSide,
    MarketType,
    MissingReason,
    NativeOIUnit,
    PositioningMetric,
    ProviderStatus,
    QualityFlag,
    QualityState,
    ReferenceType,
    RetrievalMode,
    SemanticEquivalence,
    SensorFamily,
    VenueID,
)

__all__ = [
    "AccessClass",
    "AggregationType",
    "AggressorSide",
    "BookMetricName",
    "BookSide",
    "ContractType",
    "EvidenceClass",
    "FundingType",
    "LiquidationEventShape",
    "LiquidationRole",
    "LiquidationSide",
    "MarketType",
    "MissingReason",
    "NativeOIUnit",
    "PositioningMetric",
    "ProviderStatus",
    "QualityFlag",
    "QualityState",
    "ReferenceType",
    "RetrievalMode",
    "SemanticEquivalence",
    "SensorFamily",
    "VenueID",
]
