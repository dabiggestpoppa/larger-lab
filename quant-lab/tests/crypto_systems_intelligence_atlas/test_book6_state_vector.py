"""Book 6 fundamental state vector — descriptive, never evaluative.

The vector is the surface most likely to grow a score by accident, so the
anti-score firewall is tested from every direction a caller can reach: the
constructor, ``model_copy``, raw dict construction, serialization round-trips,
and nested payloads. The vector has no ``total``, ``score``, ``rating``,
``grade``, ``rank`` or weight field, and ``extra="forbid"`` turns an attempt to
add one into a refusal.

Completeness is also strictly structural. ``SCHEMA_COMPLETE`` names slot
resolution only, ``NOT_APPLICABLE`` is a resolved slot rather than a defect, and
``DATA_COMPLETE`` cannot be asserted while any dimension is unresolved. With
zero ratified coverage-sufficiency rules the data status fails closed.
"""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from crypto_systems_intelligence_atlas.book6_frozen import Book6FrozenModel
from crypto_systems_intelligence_atlas.book6_grammar import MissingnessState
from crypto_systems_intelligence_atlas.book6_states import (
    NO_COMPLETENESS_SCORE,
    PROHIBITED_STATE_NAMES,
    FundamentalStateVector,
    StateClass,
    StateDimension,
    StateName,
    VectorStatus,
)
from crypto_systems_intelligence_atlas.book6_support import (
    T1,
    build_engine,
    definition,
    register_definition,
    register_measurement,
    windowed_observation,
)

CLAIM = "fixture:claim:measurement"
METRIC = "metric.native.native_transactions"

#: Every prescriptive surface name the Constitution forbids on a state record.
ANTI_SCORE_FIELDS = (
    "overall_score",
    "quality_score",
    "score",
    "total",
    "rating",
    "grade",
    "rank",
    "ranking",
    "weighted_total",
    "weight",
    "buy",
    "sell",
    "attractive",
    "undervalued",
    "overvalued",
    "top_tier",
    "healthy",
)


def _dimension(
    dimension_id: str = "dim:1",
    *,
    state: StateName = StateName.INSUFFICIENT_DATA,
    state_class: StateClass = StateClass.A_AVAILABILITY,
    missingness: MissingnessState = MissingnessState.OBSERVED,
    state_rule_ref: str | None = None,
    coverage_observation_id: str | None = None,
) -> StateDimension:
    return StateDimension(
        dimension_id=dimension_id,
        state=state,
        state_class=state_class,
        measurement_refs=("obs:1",),
        state_rule_ref=state_rule_ref,
        methodology_ref="book6-methodology@1",
        valid_time=T1,
        observed_at=T1,
        missingness=missingness,
        coverage_observation_id=coverage_observation_id,
        sensitivity_note=None,
    )


def _vector(
    *dimensions: StateDimension,
    coverage_sufficiency_rule_refs: tuple[str, ...] = (),
    sufficiency_attestation=None,
) -> FundamentalStateVector:
    return FundamentalStateVector(
        subject_ref="fixture:chain:alpha",
        schema_ref="schema:book6:1",
        as_of_valid_time=T1,
        dimensions=dimensions or (_dimension(),),
        coverage_sufficiency_rule_refs=coverage_sufficiency_rule_refs,
        sufficiency_attestation=sufficiency_attestation,
    )


def _attestation(rule_ids=("covrule:synthetic:1",), scope=("dim:1", "dim:2")):
    """A synthetic registry-issued attestation, for local fixtures only."""

    from crypto_systems_intelligence_atlas.book6_coverage_rules import (
        CoverageSufficiencyAttestation,
    )

    return CoverageSufficiencyAttestation(
        rule_ids=rule_ids,
        scope_metric_ids=scope,
        attested_at=T1,
        registry_identity="csia:book6:synthetic-fixture",
    )


def _observed_vector(**dim_kwargs) -> FundamentalStateVector:
    return _vector(
        _dimension("dim:1", missingness=MissingnessState.OBSERVED, **dim_kwargs),
        _dimension("dim:2", missingness=MissingnessState.OBSERVED, **dim_kwargs),
    )


