"""Book 6 normalization — the ratified separate ``NormalizationRule`` contract.

Ratified D6M-2 = B: normalization is a **separate first-class contract**, not a
flag on a metric definition and not an untyped transform hidden inside a
methodology. The lineage is therefore structural:

    NATIVE MeasurementObservation
        -> NormalizationRule
        -> NORMALIZED measurement product

    NORMALIZED_WITHOUT_NATIVE_LINEAGE = INVALID

A normalized product may not exist without explicit references to the native
inputs it was derived from, and the references may not be stripped after
construction — the lineage fields are required, immutable, and re-checked at
every use (ratified plan v0.2 §12; D6M packet v0.3 §2).

``PERCENTILE_WITHIN_COHORT`` is absent from ``NormalizationType`` by design: it
was REJECTED as a ranking surface (comparability v0.1 §4; Constitution v0.2
§5.3a) and must not be reintroduced as a convenience enum value.

Book 6 Hardening R1 adds two closures:

- ``validate_native_inputs`` — a rule for metric A may not consume metric B
  measurements merely because their ids exist;
- ``compute_normalized_value`` — the normalized number is RECOMPUTED from the
  declared inputs and the caller's value is compared against it. Before R1 the
  engine authorized any caller-supplied result, so native 10 over denominator 4
  authorized a value of 999.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Final

from pydantic import ConfigDict, Field, model_validator

from .book6_definitions import MeasurementMethodology
from .book6_frozen import Book6FrozenModel

from .book6_grammar import (
    NORMALIZATION_INVALID_FOR,
    MeasurementCategory,
    NormalizationType,
)

if TYPE_CHECKING:  # pragma: no cover - typing only, no runtime cycle
    from .book6_records import MeasurementObservation


class NormalizationRuleError(ValueError):
    """A normalization rule or its product violates the ratified contract."""


class CohortDimension(str, Enum):
    """Axes a cohort may be defined on (comparability v0.1 §5)."""

    ARCHITECTURE_FAMILY = "ARCHITECTURE_FAMILY"
    ECONOMIC_FUNCTION = "ECONOMIC_FUNCTION"
    PROTOCOL_ROLE = "PROTOCOL_ROLE"
    CHAIN_ROLE = "CHAIN_ROLE"
    MATURITY_BAND = "MATURITY_BAND"
    DEPLOYMENT_ENVIRONMENT = "DEPLOYMENT_ENVIRONMENT"
    SECURITY_MODEL = "SECURITY_MODEL"


#: Normalization operations that are cohort-relative and therefore may not be
#: declared without naming the cohort the total is relative to.
COHORT_SCOPED_NORMALIZATIONS: Final[frozenset[NormalizationType]] = frozenset(
    {NormalizationType.SHARE_OF_TOTAL}
)

#: Normalization operations that divide and therefore must name their divisor.
DIVIDING_NORMALIZATIONS: Final[frozenset[NormalizationType]] = frozenset(
    {
        NormalizationType.PER_TIME,
        NormalizationType.PER_USER,
        NormalizationType.PER_TRANSACTION,
        NormalizationType.PER_CAPITAL,
        NormalizationType.PER_VALIDATOR,
        NormalizationType.PER_BLOCK,
        NormalizationType.PER_UNIT_SECURITY,
    }
)

#: R1: ``SHARE_OF_TOTAL`` also divides — by the cohort total — so it must name
#: its divisor measurement explicitly rather than leaving the divisor implicit in
#: the cohort label. Without this, a share's denominator was whatever the caller
#: felt like supplying.
SHARE_OF_TOTAL_DIVIDES: Final[NormalizationType] = NormalizationType.SHARE_OF_TOTAL

#: Normalization operations expressed against a BASE observation rather than a
#: divisor: growth relative to a base, and an index rebased to a base.
BASE_RELATIVE_NORMALIZATIONS: Final[frozenset[NormalizationType]] = frozenset(
    {
        NormalizationType.GROWTH_RATE,
        NormalizationType.INDEX_TO_BASE,
    }
)


class Cohort(Book6FrozenModel):
    """An explicit, versioned set of subjects eligible for comparison.

    "All chains" is never an automatic cohort (comparability v0.1 §5 rule 1):
    a cohort is named, versioned, and part of the comparison methodology. A
    cohort change never rewrites prior comparisons — a superseding cohort is a
    new version (grammar v0.1 §8).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    cohort_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    dimensions: tuple[CohortDimension, ...] = Field(min_length=1)
    member_refs: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _check_members_unique(self) -> "Cohort":
        if len(set(self.member_refs)) != len(self.member_refs):
            raise NormalizationRuleError(
                "a cohort may not list the same subject twice"
            )
        return self

    def contains(self, subject_ref: str) -> bool:
        """Membership is explicit; non-membership is never silent exclusion."""

        return subject_ref in self.member_refs


