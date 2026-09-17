"""Bloc 1 mandatory contract enums.

Every canonical vocabulary value below is frozen by the Bloc 1 planning books
(`bloc_01/01_BLOC_01_CONTRACTS_AND_SEMANTICS.md` §3, §7–§12 and
`02_SCHEMA_AND_PROVIDER_REGISTRY.md` §17).  Changing a member set is a schema
breaking change requiring a major version bump and an operator review note.

Provider IDs, venue IDs and methodology IDs are deliberately NOT enum members:
they evolve independently and are controlled through the registries in
`config/crypto_sensor_fabric/`.
"""

from __future__ import annotations

from enum import Enum


class _StrEnum(str, Enum):
    """Deterministic string-valued enum base (values equal member names)."""

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


class SensorFamily(_StrEnum):
    """Canonical sensor families (frozen initial set, Bloc 1 §3 / F2)."""

    MECHANICAL_TRADE = "MECHANICAL_TRADE"
    MECHANICAL_LIQUIDATION = "MECHANICAL_LIQUIDATION"
    MECHANICAL_OPEN_INTEREST = "MECHANICAL_OPEN_INTEREST"
    MECHANICAL_FUNDING = "MECHANICAL_FUNDING"
    MECHANICAL_BOOK_SNAPSHOT = "MECHANICAL_BOOK_SNAPSHOT"
    MECHANICAL_BOOK_METRIC = "MECHANICAL_BOOK_METRIC"
    MECHANICAL_POSITIONING = "MECHANICAL_POSITIONING"
    MECHANICAL_BASIS = "MECHANICAL_BASIS"


class AccessClass(_StrEnum):
    """Free-only access taxonomy (Bloc 1 §7)."""

    FREE_AUTOMATED = "FREE_AUTOMATED"
    FREE_LIMITED_AUTOMATED = "FREE_LIMITED_AUTOMATED"
    FREE_REFERENCE_ONLY = "FREE_REFERENCE_ONLY"
    PAID_EXCLUDED = "PAID_EXCLUDED"
    UNVERIFIED = "UNVERIFIED"


class EvidenceClass(_StrEnum):
    """Evidentiary provenance class, independent of cost/access (Bloc 1 §8)."""

    FIRST_PARTY_EXCHANGE = "FIRST_PARTY_EXCHANGE"
    FIRST_PARTY_AGGREGATOR = "FIRST_PARTY_AGGREGATOR"
    THIRD_PARTY_AGGREGATOR = "THIRD_PARTY_AGGREGATOR"
    COMMUNITY_ARCHIVE = "COMMUNITY_ARCHIVE"
    RECONSTRUCTED_INTERNAL = "RECONSTRUCTED_INTERNAL"


class RetrievalMode(_StrEnum):
    """How raw source content was retrieved (Bloc 1 §6)."""

    REST = "REST"
    WS = "WS"
    BULK_FILE = "BULK_FILE"
    COMMUNITY_ARCHIVE = "COMMUNITY_ARCHIVE"


class SemanticEquivalence(_StrEnum):
    """Provider→canonical semantic equivalence class (Bloc 1 §9 / F11)."""

    EXACT_EQUIVALENT = "EXACT_EQUIVALENT"
    NORMALIZABLE_COMPARABLE = "NORMALIZABLE_COMPARABLE"
    CORROBORATION_ONLY = "CORROBORATION_ONLY"
    NOT_COMPARABLE = "NOT_COMPARABLE"


class MarketType(_StrEnum):
    """Economic market type (spot / futures / perpetual / option)."""

    SPOT = "SPOT"
    FUTURE = "FUTURE"
    PERPETUAL = "PERPETUAL"
    OPTION = "OPTION"
    OTHER = "OTHER"


class ContractType(_StrEnum):
    """Contract settlement construction (linear vs inverse vs quanto)."""

    LINEAR = "LINEAR"
    INVERSE = "INVERSE"
    QUANTO = "QUANTO"
    OTHER = "OTHER"


class AggressorSide(_StrEnum):
    """Aggressor (taker) side; also used for maker side on trade records."""

    BUY = "BUY"
    SELL = "SELL"
    UNKNOWN = "UNKNOWN"