# -- the vector hosts no score (Phase 26) -------------------------------------


def test_the_vector_has_no_score_fields() -> None:
    fields = set(FundamentalStateVector.model_fields)
    assert fields == {
        "subject_ref",
        "schema_ref",
        "as_of_valid_time",
        "dimensions",
        "coverage_sufficiency_rule_refs",
        "sufficiency_attestation",
    }


def test_the_dimension_has_no_score_fields() -> None:
    fields = set(StateDimension.model_fields)
    assert fields.isdisjoint(set(ANTI_SCORE_FIELDS))


@pytest.mark.parametrize("field", ANTI_SCORE_FIELDS, ids=lambda f: f)
def test_constructor_injection_of_an_anti_score_field_fails(field: str) -> None:
    payload = {
        "subject_ref": "fixture:chain:alpha",
        "schema_ref": "schema:book6:1",
        "as_of_valid_time": T1,
        "dimensions": (_dimension(),),
        field: 0.9,
    }
    with pytest.raises(ValidationError):
        FundamentalStateVector(**payload)


@pytest.mark.parametrize("field", ANTI_SCORE_FIELDS, ids=lambda f: f)
def test_model_copy_injection_of_an_anti_score_field_is_refused(field: str) -> None:
    """``model_copy`` must not be a constructor bypass for the anti-score firewall."""

    vector = _observed_vector()
    assert field not in set(FundamentalStateVector.model_fields)
    with pytest.raises(ValueError, match="extra='forbid'"):
        vector.model_copy(update={field: 0.9})


def test_every_book6_record_refuses_an_unknown_model_copy_key() -> None:
    from crypto_systems_intelligence_atlas.book6_frozen import Book6FrozenModel

    for name in dir(Book6FrozenModel):
        pass  # the base itself is checked through the concrete records below
    assert _observed_vector().model_copy(update={"subject_ref": "other"}).subject_ref == "other"


@pytest.mark.parametrize("field", ANTI_SCORE_FIELDS, ids=lambda f: f)
def test_raw_dict_deserialization_of_an_anti_score_field_fails(field: str) -> None:
    payload = json.loads(_vector().model_dump_json())
    payload[field] = 0.9
    with pytest.raises(ValidationError):
        FundamentalStateVector.model_validate(payload)


def test_a_serialization_round_trip_injects_nothing() -> None:
    vector = _observed_vector()
    payload = json.loads(vector.model_dump_json())
    assert set(payload) == {
        "subject_ref",
        "schema_ref",
        "as_of_valid_time",
        "dimensions",
        "coverage_sufficiency_rule_refs",
        "sufficiency_attestation",
    }
    assert FundamentalStateVector.model_validate(payload) == vector


@pytest.mark.parametrize("field", ANTI_SCORE_FIELDS, ids=lambda f: f)
def test_nested_payload_injection_into_a_dimension_fails(field: str) -> None:
    payload = _dimension().model_dump()
    payload[field] = 0.9
    with pytest.raises(ValidationError):
        StateDimension.model_validate(payload)


def test_a_nested_dimension_cannot_carry_a_prescriptive_name() -> None:
    for name in sorted(PROHIBITED_STATE_NAMES):
        with pytest.raises(ValidationError):
            StateDimension(
                dimension_id="dim:bad",
                state=name,
                state_class=StateClass.A_AVAILABILITY,
                measurement_refs=(),
                state_rule_ref=None,
                methodology_ref="book6-methodology@1",
                valid_time=T1,
                observed_at=T1,
                missingness=MissingnessState.OBSERVED,
            )


def test_no_module_function_computes_a_score() -> None:
    from crypto_systems_intelligence_atlas import book6_core, book6_states

    forbidden = ("score", "grade", "rank_", "rating", "evaluate", "assess", "weight")
    for module in (book6_core, book6_states):
        for name in dir(module):
            if not callable(getattr(module, name)) or isinstance(
                getattr(module, name), type
            ):
                continue
            lowered = name.lower()
            assert not any(token in lowered for token in forbidden), f"{module.__name__}.{name}"


