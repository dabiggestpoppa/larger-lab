"""Gate Futures provider-native parsers (SENSOR-B3-I06, parser doctrine).

Parsers are provider-native: they emit native field names and native units and
NEVER canonicalize (no canonical OI USD, no CVD, no LiquidationState /
FundingState / PositioningState / sign-asymmetry, no research features).  The
raw body is preserved upstream in the `RawPayloadEnvelope` before any parsed
convenience output exists.

Schema reality (Bloc 2 I13 / I13R1 fingerprints, 09_SCHEMA_FINGERPRINTS.jsonl):

- `contract_stats` (OI / LIQUIDATION / POSITIONING): a TOP-LEVEL LIST of
  provider-native dicts carrying one physical row whose fields span several
  mechanical concepts.  Each promoted sensor projects ONLY its own semantic
  subset — the same physical payload is NOT one combined sensor.
- `funding_rate`: a TOP-LEVEL LIST of `{r, t}` (r decimal string, t epoch
  seconds).

Structural validation is fail-closed: a required semantic field that is
missing or of the wrong type is BREAKING (parsed output blocked, raw
preserved); an EXTRA provider field is ADDITIVE (explicitly flagged, still
parsed); an empty top-level list in a valid in-range request is EMPTY_VALID.
Missing required fields are NEVER defaulted to zero (`row.get(f, 0)` is
forbidden).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...contracts.enums import SensorFamily
from ..base.enums import SchemaState
from ..base.schema import SchemaAssessment

# --------------------------------------------------------------------------- #
# contract_stats field type contract (from the committed union fingerprint)
# --------------------------------------------------------------------------- #
#: Fields that are STRICT integers (type(v) is int; bool excluded).
#: Includes the timestamp `time` (native epoch MILLISECONDS for contract_stats)
#: and the integer size/count fields.
_INT_FIELDS: frozenset[str] = frozenset(
    {
        "time",  # native epoch ms (contract_stats)
        "open_interest",  # contracts
        "long_liq_size",
        "short_liq_size",
        "long_taker_size",
        "short_taker_size",
        "long_users",
        "short_users",
        "top_long_account",
        "top_short_account",
        "top_long_size",
        "top_short_size",
    }
)
#: Fields that are provider STRING encodings (never coerced to numerics).
_STR_FIELDS: frozenset[str] = frozenset({"last_funding_rate"})
#: All other expected contract_stats fields are a NUMERIC semantic family —
#: int OR float per committed evidence (never bool), e.g. mark_price, lsr_*,
#: *_usd, *_amount, *_usd_new.
#: (Explicitly enumerated so a required-field type can be validated without an
#: ambiguous catch-all.)

_KNOWN_CONTRACT_STATS_FIELDS: frozenset[str] = _INT_FIELDS | _STR_FIELDS | frozenset(
    {
        "long_liq_amount",
        "long_liq_usd",
        "long_liq_usd_new",
        "short_liq_amount",
        "short_liq_usd",
        "short_liq_usd_new",
        "lsr_account",
        "lsr_taker",
        "mark_price",
        "open_interest_usd",
        "top_lsr_account",
        "top_lsr_size",
    }
)

#: Per-sensor required semantic fields (presence + type).  These NEVER default.
_CONTRACT_STATS_REQUIRED: dict[SensorFamily, frozenset[str]] = {
    SensorFamily.MECHANICAL_OPEN_INTEREST: frozenset(
        {"time", "open_interest", "open_interest_usd"}
    ),
    SensorFamily.MECHANICAL_LIQUIDATION: frozenset(
        {
            "time",
            "long_liq_size",
            "short_liq_size",
            "long_liq_usd",
            "short_liq_usd",
        }
    ),
    SensorFamily.MECHANICAL_POSITIONING: frozenset({"time", "lsr_taker", "lsr_account"}),
}

#: Per-sensor convenience projection (native names preserved; no cross-sensor
#: leakage of another sensor's semantics into the parsed view).
_CONTRACT_STATS_PROJECTION: dict[SensorFamily, frozenset[str]] = {
    SensorFamily.MECHANICAL_OPEN_INTEREST: frozenset(
        {"time", "open_interest", "open_interest_usd"}
    ),
    SensorFamily.MECHANICAL_LIQUIDATION: frozenset(
        {
            "time",
            "long_liq_size",
            "short_liq_size",
            "long_liq_usd",
            "short_liq_usd",
            "long_liq_amount",
            "short_liq_amount",
            "long_liq_usd_new",
            "short_liq_usd_new",
            "long_taker_size",
            "short_taker_size",
        }
    ),
    SensorFamily.MECHANICAL_POSITIONING: frozenset(
        {
            "time",
            "lsr_taker",
            "lsr_account",
            "top_lsr_account",
            "top_lsr_size",
            "top_long_size",
            "top_short_size",
            "top_long_account",
            "top_short_account",
            "long_users",
            "short_users",
        }
    ),
}

#: Funding rows `{r, t}`: r string decimal, t strict int (epoch SECONDS).
_FUNDING_REQUIRED: frozenset[str] = frozenset({"r", "t"})
_FUNDING_PROJECTION: frozenset[str] = frozenset({"r", "t"})


@dataclass(frozen=True)
class ParsedAnalytics:
    """Result of parsing one Gate Market Analytics payload."""

    rows: tuple[dict[str, Any], ...]
    schema_state: SchemaState
    assessment: SchemaAssessment | None = None
    more: bool = False

    @property
    def semantic_output_allowed(self) -> bool:
        if self.assessment is not None:
            return self.assessment.semantic_output_allowed
        return self.schema_state in (
            SchemaState.KNOWN_SCHEMA,
            SchemaState.ADDITIVE_SCHEMA_CHANGE,
        )


def _type_ok(value: Any, field: str) -> bool:
    if field in _INT_FIELDS:
        return type(value) is int  # bool (a subclass) is rejected
    if field in _STR_FIELDS or field == "r":  # funding `r` is a native decimal string
        return type(value) is str
    return type(value) in (int, float)  # numeric semantic family; bool rejected


def _breaking_assessment() -> SchemaAssessment:
    return SchemaAssessment(
        state=SchemaState.BREAKING_SCHEMA_CHANGE,
        raw_preserved=True,
        semantic_output_allowed=False,
    )


def _dict_row_violation(row: dict[str, Any], required: frozenset[str]) -> str | None:
    # provider-declared null VALUES inside a well-typed field stay native data
    # (structural absence != provider null).  We validate PRESENCE + TYPE per
    # required field; a present-but-None required scalar is a schema break.
    for field in required:
        if field not in row:
            return f"missing required field {field!r}"
        if not _type_ok(row[field], field):
            return (
                f"field {field!r} wrong type "
                f"{type(row[field]).__name__} (expected strict type)"
            )
    return None


def _assess_extra_fields(observed_keys: set[str], known: frozenset[str]) -> SchemaState:
    extra = observed_keys - known
    if extra:
        return SchemaState.ADDITIVE_SCHEMA_CHANGE
    return SchemaState.KNOWN_SCHEMA


def parse_gate_contract_stats(
    body: Any,
    sensor: SensorFamily,
) -> ParsedAnalytics:
    """Parse a `contract_stats` top-level list for one promoted sensor.

    The full physical row is preserved raw upstream; the parsed convenience
    view projects only this sensor's semantic subset.  Empty list -> EMPTY_VALID.
    """
    if sensor not in _CONTRACT_STATS_REQUIRED:
        return ParsedAnalytics(
            rows=(), more=False, schema_state=SchemaState.UNKNOWN_SCHEMA
        )
    if not isinstance(body, list):
        return ParsedAnalytics(
            rows=(), more=False, schema_state=SchemaState.UNKNOWN_SCHEMA
        )
    if not body:
        return ParsedAnalytics(
            rows=(), more=False, schema_state=SchemaState.KNOWN_SCHEMA
        )

    required = _CONTRACT_STATS_REQUIRED[sensor]
    projection = _CONTRACT_STATS_PROJECTION[sensor]
    for row in body:
        if not isinstance(row, dict):
            return ParsedAnalytics(
                rows=(), more=False, schema_state=SchemaState.BREAKING_SCHEMA_CHANGE
            )
        violation = _dict_row_violation(row, required)
        if violation is not None:
            return ParsedAnalytics(
                rows=(),
                more=False,
                schema_state=SchemaState.BREAKING_SCHEMA_CHANGE,
                assessment=_breaking_assessment(),
            )

    state = _assess_extra_fields(
        set().union(*[set(r) for r in body if isinstance(r, dict)]),
        _KNOWN_CONTRACT_STATS_FIELDS,
    )
    rows: list[dict[str, Any]] = []
    for row in body:
        rows.append({f: row[f] for f in projection if f in row})
    if state is SchemaState.ADDITIVE_SCHEMA_CHANGE:
        assessment = SchemaAssessment(
            state=SchemaState.ADDITIVE_SCHEMA_CHANGE,
            raw_preserved=True,
            semantic_output_allowed=True,
        )
        return ParsedAnalytics(
            rows=tuple(rows), more=False, schema_state=state, assessment=assessment
        )
    return ParsedAnalytics(rows=tuple(rows), more=False, schema_state=state)


def parse_gate_funding(body: Any) -> ParsedAnalytics:
    """Parse the funding `list[dict{r,t}]` payload.

    `t` is native epoch SECONDS (strict int); `r` is a provider decimal string.
    Empty list -> EMPTY_VALID.  Malformed rows -> BREAKING (raw preserved).
    """
    if not isinstance(body, list):
        return ParsedAnalytics(
            rows=(), more=False, schema_state=SchemaState.UNKNOWN_SCHEMA
        )
    if not body:
        return ParsedAnalytics(
            rows=(), more=False, schema_state=SchemaState.KNOWN_SCHEMA
        )

    for row in body:
        if not isinstance(row, dict):
            return ParsedAnalytics(
                rows=(), more=False, schema_state=SchemaState.BREAKING_SCHEMA_CHANGE
            )
        violation = _dict_row_violation(row, _FUNDING_REQUIRED)
        if violation is not None:
            return ParsedAnalytics(
                rows=(),
                more=False,
                schema_state=SchemaState.BREAKING_SCHEMA_CHANGE,
                assessment=_breaking_assessment(),
            )

    state = _assess_extra_fields(
        set().union(*[set(r) for r in body if isinstance(r, dict)]),
        _FUNDING_PROJECTION,
    )
    rows = [{f: row[f] for f in _FUNDING_PROJECTION if f in row} for row in body]
    if state is SchemaState.ADDITIVE_SCHEMA_CHANGE:
        assessment = SchemaAssessment(
            state=SchemaState.ADDITIVE_SCHEMA_CHANGE,
            raw_preserved=True,
            semantic_output_allowed=True,
        )
        return ParsedAnalytics(
            rows=tuple(rows), more=False, schema_state=state, assessment=assessment
        )
    return ParsedAnalytics(rows=tuple(rows), more=False, schema_state=state)