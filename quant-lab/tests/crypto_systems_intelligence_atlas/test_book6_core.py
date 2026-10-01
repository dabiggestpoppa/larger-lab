"""Book 6 core: grammar distinctness, provenance authority, definitions, records.

Covers the ratified core contracts: the grammar must not collapse, Book 6 must
remain a Book 2 consumer (never a claim minter), a metric name must not be a
definition, and a measurement record must enforce its value/missingness and
window disciplines.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from crypto_systems_intelligence_atlas.book6_definitions import (
    ComparabilityClass,
    DenominatorRule,
    MetricDefinition,
)
from crypto_systems_intelligence_atlas.book6_grammar import (
    GrammarCategory,
    MeasurementCategory,
    MeasurementRole,
    MissingnessState,
    ObservationStatus,
    RestatementReason,
    SubjectDomain,
    WindowClass,
)
from crypto_systems_intelligence_atlas.book6_provenance import (
    Book6Provenance,
    Book6ProvenanceError,
)
from crypto_systems_intelligence_atlas.book6_records import (
    MeasurementObservation,
    MeasurementRecordError,
)
from crypto_systems_intelligence_atlas.book6_registry import Book6RegistryError
from crypto_systems_intelligence_atlas.book6_support import (
    NOW,
    build_engine,
    definition,
    register_definition,
    register_measurement,
    windowed_observation,
)

CLAIM = "fixture:claim:measurement"


# -- grammar distinctness (Phase 3) -----------------------------------------


def test_grammar_categories_remain_distinct_types() -> None:
    assert GrammarCategory.RATE is not GrammarCategory.STOCK
    assert GrammarCategory.RATE.value != GrammarCategory.STOCK.value
    assert len({c.value for c in GrammarCategory}) == 21


def test_count_is_not_sum_and_flow_is_not_stock() -> None:
    assert MeasurementCategory.COUNT is not MeasurementCategory.FLOW
    assert MeasurementCategory.FLOW is not MeasurementCategory.STOCK
    assert MeasurementCategory.RATE is not MeasurementCategory.RATIO


def test_normalized_is_a_distinct_role() -> None:
    assert MeasurementRole.NATIVE is not MeasurementRole.DERIVED
    assert MeasurementRole.NORMALIZED not in (
        MeasurementRole.NATIVE,
        MeasurementRole.DERIVED,
    )


# -- provenance authority (Phase 2) -----------------------------------------


def test_measurement_is_not_a_book2_claim() -> None:
    """D6M-1=A: a measurement cites Book 2 authority; it is never a claim."""

    engine, _, _, _ = build_engine(CLAIM)
    observation = windowed_observation(
        "obs:1", "m:supply", value=42.0, missingness=MissingnessState.OBSERVED, claim_refs=(CLAIM,)
    )
    assert not hasattr(observation, "claim_state")
    assert not hasattr(observation, "qualifier")
    assert observation.source_claim_refs == (CLAIM,)


def test_book6_provenance_requires_explicit_resolver() -> None:
    engine, _, _, _ = build_engine(CLAIM)
    assert isinstance(engine.provenance, Book6Provenance)
    with pytest.raises(Book6ProvenanceError, match="require an explicit provenance"):
        Book6Provenance(engine.provenance.claim_store, engine.provenance.evidence_store, require_provenance=False)


def test_unknown_claim_ref_fails_closed() -> None:
    engine, _, _, _ = build_engine(CLAIM)
    with pytest.raises(Book6ProvenanceError, match="unknown Book 2 claim"):
        engine.provenance.resolve_claim("fixture:claim:nonexistent")


def test_value_bearing_observation_requires_book2_authority() -> None:
    engine, _, _, _ = build_engine(CLAIM)
    register_definition(engine, definition("m:supply"))
    with pytest.raises(ValidationError, match="must cite Book 2 source authority"):
        windowed_observation(
            "obs:none",
            "m:supply",
            value=1.0,
            missingness=MissingnessState.OBSERVED,
            claim_refs=(),
        )


# -- metric definition (Phase 4) -------------------------------------------


def test_metric_name_alone_is_not_a_definition() -> None:
    engine, _, _, _ = build_engine(CLAIM)
    with pytest.raises(Exception):
        MetricDefinition(
            metric_id="m:active_addresses",
            name="active addresses",
            semantic_definition="",
            subject_domain=SubjectDomain.CHAIN,
            category=MeasurementCategory.COUNT,
            unit="accounts",
            role=MeasurementRole.NATIVE,
            window_class=WindowClass.DAILY,
            aggregation=__import__(
                "crypto_systems_intelligence_atlas.book6_definitions", fromlist=["x"]
            ).AggregationSemantics.SUM,
            denominator_rule=DenominatorRule.NOT_APPLICABLE,
            allowed_source_families=(),
            required_evidence_semantics="",
            methodology=definition("m:seed").methodology,
            comparability_class=ComparabilityClass.CHAIN_WITHIN_FAMILY,
        )


def test_ratio_definition_must_declare_denominator_rule() -> None:
    with pytest.raises(ValidationError, match="ratio metric must declare"):
        definition(
            "m:bad_ratio",
            category=MeasurementCategory.RATIO,
            denominator_rule=DenominatorRule.NOT_APPLICABLE,
        )


def test_cross_architecture_class_may_not_be_scoped_to_families() -> None:
    with pytest.raises(ValidationError, match="cross-architecture"):
        definition(
            "m:scoped_cross",
            comparability_class=ComparabilityClass.CROSS_ARCHITECTURE,
            applies_to=("POS", "BFT_FEDERATION"),
        )


def test_architecture_applicability_is_an_allow_list() -> None:
    metric = definition("m:validator_count", applies_to=("POS",))
    assert metric.applies_to("POS") is True
    assert metric.applies_to("POW") is False


# -- window discipline (Phase 9) -------------------------------------------


def test_windowed_metric_requires_explicit_interval() -> None:
    with pytest.raises(ValidationError, match="requires an explicit"):
        MeasurementObservation(
            measurement_id="obs:bad-window",
            subject_ref="fixture:chain:alpha",
            metric_definition_ref="m:flow",
            category=MeasurementCategory.FLOW,
            missingness_state=MissingnessState.OBSERVED,
            value=5.0,
            unit="tx",
            valid_time=NOW,
            observed_at=NOW,
            window_class=WindowClass.DAILY,
            window_start=None,
            window_end=None,
            methodology_ref="book6-methodology",
            methodology_version="1",
            source_claim_refs=(CLAIM,),
            native_scope="fixture",
        )


def test_instantaneous_metric_may_not_declare_interval() -> None:
    with pytest.raises(ValidationError, match="is instantaneous"):
        MeasurementObservation(
            measurement_id="obs:bad-instant",
            subject_ref="fixture:chain:alpha",
            metric_definition_ref="m:supply",
            category=MeasurementCategory.STOCK,
            missingness_state=MissingnessState.OBSERVED,
            value=1.0,
            unit="native-unit",
            valid_time=NOW,
            observed_at=NOW,
            window_class=WindowClass.INSTANTANEOUS,
            window_start=NOW,
            window_end=NOW,
            methodology_ref="book6-methodology",
            methodology_version="1",
            source_claim_refs=(CLAIM,),
            native_scope="fixture",
        )


# -- value discipline (Phases 6-8) -----------------------------------------


def test_value_bearing_state_requires_value_and_unit() -> None:
    with pytest.raises(ValidationError, match="must carry its observed value"):
        windowed_observation(
            "obs:novalue",
            "m:supply",
            value=None,
            missingness=MissingnessState.OBSERVED,
            claim_refs=(CLAIM,),
        )


def test_supersession_requires_restatement_reason() -> None:
    with pytest.raises(ValidationError, match="restatement reason"):
        windowed_observation(
            "obs:v2",
            "m:supply",
            value=2.0,
            missingness=MissingnessState.OBSERVED,
            claim_refs=(CLAIM,),
            supersedes="obs:v1",
        )


def test_superseded_observation_must_name_its_successor() -> None:
    with pytest.raises(ValidationError, match="must name the observation"):
        windowed_observation(
            "obs:v1",
            "m:supply",
            value=1.0,
            missingness=MissingnessState.OBSERVED,
            claim_refs=(CLAIM,),
            status=ObservationStatus.SUPERSEDED,
        )


def test_valid_restatement_is_constructible() -> None:
    observation = windowed_observation(
        "obs:v2",
        "m:supply",
        value=2.0,
        missingness=MissingnessState.OBSERVED,
        claim_refs=(CLAIM,),
        supersedes="obs:v1",
        restatement_reason=RestatementReason.SOURCE_BACKFILL,
    )
    assert observation.supersedes_measurement_id == "obs:v1"


# -- registry: registration is not authority (Phase 29) --------------------


def test_measurement_requires_registered_definition() -> None:
    engine, _, _, _ = build_engine(CLAIM)
    observation = windowed_observation(
        "obs:1",
        "m:undeclared",
        value=1.0,
        missingness=MissingnessState.OBSERVED,
        claim_refs=(CLAIM,),
    )
    with pytest.raises(Book6RegistryError, match="is not registered"):
        register_measurement(engine, observation)


def test_observation_drifting_from_definition_is_refused() -> None:
    engine, _, _, _ = build_engine(CLAIM)
    register_definition(engine, definition("m:supply", unit="native-unit"))
    forged = windowed_observation(
        "obs:forged",
        "m:supply",
        value=1.0,
        missingness=MissingnessState.OBSERVED,
        claim_refs=(CLAIM,),
        unit="other-unit",
    )
    with pytest.raises(MeasurementRecordError, match="contradicts definition unit"):
        register_measurement(engine, forged)


def test_engine_exposes_only_registered_definitions() -> None:
    engine, _, _, _ = build_engine(CLAIM)
    with pytest.raises(Book6RegistryError, match="not registered"):
        engine.registry.definition("m:absent")