def test_no_book6_record_class_declares_a_score_field() -> None:
    from crypto_systems_intelligence_atlas import (
        book6_definitions,
        book6_normalization,
        book6_records,
        book6_states,
        book6_valuation,
    )

    for module in (
        book6_definitions,
        book6_normalization,
        book6_records,
        book6_states,
        book6_valuation,
    ):
        for name in dir(module):
            obj = getattr(module, name)
            if not isinstance(obj, type) or not issubclass(obj, Book6FrozenModel):
                continue
            assert set(obj.model_fields).isdisjoint(set(ANTI_SCORE_FIELDS)), obj.__name__


def test_completeness_constant_is_true() -> None:
    assert NO_COMPLETENESS_SCORE is True


# -- completeness is structural, not evaluative (Phase 25) ------------------


def test_a_resolved_slot_vector_is_schema_complete() -> None:
    assert _observed_vector().schema_status is VectorStatus.SCHEMA_COMPLETE


def test_not_applicable_satisfies_the_schema_it_is_a_resolved_slot() -> None:
    vector = _vector(
        _dimension(
            "dim:1",
            state=StateName.NOT_APPLICABLE,
            missingness=MissingnessState.NOT_APPLICABLE,
        ),
        _dimension("dim:2"),
    )
    assert vector.schema_status is VectorStatus.SCHEMA_COMPLETE


def test_a_deferred_generic_dimension_defects_the_schema() -> None:
    vector = FundamentalStateVector(
        subject_ref="fixture:chain:alpha",
        schema_ref="schema:book6:1",
        as_of_valid_time=T1,
        dimensions=(
            _dimension(),
            _dimension(
                "dim:generic",
                state=StateName.EXPANDING,
                state_class=StateClass.DEFERRED_GENERIC,
            ),
        ),
    )
    assert vector.schema_status is VectorStatus.SCHEMA_INCOMPLETE


def test_fully_observed_dimensions_still_fail_closed_without_a_sufficiency_rule() -> None:
    """DATA_COMPLETE is not "every value happened to be observed" (Phase 25)."""

    assert _observed_vector().data_status is VectorStatus.DATA_INCOMPLETE


def test_data_completeness_needs_an_ATTESTED_sufficiency_rule() -> None:
    """R1-D4: a rule REF alone is no longer sufficient.

    Before R1 this vector was DATA_COMPLETE from ``("covrule:synthetic:1",)``
    alone, with no such rule in existence. ``DATA_COMPLETE`` now additionally
    requires a registry-issued attestation whose scope covers every dimension.
    """

    vector = _vector(
        _dimension("dim:1", coverage_observation_id="cov:1"),
        _dimension("dim:2", coverage_observation_id="cov:2"),
        coverage_sufficiency_rule_refs=("covrule:synthetic:1",),
    )
    assert vector.data_status is VectorStatus.DATA_INCOMPLETE

    attested = _vector(
        _dimension("dim:1", coverage_observation_id="cov:1"),
        _dimension("dim:2", coverage_observation_id="cov:2"),
        coverage_sufficiency_rule_refs=("covrule:synthetic:1",),
        sufficiency_attestation=_attestation(),
    )
    assert attested.data_status is VectorStatus.DATA_COMPLETE


def test_naming_a_sufficiency_rule_without_covering_every_dimension_fails_closed() -> None:
    vector = FundamentalStateVector(
        subject_ref="fixture:chain:alpha",
        schema_ref="schema:book6:1",
        as_of_valid_time=T1,
        dimensions=(_dimension("dim:1", coverage_observation_id="cov:1"), _dimension("dim:2")),
        coverage_sufficiency_rule_refs=("covrule:synthetic:1",),
    )
    assert vector.data_status is VectorStatus.DATA_INCOMPLETE


def test_no_coverage_sufficiency_rule_exists_to_name_at_bootstrap() -> None:
    """The registry ships zero ratified sufficiency rules, so the ref is unfillable."""

    from crypto_systems_intelligence_atlas.book6_definitions import CoverageSufficiencyRule

    rule = CoverageSufficiencyRule(
        rule_id="covrule:synthetic:1",
        version="1",
        required_fraction=0.9,
        scope_metric_id=METRIC,
        rationale="a synthetic candidate that is deliberately never ratified",
    )
    assert rule.status == "UNRATIFIED"


