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

Book 6 Hardening R1 makes this engine the closure point for all five reported
authority defects:

- **R1-D1 / R1-D5** comparisons resolve the EXACT required methodology identity
  in the Book 6 methodology registry, which must also be authorized for that
  corpus row;
- **R1-D2** a valuation's price must cite Book 2 claims that are current and
  evidenced at authority time;
- **R1-D3** current-valuation authority requires a non-stale price at an
  EXPLICIT ``as_of``, with historical validity preserved separately;
- **R1-D4** ``DATA_COMPLETE`` requires a registry-issued sufficiency
  attestation, re-resolved live here;
- **R1-D6** a normalized value is RECOMPUTED from its declared inputs and a
  caller-supplied number that disagrees is refused.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Final

from .book6_comparability import ComparabilityError, authorize_comparison
from .book6_coverage_rules import CoverageRuleError, CoverageReport
from .book6_grammar import DenominatorState, MeasurementCategory, MissingnessState
from .book6_methodology import MethodologyRegistryError
from .book6_normalization import (
    BASE_RELATIVE_NORMALIZATIONS,
    DIVIDING_NORMALIZATIONS,
    SHARE_OF_TOTAL_DIVIDES,
    NormalizationRuleError,
    NormalizedMeasurement,
    NormalizationRule,
    check_normalization_admissibility,
    compute_normalized_value,
    validate_native_inputs,
    validate_native_lineage,
    validate_rule_methodology,
)
from .book6_predicates import (
    PredicateNotSatisfied,
    PredicateRegistry,
    PredicateRegistryError,
)
from .book6_provenance import Book6Provenance, Book6ProvenanceError
from .book6_records import MeasurementObservation
from .book6_registry import Book6MeasurementRegistry, Book6RegistryError
from .book6_states import (
    FundamentalStateVector,
    StateClass,
    StateDimension,
    StateName,
    StateRule,
    VectorStatus,
    resolve_availability_state,
)
from .book6_valuation import (
    HISTORICAL_BOOK2_AUTHORITY_REPLAY,
    PRICE_AUTHORITY_MATRIX,
    HistoricalAuthorityReport,
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
        #: R2-D2: canonical predicates. Ships with zero ratified predicates.
        self.predicates = PredicateRegistry()

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

        R1 adds four more closures, each re-validated live rather than trusted
        from the supplied objects:

        - the rule's ``methodology_ref`` must resolve in the methodology
          registry, and must declare the input metric's methodology identity
          among its inputs;
        - every native input must actually measure the declared input metric;
        - the product's unit must match its output metric definition;
        - the product's value is RECOMPUTED from the declared inputs and a
          caller-supplied number that disagrees is refused.
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

        native_observations: list[MeasurementObservation] = []
        for native_ref in registered.input_measurement_refs:
            try:
                native_observations.append(self.registry.resolve_current(native_ref))
            except Book6RegistryError as exc:
                raise Book6EngineError(
                    f"normalized product {product.normalized_measurement_id} cites "
                    f"native input {native_ref} with no current authority: {exc}"
                ) from exc

        try:
            validate_native_inputs(registered, tuple(native_observations))
        except NormalizationRuleError as exc:
            raise Book6EngineError(str(exc)) from exc

        try:
            rule_methodology = self.registry.resolve_methodology(
                registered.methodology_ref
            )
        except Book6RegistryError as exc:
            raise Book6EngineError(
                f"normalization rule {registered.normalization_rule_id} names "
                f"methodology {registered.methodology_ref}, which resolves to "
                f"nothing: {exc}"
            ) from exc
        try:
            validate_rule_methodology(
                registered,
                input_methodology_identity=input_definition.methodology.identity,
                registered_methodology=rule_methodology,
            )
        except NormalizationRuleError as exc:
            raise Book6EngineError(str(exc)) from exc

        output_definition = self.registry.definition(
            registered.output_metric_definition_ref
        )
        if product.unit != output_definition.unit:
            raise Book6EngineError(
                f"normalized product unit {product.unit!r} does not match output "
                f"metric {output_definition.metric_id} unit "
                f"{output_definition.unit!r}"
            )

        expected = self._recompute_normalized_value(
            registered, tuple(native_observations)
        )
        if product.value != expected:
            raise Book6EngineError(
                f"normalized product {product.normalized_measurement_id} asserts "
                f"value {product.value}, but the declared "
                f"{registered.normalization_type.value} derivation over its "
                f"native inputs is {expected}; a normalized value is a "
                f"deterministic function of its inputs and may not be asserted"
            )
        return product

    def _recompute_normalized_value(
        self,
        rule: NormalizationRule,
        native_observations: tuple[MeasurementObservation, ...],
    ) -> float:
        """Recompute the normalized value from the rule's declared inputs."""

        native = native_observations[0]
        if native.value is None:
            raise Book6EngineError(
                f"native input {native.measurement_id} carries no observed value "
                f"({native.missingness_state.value}); a normalized value may not "
                f"be derived through missingness"
            )
        kind = rule.normalization_type
        divisor_value: float | None = None
        base_value: float | None = None
        if kind in DIVIDING_NORMALIZATIONS or kind is SHARE_OF_TOTAL_DIVIDES:
            divisor_value = self._required_input_value(rule.denominator_ref, kind)
        elif kind in BASE_RELATIVE_NORMALIZATIONS:
            base_value = self._required_input_value(rule.base_measurement_ref, kind)
        try:
            return compute_normalized_value(
                rule,
                native_value=native.value,
                divisor_value=divisor_value,
                base_value=base_value,
            )
        except NormalizationRuleError as exc:
            raise Book6EngineError(
                f"normalized value for rule {rule.normalization_rule_id} is "
                f"undefined: {exc}"
            ) from exc

    def _required_input_value(self, measurement_ref: str | None, kind: object) -> float:
        """Resolve a declared divisor/base observation to its current value."""

        if measurement_ref is None:
            raise Book6EngineError(f"{kind} requires a declared input observation")
        try:
            observation = self.registry.resolve_current(measurement_ref)
        except Book6RegistryError as exc:
            raise Book6EngineError(
                f"declared input {measurement_ref} has no current authority: {exc}"
            ) from exc
        if observation.value is None:
            raise Book6EngineError(
                f"declared input {measurement_ref} carries no observed value "
                f"({observation.missingness_state.value}); it may not be used as "
                f"a divisor or base"
            )
        return observation.value

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
            methodologies=self.registry.methodologies,
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
        coverage_sufficiency_ratified = (
            self.registry.coverage_rules.is_sufficient(
                metric_id=observation.metric_definition_ref,
                rule_ref=coverage.sufficiency_rule_ref,
            )
            if coverage is not None and coverage.sufficiency_rule_ref is not None
            else False
        )
        return resolve_availability_state(
            has_measurements=observation.is_value_bearing,
            metric_applies=applies,
            rule_ratified=rule_ratified,
            coverage_sufficiency_rule_ratified=coverage_sufficiency_ratified,
        )

    def _check_predicate_window(self, rule: StateRule, window_class: object) -> None:
        """Enforce the rule's declared window-class constraint, live.

        Takes the rule object already returned by ``state_rules.authorize(...)``
        in this same call rather than re-resolving it, so there is exactly one
        authority resolution per emission and no second lookup path.
        """

        constraint = rule.window_class_constraint
        if constraint is None:
            return
        if constraint != getattr(window_class, "value", window_class):
            raise Book6EngineError(
                f"state rule {rule.state_rule_id} constrains its inputs to "
                f"window class {constraint}, but an input declares "
                f"{getattr(window_class, 'value', window_class)}; cross-window "
                f"comparison is not permitted without a ratified rule"
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
        """Emit a Class B or Class C state — only by REPLAYING its ratified rule.

        With ``INDIVIDUAL_STATE_RULES_RATIFIED = 0`` this always refuses, which
        is the intended behaviour: ratification is an operator act, never an
        inference.

        R2-D2 changed what "ratified" is allowed to mean. A ratified rule
        licenses a derivation METHOD; it does not assert the method's OUTCOME.
        Emission requires all four of

            RULE RATIFIED  AND  INPUTS CURRENT  AND  METHODOLOGY CURRENT
              AND  PREDICATE EVALUATES TRUE

        and a predicate that evaluates false produces an explicit
        ``PredicateNotSatisfied`` non-emission. The opposite state is never
        inferred: ``FALSE INCREASING != DECREASING``, because inverting a verdict
        is itself a directional claim requiring its own separately ratified rule.
        """

        rule: StateRule = self.registry.state_rules.authorize(target, rule_ref=rule_ref)
        try:
            self.registry.resolve_methodology(rule.methodology_ref)
        except Book6RegistryError as exc:
            raise Book6EngineError(
                f"state rule {rule_ref} names methodology {rule.methodology_ref}, "
                f"which resolves to nothing: {exc}"
            ) from exc

        if tuple(measurement_refs) != tuple(rule.required_measurement_refs):
            raise Book6EngineError(
                f"state rule {rule_ref} declares its inputs in the fixed order "
                f"{rule.required_measurement_refs}, but emission supplied "
                f"{tuple(measurement_refs)}; operand order belongs to the "
                f"predicate, not to caller convention"
            )

        operands: list[float] = []
        for measurement_ref in measurement_refs:
            observation = self.registry.resolve_current(measurement_ref)
            if observation.value is None:
                raise Book6EngineError(
                    f"state rule {rule_ref} requires {measurement_ref}, which "
                    f"carries no observed value "
                    f"({observation.missingness_state.value}); a predicate may "
                    f"not be evaluated through missingness"
                )
            self._check_predicate_window(rule, observation.window_class)
            operands.append(observation.value)

        try:
            predicate = self.predicates.resolve(rule.predicate_ref)
        except PredicateRegistryError as exc:
            raise Book6EngineError(str(exc)) from exc
        if predicate.target_state is not target:
            raise Book6EngineError(
                f"state rule {rule_ref} targets {target.value} but its predicate "
                f"{predicate.identity} evaluates to "
                f"{predicate.target_state.value}; a rule may not bind another "
                f"state's predicate"
            )
        if predicate.state_class is not rule.state_class:
            raise Book6EngineError(
                f"state rule {rule_ref} declares class {rule.state_class.value} "
                f"but predicate {predicate.identity} is "
                f"{predicate.state_class.value}"
            )
        if predicate.permitted_methodology_refs and (
            rule.methodology_ref not in predicate.permitted_methodology_refs
        ):
            raise Book6EngineError(
                f"predicate {predicate.identity} may only be evaluated under "
                f"{list(predicate.permitted_methodology_refs)}, not "
                f"{rule.methodology_ref}"
            )
        try:
            evaluation = self.predicates.evaluate(rule.predicate_ref, tuple(operands))
        except PredicateRegistryError as exc:
            raise Book6EngineError(str(exc)) from exc
        if not evaluation.result:
            raise PredicateNotSatisfied(
                f"ratified state rule {rule_ref} was replayed over operands "
                f"{evaluation.operands} and its predicate "
                f"{evaluation.predicate_identity} evaluated FALSE; the state "
                f"{target.value} is NOT emitted, and the opposite state is not "
                f"inferred either",
                predicate_id=evaluation.predicate_identity,
                operands=evaluation.operands,
            )
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
        metric_ids = tuple(dimension.dimension_id for dimension in dimensions)
        attestation = self.registry.coverage_rules.attest(metric_ids, at=as_of_valid_time)
        return FundamentalStateVector(
            subject_ref=subject_ref,
            schema_ref=schema_ref,
            as_of_valid_time=as_of_valid_time,
            dimensions=tuple(dimensions),
            coverage_sufficiency_rule_refs=(
                attestation.rule_ids if attestation is not None else ()
            ),
            sufficiency_attestation=attestation,
        )

    # -- valuation seam -------------------------------------------------------

    def authorize_current_valuation(
        self, valuation: ValuationObservation, *, as_of: datetime
    ) -> ValuationObservation:
        """Authorize a valuation as a CURRENT statement at an explicit instant.

        R1-D2 / R1-D3. Four independent requirements, all live:

        1. explicit numeraire — no default, no implicit USD;
        2. Book 2 price authority — the cited price claims must resolve, be
           current and evidenced through ``Book6Provenance``. A ``source_ref``
           string is an attribution, not evidence;
        3. purpose-specific admissibility of the price class (D6M-4 = A);
        4. a non-stale price at ``as_of``.

        ``as_of`` is always passed explicitly; there is no hidden wall clock, so
        a replay at a historical instant is reproducible.

        Book 5 remains frozen: this reads native quantities and never writes a
        numeraire, price or common-value scalar back into a Book 5 record.
        """

        self._validate_valuation_shape(valuation)
        self._require_current_price_authority(valuation)
        if valuation.is_stale_at(as_of):
            raise ValuationError(
                f"valuation {valuation.valuation_id} cites a price observed at "
                f"{valuation.price.observed_at.isoformat()}, which is stale at "
                f"{as_of.isoformat()} under its declared staleness bound of "
                f"{valuation.staleness_bound_seconds}s; a stale price may not "
                f"authorize a current valuation"
            )
        return valuation

    def validate_recorded_historical_shape(
        self, valuation: ValuationObservation
    ) -> ValuationObservation:
        """Validate the RECORDED SHAPE of a historical valuation — nothing more.

        R2-D4 replaced ``validate_historical_valuation``, which shared one helper
        with current authorization and therefore revalidated the price's Book 2
        claims as CURRENT. A price claim that was valid when the valuation was
        observed and later went STALE or SUPERSEDED retroactively erased the
        historical statement — directly contradicting

            CURRENT UNAVAILABLE  !=  HISTORICALLY INVALID

        The audit in Phase 12 settled the honest fix. Accepted Book 2 EXPOSES
        raw history (``ClaimStore.history`` plus timestamped
        ``TransitionEvent``s) but its epistemic predicate
        ``can_promote_to_graph`` is explicitly canonical-CURRENT-only by design:
        it returns ``False`` for any claim version that is not
        ``claim_store.require(id)``. Re-deriving that predicate bitemporally
        inside Book 6 would be inventing a Book 2 feature and would create a
        second epistemic engine, so R2 does not pretend to it.

        This method therefore proves RECORD SHAPE and nothing more:

        - explicit numeraire, non-empty price attribution;
        - purpose/class admissibility (D6M-4 = A);
        - the conversion methodology resolves;
        - the price was NOT already stale at the valuation's own
          ``observed_at``.

        It deliberately does NOT consult Book 2, so it can neither assert nor
        deny historical epistemic backing. Use
        :meth:`historical_authority_status` for that question, which reports
        ``NOT_REPLAYABLE`` honestly.
        """

        self._validate_valuation_shape(valuation)
        if valuation.is_stale_at(valuation.observed_at):
            raise ValuationError(
                f"valuation {valuation.valuation_id} was already stale when it was "
                f"observed at {valuation.observed_at.isoformat()}; it is not a "
                f"valid historical record either"
            )
        return valuation

    def historical_authority_status(
        self, valuation: ValuationObservation
    ) -> HistoricalAuthorityReport:
        """Report, without overclaiming, what can be said about historical authority.

        Deliberately honest about a capability Book 6 does not have. Accepted
        Book 2 cannot answer "was this claim authoritative at time T", so this
        returns ``replay_available = False`` with the audit reason, alongside the
        CURRENT status as a clearly-labelled separate fact.
        """

        current_backed = self.provenance.claim_is_current(
            valuation.price.source_claim_refs[0]
        )
        return HistoricalAuthorityReport(
            valuation_id=valuation.valuation_id,
            replay_capability=HISTORICAL_BOOK2_AUTHORITY_REPLAY,
            replay_unavailable_reason=(
                "accepted Book 2 can_promote_to_graph is canonical-current-only by "
                "design, so Book 6 cannot revalidate a historical claim's "
                "epistemic authority without inventing a Book 2 feature"
            ),
            current_claims_backed=current_backed,
            record_shape_valid=(
                self.validate_recorded_historical_shape(valuation) is valuation
            ),
        )

    def _validate_valuation_shape(self, valuation: ValuationObservation) -> None:
        """The record-shape checks shared by current and historical paths.

        R2-D4: this NEVER consults Book 2. It is everything provable about the
        record itself, independent of any claim's current or historical state.
        Leaving the Book 2 resolution here would have re-introduced exactly the
        defect R2-D4 closes — a shared helper silently making the historical
        path a current-authority path.
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
        try:
            self.registry.resolve_methodology(valuation.conversion_methodology_ref)
        except (Book6RegistryError, MethodologyRegistryError) as exc:
            raise ValuationError(
                f"valuation {valuation.valuation_id} names conversion methodology "
                f"{valuation.conversion_methodology_ref}, which resolves to "
                f"nothing: {exc}"
            ) from exc

    def _require_current_price_authority(
        self, valuation: ValuationObservation
    ) -> None:
        """Book 2 CURRENT authority for the price's cited claims.

        Split out from shape validation precisely so the historical path can
        prove record shape without inheriting a current-only epistemic check.
        """

        try:
            self.provenance.resolve_source_claim_refs(
                valuation.price.source_claim_refs, require_current=True
            )
        except Book6ProvenanceError as exc:
            raise ValuationError(
                f"valuation {valuation.valuation_id} cites price "
                f"{valuation.price.price_observation_id}, which has no current "
                f"Book 2 authority: {exc}; a price source_ref string is an "
                f"attribution, not epistemic evidence"
            ) from exc

    # -- vector data completeness --------------------------------------------

    def data_status(self, vector: FundamentalStateVector) -> VectorStatus:
        """AUTHORITATIVE data-completeness evaluation for a vector.

        R2-D3 replaced R1's check. R1 asked only whether each NAMED rule applied
        to at least one vector metric, so a forged attestation claiming a wider
        scope than the rules actually prove produced ``DATA_COMPLETE`` with a
        metric that no live rule covered.

        Sufficiency is now RECONSTRUCTED from registry state, per metric:

            covered = { m in required : some named rule is registered,
                        currently ratified, and scoped exactly to m }

            DATA_COMPLETE  iff  covered == required

        The comparison is explicit SET EQUALITY, not "each supplied rule covers
        something", so a rule for metric A can never stand in for metric B. The
        attestation is an AUDIT RECORD: it may name the same rules, but it is
        never the source of truth about scope.

        At bootstrap, with zero ratified coverage-sufficiency rules, this is
        ``DATA_INCOMPLETE`` for every vector.
        """

        if not self._derivation_is_complete(vector):
            return VectorStatus.DATA_INCOMPLETE
        required = set(vector.dimension_metric_ids())
        covered: set[str] = set()
        for rule_ref in vector.coverage_sufficiency_rule_refs:
            try:
                rule = self.registry.coverage_rules.registered_rule(rule_ref)
            except CoverageRuleError:
                continue
            for metric_id in required:
                if rule.scope_metric_id != metric_id:
                    continue
                try:
                    self.registry.coverage_rules.authorize(
                        metric_id=metric_id, rule_ref=rule_ref
                    )
                except CoverageRuleError:
                    continue
                covered.add(metric_id)
        return (
            VectorStatus.DATA_COMPLETE
            if covered == required
            else VectorStatus.DATA_INCOMPLETE
        )

    def _derivation_is_complete(self, vector: FundamentalStateVector) -> bool:
        """Whether every dimension carries an observed, applicable derivation."""

        if not vector.dimensions:
            return False
        if vector.schema_status is not VectorStatus.SCHEMA_COMPLETE:
            return False
        return all(
            dimension.missingness
            in (MissingnessState.OBSERVED, MissingnessState.ZERO_OBSERVED)
            and dimension.state_class is not StateClass.DEFERRED_GENERIC
            for dimension in vector.dimensions
        )

    def coverage_report(self, vector: FundamentalStateVector) -> CoverageReport:
        """Which required metrics are covered, which are not, and why.

        A diagnostic view of exactly the set equality ``data_status`` requires,
        so a failing vector says WHICH metric is uncovered instead of only that
        something is.
        """

        required = set(vector.dimension_metric_ids())
        covered: set[str] = set()
        reasons: dict[str, str] = {
            metric: "no named coverage-sufficiency rule covers this metric"
            for metric in required
        }
        for rule_ref in vector.coverage_sufficiency_rule_refs:
            try:
                rule = self.registry.coverage_rules.registered_rule(rule_ref)
            except CoverageRuleError as exc:
                for metric in required:
                    reasons[metric] = str(exc)
                continue
            for metric_id in required:
                if rule.scope_metric_id != metric_id:
                    continue
                try:
                    self.registry.coverage_rules.authorize(
                        metric_id=metric_id, rule_ref=rule_ref
                    )
                except CoverageRuleError as exc:
                    reasons[metric_id] = str(exc)
                    continue
                covered.add(metric_id)
                reasons.pop(metric_id, None)
        return CoverageReport(
            required_metric_ids=tuple(sorted(required)),
            covered_metric_ids=tuple(sorted(covered)),
            uncovered_metric_ids=tuple(sorted(required - covered)),
            status=(
                VectorStatus.DATA_COMPLETE
                if covered == required
                else VectorStatus.DATA_INCOMPLETE
            ),
            reasons=tuple(sorted(reasons.items())),
        )


#: Canonical invariants asserted by the accepted implementation.
MEASUREMENT_IS_NOT_A_BOOK2_CLAIM: Final[bool] = True
NO_SECOND_EPISTEMIC_ENGINE: Final[bool] = True
MISSING_NEVER_DIVIDED_THROUGH: Final[bool] = True
#: R1: no authority-bearing operation runs off a free-string methodology ref.
NO_FREE_STRING_METHODOLOGY_AUTHORITY: Final[bool] = True
#: R1: a normalized value is recomputed from its declared inputs.
NORMALIZED_VALUE_IS_RECOMPUTED: Final[bool] = True


__all__ = [
    "Book6EngineError",
    "Book6MeasurementEngine",
    "ComparabilityError",
    "MEASUREMENT_IS_NOT_A_BOOK2_CLAIM",
    "MISSING_NEVER_DIVIDED_THROUGH",
    "NO_FREE_STRING_METHODOLOGY_AUTHORITY",
    "NO_SECOND_EPISTEMIC_ENGINE",
    "NORMALIZED_VALUE_IS_RECOMPUTED",
    "RatioResult",
    "UndefinedRatio",
]
