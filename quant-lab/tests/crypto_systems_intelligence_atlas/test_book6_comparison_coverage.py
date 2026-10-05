"""Rung 7 — comparison coverage and temporal comparability.

Discharges GAP-3 / 3C (checks 12–16) and GAP-4 / 4D (check 19).

The negative cases are the substance. A coverage layer that reports
``NOT_APPLICABLE`` whenever a rule is missing looks reasonable and is wrong: it
turns "nobody determined this" into "none applies". And a comparability layer
that reports ``NOT_COMPARABLE`` for an undetermined basis reports a decision
nobody made. Both are asserted against explicitly.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from crypto_systems_intelligence_atlas.book6_comparison_coverage import (
    COVERAGE_CHECK_NUMBERS,
    NO_UPSTREAM_DETERMINATION_EXISTS,
    TEMPORAL_COMPARABILITY_CHECK,
    ReplayCheck,
    derive_temporal_comparability,
    replay_coverage_checks,
    resolve_coverage_applicability,
)
from crypto_systems_intelligence_atlas.book6_comparison_contracts import (
    CoverageObservationState,
    CoverageRequirementStatus,
    CoverageVerdict,
    TemporalComparabilityStatus,
)
from crypto_systems_intelligence_atlas.book6_coverage_rules import (
    COVERAGE_SUFFICIENCY_RULES_RATIFIED_AT_BOOTSTRAP,
    CoverageRuleError,
    CoverageRuleRegistry,
)
from crypto_systems_intelligence_atlas.book6_definitions import CoverageSufficiencyRule

NOW = datetime(2026, 10, 5, tzinfo=timezone.utc)
METRIC = "metric.tx"
OTHER = "metric.other"


def _rule(rule_id="cov:1", *, metric=METRIC, version="1", fraction=0.9):
    return CoverageSufficiencyRule(
        rule_id=rule_id, version=version, required_fraction=fraction,
        scope_metric_id=metric, rationale="ratified coverage sufficiency floor",
    )


def _registry(*rules, ratify=True):
    reg = CoverageRuleRegistry()
    for rule in rules:
        reg.register(rule)
        if ratify:
            reg.ratify(rule.rule_id, operator="operator:1", at=NOW)
    return reg


def _sufficient(_rule_ref: str, _metric_id: str) -> CoverageVerdict:
    return CoverageVerdict.SUFFICIENT


def _insufficient(_rule_ref: str, _metric_id: str) -> CoverageVerdict:
    return CoverageVerdict.INSUFFICIENT


def _unknown(_rule_ref: str, _metric_id: str) -> CoverageVerdict:
    return CoverageVerdict.UNKNOWN


def _replay(reg, *, named="cov:1", metric=METRIC,
            state=CoverageObservationState.PRESENT, ref="cov:obs",
            verdict_of=_sufficient):
    return replay_coverage_checks(
        registry=reg, metric_id=metric, named_rule_ref=named,
        observation_state=state, observation_ref=ref, coverage_verdict_of=verdict_of,
    )


def _check(auth, number):
    return next(c for c in auth.checks if c.number == number)


# -- GAP-3: applicability from the accepted authority ----------------------


def test_exact_metric_current_ratified_rule_yields_required() -> None:
    reg = _registry(_rule())
    app = resolve_coverage_applicability(registry=reg, metric_id=METRIC)
    assert app.requirement_status is CoverageRequirementStatus.REQUIRED
    assert app.coverage_rule_ref == "cov:1"
    assert app.source_ref == "coverage-rule:cov:1"


def test_no_coverage_rule_yields_unresolved_not_not_applicable() -> None:
    reg = _registry()
    app = resolve_coverage_applicability(registry=reg, metric_id=METRIC)
    assert app.requirement_status is CoverageRequirementStatus.UNRESOLVED
    assert app.requirement_status is not CoverageRequirementStatus.NOT_APPLICABLE
    assert app.reasons == (NO_UPSTREAM_DETERMINATION_EXISTS,)
    assert app.source_ref is None and app.coverage_rule_ref is None


def test_absence_never_implies_not_applicable() -> None:
    """3C: a rule nobody wrote is a gap in the basis, not a negative finding."""

    for rule in ((), (_rule(),)):
        app = resolve_coverage_applicability(
            registry=_registry(*rule), metric_id=METRIC)
        assert app.requirement_status is not CoverageRequirementStatus.NOT_APPLICABLE


def test_unratified_rule_does_not_make_coverage_required() -> None:
    reg = _registry(_rule(), ratify=False)
    app = resolve_coverage_applicability(registry=reg, metric_id=METRIC)
    assert app.requirement_status is CoverageRequirementStatus.UNRESOLVED


def test_stale_rule_does_not_authorize_comparison() -> None:
    """Supersession revokes; authority decays on a revision."""

    reg = _registry(_rule())
    reg.supersede(_rule(version="2"))
    app = resolve_coverage_applicability(registry=reg, metric_id=METRIC)
    assert app.requirement_status is CoverageRequirementStatus.UNRESOLVED
    assert reg.is_sufficient(metric_id=METRIC, rule_ref="cov:1") is False


def test_wrong_metric_rule_cannot_authorize() -> None:
    reg = _registry(_rule(metric=OTHER))
    app = resolve_coverage_applicability(registry=reg, metric_id=METRIC)
    assert app.requirement_status is CoverageRequirementStatus.UNRESOLVED
    assert reg.is_sufficient(metric_id=METRIC, rule_ref="cov:1") is False
    with pytest.raises(CoverageRuleError, match="is scoped to"):
        reg.authorize(metric_id=METRIC, rule_ref="cov:1")


def test_applicability_choice_is_deterministic() -> None:
    reg = _registry(_rule("cov:b"), _rule("cov:a"))
    first = resolve_coverage_applicability(registry=reg, metric_id=METRIC)
    second = resolve_coverage_applicability(registry=reg, metric_id=METRIC)
    assert first == second
    assert first.coverage_rule_ref == "cov:a", "id-ordered, never registration order"


# -- checks 12-16 -----------------------------------------------------------


def test_all_five_coverage_checks_are_replayed() -> None:
    auth = _replay(_registry(_rule()))
    assert tuple(c.number for c in auth.checks) == COVERAGE_CHECK_NUMBERS


def test_check_13_requires_a_rule_ref_exactly_when_required() -> None:
    auth = _replay(_registry(_rule()))
    assert _check(auth, 13).passed is True
    unresolved = _replay(_registry(), named=None)
    assert _check(unresolved, 13).passed is True, "no ref needed when not REQUIRED"


def test_check_14_reports_a_stale_rule_as_a_ratification_fault() -> None:
    """Supersession revokes; the fault is currency, not scope."""

    reg = _registry(_rule())
    reg.supersede(_rule(version="2"))
    auth = _replay(reg)
    assert _check(auth, 14).passed is False
    assert "no live ratification" in _check(auth, 14).reason
    # and it is NOT reported as a scope fault, so 14 and 15 stay separable
    assert _check(auth, 15).passed is True


def test_check_15_reports_a_scope_mismatch_independently_of_14() -> None:
    """A wrong-metric rule is ratified but out of scope: only 15 fails."""

    reg = _registry(_rule(metric=OTHER))
    auth = replay_coverage_checks(
        registry=reg, metric_id=METRIC, named_rule_ref="cov:1",
        observation_state=CoverageObservationState.PRESENT,
        observation_ref="cov:obs", coverage_verdict_of=_sufficient,
    )
    assert _check(auth, 14).passed is True, "ratification is independent of scope"
    assert _check(auth, 15).passed is False
    assert OTHER in _check(auth, 15).reason


def test_check_16_is_deterministic() -> None:
    reg = _registry(_rule())
    first = _replay(reg, verdict_of=_sufficient)
    second = _replay(reg, verdict_of=_sufficient)
    assert [c.reason for c in first.checks] == [c.reason for c in second.checks]
    assert first.verdict is CoverageVerdict.SUFFICIENT
    assert _check(first, 16).passed is True


def test_check_16_refuses_to_claim_a_verdict_it_cannot_establish() -> None:
    auth = _replay(_registry(_rule()), verdict_of=_unknown)
    assert auth.verdict is CoverageVerdict.UNKNOWN
    assert _check(auth, 16).passed is False


def test_unavailable_coverage_observation_fails_check_16() -> None:
    auth = _replay(_registry(_rule()),
                   state=CoverageObservationState.UNAVAILABLE, ref=None)
    assert _check(auth, 16).passed is False
    assert "unavailable" in _check(auth, 16).reason


def test_coverage_ref_is_dropped_when_observation_is_not_present() -> None:
    auth = _replay(_registry(_rule()),
                   state=CoverageObservationState.UNAVAILABLE, ref="cov:obs")
    assert auth.observation_state is CoverageObservationState.UNAVAILABLE
    assert auth.observation_ref is None


# -- checks 12-16 are independently falsifiable ---------------------------


@pytest.mark.parametrize("failing_number", COVERAGE_CHECK_NUMBERS)
def test_each_coverage_check_is_individually_falsifiable(failing_number) -> None:
    """One check may fail while its neighbours hold; they never stand in."""

    auth = _replay(_registry(_rule()))
    tampered = tuple(
        ReplayCheck(c.number, c.name, c.number != failing_number, c.reason)
        for c in auth.checks
    )
    results = [c.passed for c in tampered]
    assert results.count(False) == 1
    assert results[COVERAGE_CHECK_NUMBERS.index(failing_number)] is False


# -- the ordering boundary: coverage never selects ------------------------


def test_coverage_module_does_not_import_the_selector() -> None:
    """COVERAGE_SELECTS_BASELINE = FALSE, enforced structurally.

    Checked against executable source with docstrings stripped, so the prose
    naming the selector cannot satisfy its own assertion.
    """

    import ast
    import inspect

    import crypto_systems_intelligence_atlas.book6_comparison_coverage as m

    tree = ast.parse(inspect.getsource(m))
    docstrings = {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef))
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
    }
    names = [
        node.id for node in ast.walk(tree)
        if isinstance(node, ast.Name) and id(node) not in docstrings
    ]
    imports = [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    ]
    assert "select_baseline" not in names
    assert not [i for i in imports if "comparison_selector" in i]
    assert not hasattr(m, "select_baseline")


def test_coverage_is_not_a_selection_input_and_the_baseline_is_unchanged() -> None:
    """The same candidates select the same baseline with or without coverage."""

    from crypto_systems_intelligence_atlas.book6_comparison_selector import select_baseline

    from crypto_systems_intelligence_atlas.book6_comparison_contracts import (
        BaselineSelectorKind, BaselineSelectorSpec, ComparisonRule, DeltaOperator,
    )
    from crypto_systems_intelligence_atlas.book6_grammar import WindowClass
    from crypto_systems_intelligence_atlas.book6_support import windowed_observation
    from crypto_systems_intelligence_atlas.book6_grammar import MissingnessState

    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def obs(mid, day):
        return windowed_observation(
            mid, METRIC, value=float(day), missingness=MissingnessState.OBSERVED,
            claim_refs=("claim:1",), unit="count", window_class=WindowClass.INSTANTANEOUS,
            valid_time=t0 + timedelta(days=day))

    rule = ComparisonRule(
        comparison_rule_id="cmp:1", version=1, metric_definition_ref=METRIC,
        metric_definition_semantic_fingerprint="fp:metric",
        baseline_selector=BaselineSelectorSpec(
            selector_kind=BaselineSelectorKind.PRIOR_COMPARABLE_WINDOW,
            window_compatibility=(WindowClass.INSTANTANEOUS,),
            methodology_compatibility=("book6-methodology@1",)),
        delta_operator=DeltaOperator.ABSOLUTE_DELTA,
        compatible_methodology_refs=("book6-methodology@1",),
        unit_requirements="count",
        window_compatibility=(WindowClass.INSTANTANEOUS,),
        missingness_requirements=("OBSERVED",), output_semantics="ABSOLUTE_DELTA",
        coverage_requirement_status=CoverageRequirementStatus.UNRESOLVED,
    )
    comparison, cands = obs("c", 9), [obs("b1", 1), obs("b2", 5)]
    kwargs = dict(semantic_fingerprint_of=lambda _: "fp:metric",
                  is_current=lambda _: True)
    before = select_baseline(comparison=comparison, candidates=cands,
                             rule=rule, **kwargs)
    # Coverage is evaluated afterwards and cannot reach back into selection.
    insufficient = _replay(_registry(_rule()), verdict_of=_insufficient)
    verdict = derive_temporal_comparability(coverage=insufficient)
    after = select_baseline(comparison=comparison, candidates=cands,
                            rule=rule, **kwargs)
    assert before == after
    assert before.selected_measurement_ref == "b2"
    assert verdict.status is TemporalComparabilityStatus.NOT_COMPARABLE


def test_coverage_cannot_cause_reselection_or_reordering() -> None:
    """Every coverage verdict over one candidate set yields one baseline."""

    from crypto_systems_intelligence_atlas.book6_comparison_selector import select_baseline

    from crypto_systems_intelligence_atlas.book6_comparison_contracts import (
        BaselineSelectorKind, BaselineSelectorSpec, ComparisonRule, DeltaOperator,
    )
    from crypto_systems_intelligence_atlas.book6_grammar import MissingnessState, WindowClass
    from crypto_systems_intelligence_atlas.book6_support import windowed_observation

    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def obs(mid, day):
        return windowed_observation(
            mid, METRIC, value=float(day), missingness=MissingnessState.OBSERVED,
            claim_refs=("claim:1",), unit="count", window_class=WindowClass.INSTANTANEOUS,
            valid_time=t0 + timedelta(days=day))

    rule = ComparisonRule(
        comparison_rule_id="cmp:1", version=1, metric_definition_ref=METRIC,
        metric_definition_semantic_fingerprint="fp:metric",
        baseline_selector=BaselineSelectorSpec(
            selector_kind=BaselineSelectorKind.PRIOR_COMPARABLE_WINDOW,
            window_compatibility=(WindowClass.INSTANTANEOUS,),
            methodology_compatibility=("book6-methodology@1",)),
        delta_operator=DeltaOperator.ABSOLUTE_DELTA,
        compatible_methodology_refs=("book6-methodology@1",),
        unit_requirements="count",
        window_compatibility=(WindowClass.INSTANTANEOUS,),
        missingness_requirements=("OBSERVED",), output_semantics="ABSOLUTE_DELTA",
        coverage_requirement_status=CoverageRequirementStatus.UNRESOLVED,
    )
    comparison = obs("c", 9)
    cands = [obs("b1", 1), obs("b2", 5)]
    chosen = set()
    for verdict_of in (_sufficient, _insufficient, _unknown):
        verdict_of  # coverage is evaluated, then selection repeats identically
        chosen.add(select_baseline(
            comparison=comparison, candidates=cands, rule=rule,
            semantic_fingerprint_of=lambda _: "fp:metric",
            is_current=lambda _: True).selected_measurement_ref)
    assert chosen == {"b2"}


# -- GAP-4: the three comparability paths ---------------------------------


def test_comparable_path() -> None:
    auth = _replay(_registry(_rule()), verdict_of=_sufficient)
    verdict = derive_temporal_comparability(coverage=auth)
    assert verdict.status is TemporalComparabilityStatus.COMPARABLE
    assert verdict.is_comparable is True
    assert verdict.check_19.passed is True
    assert verdict.check_19.number == TEMPORAL_COMPARABILITY_CHECK


def test_not_comparable_path_requires_an_explicit_determination() -> None:
    """A ratified rule that examined coverage and found it insufficient is a
    DECISION, so it maps to NOT_COMPARABLE rather than to UNRESOLVED."""

    auth = _replay(_registry(_rule()), verdict_of=_insufficient)
    assert all(c.passed for c in auth.checks), "every coverage check holds"
    verdict = derive_temporal_comparability(coverage=auth)
    assert verdict.status is TemporalComparabilityStatus.NOT_COMPARABLE
    assert "INSUFFICIENT" in verdict.check_19.reason


def test_unresolved_path_when_no_upstream_determination_exists() -> None:
    auth = _replay(_registry(), named=None)
    verdict = derive_temporal_comparability(coverage=auth)
    assert verdict.status is TemporalComparabilityStatus.UNRESOLVED
    assert NO_UPSTREAM_DETERMINATION_EXISTS in verdict.check_19.reason


def test_naming_an_unregistered_coverage_rule_fails_closed_to_unresolved() -> None:
    """A ComparisonRule may not assert a coverage ref nothing backs.

    Check 16 still reports honestly -- it claims no verdict rather than
    inventing one -- so the fail-closed comes from checks 14 and 15.
    """

    auth = _replay(_registry(), named="cov:phantom")
    assert _check(auth, 14).passed is False
    assert _check(auth, 15).passed is False
    assert _check(auth, 16).passed is True
    assert "no verdict is claimed" in _check(auth, 16).reason
    assert auth.verdict is CoverageVerdict.UNKNOWN
    verdict = derive_temporal_comparability(coverage=auth)
    assert verdict.status is TemporalComparabilityStatus.UNRESOLVED


def test_a_named_rule_disagreeing_with_applicability_fails_check_13() -> None:
    """13 reconciles the rule's claim with the derived applicability."""

    reg = _registry(_rule("cov:a"), _rule("cov:b"))
    auth = _replay(reg, named="cov:b")   # applicability derives cov:a
    assert _check(auth, 13).passed is False
    assert "disagrees" in _check(auth, 13).reason


