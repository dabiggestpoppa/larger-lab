"""Provider-independent schema-drift classification (01 §17 / 03 §14, I04R1).

Every provider parser must distinguish KNOWN / ADDITIVE / BREAKING / UNKNOWN
schema.  Unknown and breaking payloads are archived raw and FAIL CLOSED from
parsed output — a breaking/unknown field must NEVER become `0` / `False` /
`""` / `[]` through default coercion.

This helper is provider-independent: a provider adapter supplies its expected
required native keys vs the keys actually observed, and the classifier returns
a structured decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .enums import SchemaState


@dataclass(frozen=True)
class SchemaAssessment:
    """Schema state + which keys drove the decision (Raw payload preserved)."""

    state: SchemaState
    missing_required: tuple[str, ...] = ()
    extra_additive: tuple[str, ...] = ()
    raw_preserved: bool = True
    semantic_output_allowed: bool = False


def assess_schema(
    expected_required: set[str],
    observed: set[str],
    *,
    semantics_known: bool,
) -> SchemaAssessment:
    """Classify observed keys against the expected required schema.

    - no expected schema defined yet            -> UNKNOWN (cannot parse)
    - a required key is missing                 -> BREAKING (cannot parse)
    - observed is a strict superset             -> ADDITIVE (may parse)
    - observed matches expected                 -> KNOWN (may parse)

    A missing required field is never defaulted to a zero value.
    """
    if not expected_required or not semantics_known:
        return SchemaAssessment(
            state=SchemaState.UNKNOWN_SCHEMA,
            raw_preserved=True,
            semantic_output_allowed=False,
        )

    missing = expected_required - observed
    if missing:
        return SchemaAssessment(
            state=SchemaState.BREAKING_SCHEMA_CHANGE,
            missing_required=tuple(sorted(missing)),
            raw_preserved=True,
            semantic_output_allowed=False,
        )

    extra = observed - expected_required
    if extra:
        return SchemaAssessment(
            state=SchemaState.ADDITIVE_SCHEMA_CHANGE,
            extra_additive=tuple(sorted(extra)),
            raw_preserved=True,
            semantic_output_allowed=True,
        )

    return SchemaAssessment(
        state=SchemaState.KNOWN_SCHEMA,
        raw_preserved=True,
        semantic_output_allowed=True,
    )


def parse_fail_closed(
    assessment: SchemaAssessment,
    row: dict[str, Any],
    required: set[str],
    *,
    parsed_factory: Any,
) -> Any:
    """Return parsed output for KNOWN/ADDITIVE; raise for BREAKING/UNKNOWN.

    `parsed_factory` is the parser callable that builds a parsed/native record
    from the known fields.  It must NEVER be invoked when the schema is
    breaking or unknown — those payloads stay raw and fail closed.
    """
    if assessment.state is SchemaState.BREAKING_SCHEMA_CHANGE:
        raise ValueError(
            f"schema drift (BREAKING): missing required keys "
            f"{assessment.missing_required or tuple(sorted(required - set(row)))}"
        )
    if assessment.state is SchemaState.UNKNOWN_SCHEMA:
        raise ValueError("schema drift (UNKNOWN): cannot parse without a known schema")
    # KNOWN / ADDITIVE: parse from explicit fields (never default missing -> 0)
    return parsed_factory(row)


def assert_no_zero_coercion(
    assessment: SchemaAssessment, row: dict[str, Any], field: str
) -> None:
    """Prove a missing semantic field never coerce-defaults to a zero.

    This is the structural guarantee behind 'no `dict.get(field, 0)`':
    accessing a field that the schema did not provide must raise, not default.
    """
    if assessment.state is SchemaState.KNOWN_SCHEMA and field in row:
        return
    if assessment.state is SchemaState.ADDITIVE_SCHEMA_CHANGE and field in row:
        return
    raise KeyError(
        f"refusing to coerce-default missing/non-atomic field {field!r} "
        "to 0/False/''/[] (schema drift fail-closed)"
    )