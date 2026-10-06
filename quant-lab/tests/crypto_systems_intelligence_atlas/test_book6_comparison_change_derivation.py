"""Rung 8 — deterministic ChangeObservation arithmetic (authority-sealed).

Discharges ``BOOK6-COMPARISON-OPERAND-CARDINALITY-v0.1``
(``RATIFY_ONE_COMPARISON_MEASUREMENT_PER_CHANGEOBSERVATION``), the ratified
delta grammar (amendment ratification record v0.1 :84-97), and the Rung 8
authority sealing erratum v0.1
(``CSIA_BOOK_6_RUNG8_AUTHORITY_SEALING_ERRATUM_v0.1.md``).

The laws under test:

    ONE_CHANGEOBSERVATION_ONE_COMPARISON_MEASUREMENT = TRUE
    absolute_delta = comparison_value - baseline_value      (stored binary64)
    relative_delta = (c - b) / b, UNDEFINED at b == 0
    direction from the sign of the canonical UNROUNDED delta
    non-finite operands never reach arithmetic
    the engine derives; the caller never authors
    CALLER MAY NOT provide selected_baseline_ref (grammar v0.6 §3.2)
    SELECTED_BASELINE = ENGINE_RECOMPUTED_BY_RUNG6_SELECTOR
    DIAGNOSTIC_REASON_TEXT_AUTHORITY = FALSE
    COMPARISON_OPERAND = CANONICAL_REGISTRY_RESOLUTION
    RULE_METRIC_BINDING = EXACT (three-way)

The negative cases matter more than the positive ones, exactly as in Rungs 6
and 7: an engine that computes the right delta under the wrong authority is
still wrong, and the two failure modes are only distinguishable if the fixture
makes them differ.
"""

from __future__ import annotations

import inspect
import math
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from crypto_systems_intelligence_atlas.book6_comparison_change_derivation import (
    AUTHORITATIVE_COMPARISON_MEASUREMENT_COUNT,
    BASELINE_CANDIDATE_REF_UNRESOLVED,
    BASELINE_UNAVAILABLE_AT_DERIVATION,
    MULTI_COMPARISON_MEASUREMENT_SET_NOT_AUTHORIZED,
    OPERAND_NOT_CURRENT,
    OPERAND_NOT_FINITE_VALUE_BEARING,
    STRUCTURED_COVERAGE_RESULT_REQUIRED,
    ChangeDerivationError,
    _validate_operand_cardinality,
    derive_change_observation,
)
from crypto_systems_intelligence_atlas.book6_comparison_contracts import (
    BaselineSelectorKind,
    BaselineSelectorSpec,
    ChangeKind,
    ComparisonRule,
    CoverageRequirementStatus,
    DeltaOperator,
)
from crypto_systems_intelligence_atlas.book6_comparison_coverage import (
    ComparabilityVerdict,
    ReplayCheck,
    derive_temporal_comparability,
    replay_coverage_checks,
)
from crypto_systems_intelligence_atlas.book6_comparison_registry import (
    ComparisonRuleRegistry,
)
from crypto_systems_intelligence_atlas.book6_comparison_selector import (
    BaselineOutcome,
    select_baseline,
)
from crypto_systems_intelligence_atlas.book6_coverage_rules import (
    CoverageRuleRegistry,
)
from crypto_systems_intelligence_atlas.book6_definitions import (
    CoverageObservation,
    CoverageSufficiencyRule,
)
from crypto_systems_intelligence_atlas.book6_grammar import (
    MissingnessState,
    ObservationStatus,
    RestatementReason,
    WindowClass,
)
from crypto_systems_intelligence_atlas.book6_records import MeasurementRecordError
from crypto_systems_intelligence_atlas.book6_registry import Book6RegistryError
from crypto_systems_intelligence_atlas.book6_support import (
    CLAIM_ID,
    build_engine,
    definition,
    register_definition,
    register_measurement,
    windowed_observation,
)

NOW = datetime(2026, 10, 6, tzinfo=timezone.utc)
METRIC = "metric.tx"
OTHER_METRIC = "metric.other"
FP = "fp:metric-tx"
COV_RULE = "cov:1"
COV_SOURCE = f"exact-metric:{METRIC}:1"

#: Structural checks 1-11, all passing. The engine consumes the sealed verdict,
#: so these only have to be honest: no failure among them.
_STRUCTURAL_PASSED = tuple(
    ReplayCheck(n, f"structural gate {n}", True, "passed") for n in range(1, 12)
)


def _fp(ref: str) -> str:
    """The injected fingerprint resolution authority, mirroring Rung 6's tests.

    The engine does not fabricate a fingerprint algorithm (that replay is
    Rung 9 check 17); the same injected resolver the selector tests use feeds
    the selector through the engine here.
    """

    assert ref in {METRIC, OTHER_METRIC}, f"unresolvable metric definition {ref}"
    return FP if ref == METRIC else f"fp:{ref}"


def _t(days: int) -> datetime:
    return NOW + timedelta(days=days - 100)


def _expect(actual: object, expected: object) -> None:
    """A cross-check helper. Test helpers may CROSS-CHECK only; mismatch raises.

    The engine has no parameter a caller could smuggle an expectation through,
    so the cross-check lives here, in the test, where a mismatch is a test
    failure and never a silent override of the engine's own derivation.
    """

    if actual != expected:
        raise AssertionError(f"cross-check mismatch: {actual!r} != {expected!r}")


# -- fixtures ---------------------------------------------------------------


def _engine(*, extra_definitions: bool = False):
    engine, *_ = build_engine(CLAIM_ID)
    register_definition(engine, definition(METRIC, unit="count"))
    if extra_definitions:
        register_definition(engine, definition(OTHER_METRIC, unit="count"))
    return engine


def _obs(
    mid,
    *,
    day=0,
    value=1.0,
    metric=METRIC,
    unit="count",
    missingness=MissingnessState.OBSERVED,
    cov_ref: str | None = None,
    supersedes: str | None = None,
):
    obs = windowed_observation(
        mid,
        metric,
        value=value,
        missingness=missingness,
        claim_refs=(CLAIM_ID,),
        unit=unit,
        window_class=WindowClass.INSTANTANEOUS,
        valid_time=_t(day),
        supersedes=supersedes,
        restatement_reason=(
            RestatementReason.INDEXER_CORRECTION if supersedes else None
        ),
        status=ObservationStatus.OBSERVED,
    )
    if cov_ref is not None:
        return obs.model_copy(update={"coverage_observation_id": cov_ref})
    return obs


def _rule(**kw):
    # R-2: an UNRESOLVED coverage status must carry no sufficiency rule ref and
    # no applicability source, so a status override drops both.
    status = kw.get("coverage_requirement_status", CoverageRequirementStatus.REQUIRED)
    if status is not CoverageRequirementStatus.REQUIRED:
        kw.pop("coverage_sufficiency_rule_ref", None)
        kw.pop("coverage_applicability_source_ref", None)
    base = dict(
        comparison_rule_id="cmp:1",
        version=1,
        metric_definition_ref=METRIC,
        metric_definition_semantic_fingerprint=FP,
        baseline_selector=BaselineSelectorSpec(
            selector_kind=BaselineSelectorKind.PRIOR_COMPARABLE_WINDOW,
            window_compatibility=(WindowClass.INSTANTANEOUS,),
            methodology_compatibility=("book6-methodology@1",),
        ),
        delta_operator=DeltaOperator.ABSOLUTE_DELTA,
        compatible_methodology_refs=("book6-methodology@1",),
        unit_requirements="count",
        window_compatibility=(WindowClass.INSTANTANEOUS,),
        missingness_requirements=("OBSERVED",),
        output_semantics="ABSOLUTE_DELTA",
        coverage_requirement_status=CoverageRequirementStatus.REQUIRED,
        coverage_applicability_source_ref=COV_SOURCE,
        coverage_sufficiency_rule_ref=COV_RULE,
    )
    if status is not CoverageRequirementStatus.REQUIRED:
        base.pop("coverage_sufficiency_rule_ref")
        base.pop("coverage_applicability_source_ref")
    base.update(kw)
    return ComparisonRule(**base)