class NormalizationRule(Book6FrozenModel):
    """The ratified separate normalization contract (D6M-2 = B).

    Every field the ratification bound is present and required where the
    normalization type needs it. ``input_measurement_refs`` is the native
    lineage: a rule without it cannot produce a normalized value.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    normalization_rule_id: str = Field(min_length=1)
    input_metric_definition_ref: str = Field(min_length=1)
    input_measurement_refs: tuple[str, ...] = Field(min_length=1)
    normalization_type: NormalizationType
    transformation: str = Field(min_length=4)
    denominator_ref: str | None = None
    cohort_ref: str | None = None
    methodology_ref: str = Field(min_length=1)
    valid_time: datetime
    version: str = Field(min_length=1)
    output_metric_definition_ref: str = Field(min_length=1)
    #: R1: the base observation a growth rate or index is expressed against.
    #: Required for ``GROWTH_RATE`` and ``INDEX_TO_BASE`` and forbidden for every
    #: other type, so the base can never be an implicit guess.
    base_measurement_ref: str | None = None

    @model_validator(mode="after")
    def _check_type_specific_requirements(self) -> "NormalizationRule":
        if self.normalization_type in COHORT_SCOPED_NORMALIZATIONS:
            if self.cohort_ref is None:
                raise NormalizationRuleError(
                    f"normalization {self.normalization_type.value} is "
                    f"cohort-relative and must declare the cohort it is relative to"
                )
        if self.normalization_type in DIVIDING_NORMALIZATIONS:
            if self.denominator_ref is None:
                raise NormalizationRuleError(
                    f"normalization {self.normalization_type.value} divides and "
                    f"must declare its denominator_ref"
                )
        if self.normalization_type is SHARE_OF_TOTAL_DIVIDES:
            if self.denominator_ref is None:
                raise NormalizationRuleError(
                    "SHARE_OF_TOTAL divides by a cohort total and must declare "
                    "that total as denominator_ref; an implicit divisor makes "
                    "the share unfalsifiable"
                )
        if self.normalization_type in BASE_RELATIVE_NORMALIZATIONS:
            if self.base_measurement_ref is None:
                raise NormalizationRuleError(
                    f"normalization {self.normalization_type.value} is expressed "
                    f"against a base observation and must declare "
                    f"base_measurement_ref"
                )
        elif self.base_measurement_ref is not None:
            raise NormalizationRuleError(
                f"normalization {self.normalization_type.value} is not "
                f"base-relative and may not declare base_measurement_ref"
            )
        return self


class NormalizedMeasurement(Book6FrozenModel):
    """The normalized product, carrying its native lineage (D6M-2 = B).

    The native input references are REQUIRED here as well: a product that cannot
    name what it was derived from is invalid, so lineage cannot be dropped after
    construction.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    normalized_measurement_id: str = Field(min_length=1)
    normalization_rule_id: str = Field(min_length=1)
    native_measurement_refs: tuple[str, ...] = Field(min_length=1)
    normalized_metric_definition_ref: str = Field(min_length=1)
    value: float
    unit: str = Field(min_length=1)
    cohort_ref: str | None = None
    valid_time: datetime