def test_unresolved_is_never_not_comparable() -> None:
    """The distinction the whole GAP-4 repair exists to preserve."""

    auth = _replay(_registry())
    verdict = derive_temporal_comparability(coverage=auth)
    assert verdict.status is TemporalComparabilityStatus.UNRESOLVED
    assert verdict.status is not TemporalComparabilityStatus.NOT_COMPARABLE
    assert verdict.status is not TemporalComparabilityStatus.COMPARABLE


def test_an_explicit_structural_failure_outranks_an_unresolved_basis() -> None:
    """A decision beats absence of basis; both are reported."""

    auth = _replay(_registry())
    failed = ReplayCheck(9, "comparison measurement refs", False, "unit mismatch")
    verdict = derive_temporal_comparability(
        coverage=auth, structural_checks=(failed,))
    assert verdict.status is TemporalComparabilityStatus.NOT_COMPARABLE
    assert verdict.structural_failures == (failed,)
    assert "check 9" in verdict.check_19.reason


def test_sufficient_coverage_with_a_structural_failure_is_not_comparable() -> None:
    auth = _replay(_registry(_rule()), verdict_of=_sufficient)
    failed = ReplayCheck(10, "input methodology policy", False, "not permitted")
    verdict = derive_temporal_comparability(
        coverage=auth, structural_checks=(failed,))
    assert verdict.status is TemporalComparabilityStatus.NOT_COMPARABLE


