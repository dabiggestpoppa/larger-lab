"""Bloc 3 common provider adapter foundation (SENSOR-B3-I01).

Subsystem layout (frozen plan `bloc_03/01` §20):

    enums.py        base controlled vocabularies (reusing Bloc 1/2 where they exist)
    models.py       FetchRequest / FetchBatch / RawPayloadEnvelope / ResumeToken / ...
    errors.py       typed acquisition error taxonomy
    protocol.py     MechanicalProviderAdapter common protocol
    access.py       free-only access gate (I02)
    fingerprint.py  deterministic request fingerprint + payload hash (I02)
    retry.py        typed retry/backoff model (I03)
    rate_limit.py   normalized rate-limit telemetry (I03)
    pagination.py   resume/cursor-loop protection (I03)
    conformance.py  common provider conformance suite (I04)

This package is the ACQUISITION BOUNDARY: it preserves raw provider evidence
and provider identity, and it never performs canonical normalization,
cross-venue synthesis or research computation.
"""

from __future__ import annotations

from .access import AccessDecision, assert_free_only_access, evaluate_access
from .enums import (
    ALLOWED_AUTH_MODES,
    HARD_BLOCK_AUTH_MODES,
    AdapterAuthMode,
    AdapterStatus,
    DuplicateAnnotation,
    FetchPurpose,
    FreeOnlyStatus,
    Granularity,
    HistoricalMode,
    LiveMode,
    PaginationMode,
    QualityFlagAcquisition,
    Retryability,
    SchemaState,
)
from .errors import (
    AccessClassViolation,
    AcquisitionError,
    ArchiveIntegrityFailure,
    AuthenticationRequired,
    CapabilityUnavailable,
    GeoRestricted,
    HistoricalRangeUnavailable,
    InvalidInstrument,
    PaginationFailure,
    ProviderSemanticError,
    ProviderUnavailable,
    RateLimited,
    RetryExhausted,
    SchemaDrift,
    TransportFailure,
    UnsupportedGranularity,
    error_from_failure_type,
)
from .fingerprint import fingerprint_request, payload_hash
from .models import (
    AcquisitionFailure,
    AdapterEvidenceRef,
    FetchBatch,
    FetchRequest,
    InstrumentListRequest,
    InstrumentListResult,
    ProviderCapabilities,
    ProviderHealthSignal,
    RateLimitSnapshot,
    RawPayloadEnvelope,
    ResumeToken,
    SensorCapability,
)
from .protocol import MechanicalProviderAdapter, ensure_supported

__all__ = [
    "ALLOWED_AUTH_MODES",
    "AccessClassViolation",
    "AccessDecision",
    "assert_free_only_access",
    "evaluate_access",
    "fingerprint_request",
    "payload_hash",
    "AcquisitionError",
    "AcquisitionFailure",
    "AdapterAuthMode",
    "AdapterEvidenceRef",
    "AdapterStatus",
    "ArchiveIntegrityFailure",
    "AuthenticationRequired",
    "CapabilityUnavailable",
    "DuplicateAnnotation",
    "FetchBatch",
    "FetchPurpose",
    "FetchRequest",
    "FreeOnlyStatus",
    "GeoRestricted",
    "Granularity",
    "HARD_BLOCK_AUTH_MODES",
    "HistoricalMode",
    "HistoricalRangeUnavailable",
    "InstrumentListRequest",
    "InstrumentListResult",
    "InvalidInstrument",
    "LiveMode",
    "MechanicalProviderAdapter",
    "PaginationFailure",
    "PaginationMode",
    "ProviderCapabilities",
    "ProviderHealthSignal",
    "ProviderSemanticError",
    "ProviderUnavailable",
    "QualityFlagAcquisition",
    "RateLimited",
    "RateLimitSnapshot",
    "RawPayloadEnvelope",
    "ResumeToken",
    "RetryExhausted",
    "Retryability",
    "SchemaDrift",
    "SchemaState",
    "SensorCapability",
    "TransportFailure",
    "UnsupportedGranularity",
    "ensure_supported",
    "error_from_failure_type",
]
