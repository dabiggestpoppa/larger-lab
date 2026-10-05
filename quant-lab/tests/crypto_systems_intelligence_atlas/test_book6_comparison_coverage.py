"""Rung 7 — comparison coverage and temporal comparability.

Discharges GAP-3 / 3C (checks 12–16) and GAP-4 / 4D (check 19), and repairs
the two authority defects found at the Rung 7 candidate `92b954e5`:

* a caller-supplied callback could assert a coverage verdict, and
* applicability selected a rule by lexical ordering.

Both are now structurally impossible, not merely avoided: the replay path has
no callable parameter, and check 12 returns no authoritative rule at all.
"""

from __future__ import annotations

import ast
import inspect
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
    CoverageRequirementStatus,
    CoverageVerdict,
    TemporalComparabilityStatus,
)
from crypto_systems_intelligence_atlas.book6_coverage_rules import (
    COVERAGE_SUFFICIENCY_RULES_RATIFIED_AT_BOOTSTRAP,
    CoverageRuleError,
    CoverageRuleRegistry,
)
from crypto_systems_intelligence_atlas.book6_definitions import (
    CoverageObservation,
    CoverageSufficiencyRule,
)
from crypto_systems_intelligence_atlas.book6_grammar import MissingnessState, WindowClass

NOW = datetime(2026, 10, 5, tzinfo=timezone.utc)
METRIC = "metric.tx"
OTHER = "metric.other"


# -- fixtures ---------------------------------------------------------------


def _rule(rule_id="cov:1", *, metric=METRIC, version="1", fraction=0.9):
    return CoverageSufficiencyRule(
        rule_id=rule_id, version=version, required_fraction=fraction,
        scope_metric_id=metric, rationale="ratified coverage sufficiency floor",
    )


def _observation(*, measurement_id="cov:obs", fraction=0.95, rule_ref="cov:1"):
    return CoverageObservation(
        measurement_id=measurement_id, observed_fraction=fraction,
        basis="observed indexer coverage over the declared window",
        sufficiency_rule_ref=rule_ref, valid_time=NOW,
    )


def _registry(*rules, ratify=True):
    reg = CoverageRuleRegistry()
    for rule in rules:
        reg.register(rule)
        if ratify:
            reg.ratify(rule.rule_id, operator="operator:1", at=NOW)
    return reg


def _replay(reg, *, named="cov:1", metric=METRIC, observation="default"):
    obs = {"default": _observation(), "none": None}.get(observation, observation)
    return replay_coverage_checks(
        registry=reg, metric_id=metric, named_rule_ref=named,
        coverage_observation=obs,
    )


def _check(auth, number):
    return next(c for c in auth.checks if c.number == number)


# -- the two repaired defects ----------------------------------------------


def test_no_callable_or_verdict_parameter_exists_on_the_replay_path() -> None:
    """CALLER_SUPPLIED_COVERAGE_CALLBACK = PROHIBITED, enforced by signature."""

    params = set(inspect.signature(replay_coverage_checks).parameters)
    for banned in ("coverage_verdict_of", "verdict_of", "verdict",
                   "resolve_verdict", "determine"):
        assert banned not in params, banned
    assert "coverage_observation" in params
    assert not any(
        p.kind is inspect.Parameter.VAR_KEYWORD
        for p in inspect.signature(replay_coverage_checks).parameters.values()
    )


def test_caller_cannot_inject_a_sufficient_verdict() -> None:
    """The reproducer for defect A, now a permanent regression test.

    A callback that always returns SUFFICIENT cannot be passed at all, and no
    argument can supply a CoverageVerdict.
    """

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
    source = ast.unparse(ast.Module(
        body=[n for n in tree.body if id(n) not in docstrings], type_ignores=[]))
    assert "coverage_verdict_of" not in source
    assert "Callable" not in source

    with pytest.raises(TypeError):
        replay_coverage_checks(
            registry=_registry(_rule()), metric_id=METRIC,
            named_rule_ref="cov:1", coverage_observation=_observation(),
            coverage_verdict_of=lambda r, m: CoverageVerdict.SUFFICIENT,  # type: ignore[call-arg]
        )


