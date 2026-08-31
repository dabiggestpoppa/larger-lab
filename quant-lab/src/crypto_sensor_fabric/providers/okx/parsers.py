"""OKX Swap provider-native parsers (SENSOR-B3-I07, parser doctrine).

Parsers are provider-native: they emit provider-native field names / units and
NEVER canonicalize (no canonical USD quantity, no CVD, no FundingState /
LiquidationState / book imbalance / spread regime, no sign-asymmetry, no
research feature).  The raw body is preserved upstream in the
`RawPayloadEnvelope` before any parsed convenience output exists.

Schema reality (Bloc 2 I13 fingerprints, 09_SCHEMA_FINGERPRINTS.jsonl):

- FUNDING: envelope `{code:str, data:[{formulaType, fundingRate, fundingTime,
  instId, instType, method, realizedRate}], msg}` — `fundingTime` is a
  millisecond-epoch STRING.
- TRADE:   envelope `{code:str, data:[{instId, px, side, source, sz, tradeId,
  ts}], msg}` — `ts` is a millisecond-epoch STRING; `side` is the provider
  native aggressor side preserved verbatim.
- BOOK:    envelope `{code:str, data:[{asks:list[list[str]], bids:list[list[str]],
  seqId:int, ts:str}], msg}` — `bids`/`asks` are native list-of-list price/size
  rows, `ts` is a millisecond-epoch STRING, `seqId` is an int.

Timestamps are validated strictly as provider-native ms-epoch STRINGS:
`type(v) is str` plus a numeric-string check.  `None` / bool / int / float are
rejected (no silent coercion) — a malformed timestamp is BREAKING and blocks
parsed output.  Structural missingness is BREAKING (raw preserved, parsed
blocked); an extra provider field is ADDITIVE when required semantics remain.
Never `dict.get(field, 0)`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from ...contracts.enums import SensorFamily
from ..base.enums import SchemaState
from ..base.schema import SchemaAssessment

#: ms-epoch string syntax: 1+ ASCII digits (no sign, no decimal, no separator).
_MS_EPOCH_STR = re.compile(r"\A\d+\Z")


# --------------------------------------------------------------------------- #
# per-sensor native field contracts
# --------------------------------------------------------------------------- #
#: FUNDING required semantic fields (type str for the record scalars).
_FUNDING_REQUIRED: frozenset[str] = frozenset(
    {"fundingRate", "fundingTime", "realizedRate"}
)
_FUNDING_KNOWN: frozenset[str] = frozenset(
    {
        "fundingRate",
        "fundingTime",
        "realizedRate",
        "formulaType",
        "instId",
        "instType",
        "method",
        "markPrice",  # present in committed fixture (I13 evidence)
    }
)
_FUNDING_PROJECTION: frozenset[str] = frozenset(
    {
        "fundingTime",
        "fundingRate",
        "realizedRate",
        "formulaType",
        "instId",
        "instType",
        "method",
        "markPrice",
    }
)

#: TRADE required semantic fields (all str).
_TRADE_REQUIRED: frozenset[str] = frozenset({"px", "side", "sz", "tradeId", "ts"})
_TRADE_KNOWN: frozenset[str] = frozenset(
    {"instId", "px", "side", "source", "sz", "tradeId", "ts"}
)
_TRADE_PROJECTION: frozenset[str] = frozenset(
    {"instId", "px", "side", "source", "sz", "tradeId", "ts"}
)

#: BOOK required semantic fields (bids/asks list-of-list, ts string).
_BOOK_REQUIRED: frozenset[str] = frozenset({"asks", "bids", "ts"})
_BOOK_KNOWN: frozenset[str] = frozenset({"asks", "bids", "ts", "seqId"})
_BOOK_PROJECTION: frozenset[str] = frozenset({"ts", "asks", "bids", "seqId"})


def _is_ms_epoch_str(value: Any) -> bool:
    """Strict provider-native ms-epoch string check (bool/int/float/None fail)."""
    if not isinstance(value, str):
        return False
    return _MS_EPOCH_STR.match(value) is not None


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


def _assess(observed: set[str], known: frozenset[str], required: frozenset[str]) -> SchemaState:
    missing = required - observed
    if missing:
        return SchemaState.BREAKING_SCHEMA_CHANGE
    extra = observed - known
    if extra:
        return SchemaState.ADDITIVE_SCHEMA_CHANGE
    return SchemaState.KNOWN_SCHEMA


@dataclass(frozen=True)
class ParsedOkx:
    """Result of parsing one OKX payload (funding / trade / book)."""

    rows: tuple[dict[str, Any], ...]
    schema_state: SchemaState
    assessment: SchemaAssessment | None = None

    @property
    def semantic_output_allowed(self) -> bool:
        if self.assessment is not None:
            return self.assessment.semantic_output_allowed
        return self.schema_state in (
            SchemaState.KNOWN_SCHEMA,
            SchemaState.ADDITIVE_SCHEMA_CHANGE,
        )


def _envelope_data(body: Any, sensor: SensorFamily) -> tuple[tuple[SchemaState, SchemaAssessment | None, list[Any]]]:
    """Validate the OKX envelope and return the `data` list (or drift state)."""
    if not isinstance(body, dict):
        return ((SchemaState.UNKNOWN_SCHEMA, _breaking(), []),)
    if "data" not in body or not isinstance(body["data"], list):
        return ((SchemaState.BREAKING_SCHEMA_CHANGE, _breaking(), []),)
    return ((SchemaState.KNOWN_SCHEMA, None, body["data"]),)


def _validate_funding_row(row: dict[str, Any]) -> str | None:
    if "fundingTime" in row and not _is_ms_epoch_str(row["fundingTime"]):
        return "fundingTime malformed (expected ms-epoch numeric string)"
    for field in ("fundingRate", "realizedRate"):
        if field in row and not isinstance(row[field], str):
            return f"{field} malformed (expected provider string)"
    return None


def parse_okx_funding(body: Any, symbol: str = "") -> ParsedOkx:
    """Parse an OKX funding-rate-history payload (native fields preserved)."""
    envelope = _envelope_data(body, SensorFamily.MECHANICAL_FUNDING)
    state, assessment, data = envelope[0]
    if state is not SchemaState.KNOWN_SCHEMA:
        return ParsedOkx(rows=(), schema_state=state, assessment=assessment)
    if not data:
        return ParsedOkx(rows=(), schema_state=SchemaState.KNOWN_SCHEMA)

    observed: set[str] = set()
    for row in data:
        if not isinstance(row, dict):
            return ParsedOkx(rows=(), schema_state=SchemaState.BREAKING_SCHEMA_CHANGE, assessment=_breaking())
        observed |= set(row)
        violation = _validate_funding_row(row)
        if violation is not None:
            return ParsedOkx(rows=(), schema_state=SchemaState.BREAKING_SCHEMA_CHANGE, assessment=_breaking())
    st = _assess(observed, _FUNDING_KNOWN, _FUNDING_REQUIRED)
    if st is SchemaState.BREAKING_SCHEMA_CHANGE:
        return ParsedOkx(rows=(), schema_state=st, assessment=_breaking())
    rows = [{f: row[f] for f in _FUNDING_PROJECTION if f in row} for row in data]
    if st is SchemaState.ADDITIVE_SCHEMA_CHANGE:
        return ParsedOkx(rows=tuple(rows), schema_state=st, assessment=_additive())
    return ParsedOkx(rows=tuple(rows), schema_state=st)


def parse_okx_trades(body: Any) -> ParsedOkx:
    """Parse an OKX history-trades payload (native fields preserved)."""
    envelope = _envelope_data(body, SensorFamily.MECHANICAL_TRADE)
    state, assessment, data = envelope[0]
    if state is not SchemaState.KNOWN_SCHEMA:
        return ParsedOkx(rows=(), schema_state=state, assessment=assessment)
    if not data:
        return ParsedOkx(rows=(), schema_state=SchemaState.KNOWN_SCHEMA)

    observed: set[str] = set()
    for row in data:
        if not isinstance(row, dict):
            return ParsedOkx(rows=(), schema_state=SchemaState.BREAKING_SCHEMA_CHANGE, assessment=_breaking())
        observed |= set(row)
        if "ts" in row and not _is_ms_epoch_str(row["ts"]):
            return ParsedOkx(rows=(), schema_state=SchemaState.BREAKING_SCHEMA_CHANGE, assessment=_breaking())
        for field in ("tradeId", "px", "sz", "side"):
            if field in row and not isinstance(row[field], str):
                return ParsedOkx(rows=(), schema_state=SchemaState.BREAKING_SCHEMA_CHANGE, assessment=_breaking())
    st = _assess(observed, _TRADE_KNOWN, _TRADE_REQUIRED)
    if st is SchemaState.BREAKING_SCHEMA_CHANGE:
        return ParsedOkx(rows=(), schema_state=st, assessment=_breaking())
    rows = [{f: row[f] for f in _TRADE_PROJECTION if f in row} for row in data]
    if st is SchemaState.ADDITIVE_SCHEMA_CHANGE:
        return ParsedOkx(rows=tuple(rows), schema_state=st, assessment=_additive())
    return ParsedOkx(rows=tuple(rows), schema_state=st)


def _level_ok(level: Any) -> bool:
    if not isinstance(level, list):
        return False
    if not level:
        return False
    return all(isinstance(part, str) for part in level)


def parse_okx_book(body: Any) -> ParsedOkx:
    """Parse an OKX market-books snapshot (CURRENT_ONLY, native fields kept)."""
    envelope = _envelope_data(body, SensorFamily.MECHANICAL_BOOK_SNAPSHOT)
    state, assessment, data = envelope[0]
    if state is not SchemaState.KNOWN_SCHEMA:
        return ParsedOkx(rows=(), schema_state=state, assessment=assessment)
    if not data:
        # a current snapshot returning no book is an empty-valid observation
        return ParsedOkx(rows=(), schema_state=SchemaState.KNOWN_SCHEMA)

    observed: set[str] = set()
    for book in data:
        if not isinstance(book, dict):
            return ParsedOkx(rows=(), schema_state=SchemaState.BREAKING_SCHEMA_CHANGE, assessment=_breaking())
        observed |= set(book)
        if "ts" in book and not _is_ms_epoch_str(book["ts"]):
            return ParsedOkx(rows=(), schema_state=SchemaState.BREAKING_SCHEMA_CHANGE, assessment=_breaking())
        if "seqId" in book and not isinstance(book["seqId"], int):
            return ParsedOkx(rows=(), schema_state=SchemaState.BREAKING_SCHEMA_CHANGE, assessment=_breaking())
        for side in ("bids", "asks"):
            if side in book and not isinstance(book[side], list):
                return ParsedOkx(rows=(), schema_state=SchemaState.BREAKING_SCHEMA_CHANGE, assessment=_breaking())
            if side in book:
                for level in book[side]:
                    if not _level_ok(level):
                        return ParsedOkx(
                            rows=(), schema_state=SchemaState.BREAKING_SCHEMA_CHANGE, assessment=_breaking()
                        )
    st = _assess(observed, _BOOK_KNOWN, _BOOK_REQUIRED)
    if st is SchemaState.BREAKING_SCHEMA_CHANGE:
        return ParsedOkx(rows=(), schema_state=st, assessment=_breaking())
    rows = [{f: book[f] for f in _BOOK_PROJECTION if f in book} for book in data]
    if st is SchemaState.ADDITIVE_SCHEMA_CHANGE:
        return ParsedOkx(rows=tuple(rows), schema_state=st, assessment=_additive())
    return ParsedOkx(rows=tuple(rows), schema_state=st)