# -- check 19 separability -------------------------------------------------


def test_check_19_is_separate_from_the_coverage_block() -> None:
    assert TEMPORAL_COMPARABILITY_CHECK not in COVERAGE_CHECK_NUMBERS
    auth = _replay(_registry(_rule()))
    verdict = derive_temporal_comparability(coverage=auth)
    assert verdict.check_19.number == 19
    assert all(c.number in COVERAGE_CHECK_NUMBERS for c in verdict.coverage_checks)


def test_check_19_can_fail_while_every_coverage_check_passes() -> None:
    auth = _replay(_registry(_rule()), verdict_of=_sufficient)
    assert all(c.passed for c in auth.checks)
    failed = ReplayCheck(5, "baseline candidate eligibility", False, "no eligible prior")
    verdict = derive_temporal_comparability(coverage=auth, structural_checks=(failed,))
    assert verdict.check_19.passed is False
    assert all(c.passed for c in verdict.coverage_checks)


def test_check_19_can_hold_while_a_coverage_check_fails_is_reported_separately() -> None:
    """Coverage failing routes to UNRESOLVED with 19 failing, and 12–16 intact."""

    auth = _replay(_registry(_rule()), verdict_of=_unknown)
    verdict = derive_temporal_comparability(coverage=auth)
    assert verdict.check_19.passed is False
    assert verdict.status is TemporalComparabilityStatus.UNRESOLVED
    assert [c.number for c in verdict.coverage_checks] == list(COVERAGE_CHECK_NUMBERS)


