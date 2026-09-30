"""Book 6 measurement engine — the offline deterministic measurement kernel.

Book 6 owns measurement DEFINITIONS and descriptive measured state. It measures
OVER accepted truth; it never mints it:

    BOOK 2 = only epistemic engine          BOOK 3 = native architecture truth
    BOOK 4 = dependency truth               BOOK 5 = capital topology truth
    BOOK 6 = measurement definitions + descriptive measured state

Every authority-bearing operation here re-resolves its cited Book 2 authority
live through ``Book6Provenance``. ``MeasurementObservation != Book2 Claim``: this
kernel cannot promote a measurement into a claim, introduce a Book 6 claim state,
or reach past Book 2 to manufacture authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Final

from .book6_comparability import ComparabilityError, authorize_comparison
from .book6_grammar import DenominatorState, MeasurementCategory
from .book6_normalization import (
    NormalizationRuleError,
    NormalizedMeasurement,
    NormalizationRule,
    check_normalization_admissibility,
    validate_native_lineage,
)
from .book6_provenance import Book6Provenance
from .book6_registry import Book6MeasurementRegistry
from .book6_states import (
    FundamentalStateVector,
    StateClass,
    StateDimension,
    StateName,
    StateRule,
    resolve_availability_state,
)
from .book6_valuation import (
    PRICE_AUTHORITY_MATRIX,
    ValuationError,
    ValuationObservation,
)


class Book6EngineError(ValueError):
    """A Book 6 engine operation failed closed."""


class UndefinedRatio(Book6EngineError):
    """A quotient was requested whose denominator forbids it.

    A ratio with an observed-zero denominator is UNDEFINED, not infinity, not
    zero, and not dropped (grammar v0.1 §4.2 rule 2).
    """


@dataclass(frozen=True)
class RatioResult:
    """An explicitly typed quotient result.

    ``is_undefined`` distinguishes "no ratio exists" from any numeric value, so a
    caller cannot read an undefined ratio as 0.0.
    """

    numerator: float
    denominator: float
    ratio: float | None
    denominator_state: DenominatorState
    is_undefined: bool


class Book6MeasurementEngine:
    """Offline deterministic measurement authority.

    The engine is the single place where "may this measurement be used?" is
    answered, so callers cannot bypass live Book 2 revalidation by reaching for
    a structural accessor instead.
    """

    def __init__(self, provenance: Book6Provenance) -> None:
        self.provenance = provenance
        self.registry = Book6MeasurementRegistry(provenance)

    # -- authority-bearing measurement use ----------------------------------

    def current_value(self, measurement_id: str) -> float:
        """Return a measurement's current value, or fail closed.

        This is the only sanctioned way to read a value out of the kernel.
        """

        observation = self.registry.resolve_current(measurement_id)
        if not observation.is_value_bearing or observation.value is None:
            raise Book6EngineError(
                f"measurement {measurement_id} carries no observed value "
                f"({observation.missingness_state.value}); absence is not zero"
            )
        return observation.value

    def current_unit(self, measurement_id: str) -> str:
        observation = self.registry.resolve_current(measurement_id)
        if observation.unit is None:
            raise Book6EngineError(
                f"measurement {measurement_id} carries no unit; a value never "
                f"carries an implicit unit"
            )
        return observation.unit

    # -- ratio arithmetic (denominator doctrine) -----------------------------

    def compute_ratio(self, measurement_id: str) -> RatioResult:
        """Compute a ratio with explicit denominator semantics, fail closed.

        Never divides through missingness or through zero; an observed-zero or
        absent denominator yields ``is_undefined=True`` and ``ratio=None``.
        """

        observation = self.registry.resolve_current(measurement_id)
        denominator = observation.denominator
        if observation.category is not MeasurementCategory.RATIO or denominator is None:
            raise Book6EngineError(
                f"measurement {measurement_id} is not a ratio with a declared "
                f"denominator"
            )
        if not observation.is_value_bearing or observation.value is None:
            raise Book6EngineError(
                f"ratio {measurement_id} has no observed numerator "
                f"({observation.missingness_state.value})"
            )
        state = DenominatorState(denominator.state)
        if state is not DenominatorState.PRESENT or denominator.value is None:
            return RatioResult(
                numerator=observation.value,
                denominator=float("nan"),
                ratio=None,
                denominator_state=state,
                is_undefined=True,
            )
        if denominator.value == 0.0:
            return RatioResult(
                numerator=observation.value,
                denominator=0.0,
                ratio=None,
                denominator_state=DenominatorState.ZERO,
                is_undefined=True,
            )
        return RatioResult(
            numerator=observation.value,
            denominator=denominator.value,
            ratio=observation.value / denominator.value,
            denominator_state=DenominatorState.PRESENT,
            is_undefined=False,
        )

    # -- normalization (D6M-2 = B, separate contract) -----------------------

    def normalize(
        self, product: NormalizedMeasurement, rule: NormalizationRule
    ) -> NormalizedMeasurement:
        """Authorize a normalized product by live native-lineage validation.

        Lineage is re-checked at use, so a forged copy that stripped or re-pointed
        native references cannot authorize a normalized value
        (``NORMALIZED_WITHOUT_NATIVE_LINEAGE = INVALID``).
        """

        registered = self.registry.normalized_rule(rule.normalization_rule_id)
        if registered.normalization_rule_id != rule.normalization_rule_id:
            raise Book6EngineError("normalization rule identity mismatch")
        input_definition = self.registry.definition(registered.input_metric_definition_ref)
        try:
            check_normalization_admissibility(
                registered, input_category=input_definition.category
            )
            validate_native_lineage(product, registered)
        except NormalizationRuleError as exc:
            raise Book6EngineError(
                f"normalized product {product.normalized_measurement_id} is not "
                f"authorized: {exc}"
            ) from exc
        for native_ref in registered.input_measurement_refs:
            self.registry.resolve_current(native_ref)
        return product

    # -- comparability gate ---------------------------------------------------

    def authorize_comparison(
        self,
        left_metric_id: str,
        right_metric_id: str,
        *,
        methodology_ref: str | None,
    ) -> str:
        """Authorize a metric comparison through the encoded corpus gate."""

        left_class = self.registry.definition(left_metric_id).comparability_class
        right_class = self.registry.definition(right_metric_id).comparability_class
        return authorize_comparison(
            left_metric_id,
            right_metric_id,
            methodology_ref=methodology_ref,
            left_class=left_class,
            right_class=right_class,
        )

    # -- state derivation -----------------------------------------------------

    def availability_state(self, measurement_id: str) -> StateName:
        """Resolve the Class A availability state for a dimension.

        Class A states are decidable structurally and are the only states this
        implementation can emit, because zero StateRules are ratified.
        """

        observation = self.registry.registered_measurement(measurement_id)
        definition = self.registry.definition(observation.metric_definition_ref)
        family = observation.architecture_family
        applies = True if family is None else definition.applies_to(family)
        rule_ratified = False
        coverage = self.registry.coverage_of(measurement_id)
        return resolve_availability_state(
            has_measurements=observation.is_value_bearing,
            metric_applies=applies,
            rule_ratified=rule_ratified,
            coverage_sufficiency_rule_ratified=(
                coverage.sufficiency_known if coverage is not None else False
            ),
        )

    def emit_rule_gated_state(
        self,
        target: StateName,
        *,
        rule_ref: str,
        dimension_id: str,
        measurement_refs: tuple[str, ...],
        methodology_ref: str,
        valid_time: datetime,
        observed_at: datetime,
        missingness,
        coverage_observation_id: str | None = None,
        sensitivity_note: str | None = None,
    ) -> StateDimension:
        """Emit a Class B or Class C state — only with an individually ratified rule.

        With ``INDIVIDUAL_STATE_RULES_RATIFIED = 0`` this always refuses, which
        is the intended behaviour: ratification is an operator act, never an
        inference.
        """

        rule: StateRule = self.registry.state_rules.authorize(target, rule_ref=rule_ref)
        for measurement_ref in measurement_refs:
            self.registry.resolve_current(measurement_ref)
        return StateDimension(
            dimension_id=dimension_id,
            state=target,
            state_class=rule.state_class,
            measurement_refs=measurement_refs,
            state_rule_ref=rule_ref,
            methodology_ref=methodology_ref,
            valid_time=valid_time,
            observed_at=observed_at,
            missingness=missingness,
            coverage_observation_id=coverage_observation_id,
            sensitivity_note=sensitivity_note,
        )

    def build_availability_vector(
        self,
        *,
        subject_ref: str,
        schema_ref: str,
        as_of_valid_time: datetime,
        observed_at: datetime,
        measurement_ids: tuple[str, ...],
        methodology_ref: str,
    ) -> FundamentalStateVector:
        """Build a descriptive vector from Class A availability states only.

        No score, total, rank or quality field exists on the result; the vector
        carries structural schema/data status only.
        """

        dimensions: list[StateDimension] = []
        for measurement_id in measurement_ids:
            observation = self.registry.registered_measurement(measurement_id)
            state = self.availability_state(measurement_id)
            dimensions.append(
                StateDimension(
                    dimension_id=observation.metric_definition_ref,
                    state=state,
                    state_class=StateClass.A_AVAILABILITY,
                    measurement_refs=(measurement_id,),
                    state_rule_ref=None,
                    methodology_ref=methodology_ref,
                    valid_time=as_of_valid_time,
                    observed_at=observed_at,
                    missingness=observation.missingness_state,
                    coverage_observation_id=measurement_id,
                )
            )
        return FundamentalStateVector(
            subject_ref=subject_ref,
            schema_ref=schema_ref,
            as_of_valid_time=as_of_valid_time,
            dimensions=tuple(dimensions),
        )

    # -- valuation seam -------------------------------------------------------

    def authorize_valuation(self, valuation: ValuationObservation) -> ValuationObservation:
        """Authorize a valuation product against purpose-specific price authority.

        Book 5 remains frozen: this reads native quantities and never writes a
        numeraire, price or common-value scalar back into a Book 5 record.
        """

        if not valuation.numeraire:
            raise ValuationError(
                "a valuation requires an explicit numeraire at use: there is no "
                "default and no implicit USD"
            )
        if not valuation.price.source_ref:
            raise ValuationError(
                "a valuation requires a cited price source; an unattributed "
                "price carries no authority"
            )
        admissible = PRICE_AUTHORITY_MATRIX[valuation.purpose]
        if valuation.price.price_class not in admissible:
            raise ValuationError(
                f"price class {valuation.price.price_class.value} is not "
                f"admissible for purpose {valuation.purpose.value}"
            )
        return valuation


#: Canonical invariants asserted by the accepted implementation.
MEASUREMENT_IS_NOT_A_BOOK2_CLAIM: Final[bool] = True
NO_SECOND_EPISTEMIC_ENGINE: Final[bool] = True
MISSING_NEVER_DIVIDED_THROUGH: Final[bool] = True


__all__ = [
    "Book6EngineError",
    "Book6MeasurementEngine",
    "ComparabilityError",
    "MEASUREMENT_IS_NOT_A_BOOK2_CLAIM",
    "MISSING_NEVER_DIVIDED_THROUGH",
    "NO_SECOND_EPISTEMIC_ENGINE",
    "RatioResult",
    "UndefinedRatio",
]
