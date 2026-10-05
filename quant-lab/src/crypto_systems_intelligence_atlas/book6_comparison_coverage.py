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
authority. ``CoverageSufficiencyRule`` is not re-declared here; the accepted
type is imported and used as-is.

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
from typing import Callable, Final, Sequence

from .book6_comparison_contracts import (
    CoverageObservationState,
    CoverageRequirementStatus,
    CoverageVerdict,
    TemporalComparabilityStatus,
)
from .book6_coverage_rules import CoverageRuleError, CoverageRuleRegistry


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
    """The GAP-3 / 3C answer for one exact metric."""

    requirement_status: CoverageRequirementStatus
    source_ref: str | None
    coverage_rule_ref: str | None
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class CoverageAuthorization:
    """Checks 12–16 for one comparison, plus the fields they determine."""

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
    """GAP-3 / 3C: is coverage required for this exact metric, and on whose word?

    ``REQUIRED`` requires a rule that is registered, carries a live ratification
    for its CURRENT version, and is scoped to this exact metric — all three
    checked live through the accepted registry, never through a local mirror.

    Anything else is ``UNRESOLVED`` with ``NO_UPSTREAM_DETERMINATION_EXISTS``.
    It is deliberately never ``NOT_APPLICABLE``: see the module docstring.
    """

    candidates = registry.rules_for_metric(metric_id)
    authorizing = [
        rule.rule_id
        for rule in candidates
        if registry.is_sufficient(metric_id=metric_id, rule_ref=rule.rule_id)
    ]
    if not authorizing:
        return CoverageApplicability(
            requirement_status=CoverageRequirementStatus.UNRESOLVED,
            source_ref=None,
            coverage_rule_ref=None,
            reasons=(NO_UPSTREAM_DETERMINATION_EXISTS,),
        )
    # Deterministic: id-ordered, so the chosen rule never depends on
    # registration order or dict iteration.
    chosen = sorted(authorizing)[0]
    return CoverageApplicability(
        requirement_status=CoverageRequirementStatus.REQUIRED,
        source_ref=f"coverage-rule:{chosen}",
        coverage_rule_ref=chosen,
        reasons=(),
    )


def replay_coverage_checks(
    *,
    registry: CoverageRuleRegistry,
    metric_id: str,
    named_rule_ref: str | None,
    observation_state: CoverageObservationState,
    observation_ref: str | None,
    coverage_verdict_of: Callable[[str, str], CoverageVerdict],
) -> CoverageAuthorization:
    """Replay canonical checks 12–16, each independently.

    ``named_rule_ref`` is what the ``ComparisonRule`` names. It is the input to
    check 13, and it never silently substitutes for the derived applicability in
    check 12 — a mismatch between the two is itself a failure, because a rule
    that asserts a coverage ref the applicability derivation does not support is
    making a claim the corpus has not established.

    ``coverage_verdict_of`` stands for the ratified rule's deterministic verdict
    for a comparison. It is injected rather than computed because the accepted
    substrate has no coverage-fraction reader, and inventing one here would be
    new aggregation semantics. Returning ``UNKNOWN`` is the honest answer when
    no determination exists — and ``UNKNOWN`` routes to ``UNRESOLVED``, not to
    ``NOT_COMPARABLE``.
    """

    applicability = resolve_coverage_applicability(
        registry=registry, metric_id=metric_id
    )
    required = applicability.requirement_status is CoverageRequirementStatus.REQUIRED
    # The rule the ComparisonRule NAMES is the subject of checks 13-15. The
    # derived applicability is a separate input, and check 13 is where the two
    # are reconciled. Preferring the derived ref here would make checks 14 and
    # 15 unfalsifiable: no naming mistake could ever reach them.
    effective_ref = named_rule_ref or applicability.coverage_rule_ref

    checks: list[ReplayCheck] = []

    # 12 — coverage applicability resolution
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

    # 13 — coverage-sufficiency rule ref, required exactly when REQUIRED, and
    #      required to agree with the derived applicability when it is.
    if not required:
        ref_ok = True
        ref_reason = f"coverage is not REQUIRED for {metric_id}, so no rule ref is needed"
    elif effective_ref is None:
        ref_ok = False
        ref_reason = f"coverage is REQUIRED for {metric_id} but no rule ref was named"
    elif applicability.coverage_rule_ref != effective_ref:
        ref_ok = False
        ref_reason = (
            f"named rule ref {effective_ref} disagrees with the derived "
            f"applicability ref {applicability.coverage_rule_ref}"
        )
    else:
        ref_ok = True
        ref_reason = f"coverage rule ref {effective_ref} is bound"
    checks.append(
        ReplayCheck(
            13, "coverage sufficiency rule ref present where REQUIRED",
            ref_ok, ref_reason,
        )
    )

    # 14 — ratification and currency. Supersession revokes the ledger entry, so
    #      a stale version reports here and NOT as a scope problem.
    if effective_ref is None:
        ratified_ok = True
        ratification_reason = "no coverage rule ref is bound, so there is nothing to ratify"
    else:
        try:
            registry.registered_rule(effective_ref)
        except CoverageRuleError as exc:
            ratified_ok, ratification_reason = False, str(exc)
        else:
            decision = registry.ratification_of(effective_ref)
            if decision is None:
                ratified_ok = False
                ratification_reason = (
                    f"{effective_ref} carries no live ratification for its "
                    f"current version; authority decays on supersession"
                )
            else:
                ratified_ok = True
                ratification_reason = (
                    f"{effective_ref} carries a live ratification by "
                    f"{decision.operator} for version {decision.version}"
                )
    checks.append(
        ReplayCheck(
            14, "coverage rule ratification and currentness",
            ratified_ok, ratification_reason,
        )
    )

    # 15 — scope match against the exact metric, judged independently of 14 so
    #      a wrong-metric rule is reported as a scope fault, not a ratification
    #      fault.
    if effective_ref is None:
        scope_ok = True
        scope_reason = "no coverage rule ref is bound, so there is no scope to match"
    else:
        try:
            rule = registry.registered_rule(effective_ref)
        except CoverageRuleError as exc:
            scope_ok, scope_reason = False, str(exc)
        else:
            scope_ok = rule.scope_metric_id == metric_id
            scope_reason = (
                f"{effective_ref} is scoped to {metric_id}"
                if scope_ok
                else f"{effective_ref} is scoped to {rule.scope_metric_id}, "
                     f"not {metric_id}"
            )
    checks.append(
        ReplayCheck(15, "coverage scope match", scope_ok, scope_reason)
    )

    # 16 — deterministic coverage verdict
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
    elif observation_state is CoverageObservationState.UNAVAILABLE:
        verdict, verdict_ok, verdict_reason = (
            CoverageVerdict.UNKNOWN,
            False,
            "the coverage observation required by the rule is unavailable",
        )
    else:
        verdict = coverage_verdict_of(effective_ref or "", metric_id)
        verdict_ok = True
        verdict_reason = f"{effective_ref} determined coverage {verdict.value}"
        if verdict is CoverageVerdict.UNKNOWN:
            verdict_ok = False
            verdict_reason = f"{effective_ref} produced no coverage determination"

    checks.append(
        ReplayCheck(16, "deterministic coverage verdict", verdict_ok, verdict_reason)
    )

    resolved_state = (
        CoverageObservationState.NOT_APPLICABLE
        if not required
        else observation_state
    )
    return CoverageAuthorization(
        applicability=applicability,
        observation_state=resolved_state,
        observation_ref=observation_ref
        if resolved_state is CoverageObservationState.PRESENT
        else None,
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
