"""Book 6 sensitivity — methodology sensitivity (6D.2) and cross-source parity (6D.4).

The ratified obligation is not to resolve disagreement but to make it VISIBLE.
Two reasonable methodologies routinely disagree, and four source families
routinely disagree. The suite proves the findings name the disagreement, choose
no winner, average nothing, and invent no tolerance — because choosing is a
state derivation that would need a ratified rule, and a tolerance is exactly
such a rule.
"""

from __future__ import annotations

import pytest

from crypto_systems_intelligence_atlas.book6_grammar import MissingnessState
from crypto_systems_intelligence_atlas.book6_sensitivity import (
    NO_CONSENSUS_VALUE_IS_COMPUTED,
    NO_PREFERRED_METHODOLOGY,
    NO_TOLERANCE_IS_INVENTED,
    MethodologyVariant,
    ParityOutcome,
    SensitivityError,
    SensitivityOutcome,
    compare_methodology_variants,
    compare_sources,
)
from crypto_systems_intelligence_atlas.book6_support import (
    T1,
    definition,
    register_measurement,
    windowed_observation,
)
from crypto_systems_intelligence_atlas.book6_definitions import SourceFamily
from crypto_systems_intelligence_atlas.book6_support import build_engine_with_definitions

CLAIM_A = "fixture:claim:methodology-a"
CLAIM_B = "fixture:claim:methodology-b"
CLAIM_C = "fixture:claim:methodology-c"

METRIC_EOA = "metric.sensitivity.active_accounts_eoa"
METRIC_CLUSTER = "metric.sensitivity.active_accounts_cluster"
METRIC_GROSS = "metric.sensitivity.volume_gross"
METRIC_NET = "metric.sensitivity.volume_net"
METRIC_FEES = "metric.sensitivity.fees_paid"
METRIC_REVENUE = "metric.sensitivity.protocol_revenue"
METRIC_CONTRIBUTORS = "metric.sensitivity.developer_contributors"
METRIC_COMMITS = "metric.sensitivity.developer_commits"
METRIC_NATIVE_CAPITAL = "metric.sensitivity.native_capital"
METRIC_VALUED_CAPITAL = "metric.sensitivity.valued_capital"

SOURCE_METRIC = "metric.parity.transactions"
SOURCE_FAMILY_METRIC = "metric.parity.transactions_indexer"


def _engine(*metric_ids: str, claim_ids: tuple[str, ...] = (CLAIM_A,)):
    return build_engine_with_definitions(
        *(definition(metric_id) for metric_id in metric_ids), claim_ids=claim_ids
    )


def _observe(engine, measurement_id, metric_id, *, value, claim=CLAIM_A):
    register_measurement(engine, 
        windowed_observation(
            measurement_id,
            metric_id,
            value=value,
            missingness=(
                MissingnessState.OBSERVED if value is not None else MissingnessState.NOT_COLLECTED
            ),
            claim_refs=(claim,),
        )
    )


# -- methodology sensitivity is reported, not resolved (Phase 33) ------------


def test_agreeing_methodologies_are_reported_independent() -> None:
    engine = _engine(METRIC_EOA, METRIC_CLUSTER, claim_ids=(CLAIM_A, CLAIM_B))
    _observe(engine, "obs:1", METRIC_EOA, value=5.0, claim=CLAIM_A)
    _observe(engine, "obs:2", METRIC_CLUSTER, value=5.0, claim=CLAIM_B)
    finding = compare_methodology_variants(
        engine.registry,
        subject_ref="fixture:chain:alpha",
        construct_label="active accounts",
        as_of_valid_time=T1,
        measurement_ids=("obs:1", "obs:2"),
    )
    assert finding.outcome is SensitivityOutcome.METHODOLOGY_INDEPENDENT
    assert [v.value for v in finding.variants] == [5.0, 5.0]


