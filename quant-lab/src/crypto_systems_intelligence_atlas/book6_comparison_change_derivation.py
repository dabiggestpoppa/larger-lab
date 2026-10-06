"""Book 6 change derivation — RUNG 8 (deterministic ChangeObservation arithmetic).

This rung produces the one thing every earlier rung prepared: an authoritative
:class:`ChangeObservation` carrying derived, never caller-authored, deltas.

**The operand law is the point of the module.** Per
``BOOK6-COMPARISON-OPERAND-CARDINALITY-v0.1``
(``RATIFY_ONE_COMPARISON_MEASUREMENT_PER_CHANGEOBSERVATION``):

    ONE_CHANGEOBSERVATION_ONE_COMPARISON_MEASUREMENT = TRUE

One ``ChangeObservation`` describes ONE comparison ``MeasurementObservation``
against ONE selected baseline ``MeasurementObservation``. There is no
comparison-side selector, no tie-break, no reducer, and no aggregation, because
there is nothing for one to operate on: the engine receives exactly one
comparison observation or it refuses. ``comparison_measurement_refs`` is not a
parameter at all — the engine stamps it from the one observation it received —
so a caller cannot assert a plural comparison set, and no code path exists that
could pick first, pick last, sort lexically, average, sum, select by time,
select by coverage, or select by caller order.

The refusal is enforced at **this** derivation layer, not as a schema rewrite.
``ChangeObservation.comparison_measurement_refs`` keeps its ratified
``tuple[str, ...]`` shape with ``min_length=1`` for schema continuity and
historical compatibility; adding a model validator that demanded ``len == 1``
would retroactively change what historical records can exist — records the
schema has always permitted — which the ratification explicitly does not
authorize. This module is the only authoritative production path for change
arithmetic, so the executable-cardinality restriction lives here, where it
gates exactly the records this amendment produces.

**Caller authority.** ``derive_change_observation`` has no parameter that could
carry a caller-authored ``absolute_delta``, ``relative_delta``, or
``change_kind`` — not an ignored one, none at all. The engine derives all
three from the stored operand values, and the selected baseline identity it
writes is the Rung 6 selector's already-resolved result.

**The engine consumes, never recomputes, Rung 7.** Coverage and comparability
arrive as an already-derived :class:`ComparabilityVerdict` — check 19's own
result, sealed by the rung that owns it. Replaying coverage here would create a
second, parallel coverage authority and could disagree with the verdict the
corpus already recorded. The engine reads the replayed checks out of the frozen
verdict and refuses to *assert* a comparability it was not handed: a caller
cannot write ``COMPARABLE`` into the record while passing a verdict that says
otherwise, because the record's ``comparability_status`` **is** the verdict's
status field.

Under Rung 7's own law, ``COMPARABLE`` is reachable only when the sealed
coverage replay recomputed ``SUFFICIENT`` under a live, ratified, in-scope rule
(anything less maps to ``UNRESOLVED`` or ``NOT_COMPARABLE``). The engine
enforces that equivalence instead of trusting it: a ``COMPARABLE`` verdict
whose check 16 did not recompute ``SUFFICIENT`` is refused, and the record's
coverage fields are the sealed replay's answer, never a recomputation.

**Stored binary64 arithmetic, exactly as ratified.** ``absolute_delta`` is one
IEEE-754 subtraction of stored values, ``relative_delta`` one division. No
epsilon, no tolerance, no ``isclose``, no ``Decimal``, no ``Fraction``, no
rounding anywhere. Direction comes from the sign of the canonical UNROUNDED
stored absolute delta: ``> 0 -> INCREASE``, ``< 0 -> DECREASE``, ``== 0.0 ->
NO_CHANGE``. IEEE-754 equality is total over the zeros — ``+0.0 == -0.0`` is
true — so both signed zeros are ``NO_CHANGE``, exactly as the law requires.

**The zero-baseline law.** When the selected baseline's stored value is exactly
``0.0`` the absolute delta still computes (``c - 0.0 == c`` for finite ``c``),
but the relative delta is **undefined**: it is ``None``, and the record's
``change_kind`` is ``CHANGE_UNDEFINED`` whenever the relative delta is the
operative requested delta. It is never ``0``, ``inf``, ``NaN``, a capped
value, a percentage, or any other sentinel — those would each smuggle a policy
into the denominator of a fraction that has no value there.

**Non-finite operands never reach arithmetic.** ``NaN``, ``+Inf`` and ``-Inf``
in either stored operand fail closed before the subtraction: the engine raises
and no non-finite delta can ever be persisted. (The ``ChangeObservation``
contract independently refuses non-finite stored deltas; this firewall keeps
them from being *derived* at all, which is earlier and cheaper than refusal at
construction.)

**Currentness is re-resolved live, on both operands.** Registration is not
authority. At derivation time the engine resolves each operand through the
accepted :class:`Book6MeasurementRegistry` resolver — the GAP-7 currentness
authority — and refuses anything that is not current *now*. It checks the
comparison observation too, not only the baseline: a comparison whose lineage
has been superseded is exactly as dead as a superseded baseline, and Rung 6's
candidate-side check is not this check. The comparison rule's own authority is
re-checked live through :class:`ComparisonRuleRegistry` at the same moment.

**Structural identity is re-checked here, fail closed.** Same metric
definition and same exact unit — no conversion — between the two resolved
operands. A unitless operand is not an arithmetic value this engine may
compare. These gates raise rather than downgrade: a record they would produce
has no honest arithmetic to carry.

**Refusals the sealed verdict already decided become records.** When the
sealed Rung 7 verdict is ``NOT_COMPARABLE`` or ``UNRESOLVED``, no arithmetic
runs and no baseline resolution is asserted: the engine writes the refusal
record carrying the verdict's own decision, its own producing checks as
refusal reasons, and ``selected_baseline_measurement_ref = None`` — which the
contract's presence law requires, because absence of a selected baseline means
BASELINE_UNAVAILABLE and nothing else. Structural faults the engine detects
itself (non-current operands, identity mismatches, non-finite values) raise
:class:`ChangeDerivationError` instead; they are faults in the inputs to
derivation, not decisions the sealed replay made.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final

from .book6_comparison_contracts import (
    ChangeKind,
    ChangeObservation,
    ComparisonRule,
    CoverageObservationState,
    CoverageRequirementStatus,
    CoverageVerdict,
    DeltaOperator,
    TemporalComparabilityStatus,
)
from .book6_comparison_coverage import ComparabilityVerdict, ReplayCheck
from .book6_comparison_registry import (
    ComparisonRuleRegistry,
    baseline_selector_fingerprint,
    comparison_rule_fingerprint,
)
from .book6_records import MeasurementObservation
from .book6_registry import Book6MeasurementRegistry


class ChangeDerivationError(ValueError):
    """A ChangeObservation could not be derived under the ratified laws."""


#: The executable-cardinality refusal reason. A named constant because it is a
#: law the tests assert on verbatim, not a message string that may drift.
MULTI_COMPARISON_MEASUREMENT_SET_NOT_AUTHORIZED: Final[str] = (
    "MULTI_COMPARISON_MEASUREMENT_SET_NOT_AUTHORIZED"
)

#: The one count an authoritative comparison set may have.
AUTHORITATIVE_COMPARISON_MEASUREMENT_COUNT: Final[int] = 1

#: The refusal reason for a non-current operand at derivation time.
OPERAND_NOT_CURRENT: Final[str] = "operand is not current at derivation time"

#: The refusal reason for an operand that does not carry a finite stored value.
OPERAND_NOT_FINITE_VALUE_BEARING: Final[str] = (
    "operand does not carry a finite stored binary64 value"
)

#: The sealed-replay reason fragment Rung 7 writes when check 16 recomputed a
#: verdict. The engine consumes these recordings; it never recomputes them.
_SUFFICIENT_RECORDING: Final[str] = "-> SUFFICIENT"
_INSUFFICIENT_RECORDING: Final[str] = "-> INSUFFICIENT"

#: The sealed-replay reason fragment Rung 7 writes when coverage applicability
#: resolved to REQUIRED for the exact metric.
_REQUIRED_RECORDING: Final[str] = "coverage is REQUIRED"


@dataclass(frozen=True)
class DerivedChange:
    """The arithmetic result, before it becomes a ``ChangeObservation``.

    A value object, not an authority-bearing contract. The engine, not the
    caller, owns every field here.
    """

    absolute_delta: float
    relative_delta: float | None
    change_kind: ChangeKind


@dataclass(frozen=True)
class SealedCoverage:
    """The coverage facts the sealed Rung 7 result carries for one record.

    Read out of the frozen :class:`ComparabilityVerdict` — never recomputed.
    ``required`` and ``verdict`` are the replay's own answers; ``state`` is
    the R-3 discriminator derived from them.
    """

    required: bool
    verdict: CoverageVerdict
    state: CoverageObservationState


def _validate_operand_cardinality(
    comparison_measurement_refs: tuple[str, ...],
) -> None:
    """Fail closed unless the comparison set has exactly one member.

    This is the executable-cardinality firewall of
    ``BOOK6-COMPARISON-OPERAND-CARDINALITY-v0.1``. The engine receives the
    comparison set only as it stamps it — one ref, from the one observation —
    so this check runs on every authoritative production path, before any
    operand is examined or used. A set of any size other than one is refused
    as a set: there is no comparison-side selector, tie-break, reducer or
    aggregation to reduce it with, and none may be invented. The empty set is
    refused here in the same terms, so even a Python caller bypassing the
    contract's ``min_length=1`` can never reach arithmetic with zero operands.
    """

    count = len(comparison_measurement_refs)
    if count != AUTHORITATIVE_COMPARISON_MEASUREMENT_COUNT:
        raise ChangeDerivationError(
            f"{MULTI_COMPARISON_MEASUREMENT_SET_NOT_AUTHORIZED}: an authoritative "
            f"ChangeObservation carries exactly one comparison measurement ref "
            f"(requested {count}); there is no comparison-side selector, "
            f"tie-break, reducer or aggregation to reduce a set with, and none "
            f"may be invented"
        )


def _resolve_operand(
    registry: Book6MeasurementRegistry,
    measurement_ref: str,
    *,
    role: str,
) -> MeasurementObservation:
    """Resolve one arithmetic operand as current, or fail closed.

    Uses the accepted GAP-7 resolver — registered lookup, lineage validity,
    terminality, structural validation, source authority, live claim
    resolution — never a plain store read. A superseded or unregistered
    operand is not a value; it is an absence of authority, whatever its
    stored ``value`` field says.
    """

    try:
        return registry.resolve_current(measurement_ref)
    except Exception as exc:  # noqa: BLE001 - resolver refusal is fail-closed
        raise ChangeDerivationError(
            f"{role} measurement {measurement_ref} is not current at derivation "
            f"time ({OPERAND_NOT_CURRENT}): {exc}"
        ) from exc


def _derive_direction(absolute_delta: float) -> ChangeKind:
    """Direction from the sign of the canonical UNROUNDED stored delta.

    ``> 0 -> INCREASE``, ``< 0 -> DECREASE``, ``== 0.0 -> NO_CHANGE``. IEEE-754
    equality is total over the zeros: ``+0.0 == -0.0`` compares equal, so both
    signed zeros are ``NO_CHANGE`` without a single extra branch — and that is
    the ratified law, not an implementation shortcut.
    """

    if absolute_delta > 0.0:
        return ChangeKind.INCREASE
    if absolute_delta < 0.0:
        return ChangeKind.DECREASE
    return ChangeKind.NO_CHANGE


def _derive_deltas(
    *,
    comparison_value: float,
    baseline_value: float,
    delta_operator: DeltaOperator,
) -> DerivedChange:
    """The ratified arithmetic, exactly once, from exactly two stored values.

    Stored binary64 throughout: one subtraction, at most one division. No
    epsilon, no tolerance, no ``isclose``, no ``Decimal``, no ``Fraction``, no
    rounding. Direction derives from the sign of the canonical UNROUNDED
    absolute delta — never from a rounded, displayed or relative magnitude.
    """

    absolute_delta: float = comparison_value - baseline_value

    if delta_operator is DeltaOperator.RELATIVE_DELTA:
        if baseline_value == 0.0:
            # The zero-baseline law. relative_delta is UNDEFINED: None on the
            # record, never 0, inf, NaN, capped, or a percentage. The kind
            # says why the relative delta is absent.
            return DerivedChange(
                absolute_delta=absolute_delta,
                relative_delta=None,
                change_kind=ChangeKind.CHANGE_UNDEFINED,
            )
        relative_delta: float | None = (
            (comparison_value - baseline_value) / baseline_value
        )
    else:
        relative_delta = None

    return DerivedChange(
        absolute_delta=absolute_delta,
        relative_delta=relative_delta,
        change_kind=_derive_direction(absolute_delta),
    )


def _sealed_coverage(comparability: ComparabilityVerdict) -> SealedCoverage:
    """Read the coverage facts the sealed Rung 7 result already carries.

    Check 12's recorded reason says whether applicability resolved to
    REQUIRED; check 16's recorded reason says what verdict the ratified rule
    produced — ``-> SUFFICIENT`` or ``-> INSUFFICIENT`` — when a
    determination was reached at all. A failed check 16 means no verdict was
    claimed, which is ``UNKNOWN``: an absence of basis, never a recomputed
    finding. Nothing here replays or recomputes anything; the recordings are
    the rung's own sealed output.
    """

    check_12 = _check_of(comparability, 12)
    check_16 = _check_of(comparability, 16)

    required = _REQUIRED_RECORDING in check_12.reason

    if check_16.passed and _SUFFICIENT_RECORDING in check_16.reason:
        verdict = CoverageVerdict.SUFFICIENT
    elif check_16.passed and _INSUFFICIENT_RECORDING in check_16.reason:
        verdict = CoverageVerdict.INSUFFICIENT
    else:
        verdict = CoverageVerdict.UNKNOWN

    if not required:
        state = CoverageObservationState.NOT_APPLICABLE
    elif verdict is CoverageVerdict.UNKNOWN:
        state = CoverageObservationState.UNAVAILABLE
    else:
        state = CoverageObservationState.PRESENT

    return SealedCoverage(required=required, verdict=verdict, state=state)


def _check_of(comparability: ComparabilityVerdict, number: int) -> ReplayCheck:
    """One replayed check from the sealed result, or fail closed.

    A sealed result that does not carry the checks it claims to seal cannot be
    consumed; guessing would be recomputation by another name.
    """

    check = next(
        (c for c in comparability.coverage_checks if c.number == number), None
    )
    if check is None:
        raise ChangeDerivationError(
            f"the sealed Rung 7 result carries no check {number}; a coverage "
            f"fact cannot be consumed without the replay that produced it"
        )
    return check


def _refusal_reasons(
    comparability: ComparabilityVerdict,
) -> tuple[tuple[str, str], ...]:
    """The producing checks behind a non-COMPARABLE verdict, as record rows.

    GAP-4 requires a refusal to name its gates. Every failed check the sealed
    verdict carries is a producer: structural failures first (they are
    decisions), then the coverage replay, then check 19 itself — which is
    always failed on a non-COMPARABLE verdict, so the tuple is never empty and
    the contract's producing-gate law is satisfiable by construction.
    """

    failed: list[ReplayCheck] = [
        c for c in comparability.structural_failures if c.failed
    ]
    failed.extend(c for c in comparability.coverage_checks if c.failed)
    if comparability.check_19.failed:
        failed.append(comparability.check_19)
    reasons = tuple((f"check:{c.number}", c.reason) for c in failed)
    if not reasons:  # pragma: no cover - check_19 guarantees non-empty
        raise ChangeDerivationError(
            "a non-COMPARABLE verdict must name at least one producing gate"
        )
    return reasons


def derive_change_observation(
    *,
    comparison: MeasurementObservation,
    baseline_measurement_refs: tuple[str, ...],
    selected_baseline_ref: str | None,
    rule: ComparisonRule,
    registry: Book6MeasurementRegistry,
    comparison_rules_registry: ComparisonRuleRegistry,
    comparability: ComparabilityVerdict,
    change_observation_id: str,
    derivation_binding_ref: str,
) -> ChangeObservation:
    """Derive one authoritative ``ChangeObservation`` from sealed rung results.

    Parameters the caller may not supply, on purpose, because the engine owns
    them: ``absolute_delta``, ``relative_delta``, ``change_kind``,
    ``comparison_measurement_refs`` (stamped from ``comparison``), the record's
    ``selected_baseline_measurement_ref`` (``selected_baseline_ref`` is the
    Rung 6 selector's resolved result and becomes an operand only through the
    engine's own live resolution), and ``comparison_rule_fingerprint`` (derived
    from the rule's canonical content; a fingerprint is content, not an
    assertion). The signature has no parameter that could carry any of them.

    The engine consumes the sealed Rung 7 ``ComparabilityVerdict`` — check 19's
    own result. It never replays coverage, never recomputes a verdict, and
    never lets a caller assert a comparability the verdict does not carry.
    """

    if rule is None:  # pragma: no cover - typed signature forbids it
        raise ChangeDerivationError("a resolved ComparisonRule is required")

    # -- 1. the operand law, before anything else --------------------------
    comparison_refs: tuple[str, ...] = (comparison.measurement_id,)
    _validate_operand_cardinality(comparison_refs)

    # -- 2. the sealed Rung 7 decision is the only comparability input -----
    status = comparability.status

    if status is not TemporalComparabilityStatus.COMPARABLE:
        # No arithmetic runs on an unresolved or refused comparison. The
        # record carries the verdict's own decision, its own reasons, and no
        # baseline resolution — and no operands are resolved, because a
        # refusal record must not depend on operand state the refusal
        # already supersedes.
        if not baseline_measurement_refs:
            raise ChangeDerivationError(
                "the contract requires at least one baseline candidate ref on "
                "the record even for a refusal; an empty candidate set cannot "
                "be recorded (record the refusal through the selector's own "
                "exclusions instead)"
            )
        sealed = _sealed_coverage(comparability)
        _require_declared_and_sealed_agree(rule, sealed)
        return ChangeObservation(
            change_observation_id=change_observation_id,
            subject_ref=comparison.subject_ref,
            valid_time=comparison.valid_time,
            metric_definition_ref=comparison.metric_definition_ref,
            metric_definition_semantic_fingerprint=(
                rule.metric_definition_semantic_fingerprint
            ),
            comparison_rule_ref=rule.comparison_rule_id,
            comparison_rule_version=rule.version,
            comparison_rule_fingerprint=comparison_rule_fingerprint(rule),
            derivation_binding_ref=derivation_binding_ref,
            baseline_selector_spec_fingerprint=(
                baseline_selector_fingerprint(rule.baseline_selector)
            ),
            baseline_measurement_refs=baseline_measurement_refs,
            comparison_measurement_refs=comparison_refs,
            selected_baseline_measurement_ref=None,
            absolute_delta=None,
            relative_delta=None,
            delta_operator=rule.delta_operator,
            change_kind=(
                ChangeKind.NOT_COMPARABLE
                if status is TemporalComparabilityStatus.NOT_COMPARABLE
                else ChangeKind.INSUFFICIENT_DATA
            ),
            unit=comparison.unit or "unknown",
            source_measurement_refs=(comparison.measurement_id,),
            measurement_methodology_refs=(comparison.methodology_identity,),
            coverage_requirement_status=rule.coverage_requirement_status,
            coverage_applicability_source_ref=(
                rule.coverage_applicability_source_ref if sealed.required else None
            ),
            coverage_observation_state=sealed.state,
            coverage_observation_ref=(
                comparison.coverage_observation_id
                if sealed.state is CoverageObservationState.PRESENT
                else None
            ),
            coverage_verdict=sealed.verdict,
            missingness=comparison.missingness_state.value,
            comparability_status=status,
            comparability_refusal_reasons=_refusal_reasons(comparability),
            display_metadata={},
        )

    # -- 3. the sealed replay and the governing rule must agree, and
    #       COMPARABLE requires the sealed replay to have recomputed a
    #       SUFFICIENT verdict; the engine enforces both instead of
    #       trusting either -------------------------------------------------
    sealed = _sealed_coverage(comparability)
    _require_declared_and_sealed_agree(rule, sealed)
    if sealed.verdict is not CoverageVerdict.SUFFICIENT:
        raise ChangeDerivationError(
            "comparability is COMPARABLE but the sealed Rung 7 replay did not "
            "recompute SUFFICIENT coverage; the engine consumes the sealed "
            "result and will not perform arithmetic that contradicts it"
        )

    # -- 4. live currentness of BOTH operands ------------------------------
    if selected_baseline_ref is None:
        raise ChangeDerivationError(
            "COMPARABLE arithmetic requires a selected baseline; None means "
            "BASELINE_UNAVAILABLE and no arithmetic can run"
        )
    comparison_current = _resolve_operand(
        registry, comparison.measurement_id, role="comparison"
    )
    baseline_current = _resolve_operand(
        registry, selected_baseline_ref, role="baseline"
    )

    # -- 5. same metric definition, same exact unit ------------------------
    if (
        baseline_current.metric_definition_ref
        != comparison_current.metric_definition_ref
    ):
        raise ChangeDerivationError(
            f"baseline {baseline_current.measurement_id} measures "
            f"{baseline_current.metric_definition_ref}, comparison measures "
            f"{comparison_current.metric_definition_ref}; same-metric exact-unit "
            f"identity forbids cross-metric arithmetic and no conversion exists"
        )
    if baseline_current.unit != comparison_current.unit:
        raise ChangeDerivationError(
            f"baseline unit {baseline_current.unit!r} != comparison unit "
            f"{comparison_current.unit!r}; exact-unit identity forbids the "
            f"comparison and no unit conversion exists"
        )
    if baseline_current.unit is None or comparison_current.unit is None:
        # Unreachable through the != guard above unless both are None, which
        # is exactly the unitless case this branch exists to refuse.
        raise ChangeDerivationError(
            "both operands must carry an exact unit; a unitless operand is "
            "not an arithmetic value this engine may compare"
        )

    # -- 6. the rule itself must hold authority now ------------------------
    _require_rule_authority(comparison_rules_registry, rule)

    # -- 7. finite stored operands, then the arithmetic, exactly once ------
    comparison_value = _finite_operand_value(
        comparison_current.value, role="comparison"
    )
    baseline_value = _finite_operand_value(baseline_current.value, role="baseline")

    derived = _derive_deltas(
        comparison_value=comparison_value,
        baseline_value=baseline_value,
        delta_operator=rule.delta_operator,
    )

    # -- 8. the coverage observation ref travels with its evidence ---------
    if comparison_current.coverage_observation_id is None:
        raise ChangeDerivationError(
            f"coverage replay reached SUFFICIENT for "
            f"{comparison_current.measurement_id} but the observation record "
            f"cites no coverage_observation_id; a PRESENT coverage state "
            f"without its observation ref is not a record this engine may write"
        )

    # -- 9. assemble the authoritative record ------------------------------
    return ChangeObservation(
        change_observation_id=change_observation_id,
        subject_ref=comparison_current.subject_ref,
        valid_time=comparison_current.valid_time,
        metric_definition_ref=comparison_current.metric_definition_ref,
        metric_definition_semantic_fingerprint=(
            rule.metric_definition_semantic_fingerprint
        ),
        comparison_rule_ref=rule.comparison_rule_id,
        comparison_rule_version=rule.version,
        comparison_rule_fingerprint=comparison_rule_fingerprint(rule),
        derivation_binding_ref=derivation_binding_ref,
        baseline_selector_spec_fingerprint=(
            baseline_selector_fingerprint(rule.baseline_selector)
        ),
        baseline_measurement_refs=baseline_measurement_refs,
        comparison_measurement_refs=comparison_refs,
        selected_baseline_measurement_ref=baseline_current.measurement_id,
        absolute_delta=derived.absolute_delta,
        relative_delta=derived.relative_delta,
        delta_operator=rule.delta_operator,
        change_kind=derived.change_kind,
        unit=comparison_current.unit,
        source_measurement_refs=(
            comparison_current.measurement_id,
            baseline_current.measurement_id,
        ),
        measurement_methodology_refs=(
            comparison_current.methodology_identity,
            baseline_current.methodology_identity,
        ),
        coverage_requirement_status=CoverageRequirementStatus.REQUIRED,
        coverage_applicability_source_ref=rule.coverage_applicability_source_ref,
        coverage_observation_state=sealed.state,
        coverage_observation_ref=comparison_current.coverage_observation_id,
        coverage_verdict=sealed.verdict,
        missingness=comparison_current.missingness_state.value,
        comparability_status=status,
        comparability_refusal_reasons=(),
        display_metadata={},
    )


def _require_declared_and_sealed_agree(
    rule: ComparisonRule, sealed: SealedCoverage
) -> None:
    """Fail closed when the sealed replay and the governing rule disagree.

    The replay resolved applicability for the exact metric; the rule declares
    what the operator ratified. Honest inputs agree, because the rule's own
    R-2 validator ties its declared status to a recorded upstream
    determination. A disagreement means one of the two is not what it claims
    and neither may be recorded.
    """

    declared_required = (
        rule.coverage_requirement_status is CoverageRequirementStatus.REQUIRED
    )
    if sealed.required != declared_required:
        raise ChangeDerivationError(
            f"the sealed coverage replay resolved applicability "
            f"{'REQUIRED' if sealed.required else 'UNRESOLVED'} but the "
            f"governing rule declares "
            f"{rule.coverage_requirement_status.value}; the engine consumes "
            f"sealed results and will not record a coverage basis that "
            f"disagrees with itself"
        )


def _require_rule_authority(
    comparison_rules_registry: ComparisonRuleRegistry, rule: ComparisonRule
) -> None:
    """Re-check the governing rule's authority live, at the moment of use.

    Registration is not authority: the accepted
    :class:`ComparisonRuleRegistry` re-checks registration, currency,
    invalidation, live ratification and content digest at the moment of use,
    and the engine asks it rather than trusting that the caller resolved the
    rule honestly.
    """

    if not comparison_rules_registry.is_authoritative_now(rule.comparison_rule_id):
        raise ChangeDerivationError(
            f"comparison rule {rule.comparison_rule_id} does not hold "
            f"authority at derivation time; registration is not authority"
        )


def _finite_operand_value(value: float | None, *, role: str) -> float:
    """The operand's stored value iff it exists and is finite, else refuse.

    NaN, ``+Inf`` and ``-Inf`` never reach the arithmetic: the engine fails
    closed here, before the subtraction, so no non-finite delta can be
    derived and none can be persisted.
    """

    if value is None or not math.isfinite(value):
        raise ChangeDerivationError(
            f"{OPERAND_NOT_FINITE_VALUE_BEARING}: the {role} operand carries "
            f"value {value!r}; no arithmetic is performed and no non-finite "
            f"delta may be persisted"
        )
    return value


__all__ = [
    "AUTHORITATIVE_COMPARISON_MEASUREMENT_COUNT",
    "MULTI_COMPARISON_MEASUREMENT_SET_NOT_AUTHORIZED",
    "OPERAND_NOT_CURRENT",
    "OPERAND_NOT_FINITE_VALUE_BEARING",
    "ChangeDerivationError",
    "DerivedChange",
    "SealedCoverage",
    "derive_change_observation",
]