def _relative_rule(**kw):
    return _rule(
        delta_operator=DeltaOperator.RELATIVE_DELTA,
        output_semantics="RELATIVE_DELTA",
        **kw,
    )


def _rules_registry(*rules, ratify=True) -> ComparisonRuleRegistry:
    reg = ComparisonRuleRegistry()
    for rule in rules:
        reg.register_rule(rule)
        if ratify:
            reg.ratify_rule(
                rule.comparison_rule_id, version=rule.version,
                operator="operator:1", at=NOW,
            )
    return reg


def _cov_registry(*, fraction=0.9) -> CoverageRuleRegistry:
    reg = CoverageRuleRegistry()
    reg.register(
        CoverageSufficiencyRule(
            rule_id=COV_RULE, version="1", required_fraction=fraction,
            scope_metric_id=METRIC, rationale="ratified coverage sufficiency floor",
        )
    )
    reg.ratify(COV_RULE, operator="operator:1", at=NOW)
    return reg


def _coverage_obs(measurement_id: str, *, fraction=0.95) -> CoverageObservation:
    return CoverageObservation(
        measurement_id=measurement_id, observed_fraction=fraction,
        basis="observed indexer coverage over the declared window",
        sufficiency_rule_ref=COV_RULE, valid_time=NOW,
    )


def _seal(
    *,
    comparison_id="obs:c",
    coverage_observation="default",
    cov_fraction=0.9,
    mutate_reasons=None,
) -> ComparabilityVerdict:
    """A sealed Rung 7 result, produced by the REAL Rung 7 code path.

    The registry-derived replay consumes the canonical registered evidence; the
    ``coverage_observation`` fixture is what the engine's own store carries for
    the comparison. ``mutate_reasons`` rewrites check-reason text WITHOUT
    touching any check number, passed state, or verdict — the diagnostic-text
    independence fixture. The structured authorization travels with the verdict
    either way, carrying its identity seal (comparison, metric, named rule).
    """

    engine = _engine()
    # the seal's own registry must carry the canonical comparison measurement:
    # the registry-derived replay resolves it live before any check runs
    register_measurement(
        engine, _obs(comparison_id, day=10, value=7.5, cov_ref=comparison_id))
    reg = engine.registry
    reg.coverage_rules.register(
        CoverageSufficiencyRule(
            rule_id=COV_RULE, version="1", required_fraction=cov_fraction,
            scope_metric_id=METRIC, rationale="ratified coverage sufficiency floor",
        )
    )
    reg.coverage_rules.ratify(COV_RULE, operator="operator:1", at=NOW)
    obs = {"default": _coverage_obs(comparison_id), "none": None}.get(
        coverage_observation, coverage_observation
    )
    if obs is not None:
        reg.register_coverage(obs)
    auth = replay_coverage_checks(
        measurement_registry=reg,
        comparison_measurement_ref=comparison_id,
        named_rule_ref=COV_RULE,
    )
    verdict = derive_temporal_comparability(
        coverage=auth, structural_checks=_STRUCTURAL_PASSED
    )
    if mutate_reasons is not None:
        verdict = replace(
            verdict,
            check_19=replace(verdict.check_19, reason=mutate_reasons(
                verdict.check_19.reason)),
            coverage_checks=tuple(
                replace(c, reason=mutate_reasons(c.reason))
                for c in verdict.coverage_checks
            ),
        )
    return verdict


def _populated_engine(*, live_fraction: float = 0.95):
    """Engine with a current comparison (7.5) and baseline (3.0), coverage cited."""

    engine = _engine()
    register_measurement(engine, _obs("obs:c", day=10, value=7.5, cov_ref="obs:c"))
    register_measurement(engine, _obs("obs:b", day=0, value=3.0))
    engine.registry.register_coverage(
        _coverage_obs("obs:c", fraction=live_fraction)
    )
    return engine


def _candidate_engine(*, live_fraction: float = 0.95):
    """Engine with two eligible candidates (A day 5 value 1, B day 3 value 2).

    The ratified PRIOR_COMPARABLE_WINDOW selector deterministically picks
    ``obs:a`` (greatest effective_end). ``obs:outsider`` is registered and
    current but is NOT in the candidate set.
    """

    engine = _populated_engine(live_fraction=live_fraction)
    register_measurement(engine, _obs("obs:a", day=5, value=1.0))
    register_measurement(engine, _obs("obs:b3", day=3, value=2.0))
    register_measurement(engine, _obs("obs:outsider", day=8, value=100.0))
    return engine


def _derive(
    engine=None,
    *,
    comparison="obs:c",
    rule=None,
    comparability=None,
    baseline_measurement_refs=("obs:b",),
    rules_registry=None,
    change_observation_id="chg:1",
):
    engine = engine or _populated_engine()
    return derive_change_observation(
        comparison_measurement_ref=(
            comparison if isinstance(comparison, str) else comparison.measurement_id
        ),
        baseline_measurement_refs=baseline_measurement_refs,
        rule=rule or _rule(),
        registry=engine.registry,
        comparison_rules_registry=rules_registry or _rules_registry(_rule()),
        semantic_fingerprint_of=_fp,
        comparability=comparability if comparability is not None else _seal(),
        change_observation_id=change_observation_id,
        derivation_binding_ref="binding:1",
    )


# -- 1-5. the operand cardinality law ----------------------------------------


def test_exactly_one_comparison_ref_is_accepted() -> None:
    """The positive path: one comparison measurement, stamped by the engine."""

    engine = _populated_engine()
    record = _derive(engine)
    assert record.comparison_measurement_refs == ("obs:c",)
    assert len(record.comparison_measurement_refs) == (
        AUTHORITATIVE_COMPARISON_MEASUREMENT_COUNT
    )


def test_zero_comparison_refs_are_refused() -> None:
    """() is refused as a set — no default, no first, nothing."""

    with pytest.raises(ChangeDerivationError) as excinfo:
        _validate_operand_cardinality(())
    assert MULTI_COMPARISON_MEASUREMENT_SET_NOT_AUTHORIZED in str(excinfo.value)


def test_two_comparison_refs_are_refused() -> None:
    with pytest.raises(ChangeDerivationError) as excinfo:
        _validate_operand_cardinality(("obs:c", "obs:c2"))
    assert MULTI_COMPARISON_MEASUREMENT_SET_NOT_AUTHORIZED in str(excinfo.value)


def test_three_comparison_refs_are_refused() -> None:
    with pytest.raises(ChangeDerivationError) as excinfo:
        _validate_operand_cardinality(("obs:c", "obs:c2", "obs:c3"))
    assert MULTI_COMPARISON_MEASUREMENT_SET_NOT_AUTHORIZED in str(excinfo.value)


