"""Book 6 comparison coverage and temporal comparability — RUNG 7.

This rung derives two things, in this order and never the other way round:

1. **Coverage applicability and sufficiency** (GAP-3 / 3C), replaying canonical
   checks 12–16; and
2. **Temporal comparability** (GAP-4 / 4D), replaying canonical check 19.

The ordering boundary is the point of the module. Coverage is applied **after**
structural baseline selection, so:

    COVERAGE_SELECTS_BASELINE  = FALSE
    COVERAGE_REORDERS_CANDIDATES = FALSE

Coverage is not an input to ``select_baseline`` and this module does not import
it. The baseline arrives already resolved; nothing here can change which
observation was chosen, only whether the comparison may proceed.

**No second coverage authority.** Coverage-rule currentness comes from the
accepted ``CoverageRuleRegistry`` — the same registry that seals
``DATA_COMPLETE`` for the state vector. This module adds no registry, no
ratification mechanism, no comparison-local coverage authority, and no benchmark
authority. ``CoverageSufficiencyRule`` and ``CoverageObservation`` are not
re-declared here; the accepted types are imported and used as-is.

**No caller-supplied verdict.** There is deliberately no callable parameter on
the replay path. Check 16 recomputes its verdict from an actual
``CoverageObservation``'s ``observed_fraction`` against the named rule's
``required_fraction`` — two fields of accepted frozen models, both constrained
to ``[0, 1]``, compared with no epsilon, no tolerance and no rounding. A
caller-supplied ``CoverageVerdict`` would be a self-declared coverage claim,
which is precisely what the accepted corpus forbids.

**No lexical rule selection.** Check 12 answers one question — does *any*
current, ratified, exact-metric rule exist — and selects nothing. Which rule
governs is the operator's choice, recorded as
``ComparisonRule.coverage_sufficiency_rule_ref`` and sealed inside the rule's
own ratified fingerprint. Registry ordering is not a source of authority.

**Coverage evidence is bound to one exact measurement.** The accepted substrate
already carries the binding: ``CoverageObservation.measurement_id`` is a
required field, ``register_coverage`` keys the store by it, and ``coverage_of``
reads by it, so no accepted path can return measurement B's coverage when asked
for measurement A's. Check 16 performs that binding rather than assuming it, and
it performs it **before** reading ``observed_fraction``:

    coverage_observation.measurement_id == comparison_measurement_ref

A rule match, a live ratification and an exact metric scope say nothing about
which observation was measured, so passing checks 14 and 15 with another
measurement's observation is not evidence for this comparison at all:

    CROSS_MEASUREMENT_COVERAGE_SUBSTITUTION = PROHIBITED
    RULE_MATCH_ALONE_IS_NOT_ENOUGH          = TRUE

The expected identity arrives as a required parameter and is never inferred from
the rule, the metric, a caller convention, the registry, or the observation
itself — inferring it from the observation would satisfy the check with the very
substitution the check exists to catch.

**A wrong-measurement observation yields no verdict at all.** It is not a
recomputed ``INSUFFICIENT`` and not a finding; it is an absence of basis:

    CHECK 16 = FAIL, COVERAGE_VERDICT = UNKNOWN, COMPARABILITY = UNRESOLVED

Per ``BOOK6-COVERAGE-MEASUREMENT-BINDING-v0.1``
(``BIND_COVERAGE_TO_THE_COMPARISON_MEASUREMENT``), the evidence attaches to the
comparison measurement. ``comparison_measurement_refs`` on the record is a
plural set, so this module replays **one measurement per call** and defines no
aggregate verdict — N comparison measurements are N replays, each against its own
observation. No aggregation semantics are introduced here.

**Check 16 succeeds by recomputing, whatever it recomputes.** An
``INSUFFICIENT`` verdict is a *successful* replay of a ratified rule that found
coverage insufficient; check 19 maps that explicit determination to
``NOT_COMPARABLE``. Check 16 *fails* only when the replay could not be
performed — no observation, or one naming a different rule — which is an absence
of basis and maps to ``UNRESOLVED``. Merging those two is the GAP-4 collapse.

**GAP-3 / 3C, stated exactly.** For the exact metric being compared:

    a current, ratified, in-scope CoverageSufficiencyRule exists
        -> applicability REQUIRED
    otherwise
        -> applicability UNRESOLVED, reason NO_UPSTREAM_DETERMINATION_EXISTS

``NOT_APPLICABLE`` is **never** derived from the absence of a rule. That
distinction is the whole content of 3C: a coverage requirement that nobody has
yet determined is a gap in the basis, not a statement that none applies. An
engine that maps "no rule" to ``NOT_APPLICABLE`` reports a decision nobody made.

**GAP-4 / 4D, stated exactly.** ``TemporalComparabilityStatus`` has three
members and the third is not a synonym for the second:

    COMPARABLE       every applicable gate passed
    NOT_COMPARABLE   an explicit structural requirement FAILED
    UNRESOLVED       insufficient authoritative basis to decide

``UNRESOLVED`` is never mapped to ``NOT_COMPARABLE``. A structural failure is a
decision; absence of basis is not a failure. Collapsing them would report a
determination the engine never made — and it would convert "nobody has decided"
into "this pair is incompatible", which is a materially different claim.

**Checks 12–16 and check 19 stay separately falsifiable.** Each is returned as
its own :class:`ReplayCheck` with its own verdict and reason, so a caller can
fail one without failing the others. In particular check 19 may pass while a
coverage check fails (and the reverse), and neither is derivable from the other.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Sequence

from .book6_comparison_contracts import (
    CoverageObservationState,
    CoverageRequirementStatus,
    CoverageVerdict,
    TemporalComparabilityStatus,
)
from .book6_coverage_rules import CoverageRuleError, CoverageRuleRegistry
from .book6_definitions import CoverageObservation


class ComparisonCoverageError(ValueError):
    """A coverage or comparability replay could not be evaluated."""


#: The single meaning of an absent applicability source, per R-2. It is not a
#: generic "unknown": it says specifically that no upstream determination
#: exists for this metric, which is why ``NOT_APPLICABLE`` is not derivable.
NO_UPSTREAM_DETERMINATION_EXISTS: Final[str] = "NO_UPSTREAM_DETERMINATION_EXISTS"

#: The canonical replay checks this module discharges.
COVERAGE_CHECK_NUMBERS: Final[tuple[int, ...]] = (12, 13, 14, 15, 16)

#: Check 19 is temporal comparability and is deliberately NOT in the coverage
#: block: it must stay independently falsifiable from all five.
TEMPORAL_COMPARABILITY_CHECK: Final[int] = 19

#: Check 16's failure reason when the observation belongs to another measurement.
#: A named constant because it is a law the tests assert on verbatim, not a
#: message string that may drift.
COVERAGE_OBSERVATION_BELONGS_TO_ANOTHER_MEASUREMENT: Final[str] = (
    "coverage observation belongs to another measurement"
)

#: ...and when the caller supplied no expected identity to bind against. Kept
#: distinct: omitting the expectation is not the same fault as contradicting it.
COVERAGE_EXPECTED_MEASUREMENT_NOT_SUPPLIED: Final[str] = (
    "coverage is REQUIRED but no expected measurement identity was supplied"
)


@dataclass(frozen=True)
class ReplayCheck:
    """One authority-replay check: its verdict, and why.

    A value object, not an authority-bearing contract. ``AGGREGATE_ONLY =
    REJECTED``: every check names the requirement that decided it, so a failure
    is diagnosable instead of guessed at.
    """

    number: int
    name: str
    passed: bool
    reason: str

    @property
    def failed(self) -> bool:
        return not self.passed


@dataclass(frozen=True)
class CoverageApplicability:
    """The GAP-3 / 3C answer for one exact metric.

    ``candidate_rule_refs`` is DIAGNOSTIC ONLY. It exists so a failure can say
    which rules were considered, and it is deliberately never consulted to
    pick one: check 12 answers a yes/no existence question and the authoritative
    binding is the ``ComparisonRule``'s own citation.
    """

    requirement_status: CoverageRequirementStatus
    source_ref: str | None
    candidate_rule_refs: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class CoverageAuthorization:
    """Checks 12–16 for one comparison, plus the fields they determine.

    ``observation_state`` answers *was an observation supplied* (grammar §3.1
    R-3), not *was it accepted*. A rejected observation is still PRESENT on the
    record; check 16 is where acceptance is decided, so the two never collapse.
    """

    applicability: CoverageApplicability
    observation_state: CoverageObservationState
    observation_ref: str | None
    verdict: CoverageVerdict
    checks: tuple[ReplayCheck, ...]


@dataclass(frozen=True)
class ComparabilityVerdict:
    """The GAP-4 / 4D answer, with check 19 separable from 12–16."""

    status: TemporalComparabilityStatus
    check_19: ReplayCheck
    coverage_checks: tuple[ReplayCheck, ...]
    structural_failures: tuple[ReplayCheck, ...] = ()

    @property
    def is_comparable(self) -> bool:
        return self.status is TemporalComparabilityStatus.COMPARABLE


def resolve_coverage_applicability(
    *, registry: CoverageRuleRegistry, metric_id: str
) -> CoverageApplicability:
    """GAP-3 / 3C: is coverage required for this exact metric?

    ``REQUIRED`` requires SOME rule that is registered, carries a live
    ratification for its CURRENT version, and is scoped to this exact metric —
    all three checked live through the accepted registry, never through a
    local mirror.

    This function deliberately selects no rule. It answers one question. Which
    ratified rule this comparison is bound to is a property of the
    operator-ratified ``ComparisonRule``, not of registry ordering; the earlier
    ``sorted(...)[0]`` tie-break was an unratified invention with no basis in
    any ratification. Candidate refs are returned for diagnostics only.

    Anything else is ``UNRESOLVED`` with ``NO_UPSTREAM_DETERMINATION_EXISTS``.
    It is deliberately never ``NOT_APPLICABLE``: see the module docstring.
    """

    candidates = registry.rules_for_metric(metric_id)
    authorizing = tuple(
        sorted(
            rule.rule_id
            for rule in candidates
            if registry.is_sufficient(metric_id=metric_id, rule_ref=rule.rule_id)
        )
    )
    if not authorizing:
        return CoverageApplicability(
            requirement_status=CoverageRequirementStatus.UNRESOLVED,
            source_ref=None,
            candidate_rule_refs=(),
            reasons=(NO_UPSTREAM_DETERMINATION_EXISTS,),
        )
    # source_ref records THAT a determination exists, not WHICH rule governs.
    return CoverageApplicability(
        requirement_status=CoverageRequirementStatus.REQUIRED,
        source_ref=f"exact-metric:{metric_id}:{len(authorizing)}",
        candidate_rule_refs=authorizing,
        reasons=(),
    )


def replay_coverage_checks(
    *,
    registry: CoverageRuleRegistry,
    metric_id: str,
    named_rule_ref: str | None,
    comparison_measurement_ref: str,
    coverage_observation: CoverageObservation | None,
) -> CoverageAuthorization:
    """Replay canonical checks 12–16, each independently.

    ``named_rule_ref`` is ``ComparisonRule.coverage_sufficiency_rule_ref`` — the
    citation the operator bound into the ratified rule. It is the authoritative
    binding and no registry ordering may substitute for it.

    ``comparison_measurement_ref`` is the exact identity of the measurement whose
    coverage is being replayed. It is a **required** parameter with no default
    and no optional path: the expected identity is never inferred from the rule
    id, the metric id, a caller convention, registry ordering, or the observation
    itself, because the last of those would satisfy the check with the very
    substitution it exists to reject.

    ``coverage_observation`` is an actual accepted ``CoverageObservation``. There
    is deliberately **no** callable parameter: a caller-supplied verdict would
    be a self-declared coverage claim, which the corpus forbids. Check 16
    recomputes the verdict from two ratified-bounded numbers — the
    observation's ``observed_fraction`` against the named rule's
    ``required_fraction`` — with no epsilon, tolerance or caller input.

    Check 16 succeeds when it faithfully recomputes the rule's verdict,
    *whatever* that verdict is. A recomputed ``INSUFFICIENT`` is a successful
    replay; a check 16 that could not run at all is a failure and means an
    absence of basis. The distinction is load-bearing and is what keeps
    ``NOT_COMPARABLE`` distinct from ``UNRESOLVED`` downstream.

    The same distinction governs the measurement binding. An observation that
    belongs to another measurement does not recompute ``INSUFFICIENT`` — it
    fails, and a failure is an absence of basis.
    """

    applicability = resolve_coverage_applicability(
        registry=registry, metric_id=metric_id
    )
    required = applicability.requirement_status is CoverageRequirementStatus.REQUIRED

    checks: list[ReplayCheck] = []

    # 12 — applicability only. It selects no rule.
    checks.append(
        ReplayCheck(
            12,
            "coverage applicability resolution",
            True,
            (
                f"coverage is {applicability.requirement_status.value} for "
                f"{metric_id}: {applicability.source_ref or NO_UPSTREAM_DETERMINATION_EXISTS}"
            ),
        )
    )

    # 13 — the operator's citation must be present when coverage is REQUIRED.
    if not required:
        ref_ok = True
        ref_reason = (
            f"coverage is not REQUIRED for {metric_id}, so no rule ref is needed"
        )
    elif named_rule_ref is None:
        ref_ok = False
        ref_reason = (
            f"coverage is REQUIRED for {metric_id} but the ComparisonRule "
            f"names no coverage_sufficiency_rule_ref"
        )
    else:
        ref_ok = True
        ref_reason = (
            f"ComparisonRule binds coverage_sufficiency_rule_ref "
            f"{named_rule_ref}; check 12 considered "
            f"{list(applicability.candidate_rule_refs)}"
        )
    checks.append(
        ReplayCheck(
            13, "coverage sufficiency rule ref present where REQUIRED",
            ref_ok, ref_reason,
        )
    )

    # 14 — the NAMED rule's ratification and currency, live through the
    #      accepted registry. Supersession revokes, so a stale version lands
    #      here and not as a scope problem.
    if named_rule_ref is None:
        ratified_ok = True
        ratification_reason = "no coverage rule ref is bound, so there is nothing to ratify"
    else:
        try:
            registry.registered_rule(named_rule_ref)
        except CoverageRuleError as exc:
            ratified_ok, ratification_reason = False, str(exc)
        else:
            decision = registry.ratification_of(named_rule_ref)
            if decision is None:
                ratified_ok = False
                ratification_reason = (
                    f"{named_rule_ref} carries no live ratification for its "
                    f"current version; authority decays on supersession"
                )
            else:
                ratified_ok = True
                ratification_reason = (
                    f"{named_rule_ref} carries a live ratification by "
                    f"{decision.operator} for version {decision.version}"
                )
    checks.append(
        ReplayCheck(
            14, "coverage rule ratification and currentness",
            ratified_ok, ratification_reason,
        )
    )

    # 15 — the NAMED rule's scope, judged independently of 14 so a
    #      wrong-metric rule reports as a scope fault and not a ratification
    #      fault. No alternative rule may silently replace it.
    if named_rule_ref is None:
        scope_ok = True
        scope_reason = "no coverage rule ref is bound, so there is no scope to match"
    else:
        try:
            named_rule = registry.registered_rule(named_rule_ref)
        except CoverageRuleError as exc:
            scope_ok, scope_reason = False, str(exc)
        else:
            scope_ok = named_rule.scope_metric_id == metric_id
            scope_reason = (
                f"{named_rule_ref} is scoped to {metric_id}"
                if scope_ok
                else f"{named_rule_ref} is scoped to {named_rule.scope_metric_id}, "
                     f"not {metric_id}"
            )
    checks.append(
        ReplayCheck(15, "coverage scope match", scope_ok, scope_reason)
    )

    # 16 — deterministic recomputation from an ACTUAL observation under the
    #      NAMED rule, bound to the EXACT measurement under comparison.
    #      No caller input of any kind beyond the required identities.
    if not required:
        verdict, verdict_ok, verdict_reason = (
            CoverageVerdict.UNKNOWN,
            True,
            "coverage applicability is unresolved; no verdict is claimed",
        )
    elif not (ref_ok and ratified_ok and scope_ok):
        verdict, verdict_ok, verdict_reason = (
            CoverageVerdict.UNKNOWN,
            False,
            "coverage authority could not be established, so no verdict is claimed",
        )
    elif coverage_observation is None:
        verdict, verdict_ok, verdict_reason = (
            CoverageVerdict.UNKNOWN,
            False,
            f"coverage is REQUIRED under {named_rule_ref} but no applicable "
            f"CoverageObservation exists for this comparison",
        )
    elif coverage_observation.sufficiency_rule_ref != named_rule_ref:
        verdict, verdict_ok, verdict_reason = (
            CoverageVerdict.UNKNOWN,
            False,
            f"CoverageObservation names "
            f"{coverage_observation.sufficiency_rule_ref}, not the bound rule "
            f"{named_rule_ref}; no rule substitution is permitted",
        )
    elif comparison_measurement_ref is None:
        # Unreachable through the typed signature; guarded because a Python
        # caller can still pass None and a silently unbound replay would be the
        # exact defect this branch exists to close.
        verdict, verdict_ok, verdict_reason = (
            CoverageVerdict.UNKNOWN,
            False,
            COVERAGE_EXPECTED_MEASUREMENT_NOT_SUPPLIED,
        )
    elif coverage_observation.measurement_id != comparison_measurement_ref:
        # The binding, and it comes BEFORE observed_fraction is read: another
        # measurement's fraction says nothing about this one, however good it
        # looks or however well it matches the rule.
        verdict, verdict_ok, verdict_reason = (
            CoverageVerdict.UNKNOWN,
            False,
            f"{COVERAGE_OBSERVATION_BELONGS_TO_ANOTHER_MEASUREMENT}: the "
            f"observation is attached to {coverage_observation.measurement_id}, "
            f"but coverage is being replayed for "
            f"{comparison_measurement_ref}; no measurement substitution is "
            f"permitted",
        )
    else:
        # The deterministic comparison. Both operands are accepted frozen
        # fields constrained to [0, 1]. No epsilon, no tolerance, no rounding:
        # the number is the RULE'S INPUT, never its own verdict.
        assert named_rule_ref is not None  # narrowed by check 13 above
        named_rule = registry.registered_rule(named_rule_ref)
        verdict = (
            CoverageVerdict.SUFFICIENT
            if coverage_observation.observed_fraction >= named_rule.required_fraction
            else CoverageVerdict.INSUFFICIENT
        )
        verdict_ok = True
        verdict_reason = (
            f"{named_rule_ref} requires {named_rule.required_fraction} and "
            f"observation {coverage_observation.measurement_id} is bound to "
            f"{comparison_measurement_ref} and observed "
            f"{coverage_observation.observed_fraction} -> {verdict.value}"
        )

    checks.append(
        ReplayCheck(16, "deterministic coverage verdict", verdict_ok, verdict_reason)
    )

    resolved_state = (
        CoverageObservationState.NOT_APPLICABLE
        if not required
        else (
            CoverageObservationState.PRESENT
            if coverage_observation is not None
            else CoverageObservationState.UNAVAILABLE
        )
    )
    return CoverageAuthorization(
        applicability=applicability,
        observation_state=resolved_state,
        observation_ref=(
            coverage_observation.measurement_id
            if resolved_state is CoverageObservationState.PRESENT
            and coverage_observation is not None
            else None
        ),
        verdict=verdict,
        checks=tuple(checks),
    )


def derive_temporal_comparability(
    *,
    coverage: CoverageAuthorization,
    structural_checks: Sequence[ReplayCheck] = (),
) -> ComparabilityVerdict:
    """GAP-4 / 4D: derive check 19 from the gates, keeping 12–16 separable.

    The derivation is a strict three-way, and the order of the branches is the
    law:

    * an explicit structural requirement FAILED -> ``NOT_COMPARABLE``
    * otherwise, coverage could not be determined -> ``UNRESOLVED``
    * otherwise -> ``COMPARABLE``

    ``UNRESOLVED`` is checked **before** returning ``COMPARABLE`` and is never
    folded into ``NOT_COMPARABLE``. That is the difference between "this pair is
    structurally incompatible" and "nobody has established whether they are", and
    the two must never share an outcome.

    ``structural_checks`` is the already-resolved outcome of canonical checks
    1–11. It is passed in rather than recomputed so check 19 remains
    independently falsifiable: a caller can hold 12–16 green and make 19 fail,
    or make 12–16 fail while 19's own inputs are otherwise sound.
    """

    structural = tuple(structural_checks)
    explicit_failures = tuple(c for c in structural if c.failed)

    # An explicit failure is a decision, and outranks an unresolved basis.
    if explicit_failures:
        reasons = "; ".join(f"check {c.number} {c.name}: {c.reason}" for c in explicit_failures)
        check_19 = ReplayCheck(
            TEMPORAL_COMPARABILITY_CHECK,
            "temporal comparability",
            False,
            f"an explicit structural requirement failed -> {reasons}",
        )
        return ComparabilityVerdict(
            status=TemporalComparabilityStatus.NOT_COMPARABLE,
            check_19=check_19,
            coverage_checks=coverage.checks,
            structural_failures=explicit_failures,
        )

    # Coverage authority: could a determination be established at all?
    coverage_authority_ok = all(c.passed for c in coverage.checks[1:])
    failed_reasons = [f"check {c.number}: {c.reason}" for c in coverage.checks if c.failed]

    if not coverage_authority_ok:
        # Insufficient authoritative basis, NOT a structural incompatibility.
        check_19 = ReplayCheck(
            TEMPORAL_COMPARABILITY_CHECK,
            "temporal comparability",
            False,
            "insufficient authoritative basis to decide -> "
            + "; ".join(failed_reasons),
        )
        return ComparabilityVerdict(
            status=TemporalComparabilityStatus.UNRESOLVED,
            check_19=check_19,
            coverage_checks=coverage.checks,
        )

    if coverage.verdict is CoverageVerdict.INSUFFICIENT:
        # A ratified, current, in-scope rule examined the coverage and found it
        # insufficient. That is an explicit structural finding, so it is a
        # DECISION and maps to NOT_COMPARABLE -- unlike an absent
        # determination, which maps to UNRESOLVED.
        check_19 = ReplayCheck(
            TEMPORAL_COMPARABILITY_CHECK,
            "temporal comparability",
            False,
            "the ratified coverage rule determined coverage INSUFFICIENT",
        )
        return ComparabilityVerdict(
            status=TemporalComparabilityStatus.NOT_COMPARABLE,
            check_19=check_19,
            coverage_checks=coverage.checks,
        )

    if coverage.verdict is not CoverageVerdict.SUFFICIENT:
        # Authority held, but nobody determined a verdict.
        detail = "; ".join(coverage.applicability.reasons) or "coverage undetermined"
        check_19 = ReplayCheck(
            TEMPORAL_COMPARABILITY_CHECK,
            "temporal comparability",
            False,
            f"insufficient authoritative basis to decide -> {detail}",
        )
        return ComparabilityVerdict(
            status=TemporalComparabilityStatus.UNRESOLVED,
            check_19=check_19,
            coverage_checks=coverage.checks,
        )

    check_19 = ReplayCheck(
        TEMPORAL_COMPARABILITY_CHECK,
        "temporal comparability",
        True,
        "every applicable structural and coverage gate passed",
    )
    return ComparabilityVerdict(
        status=TemporalComparabilityStatus.COMPARABLE,
        check_19=check_19,
        coverage_checks=coverage.checks,
    )


__all__ = [
    "COVERAGE_CHECK_NUMBERS",
    "COVERAGE_EXPECTED_MEASUREMENT_NOT_SUPPLIED",
    "COVERAGE_OBSERVATION_BELONGS_TO_ANOTHER_MEASUREMENT",
    "NO_UPSTREAM_DETERMINATION_EXISTS",
    "TEMPORAL_COMPARABILITY_CHECK",
    "ComparabilityVerdict",
    "ComparisonCoverageError",
    "CoverageApplicability",
    "CoverageAuthorization",
    "ReplayCheck",
    "derive_temporal_comparability",
    "replay_coverage_checks",
    "resolve_coverage_applicability",
]