def test_coverage_checks_are_carried_into_the_verdict_unchanged() -> None:
    auth = _replay(_registry())
    verdict = derive_temporal_comparability(coverage=auth)
    assert verdict.coverage_checks == auth.checks


# -- no new authority -------------------------------------------------------


def test_no_second_coverage_authority_or_benchmark_is_introduced() -> None:
    from crypto_systems_intelligence_atlas import book6_comparison_coverage as m

    for banned in ("CoverageRuleRegistry_", "BenchmarkRule", "benchmark",
                   "register_coverage_rule", "ratify_coverage_rule"):
        assert not hasattr(m, banned), banned
    # the accepted registry is imported and reused, not re-declared
    assert m.CoverageRuleRegistry is CoverageRuleRegistry
    assert COVERAGE_SUFFICIENCY_RULES_RATIFIED_AT_BOOTSTRAP == 0


def test_no_third_comparison_authority_bearing_contract_is_introduced() -> None:
    """G-8 still holds: ComparisonRule + ChangeObservation, and nothing else."""

    from crypto_systems_intelligence_atlas.book6_coverage_rules import (
        CoverageSufficiencyAttestation, CoverageReport,
    )
    from crypto_systems_intelligence_atlas.book6_frozen import Book6FrozenModel

    import crypto_systems_intelligence_atlas.book6_comparison_coverage as m
    from crypto_systems_intelligence_atlas.book6_comparison_contracts import (
        BaselineSelectorSpec, ChangeObservation, ComparisonRule,
    )

    declared = {
        name: obj for name, obj in vars(m).items()
        if isinstance(obj, type) and issubclass(obj, Book6FrozenModel)
        and obj is not Book6FrozenModel and obj.__module__ == m.__name__
    }
    assert declared == {}, f"no new record contract allowed here: {sorted(declared)}"
    # the accepted types are used, not redefined
    for accepted in (CoverageRuleRegistry, CoverageSufficiencyRule,
                     CoverageSufficiencyAttestation, CoverageReport,
                     ComparisonRule, ChangeObservation, BaselineSelectorSpec):
        assert accepted.__module__ != m.__name__


def test_rung_7_adds_no_aggregation_or_new_policy() -> None:
    import inspect

    import crypto_systems_intelligence_atlas.book6_comparison_coverage as m

    source = inspect.getsource(m)
    for banned in ("required_fraction", "timedelta", "rolling", "median",
                   "epsilon", "tolerance", "materiality"):
        assert banned not in source, banned