def test_caller_order_cannot_select_a_comparison_operand() -> None:
    """There is no parameter to order, and the stamp is the engine's own."""

    params = set(inspect.signature(derive_change_observation).parameters)
    for banned in (
        "comparison_measurement_refs", "comparison_refs", "refs",
        "candidates", "comparison_candidates", "comparison_set", "comparison",
    ):
        assert banned not in params, f"{banned} must not be a parameter"
    engine = _populated_engine()
    a = _derive(engine)
    b = _derive(engine)
    assert a.comparison_measurement_refs == b.comparison_measurement_refs == ("obs:c",)


# -- 6-10. absolute delta, stored binary64 -----------------------------------


def test_absolute_increase() -> None:
    engine = _populated_engine()
    record = _derive(engine)
    _expect(record.absolute_delta, 7.5 - 3.0)
    assert record.absolute_delta == 4.5
    assert record.change_kind is ChangeKind.INCREASE
    assert record.selected_baseline_measurement_ref == "obs:b"


def test_absolute_decrease() -> None:
    engine2 = _engine()
    register_measurement(engine2, _obs("obs:c", day=10, value=2.0, cov_ref="obs:c"))
    register_measurement(engine2, _obs("obs:b", day=0, value=5.0))
    engine2.registry.register_coverage(_coverage_obs("obs:c"))
    record = _derive(engine2)
    _expect(record.absolute_delta, 2.0 - 5.0)
    assert record.absolute_delta == -3.0
    assert record.change_kind is ChangeKind.DECREASE


def test_exact_equality_is_no_change() -> None:
    engine = _engine()
    register_measurement(engine, _obs("obs:c", day=10, value=5.0, cov_ref="obs:c"))
    register_measurement(engine, _obs("obs:b", day=0, value=5.0))
    engine.registry.register_coverage(_coverage_obs("obs:c"))
    record = _derive(engine)
    assert record.absolute_delta == 0.0
    assert record.change_kind is ChangeKind.NO_CHANGE


def test_stored_binary64_semantics_0_1_plus_0_2_vs_0_3() -> None:
    """No epsilon, no tolerance: the stored binary64 subtraction IS the answer."""

    engine = _engine()
    register_measurement(
        engine, _obs("obs:c", day=10, value=0.1 + 0.2, cov_ref="obs:c")
    )
    register_measurement(engine, _obs("obs:b", day=0, value=0.3))
    engine.registry.register_coverage(_coverage_obs("obs:c"))
    record = _derive(engine)
    expected = (0.1 + 0.2) - 0.3
    assert record.absolute_delta == expected          # stored binary64 exactly
    assert record.absolute_delta == 0.30000000000000004 - 0.3
    assert record.absolute_delta != 0.0               # and it is NOT "no change"
    assert record.change_kind is ChangeKind.INCREASE  # sign of the unrounded delta


def test_signed_zero_in_both_directions_is_no_change() -> None:
    for c_value, b_value in ((0.0, -0.0), (-0.0, 0.0)):
        engine = _engine()
        register_measurement(
            engine, _obs("obs:c", day=10, value=c_value, cov_ref="obs:c")
        )
        register_measurement(engine, _obs("obs:b", day=0, value=b_value))
        engine.registry.register_coverage(_coverage_obs("obs:c"))
        record = _derive(engine)
        assert record.absolute_delta == 0.0  # +0.0 == -0.0 under IEEE-754
        assert record.change_kind is ChangeKind.NO_CHANGE


# -- 11-14. relative delta and the zero-baseline law --------------------------


def test_relative_positive() -> None:
    engine = _populated_engine()
    rule = _relative_rule()
    record = _derive(engine, rule=rule, rules_registry=_rules_registry(rule))
    _expect(record.relative_delta, (7.5 - 3.0) / 3.0)
    assert record.relative_delta == 1.5
    assert record.change_kind is ChangeKind.INCREASE


def test_relative_negative() -> None:
    engine = _engine()
    register_measurement(engine, _obs("obs:c", day=10, value=2.0, cov_ref="obs:c"))
    register_measurement(engine, _obs("obs:b", day=0, value=5.0))
    engine.registry.register_coverage(_coverage_obs("obs:c"))
    rule = _relative_rule()
    record = _derive(engine, rule=rule, rules_registry=_rules_registry(rule))
    _expect(record.relative_delta, (2.0 - 5.0) / 5.0)
    assert record.relative_delta == -0.6
    assert record.change_kind is ChangeKind.DECREASE


def test_zero_baseline_relative_is_change_undefined() -> None:
    """b == 0.0: relative delta is None, kind is CHANGE_UNDEFINED — never 0/inf/NaN."""

    engine = _engine()
    register_measurement(engine, _obs("obs:c", day=10, value=7.5, cov_ref="obs:c"))
    register_measurement(engine, _obs("obs:b", day=0, value=0.0))
    engine.registry.register_coverage(_coverage_obs("obs:c"))
    rule = _relative_rule()
    record = _derive(engine, rule=rule, rules_registry=_rules_registry(rule))
    assert record.relative_delta is None
    assert record.change_kind is ChangeKind.CHANGE_UNDEFINED
    assert record.absolute_delta == 7.5  # the absolute delta still computed
    assert math.isfinite(record.absolute_delta)


def test_zero_baseline_absolute_still_computes() -> None:
    engine = _engine()
    register_measurement(engine, _obs("obs:c", day=10, value=7.5, cov_ref="obs:c"))
    register_measurement(engine, _obs("obs:b", day=0, value=0.0))
    engine.registry.register_coverage(_coverage_obs("obs:c"))
    record = _derive(engine)
    assert record.absolute_delta == 7.5
    assert record.change_kind is ChangeKind.INCREASE
    assert record.relative_delta is None  # ABSOLUTE_DELTA was requested


# -- 15-18. the non-finite firewall -------------------------------------------


@pytest.mark.parametrize("bad_value", [float("nan"), float("inf"), -float("inf")])
def test_non_finite_comparison_is_refused(bad_value) -> None:
    engine = _engine()
    register_measurement(
        engine, _obs("obs:c", day=10, value=bad_value, cov_ref="obs:c")
    )
    register_measurement(engine, _obs("obs:b", day=0, value=3.0))
    engine.registry.register_coverage(_coverage_obs("obs:c"))
    with pytest.raises(ChangeDerivationError) as excinfo:
        _derive(engine)
    assert OPERAND_NOT_FINITE_VALUE_BEARING in str(excinfo.value)
    assert "comparison" in str(excinfo.value)


def test_non_finite_baseline_is_refused() -> None:
    engine = _engine()
    register_measurement(engine, _obs("obs:c", day=10, value=7.5, cov_ref="obs:c"))
    register_measurement(engine, _obs("obs:b", day=0, value=float("nan")))
    engine.registry.register_coverage(_coverage_obs("obs:c"))
    with pytest.raises(ChangeDerivationError) as excinfo:
        _derive(engine)
    assert OPERAND_NOT_FINITE_VALUE_BEARING in str(excinfo.value)
    assert "baseline" in str(excinfo.value)


# -- 19-20. exact-unit and same-metric identity -------------------------------


def test_unit_mismatch_never_reaches_arithmetic() -> None:
    """GAP-2: same-metric exact-unit identity, enforced from the record model up."""

    engine = _engine()
    register_measurement(engine, _obs("obs:c", day=10, value=7.5, cov_ref="obs:c"))
    # a same-metric observation with a different unit contradicts its metric
    # definition and the accepted record model refuses the registration itself
    forged = windowed_observation(
        "obs:b", METRIC, value=3.0, missingness=MissingnessState.OBSERVED,
        claim_refs=(CLAIM_ID,), unit="bananas",
        window_class=WindowClass.INSTANTANEOUS, valid_time=_t(0),
    )
    with pytest.raises(MeasurementRecordError):
        register_measurement(engine, forged)


