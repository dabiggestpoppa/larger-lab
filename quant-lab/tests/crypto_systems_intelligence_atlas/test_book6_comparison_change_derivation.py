"""Rung 8 — deterministic ChangeObservation arithmetic.

Discharges ``BOOK6-COMPARISON-OPERAND-CARDINALITY-v0.1``
(``RATIFY_ONE_COMPARISON_MEASUREMENT_PER_CHANGEOBSERVATION``) and the ratified
delta grammar (amendment ratification record v0.1 :84-97).

The laws under test:

    ONE_CHANGEOBSERVATION_ONE_COMPARISON_MEASUREMENT = TRUE
    absolute_delta = comparison_value - baseline_value      (stored binary64)
    relative_delta = (c - b) / b, UNDEFINED at b == 0
    direction from the sign of the canonical UNROUNDED delta
    non-finite operands never reach arithmetic
    the engine derives; the caller never authors

The negative cases matter more than the positive ones, exactly as in Rungs 6
and 7: an engine that computes the right delta under the wrong authority is
still wrong, and the two failure modes are only distinguishable if the fixture
makes them differ.
"""

from __future__ import annotations

import inspect
import math
from datetime import datetime, timedelta, timezone

import pytest

from crypto_systems_intelligence_atlas.book6_comparison_change_derivation import (
    AUTHORITATIVE_COMPARISON_MEASUREMENT_COUNT,
    MULTI_COMPARISON_MEASUREMENT_SET_NOT_AUTHORIZED,
    OPERAND_NOT_CURRENT,
    OPERAND_NOT_FINITE_VALUE_BEARING,
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
) -> ComparabilityVerdict:
    """A sealed Rung 7 result, produced by the REAL Rung 7 code path."""

    reg = _cov_registry(fraction=cov_fraction)
    obs = {"default": _coverage_obs(comparison_id), "none": None}.get(
        coverage_observation, coverage_observation
    )
    auth = replay_coverage_checks(
        registry=reg, metric_id=METRIC, named_rule_ref=COV_RULE,
        comparison_measurement_ref=comparison_id, coverage_observation=obs,
    )
    return derive_temporal_comparability(
        coverage=auth, structural_checks=_STRUCTURAL_PASSED
    )


def _populated_engine():
    """Engine with a current comparison (7.5) and baseline (3.0), coverage cited."""

    engine = _engine()
    register_measurement(engine, _obs("obs:c", day=10, value=7.5, cov_ref="obs:c"))
    register_measurement(engine, _obs("obs:b", day=0, value=3.0))
    engine.registry.register_coverage(_coverage_obs("obs:c"))
    return engine


