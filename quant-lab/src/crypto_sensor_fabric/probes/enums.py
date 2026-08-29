"""Bloc 2 probe-harness controlled vocabularies.

Frozen from `bloc_02/03_EVIDENCE_SCORING_COVERAGE_AND_FAILURE_TAXONOMY.md` and
`bloc_02/05_PROBE_OUTPUT_TEMPLATES.md`.  Where Bloc 1 already defines the
semantics (SensorFamily, SemanticEquivalence, MissingReason, AccessClass) the
Bloc 1 enums are reused — no duplicated semantics under new names.

Probe-layer missingness (`CapabilityMissingness`) deliberately carries richer
distinctions than the Bloc 1 `MissingReason` vocabulary (PRE_LISTING,
SENSOR_NOT_SUPPORTED, OUTSIDE_PROVIDER_RETENTION, ...).  Mapping into Bloc 1
missingness happens at handoff; distinctions without a faithful Bloc 1 member
are preserved at the probe layer and flagged `BLOC5_SCHEMA_REFINEMENT_PENDING`
(operator forward-compatibility note) rather than forcing Bloc 1 schema
expansion during Bloc 2.
"""

from __future__ import annotations

from enum import Enum


class _StrEnum(str, Enum):
    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


class CapabilityStatus(_StrEnum):
    """Final verdict for one provider/sensor/scope probe (03 §4)."""

    VERIFIED = "VERIFIED"
    VERIFIED_LIMITED = "VERIFIED_LIMITED"
    VERIFIED_CURRENT_ONLY = "VERIFIED_CURRENT_ONLY"
    VERIFIED_ARCHIVE_ONLY = "VERIFIED_ARCHIVE_ONLY"
    UNSUPPORTED = "UNSUPPORTED"
    ACCESS_BLOCKED = "ACCESS_BLOCKED"
    GEO_BLOCKED = "GEO_BLOCKED"
    AUTH_BLOCKED = "AUTH_BLOCKED"
    PAYMENT_BLOCKED = "PAYMENT_BLOCKED"
    HISTORY_BLOCKED = "HISTORY_BLOCKED"
    SEMANTICALLY_UNUSABLE = "SEMANTICALLY_UNUSABLE"
    TRANSIENT_FAILURE = "TRANSIENT_FAILURE"
    UNVERIFIED = "UNVERIFIED"


class ProbeRunStatus(_StrEnum):
    """Run-level outcome (03 §22).  PARTIAL never implies unattempted=unsupported."""

    COMPLETE = "COMPLETE"
    COMPLETE_WITH_LIMITATIONS = "COMPLETE_WITH_LIMITATIONS"
    PARTIAL = "PARTIAL"
    ABORTED_HARD_BLOCK = "ABORTED_HARD_BLOCK"
    ABORTED_TRANSIENT = "ABORTED_TRANSIENT"


class EvidenceLevel(_StrEnum):
    """Evidence ladder (03 §1 / F2.5).  Never upgrade without observation."""

    E0_CLAIM_ONLY = "E0_CLAIM_ONLY"
    E1_DOC_CONTRACT_VERIFIED = "E1_DOC_CONTRACT_VERIFIED"
    E2_LIVE_RECENT_VERIFIED = "E2_LIVE_RECENT_VERIFIED"
    E3_HISTORICAL_CHECKPOINT_VERIFIED = "E3_HISTORICAL_CHECKPOINT_VERIFIED"
    E4_MULTI_ERA_VERIFIED = "E4_MULTI_ERA_VERIFIED"
    E5_REPRODUCIBLE_COVERAGE_VERIFIED = "E5_REPRODUCIBLE_COVERAGE_VERIFIED"


class PITReadiness(_StrEnum):
    """PIT readiness classification (03 §10 / F2.9)."""

    PIT_READY = "PIT_READY"
    PIT_READY_WITH_METHOD_VERSION = "PIT_READY_WITH_METHOD_VERSION"
    PIT_LIMITED = "PIT_LIMITED"
    NOT_PIT_READY = "NOT_PIT_READY"


class ProviderRole(_StrEnum):
    """Sensor-specific source role (03 §16 / F2.3)."""

    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    FALLBACK = "FALLBACK"
    CORROBORATOR = "CORROBORATOR"
    MECHANISM_MICROSCOPE = "MECHANISM_MICROSCOPE"
    CURRENT_ONLY = "CURRENT_ONLY"
    ARCHIVE_ONLY = "ARCHIVE_ONLY"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    EXCLUDED = "EXCLUDED"