def test_metric_mismatch_never_reaches_arithmetic() -> None:
    """A cross-metric candidate cannot become the operand: the selector refuses."""

    engine = _engine(extra_definitions=True)
    register_measurement(engine, _obs("obs:c", day=10, value=7.5, cov_ref="obs:c"))
    register_measurement(engine, _obs("obs:b", day=0, value=3.0, metric=OTHER_METRIC))
    engine.registry.register_coverage(_coverage_obs("obs:c"))
    with pytest.raises(ChangeDerivationError) as excinfo:
        _derive(engine, baseline_measurement_refs=("obs:b",))
    # eligibility excludes it (METRIC_DEFINITION_MISMATCH) -> BASELINE_UNAVAILABLE
    assert BASELINE_UNAVAILABLE_AT_DERIVATION in str(excinfo.value)
    assert "no candidate satisfied" in str(excinfo.value)


# -- 21-22. the comparability firewall ----------------------------------------


def test_unresolved_comparability_never_reaches_arithmetic() -> None:
    """No coverage observation -> sealed UNRESOLVED -> INSUFFICIENT_DATA record."""

    engine = _populated_engine()
    sealed = _seal(coverage_observation="none")
    assert sealed.status.value == "UNRESOLVED"
    record = _derive(engine, comparability=sealed)
    assert record.comparability_status.value == "UNRESOLVED"
    assert record.change_kind is ChangeKind.INSUFFICIENT_DATA
    assert record.absolute_delta is None and record.relative_delta is None
    assert record.selected_baseline_measurement_ref is None
    assert record.comparability_refusal_reasons  # producing gates are recorded
    # the structured authorization is what populated the record
    assert record.coverage_verdict.value == "UNKNOWN"
    assert record.coverage_observation_state.value == "UNAVAILABLE"
    assert record.coverage_observation_ref is None


def test_not_comparable_never_reaches_arithmetic() -> None:
    """An INSUFFICIENT determination is a decision -> sealed NOT_COMPARABLE."""

    engine = _populated_engine()
    sealed = _seal(coverage_observation=_coverage_obs("obs:c", fraction=0.5))
    assert sealed.status.value == "NOT_COMPARABLE"
    record = _derive(engine, comparability=sealed)
    assert record.comparability_status.value == "NOT_COMPARABLE"
    assert record.change_kind is ChangeKind.NOT_COMPARABLE
    assert record.absolute_delta is None and record.relative_delta is None
    assert record.selected_baseline_measurement_ref is None
    assert record.comparability_refusal_reasons
    assert record.coverage_verdict.value == "INSUFFICIENT"
    assert record.coverage_observation_state.value == "PRESENT"
    assert record.coverage_observation_ref == "obs:c"


# -- BASELINE AUTHORITY (erratum §1/§7-A) -------------------------------------


def test_caller_cannot_provide_selected_baseline_ref() -> None:
    """Grammar v0.6 §3.2: the derivation API has no selected_baseline_ref."""

    params = set(inspect.signature(derive_change_observation).parameters)
    for banned in (
        "selected_baseline_ref", "baseline_selector_result", "baseline_is_valid",
    ):
        assert banned not in params, f"{banned} must not be a parameter"


def test_outsider_cannot_become_the_selected_baseline() -> None:
    """A current observation outside the candidate set cannot be the operand."""

    engine = _candidate_engine()
    record = _derive(
        engine, baseline_measurement_refs=("obs:a", "obs:b3"),
    )
    # the selector's answer, not any caller preference: A (day 5) beats B (day 3)
    assert record.selected_baseline_measurement_ref == "obs:a"
    assert record.absolute_delta == 7.5 - 1.0
    assert record.source_measurement_refs == ("obs:c", "obs:a")
    # and the outsider never appears anywhere on the record
    assert "obs:outsider" not in record.source_measurement_refs
    assert "obs:outsider" not in record.baseline_measurement_refs


def test_caller_cannot_force_b_when_the_selector_selects_a() -> None:
    """The candidate SET is the caller's only influence; ordering is the engine's."""

    engine = _candidate_engine()
    # the same candidate set, supplied in the opposite order, yields the SAME
    # selected baseline: caller order cannot reorder the engine's derivation
    r1 = _derive(engine, baseline_measurement_refs=("obs:a", "obs:b3"),
                 change_observation_id="chg:o1")
    r2 = _derive(engine, baseline_measurement_refs=("obs:b3", "obs:a"),
                 change_observation_id="chg:o2")
    assert r1.selected_baseline_measurement_ref == "obs:a"
    assert r2.selected_baseline_measurement_ref == "obs:a"
    assert r1.absolute_delta == 6.5
    assert r2.absolute_delta == 6.5


def test_candidate_ordering_does_not_change_the_result() -> None:
    """The selector's total key makes the DERIVATION independent of caller order.

    The record stores the candidate refs as supplied — a replay record of the
    caller's input, not a derived output — but every derived field (selection,
    deltas, kind) is identical, and the recorded SET is the same.
    """

    engine = _candidate_engine()
    forward = _derive(engine, baseline_measurement_refs=("obs:a", "obs:b3"))
    reverse = _derive(engine, baseline_measurement_refs=("obs:b3", "obs:a"))
    f, r = forward.model_dump(), reverse.model_dump()
    f["baseline_measurement_refs"], r["baseline_measurement_refs"] = None, None
    assert f == r  # every derived field is order-independent
    assert set(forward.baseline_measurement_refs) == (
        set(reverse.baseline_measurement_refs)
    )
    assert forward.selected_baseline_measurement_ref == "obs:a"
    assert reverse.selected_baseline_measurement_ref == "obs:a"


def test_selected_baseline_is_always_in_the_candidate_set() -> None:
    """The engine-derived selection is provably a member of the supplied set."""

    engine = _candidate_engine()
    record = _derive(engine, baseline_measurement_refs=("obs:a", "obs:b3"))
    assert record.selected_baseline_measurement_ref in {"obs:a", "obs:b3"}
    assert record.selected_baseline_measurement_ref == "obs:a"


def test_unknown_candidate_fails_closed() -> None:
    """A dangling candidate ref refuses the whole set: no pruning, no substitute."""

    engine = _candidate_engine()
    with pytest.raises(ChangeDerivationError) as excinfo:
        _derive(engine, baseline_measurement_refs=("obs:a", "obs:ghost"))
    assert BASELINE_CANDIDATE_REF_UNRESOLVED in str(excinfo.value)
    # the refusal names the dangling ref and substitutes nothing
    assert "obs:ghost" in str(excinfo.value)
    # and an unknown ref is refused even when a viable candidate exists


def test_unknown_candidate_is_refused_even_alongside_a_viable_one() -> None:
    engine = _candidate_engine()
    with pytest.raises(ChangeDerivationError) as excinfo:
        _derive(engine, baseline_measurement_refs=("obs:b3", "obs:ghost"))
    assert BASELINE_CANDIDATE_REF_UNRESOLVED in str(excinfo.value)
    # unregistered (as opposed to dangling) refs fail the same way
    with pytest.raises(Book6RegistryError):
        engine.registry.registered_measurement("obs:never-registered")
    with pytest.raises(ChangeDerivationError) as excinfo2:
        _derive(engine, baseline_measurement_refs=("obs:never-registered",))
    assert BASELINE_CANDIDATE_REF_UNRESOLVED in str(excinfo2.value)