def test_disagreeing_methodologies_are_reported_sensitive() -> None:
    engine = _engine(METRIC_EOA, METRIC_CLUSTER, claim_ids=(CLAIM_A, CLAIM_B))
    _observe(engine, "obs:1", METRIC_EOA, value=5.0, claim=CLAIM_A)
    _observe(engine, "obs:2", METRIC_CLUSTER, value=2.0, claim=CLAIM_B)
    finding = compare_methodology_variants(
        engine.registry,
        subject_ref="fixture:chain:alpha",
        construct_label="active accounts",
        as_of_valid_time=T1,
        measurement_ids=("obs:1", "obs:2"),
    )
    assert finding.outcome is SensitivityOutcome.METHODOLOGY_SENSITIVE
    assert [v.value for v in finding.variants] == [5.0, 2.0]


def test_a_sensitive_finding_names_no_winner() -> None:
    engine = _engine(METRIC_EOA, METRIC_CLUSTER, claim_ids=(CLAIM_A, CLAIM_B))
    _observe(engine, "obs:1", METRIC_EOA, value=5.0, claim=CLAIM_A)
    _observe(engine, "obs:2", METRIC_CLUSTER, value=2.0, claim=CLAIM_B)
    finding = compare_methodology_variants(
        engine.registry,
        subject_ref="fixture:chain:alpha",
        construct_label="active accounts",
        as_of_valid_time=T1,
        measurement_ids=("obs:1", "obs:2"),
    )
    fields = set(type(finding).model_fields)
    assert fields.isdisjoint(
        {"preferred", "best", "canonical", "default", "winner", "score", "severity"}
    )
    assert "no methodology is preferred" in finding.note


def test_each_variant_keeps_its_own_methodology_identity() -> None:
    engine = _engine(METRIC_EOA, METRIC_CLUSTER, claim_ids=(CLAIM_A, CLAIM_B))
    _observe(engine, "obs:1", METRIC_EOA, value=5.0, claim=CLAIM_A)
    _observe(engine, "obs:2", METRIC_CLUSTER, value=2.0, claim=CLAIM_B)
    finding = compare_methodology_variants(
        engine.registry,
        subject_ref="fixture:chain:alpha",
        construct_label="active accounts",
        as_of_valid_time=T1,
        measurement_ids=("obs:1", "obs:2"),
    )
    assert [v.methodology_ref for v in finding.variants] == [
        "book6-methodology",
        "book6-methodology",
    ]
    assert all(v.declared_meaning for v in finding.variants)


def test_an_unobserved_variant_makes_the_comparison_undetermined_not_zero() -> None:
    engine = _engine(METRIC_EOA, METRIC_CLUSTER, claim_ids=(CLAIM_A, CLAIM_B))
    _observe(engine, "obs:1", METRIC_EOA, value=5.0, claim=CLAIM_A)
    _observe(engine, "obs:2", METRIC_CLUSTER, value=None, claim=CLAIM_B)
    finding = compare_methodology_variants(
        engine.registry,
        subject_ref="fixture:chain:alpha",
        construct_label="active accounts",
        as_of_valid_time=T1,
        measurement_ids=("obs:1", "obs:2"),
    )
    assert finding.outcome is SensitivityOutcome.UNDETERMINED
    assert finding.variants[1].value is None
    assert "absence is not zero" in finding.note


def test_comparing_one_methodology_to_itself_is_refused() -> None:
    engine = _engine(METRIC_EOA)
    _observe(engine, "obs:1", METRIC_EOA, value=5.0)
    with pytest.raises(SensitivityError, match="at least two methodologies"):
        compare_methodology_variants(
            engine.registry,
            subject_ref="fixture:chain:alpha",
            construct_label="active accounts",
            as_of_valid_time=T1,
            measurement_ids=("obs:1",),
        )


def test_sensitivity_finding_carries_no_numeric_severity() -> None:
    engine = _engine(METRIC_EOA, METRIC_CLUSTER, claim_ids=(CLAIM_A, CLAIM_B))
    _observe(engine, "obs:1", METRIC_EOA, value=5.0, claim=CLAIM_A)
    _observe(engine, "obs:2", METRIC_CLUSTER, value=2.0, claim=CLAIM_B)
    finding = compare_methodology_variants(
        engine.registry,
        subject_ref="fixture:chain:alpha",
        construct_label="active accounts",
        as_of_valid_time=T1,
        measurement_ids=("obs:1", "obs:2"),
    )
    numeric = {
        name
        for name in type(finding).model_fields
        if isinstance(getattr(finding, name), (int, float))
    }
    assert numeric == set()
    assert "variants" not in numeric