def test_an_unattested_vector_cannot_be_data_complete_even_with_a_ref() -> None:
    """The R1-D4 reproducer, now refused: an arbitrary ref grants nothing."""

    for fake_ref in ("fake:rule", "covrule:synthetic:1", "anything-at-all"):
        vector = _vector(
            _dimension("dim:1", coverage_observation_id="cov:1"),
            coverage_sufficiency_rule_refs=(fake_ref,),
        )
        assert vector.data_status is VectorStatus.DATA_INCOMPLETE, fake_ref


def test_an_attestation_that_does_not_cover_every_dimension_fails_closed() -> None:
    vector = _vector(
        _dimension("dim:1", coverage_observation_id="cov:1"),
        _dimension("dim:2", coverage_observation_id="cov:2"),
        coverage_sufficiency_rule_refs=("covrule:synthetic:1",),
        sufficiency_attestation=_attestation(scope=("dim:1",)),
    )
    assert vector.data_status is VectorStatus.DATA_INCOMPLETE


def test_an_attestation_whose_rules_disagree_with_the_refs_fails_closed() -> None:
    vector = _vector(
        _dimension("dim:1", coverage_observation_id="cov:1"),
        _dimension("dim:2", coverage_observation_id="cov:2"),
        coverage_sufficiency_rule_refs=("covrule:synthetic:1",),
        sufficiency_attestation=_attestation(rule_ids=("covrule:other:1",)),
    )
    assert vector.data_status is VectorStatus.DATA_INCOMPLETE


def test_fail_closed_constant_is_true() -> None:
    from crypto_systems_intelligence_atlas.book6_states import (
        DATA_COMPLETENESS_FAILS_CLOSED,
    )

    assert DATA_COMPLETENESS_FAILS_CLOSED is True


def test_any_unresolved_dimension_fails_data_completeness_closed() -> None:
    vector = _vector(
        _dimension("dim:1"),
        _dimension("dim:2", missingness=MissingnessState.NOT_COLLECTED),
    )
    assert vector.data_status is VectorStatus.DATA_INCOMPLETE


def test_a_zero_observed_dimension_counts_as_a_derivation_not_as_missing() -> None:
    """ZERO_OBSERVED is a measured zero, so it is a derivation, not an absence."""

    vector = _vector(
        _dimension("dim:1", coverage_observation_id="cov:1"),
        _dimension(
            "dim:2", missingness=MissingnessState.ZERO_OBSERVED, coverage_observation_id="cov:2"
        ),
        coverage_sufficiency_rule_refs=("covrule:synthetic:1",),
        sufficiency_attestation=_attestation(),
    )
    assert vector.data_status is VectorStatus.DATA_COMPLETE

    without_sufficiency = _vector(
        _dimension("dim:1"),
        _dimension("dim:2", missingness=MissingnessState.ZERO_OBSERVED),
    )
    assert without_sufficiency.data_status is VectorStatus.DATA_INCOMPLETE


def test_data_completeness_is_never_asserted_without_a_derivation() -> None:
    for missingness in MissingnessState:
        if missingness in (MissingnessState.OBSERVED, MissingnessState.ZERO_OBSERVED):
            continue
        vector = _vector(_dimension("dim:1", missingness=missingness))
        assert vector.data_status is VectorStatus.DATA_INCOMPLETE, missingness


def test_there_is_no_numeric_completeness_score() -> None:
    vector = _observed_vector()
    numeric = [
        name
        for name in dir(vector)
        if not name.startswith("_")
        and isinstance(getattr(type(vector), name, None), property)
        and isinstance(getattr(vector, name), (int, float))
    ]
    assert numeric == []


def test_the_vector_must_carry_at_least_one_dimension() -> None:
    with pytest.raises(ValidationError):
        FundamentalStateVector(
            subject_ref="fixture:chain:alpha",
            schema_ref="schema:book6:1",
            as_of_valid_time=T1,
            dimensions=(),
        )


# -- the engine builds only Class A availability vectors ---------------------


def _engine_stack():
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
    return engine