def validate_native_lineage(
    product: NormalizedMeasurement, rule: NormalizationRule
) -> None:
    """Fail closed unless the product's native lineage matches its rule.

    Checked at use, not only at construction, so a forged ``model_copy`` cannot
    strip or re-point lineage and still authorize a normalized value
    (``NORMALIZED_WITHOUT_NATIVE_LINEAGE = INVALID``).
    """

    if product.normalization_rule_id != rule.normalization_rule_id:
        raise NormalizationRuleError(
            f"normalized product {product.normalized_measurement_id} cites rule "
            f"{product.normalization_rule_id}, not {rule.normalization_rule_id}"
        )
    if not product.native_measurement_refs:
        raise NormalizationRuleError(
            "NORMALIZED_WITHOUT_NATIVE_LINEAGE = INVALID: a normalized value may "
            "not exist independently of its native lineage"
        )
    if set(product.native_measurement_refs) != set(rule.input_measurement_refs):
        raise NormalizationRuleError(
            f"normalized product lineage {product.native_measurement_refs} does "
            f"not match rule inputs {rule.input_measurement_refs}"
        )
    if product.normalized_metric_definition_ref != rule.output_metric_definition_ref:
        raise NormalizationRuleError(
            "normalized product output metric definition does not match its rule"
        )


def validate_native_inputs(
    rule: NormalizationRule,
    native_observations: tuple["MeasurementObservation", ...],
) -> None:
    """Fail closed unless every native input actually measures the declared metric.

    R1 (Phase 9): without this, a normalization rule for metric A could consume
    arbitrary metric B measurements merely because their ids existed. The rule's
    ``input_metric_definition_ref`` is a binding constraint, not decoration.
    """

    if not native_observations:
        raise NormalizationRuleError(
            "a normalization rule must resolve its native inputs; lineage that "
            "resolves to nothing is not lineage"
        )
    for observation in native_observations:
        declared = getattr(observation, "metric_definition_ref", None)
        if declared != rule.input_metric_definition_ref:
            raise NormalizationRuleError(
                f"normalization rule {rule.normalization_rule_id} declares input "
                f"metric {rule.input_metric_definition_ref}, but native input "
                f"{getattr(observation, 'measurement_id', '?')} measures "
                f"{declared}; a rule may not normalize a different metric"
            )


def validate_rule_methodology(
    rule: NormalizationRule,
    *,
    input_methodology_identity: str,
    registered_methodology: MeasurementMethodology,
) -> None:
    """Fail closed unless the rule's methodology matches its native inputs.

    R1 (Phase 9): a normalization rule's ``methodology_ref`` must resolve in the
    Book 6 methodology registry, AND that methodology must declare the input
    metric's methodology identity among its ``input_methodology_refs``. A rule
    whose method does not match its inputs is refused rather than silently
    reinterpreting them.
    """

    allowed = registered_methodology.input_methodology_refs
    if input_methodology_identity not in allowed:
        raise NormalizationRuleError(
            f"methodology {registered_methodology.identity} does "
            f"not declare input methodology {input_methodology_identity}; a "
            f"normalization rule may not reinterpret inputs it was not defined "
            f"over"
        )


