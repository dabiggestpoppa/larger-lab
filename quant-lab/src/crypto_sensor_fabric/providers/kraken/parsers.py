"""Kraken Market Analytics parsers (SENSOR-B3-I05, parser doctrine).

Parsers are provider-native: they emit native timestamps, native symbol, native
analytic field names and native values — never canonical OI USD, cross-venue
CVD, LiquidationState/FundingState/PositioningState, sign-asymmetry features or
research mechanisms.  The raw body is preserved upstream in the
`RawPayloadEnvelope` before any parsed convenience output exists.

Bloc 2 observed (I13R1 §2 / schema fingerprints) that Kraken analytics `data`
may be EITHER a list-of-buckets (OI, positioning, liquidation-volume) OR a dict
of per-metric lists parallel to `timestamp` (funding `{rate, relativeRate}`,
basis `{basis}`, orderbook `{ask, bid}`).  Both shapes are handled here.

Schema policy uses the common FAIL-CLOSED classifier: KNOWN / ADDITIVE may
produce parsed rows; BREAKING / UNKNOWN keep raw and block parsed output.  A
missing semantic field is NEVER coerced to 0 / False / '' / [].
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...contracts.enums import SensorFamily
from ..base.enums import SchemaState
from ..base.schema import SchemaAssessment, assess_schema

#: Sensors whose analytics `data` is a LIST of linear buckets (datum per ts).
_LIST_DATA_SENSORS: frozenset[SensorFamily] = frozenset(
    {
        SensorFamily.MECHANICAL_OPEN_INTEREST,
        SensorFamily.MECHANICAL_POSITIONING,
        SensorFamily.MECHANICAL_LIQUIDATION,
    }
)

#: Sensors whose analytics `data` is a DICT of per-metric lists + the primary
#: required metric key for schema classification (additional metrics = additive).
_DICT_DATA_REQUIRED: dict[SensorFamily, frozenset[str]] = {
    SensorFamily.MECHANICAL_FUNDING: frozenset({"rate"}),
    SensorFamily.MECHANICAL_BASIS: frozenset({"basis"}),
    SensorFamily.MECHANICAL_BOOK_METRIC: frozenset({"ask", "bid"}),
}


@dataclass(frozen=True)
class ParsedAnalytics:
    """Result of parsing one Kraken Market Analytics payload."""

    rows: tuple[dict[str, Any], ...]
    more: bool
    schema_state: SchemaState
    assessment: SchemaAssessment | None = None

    @property
    def semantic_output_allowed(self) -> bool:
        """True when parsed rows may be consumed (KNOWN/ADDITIVE only).

        Single source of truth for the fail-closed adapter decision; a
        BREAKING/UNKNOWN payload always blocks parsed output here (the raw
        body is preserved upstream in the RawPayloadEnvelope).
        """
        if self.assessment is not None:
            return self.assessment.semantic_output_allowed
        return self.schema_state in (
            SchemaState.KNOWN_SCHEMA,
            SchemaState.ADDITIVE_SCHEMA_CHANGE,
        )


def _envelope_ok(body: Any) -> tuple[bool, dict[str, Any] | None]:
    if not isinstance(body, dict):
        return False, None
    result = body.get("result")
    if not isinstance(result, dict):
        return False, None
    if not isinstance(result.get("timestamp"), list):
        return False, None
    return True, result


def parse_kraken_analytics(
    body: Any, sensor: SensorFamily
) -> ParsedAnalytics:
    """Parse one Market Analytics envelope for a promoted sensor.

    On BREAKING/UNKNOWN schema the raw body is preserved upstream and parsed
    output is blocked (the adapter raises `SchemaDrift`); rows is empty here.
    """
    ok, result = _envelope_ok(body)
    if not ok or result is None:
        return ParsedAnalytics(
            rows=(),
            more=False,
            schema_state=SchemaState.UNKNOWN_SCHEMA,
        )

    more = bool(result.get("more", False))
    timestamps = result["timestamp"]
    data = result.get("data")

    if isinstance(data, dict):
        if sensor not in _DICT_DATA_REQUIRED:
            # a list-shape sensor returned a dict -> schema changed
            return ParsedAnalytics(
                rows=(), more=more, schema_state=SchemaState.UNKNOWN_SCHEMA
            )
        required = _DICT_DATA_REQUIRED[sensor]
        observed = set(data.keys())
        assessment = assess_schema(set(required), observed, semantics_known=True)
        if not assessment.semantic_output_allowed:
            return ParsedAnalytics(
                rows=(), more=more, schema_state=assessment.state, assessment=assessment
            )
        # fail closed: a metric column shorter than the timestamp column is a
        # schema break (never zero-pad / silently truncate)
        if _any_short_column(data, timestamps):
            short_assessment = SchemaAssessment(
                state=SchemaState.BREAKING_SCHEMA_CHANGE,
                raw_preserved=True,
                semantic_output_allowed=False,
            )
            return ParsedAnalytics(
                rows=(),
                more=more,
                schema_state=SchemaState.BREAKING_SCHEMA_CHANGE,
                assessment=short_assessment,
            )
        return ParsedAnalytics(
            rows=_build_dict_rows(timestamps, data),
            more=more,
            schema_state=assessment.state,
            assessment=assessment,
        )

    if isinstance(data, list):
        # list-of-buckets shape (OI / positioning / liquidation-volume);
        # an empty `data` + empty `timestamp` is a valid EMPTY_VALID response.
        rows: list[dict[str, Any]] = []
        for i, ts in enumerate(timestamps):
            datum = data[i] if i < len(data) else None
            row: dict[str, Any] = {"timestamp": ts}
            if isinstance(datum, list):
                row["value"] = datum  # native multi-value bucket array
            else:
                row["value"] = datum
            rows.append(row)
        return ParsedAnalytics(
            rows=tuple(rows), more=more, schema_state=SchemaState.KNOWN_SCHEMA
        )

    # data is neither list nor dict -> schema change (unknown)
    return ParsedAnalytics(
        rows=(), more=more, schema_state=SchemaState.UNKNOWN_SCHEMA
    )


def _column_is_short(column: Any, n: int) -> bool:
    """A metric column is short when it is not a list of length >= n.

    Handles both flat metric lists (funding `rate`) and nested side-sub-maps
    (book_metric `ask` / `bid`, where each leaf is a list parallel to ts).
    """
    if isinstance(column, list):
        return len(column) < n
    if isinstance(column, dict):
        return not column or any(
            not isinstance(leaf, list) or len(leaf) < n for leaf in column.values()
        )
    return True


def _column_value(column: Any, i: int) -> Any:
    """Value at bucket `i` of a metric column (list or nested sub-map)."""
    if isinstance(column, list):
        return column[i]
    if isinstance(column, dict):
        return {sub: leaf[i] for sub, leaf in column.items() if isinstance(leaf, list)}
    raise ValueError("unexpected non-list metric column")


def _any_short_column(data: dict[str, Any], timestamps: list[Any]) -> bool:
    """True when any metric column is shorter than the timestamp column."""
    return any(_column_is_short(col, len(timestamps)) for col in data.values())


def _build_dict_rows(
    timestamps: list[Any],
    data: dict[str, Any],
) -> tuple[dict[str, Any], ...]:
    """Build native rows from a dict-of-metrics analytics payload.

    Each row carries the bucket timestamp + one native value per metric
    (nested `ask`/`bid` side-maps for book_metric preserved as-is, native
    values never normalized or defaulted).
    """
    rows: list[dict[str, Any]] = []
    metrics = list(data)
    for i, ts in enumerate(timestamps):
        row: dict[str, Any] = {"timestamp": ts}
        for metric in metrics:
            row[metric] = _column_value(data[metric], i)
        rows.append(row)
    return tuple(rows)