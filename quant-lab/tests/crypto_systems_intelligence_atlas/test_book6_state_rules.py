"""Book 6 state rules — ``INDIVIDUAL_STATE_RULES_RATIFIED = 0`` is mechanical.

The ratified governance model ratified NO rule. That fact has to be structural,
not documentary, or the v0.1 failure mode repeats: six unratified rules hiding
inside descriptive labels. The suite proves:

- the registry ships with zero ratified rules and holds no authority of its own;
- a Class B or Class C state cannot be emitted without naming an individually
  RATIFIED rule, and ratification is never inferred, delegated or automatic;
- Class A states need no rule and may not carry one;
- generic ``EXPANDING`` / ``CONTRACTING`` are not representable as a rule at all;
- synthetic local ratification exercises the engine without becoming canonical.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from crypto_systems_intelligence_atlas.book6_core import Book6EngineError
from crypto_systems_intelligence_atlas.book6_states import (
    CLASS_B_AND_C_ARE_RULE_GATED,
    GENERIC_EXPANDING_CONTRACTING_DEFERRED,
    INDIVIDUAL_STATE_RULES_RATIFIED_AT_BOOTSTRAP,
    PROHIBITED_STATE_NAMES,
    STATE_CLASS_BY_NAME,
    RuleRatificationStatus,
    StateClass,
    StateDimension,
    StateError,
    StateName,
    StateRule,
    StateRuleRegistry,
    resolve_availability_state,
)
from crypto_systems_intelligence_atlas.book6_support import (
    NOW,
    T1,
    T2,
    build_engine,
    definition,
    register_definition,
    register_measurement,
    windowed_observation,
)
from crypto_systems_intelligence_atlas.book6_grammar import MissingnessState

CLAIM = "fixture:claim:measurement"
METRIC = "metric.native.native_transactions"

CLASS_B_STATES = [
    StateName.INCREASING,
    StateName.DECREASING,
    StateName.UNCHANGED,
]
CLASS_C_STATES = [
    StateName.STABLE,
    StateName.VOLATILE,
    StateName.HIGHER_THAN_OWN_HISTORY,
    StateName.LOWER_THAN_OWN_HISTORY,
]
CLASS_A_STATES = [
    StateName.INSUFFICIENT_DATA,
    StateName.NOT_APPLICABLE,
    StateName.RULE_NOT_RATIFIED,
    StateName.COVERAGE_SUFFICIENCY_UNKNOWN,
]
GENERIC_STATES = [StateName.EXPANDING, StateName.CONTRACTING]


def _rule(
    target: StateName = StateName.INCREASING,
    *,
    rule_id: str = "staterule:increasing:1",
    **overrides: object,
) -> StateRule:
    state_class = STATE_CLASS_BY_NAME[target]
    payload: dict[str, object] = {
        "state_rule_id": rule_id,
        "target_state": target,
        "state_class": state_class,
        "predicate_ref": "predicate:monotone-comparison@1",
        "methodology_ref": "book6-methodology@1",
        "required_measurement_refs": ("obs:1", "obs:2"),
        "window_class_constraint": "CALENDAR_MONTH",
        "comparability_constraint": "same cohort version, same window class",
        "precision_semantics": "exact equality on the declared numeric precision",
        "benchmark_methodology_ref": "benchmark:own-history@1",
        "coverage_sufficiency_ref": None,
        "tolerance_ref": "tolerance:declared@1",
        "volatility_measure_ref": "volatility:declared@1",
        "decision_rule_ref": "decision:declared@1",
        "version": "1",
    }
    if target is StateName.UNCHANGED:
        payload["benchmark_methodology_ref"] = None
        payload["tolerance_ref"] = None
        payload["volatility_measure_ref"] = None
    payload.update(overrides)
    return StateRule(**payload)  # type: ignore[arg-type]


def _stack():
    engine, *_ = build_engine()
    register_definition(engine, definition(METRIC))
    register_measurement(engine, 
        windowed_observation(
            "obs:1",
            METRIC,
            value=7.0,
            missingness=MissingnessState.OBSERVED,
            claim_refs=(CLAIM,),
        )
    )
    register_measurement(engine, 
        windowed_observation(
            "obs:2",
            METRIC,
            value=9.0,
            missingness=MissingnessState.OBSERVED,
            claim_refs=(CLAIM,),
        )
    )
    return engine


# -- bootstrap: zero ratified rules (Phase 21, 37) ----------------------------


def test_bootstrap_ratified_count_is_zero() -> None:
    assert INDIVIDUAL_STATE_RULES_RATIFIED_AT_BOOTSTRAP == 0


def test_a_fresh_registry_holds_no_rules_at_all() -> None:
    registry = StateRuleRegistry()
    assert registry.ratified_count() == 0
    for target in StateName:
        assert registry.rules_for(target) == ()


def test_registering_a_rule_does_not_ratify_it() -> None:
    registry = StateRuleRegistry()
    registry.register(_rule())
    assert registry.ratified_count() == 0
    with pytest.raises(StateError, match="no registry ratification decision"):
        registry.authorize(StateName.INCREASING, rule_ref="staterule:increasing:1")


def test_the_engine_registry_starts_with_zero_ratified_rules() -> None:
    engine, *_ = build_engine()
    assert engine.registry.state_rules.ratified_count() == 0


# -- Class B / C are rule-gated (Phase 23) -----------------------------------


@pytest.mark.parametrize("target", CLASS_B_STATES + CLASS_C_STATES, ids=lambda s: s.value)
def test_no_class_b_or_c_state_is_emittable_at_bootstrap(target: StateName) -> None:
    engine = _stack()
    with pytest.raises(StateError):
        engine.registry.state_rules.authorize(target, rule_ref="staterule:any:1")


@pytest.mark.parametrize("target", CLASS_B_STATES + CLASS_C_STATES, ids=lambda s: s.value)
def test_the_engine_refuses_to_emit_any_class_b_or_c_state(target: StateName) -> None:
    engine = _stack()
    with pytest.raises((StateError, Book6EngineError)):
        engine.emit_rule_gated_state(
            target,
            rule_ref=f"staterule:{target.value}:1",
            dimension_id="dim:1",
            measurement_refs=("obs:1", "obs:2"),
            methodology_ref="book6-methodology@1",
            valid_time=T1,
            observed_at=T1,
            missingness=MissingnessState.OBSERVED,
        )


def test_class_b_and_c_gate_constant_is_true() -> None:
    assert CLASS_B_AND_C_ARE_RULE_GATED is True


def test_an_unregistered_rule_ref_is_refused() -> None:
    engine = _stack()
    engine.registry.register_state_rule(_rule())
    with pytest.raises(StateError, match="is not registered"):
        engine.registry.state_rules.authorize(
            StateName.INCREASING, rule_ref="staterule:never-registered:1"
        )


def test_a_rule_may_not_be_used_for_a_state_it_does_not_target() -> None:
    engine = _stack()
    engine.registry.register_state_rule(_rule(StateName.INCREASING))
    engine.registry.state_rules.ratify(
        "staterule:increasing:1", operator="synthetic-operator", at=NOW
    )
    with pytest.raises(StateError, match="targets"):
        engine.registry.state_rules.authorize(
            StateName.DECREASING, rule_ref="staterule:increasing:1"
        )


# -- synthetic local ratification exercises the engine (Phase 37) ------------


def test_a_synthetic_ratified_rule_unblocks_exactly_its_own_state() -> None:
    """A synthetic ratified rule unblocks exactly its own state — by REPLAY.

    R2 (Phase 4): ``RATIFIED RULE != TRUE PREDICATE``. Ratification licenses
    the derivation method; it does not assert the method's outcome. Emission
    here happens because a locally registered synthetic predicate REPLAYS TRUE
    over the operands (current 10.0 > prior 7.0), against a rule that binds
    that exact predicate and declares the same window class its inputs carry.
    The same rule with a false predicate is refused in
    ``test_book6_hardening_r2.py`` (R2-D2).
    """

    from crypto_systems_intelligence_atlas.book6_predicates import (
        EvaluatorKind,
        StatePredicateDefinition,
    )

    engine = _stack()
    for mid, value in (("obs:cur", 10.0), ("obs:pri", 7.0)):
        register_measurement(
            engine,
            windowed_observation(
                mid,
                METRIC,
                value=value,
                missingness=MissingnessState.OBSERVED,
                claim_refs=(CLAIM,),
            ),
        )
    engine.predicates.register(
        StatePredicateDefinition(
            predicate_id="predicate:monotone-comparison",
            version="1",
            state_class=StateClass.B_SPECIFICATION_ONLY,
            target_state=StateName.INCREASING,
            description="synthetic fixture predicate; canonically unratified",
            required_input_arity=2,
            evaluator_kind=EvaluatorKind.CURRENT_GREATER_THAN_PRIOR,
        )
    )
    engine.registry.register_state_rule(
        _rule(
            StateName.INCREASING,
            required_measurement_refs=("obs:cur", "obs:pri"),
            window_class_constraint="INSTANTANEOUS",
        )
    )
    engine.registry.state_rules.ratify(
        "staterule:increasing:1", operator="synthetic-fixture-operator", at=NOW
    )
    dimension = engine.emit_rule_gated_state(
        StateName.INCREASING,
        rule_ref="staterule:increasing:1",
        dimension_id="dim:1",
        measurement_refs=("obs:cur", "obs:pri"),
        methodology_ref="book6-methodology@1",
        valid_time=T1,
        observed_at=T1,
        missingness=MissingnessState.OBSERVED,
    )
    assert dimension.state is StateName.INCREASING
    assert dimension.state_rule_ref == "staterule:increasing:1"


def test_synthetic_ratification_is_local_and_not_canonical() -> None:
    engine = _stack()
    engine.registry.register_state_rule(_rule(StateName.INCREASING))
    engine.registry.state_rules.ratify(
        "staterule:increasing:1", operator="synthetic-fixture-operator", at=NOW
    )
    assert engine.registry.state_rules.ratified_count() == 1
    # a different engine, built fresh, is still at zero
    other, *_ = build_engine()
    assert other.registry.state_rules.ratified_count() == 0
    assert INDIVIDUAL_STATE_RULES_RATIFIED_AT_BOOTSTRAP == 0


def test_ratification_is_individual_and_not_repeatable() -> None:
    registry = StateRuleRegistry()
    registry.register(_rule())
    registry.ratify("staterule:increasing:1", operator="op", at=NOW)
    with pytest.raises(StateError, match="already ratified"):
        registry.ratify("staterule:increasing:1", operator="op", at=T2)


def test_ratifying_an_unregistered_rule_is_refused() -> None:
    registry = StateRuleRegistry()
    with pytest.raises(StateError, match="is not registered"):
        registry.ratify("staterule:ghost:1", operator="op", at=NOW)


def test_there_is_no_delegated_or_automatic_ratification_path() -> None:
    """D6M-3 = A: no delegation register, no bulk or automatic ratification."""

    registry = StateRuleRegistry()
    surface = {
        name
        for name in dir(registry)
        if not name.startswith("_")
        and callable(getattr(registry, name))
        and any(
            token in name.lower()
            for token in ("delegate", "auto_ratif", "bulk", "cascade", "promote", "assume")
        )
    }
    assert surface == set()


def test_no_module_level_ratification_helper_exists() -> None:
    from crypto_systems_intelligence_atlas import book6_states

    for name in dir(book6_states):
        lowered = name.lower()
        assert "ratify_all" not in lowered
        assert "auto_ratify" not in lowered
        assert "delegate" not in lowered


# -- Class A needs no rule and may not carry one (Phase 22) ------------------


def test_a_class_a_state_may_not_carry_a_rule() -> None:
    with pytest.raises(ValidationError, match="may not carry one"):
        _rule(StateName.INSUFFICIENT_DATA)


@pytest.mark.parametrize("target", CLASS_A_STATES, ids=lambda s: s.value)
def test_class_a_states_are_emittable_without_any_rule(target: StateName) -> None:
    assert STATE_CLASS_BY_NAME[target] is StateClass.A_AVAILABILITY
    dimension = StateDimension(
        dimension_id="dim:a",
        state=target,
        state_class=StateClass.A_AVAILABILITY,
        measurement_refs=(),
        state_rule_ref=None,
        methodology_ref="book6-methodology@1",
        valid_time=T1,
        observed_at=T1,
        missingness=MissingnessState.NOT_APPLICABLE,
    )
    assert dimension.state is target
    assert dimension.state_rule_ref is None


@pytest.mark.parametrize("target", CLASS_B_STATES + CLASS_C_STATES, ids=lambda s: s.value)
def test_a_class_b_or_c_dimension_must_name_its_rule(target: StateName) -> None:
    with pytest.raises(ValidationError, match="must name its state_rule_ref"):
        StateDimension(
            dimension_id="dim:b",
            state=target,
            state_class=STATE_CLASS_BY_NAME[target],
            measurement_refs=("obs:1",),
            state_rule_ref=None,
            methodology_ref="book6-methodology@1",
            valid_time=T1,
            observed_at=T1,
            missingness=MissingnessState.OBSERVED,
        )


# -- generic EXPANDING / CONTRACTING are deferred (Phase 23) -----------------


@pytest.mark.parametrize("target", GENERIC_STATES, ids=lambda s: s.value)
def test_generic_expanding_contracting_are_deferred(target: StateName) -> None:
    assert STATE_CLASS_BY_NAME[target] is StateClass.DEFERRED_GENERIC


@pytest.mark.parametrize("target", GENERIC_STATES, ids=lambda s: s.value)
def test_no_rule_can_be_written_for_a_generic_state(target: StateName) -> None:
    with pytest.raises(ValidationError, match="DEFERRED"):
        _rule(target)


@pytest.mark.parametrize("target", GENERIC_STATES, ids=lambda s: s.value)
def test_a_generic_state_can_never_be_authorized(target: StateName) -> None:
    registry = StateRuleRegistry()
    with pytest.raises(StateError):
        registry.authorize(target, rule_ref="staterule:generic:1")


def test_generic_deferred_constant_is_true() -> None:
    assert GENERIC_EXPANDING_CONTRACTING_DEFERRED is True


# -- the rule object can represent an unratified rule (Phase 20) --------------


def test_an_unratified_rule_is_representable() -> None:
    rule = _rule()
    assert rule.status is RuleRatificationStatus.UNRATIFIED
    assert rule.ratified_by is None
    assert rule.ratified_at is None
    assert rule.is_ratified() is False


def test_a_rule_object_may_never_declare_itself_ratified() -> None:
    """R1-D7: ratification is a registry decision, never a field on the rule.

    Before R1 a caller could construct a RATIFIED rule with an arbitrary
    ``ratified_by="operator"`` string and register it. Now the object refuses,
    so authority can only come from ``StateRuleRegistry.ratify``.
    """

    with pytest.raises(ValidationError, match="may not declare itself RATIFIED"):
        _rule(status=RuleRatificationStatus.RATIFIED)
    with pytest.raises(ValidationError, match="may not declare itself RATIFIED"):
        _rule(
            status=RuleRatificationStatus.RATIFIED,
            ratified_by="operator",
            ratified_at=NOW,
        )


def test_a_registered_ratified_rule_is_refused_by_the_registry() -> None:
    """Even a forged object cannot enter the registry carrying its own status."""

    forged = _rule().model_copy(
        update={
            "status": RuleRatificationStatus.RATIFIED,
            "ratified_by": "operator",
            "ratified_at": NOW,
        }
    )
    registry = StateRuleRegistry()
    with pytest.raises(StateError, match="may only be registered"):
        registry.register(forged)


def test_the_registry_ratification_is_recorded_not_self_declared() -> None:
    registry = StateRuleRegistry()
    registry.register(_rule())
    ratified = registry.ratify("staterule:increasing:1", operator="op", at=NOW)
    # the object stays UNRATIFIED; the DECISION lives in the registry ledger
    assert ratified.status is RuleRatificationStatus.UNRATIFIED
    decision = registry.ratification_of("staterule:increasing:1")
    assert decision is not None
    assert decision.operator == "op"
    assert decision.registry_identity == registry.registry_identity


def test_a_class_c_rule_needs_a_benchmark_tolerance_or_volatility_identity() -> None:
    with pytest.raises(ValidationError, match="threshold/benchmark dependent"):
        _rule(
            StateName.STABLE,
            benchmark_methodology_ref=None,
            tolerance_ref=None,
            volatility_measure_ref=None,
        )


def test_unchanged_requires_explicit_precision_semantics() -> None:
    with pytest.raises(ValidationError, match="precision semantics"):
        _rule(StateName.UNCHANGED, precision_semantics=None)


def test_a_rule_may_not_mislabelling_its_target_class() -> None:
    with pytest.raises(ValidationError, match="declares class"):
        _rule(StateName.INCREASING, state_class=StateClass.C_THRESHOLD_BENCHMARK)


def test_a_rule_id_may_not_be_registered_twice() -> None:
    registry = StateRuleRegistry()
    registry.register(_rule())
    with pytest.raises(StateError, match="already registered"):
        registry.register(_rule())


def test_rule_lookup_is_deterministic() -> None:
    registry = StateRuleRegistry()
    registry.register(_rule(StateName.INCREASING, rule_id="staterule:b"))
    registry.register(_rule(StateName.INCREASING, rule_id="staterule:a"))
    assert [r.state_rule_id for r in registry.rules_for(StateName.INCREASING)] == [
        "staterule:a",
        "staterule:b",
    ]


def test_supersession_installs_a_new_version_and_retains_the_prior_one() -> None:
    registry = StateRuleRegistry()
    registry.register(_rule())
    registry.ratify("staterule:increasing:1", operator="op", at=NOW)
    registry.supersede(_rule(version="2"))
    current = registry.rules_for(StateName.INCREASING)[0]
    assert current.version == "2"
    assert [r.version for r in registry.superseded_versions("staterule:increasing:1")] == ["1"]


def test_a_new_version_does_not_inherit_the_prior_ratification() -> None:
    """Authority decays on a rule revision; it is never carried forward."""

    registry = StateRuleRegistry()
    registry.register(_rule())
    registry.ratify("staterule:increasing:1", operator="op", at=NOW)
    registry.supersede(_rule(version="2"))
    assert registry.ratified_count() == 0
    with pytest.raises(StateError, match="no registry ratification decision"):
        registry.authorize(StateName.INCREASING, rule_ref="staterule:increasing:1")
    registry.ratify("staterule:increasing:1", operator="op-2", at=T2)
    assert registry.authorize(
        StateName.INCREASING, rule_ref="staterule:increasing:1"
    ).version == "2"


def test_supersession_requires_a_prior_version_and_a_new_version() -> None:
    registry = StateRuleRegistry()
    with pytest.raises(StateError, match="is not registered"):
        registry.supersede(_rule())
    registry.register(_rule())
    with pytest.raises(StateError, match="already at version"):
        registry.supersede(_rule(version="1"))


def test_supersession_may_not_change_the_target_state() -> None:
    registry = StateRuleRegistry()
    registry.register(_rule(StateName.INCREASING))
    with pytest.raises(StateError, match="may not change the target state"):
        registry.supersede(_rule(StateName.DECREASING, version="2"))


def test_supersession_history_is_append_only() -> None:
    registry = StateRuleRegistry()
    registry.register(_rule(version="1"))
    registry.supersede(_rule(version="2"))
    registry.supersede(_rule(version="3"))
    assert [r.version for r in registry.superseded_versions("staterule:increasing:1")] == [
        "1",
        "2",
    ]
    assert registry.rules_for(StateName.INCREASING)[0].version == "3"


def test_a_superseded_status_is_representable_in_the_enum() -> None:
    """The vocabulary still names SUPERSEDED, but no object may carry it.

    R1: supersession is recorded by the registry (which installs a fresh
    UNRATIFIED version and drops the decision), so the rule object never needs
    to declare a non-current status for itself.
    """

    assert RuleRatificationStatus.SUPERSEDED.value == "SUPERSEDED"
    assert RuleRatificationStatus.SUPERSEDED is not RuleRatificationStatus.RATIFIED
    assert _rule().is_ratified() is False


# -- prohibited prescriptive names (anti-score firewall precursor) -----------


def test_prohibited_names_include_the_prescriptive_vocabulary() -> None:
    for name in ("BUY", "SELL", "UNDERVALUED", "OVERVALUED", "TOP_TIER", "HEALTHY"):
        assert name in PROHIBITED_STATE_NAMES


@pytest.mark.parametrize("name", sorted(PROHIBITED_STATE_NAMES))
def test_no_prohibited_name_is_a_state(name: str) -> None:
    assert name not in {state.value for state in StateName}


# -- resolution of Class A states is structural (Phase 22) -------------------


def test_inapplicable_metric_wins_over_every_other_condition() -> None:
    assert (
        resolve_availability_state(
            has_measurements=True,
            metric_applies=False,
            rule_ratified=True,
            coverage_sufficiency_rule_ratified=True,
        )
        is StateName.NOT_APPLICABLE
    )


def test_unratified_rule_beats_present_data() -> None:
    assert (
        resolve_availability_state(
            has_measurements=True,
            metric_applies=True,
            rule_ratified=False,
            coverage_sufficiency_rule_ratified=True,
        )
        is StateName.RULE_NOT_RATIFIED
    )


def test_no_data_reports_insufficient_data_not_zero() -> None:
    assert (
        resolve_availability_state(
            has_measurements=False,
            metric_applies=True,
            rule_ratified=True,
            coverage_sufficiency_rule_ratified=True,
        )
        is StateName.INSUFFICIENT_DATA
    )


def test_unratified_coverage_sufficiency_is_reported_not_assumed() -> None:
    assert (
        resolve_availability_state(
            has_measurements=True,
            metric_applies=True,
            rule_ratified=True,
            coverage_sufficiency_rule_ratified=False,
        )
        is StateName.COVERAGE_SUFFICIENCY_UNKNOWN
    )


def test_the_engine_resolves_class_a_states_only() -> None:
    engine = _stack()
    assert STATE_CLASS_BY_NAME[engine.availability_state("obs:1")] is StateClass.A_AVAILABILITY
