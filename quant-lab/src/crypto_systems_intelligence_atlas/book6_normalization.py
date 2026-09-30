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
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Final

from pydantic import ConfigDict, Field, model_validator

from .book6_frozen import Book6FrozenModel

from .book6_grammar import (
    NORMALIZATION_INVALID_FOR,
    MeasurementCategory,
    NormalizationType,
)


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
    "COHORT_SCOPED_NORMALIZATIONS",
    "Cohort",
    "CohortDimension",
    "DIVIDING_NORMALIZATIONS",
    "NormalizedMeasurement",
    "NORMALIZED_WITHOUT_NATIVE_LINEAGE_IS_INVALID",
    "NormalizationRule",
    "NormalizationRuleError",
    "PERCENTILE_NORMALIZATION_IS_REJECTED",
    "check_normalization_admissibility",
    "check_windows_comparable",
    "validate_native_lineage",
]