def test_rung8_selector_result_equals_direct_rung6_selector_result() -> None:
    """SELECTOR_IMPLEMENTATIONS = 1: Rung 8 replays the SAME Rung 6 function."""

    engine = _candidate_engine()
    rule = _rule()
    comparison = engine.registry.resolve_current("obs:c")
    candidates = tuple(
        engine.registry.registered_measurement(ref)
        for ref in ("obs:a", "obs:b3")
    )
    direct = select_baseline(
        comparison=comparison,
        candidates=candidates,
        rule=rule,
        semantic_fingerprint_of=_fp,
        is_current=engine.registry.is_authoritative_now,
    )
    assert direct.outcome is BaselineOutcome.RESOLVED
    record = _derive(
        engine, rule=rule, rules_registry=_rules_registry(rule),
        baseline_measurement_refs=("obs:a", "obs:b3"),
    )
    assert record.selected_baseline_measurement_ref == "obs:a"
    assert direct.selected_measurement_ref == "obs:a"


def test_coverage_never_influences_baseline_selection() -> None:
    """The selector reads no coverage state; the sealed verdict rides alongside."""

    engine = _candidate_engine()
    # candidate obs:a cites coverage, obs:b3 cites none; selection ignores it
    covered = engine.registry.registered_measurement("obs:a").model_copy(
        update={"coverage_observation_id": "cov:obs-a"}
    )
    # re-registering is refused, so prove the point differently: the same
    # candidate set with a coverage-citing candidate yields the same selection
    # as the direct selector run over the same records
    direct = select_baseline(
        comparison=engine.registry.resolve_current("obs:c"),
        candidates=tuple(engine.registry.registered_measurement(r) for r in ("obs:a", "obs:b3")),
        rule=_rule(),
        semantic_fingerprint_of=_fp,
        is_current=engine.registry.is_authoritative_now,
    )
    record = _derive(engine, baseline_measurement_refs=("obs:a", "obs:b3"))
    assert direct.selected_measurement_ref == record.selected_baseline_measurement_ref
    # and a live INSUFFICIENT coverage state under the SAME sealed verdict does
    # not move the selection either (consumption, not recomputation)
    sealed = _seal()
    engine_b = _candidate_engine(live_fraction=0.5)
    r1 = _derive(engine, comparability=sealed, baseline_measurement_refs=("obs:a", "obs:b3"))
    r2 = _derive(engine_b, comparability=sealed, baseline_measurement_refs=("obs:a", "obs:b3"))
    assert r1.selected_baseline_measurement_ref == r2.selected_baseline_measurement_ref
    del covered


# -- STRUCTURED COVERAGE (erratum §2/§7-B) ------------------------------------


def test_reason_wording_cannot_change_the_coverage_verdict() -> None:
    """Rewriting diagnostic prose (only) changes nothing in the derivation."""

    engine = _candidate_engine()

    def reword(reason: str) -> str:
        return reason.replace("-> SUFFICIENT", "deterministically sufficient")

    plain = _derive(engine, baseline_measurement_refs=("obs:a", "obs:b3"),
                    change_observation_id="chg:same")
    reworded_seal = _seal(mutate_reasons=reword)
    assert reworded_seal.status is plain.comparability_status
    assert reworded_seal.coverage.verdict.value == "SUFFICIENT"
    altered = derive_change_observation(
        comparison_measurement_ref="obs:c",
        baseline_measurement_refs=("obs:a", "obs:b3"),
        rule=_rule(),
        registry=engine.registry,
        comparison_rules_registry=_rules_registry(_rule()),
        semantic_fingerprint_of=_fp,
        comparability=reworded_seal,
        change_observation_id="chg:same",
        derivation_binding_ref="binding:1",
    )
    assert altered == plain  # record-identical under prose-only mutation


def test_reason_wording_cannot_change_the_requirement_status() -> None:
    """Requirement status is a structured field; check 12's prose is not."""

    engine = _candidate_engine()

    def reword(reason: str) -> str:
        return reason.replace("coverage is REQUIRED", "coverage is deemed needed")

    sealed = _seal(mutate_reasons=reword)
    assert sealed.coverage.applicability.requirement_status is (
        CoverageRequirementStatus.REQUIRED
    )
    record = _derive(engine, comparability=sealed)
    assert record.coverage_requirement_status is CoverageRequirementStatus.REQUIRED
    assert record.coverage_applicability_source_ref == COV_SOURCE


def test_rung8_reads_no_reason_string_for_semantic_decisions() -> None:
    """The module imports no reason fragment as authority and has no prose parser."""

    import crypto_systems_intelligence_atlas.book6_comparison_change_derivation as mod

    source = inspect.getsource(mod)
    for fragment in ("-> SUFFICIENT", "-> INSUFFICIENT", "coverage is REQUIRED"):
        assert fragment not in source, f"prose fragment treated as authority: {fragment}"
    # the deliberate refusal of a prose fallback is itself asserted
    assert "STRUCTURED_COVERAGE_RESULT_REQUIRED" in source


def test_sealed_verdict_without_structured_coverage_cannot_drive_arithmetic() -> None:
    """No structured authorization -> fail closed; prose is never a fallback."""

    engine = _candidate_engine()
    sealed = _seal()
    stripped = replace(sealed, coverage=None)  # the historical hand-built shape
    with pytest.raises(ChangeDerivationError) as excinfo:
        _derive(engine, comparability=stripped,
                baseline_measurement_refs=("obs:a", "obs:b3"))
    assert STRUCTURED_COVERAGE_RESULT_REQUIRED in str(excinfo.value)
    # and the refusal path fails closed the same way — no prose reconstruction
    unresolved = _seal(coverage_observation="none")
    with pytest.raises(ChangeDerivationError) as excinfo2:
        _derive(engine, comparability=replace(unresolved, coverage=None))
    assert STRUCTURED_COVERAGE_RESULT_REQUIRED in str(excinfo2.value)


def test_sufficient_structured_verdict_persists() -> None:
    engine = _candidate_engine()
    record = _derive(engine, baseline_measurement_refs=("obs:a", "obs:b3"))
    assert record.coverage_verdict.value == "SUFFICIENT"
    assert record.coverage_observation_state.value == "PRESENT"
    assert record.coverage_observation_ref == "obs:c"
    assert record.coverage_requirement_status is CoverageRequirementStatus.REQUIRED


def test_insufficient_structured_verdict_persists() -> None:
    engine = _candidate_engine()
    sealed = _seal(coverage_observation=_coverage_obs("obs:c", fraction=0.5))
    record = _derive(engine, comparability=sealed,
                     baseline_measurement_refs=("obs:a", "obs:b3"))
    assert record.coverage_verdict.value == "INSUFFICIENT"
    assert record.change_kind is ChangeKind.NOT_COMPARABLE


def test_unknown_structured_verdict_persists() -> None:
    engine = _candidate_engine()
    sealed = _seal(coverage_observation="none")
    record = _derive(engine, comparability=sealed,
                     baseline_measurement_refs=("obs:a", "obs:b3"))
    assert record.coverage_verdict.value == "UNKNOWN"
    assert record.coverage_observation_state.value == "UNAVAILABLE"
    assert record.change_kind is ChangeKind.INSUFFICIENT_DATA