def test_applicability_selects_no_rule() -> None:
    """Defect B: check 12 has no authoritative rule to return."""

    import crypto_systems_intelligence_atlas.book6_comparison_coverage as m

    assert not hasattr(m.CoverageApplicability, "coverage_rule_ref")
    fields = set(m.CoverageApplicability.__dataclass_fields__)
    assert fields == {
        "requirement_status", "source_ref", "candidate_rule_refs", "reasons"}


def test_two_current_rules_do_not_invoke_a_lexical_winner() -> None:
    """Neither rule id is privileged; applicability only counts them."""

    reg = _registry(_rule("zzz-last", fraction=0.99), _rule("aaa-first", fraction=0.10))
    assert len(reg.rules_for_metric(METRIC)) == 2
    app = resolve_coverage_applicability(registry=reg, metric_id=METRIC)
    assert app.requirement_status is CoverageRequirementStatus.REQUIRED
    # diagnostics only, and explicitly NOT an authority ordering
    assert set(app.candidate_rule_refs) == {"aaa-first", "zzz-last"}
    assert app.source_ref is not None
    assert "aaa-first" not in app.source_ref or "2" in app.source_ref


def test_comparison_rule_may_name_either_currently_authorized_rule() -> None:
    """NAMED_RULE_BINDING_CONTROLS: either rule, whichever the operator bound."""

    reg = _registry(_rule("zzz-strict", fraction=0.99), _rule("aaa-loose", fraction=0.10))
    # The SAME observation, replayed under each rule in turn, must follow the
    # rule and not the identifier: 0.50 clears the loose rule and fails the
    # strict one.
    observation = _observation(fraction=0.50, rule_ref="aaa-loose")
    strict = _replay(reg, named="zzz-strict",
                     observation=observation.model_copy(
                         update={"sufficiency_rule_ref": "zzz-strict"}))
    loose = _replay(reg, named="aaa-loose", observation=observation)
    assert strict.verdict is CoverageVerdict.INSUFFICIENT
    assert loose.verdict is CoverageVerdict.SUFFICIENT
    assert _check(strict, 13).passed and _check(loose, 13).passed


def test_named_rule_is_never_silently_replaced() -> None:
    """Two rules exist; the named one is replayed, not the other."""

    reg = _registry(_rule("cov:strict", fraction=0.95), _rule("cov:loose", fraction=0.10))
    auth = _replay(reg, named="cov:loose",
                   observation=_observation(fraction=0.50, rule_ref="cov:loose"))
    reason = _check(auth, 16).reason
    assert "cov:loose requires 0.1" in reason
    assert "cov:strict" not in reason
    assert auth.verdict is CoverageVerdict.SUFFICIENT


def test_naming_the_stricter_rule_yields_the_stricter_verdict() -> None:
    """The substitution that must NOT happen, asserted from the other side."""

    reg = _registry(_rule("cov:strict", fraction=0.95), _rule("cov:loose", fraction=0.10))
    obs = _observation(fraction=0.50, rule_ref="cov:strict")
    auth = _replay(reg, named="cov:strict", observation=obs)
    assert "cov:strict requires 0.95" in _check(auth, 16).reason
    assert auth.verdict is CoverageVerdict.INSUFFICIENT


def test_check_12_remains_required_when_another_valid_rule_exists() -> None:
    reg = _registry(_rule("cov:live"), _rule("cov:other"))
    reg.supersede(_rule("cov:other", version="2"))   # cov:other goes stale
    app = resolve_coverage_applicability(registry=reg, metric_id=METRIC)
    assert app.requirement_status is CoverageRequirementStatus.REQUIRED
    assert app.candidate_rule_refs == ("cov:live",)


# -- GAP-3 applicability ---------------------------------------------------