class AggregationType(_StrEnum):
    """Trade record shape: single event vs provider-aggregated trade."""

    INDIVIDUAL = "INDIVIDUAL"
    AGGREGATED = "AGGREGATED"


class LiquidationSide(_StrEnum):
    """Position side that was liquidated (forced deleveraging)."""

    LONG = "LONG"
    SHORT = "SHORT"
    BOTH = "BOTH"
    UNKNOWN = "UNKNOWN"


class LiquidationRole(_StrEnum):
    """Liquidation role when a provider distinguishes maker/taker."""

    MAKER = "MAKER"
    TAKER = "TAKER"
    BOTH = "BOTH"
    UNKNOWN = "UNKNOWN"


class LiquidationEventShape(_StrEnum):
    """Liquidation observation shape; shapes are never numerically merged (T11)."""

    TRADE_LEVEL = "TRADE_LEVEL"
    INTERVAL_AGGREGATE = "INTERVAL_AGGREGATE"
    TOTAL_AGGREGATE = "TOTAL_AGGREGATE"


class NativeOIUnit(_StrEnum):
    """Unit of the provider-native open-interest value."""

    CONTRACTS = "CONTRACTS"
    BASE_ASSET = "BASE_ASSET"
    QUOTE_ASSET = "QUOTE_ASSET"
    USD = "USD"
    OTHER = "OTHER"


class FundingType(_StrEnum):
    """Whether a funding value is realized or predicted by the provider."""

    REALIZED = "REALIZED"
    PREDICTED = "PREDICTED"
    UNKNOWN = "UNKNOWN"


class PositioningMetric(_StrEnum):
    """Positioning population metric; different populations are never equated."""

    GLOBAL_LONG_SHORT_RATIO = "GLOBAL_LONG_SHORT_RATIO"
    TOP_TRADER_ACCOUNT_RATIO = "TOP_TRADER_ACCOUNT_RATIO"
    TOP_TRADER_POSITION_RATIO = "TOP_TRADER_POSITION_RATIO"
    TAKER_LONG_SHORT_RATIO = "TAKER_LONG_SHORT_RATIO"
    USER_LONG_SHORT_RATIO = "USER_LONG_SHORT_RATIO"


class QualityFlag(_StrEnum):
    """Additive per-record quality flags (Bloc 1 §12). Canonical set."""

    SOURCE_NATIVE = "SOURCE_NATIVE"
    SOURCE_AGGREGATED = "SOURCE_AGGREGATED"
    SOURCE_COMMUNITY = "SOURCE_COMMUNITY"
    RECONSTRUCTED_INTERNAL = "RECONSTRUCTED_INTERNAL"
    TIMESTAMP_ASSUMED = "TIMESTAMP_ASSUMED"
    TIMESTAMP_COARSE = "TIMESTAMP_COARSE"
    UNIT_NATIVE_ONLY = "UNIT_NATIVE_ONLY"
    UNIT_NORMALIZED = "UNIT_NORMALIZED"
    UNIT_NORMALIZATION_UNAVAILABLE = "UNIT_NORMALIZATION_UNAVAILABLE"
    VENUE_NOT_DECOMPOSABLE = "VENUE_NOT_DECOMPOSABLE"
    INSTRUMENT_ID_UNRESOLVED = "INSTRUMENT_ID_UNRESOLVED"
    WINDOW_SEMANTICS_UNCERTAIN = "WINDOW_SEMANTICS_UNCERTAIN"
    PARTIAL_INTERVAL = "PARTIAL_INTERVAL"
    DUPLICATE_SOURCE_RECORD = "DUPLICATE_SOURCE_RECORD"
    SOURCE_GAP = "SOURCE_GAP"
    STALE_SOURCE = "STALE_SOURCE"
    PROVIDER_DEGRADED = "PROVIDER_DEGRADED"
    CROSS_PROVIDER_DISAGREEMENT = "CROSS_PROVIDER_DISAGREEMENT"
    HISTORICAL_DEPTH_UNVERIFIED = "HISTORICAL_DEPTH_UNVERIFIED"
    ACCESS_CLASS_UNVERIFIED = "ACCESS_CLASS_UNVERIFIED"
    PIT_RISK = "PIT_RISK"