def test_replaycheck_reasons_remain_present_for_diagnostics() -> None:
    """Structured consumption does not delete the check-by-check record."""

    sealed = _seal()
    assert len(sealed.coverage_checks) == 5  # checks 12-16, all present
    assert all(c.reason for c in sealed.coverage_checks)
    assert sealed.check_19.reason
    # and they stay individually falsifiable on the refusal record
    engine = _candidate_engine()
    failing = _seal(coverage_observation=_coverage_obs("obs:c", fraction=0.5))
    record = _derive(engine, comparability=failing,
                     baseline_measurement_refs=("obs:a", "obs:b3"))
    numbers = {tag for tag, _ in record.comparability_refusal_reasons}
    # check 16 PASSED here — recomputing INSUFFICIENT is a successful replay —
    # so the producing gate is check 19, the decision itself (Rung 7's law)
    assert "check:19" in numbers
    assert record.comparability_refusal_reasons


# -- RULE METRIC BINDING / CANONICAL OBJECT (erratum §3/§7-C/D) ----------------


def test_rule_metric_b_with_metric_a_operands_is_refused() -> None:
    """The rule's own metric binding is exact: a rule for B cannot govern A."""

    engine = _candidate_engine()
    rule_b = _rule(metric_definition_ref=OTHER_METRIC)
    with pytest.raises(ChangeDerivationError) as excinfo:
        _derive(
            engine, rule=rule_b, rules_registry=_rules_registry(rule_b),
            baseline_measurement_refs=("obs:a", "obs:b3"),
        )
    text = str(excinfo.value)
    assert OTHER_METRIC in text and METRIC in text
    assert "exact rule metric binding" in text


def test_baseline_metric_differs_from_rule_metric_is_refused() -> None:
    """Three-way binding: comparison == rule but baseline metric differs -> refused."""

    engine = _engine(extra_definitions=True)
    register_measurement(engine, _obs("obs:c", day=10, value=7.5, cov_ref="obs:c"))
    # a same-subject candidate measuring another metric: eligible on nothing,
    # but prove the engine's own binding gate regardless of selector outcome
    register_measurement(engine, _obs("obs:bm", day=0, value=3.0, metric=OTHER_METRIC))
    with pytest.raises(ChangeDerivationError) as excinfo:
        _derive(engine, baseline_measurement_refs=("obs:bm",))
    assert (
        BASELINE_UNAVAILABLE_AT_DERIVATION in str(excinfo.value)
        or "exact rule metric" in str(excinfo.value)
    )


def test_all_three_metric_refs_equal_is_the_positive_path() -> None:
    engine = _candidate_engine()
    record = _derive(engine, baseline_measurement_refs=("obs:a", "obs:b3"))
    assert record.metric_definition_ref == METRIC
    assert engine.registry.resolve_current("obs:c").metric_definition_ref == METRIC
    assert engine.registry.resolve_current(
        record.selected_baseline_measurement_ref
    ).metric_definition_ref == METRIC
    assert _rule().metric_definition_ref == METRIC


def test_mutated_caller_comparison_object_has_no_authority_channel() -> None:
    """The API takes a ref; a mutated copy has nothing to mutate."""

    engine = _candidate_engine()
    canonical = engine.registry.resolve_current("obs:c")
    mutated = canonical.model_copy(update={
        "subject_ref": "subject:EVIL",
        "metric_definition_ref": OTHER_METRIC,
        "coverage_observation_id": "cov:evil",
    })
    # there is no object parameter to pass it through
    params = set(inspect.signature(derive_change_observation).parameters)
    assert "comparison" not in params and "comparison_observation" not in params
    # derivation goes through the REF; every field is the registry's answer
    record = _derive(engine, baseline_measurement_refs=("obs:a", "obs:b3"))
    assert record.subject_ref == canonical.subject_ref
    assert record.metric_definition_ref == METRIC
    assert record.coverage_observation_ref == "obs:c"
    del mutated


def test_refusal_record_uses_canonical_registered_comparison() -> None:
    """UNRESOLVED refusals are built from the registry, not the caller's copy."""

    engine = _candidate_engine()
    canonical = engine.registry.resolve_current("obs:c")
    mutated = canonical.model_copy(update={"subject_ref": "subject:EVIL"})
    sealed = _seal(coverage_observation="none")
    record = _derive(engine, comparability=sealed,
                     baseline_measurement_refs=("obs:a", "obs:b3"))
    assert record.subject_ref == canonical.subject_ref
    assert record.subject_ref != "subject:EVIL"
    assert record.metric_definition_ref == canonical.metric_definition_ref
    assert record.unit == canonical.unit
    assert record.valid_time == canonical.valid_time
    del mutated


def test_not_comparable_refusal_record_uses_canonical_registered_comparison() -> None:
    engine = _candidate_engine()
    canonical = engine.registry.resolve_current("obs:c")
    mutated = canonical.model_copy(update={
        "metric_definition_ref": OTHER_METRIC,
        "coverage_observation_id": "cov:evil",
    })
    sealed = _seal(coverage_observation=_coverage_obs("obs:c", fraction=0.5))
    record = _derive(engine, comparability=sealed,
                     baseline_measurement_refs=("obs:a", "obs:b3"))
    assert record.metric_definition_ref == canonical.metric_definition_ref == METRIC
    assert record.coverage_observation_ref == canonical.coverage_observation_id
    assert record.subject_ref == canonical.subject_ref
    del mutated


def test_methodology_identity_derives_from_the_canonical_record() -> None:
    engine = _candidate_engine()
    record = _derive(engine, baseline_measurement_refs=("obs:a", "obs:b3"))
    canonical = engine.registry.resolve_current("obs:c")
    assert record.measurement_methodology_refs[0] == canonical.methodology_identity
    baseline = engine.registry.resolve_current(
        record.selected_baseline_measurement_ref
    )
    assert record.measurement_methodology_refs[1] == baseline.methodology_identity


# -- COMPARABLE-baseline-unavailable, candidate currency -----------------------


def test_comparable_with_no_eligible_baseline_fails_closed() -> None:
    """BASELINE_UNAVAILABLE on a COMPARABLE verdict is a fault, not a record."""

    engine = _populated_engine()
    # the only candidate is NOT strictly prior -> BASELINE_UNAVAILABLE
    with pytest.raises(ChangeDerivationError) as excinfo:
        _derive(engine, baseline_measurement_refs=("obs:c",))
    assert BASELINE_UNAVAILABLE_AT_DERIVATION in str(excinfo.value)
    # and no placeholder baseline ref is ever invented
    assert "placeholder" in str(excinfo.value).lower() or "substitution" in (
        str(excinfo.value)
    )


def test_superseded_candidate_is_excluded_by_the_selector_gate() -> None:
    """A superseded predecessor is excluded (NOT_CURRENT), never selected."""

    engine = _populated_engine()
    register_measurement(engine, _obs("obs:b2", day=1, value=3.0, supersedes="obs:b"))
    # obs:b is now superseded: as a candidate it is excluded, and as the sole
    # candidate its exclusion leaves BASELINE_UNAVAILABLE
    with pytest.raises(ChangeDerivationError) as excinfo:
        _derive(engine, baseline_measurement_refs=("obs:b",))
    assert BASELINE_UNAVAILABLE_AT_DERIVATION in str(excinfo.value)
    assert "NOT_CURRENT" in str(excinfo.value)


# -- sealed-consumption and caller-authority walls (regression) ----------------


