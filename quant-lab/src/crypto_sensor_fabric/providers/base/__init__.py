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
from .capabilities import (
    DEFAULT_PROMOTION_FILE,
    capabilities_from_promotion,
    load_promotion_candidates,
    promotion_bound_violations,
    promotion_provider_ids,
)
from .conformance import (
    AdapterUnderTest,
    ConformanceResult,
    run_conformance_suite,
    summarize_conformance,
)
from .enums import (
    ALLOWED_AUTH_MODES,
    HARD_BLOCK_AUTH_MODES,
    AdapterAuthMode,
    AdapterConformanceMode,
    AdapterStatus,
    DuplicateAnnotation,
    FetchPurpose,
    FreeOnlyStatus,
    Granularity,
    HistoryScope,
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
from .native import (
    ProviderNativeCapabilityEvidence,
    apply_native_evidence,
    native_evidence_violations,
)
from .pagination import (
    CursorTracker,
    completion_from_provider_semantics,
    resume_token_round_trip,
)
from .protocol import (
    SENSOR_FETCH_METHOD,
    MechanicalProviderAdapter,
    dispatch_fetch,
    ensure_supported,
)
from .rate_limit import rate_limit_from_headers, unknown_rate_limit
from .retry import RetryPolicy, classify_retryability, is_retryable
from .schema import (
    SchemaAssessment,
    assert_no_zero_coercion,
    assess_schema,
    parse_fail_closed,
)

__all__ = [
    "ALLOWED_AUTH_MODES",
    "AccessClassViolation",
    "AccessDecision",
    "AdapterConformanceMode",
    "AdapterUnderTest",
    "ConformanceResult",
    "CursorTracker",
    "DEFAULT_PROMOTION_FILE",
    "RetryPolicy",
    "SchemaAssessment",
    "assert_free_only_access",
    "assert_no_zero_coercion",
    "assess_schema",
    "classify_retryability",
    "capabilities_from_promotion",
    "completion_from_provider_semantics",
    "evaluate_access",
    "fingerprint_request",
    "load_promotion_candidates",
    "is_retryable",
    "parse_fail_closed",
    "payload_hash",
    "promotion_bound_violations",
    "promotion_provider_ids",
    "rate_limit_from_headers",
    "resume_token_round_trip",
    "run_conformance_suite",
    "summarize_conformance",
    "unknown_rate_limit",
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
    "HistoryScope",
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
    "ProviderNativeCapabilityEvidence",
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
    "SENSOR_FETCH_METHOD",
    "apply_native_evidence",
    "dispatch_fetch",
    "ensure_supported",
    "error_from_failure_type",
    "native_evidence_violations",
]
