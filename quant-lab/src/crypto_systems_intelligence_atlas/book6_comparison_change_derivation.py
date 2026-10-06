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
comparison measurement ref or it refuses. ``comparison_measurement_refs`` is not
a parameter at all — the engine stamps it from the one ref it received — so a
caller cannot assert a plural comparison set, and no code path exists that could
pick first, pick last, sort lexically, average, sum, select by time, select by
coverage, or select by caller order.

The refusal is enforced at **this** derivation layer, not as a schema rewrite.
``ChangeObservation.comparison_measurement_refs`` keeps its ratified
``tuple[str, ...]`` shape with ``min_length=1`` for schema continuity and
historical compatibility; adding a model validator that demanded ``len == 1``
would retroactively change what historical records can exist — records the
schema has always permitted — which the ratification explicitly does not
authorize. This module is the only authoritative production path for change
arithmetic, so the executable-cardinality restriction lives here, where it
gates exactly the records this amendment produces.

**Caller authority — sealed by the Rung 8 authority sealing erratum v0.1.**
``derive_change_observation`` has no parameter that could carry a
caller-authored ``absolute_delta``, ``relative_delta``, ``change_kind``, or —
per grammar v0.6 §3.2 — a ``selected_baseline_ref``, a
``baseline_selector_result``, or a ``baseline_is_valid`` flag:

    CALLER MAY provide:      candidate baseline refs (for offline resolution)
    CALLER MAY NOT provide:  selected_baseline_ref
                             baseline_selector_result
                             baseline_is_valid

The caller supplies the comparison measurement **ref** (an identity, not an
object — a mutated copy has nothing to mutate) and the candidate baseline refs.
Everything else is derived: the engine resolves the canonical comparison through
the GAP-7 registry, structurally loads every candidate ref through the same
registry, and invokes the **one** ratified Rung 6 selector
(:func:`select_baseline`) itself with the ratified inputs. No second selector
implementation exists; ``SELECTOR_IMPLEMENTATIONS = 1``. A candidate ref that
does not resolve fails closed — no silent removal from the candidate set, no
substitution. The selector's result is the only baseline that can become an
operand, it must be a member of the supplied candidate set, and coverage never
influences it (the selector does not read ``coverage_observation_id``).

**The engine consumes, never recomputes, Rung 7 — and never parses prose.**
Coverage and comparability arrive as an already-derived
:class:`ComparabilityVerdict` — check 19's own result, sealed by the rung that
owns it. The verdict now carries its structured :class:`CoverageAuthorization`
(the applicability, observation state, observation ref and verdict Rung 7
already derived), and the engine reads **only** those structured fields. A
sealed verdict without its structured result cannot drive arithmetic: there is
deliberately no fallback that reconstructs the facts from check-reason text,
because ``ReplayCheck.reason`` is diagnostic prose, not a canonical authority
field. Changing reason wording changes nothing; the reasons remain present for
check-by-check falsifiability, and are never canonical.

**The sealed bundle's identity seal is verified, not merely read.** A
structured authorization records which authority bundle produced it — the
comparison measurement, the metric, and the named rule. Before the record's
deltas, and before any refusal record, the engine proves that bundle is THIS
comparison's bundle: the sealed measurement identity equals the canonical
resolved comparison, the sealed metric equals the comparison's canonical
metric AND the governing rule's ``metric_definition_ref``, the sealed rule
identity equals the rule's ``coverage_sufficiency_rule_ref`` (absent exactly
when the rule declares coverage not REQUIRED, per R-2), and the sealed
applicability source equals the rule's ``coverage_applicability_source_ref``.
Equal requirement STATUS alone proves nothing: same status, different
authority bundle, is a substitution and is refused.

Under Rung 7's own law, ``COMPARABLE`` is reachable only when the sealed
coverage replay recomputed ``SUFFICIENT`` under a live, ratified, in-scope rule
(anything less maps to ``UNRESOLVED`` or ``NOT_COMPARABLE``). The engine
enforces that equivalence on the **structured** verdict instead of trusting it:
a ``COMPARABLE`` verdict whose sealed coverage verdict is not ``SUFFICIENT`` is
refused, and the record's coverage fields are the sealed authorization's
answer, never a recomputation.

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
authority. The engine resolves the comparison operand through the accepted
:class:`Book6MeasurementRegistry` resolver — the GAP-7 currentness authority —
before anything else, and refuses anything that is not current *now*. The
selected baseline is resolved through the same resolver, and the selector's
own eligibility gate applies the same authority to every candidate before any
ordering runs. The comparison rule's own authority is re-checked live through
:class:`ComparisonRuleRegistry` at the moment of use.