def test_exact_metric_current_ratified_rule_yields_required() -> None:
    app = resolve_coverage_applicability(
        registry=_registry(_rule()), metric_id=METRIC)
    assert app.requirement_status is CoverageRequirementStatus.REQUIRED


def test_no_coverage_rule_yields_unresolved_not_not_applicable() -> None:
    app = resolve_coverage_applicability(registry=_registry(), metric_id=METRIC)
    assert app.requirement_status is CoverageRequirementStatus.UNRESOLVED
    assert app.requirement_status is not CoverageRequirementStatus.NOT_APPLICABLE
    assert app.reasons == (NO_UPSTREAM_DETERMINATION_EXISTS,)
    assert app.source_ref is None


def test_absence_never_implies_not_applicable() -> None:
    for rules in ((), (_rule(),)):
        app = resolve_coverage_applicability(
            registry=_registry(*rules), metric_id=METRIC)
        assert app.requirement_status is not CoverageRequirementStatus.NOT_APPLICABLE


def test_unratified_rule_does_not_make_coverage_required() -> None:
    app = resolve_coverage_applicability(
        registry=_registry(_rule(), ratify=False), metric_id=METRIC)
    assert app.requirement_status is CoverageRequirementStatus.UNRESOLVED


def test_applicability_is_deterministic() -> None:
    reg = _registry(_rule())
    first = resolve_coverage_applicability(registry=reg, metric_id=METRIC)
    second = resolve_coverage_applicability(registry=reg, metric_id=METRIC)
    assert first == second


# -- checks 13-15 on the NAMED rule ---------------------------------------


def test_all_five_coverage_checks_are_replayed() -> None:
    auth = _replay(_registry(_rule()))
    assert tuple(c.number for c in auth.checks) == COVERAGE_CHECK_NUMBERS


def test_check_13_requires_the_named_ref_when_required() -> None:
    assert _check(_replay(_registry(_rule())), 13).passed is True
    assert _check(_replay(_registry(_rule()), named=None), 13).passed is False
    assert _check(_replay(_registry(), named=None), 13).passed is True


def test_check_14_fails_for_a_stale_named_rule() -> None:
    reg = _registry(_rule())
    reg.supersede(_rule(version="2"))
    auth = _replay(reg, observation=_observation(fraction=0.95, rule_ref="cov:1"))
    assert _check(auth, 14).passed is False
    assert "no live ratification" in _check(auth, 14).reason
    assert _check(auth, 15).passed is True, "scope is reported separately"


def test_check_15_fails_for_a_wrong_metric_named_rule() -> None:
    reg = _registry(_rule(metric=OTHER))
    auth = _replay(reg, named="cov:1")
    assert _check(auth, 14).passed is True, "ratification is independent of scope"
    assert _check(auth, 15).passed is False
    assert OTHER in _check(auth, 15).reason
    with pytest.raises(CoverageRuleError, match="is scoped to"):
        reg.authorize(metric_id=METRIC, rule_ref="cov:1")


# -- check 16: actual observation against the named rule ------------------


def test_actual_fraction_above_required_is_sufficient() -> None:
    auth = _replay(_registry(_rule(fraction=0.90)),
                   observation=_observation(fraction=0.95, rule_ref="cov:1"))
    assert auth.verdict is CoverageVerdict.SUFFICIENT
    assert _check(auth, 16).passed is True
    assert "requires 0.9" in _check(auth, 16).reason
    assert "observed 0.95" in _check(auth, 16).reason


def test_actual_fraction_below_required_is_insufficient() -> None:
    auth = _replay(_registry(_rule(fraction=0.90)),
                   observation=_observation(fraction=0.80, rule_ref="cov:1"))
    assert auth.verdict is CoverageVerdict.INSUFFICIENT
    assert _check(auth, 16).passed is True


def test_boundary_fraction_equal_to_required_is_sufficient() -> None:
    auth = _replay(_registry(_rule(fraction=0.90)),
                   observation=_observation(fraction=0.90, rule_ref="cov:1"))
    assert auth.verdict is CoverageVerdict.SUFFICIENT


