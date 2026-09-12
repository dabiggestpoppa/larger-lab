"""Deribit v2 public provider-native parsers (SENSOR-B3-I08).

Parsers are provider-native: they emit provider-native field names / units and
NEVER canonicalize (no interval liquidation totals, no CVD, no directional
interpretation, no funding-state model, no book imbalance/spread).  The raw
body is preserved upstream in the `RawPayloadEnvelope` before any parsed
convenience output exists.

Schema reality (Bloc 2 I13 fingerprints, 09_SCHEMA_FINGERPRINTS.jsonl):

- TRADE / LIQUIDATION envelope:
  `{jsonrpc:str, result: {has_more: bool, trades: [<row>]}, testnet, usDiff,
  usIn, usOut}`.  The runtime trade row is a closed THIRTEEN-field record:
  `amount, contracts, direction, index_price, instrument_name, mark_price,
  price, starbase_match_id, starbase_timestamp, tick_direction, timestamp,
  trade_id, trade_seq` — every field structurally required.  `timestamp` is an
  epoch-MILLISECOND int (strict `type(x) is int`, bool rejected).
- The LIQUIDATION fingerprint is a UNION shape: the same base row optionally
  carries `combo_id` / `combo_trade_id` (known-optional).  The `liquidation`
  flag (characterization-backed: `"liquidation" | "taker" | "maker"`) marks
  forced-liquidation trades and is KNOWN-OPTIONAL — never required, preserved
  verbatim when present.  The LIQUIDATION sensor projects ONLY rows whose flag
  value is `"liquidation"`; other rows (and rows without the flag) are ordinary
  trades and are excluded from the liquidation view (raw payload still fully
  preserved upstream).
- FUNDING envelope: `{jsonrpc:str, result: list[<row>], testnet, usDiff, usIn,
  usOut}` — `result` is a RAW LIST (observed LIVE; never `{data:[...]}`).  The
  runtime funding row is a closed FIVE-field record: `index_price,
  interest_1h, interest_8h, prev_index_price, timestamp` (epoch-ms int).
  `funding_rate` / `funding_1h` / `funding_8h` appear only in the Bloc 2
  probe/synthetic fixture (NOT the runtime fingerprint), so they are modeled
  as OPTIONAL / UNVERIFIED additive fields: never required, flagged ADDITIVE
  and preserved under their native names when present.
- BOOK envelope: `{jsonrpc:str, result: {bids, asks, timestamp, ...},
  testnet, usDiff, usIn, usOut}`.  Structural core: `timestamp` (epoch-ms
  int), `instrument_name` (str), `bids` + `asks` (list of levels).  Every
  other fingerprint-listed result field is KNOWN-OPTIONAL (validated when
  present).  Book levels are `list[float]` with at minimum `[price, amount]`
  (numeric semantic family; bool rejected; nothing converted, values preserved
  as returned).

Numeric semantic-family doctrine: price/amount/rate fields accept int or float
(legitimate provider variation) but NEVER bool; timestamp/sequence/id fields
use EXACT int typing so bool cannot masquerade.  Malformed timestamps and
missing structural fields are BREAKING (raw preserved, parsed blocked).
Never `dict.get(field, 0)`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...contracts.enums import SensorFamily
from ..base.enums import SchemaState
from ..base.schema import SchemaAssessment

# --------------------------------------------------------------------------- #
# per-sensor native field contracts
# --------------------------------------------------------------------------- #
#: TRADE/LIQUIDATION row REQUIRED fields — the closed THIRTEEN-field record of
#: the committed 09 trade fingerprint (RECENT_CONTROL runtime sample).
_TRADE_REQUIRED: frozenset[str] = frozenset(
    {
        "amount",
        "contracts",
        "direction",
        "index_price",
        "instrument_name",
        "mark_price",
        "price",
        "starbase_match_id",
        "starbase_timestamp",
        "tick_direction",
        "timestamp",
        "trade_id",
        "trade_seq",
    }
)
#: KNOWN-OPTIONAL trade/liquidation fields: `combo_id`/`combo_trade_id` come
#: from the LIQUIDATION fingerprint union shape; `liquidation` is the
#: characterization-backed forced-liquidation flag (`"liquidation"` value).
_TRADE_KNOWN: frozenset[str] = _TRADE_REQUIRED | frozenset(
    {"combo_id", "combo_trade_id", "liquidation"}
)

#: FUNDING row REQUIRED fields — the closed FIVE-field record of the committed
#: 09 funding fingerprint.  `funding_rate`/`funding_1h`/`funding_8h` are
#: probe-fixture-only (unverified additive) and are deliberately NOT in the
#: known set: their presence flags ADDITIVE while being preserved.
_FUNDING_REQUIRED: frozenset[str] = frozenset(
    {"index_price", "interest_1h", "interest_8h", "prev_index_price", "timestamp"}
)
_FUNDING_KNOWN: frozenset[str] = frozenset(_FUNDING_REQUIRED)

#: BOOK result REQUIRED semantic core (the sensor view).  The full fingerprint
#: result dict carries ~25 fields; the snapshot's semantic core is timestamp +
#: instrument_name + bids + asks.  Every other fingerprint-listed field is
#: KNOWN-OPTIONAL (validated when present, never required for the view).
_BOOK_REQUIRED: frozenset[str] = frozenset(
    {"timestamp", "instrument_name", "bids", "asks"}
)
_BOOK_KNOWN: frozenset[str] = frozenset(
    {
        "timestamp",
        "instrument_name",
        "bids",
        "asks",
        "best_ask_amount",
        "best_ask_price",
        "best_bid_amount",
        "best_bid_price",
        "change_id",
        "current_funding",
        "estimated_delivery_price",
        "funding_8h",
        "index_price",
        "interest_value",
        "last_price",
        "mark_price",
        "max_price",
        "min_price",
        "open_interest",
        "settlement_price",
        "state",
        "stats",
    }
)
_BOOK_NUMERIC_FIELDS: frozenset[str] = frozenset(
    {
        "best_ask_amount",
        "best_ask_price",
        "best_bid_amount",
        "best_bid_price",
        "current_funding",
        "estimated_delivery_price",
        "funding_8h",
        "index_price",
        "interest_value",
        "last_price",
        "mark_price",
        "max_price",
        "min_price",
        "settlement_price",
    }
)
_BOOK_EXACT_INT_FIELDS: frozenset[str] = frozenset({"change_id", "open_interest"})

#: Forced-liquidation flag value (characterization-backed: the `liquidation`
#: field marks forced-liquidation trades when it equals "liquidation").
LIQUIDATION_FLAG_VALUE = "liquidation"


# --------------------------------------------------------------------------- #
# assessment helpers
# --------------------------------------------------------------------------- #
def _breaking() -> SchemaAssessment:
    return SchemaAssessment(
        state=SchemaState.BREAKING_SCHEMA_CHANGE,
        raw_preserved=True,
        semantic_output_allowed=False,
    )


def _additive() -> SchemaAssessment:
    return SchemaAssessment(
        state=SchemaState.ADDITIVE_SCHEMA_CHANGE,
        raw_preserved=True,
        semantic_output_allowed=True,
    )


def _assess(
    observed: set[str], known: frozenset[str], required: frozenset[str]
) -> SchemaState:
    missing = required - observed
    if missing:
        return SchemaState.BREAKING_SCHEMA_CHANGE
    extra = observed - known
    if extra:
        return SchemaState.ADDITIVE_SCHEMA_CHANGE
    return SchemaState.KNOWN_SCHEMA


def _is_numeric(value: Any) -> bool:
    """Numeric semantic family: int or float; bool is NOT numeric here."""
    return type(value) in (int, float)


def _is_exact_int(value: Any) -> bool:
    """Exact int typing: bool (an int subclass) is rejected."""
    return type(value) is int


# --------------------------------------------------------------------------- #
# row validators
# --------------------------------------------------------------------------- #
def _validate_trade_row(row: dict[str, Any]) -> str | None:
    """Validate one trade/liquidation row; None means OK, else a violation."""
    if not _is_exact_int(row.get("timestamp")):
        return "timestamp malformed (expected epoch-ms int)"
    for field in ("starbase_match_id", "starbase_timestamp", "tick_direction", "trade_seq"):
        if not _is_exact_int(row.get(field)):
            return f"{field} malformed (expected exact int)"
    for field in ("amount", "contracts", "index_price", "mark_price", "price"):
        if not _is_numeric(row.get(field)):
            return f"{field} malformed (expected numeric semantic family)"
    for field in ("direction", "instrument_name", "trade_id"):
        if not isinstance(row.get(field), str):
            return f"{field} malformed (expected provider string)"
    for field in ("combo_id", "combo_trade_id", "liquidation"):
        if field in row and not isinstance(row[field], str):
            return f"{field} malformed (expected provider string)"
    return None


def _validate_funding_row(row: dict[str, Any]) -> str | None:
    """Validate one funding row; None means OK, else a violation."""
    if not _is_exact_int(row.get("timestamp")):
        return "timestamp malformed (expected epoch-ms int)"
    for field in ("index_price", "interest_1h", "interest_8h", "prev_index_price"):
        if not _is_numeric(row.get(field)):
            return f"{field} malformed (expected numeric semantic family)"
    return None


def _level_ok(level: Any) -> bool:
    """Book level: list of numerics with at minimum [price, amount].

    The runtime fingerprint declares `bids`/`asks` as `list[list[float]]` and
    the committed fixture shows `[price, amount]` pairs; optional trailing
    native components are allowed but every component must be numeric-family
    (bool rejected).  Nothing is converted; values are preserved as returned.
    """
    if not isinstance(level, list):
        return False
    if len(level) < 2:
        return False
    return all(_is_numeric(part) for part in level)


def _validate_book_result(result: dict[str, Any]) -> str | None:
    """Validate a book result dict; None means OK, else a violation."""
    if not _is_exact_int(result.get("timestamp")):
        return "timestamp malformed (expected epoch-ms int)"
    if not isinstance(result.get("instrument_name"), str):
        return "instrument_name malformed (expected provider string)"
    for side in ("bids", "asks"):
        levels = result.get(side)
        if not isinstance(levels, list):
            return f"{side} malformed (expected list of levels)"
        for level in levels:
            if not _level_ok(level):
                return f"{side} contains a malformed level (expected [price, amount, ...])"
    if "state" in result and not isinstance(result["state"], str):
        return "state malformed (expected provider string)"
    if "stats" in result and not isinstance(result["stats"], dict):
        return "stats malformed (expected provider dict)"
    for field in _BOOK_EXACT_INT_FIELDS:
        if field in result and not _is_exact_int(result[field]):
            return f"{field} malformed (expected exact int)"
    for field in _BOOK_NUMERIC_FIELDS:
        if field in result and not _is_numeric(result[field]):
            return f"{field} malformed (expected numeric semantic family)"
    return None


# --------------------------------------------------------------------------- #
# parsed result container
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ParsedDeribit:
    """Result of parsing one Deribit payload (trade / liquidation / funding / book)."""

    rows: tuple[dict[str, Any], ...]
    schema_state: SchemaState
    assessment: SchemaAssessment | None = None
    #: Provider-native terminal flag from the result envelope (trade/liq only):
    #: `has_more` bool, or None when the surface does not carry it (funding /
    #: book) or the envelope was structurally broken.
    has_more: bool | None = None
    #: Schema-validated epoch-ms timestamps of the FULL SOURCE page (I08R1
    #: coverage seam).  For TRADE this equals the semantic rows; for
    #: LIQUIDATION it is EVERY validated trade row (ordinary + forced
    #: liquidation) — the acquisition-coverage surface completion must be
    #: judged against, never against the narrower filtered projection.  For
    #: FUNDING it is every funding row (semantic == source).  Book snapshots
    #: do not use it.  Every member is an exact int (already schema-validated;
    #: no unvalidated raw timestamps reach the adapter).
    coverage_timestamps: tuple[int, ...] = ()

    @property
    def semantic_output_allowed(self) -> bool:
        if self.assessment is not None:
            return self.assessment.semantic_output_allowed
        return self.schema_state in (
            SchemaState.KNOWN_SCHEMA,
            SchemaState.ADDITIVE_SCHEMA_CHANGE,
        )


def _unknown() -> tuple[SchemaState, SchemaAssessment]:
    return SchemaState.UNKNOWN_SCHEMA, _breaking()


def _parse_trade_like(
    body: Any, sensor: SensorFamily, *, liquidation_only: bool
) -> ParsedDeribit:
    """Shared trade/liquidation envelope + row validation and projection."""
    if not isinstance(body, dict):
        state, assessment = _unknown()
        return ParsedDeribit(rows=(), schema_state=state, assessment=assessment)
    result = body.get("result")
    if not isinstance(result, dict):
        return ParsedDeribit(
            rows=(), schema_state=SchemaState.BREAKING_SCHEMA_CHANGE, assessment=_breaking()
        )
    if "has_more" not in result:
        return ParsedDeribit(
            rows=(), schema_state=SchemaState.BREAKING_SCHEMA_CHANGE, assessment=_breaking()
        )
    if not isinstance(result["has_more"], bool):
        return ParsedDeribit(
            rows=(), schema_state=SchemaState.BREAKING_SCHEMA_CHANGE, assessment=_breaking()
        )
    has_more = result["has_more"]
    trades = result.get("trades")
    if not isinstance(trades, list):
        return ParsedDeribit(
            rows=(), schema_state=SchemaState.BREAKING_SCHEMA_CHANGE, assessment=_breaking()
        )
    if not trades:
        # A valid empty trades list with a well-formed envelope is EMPTY_VALID:
        # no required-row assessment applies (structural absence of rows, not a
        # schema violation).  has_more is preserved.
        return ParsedDeribit(rows=(), schema_state=SchemaState.KNOWN_SCHEMA, has_more=has_more)

    observed: set[str] = set()
    for row in trades:
        if not isinstance(row, dict):
            return ParsedDeribit(
                rows=(), schema_state=SchemaState.BREAKING_SCHEMA_CHANGE, assessment=_breaking()
            )
        observed |= set(row)
        violation = _validate_trade_row(row)
        if violation is not None:
            return ParsedDeribit(
                rows=(), schema_state=SchemaState.BREAKING_SCHEMA_CHANGE, assessment=_breaking()
            )
    state = _assess(observed, _TRADE_KNOWN, _TRADE_REQUIRED)
    if state is SchemaState.BREAKING_SCHEMA_CHANGE:
        return ParsedDeribit(rows=(), schema_state=state, assessment=_breaking())

    # SOURCE-page coverage timestamps: every schema-validated trade row
    # (ordinary + forced liquidation) — the acquisition-coverage surface for
    # completion truth (I08R1 Defect C).  `timestamp` is already validated as
    # an exact int; no coercion here.
    coverage = tuple(int(row["timestamp"]) for row in trades)

    if liquidation_only:
        # Mechanism-microscope projection: retain ONLY rows whose
        # characterization-backed flag marks a forced liquidation.  Rows
        # without the flag (or with "taker"/"maker") are ordinary trades and
        # are excluded from the liquidation view — the FULL raw payload is
        # still preserved upstream in the RawPayloadEnvelope.
        rows = [row for row in trades if row.get("liquidation") == LIQUIDATION_FLAG_VALUE]
    else:
        rows = [dict(row) for row in trades]

    if state is SchemaState.ADDITIVE_SCHEMA_CHANGE:
        return ParsedDeribit(
            rows=tuple(rows), schema_state=state, assessment=_additive(),
            has_more=has_more, coverage_timestamps=coverage,
        )
    return ParsedDeribit(
        rows=tuple(rows), schema_state=state, has_more=has_more,
        coverage_timestamps=coverage,
    )


def parse_deribit_trades(body: Any) -> ParsedDeribit:
    """Parse a get_last_trades_by_instrument payload as MECHANICAL_TRADE."""
    return _parse_trade_like(body, SensorFamily.MECHANICAL_TRADE, liquidation_only=False)


def parse_deribit_liquidations(body: Any) -> ParsedDeribit:
    """Parse a get_last_trades_by_instrument payload as MECHANICAL_LIQUIDATION.

    Same physical envelope; the liquidation view retains only rows carrying the
    evidence-backed forced-liquidation flag value.  A page with no liquidation
    events yields row_count 0 / EMPTY_VALID while the raw payload is preserved
    upstream.  This is TRADE-LEVEL anatomy — never interval liquidation totals.
    """
    return _parse_trade_like(
        body, SensorFamily.MECHANICAL_LIQUIDATION, liquidation_only=True
    )


def parse_deribit_funding(body: Any) -> ParsedDeribit:
    """Parse a get_funding_rate_history payload (result is a RAW LIST)."""
    if not isinstance(body, dict):
        state, assessment = _unknown()
        return ParsedDeribit(rows=(), schema_state=state, assessment=assessment)
    result = body.get("result")
    # Observed LIVE: `result` is a raw list, NOT `{data:[...]}` — a dict result
    # (the old wrong envelope assumption) is BREAKING, never silently repaired.
    if not isinstance(result, list):
        return ParsedDeribit(
            rows=(), schema_state=SchemaState.BREAKING_SCHEMA_CHANGE, assessment=_breaking()
        )
    if not result:
        return ParsedDeribit(rows=(), schema_state=SchemaState.KNOWN_SCHEMA)

    observed: set[str] = set()
    for row in result:
        if not isinstance(row, dict):
            return ParsedDeribit(
                rows=(), schema_state=SchemaState.BREAKING_SCHEMA_CHANGE, assessment=_breaking()
            )
        observed |= set(row)
        violation = _validate_funding_row(row)
        if violation is not None:
            return ParsedDeribit(
                rows=(), schema_state=SchemaState.BREAKING_SCHEMA_CHANGE, assessment=_breaking()
            )
    state = _assess(observed, _FUNDING_KNOWN, _FUNDING_REQUIRED)
    if state is SchemaState.BREAKING_SCHEMA_CHANGE:
        return ParsedDeribit(rows=(), schema_state=state, assessment=_breaking())
    # Semantic rows == source rows for funding (no projection), so coverage is
    # the same validated timestamp set (I08R1 coverage seam).
    coverage = tuple(int(row["timestamp"]) for row in result)
    rows = [dict(row) for row in result]
    if state is SchemaState.ADDITIVE_SCHEMA_CHANGE:
        return ParsedDeribit(
            rows=tuple(rows), schema_state=state, assessment=_additive(),
            coverage_timestamps=coverage,
        )
    return ParsedDeribit(
        rows=tuple(rows), schema_state=state, coverage_timestamps=coverage
    )


def parse_deribit_book(body: Any) -> ParsedDeribit:
    """Parse a get_order_book snapshot (CURRENT_ONLY, native fields kept)."""
    if not isinstance(body, dict):
        state, assessment = _unknown()
        return ParsedDeribit(rows=(), schema_state=state, assessment=assessment)
    result = body.get("result")
    if not isinstance(result, dict):
        return ParsedDeribit(
            rows=(), schema_state=SchemaState.BREAKING_SCHEMA_CHANGE, assessment=_breaking()
        )
    violation = _validate_book_result(result)
    if violation is not None:
        return ParsedDeribit(
            rows=(), schema_state=SchemaState.BREAKING_SCHEMA_CHANGE, assessment=_breaking()
        )
    observed = set(result)
    state = _assess(observed, _BOOK_KNOWN, _BOOK_REQUIRED)
    if state is SchemaState.BREAKING_SCHEMA_CHANGE:
        return ParsedDeribit(rows=(), schema_state=state, assessment=_breaking())
    rows = [dict(result)]
    if state is SchemaState.ADDITIVE_SCHEMA_CHANGE:
        return ParsedDeribit(rows=tuple(rows), schema_state=state, assessment=_additive())
    return ParsedDeribit(rows=tuple(rows), schema_state=state)