def compute_normalized_value(
    rule: NormalizationRule,
    *,
    native_value: float,
    divisor_value: float | None = None,
    base_value: float | None = None,
) -> float:
    """Compute the normalized value deterministically from declared inputs.

    R1-D6: before this, the engine authorized whatever ``value`` the caller
    supplied on the ``NormalizedMeasurement``, so native 10 over denominator 4
    (2.5) authorized a caller-supplied 999. Normalization is a deterministic
    function of its declared inputs, so the engine now computes the product
    itself and compares. A caller may not assert a normalized number.

    Denominator doctrine is inherited: a zero divisor yields UNDEFINED, never
    infinity, never zero, never a dropped observation.
    """

    kind = rule.normalization_type
    if kind in DIVIDING_NORMALIZATIONS or kind is SHARE_OF_TOTAL_DIVIDES:
        if divisor_value is None:
            raise NormalizationRuleError(
                f"normalization {kind.value} requires a declared divisor value"
            )
        if divisor_value == 0.0:
            raise NormalizationRuleError(
                f"normalization {kind.value} has an observed-zero divisor; the "
                f"normalized value is UNDEFINED, not zero and not infinity"
            )
        return native_value / divisor_value
    if kind is NormalizationType.GROWTH_RATE:
        if base_value is None:
            raise NormalizationRuleError(
                "GROWTH_RATE requires a declared base observation value"
            )
        if base_value == 0.0:
            raise NormalizationRuleError(
                "GROWTH_RATE has an observed-zero base; growth is UNDEFINED"
            )
        return (native_value - base_value) / base_value
    if kind is NormalizationType.INDEX_TO_BASE:
        if base_value is None:
            raise NormalizationRuleError(
                "INDEX_TO_BASE requires a declared base observation value"
            )
        if base_value == 0.0:
            raise NormalizationRuleError(
                "INDEX_TO_BASE has an observed-zero base; the index is UNDEFINED"
            )
        return native_value / base_value
    raise NormalizationRuleError(  # pragma: no cover - enum is closed
        f"normalization {kind.value} has no deterministic offline computation"
    )


#: R1-D6: a normalized value is verified against a deterministic recomputation
#: from the declared inputs, never accepted as a caller-supplied result.
NORMALIZED_VALUE_IS_RECOMPUTED: Final[bool] = True


def check_normalization_admissibility(
    rule: NormalizationRule, *, input_category: MeasurementCategory
) -> None:
    """Reject a normalization structurally invalid for a metric category.

    Validity is scoped to (metric × cohort × methodology), never assumed global
    (comparability v0.1 §4).
    """

    forbidden = NORMALIZATION_INVALID_FOR.get(input_category, frozenset())
    if rule.normalization_type in forbidden:
        raise NormalizationRuleError(
            f"normalization {rule.normalization_type.value} is structurally "
            f"invalid for a {input_category.value} metric"
        )


def check_windows_comparable(
    current_window_class: str, prior_window_class: str
) -> None:
    """Fail closed on cross-class window comparison (grammar v0.1 §4.2 rule 3).

    A 7-day window is not comparable to a 30-day window without an explicit
    ratified rule; no such rule exists in the accepted kernel.
    """

    if current_window_class != prior_window_class:
        raise NormalizationRuleError(
            f"window class {current_window_class} is not comparable to "
            f"{prior_window_class} without a ratified comparison rule"
        )


#: Canonical invariants asserted by the accepted implementation.
NORMALIZED_WITHOUT_NATIVE_LINEAGE_IS_INVALID: Final[bool] = True
PERCENTILE_NORMALIZATION_IS_REJECTED: Final[bool] = True


__all__ = [
    "BASE_RELATIVE_NORMALIZATIONS",
    "COHORT_SCOPED_NORMALIZATIONS",
    "Cohort",
    "CohortDimension",
    "compute_normalized_value",
    "DIVIDING_NORMALIZATIONS",
    "NormalizedMeasurement",
    "NORMALIZED_VALUE_IS_RECOMPUTED",
    "NORMALIZED_WITHOUT_NATIVE_LINEAGE_IS_INVALID",
    "NormalizationRule",
    "NormalizationRuleError",
    "PERCENTILE_NORMALIZATION_IS_REJECTED",
    "SHARE_OF_TOTAL_DIVIDES",
    "check_normalization_admissibility",
    "check_windows_comparable",
    "validate_native_inputs",
    "validate_native_lineage",
    "validate_rule_methodology",
]
