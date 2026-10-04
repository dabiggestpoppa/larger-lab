"""Book 6 missingness, denominator and coverage semantics (6D.1).

The ratified laws under test:

    ZERO_OBSERVED  !=  missing          (a measured zero is not an absence)
    NO VALUE       !=  ZERO             (a forbidden-value state may not carry 0)
    COVERAGE_OBSERVATION != COVERAGE_SUFFICIENCY
    never divide through missingness; an observed-zero denominator is UNDEFINED
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from crypto_systems_intelligence_atlas.book6_core import Book6EngineError
from crypto_systems_intelligence_atlas.book6_registry import (
    Book6CurrentnessError,
    CurrentnessRefusal,
)
from crypto_systems_intelligence_atlas.book6_definitions import (
    CoverageObservation,
    CoverageSufficiencyRule,
    DenominatorRule,
)
from crypto_systems_intelligence_atlas.book6_grammar import (
    DenominatorState,
    MeasurementCategory,
    MissingnessState,
    VALUE_BEARING_MISSINGNESS,
    VALUE_FORBIDDEN_MISSINGNESS,
)
from crypto_systems_intelligence_atlas.book6_records import DenominatorRef
from crypto_systems_intelligence_atlas.book6_support import (
    NOW,
    absent_denominator,
    build_engine,
    coverage,
    definition,
    present_denominator,
    ratio_observation,
    register_definition,
    register_measurement,
    windowed_observation,
    zero_denominator,
)

CLAIM = "fixture:claim:measurement"

NON_VALUE_STATES = [
    state
    for state in MissingnessState
    if state not in VALUE_BEARING_MISSINGNESS
]


# -- missingness states (Phase 7) ------------------------------------------


def test_ten_distinct_missingness_states() -> None:
    assert len(list(MissingnessState)) == 10
    assert len({s.value for s in MissingnessState}) == 10


def test_zero_observed_is_distinct_from_every_absence() -> None:
    assert MissingnessState.ZERO_OBSERVED in VALUE_BEARING_MISSINGNESS
    for state in NON_VALUE_STATES:
        assert MissingnessState.ZERO_OBSERVED is not state


@pytest.mark.parametrize("state", NON_VALUE_STATES)
def test_absence_may_never_carry_a_fabricated_zero(state: MissingnessState) -> None:
    """MISSING != ZERO: no value-forbidding state may carry 0.0."""

    with pytest.raises(ValidationError, match="forbids a value"):
        windowed_observation(
            f"obs:{state.value}",
            "m:supply",
            value=0.0,
            missingness=state,
            claim_refs=(CLAIM,),
        )


@pytest.mark.parametrize("state", NON_VALUE_STATES)
def test_absence_carries_no_value_at_all(state: MissingnessState) -> None:
    observation = windowed_observation(
        f"obs:none-{state.value}",
        "m:supply",
        value=None,
        missingness=state,
        claim_refs=(),
        unit=None,
    )
    assert observation.value is None
    assert observation.is_value_bearing is False


def test_zero_observed_carries_a_real_zero() -> None:
    observation = windowed_observation(
        "obs:zero",
        "m:supply",
        value=0.0,
        missingness=MissingnessState.ZERO_OBSERVED,
        claim_refs=(CLAIM,),
    )
    assert observation.value == 0.0
    assert observation.is_value_bearing is True


def test_value_forbidden_states_exclude_both_value_states() -> None:
    assert VALUE_FORBIDDEN_MISSINGNESS == frozenset(set(MissingnessState) - VALUE_BEARING_MISSINGNESS)
    assert not (VALUE_FORBIDDEN_MISSINGNESS & VALUE_BEARING_MISSINGNESS)


def test_engine_refuses_to_read_a_value_out_of_an_absence() -> None:
    """Absence is not zero, at the value-read gate.

    The record here CITES a Book 2 claim on purpose. That lets it clear the NV-B
    currentness gate (step 7) and reach the absence read, which is the gate this
    test is about. The source-less variant is a different gate and is asserted
    separately below.
    """

    engine, _, _, _ = build_engine(CLAIM)
    register_definition(engine, definition("m:supply"))
    register_measurement(engine, 
        windowed_observation(
            "obs:na",
            "m:supply",
            value=None,
            missingness=MissingnessState.NOT_COLLECTED,
            claim_refs=(CLAIM,),
            unit=None,
        )
    )
    with pytest.raises(Book6EngineError, match="absence is not zero"):
        engine.current_value("obs:na")


def test_source_less_missingness_is_not_current_under_nv_b() -> None:
    """NV-B: source-less records are history, never current authority.

    Before the GAP-7 amendment this record reached the consumer through the
    non-value-bearing early bypass. It is now refused at resolver step 7, before
    any consumer can read it, and the record stays registered and queryable.
    """

    engine, _, _, _ = build_engine(CLAIM)
    register_definition(engine, definition("m:supply"))
    register_measurement(engine,
        windowed_observation(
            "obs:sourceless",
            "m:supply",
            value=None,
            missingness=MissingnessState.NOT_COLLECTED,
            claim_refs=(),
            unit=None,
        )
    )
    assert engine.registry.is_authoritative_now("obs:sourceless") is False
    with pytest.raises(Book6CurrentnessError) as excinfo:
        engine.registry.resolve_current("obs:sourceless")
    assert excinfo.value.reason is CurrentnessRefusal.SOURCE_CLAIMS_ABSENT
    # still history
    assert engine.registry.registered_measurement("obs:sourceless").measurement_id == (
        "obs:sourceless"
    )


# -- denominator doctrine (Phase 8) ----------------------------------------


def test_denominator_states_are_distinct() -> None:
    assert len({s.value for s in DenominatorState}) == 6
    assert DenominatorState.ZERO is not DenominatorState.UNKNOWN
    assert DenominatorState.UNAVAILABLE is not DenominatorState.UNKNOWN


def test_present_denominator_requires_its_value() -> None:
    with pytest.raises(ValidationError, match="PRESENT denominator must carry"):
        DenominatorRef(
            denominator_measurement_id="obs:d",
            denominator_identity="d",
            state="PRESENT",
        )


def test_zero_denominator_carries_observed_zero_only() -> None:
    assert zero_denominator().value == 0.0
    with pytest.raises(ValidationError, match="observed 0.0"):
        DenominatorRef(
            denominator_measurement_id="obs:d",
            denominator_identity="d",
            state="ZERO",
            value=5.0,
        )


@pytest.mark.parametrize("state", ["UNKNOWN", "UNAVAILABLE", "UNSTABLE", "NOT_APPLICABLE"])
def test_absent_denominator_states_may_not_carry_values(state: str) -> None:
    with pytest.raises(ValidationError, match="may not carry a numeric value"):
        DenominatorRef(
            denominator_measurement_id="obs:d",
            denominator_identity="d",
            state=state,
            value=1.0,
        )


def _ratio_engine():
    engine, _, _, _ = build_engine(CLAIM)
    register_definition(engine, 
        definition(
            "m:ratio",
            category=MeasurementCategory.RATIO,
            denominator_rule=DenominatorRule.OBSERVED_MEASUREMENT,
            unit="ratio",
        )
    )
    return engine


def test_ratio_with_present_denominator_computes() -> None:
    engine = _ratio_engine()
    register_measurement(engine, 
        ratio_observation(
            "obs:r", "m:ratio", value=8.0, denominator=present_denominator(), claim_refs=(CLAIM,)
        )
    )
    result = engine.compute_ratio("obs:r")
    assert result.is_undefined is False
    assert result.ratio == pytest.approx(2.0)


def test_observed_zero_denominator_yields_undefined_not_infinity() -> None:
    engine = _ratio_engine()
    register_measurement(engine, 
        ratio_observation(
            "obs:rz", "m:ratio", value=8.0, denominator=zero_denominator(), claim_refs=(CLAIM,)
        )
    )
    result = engine.compute_ratio("obs:rz")
    assert result.is_undefined is True
    assert result.ratio is None
    assert result.denominator_state is DenominatorState.ZERO


@pytest.mark.parametrize("state", ["UNKNOWN", "UNAVAILABLE", "UNSTABLE"])
def test_missing_denominator_never_produces_a_ratio(state: str) -> None:
    engine = _ratio_engine()
    register_measurement(engine, 
        ratio_observation(
            f"obs:rd-{state}",
            "m:ratio",
            value=8.0,
            denominator=absent_denominator(state=state),
            claim_refs=(CLAIM,),
        )
    )
    result = engine.compute_ratio(f"obs:rd-{state}")
    assert result.is_undefined is True
    assert result.ratio is None
    assert result.denominator_state is DenominatorState(state)


def test_ratio_must_carry_a_denominator_at_all() -> None:
    with pytest.raises(ValidationError, match="must carry its denominator"):
        ratio_observation("obs:r-none", "m:ratio", value=1.0, denominator=None, claim_refs=(CLAIM,))


def test_non_ratio_may_not_declare_a_denominator() -> None:
    with pytest.raises(ValidationError, match="may not declare a denominator"):
        windowed_observation(
            "obs:stock-with-den",
            "m:supply",
            value=1.0,
            missingness=MissingnessState.OBSERVED,
            claim_refs=(CLAIM,),
            denominator=present_denominator(),
        )


# -- coverage observation is not sufficiency (Phase 11) --------------------


def test_coverage_percentage_asserts_no_sufficiency() -> None:
    observation = coverage("obs:1", 0.72)
    assert observation.observed_fraction == pytest.approx(0.72)
    # R1: the structural predicate is renamed and carries NO authority.
    assert observation.names_a_sufficiency_rule is False
    assert not hasattr(observation, "sufficiency_known")
    assert not hasattr(observation, "sufficiency")
    assert not hasattr(observation, "is_sufficient")


def test_coverage_carries_no_unratified_floor() -> None:
    rule = CoverageSufficiencyRule(
        version="1",
        rule_id="csr:unratified",
        required_fraction=0.9,
        scope_metric_id="m:supply",
        rationale="candidate rule only; not ratified by any operator decision",
    )
    assert rule.status == "UNRATIFIED"


def test_coverage_requires_a_declared_basis() -> None:
    with pytest.raises(ValidationError):
        CoverageObservation(
            measurement_id="obs:1",
            observed_fraction=0.5,
            basis="",
            valid_time=NOW,
        )
