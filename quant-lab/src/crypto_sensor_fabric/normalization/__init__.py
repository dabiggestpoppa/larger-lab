"""SENSOR-B5-I01 — Bloc 5 normalization base layer: vocabulary + T1 envelope.

This package is the foundational type layer of Bloc 5.  It defines:

* the frozen normalization vocabularies (status, typed missingness, quality
  flags and dimension states, lineage state, reasoned quarantine, payoff type,
  interval convention, availability basis, timestamp precision);
* the base T1 observation envelope and its parts (time coordinates, native
  quantity, quality dimensions, lineage refs, version refs);
* two read-only frozen correspondences (blocked status -> missingness cause,
  blocking quality flags) and one deterministic serialization helper.

It deliberately implements **no** behavior: no identity/lifecycle/alias
registry or resolver, no contract terms, no linear/inverse conversion, no unit
or stablecoin conversion, no timestamp or availability derivation, no revision
engine, no methodology registry, no sensor normalizer, no T1 writer, manifest,
generation, storage or canonical query, no provider fixture and no network
access.  Each of those belongs to a later frozen checkpoint; the split is
recorded row by row in
``research/crypto_foundry/sensor_fabric/evidence/bloc_05/BLOC_05_I01_TYPE_SCOPE_MATRIX.json``.

Only the symbols below are public contract.  Everything else in ``enums`` and
``models`` (helpers, private bases, intermediate validators) is an
implementation detail and is deliberately absent from ``__all__``.

The frozen full name ``T1ObservationEnvelope`` is intentionally NOT exported:
the frozen envelope also carries identity, methodology and replay-eligibility
fields owned by later checkpoints, and exporting the full name now would let a
consumer mistake this base layer for the finished contract.
"""

from __future__ import annotations

from .enums import (
    BLOCKED_STATUS_MISSINGNESS_REASON,
    BLOCKING_QUALITY_FLAGS,
    AvailabilityBasis,
    IntervalTimeConvention,
    LineageState,
    MissingnessReason,
    NormalizationQualityFlag,
    NormalizationStatus,
    PayoffType,
    QuarantineReason,
    QualityDimensionState,
    TimestampPrecision,
)
from .models import (
    ContractInstanceId,
    NativeQuantity,
    ObservationTimeEnvelope,
    OpaqueIdentifier,
    RegistryVersion,
    T1BaseEnvelope,
    T1GenerationId,
    T1LineageRef,
    T1Quality,
    T1RecordId,
    T1VersionContext,
    canonical_json_bytes,
)

__all__ = [
    # frozen vocabularies
    "AvailabilityBasis",
    "IntervalTimeConvention",
    "LineageState",
    "MissingnessReason",
    "NormalizationQualityFlag",
    "NormalizationStatus",
    "PayoffType",
    "QuarantineReason",
    "QualityDimensionState",
    "TimestampPrecision",
    # frozen correspondences (read-only data, not behavior)
    "BLOCKED_STATUS_MISSINGNESS_REASON",
    "BLOCKING_QUALITY_FLAGS",
    # validated opaque identifier types (no algorithms, no registries)
    "ContractInstanceId",
    "OpaqueIdentifier",
    "RegistryVersion",
    "T1GenerationId",
    "T1RecordId",
    # base models
    "NativeQuantity",
    "ObservationTimeEnvelope",
    "T1BaseEnvelope",
    "T1LineageRef",
    "T1Quality",
    "T1VersionContext",
    # serialization
    "canonical_json_bytes",
]