# -- the five ratified sensitivity examples -----------------------------------


@pytest.mark.parametrize(
    ("construct", "left_metric", "right_metric", "left_value", "right_value"),
    [
        ("active accounts", METRIC_EOA, METRIC_CLUSTER, 5.0, 2.0),
        ("volume", METRIC_GROSS, METRIC_NET, 100.0, 60.0),
        ("protocol economics", METRIC_FEES, METRIC_REVENUE, 3.0, 1.0),
        ("developer activity", METRIC_CONTRIBUTORS, METRIC_COMMITS, 12.0, 400.0),
        ("capital", METRIC_NATIVE_CAPITAL, METRIC_VALUED_CAPITAL, 1000.0, 2500.0),
    ],
    ids=[
        "active-account-definitions",
        "gross-vs-net-volume",
        "fees-vs-revenue",
        "contributors-vs-commits",
        "native-vs-valued-capital",
    ],
)
def test_each_ratified_methodology_divergence_is_surfaced(
    construct: str,
    left_metric: str,
    right_metric: str,
    left_value: float,
    right_value: float,
) -> None:
    engine = _engine(left_metric, right_metric, claim_ids=(CLAIM_A, CLAIM_B))
    _observe(engine, "obs:left", left_metric, value=left_value, claim=CLAIM_A)
    _observe(engine, "obs:right", right_metric, value=right_value, claim=CLAIM_B)
    finding = compare_methodology_variants(
        engine.registry,
        subject_ref="fixture:chain:alpha",
        construct_label=construct,
        as_of_valid_time=T1,
        measurement_ids=("obs:left", "obs:right"),
    )
    assert finding.outcome is SensitivityOutcome.METHODOLOGY_SENSITIVE
    assert finding.construct_label == construct
    assert left_value in {v.value for v in finding.variants}
    assert right_value in {v.value for v in finding.variants}


# -- cross-source parity preserves divergence (Phase 34) ---------------------


def _parity_engine():
    engine = build_engine_with_definitions(
        definition(SOURCE_METRIC, source_families=(SourceFamily.NATIVE_CHAIN,)),
        definition(
            SOURCE_FAMILY_METRIC,
            source_families=(SourceFamily.INDEPENDENT_INDEXER,),
        ),
        claim_ids=(CLAIM_A, CLAIM_B),
    )
    return engine


def test_sources_that_agree_are_reported_agreeing() -> None:
    engine = _parity_engine()
    _observe(engine, "obs:native", SOURCE_METRIC, value=100.0, claim=CLAIM_A)
    _observe(engine, "obs:indexer", SOURCE_FAMILY_METRIC, value=100.0, claim=CLAIM_B)
    finding = compare_sources(
        engine.registry,
        subject_ref="fixture:chain:alpha",
        construct_label="executed transactions",
        as_of_valid_time=T1,
        measurement_ids=("obs:native", "obs:indexer"),
    )
    assert finding.outcome is ParityOutcome.SOURCES_AGREE


def test_divergent_sources_are_reported_diverging_and_preserved() -> None:
    engine = _parity_engine()
    _observe(engine, "obs:native", SOURCE_METRIC, value=100.0, claim=CLAIM_A)
    _observe(engine, "obs:indexer", SOURCE_FAMILY_METRIC, value=94.0, claim=CLAIM_B)
    finding = compare_sources(
        engine.registry,
        subject_ref="fixture:chain:alpha",
        construct_label="executed transactions",
        as_of_valid_time=T1,
        measurement_ids=("obs:native", "obs:indexer"),
    )
    assert finding.outcome is ParityOutcome.SOURCES_DIVERGE
    assert [m.value for m in finding.measurements] == [100.0, 94.0]
    assert {m.source_family for m in finding.measurements} == {
        SourceFamily.NATIVE_CHAIN,
        SourceFamily.INDEPENDENT_INDEXER,
    }