class RedundancyClass(_StrEnum):
    """Independence-aware redundancy (03 §17 / F2.17).

    Aliases of one upstream venue never count as multiple independent sources.
    """

    R0_NONE = "R0_NONE"
    R1_SINGLE_INDEPENDENT = "R1_SINGLE_INDEPENDENT"
    R2_TWO_INDEPENDENT = "R2_TWO_INDEPENDENT"
    R3_THREE_PLUS_INDEPENDENT = "R3_THREE_PLUS_INDEPENDENT"
    RX_DEPENDENCY_AMBIGUOUS = "RX_DEPENDENCY_AMBIGUOUS"


class AccessMode(_StrEnum):
    """How the probe reaches the source (01 §5.7)."""

    PUBLIC_REST = "PUBLIC_REST"
    PUBLIC_WEBSOCKET = "PUBLIC_WEBSOCKET"
    PUBLIC_ARCHIVE = "PUBLIC_ARCHIVE"
    FREE_API_KEY = "FREE_API_KEY"
    COMMUNITY_ARCHIVE = "COMMUNITY_ARCHIVE"


class QueryMode(_StrEnum):
    """Navigation shape of the source (01 §5.8)."""

    TIME_RANGE = "TIME_RANGE"
    CURSOR = "CURSOR"
    SEQUENCE = "SEQUENCE"
    PAGE = "PAGE"
    DOWNLOAD_FILE = "DOWNLOAD_FILE"
    LATEST_ONLY = "LATEST_ONLY"


class HistoricalBoundaryConfidence(_StrEnum):
    """Earliest-history confidence (03 §12)."""

    EXACT_ARCHIVE_BOUNDARY = "EXACT_ARCHIVE_BOUNDARY"
    MONTH_BOUNDARY_VERIFIED = "MONTH_BOUNDARY_VERIFIED"
    ERA_BOUNDARY_VERIFIED = "ERA_BOUNDARY_VERIFIED"
    APPROXIMATE = "APPROXIMATE"
    UNKNOWN = "UNKNOWN"


class Granularity(_StrEnum):
    """Canonical probe granularity set (01 §5.6)."""

    G1M = "1m"
    G5M = "5m"
    G15M = "15m"
    G1H = "1h"
    G4H = "4h"
    G1D = "1d"
    RAW_EVENT = "RAW_EVENT"
    BOOK_SNAPSHOT = "BOOK_SNAPSHOT"


class ResponseStatusClass(_StrEnum):
    """Coarse outcome of one attempt (05 §1)."""

    VERIFIED_SAMPLE = "VERIFIED_SAMPLE"
    EMPTY_VALID = "EMPTY_VALID"
    FAILED = "FAILED"
    NOT_ATTEMPTED = "NOT_ATTEMPTED"


class ProbeFailureFamily(_StrEnum):
    """Failure taxonomy families (freeze manifest §7)."""

    ACCESS = "ACCESS"
    NETWORK_SERVER = "NETWORK_SERVER"
    ENDPOINT_ARCHIVE = "ENDPOINT_ARCHIVE"
    SYMBOL_LISTING = "SYMBOL_LISTING"
    HISTORY = "HISTORY"
    PAGINATION = "PAGINATION"
    SCHEMA = "SCHEMA"
    SEMANTIC = "SEMANTIC"
    QUALITY_CORRUPTION = "QUALITY_CORRUPTION"
    DOC_RUNTIME_CONTRADICTION = "DOC_RUNTIME_CONTRADICTION"
    UNSUPPORTED = "UNSUPPORTED"