class QualityState(_StrEnum):
    """Future-compatible runtime health states (Bloc 1 §17 / 02 §17)."""

    GOOD = "GOOD"
    DEGRADED = "DEGRADED"
    STALE = "STALE"
    PARTIAL = "PARTIAL"
    UNVERIFIED = "UNVERIFIED"
    BLOCKED = "BLOCKED"


class MissingReason(_StrEnum):
    """Structured missingness vocabulary (Bloc 1 §11). No member is a zero."""

    NOT_SUPPORTED = "NOT_SUPPORTED"
    NOT_LISTED = "NOT_LISTED"
    OUTSIDE_PROVIDER_HISTORY = "OUTSIDE_PROVIDER_HISTORY"
    ENDPOINT_UNAVAILABLE = "ENDPOINT_UNAVAILABLE"
    RATE_LIMITED = "RATE_LIMITED"
    AUTH_BLOCKED = "AUTH_BLOCKED"
    GEO_BLOCKED = "GEO_BLOCKED"
    PROVIDER_GAP = "PROVIDER_GAP"
    PARSE_FAILED = "PARSE_FAILED"
    SEMANTIC_UNRESOLVED = "SEMANTIC_UNRESOLVED"
    DATA_BLOCKED = "DATA_BLOCKED"


class BookSide(_StrEnum):
    """Side qualifier for book metrics (02 §9)."""

    BID = "BID"
    ASK = "ASK"
    BOTH = "BOTH"
    NONE = "NONE"


class ReferenceType(_StrEnum):
    """Basis reference price type (02 §11)."""

    SPOT = "SPOT"
    INDEX = "INDEX"
    MARK = "MARK"
    OTHER = "OTHER"


class BookMetricName(_StrEnum):
    """Initial canonical book metric names (02 §9)."""

    SPREAD_BPS = "SPREAD_BPS"
    DEPTH_BID_5BPS = "DEPTH_BID_5BPS"
    DEPTH_ASK_5BPS = "DEPTH_ASK_5BPS"
    DEPTH_BID_10BPS = "DEPTH_BID_10BPS"
    DEPTH_ASK_10BPS = "DEPTH_ASK_10BPS"
    DEPTH_BID_25BPS = "DEPTH_BID_25BPS"
    DEPTH_ASK_25BPS = "DEPTH_ASK_25BPS"
    DEPTH_BID_50BPS = "DEPTH_BID_50BPS"
    DEPTH_ASK_50BPS = "DEPTH_ASK_50BPS"
    BOOK_IMBALANCE_10BPS = "BOOK_IMBALANCE_10BPS"
    BOOK_IMBALANCE_25BPS = "BOOK_IMBALANCE_25BPS"
    SLIPPAGE_BUY_10K_USD = "SLIPPAGE_BUY_10K_USD"
    SLIPPAGE_SELL_10K_USD = "SLIPPAGE_SELL_10K_USD"
    SLIPPAGE_BUY_100K_USD = "SLIPPAGE_BUY_100K_USD"
    SLIPPAGE_SELL_100K_USD = "SLIPPAGE_SELL_100K_USD"


class ProviderStatus(_StrEnum):
    """Registry lifecycle status for a provider entry."""

    CANDIDATE = "CANDIDATE"
    ACTIVE = "ACTIVE"
    DEMOTED = "DEMOTED"
    EXCLUDED = "EXCLUDED"


class VenueID(_StrEnum):
    """Canonical venue vocabulary (Bloc 1 §4.1).

    Used by registry configuration.  Schema `venue` fields are plain strings
    validated against registry-controlled values; this enum is the vocabulary
    those strings must come from.
    """

    KRAKEN_FUTURES = "KRAKEN_FUTURES"
    GATE_FUTURES = "GATE_FUTURES"
    BINANCE_USDM = "BINANCE_USDM"
    BYBIT_LINEAR = "BYBIT_LINEAR"
    OKX_SWAP = "OKX_SWAP"
    DERIBIT = "DERIBIT"
    BITFINEX = "BITFINEX"
    AGGREGATED_UNKNOWN = "AGGREGATED_UNKNOWN"
    UNKNOWN = "UNKNOWN"
