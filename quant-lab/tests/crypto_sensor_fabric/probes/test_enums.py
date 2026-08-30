"""Freeze the Bloc 2 probe vocabulary sets (04 §4)."""

from __future__ import annotations

from crypto_sensor_fabric.probes.enums import (
    AccessMode,
    AuthMode,
    CapabilityMissingness,
    CapabilityStatus,
    ContradictionResolutionStatus,
    ContradictionSeverity,
    EvidenceLevel,
    EvidenceSourceClass,
    FreeOnlyStatus,
    Granularity,
    HistoricalBoundaryConfidence,
    PITReadiness,
    ProbeFailureClass,
    ProbeFailureFamily,
    ProbeRunStatus,
    ProviderRole,
    QueryMode,
    RedundancyClass,
    ResponseStatusClass,
)

EXPECTED_MEMBERS: dict[str, set[str]] = {
    "CapabilityStatus": {
        "VERIFIED",
        "VERIFIED_LIMITED",
        "VERIFIED_CURRENT_ONLY",
        "VERIFIED_ARCHIVE_ONLY",
        "UNSUPPORTED",
        "ACCESS_BLOCKED",
        "GEO_BLOCKED",
        "AUTH_BLOCKED",
        "PAYMENT_BLOCKED",
        "HISTORY_BLOCKED",
        "SEMANTICALLY_UNUSABLE",
        "TRANSIENT_FAILURE",
        "CREDENTIAL_NOT_CONFIGURED",  # I12R1: local run prerequisite, not a provider failure
        "UNVERIFIED",
    },
    "ProbeRunStatus": {
        "COMPLETE",
        "COMPLETE_WITH_LIMITATIONS",
        "PARTIAL",
        "ABORTED_HARD_BLOCK",
        "ABORTED_TRANSIENT",
    },
    "EvidenceLevel": {
        "E0_CLAIM_ONLY",
        "E1_DOC_CONTRACT_VERIFIED",
        "E2_LIVE_RECENT_VERIFIED",
        "E3_HISTORICAL_CHECKPOINT_VERIFIED",
        "E4_MULTI_ERA_VERIFIED",
        "E5_REPRODUCIBLE_COVERAGE_VERIFIED",
    },
    "EvidenceSourceClass": {
        "FIRST_PARTY_RUNTIME",
        "FIRST_PARTY_ARCHIVE",
        "FIRST_PARTY_DOCUMENTATION",
        "THIRD_PARTY_AGGREGATOR",
        "COMMUNITY_RECONSTRUCTION",
        "COMMUNITY_ARCHIVE",
    },
    "PITReadiness": {
        "PIT_READY",
        "PIT_READY_WITH_METHOD_VERSION",
        "PIT_LIMITED",
        "NOT_PIT_READY",
    },
    "ProviderRole": {
        "PRIMARY",
        "SECONDARY",
        "FALLBACK",
        "CORROBORATOR",
        "MECHANISM_MICROSCOPE",
        "CURRENT_ONLY",
        "ARCHIVE_ONLY",
        "REFERENCE_ONLY",
        "EXCLUDED",
    },
    "RedundancyClass": {
        "R0_NONE",
        "R1_SINGLE_INDEPENDENT",
        "R2_TWO_INDEPENDENT",
        "R3_THREE_PLUS_INDEPENDENT",
        "RX_DEPENDENCY_AMBIGUOUS",
    },
    "AccessMode": {
        "PUBLIC_REST",
        "PUBLIC_WEBSOCKET",
        "PUBLIC_ARCHIVE",
        "FREE_API_KEY",
        "COMMUNITY_ARCHIVE",
    },
    "QueryMode": {
        "TIME_RANGE",
        "CURSOR",
        "SEQUENCE",
        "PAGE",
        "DOWNLOAD_FILE",
        "LATEST_ONLY",
    },
    "HistoricalBoundaryConfidence": {
        "EXACT_ARCHIVE_BOUNDARY",
        "MONTH_BOUNDARY_VERIFIED",
        "ERA_BOUNDARY_VERIFIED",
        "APPROXIMATE",
        "UNKNOWN",
    },
    "Granularity": {"1m", "5m", "15m", "1h", "4h", "1d", "RAW_EVENT", "BOOK_SNAPSHOT"},
    "ResponseStatusClass": {"VERIFIED_SAMPLE", "EMPTY_VALID", "FAILED", "NOT_ATTEMPTED"},
    "ProbeFailureClass": {
        "F_ACCESS_GEO",
        "F_ACCESS_AUTH",
        "F_ACCESS_PAYMENT",
        "F_ACCESS_RATE_LIMIT",
        "F_NETWORK_TIMEOUT",
        "F_NETWORK_DNS",
        "F_NETWORK_TLS",
        "F_SERVER_5XX",
        "F_CLIENT_4XX",
        "F_ENDPOINT_REMOVED",
        "F_ARCHIVE_NOT_FOUND",
        "F_REQUIRED_ARTIFACT_MISSING",
        "F_SYMBOL_NOT_FOUND",
        "F_PRE_LISTING",
        "F_HISTORY_TRUNCATED",
        "F_EMPTY_VALID_WINDOW",
        "F_PAGINATION_LOOP",
        "F_PAGINATION_TRUNCATED",
        "F_SCHEMA_CHANGED",
        "F_TIMESTAMP_UNCLEAR",
        "F_UNIT_UNCLEAR",
        "F_METHOD_UNCLEAR",
        "F_DUPLICATE_EXCESS",
        "F_GAP_EXCESS",
        "F_CHECKSUM_FAILURE",
        "F_PAYLOAD_CORRUPT",
        "F_QUOTA_EXHAUSTED",
        "F_DOC_RUNTIME_CONTRADICTION",
        "F_UNSUPPORTED_SENSOR",
        "F_UNKNOWN",
    },
    "ProbeFailureFamily": {
        "ACCESS",
        "NETWORK_SERVER",
        "ENDPOINT_ARCHIVE",
        "SYMBOL_LISTING",
        "HISTORY",
        "PAGINATION",
        "SCHEMA",
        "SEMANTIC",
        "QUALITY_CORRUPTION",
        "DOC_RUNTIME_CONTRADICTION",
        "UNSUPPORTED",
    },
    "CapabilityMissingness": {
        "PRE_LISTING",
        "UNSUPPORTED_INSTRUMENT",
        "UNKNOWN_SYMBOL",
        "OUTSIDE_PROVIDER_RETENTION",
        "SENSOR_NOT_SUPPORTED",
        "PROVIDER_SCHEMA_BREAK",
        "ENDPOINT_UNAVAILABLE",
        "RATE_LIMITED",
        "AUTH_BLOCKED",
        "GEO_BLOCKED",
        "PAYMENT_BLOCKED",
        "PROVIDER_GAP",
        "DATA_BLOCKED",
    },
    "ContradictionSeverity": {"INFO", "MATERIAL", "BLOCKING"},
    "ContradictionResolutionStatus": {"OPEN", "RESOLVED", "SUPERSEDED"},
    "AuthMode": {
        "NO_AUTH",
        "FREE_API_KEY",
        "ACCOUNT_REQUIRED_NO_PAYMENT",
        "PAYMENT_METHOD_REQUIRED",
        "PAID_SUBSCRIPTION_REQUIRED",
        "UNVERIFIED",
    },
    "FreeOnlyStatus": {"FREE_COMPLIANT", "FREE_LIMITED", "UNVERIFIED", "PAID_BLOCKED"},
}