**Structural identity is re-checked here, fail closed, against the RULE.** The
binding is three-way, not pairwise: the canonical comparison's metric
definition, the selected baseline's metric definition, and the governing
``ComparisonRule``'s ``metric_definition_ref`` must all be the same exact ref,
and the two operands must carry the same exact unit — no conversion. (The
rule's declared metric-definition semantic fingerprint is sealed content; its
replay against a recomputation from the registered ``MetricDefinition`` is
reserved as Rung 9 check 17, because no canonical fingerprint helper exists in
executable form yet and inventing one is out of authority.) These gates raise
rather than downgrade: a record they would produce has no honest arithmetic to
carry.

**Refusals the sealed verdict already decided become records.** When the
sealed Rung 7 verdict is ``NOT_COMPARABLE`` or ``UNRESOLVED``, no arithmetic
runs and no baseline selection is asserted: the engine writes the refusal
record carrying the verdict's own decision, its producing checks as refusal
reasons, and ``selected_baseline_measurement_ref = None`` — which the
contract's presence law requires, because absence of a selected baseline means
BASELINE_UNAVAILABLE and nothing else. The refusal record is built from the
**canonical registry-resolved comparison**, exactly like a positive record —
refusal records are not exempt from registered lookup, currentness, metric
identity or methodology identity, because canonical replay checks 9–11 precede
coverage and comparability. Candidate refs are recorded as supplied, after
structural existence validation; an empty candidate set cannot be recorded
(the contract's ``min_length=1`` has no placeholder). Structural faults the
engine detects itself (non-current operands, identity mismatches, non-finite
values, unresolvable candidates) raise :class:`ChangeDerivationError` instead;
they are faults in the inputs to derivation, not decisions the sealed replay
made.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Final

from .book6_comparison_contracts import (
    ChangeKind,
    ChangeObservation,
    ComparisonRule,
    CoverageRequirementStatus,
    CoverageVerdict,
    DeltaOperator,
    TemporalComparabilityStatus,
)
from .book6_comparison_coverage import (
    ComparabilityVerdict,
    CoverageAuthorization,
    ReplayCheck,
)
from .book6_comparison_registry import (
    ComparisonRuleRegistry,
    baseline_selector_fingerprint,
    comparison_rule_fingerprint,
)
from .book6_comparison_selector import (
    BaselineOutcome,
    BaselineSelectorError,
    select_baseline,
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

#: The refusal reason for a candidate ref that does not resolve in the
#: registry. Candidates fail closed as a set: no silent removal, no substitute.
BASELINE_CANDIDATE_REF_UNRESOLVED: Final[str] = (
    "BASELINE_CANDIDATE_REF_UNRESOLVED"
)

#: The refusal reason for a sealed verdict that arrives without its structured
#: coverage authorization. Diagnostic prose is never a fallback.
STRUCTURED_COVERAGE_RESULT_REQUIRED: Final[str] = (
    "STRUCTURED_COVERAGE_RESULT_REQUIRED"
)

#: The refusal reason when the sealed selection cannot resolve a baseline for a
#: COMPARABLE comparison. Not a record: the sealed replay made no such decision.
BASELINE_UNAVAILABLE_AT_DERIVATION: Final[str] = (
    "BASELINE_UNAVAILABLE_AT_DERIVATION"
)


@dataclass(frozen=True)
class DerivedChange:
    """The arithmetic result, before it becomes a ``ChangeObservation``.

    A value object, not an authority-bearing contract. The engine, not the
    caller, owns every field here.
    """

    absolute_delta: float
    relative_delta: float | None
    change_kind: ChangeKind


def _validate_operand_cardinality(
    comparison_measurement_refs: tuple[str, ...],
) -> None:
    """Fail closed unless the comparison set has exactly one member.

    This is the executable-cardinality firewall of
    ``BOOK6-COMPARISON-OPERAND-CARDINALITY-v0.1``. The engine receives the
    comparison set only as it stamps it — one ref, from the one identity it
    resolved — so this check runs on every authoritative production path,
    before any operand is examined or used. A set of any size other than one is
    refused as a set: there is no comparison-side selector, tie-break, reducer
    or aggregation to reduce it with, and none may be invented. The empty set
    is refused here in the same terms, so even a Python caller bypassing the
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


def _load_candidate(
    registry: Book6MeasurementRegistry, measurement_ref: str
) -> MeasurementObservation:
    """Structurally load one candidate ref, or fail closed.

    Existence only — currency is the selector's eligibility gate. A candidate
    ref that does not resolve is refused as supplied: the candidate set is
    never silently pruned, and no other ref is ever substituted for it.
    """

    try:
        return registry.registered_measurement(measurement_ref)
    except Exception as exc:  # noqa: BLE001 - registry refusal is fail-closed
        raise ChangeDerivationError(
            f"{BASELINE_CANDIDATE_REF_UNRESOLVED}: baseline candidate "
            f"{measurement_ref} does not resolve to a registered observation; "
            f"the candidate set fails closed as supplied"
        ) from exc


def _is_current(
    registry: Book6MeasurementRegistry,
) -> Callable[[str], bool]:
    """The selector's currentness authority: the GAP-7 resolver, live."""

    return registry.is_authoritative_now


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


def _sealed_coverage(
    comparability: ComparabilityVerdict,
) -> CoverageAuthorization:
    """The structured coverage authorization the sealed Rung 7 result carries.

    A sealed verdict without its structured result cannot drive arithmetic:
    reconstructing the facts from ``ReplayCheck.reason`` text would make
    diagnostic prose into authority, which the sealing erratum forbids. There
    is deliberately no prose fallback.
    """

    authorization = comparability.coverage
    if authorization is None:
        raise ChangeDerivationError(
            f"{STRUCTURED_COVERAGE_RESULT_REQUIRED}: the sealed Rung 7 result "
            f"carries no structured CoverageAuthorization; diagnostic check "
            f"reasons are not a canonical authority surface and will not be "
            f"parsed as one"
        )
    return authorization


def _refusal_reasons(
    comparability: ComparabilityVerdict,
) -> tuple[tuple[str, str], ...]:
    """The producing checks behind a non-COMPARABLE verdict, as record rows.

    GAP-4 requires a refusal to name its gates. Every failed check the sealed
    verdict carries is a producer: structural failures first (they are
    decisions), then the coverage replay, then check 19 itself — which is
    always failed on a non-COMPARABLE verdict, so the tuple is never empty and
    the contract's producing-gate law is satisfiable by construction. Reasons
    are diagnostics attached to a decision the sealed replay made; they are
    never the decision itself.
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
    comparison_measurement_ref: str,
    baseline_measurement_refs: tuple[str, ...],
    rule: ComparisonRule,
    registry: Book6MeasurementRegistry,
    comparison_rules_registry: ComparisonRuleRegistry,
    semantic_fingerprint_of: Callable[[str], str],
    comparability: ComparabilityVerdict,
    change_observation_id: str,
    derivation_binding_ref: str,
) -> ChangeObservation:
    """Derive one authoritative ``ChangeObservation`` from sealed rung results.

    Parameters the caller may not supply, on purpose, because the engine owns
    them: ``absolute_delta``, ``relative_delta``, ``change_kind``,
    ``comparison_measurement_refs`` (stamped from the one resolved operand),
    the record's ``selected_baseline_measurement_ref`` (the Rung 6 selector's
    engine-derived result, never a caller value), and
    ``comparison_rule_fingerprint`` (derived from the rule's canonical
    content). The signature has no parameter that could carry any of them —
    and, per grammar v0.6 §3.2, no ``selected_baseline_ref``,
    ``baseline_selector_result`` or ``baseline_is_valid``.

    The caller supplies the comparison measurement **ref** and the candidate
    baseline refs. The engine resolves the canonical comparison through the
    GAP-7 registry, loads every candidate structurally, replays the ratified
    selector, and consumes the sealed Rung 7 result's structured coverage
    authorization — never its diagnostic prose.

    ``semantic_fingerprint_of`` is the same injected resolution authority the
    ratified selector takes from its operator — one of the "same ratified
    inputs" the sealing erratum names. The engine does not fabricate a
    fingerprint algorithm: replaying the rule's declared
    ``metric_definition_semantic_fingerprint`` against a canonical
    recomputation is reserved as Rung 9 check 17, and until that helper exists
    the gate stays injected rather than invented. ``is_current`` needs no
    injection: the GAP-7 resolver on the accepted registry IS the currentness
    authority, and the engine derives it.
    """

    if rule is None:  # pragma: no cover - typed signature forbids it
        raise ChangeDerivationError("a resolved ComparisonRule is required")

    # -- 1. canonical comparison resolution, before anything else ----------
    # Refusal records are downstream of the same resolution: canonical replay
    # checks 9-11 (registered lookup, currentness, identity) precede coverage
    # and comparability, so no record is ever built from a caller object.
    comparison_current = _resolve_operand(
        registry, comparison_measurement_ref, role="comparison"
    )

    # -- 2. the operand law, before anything else --------------------------
    comparison_refs: tuple[str, ...] = (comparison_current.measurement_id,)
    _validate_operand_cardinality(comparison_refs)

    # -- 3. the sealed Rung 7 decision is the only comparability input, and
    #       it must carry its structured coverage authorization, whose
    #       identity seal must agree with THIS rule and THIS comparison ------
    status = comparability.status
    sealed = _sealed_coverage(comparability)
    _require_declared_and_sealed_agree(rule, sealed, comparison_current)

    if status is not TemporalComparabilityStatus.COMPARABLE:
        # No arithmetic runs on an unresolved or refused comparison. The
        # record carries the verdict's own decision, its own reasons, and no
        # baseline selection. Candidates are recorded as supplied, after
        # structural existence validation — the refusal does not launder a
        # dangling ref, and an empty set cannot be recorded at all.
        if not baseline_measurement_refs:
            raise ChangeDerivationError(
                "the contract requires at least one baseline candidate ref on "
                "the record even for a refusal; an empty candidate set cannot "
                "be recorded (record the refusal through the selector's own "
                "exclusions instead)"
            )
        for ref in baseline_measurement_refs:
            _load_candidate(registry, ref)
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
            selected_baseline_measurement_ref=None,
            absolute_delta=None,
            relative_delta=None,
            delta_operator=rule.delta_operator,
            change_kind=(
                ChangeKind.NOT_COMPARABLE
                if status is TemporalComparabilityStatus.NOT_COMPARABLE
                else ChangeKind.INSUFFICIENT_DATA
            ),
            unit=comparison_current.unit or "unknown",
            source_measurement_refs=(comparison_current.measurement_id,),
            measurement_methodology_refs=(comparison_current.methodology_identity,),
            coverage_requirement_status=sealed.applicability.requirement_status,
            coverage_applicability_source_ref=(
                rule.coverage_applicability_source_ref
                if sealed.applicability.requirement_status
                is CoverageRequirementStatus.REQUIRED
                else None
            ),
            coverage_observation_state=sealed.observation_state,
            coverage_observation_ref=sealed.observation_ref,
            coverage_verdict=sealed.verdict,
            missingness=comparison_current.missingness_state.value,
            comparability_status=status,
            comparability_refusal_reasons=_refusal_reasons(comparability),
            display_metadata={},
        )

    # -- 4. COMPARABLE requires the sealed replay to have recomputed a
    #       SUFFICIENT verdict; the engine enforces this on the STRUCTURED
    #       verdict instead of trusting either side ------------------------
    if sealed.verdict is not CoverageVerdict.SUFFICIENT:
        raise ChangeDerivationError(
            "comparability is COMPARABLE but the sealed Rung 7 replay did not "
            "recompute SUFFICIENT coverage; the engine consumes the sealed "
            "result and will not perform arithmetic that contradicts it"
        )

    # -- 5. exact rule metric binding: the comparison operand must measure
    #       the metric the governing rule governs. Pairwise operand equality
    #       alone would let a rule for metric B drive metric A arithmetic. --
    if comparison_current.metric_definition_ref != rule.metric_definition_ref:
        raise ChangeDerivationError(
            f"the comparison measures {comparison_current.metric_definition_ref} "
            f"but the governing rule {rule.comparison_rule_id} is bound to "
            f"{rule.metric_definition_ref}; exact rule metric binding forbids "
            f"the derivation and no substitution exists"
        )

    # -- 6. candidate integrity: every candidate ref must structurally
    #       resolve. The set fails closed as supplied — no pruning, no
    #       substitution, and the selector's answer must be one of them. ----
    candidates = tuple(
        _load_candidate(registry, ref) for ref in baseline_measurement_refs
    )
    candidate_refs = frozenset(baseline_measurement_refs)

    # -- 7. the ratified Rung 6 selector, replayed by the engine. Same
    #       function, same ratified inputs; there is no second selector. ----
    try:
        selection = select_baseline(
            comparison=comparison_current,
            candidates=candidates,
            rule=rule,
            semantic_fingerprint_of=semantic_fingerprint_of,
            is_current=_is_current(registry),
        )
    except BaselineSelectorError as exc:
        raise ChangeDerivationError(
            f"{BASELINE_UNAVAILABLE_AT_DERIVATION}: the ratified selector "
            f"could not run fail-closed ({exc})"
        ) from exc
    if selection.outcome is not BaselineOutcome.RESOLVED:
        exclusions = ", ".join(
            f"{ref}: {reason.value}" for ref, reason in selection.exclusions
        ) or "no candidates were supplied"
        raise ChangeDerivationError(
            f"{BASELINE_UNAVAILABLE_AT_DERIVATION}: no candidate satisfied the "
            f"ratified PRIOR_COMPARABLE_WINDOW gates for rule metric "
            f"{rule.metric_definition_ref} and comparison metric "
            f"{comparison_current.metric_definition_ref} (exclusions: "
            f"{exclusions}); no unit conversion exists and no candidate "
            f"substitution is permitted"
        )
    selected_ref = selection.selected_measurement_ref
    if selected_ref is None or selected_ref not in candidate_refs:
        # Unreachable through the selector's own contract; guarded because the
        # selected operand must provably be a member of the supplied set.
        raise ChangeDerivationError(  # pragma: no cover - selector invariant
            f"{BASELINE_UNAVAILABLE_AT_DERIVATION}: the selector's result "
            f"{selected_ref!r} is not a member of the supplied candidate set"
        )

    # -- 8. live currentness of the selected baseline, through the same
    #       GAP-7 resolver the comparison went through ----------------------
    baseline_current = _resolve_operand(registry, selected_ref, role="baseline")

    # -- 9. the three-way binding completes: the selected baseline measures
    #       the rule's metric too, and the operands share one exact unit ----
    if baseline_current.metric_definition_ref != rule.metric_definition_ref:
        raise ChangeDerivationError(
            f"baseline {baseline_current.measurement_id} measures "
            f"{baseline_current.metric_definition_ref} but the governing rule "
            f"is bound to {rule.metric_definition_ref}; exact rule metric "
            f"binding forbids the derivation"
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

    # -- 10. the rule itself must hold authority now ------------------------
    _require_rule_authority(comparison_rules_registry, rule)

    # -- 11. finite stored operands, then the arithmetic, exactly once ------
    comparison_value = _finite_operand_value(
        comparison_current.value, role="comparison"
    )
    baseline_value = _finite_operand_value(baseline_current.value, role="baseline")

    derived = _derive_deltas(
        comparison_value=comparison_value,
        baseline_value=baseline_value,
        delta_operator=rule.delta_operator,
    )

    # -- 12. the sealed coverage facts are the record's coverage facts ------
    if sealed.observation_ref is None:
        raise ChangeDerivationError(
            f"the sealed Rung 7 replay recomputed SUFFICIENT for "
            f"{comparison_current.measurement_id} but its structured "
            f"authorization names no coverage observation ref; a PRESENT "
            f"coverage state without its observation ref is not a record this "
            f"engine may write (R-3)"
        )

    # -- 13. assemble the authoritative record ------------------------------
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
        coverage_requirement_status=sealed.applicability.requirement_status,
        coverage_applicability_source_ref=rule.coverage_applicability_source_ref,
        coverage_observation_state=sealed.observation_state,
        coverage_observation_ref=sealed.observation_ref,
        coverage_verdict=sealed.verdict,
        missingness=comparison_current.missingness_state.value,
        comparability_status=status,
        comparability_refusal_reasons=(),
        display_metadata={},
    )


def _require_declared_and_sealed_agree(
    rule: ComparisonRule,
    sealed: CoverageAuthorization,
    comparison_current: MeasurementObservation,
) -> None:
    """Fail closed when the sealed bundle, the rule and the operand disagree.

    Status agreement alone proves nothing: a sealed ``REQUIRED`` result derived
    for another measurement, another metric or another coverage rule would
    carry the same status. The sealed authorization's identity seal (coverage
    identity sealing erratum v0.1) is therefore verified field by field:

    * ``sealed.comparison_measurement_ref`` is the canonical comparison
      resolved through the registry — not merely the ref the caller named;
    * ``sealed.metric_id`` is that comparison's canonical metric AND the
      governing rule's ``metric_definition_ref``;
    * ``sealed.named_rule_ref`` is the rule's
      ``coverage_sufficiency_rule_ref`` — present exactly when the rule
      declares coverage REQUIRED, absent otherwise (R-2 single meanings);
    * ``sealed.applicability.source_ref`` is the rule's
      ``coverage_applicability_source_ref`` — the operator's recorded upstream
      determination, or absence meaning NO_UPSTREAM_DETERMINATION_EXISTS.

    A disagreement means the sealed verdict belongs to another authority
    bundle, and neither side may be recorded.
    """

    declared_required = (
        rule.coverage_requirement_status is CoverageRequirementStatus.REQUIRED
    )
    sealed_required = (
        sealed.applicability.requirement_status is CoverageRequirementStatus.REQUIRED
    )
    if sealed_required != declared_required:
        raise ChangeDerivationError(
            f"the sealed coverage replay resolved applicability "
            f"{'REQUIRED' if sealed_required else 'UNRESOLVED'} but the "
            f"governing rule declares "
            f"{rule.coverage_requirement_status.value}; the engine consumes "
            f"sealed results and will not record a coverage basis that "
            f"disagrees with itself"
        )

    if sealed.comparison_measurement_ref != comparison_current.measurement_id:
        raise ChangeDerivationError(
            f"the sealed coverage bundle was derived for "
            f"{sealed.comparison_measurement_ref!r}, not for the canonical "
            f"comparison {comparison_current.measurement_id!r}; same coverage "
            f"status from another measurement's authority bundle is a "
            f"substitution and is refused"
        )
    if sealed.metric_id != comparison_current.metric_definition_ref:
        raise ChangeDerivationError(
            f"the sealed coverage bundle resolved applicability for metric "
            f"{sealed.metric_id!r}, but the canonical comparison measures "
            f"{comparison_current.metric_definition_ref!r}; same coverage "
            f"status from another metric's authority bundle is a substitution "
            f"and is refused"
        )
    if sealed.metric_id != rule.metric_definition_ref:
        raise ChangeDerivationError(
            f"the sealed coverage bundle resolved applicability for metric "
            f"{sealed.metric_id!r} but the governing rule "
            f"{rule.comparison_rule_id} is bound to "
            f"{rule.metric_definition_ref!r}; exact rule metric binding "
            f"forbids the derivation and no substitution exists"
        )
    declared_rule_ref = (
        rule.coverage_sufficiency_rule_ref if declared_required else None
    )
    if sealed.named_rule_ref != declared_rule_ref:
        raise ChangeDerivationError(
            f"the sealed coverage bundle was derived under coverage rule "
            f"{sealed.named_rule_ref!r}, not the governing rule's bound "
            f"{declared_rule_ref!r}; same coverage status from another "
            f"coverage rule's authority bundle is a substitution and is refused"
        )
    if sealed.applicability.source_ref != rule.coverage_applicability_source_ref:
        raise ChangeDerivationError(
            f"the sealed coverage bundle's applicability source "
            f"{sealed.applicability.source_ref!r} is not the governing rule's "
            f"declared source {rule.coverage_applicability_source_ref!r}; the "
            f"upstream determination must be the one the operator recorded"
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
    "BASELINE_CANDIDATE_REF_UNRESOLVED",
    "BASELINE_UNAVAILABLE_AT_DERIVATION",
    "MULTI_COMPARISON_MEASUREMENT_SET_NOT_AUTHORIZED",
    "OPERAND_NOT_CURRENT",
    "OPERAND_NOT_FINITE_VALUE_BEARING",
    "STRUCTURED_COVERAGE_RESULT_REQUIRED",
    "ChangeDerivationError",
    "DerivedChange",
    "derive_change_observation",
]
