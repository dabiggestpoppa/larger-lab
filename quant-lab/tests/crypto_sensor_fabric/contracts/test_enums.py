"""Freeze the Bloc 1 mandatory contract enums (03 §3).

The exact member sets below are the Bloc 1 vocabulary contract.  Any member
set drift fails this suite so it is visible in Git instead of silent.
"""

from __future__ import annotations

from crypto_sensor_fabric.contracts.enums import (
    AccessClass,
    AggressorSide,
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
    QualityFlag,
    QualityState,
    RetrievalMode,
    SemanticEquivalence,
    SensorFamily,
)

EXPECTED_MEMBERS: dict[str, set[str]] = {
    "SensorFamily": {
        "MECHANICAL_TRADE",
        "MECHANICAL_LIQUIDATION",
        "MECHANICAL_OPEN_INTEREST",
        "MECHANICAL_FUNDING",
        "MECHANICAL_BOOK_SNAPSHOT",
        "MECHANICAL_BOOK_METRIC",
        "MECHANICAL_POSITIONING",
        "MECHANICAL_BASIS",
    },
    "AccessClass": {
        "FREE_AUTOMATED",
        "FREE_LIMITED_AUTOMATED",
        "FREE_REFERENCE_ONLY",
        "PAID_EXCLUDED",
        "UNVERIFIED",
    },
    "EvidenceClass": {
        "FIRST_PARTY_EXCHANGE",
        "FIRST_PARTY_AGGREGATOR",
        "THIRD_PARTY_AGGREGATOR",
        "COMMUNITY_ARCHIVE",
        "RECONSTRUCTED_INTERNAL",
    },
    "RetrievalMode": {"REST", "WS", "BULK_FILE", "COMMUNITY_ARCHIVE"},
    "SemanticEquivalence": {
        "EXACT_EQUIVALENT",
        "NORMALIZABLE_COMPARABLE",
        "CORROBORATION_ONLY",
        "NOT_COMPARABLE",
    },
    "MarketType": {"SPOT", "FUTURE", "PERPETUAL", "OPTION", "OTHER"},
    "ContractType": {"LINEAR", "INVERSE", "QUANTO", "OTHER"},
    "AggressorSide": {"BUY", "SELL", "UNKNOWN"},
    "LiquidationSide": {"LONG", "SHORT", "BOTH", "UNKNOWN"},
    "LiquidationRole": {"MAKER", "TAKER", "BOTH", "UNKNOWN"},
    "LiquidationEventShape": {
        "TRADE_LEVEL",
        "INTERVAL_AGGREGATE",
        "TOTAL_AGGREGATE",
    },
    "NativeOIUnit": {"CONTRACTS", "BASE_ASSET", "QUOTE_ASSET", "USD", "OTHER"},
    "FundingType": {"REALIZED", "PREDICTED", "UNKNOWN"},
    "PositioningMetric": {
        "GLOBAL_LONG_SHORT_RATIO",
        "TOP_TRADER_ACCOUNT_RATIO",
        "TOP_TRADER_POSITION_RATIO",
        "TAKER_LONG_SHORT_RATIO",
        "USER_LONG_SHORT_RATIO",
    },
    "QualityFlag": {
        "SOURCE_NATIVE",
        "SOURCE_AGGREGATED",
        "SOURCE_COMMUNITY",
        "RECONSTRUCTED_INTERNAL",
        "TIMESTAMP_ASSUMED",
        "TIMESTAMP_COARSE",
        "UNIT_NATIVE_ONLY",
        "UNIT_NORMALIZED",
        "UNIT_NORMALIZATION_UNAVAILABLE",
        "VENUE_NOT_DECOMPOSABLE",
        "INSTRUMENT_ID_UNRESOLVED",
        "WINDOW_SEMANTICS_UNCERTAIN",
        "PARTIAL_INTERVAL",
        "DUPLICATE_SOURCE_RECORD",
        "SOURCE_GAP",
        "STALE_SOURCE",
        "PROVIDER_DEGRADED",
        "CROSS_PROVIDER_DISAGREEMENT",
        "HISTORICAL_DEPTH_UNVERIFIED",
        "ACCESS_CLASS_UNVERIFIED",
        "PIT_RISK",
    },
    "QualityState": {"GOOD", "DEGRADED", "STALE", "PARTIAL", "UNVERIFIED", "BLOCKED"},
    "MissingReason": {
        "NOT_SUPPORTED",
        "NOT_LISTED",
        "OUTSIDE_PROVIDER_HISTORY",
        "ENDPOINT_UNAVAILABLE",
        "RATE_LIMITED",
        "AUTH_BLOCKED",
        "GEO_BLOCKED",
        "PROVIDER_GAP",
        "PARSE_FAILED",
        "SEMANTIC_UNRESOLVED",
        "DATA_BLOCKED",
    },
}

ENUM_CLASSES = [
    SensorFamily,
    AccessClass,
    EvidenceClass,
    RetrievalMode,
    SemanticEquivalence,
    MarketType,
    ContractType,
    AggressorSide,
    LiquidationSide,
    LiquidationRole,
    LiquidationEventShape,
    NativeOIUnit,
    FundingType,
    PositioningMetric,
    QualityFlag,
    QualityState,
    MissingReason,
]


def test_mandatory_enum_member_sets_are_frozen():
    for enum_cls in ENUM_CLASSES:
        expected = EXPECTED_MEMBERS[enum_cls.__name__]
        actual = {member.value for member in enum_cls}
        assert actual == expected, (
            f"{enum_cls.__name__} member set drifted: "
            f"unexpected={sorted(actual - expected)} missing={sorted(expected - actual)}"
        )


def test_enum_values_equal_names():
    """Deterministic canonical values: value == member name (02 §19)."""
    for enum_cls in ENUM_CLASSES:
        for member in enum_cls:
            assert member.value == member.name


def test_enums_are_string_serializable():
    for enum_cls in ENUM_CLASSES:
        for member in enum_cls:
            assert str(member) == member.value
            assert enum_cls(member.value) is member