ENUM_CLASSES = [
    CapabilityStatus,
    ProbeRunStatus,
    EvidenceLevel,
    EvidenceSourceClass,
    PITReadiness,
    ProviderRole,
    RedundancyClass,
    AccessMode,
    QueryMode,
    HistoricalBoundaryConfidence,
    Granularity,
    ResponseStatusClass,
    ProbeFailureClass,
    ProbeFailureFamily,
    CapabilityMissingness,
    ContradictionSeverity,
    ContradictionResolutionStatus,
    AuthMode,
    FreeOnlyStatus,
]


def test_probe_enum_member_sets_are_frozen():
    for enum_cls in ENUM_CLASSES:
        expected = EXPECTED_MEMBERS[enum_cls.__name__]
        actual = {member.value for member in enum_cls}
        assert actual == expected, (
            f"{enum_cls.__name__} member set drifted: "
            f"unexpected={sorted(actual - expected)} missing={sorted(expected - actual)}"
        )


def test_probe_enum_values_equal_names():
    # Granularity uses short native values ("1m") deliberately; its canonical
    # names are frozen separately in EXPECTED_MEMBERS.
    for enum_cls in ENUM_CLASSES:
        if enum_cls is Granularity:
            continue
        for member in enum_cls:
            assert member.value == member.name, enum_cls.__name__


def test_credential_not_configured_is_local_prereq_not_auth_blocked():
    # I12R1: a missing free key locally is a run prerequisite, never a provider
    # failure and never AUTH_BLOCKED without a real provider response.
    assert (
        CapabilityStatus.CREDENTIAL_NOT_CONFIGURED
        is not CapabilityStatus.AUTH_BLOCKED
    )
    assert CapabilityStatus.CREDENTIAL_NOT_CONFIGURED.value == (
        "CREDENTIAL_NOT_CONFIGURED"
    )