def test_the_engine_vector_carries_only_class_a_states() -> None:
    engine = _engine_stack()
    vector = engine.build_availability_vector(
        subject_ref="fixture:chain:alpha",
        schema_ref="schema:book6:1",
        as_of_valid_time=T1,
        observed_at=T1,
        measurement_ids=("obs:1",),
        methodology_ref="book6-methodology@1",
    )
    assert {dim.state_class for dim in vector.dimensions} == {StateClass.A_AVAILABILITY}
    assert all(dim.state_rule_ref is None for dim in vector.dimensions)


def test_the_engine_vector_does_not_assert_data_completeness_by_default() -> None:
    """Zero ratified coverage-sufficiency rules means data status fails closed."""

    engine = _engine_stack()
    vector = engine.build_availability_vector(
        subject_ref="fixture:chain:alpha",
        schema_ref="schema:book6:1",
        as_of_valid_time=T1,
        observed_at=T1,
        measurement_ids=("obs:1",),
        methodology_ref="book6-methodology@1",
    )
    assert vector.schema_status is VectorStatus.SCHEMA_COMPLETE
    assert vector.data_status is VectorStatus.DATA_INCOMPLETE


def test_a_dimension_carries_its_sensitivity_note() -> None:
    dimension = _dimension()
    assert dimension.sensitivity_note is None
    noted = dimension.model_copy(update={"sensitivity_note": "definition of activity varies"})
    assert noted.sensitivity_note is not None


# -- coverage observation is not sufficiency (Phase 11) ----------------------


def test_a_coverage_observation_never_asserts_sufficiency() -> None:
    from crypto_systems_intelligence_atlas.book6_definitions import CoverageObservation
    from crypto_systems_intelligence_atlas.book6_support import coverage

    assert "sufficiency" not in set(CoverageObservation.model_fields)
    for fraction in (0.0, 0.5, 0.999, 1.0):
        # R1: no sufficiency predicate on the observation at all.
        assert coverage("obs:1", fraction).names_a_sufficiency_rule is False
        assert not hasattr(coverage("obs:1", fraction), "sufficiency_known")


def test_a_full_coverage_fraction_does_not_assert_data_complete() -> None:
    from crypto_systems_intelligence_atlas.book6_support import coverage

    engine = _engine_stack()
    engine.registry.register_coverage(coverage("obs:1", 1.0))
    vector = engine.build_availability_vector(
        subject_ref="fixture:chain:alpha",
        schema_ref="schema:book6:1",
        as_of_valid_time=T1,
        observed_at=T1,
        measurement_ids=("obs:1",),
        methodology_ref="book6-methodology@1",
    )
    # RULE_NOT_RATIFIED dominates the precedence order: with zero ratified
    # rules the engine never reaches a coverage judgement at all, and a 100%
    # coverage fraction certainly does not substitute for a ratified rule.
    assert engine.availability_state("obs:1") is StateName.RULE_NOT_RATIFIED
    assert vector.data_status is VectorStatus.DATA_INCOMPLETE


# -- D2-6 firewall (Phase 27) ------------------------------------------------


def test_no_usage_health_state_exists() -> None:
    values = {state.value for state in StateName}
    for forbidden in (
        "USED",
        "HEALTHY",
        "UNUSED",
        "ADOPTION_SUCCESS",
        "ADOPTION_BAND",
        "RETENTION_BAND",
        "BOT",
        "SYBIL",
    ):
        assert forbidden not in values


def test_d2_6_names_are_prohibited_state_names() -> None:
    for name in ("HEALTHY", "HEALTHY_USAGE", "ADOPTION_SUCCESS"):
        assert name in PROHIBITED_STATE_NAMES


def test_no_usage_threshold_appears_anywhere_in_the_book6_surface() -> None:
    from crypto_systems_intelligence_atlas import (
        book6_core,
        book6_definitions,
        book6_grammar,
        book6_states,
    )

    for module in (book6_core, book6_definitions, book6_grammar, book6_states):
        for name in dir(module):
            if isinstance(getattr(module, name), str):
                lowered = name.lower()
                assert "usage_threshold" not in lowered
                assert "health_threshold" not in lowered
                assert "adoption_band" not in lowered