def test_no_consensus_value_is_computed_from_divergent_sources() -> None:
    engine = _parity_engine()
    _observe(engine, "obs:native", SOURCE_METRIC, value=100.0, claim=CLAIM_A)
    _observe(engine, "obs:indexer", SOURCE_FAMILY_METRIC, value=94.0, claim=CLAIM_B)
    finding = compare_sources(
        engine.registry,
        subject_ref="fixture:chain:alpha",
        construct_label="executed transactions",
        as_of_valid_time=T1,
        measurement_ids=("obs:native", "obs:indexer"),
    )
    assert not hasattr(finding, "consensus_value")
    assert "consensus" not in set(type(finding).model_fields)
    assert 100.0 in {m.value for m in finding.measurements}
    assert 94.0 in {m.value for m in finding.measurements}
    # the naive mean (97.0) exists nowhere in the finding
    assert 97.0 not in {m.value for m in finding.measurements}


def test_the_module_offers_no_averaging_helper() -> None:
    from crypto_systems_intelligence_atlas import book6_sensitivity

    forbidden = ("mean", "median", "average", "consensus", "blend", "reconcile", "trimmed")
    for name in dir(book6_sensitivity):
        if not callable(getattr(book6_sensitivity, name)) or isinstance(
            getattr(book6_sensitivity, name), type
        ):
            continue
        lowered = name.lower()
        assert not any(token in lowered for token in forbidden), name


def test_an_absent_source_is_not_a_source_that_agrees() -> None:
    engine = _parity_engine()
    _observe(engine, "obs:native", SOURCE_METRIC, value=100.0, claim=CLAIM_A)
    _observe(engine, "obs:indexer", SOURCE_FAMILY_METRIC, value=None, claim=CLAIM_B)
    finding = compare_sources(
        engine.registry,
        subject_ref="fixture:chain:alpha",
        construct_label="executed transactions",
        as_of_valid_time=T1,
        measurement_ids=("obs:native", "obs:indexer"),
    )
    assert finding.outcome is ParityOutcome.UNDETERMINED
    assert "a missing source is not a source that agrees" in finding.note


def test_a_single_source_cannot_be_in_parity_with_itself() -> None:
    engine = _parity_engine()
    _observe(engine, "obs:native", SOURCE_METRIC, value=100.0, claim=CLAIM_A)
    with pytest.raises(SensitivityError, match="at least two sources"):
        compare_sources(
            engine.registry,
            subject_ref="fixture:chain:alpha",
            construct_label="executed transactions",
            as_of_valid_time=T1,
            measurement_ids=("obs:native",),
        )


def test_no_tolerance_is_invented_for_float_agreement() -> None:
    """Two floats that differ by 1e-12 DIVERGE; smoothing them needs a ratified rule."""

    engine = _parity_engine()
    _observe(engine, "obs:native", SOURCE_METRIC, value=100.0, claim=CLAIM_A)
    _observe(engine, "obs:indexer", SOURCE_FAMILY_METRIC, value=100.0 + 1e-12, claim=CLAIM_B)
    finding = compare_sources(
        engine.registry,
        subject_ref="fixture:chain:alpha",
        construct_label="executed transactions",
        as_of_valid_time=T1,
        measurement_ids=("obs:native", "obs:indexer"),
    )
    assert finding.outcome is ParityOutcome.SOURCES_DIVERGE
    assert "no consensus value is computed" in finding.note


def test_no_tolerance_field_or_parameter_exists() -> None:
    from crypto_systems_intelligence_atlas import book6_sensitivity

    assert "tolerance" not in dir(book6_sensitivity)
    for model in (MethodologyVariant,):
        assert "tolerance" not in set(model.model_fields)


def test_the_sensitivity_constants_are_true() -> None:
    assert NO_PREFERRED_METHODOLOGY is True
    assert NO_CONSENSUS_VALUE_IS_COMPUTED is True
    assert NO_TOLERANCE_IS_INVENTED is True