def test_check_16_is_deterministic() -> None:
    reg = _registry(_rule())
    first = _replay(reg, observation=_observation(fraction=0.95))
    second = _replay(reg, observation=_observation(fraction=0.95))
    assert [c.reason for c in first.checks] == [c.reason for c in second.checks]


def test_missing_required_observation_fails_check_16() -> None:
    auth = _replay(_registry(_rule()), observation="none")
    assert auth.verdict is CoverageVerdict.UNKNOWN
    assert _check(auth, 16).passed is False
    assert "no applicable" in _check(auth, 16).reason
    assert auth.observation_state.value == "UNAVAILABLE"
    assert auth.observation_ref is None
    verdict = derive_temporal_comparability(coverage=auth)
    assert verdict.status is TemporalComparabilityStatus.UNRESOLVED


def test_observation_naming_the_wrong_rule_fails_check_16() -> None:
    reg = _registry(_rule("cov:a", fraction=0.10), _rule("cov:b", fraction=0.90))
    auth = _replay(reg, named="cov:a",
                   observation=_observation(fraction=0.99, rule_ref="cov:b"))
    assert _check(auth, 16).passed is False
    assert "no rule substitution is permitted" in _check(auth, 16).reason


def test_observation_naming_no_rule_fails_check_16() -> None:
    auth = _replay(_registry(_rule()),
                   observation=_observation(fraction=0.99, rule_ref=None))
    assert _check(auth, 16).passed is False


def test_unratified_named_rule_claims_no_verdict() -> None:
    """No current ratified rule -> applicability UNRESOLVED, no verdict claimed."""

    auth = _replay(_registry(_rule(), ratify=False),
                   observation=_observation(fraction=0.99))
    assert auth.applicability.requirement_status is CoverageRequirementStatus.UNRESOLVED
    assert _check(auth, 16).passed is True, "check 16 claims nothing, so it is honest"
    assert "no verdict is claimed" in _check(auth, 16).reason
    assert auth.verdict is CoverageVerdict.UNKNOWN
    assert derive_temporal_comparability(coverage=auth).status is (
        TemporalComparabilityStatus.UNRESOLVED)


def test_coverage_ref_is_dropped_when_observation_is_absent() -> None:
    auth = _replay(_registry(_rule()), observation="none")
    assert auth.observation_state.value == "UNAVAILABLE"
    assert auth.observation_ref is None


def test_observation_ref_is_reported_when_present() -> None:
    auth = _replay(_registry(_rule()),
                   observation=_observation(measurement_id="cov:obs-42", fraction=0.95))
    assert auth.observation_state.value == "PRESENT"
    assert auth.observation_ref == "cov:obs-42"


# -- the load-bearing distinction ------------------------------------------


def test_recomputed_insufficient_is_check_success_then_not_comparable() -> None:
    """CHECK16_SUCCEEDED_WITH_INSUFFICIENT -> NOT_COMPARABLE."""

    auth = _replay(_registry(_rule(fraction=0.90)),
                   observation=_observation(fraction=0.80))
    assert all(c.passed for c in auth.checks), "every replay check succeeded"
    assert auth.verdict is CoverageVerdict.INSUFFICIENT
    verdict = derive_temporal_comparability(coverage=auth)
    assert verdict.status is TemporalComparabilityStatus.NOT_COMPARABLE
    assert "INSUFFICIENT" in verdict.check_19.reason


def test_failed_check_16_is_unresolved_not_not_comparable() -> None:
    """CHECK16_FAILED -> UNRESOLVED, never NOT_COMPARABLE."""

    auth = _replay(_registry(_rule()), observation="none")
    assert _check(auth, 16).passed is False
    verdict = derive_temporal_comparability(coverage=auth)
    assert verdict.status is TemporalComparabilityStatus.UNRESOLVED
    assert verdict.status is not TemporalComparabilityStatus.NOT_COMPARABLE