class ProbeFailureClass(_StrEnum):
    """Machine-readable failure codes (03 §5)."""

    F_ACCESS_GEO = "F_ACCESS_GEO"
    F_ACCESS_AUTH = "F_ACCESS_AUTH"
    F_ACCESS_PAYMENT = "F_ACCESS_PAYMENT"
    F_ACCESS_RATE_LIMIT = "F_ACCESS_RATE_LIMIT"
    F_NETWORK_TIMEOUT = "F_NETWORK_TIMEOUT"
    F_NETWORK_DNS = "F_NETWORK_DNS"
    F_NETWORK_TLS = "F_NETWORK_TLS"
    F_SERVER_5XX = "F_SERVER_5XX"
    F_CLIENT_4XX = "F_CLIENT_4XX"
    F_ENDPOINT_REMOVED = "F_ENDPOINT_REMOVED"
    F_ARCHIVE_NOT_FOUND = "F_ARCHIVE_NOT_FOUND"
    F_SYMBOL_NOT_FOUND = "F_SYMBOL_NOT_FOUND"
    F_PRE_LISTING = "F_PRE_LISTING"
    F_HISTORY_TRUNCATED = "F_HISTORY_TRUNCATED"
    F_EMPTY_VALID_WINDOW = "F_EMPTY_VALID_WINDOW"
    F_PAGINATION_LOOP = "F_PAGINATION_LOOP"
    F_PAGINATION_TRUNCATED = "F_PAGINATION_TRUNCATED"
    F_SCHEMA_CHANGED = "F_SCHEMA_CHANGED"
    F_TIMESTAMP_UNCLEAR = "F_TIMESTAMP_UNCLEAR"
    F_UNIT_UNCLEAR = "F_UNIT_UNCLEAR"
    F_METHOD_UNCLEAR = "F_METHOD_UNCLEAR"
    F_DUPLICATE_EXCESS = "F_DUPLICATE_EXCESS"
    F_GAP_EXCESS = "F_GAP_EXCESS"
    F_CHECKSUM_FAILURE = "F_CHECKSUM_FAILURE"
    F_PAYLOAD_CORRUPT = "F_PAYLOAD_CORRUPT"
    F_QUOTA_EXHAUSTED = "F_QUOTA_EXHAUSTED"
    F_DOC_RUNTIME_CONTRADICTION = "F_DOC_RUNTIME_CONTRADICTION"
    F_UNSUPPORTED_SENSOR = "F_UNSUPPORTED_SENSOR"
    F_UNKNOWN = "F_UNKNOWN"


class CapabilityMissingness(_StrEnum):
    """Probe-layer missingness (03 §6).

    Richer than Bloc 1 MissingReason by design; mapped at handoff, with
    unrepresentable distinctions preserved and flagged for Bloc 5 refinement.
    """

    PRE_LISTING = "PRE_LISTING"
    UNSUPPORTED_INSTRUMENT = "UNSUPPORTED_INSTRUMENT"
    UNKNOWN_SYMBOL = "UNKNOWN_SYMBOL"
    OUTSIDE_PROVIDER_RETENTION = "OUTSIDE_PROVIDER_RETENTION"
    SENSOR_NOT_SUPPORTED = "SENSOR_NOT_SUPPORTED"
    PROVIDER_SCHEMA_BREAK = "PROVIDER_SCHEMA_BREAK"
    ENDPOINT_UNAVAILABLE = "ENDPOINT_UNAVAILABLE"
    RATE_LIMITED = "RATE_LIMITED"
    AUTH_BLOCKED = "AUTH_BLOCKED"
    GEO_BLOCKED = "GEO_BLOCKED"
    PAYMENT_BLOCKED = "PAYMENT_BLOCKED"
    PROVIDER_GAP = "PROVIDER_GAP"
    DATA_BLOCKED = "DATA_BLOCKED"


class ContradictionSeverity(_StrEnum):
    """Documentation/runtime contradiction severity (03 §15)."""

    INFO = "INFO"
    MATERIAL = "MATERIAL"
    BLOCKING = "BLOCKING"


class ContradictionResolutionStatus(_StrEnum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    SUPERSEDED = "SUPERSEDED"


class AuthMode(_StrEnum):
    """Authentication classification (01 §24)."""

    NO_AUTH = "NO_AUTH"
    FREE_API_KEY = "FREE_API_KEY"
    ACCOUNT_REQUIRED_NO_PAYMENT = "ACCOUNT_REQUIRED_NO_PAYMENT"
    PAYMENT_METHOD_REQUIRED = "PAYMENT_METHOD_REQUIRED"
    PAID_SUBSCRIPTION_REQUIRED = "PAID_SUBSCRIPTION_REQUIRED"
    UNVERIFIED = "UNVERIFIED"


class FreeOnlyStatus(_StrEnum):
    """Free-only status attached to a capability claim."""

    FREE_COMPLIANT = "FREE_COMPLIANT"
    FREE_LIMITED = "FREE_LIMITED"
    UNVERIFIED = "UNVERIFIED"
    PAID_BLOCKED = "PAID_BLOCKED"