def test_coverage_result_is_consumed_not_recomputed() -> None:
    """Two engines, one sealed verdict: the recorded verdict is the SEALED one."""

    sealed = _seal()  # SUFFICIENT, sealed from a 0.95 observation
    engine_a = _candidate_engine()
    record_a = _derive(engine_a, comparability=sealed,
                       baseline_measurement_refs=("obs:a", "obs:b3"))

    # engine_b's live coverage state is INSUFFICIENT (0.5), but the SAME sealed
    # verdict is handed to the engine. If the engine recomputed, b would differ.
    engine_b = _candidate_engine(live_fraction=0.5)
    record_b = _derive(engine_b, comparability=sealed,
                       baseline_measurement_refs=("obs:a", "obs:b3"))
    assert record_a.coverage_verdict.value == "SUFFICIENT"
    assert record_b.coverage_verdict.value == "SUFFICIENT"
    assert record_b.absolute_delta == 6.5
    assert record_a.absolute_delta == 6.5


def test_selected_baseline_is_engine_derived() -> None:
    """The selected ref is resolved live; a superseded selection is refused."""

    engine = _populated_engine()
    record = _derive(engine)
    assert record.selected_baseline_measurement_ref == "obs:b"
    assert "obs:b" in record.source_measurement_refs
    assert "obs:b" in record.baseline_measurement_refs

    # a superseded baseline cannot even be selected: the selector's live
    # currentness gate excludes it before ordering (stronger than the old
    # resolve-time refusal, because the exclusion is auditable)
    engine2 = _populated_engine()
    register_measurement(engine2, _obs("obs:b2", day=1, value=3.0, supersedes="obs:b"))
    with pytest.raises(ChangeDerivationError) as excinfo:
        _derive(engine2)
    assert BASELINE_UNAVAILABLE_AT_DERIVATION in str(excinfo.value)
    assert "NOT_CURRENT" in str(excinfo.value)


def test_caller_cannot_author_deltas() -> None:
    """The signature has no delta parameter; the engine's result is cross-checked."""

    params = set(inspect.signature(derive_change_observation).parameters)
    for banned in (
        "absolute_delta", "relative_delta", "expected_absolute_delta",
        "expected_relative_delta", "deltas",
    ):
        assert banned not in params, f"{banned} must not be a parameter"
    engine = _populated_engine()
    record = _derive(engine)
    _expect(record.absolute_delta, 4.5)      # the cross-check agrees
    with pytest.raises(AssertionError):
        _expect(record.absolute_delta, 99.0)  # a mismatch raises — never overrides


def test_caller_cannot_author_change_kind() -> None:
    """Direction is the engine's derivation from the canonical unrounded sign."""

    params = set(inspect.signature(derive_change_observation).parameters)
    for banned in ("change_kind", "kind", "expected_change_kind"):
        assert banned not in params, f"{banned} must not be a parameter"
    engine = _populated_engine()
    record = _derive(engine)
    _expect(record.change_kind, ChangeKind.INCREASE)
    with pytest.raises(AssertionError):
        _expect(record.change_kind, ChangeKind.DECREASE)


def test_display_metadata_cannot_alter_arithmetic() -> None:
    """Two rules identical except display_metadata derive identical deltas."""

    engine = _populated_engine()
    plain = _rule()
    decorated = _rule(
        comparison_rule_id="cmp:2",
        display_metadata={"rounding": 2, "epsilon": 0.5, "label": "x"},
    )
    a = _derive(engine, rule=plain, rules_registry=_rules_registry(plain))
    b = _derive(
        engine, rule=decorated, rules_registry=_rules_registry(plain, decorated),
        change_observation_id="chg:2",
    )
    assert a.absolute_delta == b.absolute_delta == 4.5
    assert a.change_kind is b.change_kind
    from crypto_systems_intelligence_atlas.book6_comparison_registry import (
        comparison_rule_fingerprint,
    )
    assert comparison_rule_fingerprint(plain) == comparison_rule_fingerprint(
        plain.model_copy(update={"display_metadata": {"epsilon": 99}})
    )


def test_rule_without_live_authority_is_refused() -> None:
    """Registration is not authority: an unratified rule cannot drive arithmetic."""

    engine = _populated_engine()
    rule = _rule()
    unratified = ComparisonRuleRegistry()
    unratified.register_rule(rule)
    with pytest.raises(ChangeDerivationError) as excinfo:
        _derive(engine, rule=rule, rules_registry=unratified)
    assert "does not hold authority" in str(excinfo.value)


def test_invalidated_rule_is_refused() -> None:
    engine = _populated_engine()
    rule = _rule()
    reg = _rules_registry(rule)
    reg.invalidate_rule(
        reg.current_identity(rule.comparison_rule_id), reason="operator withdrawal"
    )
    with pytest.raises(ChangeDerivationError) as excinfo:
        _derive(engine, rule=rule, rules_registry=reg)
    assert "does not hold authority" in str(excinfo.value)


def test_superseded_comparison_operand_is_refused() -> None:
    """The comparison operand is currentness-checked too, not only the baseline."""

    engine = _populated_engine()
    # keep the comparison ref, then take its successor; the engine's own live
    # resolution must do the refusing — the caller passed only the identity
    register_measurement(engine, _obs("obs:c2", day=11, value=7.5, supersedes="obs:c"))
    with pytest.raises(ChangeDerivationError) as excinfo:
        _derive(engine, comparison="obs:c")
    assert OPERAND_NOT_CURRENT in str(excinfo.value)


def test_comparable_with_unknown_sealed_verdict_is_refused() -> None:
    """The engine enforces COMPARABLE <=> sealed SUFFICIENT on structured fields."""

    engine = _candidate_engine()
    sealed = _seal()
    broken = replace(
        sealed,
        coverage=replace(sealed.coverage, verdict=__import__(
            "crypto_systems_intelligence_atlas.book6_comparison_contracts",
            fromlist=["CoverageVerdict"]).CoverageVerdict.UNKNOWN),
    )
    with pytest.raises(ChangeDerivationError) as excinfo:
        _derive(engine, comparability=broken,
                baseline_measurement_refs=("obs:a", "obs:b3"))
    assert "did not recompute SUFFICIENT" in str(excinfo.value)


def test_sealed_applicability_must_agree_with_the_governing_rule() -> None:
    """A rule declaring UNRESOLVED coverage cannot ride a REQUIRED sealed replay."""

    engine = _candidate_engine()
    rule = _rule(coverage_requirement_status=CoverageRequirementStatus.UNRESOLVED)
    with pytest.raises(ChangeDerivationError) as excinfo:
        _derive(engine, rule=rule, rules_registry=_rules_registry(rule),
                baseline_measurement_refs=("obs:a", "obs:b3"))
    assert "disagrees with itself" in str(excinfo.value)


def test_sufficient_coverage_without_cited_observation_ref_is_refused() -> None:
    """A sealed SUFFICIENT whose authorization names no observation ref is refused."""

    engine = _candidate_engine()
    sealed = _seal()
    refless = replace(sealed, coverage=replace(sealed.coverage, observation_ref=None))
    with pytest.raises(ChangeDerivationError) as excinfo:
        _derive(engine, comparability=refless,
                baseline_measurement_refs=("obs:a", "obs:b3"))
    assert "observation ref" in str(excinfo.value)