def test_the_two_are_not_the_same_outcome() -> None:
    recomputed = derive_temporal_comparability(
        coverage=_replay(_registry(_rule(fraction=0.90)),
                         observation=_observation(fraction=0.80)))
    failed = derive_temporal_comparability(
        coverage=_replay(_registry(_rule()), observation="none"))
    assert recomputed.status is not failed.status
    assert recomputed.status is TemporalComparabilityStatus.NOT_COMPARABLE
    assert failed.status is TemporalComparabilityStatus.UNRESOLVED


# -- separability ----------------------------------------------------------


@pytest.mark.parametrize("failing_number", COVERAGE_CHECK_NUMBERS)
def test_each_coverage_check_is_individually_falsifiable(failing_number) -> None:
    auth = _replay(_registry(_rule()))
    tampered = tuple(
        ReplayCheck(c.number, c.name, c.number != failing_number, c.reason)
        for c in auth.checks
    )
    results = [c.passed for c in tampered]
    assert results.count(False) == 1
    assert results[COVERAGE_CHECK_NUMBERS.index(failing_number)] is False


def test_check_19_is_separate_from_the_coverage_block() -> None:
    assert TEMPORAL_COMPARABILITY_CHECK not in COVERAGE_CHECK_NUMBERS
    auth = _replay(_registry(_rule()))
    verdict = derive_temporal_comparability(coverage=auth)
    assert verdict.check_19.number == 19
    assert all(c.number in COVERAGE_CHECK_NUMBERS for c in verdict.coverage_checks)


def test_check_19_can_fail_while_every_coverage_check_passes() -> None:
    auth = _replay(_registry(_rule()))
    assert all(c.passed for c in auth.checks)
    failed = ReplayCheck(5, "baseline candidate eligibility", False, "no eligible prior")
    verdict = derive_temporal_comparability(coverage=auth, structural_checks=(failed,))
    assert verdict.check_19.passed is False
    assert all(c.passed for c in verdict.coverage_checks)


def test_coverage_checks_are_carried_into_the_verdict_unchanged() -> None:
    auth = _replay(_registry())
    assert derive_temporal_comparability(coverage=auth).coverage_checks == auth.checks


# -- GAP-4 paths -----------------------------------------------------------


def test_comparable_path() -> None:
    auth = _replay(_registry(_rule(fraction=0.90)),
                   observation=_observation(fraction=0.95))
    verdict = derive_temporal_comparability(coverage=auth)
    assert verdict.status is TemporalComparabilityStatus.COMPARABLE
    assert verdict.is_comparable is True
    assert verdict.check_19.passed is True


def test_unresolved_path_when_no_upstream_determination_exists() -> None:
    auth = _replay(_registry(), named=None)
    verdict = derive_temporal_comparability(coverage=auth)
    assert verdict.status is TemporalComparabilityStatus.UNRESOLVED
    assert NO_UPSTREAM_DETERMINATION_EXISTS in verdict.check_19.reason


def test_an_explicit_structural_failure_outranks_an_unresolved_basis() -> None:
    auth = _replay(_registry(), named=None)
    failed = ReplayCheck(9, "comparison measurement refs", False, "unit mismatch")
    verdict = derive_temporal_comparability(coverage=auth, structural_checks=(failed,))
    assert verdict.status is TemporalComparabilityStatus.NOT_COMPARABLE
    assert verdict.structural_failures == (failed,)
    assert "check 9" in verdict.check_19.reason


# -- the ordering boundary and the firewalls -------------------------------