def _derive(
    engine=None,
    *,
    comparison=None,
    rule=None,
    comparability=None,
    baseline_measurement_refs=("obs:b",),
    selected_baseline_ref="obs:b",
    rules_registry=None,
    change_observation_id="chg:1",
):
    comparison = comparison or "obs:c"
    if isinstance(comparison, str):
        comparison = engine.registry.resolve_current(comparison)
    return derive_change_observation(
        comparison=comparison,
        baseline_measurement_refs=baseline_measurement_refs,
        selected_baseline_ref=selected_baseline_ref,
        rule=rule or _rule(),
        registry=engine.registry,
        comparison_rules_registry=rules_registry or _rules_registry(_rule()),
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
    # and neither element was picked
    assert "obs:c" not in str(excinfo.value).split("requested")[1]


def test_three_comparison_refs_are_refused() -> None:
    with pytest.raises(ChangeDerivationError) as excinfo:
        _validate_operand_cardinality(("obs:c", "obs:c2", "obs:c3"))
    assert MULTI_COMPARISON_MEASUREMENT_SET_NOT_AUTHORIZED in str(excinfo.value)


def test_caller_order_cannot_select_a_comparison_operand() -> None:
    """There is no parameter to order, and the stamp is the engine's own."""

    params = set(inspect.signature(derive_change_observation).parameters)
    for banned in (
        "comparison_measurement_refs", "comparison_refs", "refs",
        "candidates", "comparison_candidates", "comparison_set",
    ):
        assert banned not in params, f"{banned} must not be a parameter"
    # the stamped set is the one observation the engine received, in both orders
    engine = _populated_engine()
    a = _derive(engine, comparison="obs:c")
    b = _derive(engine, comparison="obs:c")
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
    record = _derive(engine2, comparison="obs:c")
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
    record = _derive(
        engine, rule=rule, rules_registry=_rules_registry(rule),
        comparability=_seal(),
    )
    _expect(record.relative_delta, (7.5 - 3.0) / 3.0)
    assert record.relative_delta == 1.5
    assert record.change_kind is ChangeKind.INCREASE


def test_relative_negative() -> None:
    engine = _engine()
    register_measurement(engine, _obs("obs:c", day=10, value=2.0, cov_ref="obs:c"))
    register_measurement(engine, _obs("obs:b", day=0, value=5.0))
    engine.registry.register_coverage(_coverage_obs("obs:c"))
    rule = _relative_rule()
    record = _derive(
        engine, rule=rule, rules_registry=_rules_registry(rule)
    )
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
    # and a cross-metric unit difference is refused by the engine before any
    # arithmetic (see next test) — no path reaches the subtraction


def test_metric_mismatch_never_reaches_arithmetic() -> None:
    engine = _engine(extra_definitions=True)
    register_measurement(engine, _obs("obs:c", day=10, value=7.5, cov_ref="obs:c"))
    register_measurement(engine, _obs("obs:b", day=0, value=3.0, metric=OTHER_METRIC))
    engine.registry.register_coverage(_coverage_obs("obs:c"))
    with pytest.raises(ChangeDerivationError) as excinfo:
        _derive(engine)
    text = str(excinfo.value)
    assert OTHER_METRIC in text and METRIC in text
    assert "no conversion exists" in text


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


# -- 23-24. caller authority ---------------------------------------------------


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


# -- 25. display separation ----------------------------------------------------


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
    # and display_metadata is fingerprint-invisible: same id, same content,
    # only display changed -> the digest cannot see it
    from crypto_systems_intelligence_atlas.book6_comparison_registry import (
        comparison_rule_fingerprint,
    )
    assert comparison_rule_fingerprint(plain) == comparison_rule_fingerprint(
        plain.model_copy(update={"display_metadata": {"epsilon": 99}})
    )


# -- 26-27. sealed coverage consumption and engine-derived baseline -------------


def test_coverage_result_is_consumed_not_recomputed() -> None:
    """Two engines, one sealed verdict: the recorded verdict is the SEALED one."""

    sealed = _seal()  # SUFFICIENT, sealed from a 0.95 observation
    engine_a = _populated_engine()
    record_a = _derive(engine_a, comparability=sealed)

    # engine_b's live coverage state is INSUFFICIENT (0.5), but the SAME sealed
    # verdict is handed to the engine. If the engine recomputed, b would differ.
    engine_b = _engine()
    register_measurement(engine_b, _obs("obs:c", day=10, value=7.5, cov_ref="obs:c"))
    register_measurement(engine_b, _obs("obs:b", day=0, value=3.0))
    engine_b.registry.register_coverage(_coverage_obs("obs:c", fraction=0.5))
    record_b = _derive(engine_b, comparability=sealed)
    assert record_a.coverage_verdict.value == "SUFFICIENT"
    assert record_b.coverage_verdict.value == "SUFFICIENT"
    assert record_b.absolute_delta == record_a.absolute_delta == 4.5


def test_selected_baseline_is_engine_derived() -> None:
    """The selected ref is resolved live; a superseded selection is refused."""

    engine = _populated_engine()
    record = _derive(engine)
    assert record.selected_baseline_measurement_ref == "obs:b"
    assert "obs:b" in record.source_measurement_refs
    assert "obs:b" in record.baseline_measurement_refs

    # a superseded baseline is not current at derivation time
    engine2 = _populated_engine()
    register_measurement(engine2, _obs("obs:b2", day=1, value=3.0, supersedes="obs:b"))
    with pytest.raises(ChangeDerivationError) as excinfo:
        _derive(engine2)
    assert OPERAND_NOT_CURRENT in str(excinfo.value)


# -- 28. no aggregation path exists --------------------------------------------


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


# -- additional authority walls -------------------------------------------------


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
    # keep the comparison RECORD (resolved while it was current), then take
    # its successor; the engine's own live resolution must do the refusing
    comparison_record = engine.registry.resolve_current("obs:c")
    register_measurement(engine, _obs("obs:c2", day=11, value=7.5, supersedes="obs:c"))
    with pytest.raises(ChangeDerivationError) as excinfo:
        _derive(engine, comparison=comparison_record)
    assert OPERAND_NOT_CURRENT in str(excinfo.value)


def test_comparable_with_unknown_sealed_verdict_is_refused() -> None:
    """The engine enforces COMPARABLE <=> recomputed SUFFICIENT instead of trusting."""

    engine = _populated_engine()
    sealed = _seal()
    # forge a verdict object claiming COMPARABLE while check 16 failed
    from dataclasses import replace

    broken = replace(
        sealed,
        coverage_checks=tuple(
            replace(c, passed=False, reason="coverage authority failed")
            if c.number == 16 else c
            for c in sealed.coverage_checks
        ),
    )
    with pytest.raises(ChangeDerivationError) as excinfo:
        _derive(engine, comparability=broken)
    assert "did not recompute SUFFICIENT" in str(excinfo.value)


def test_sealed_applicability_must_agree_with_the_governing_rule() -> None:
    """A rule declaring UNRESOLVED coverage cannot ride a REQUIRED sealed replay."""

    engine = _populated_engine()
    rule = _rule(coverage_requirement_status=CoverageRequirementStatus.UNRESOLVED)
    with pytest.raises(ChangeDerivationError) as excinfo:
        _derive(engine, rule=rule, rules_registry=_rules_registry(rule))
    assert "disagrees with itself" in str(excinfo.value)


def test_sufficient_coverage_without_cited_observation_ref_is_refused() -> None:
    """A PRESENT coverage state needs its observation ref; silence is INVALID."""

    engine = _engine()
    # the comparison cites no coverage_observation_id
    register_measurement(engine, _obs("obs:c", day=10, value=7.5))
    register_measurement(engine, _obs("obs:b", day=0, value=3.0))
    with pytest.raises(ChangeDerivationError) as excinfo:
        _derive(engine)
    assert "coverage_observation_id" in str(excinfo.value)


def test_refusal_record_requires_baseline_candidates_to_record() -> None:
    """A refusal record still carries the candidate set; an empty one cannot."""

    engine = _populated_engine()
    sealed = _seal(coverage_observation="none")
    with pytest.raises(ChangeDerivationError) as excinfo:
        _derive(engine, comparability=sealed, baseline_measurement_refs=())
    assert "candidate" in str(excinfo.value)