def test_refusal_record_requires_baseline_candidates_to_record() -> None:
    """A refusal record still carries the candidate set; an empty one cannot."""

    engine = _candidate_engine()
    sealed = _seal(coverage_observation="none")
    with pytest.raises(ChangeDerivationError) as excinfo:
        _derive(engine, comparability=sealed, baseline_measurement_refs=())
    assert "candidate" in str(excinfo.value)


# -- no aggregation surface ----------------------------------------------------


def test_no_aggregation_path_exists() -> None:
    """No comparison-side selector, reducer or aggregation exists in the module."""

    import crypto_systems_intelligence_atlas.book6_comparison_change_derivation as mod

    forbidden_name_parts = (
        "aggregate", "aggregation", "reduce", "reducer", "mean", "median",
        "sum", "average", "pick_first", "pick_last", "tie_break",
        "select_comparison", "comparison_selector",
    )
    for name, obj in vars(mod).items():
        if callable(obj) and getattr(obj, "__module__", None) == mod.__name__:
            lowered = name.lower()
            for part in forbidden_name_parts:
                assert part not in lowered, f"forbidden aggregation surface: {name}"
    params = set(inspect.signature(derive_change_observation).parameters)
    for banned in (
        "comparisons", "comparison_set", "comparison_candidates", "refs",
        "aggregation", "reducer",
    ):
        assert banned not in params
    # every non-one count is refused as a set
    for count in (0, 2, 3, 7):
        with pytest.raises(ChangeDerivationError) as excinfo:
            _validate_operand_cardinality(tuple(f"m{i}" for i in range(count)))
        assert MULTI_COMPARISON_MEASUREMENT_SET_NOT_AUTHORIZED in str(excinfo.value)


# -- SEALED BUNDLE IDENTITY AGREEMENT (identity sealing erratum v0.1) --------
#
# Status agreement alone proves nothing: a sealed REQUIRED verdict derived for
# another measurement, metric or coverage rule carries the same status. The
# engine verifies the sealed authorization's identity seal field by field
# before trusting the bundle — same status, different authority bundle, is a
# substitution and is refused.


def test_rung8_refuses_sealed_result_from_another_measurement() -> None:
    """The AUTH-B reproducer: an honest foreign bundle cannot drive arithmetic."""

    engine = _engine(extra_definitions=True)
    register_measurement(engine, _obs("obs:c", day=10, value=7.5, cov_ref="obs:c"))
    register_measurement(engine, _obs("obs:b", day=0, value=3.0))
    engine.registry.register_coverage(_coverage_obs("obs:c"))
    # an honest sealed bundle for ANOTHER measurement, metric and rule
    foreign_engine = _engine(extra_definitions=True)
    foreign_reg = foreign_engine.registry
    foreign_reg.coverage_rules.register(
        CoverageSufficiencyRule(
            rule_id="cov:foreign", version="1", required_fraction=0.9,
            scope_metric_id=OTHER_METRIC,
            rationale="foreign coverage floor",
        )
    )
    foreign_reg.coverage_rules.ratify(
        "cov:foreign", operator="operator:1", at=NOW)
    register_measurement(
        foreign_engine,
        _obs("obs:b", day=10, value=9.9, metric=OTHER_METRIC, cov_ref="obs:b"))
    foreign_reg.register_coverage(
        _coverage_obs("obs:b").model_copy(update={"sufficiency_rule_ref": "cov:foreign"}))
    foreign_auth = replay_coverage_checks(
        measurement_registry=foreign_reg,
        comparison_measurement_ref="obs:b",
        named_rule_ref="cov:foreign",
    )
    foreign_rule = _rule(
        metric_definition_ref=OTHER_METRIC,
        comparison_rule_id="cmp:foreign",
        coverage_applicability_source_ref=f"exact-metric:{OTHER_METRIC}:1",
        coverage_sufficiency_rule_ref="cov:foreign",
    )
    foreign_verdict = derive_temporal_comparability(
        coverage=foreign_auth, structural_checks=_STRUCTURAL_PASSED)
    assert foreign_verdict.status.value == "COMPARABLE"
    with pytest.raises(ChangeDerivationError) as excinfo:
        _derive(
            engine, comparability=foreign_verdict, rule=foreign_rule,
            rules_registry=_rules_registry(foreign_rule),
            baseline_measurement_refs=("obs:b",),
        )
    text = str(excinfo.value)
    assert "obs:b" in text and "obs:c" in text
    assert "substitution" in text


def test_rung8_refuses_sealed_result_from_another_metric() -> None:
    """A sealed bundle claiming another metric is refused before arithmetic."""

    engine = _candidate_engine()
    sealed = _seal()
    relabeled = replace(
        sealed, coverage=replace(sealed.coverage, metric_id=OTHER_METRIC))
    with pytest.raises(ChangeDerivationError) as excinfo:
        _derive(engine, comparability=relabeled,
                baseline_measurement_refs=("obs:a", "obs:b3"))
    assert "another metric" in str(excinfo.value)
    assert OTHER_METRIC in str(excinfo.value)


def test_rung8_refuses_sealed_result_from_another_coverage_rule() -> None:
    """A sealed bundle derived under another rule is refused."""

    engine = _candidate_engine()
    sealed = _seal()
    foreign_rule_bundle = replace(
        sealed, coverage=replace(sealed.coverage, named_rule_ref="cov:other"))
    with pytest.raises(ChangeDerivationError) as excinfo:
        _derive(engine, comparability=foreign_rule_bundle,
                baseline_measurement_refs=("obs:a", "obs:b3"))
    assert "cov:other" in str(excinfo.value)
    assert "substitution" in str(excinfo.value)


def test_rung8_refuses_a_different_applicability_source_ref() -> None:
    """The upstream determination must be the one the operator recorded."""

    engine = _candidate_engine()
    sealed = _seal()
    relabeled = replace(
        sealed,
        coverage=replace(
            sealed.coverage,
            applicability=replace(
                sealed.coverage.applicability,
                source_ref="exact-metric:metric.tx:99",
            ),
        ),
    )
    with pytest.raises(ChangeDerivationError) as excinfo:
        _derive(engine, comparability=relabeled,
                baseline_measurement_refs=("obs:a", "obs:b3"))
    assert "exact-metric:metric.tx:99" in str(excinfo.value)
    assert COV_SOURCE in str(excinfo.value)


def test_same_required_status_alone_cannot_satisfy_bundle_agreement() -> None:
    """A4: status equality is necessary and provably insufficient.

    Every identity field is crossed with the honest bundle in turn — each
    mismatch is refused even though the requirement status matches throughout.
    """

    engine = _candidate_engine()
    sealed = _seal()
    assert sealed.coverage.applicability.requirement_status is (
        CoverageRequirementStatus.REQUIRED
    )
    mutations = (
        {"comparison_measurement_ref": "obs:elsewhere"},
        {"metric_id": OTHER_METRIC},
        {"named_rule_ref": "cov:other"},
        {"applicability": replace(
            sealed.coverage.applicability, source_ref="exact-metric:other:1")},
    )
    for kwargs in mutations:
        forged = replace(sealed, coverage=replace(sealed.coverage, **kwargs))
        with pytest.raises(ChangeDerivationError) as excinfo:
            _derive(engine, comparability=forged,
                    baseline_measurement_refs=("obs:a", "obs:b3"))
        assert "substitution" in str(excinfo.value) or "source" in str(
            excinfo.value), kwargs
    # the honest bundle still derives
    record = _derive(engine, comparability=sealed,
                     baseline_measurement_refs=("obs:a", "obs:b3"))
    assert record.absolute_delta == 6.5