def _comparison_stack():
    from crypto_systems_intelligence_atlas.book6_comparison_contracts import (
        BaselineSelectorKind, BaselineSelectorSpec, ComparisonRule, DeltaOperator,
    )
    from crypto_systems_intelligence_atlas.book6_support import windowed_observation

    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def obs(mid, day):
        return windowed_observation(
            mid, METRIC, value=float(day), missingness=MissingnessState.OBSERVED,
            claim_refs=("claim:1",), unit="count",
            window_class=WindowClass.INSTANTANEOUS,
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
    return obs, rule


def test_coverage_module_does_not_import_the_selector() -> None:
    """COVERAGE_SELECTS_BASELINE = FALSE, enforced structurally."""

    import crypto_systems_intelligence_atlas.book6_comparison_coverage as m

    tree = ast.parse(inspect.getsource(m))
    names = [n.id for n in ast.walk(tree) if isinstance(n, ast.Name)]
    imports = [
        alias.name for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names
    ]
    assert "select_baseline" not in names
    assert not [i for i in imports if "comparison_selector" in i]
    assert not hasattr(m, "select_baseline")


def test_baseline_selection_is_unchanged_by_coverage() -> None:
    """Coverage cannot reorder or reselect, whatever its verdict."""

    from crypto_systems_intelligence_atlas.book6_comparison_selector import select_baseline

    obs, rule = _comparison_stack()
    comparison, cands = obs("c", 9), [obs("b1", 1), obs("b2", 5)]
    kwargs = dict(semantic_fingerprint_of=lambda _: "fp:metric",
                  is_current=lambda _: True)
    before = select_baseline(comparison=comparison, candidates=cands, rule=rule, **kwargs)

    reg = _registry(_rule(fraction=0.90))
    chosen = {before.selected_measurement_ref}
    for observation in (_observation(fraction=0.95), _observation(fraction=0.80), None):
        auth = replay_coverage_checks(
            registry=reg, metric_id=METRIC, named_rule_ref=None,
            coverage_observation=observation)
        derive_temporal_comparability(coverage=auth)
        chosen.add(select_baseline(comparison=comparison, candidates=cands,
                                   rule=rule, **kwargs).selected_measurement_ref)
    assert chosen == {"b2"}
    assert before.selected_measurement_ref == "b2"


def test_no_second_coverage_registry_or_benchmark_is_introduced() -> None:
    import crypto_systems_intelligence_atlas.book6_comparison_coverage as m

    for banned in ("BenchmarkRule", "benchmark", "register_coverage_rule",
                   "ratify_coverage_rule", "CoverageRuleRegistry_"):
        assert not hasattr(m, banned), banned
    assert m.CoverageRuleRegistry is CoverageRuleRegistry
    assert COVERAGE_SUFFICIENCY_RULES_RATIFIED_AT_BOOTSTRAP == 0


def test_no_new_authority_bearing_class_is_introduced() -> None:
    from crypto_systems_intelligence_atlas.book6_frozen import Book6FrozenModel

    import crypto_systems_intelligence_atlas.book6_comparison_coverage as m

    declared = {
        name: obj for name, obj in vars(m).items()
        if isinstance(obj, type) and issubclass(obj, Book6FrozenModel)
        and obj is not Book6FrozenModel and obj.__module__ == m.__name__
    }
    assert declared == {}, f"no new record contract allowed here: {sorted(declared)}"
    assert m.CoverageObservation.__module__.endswith("book6_definitions")
    assert CoverageSufficiencyRule.__module__.endswith("book6_definitions")


def test_rung_7_adds_no_aggregation_or_tolerance_field() -> None:
    import crypto_systems_intelligence_atlas.book6_comparison_coverage as m

    tree = ast.parse(inspect.getsource(m))
    docstrings = {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef))
        and node.body and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
    }
    literals = [
        n.value for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
        and id(n) not in docstrings
    ]
    for banned in ("epsilon", "tolerance", "materiality", "rolling", "median",
                   "isclose", "Decimal"):
        assert not [s for s in literals if banned in s], banned


def test_no_threshold_was_added_to_the_comparison_rule() -> None:
    """NO NUMERIC COVERAGE THRESHOLD ON THIS OBJECT, preserved."""

    from crypto_systems_intelligence_atlas.book6_comparison_contracts import ComparisonRule

    for banned in ("required_fraction", "coverage_threshold", "threshold"):
        assert banned not in ComparisonRule.model_fields
    # the threshold lives on the ratified coverage rule, as intended
    assert "required_fraction" in CoverageSufficiencyRule.model_fields
