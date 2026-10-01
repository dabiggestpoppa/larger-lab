"""Book 6 temporal — revision history, Book 2 decay, and bitemporal prices.

Time is where measurement systems quietly destroy truth, so this suite attacks
it from four directions:

- **Revision and supersession.** A restated value creates a NEW observation that
  supersedes the prior one. The prior value is retained and stays queryable; a
  chain reorg is bounded to its own window and never rewrites the whole
  history.
- **Book 2 decay propagation.** A measurement registered against a current Book
  2 claim loses authority the moment that claim legally decays, and regains it
  when Book 2 legally restores. Rejection is not an irreversible tombstone.
- **Bitemporal price staleness.** A stale CURRENT price makes a current
  valuation unavailable without invalidating a historical one, and a
  source-unavailable price is absent rather than zero.
- **Replay determinism.** The same sequence of registrations and transitions
  produces the same history every time, with no wall-clock dependence.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from crypto_systems_intelligence_atlas.book6_grammar import (
    INTERVAL_WINDOW_CLASSES,
    MissingnessState,
    ObservationStatus,
    RestatementReason,
    WINDOW_BOUNDED_RESTATEMENT_REASONS,
    WindowClass,
    windows_are_comparable,
)
from crypto_systems_intelligence_atlas.book6_records import MeasurementObservation
from crypto_systems_intelligence_atlas.book6_normalization import check_windows_comparable
from crypto_systems_intelligence_atlas.book6_provenance import Book6ProvenanceError
from crypto_systems_intelligence_atlas.book6_registry import Book6RegistryError
from crypto_systems_intelligence_atlas.book6_support import (
    normalization_methodology,
    NOW,
    T1,
    T2,
    build_engine,
    decay_claim,
    definition,
    register_definition,
    register_measurement,
    windowed_observation,
)
from crypto_systems_intelligence_atlas.book6_valuation import (
    PRICE_AUTHORITY_MATRIX,
    PriceObservation,
    PriceObservationClass,
    ValuationObservation,
    ValuationPurpose,
)

CLAIM = "fixture:claim:measurement"
DECAYABLE = "fixture:claim:decayable"
METRIC = "metric.native.native_transactions"
WINDOWED_METRIC = "metric.native.monthly_transactions"

REV = timedelta(days=30)


def _stack(*claim_ids: str):
    engine, claim_store, _, service = build_engine(*claim_ids)
    register_definition(engine, definition(METRIC))
    return engine, claim_store, service


def _observe(engine, measurement_id, *, value, at=T1, claim=CLAIM, **kwargs):
    register_measurement(engine, 
        windowed_observation(
            measurement_id,
            METRIC,
            value=value,
            missingness=MissingnessState.OBSERVED,
            claim_refs=(claim,),
            valid_time=at,
            **kwargs,
        )
    )


# -- revision and supersession (Phase 10) -------------------------------------


def test_a_restatement_creates_a_new_observation_rather_than_overwriting() -> None:
    engine, _, _ = _stack()
    _observe(engine, "obs:1", value=100.0)
    _observe(
        engine,
        "obs:2",
        value=101.0,
        at=T2,
        supersedes="obs:1",
        restatement_reason=RestatementReason.LATE_BLOCKS,
    )
    # the original is still there, unchanged
    assert engine.registry.registered_measurement("obs:1").value == 100.0
    assert engine.registry.registered_measurement("obs:2").value == 101.0
    assert engine.registry.registered_refs() == ("obs:1", "obs:2")


def test_the_supersession_chain_is_linear_and_ordered() -> None:
    engine, _, _ = _stack()
    _observe(engine, "obs:1", value=100.0)
    _observe(
        engine,
        "obs:2",
        value=101.0,
        at=T2,
        supersedes="obs:1",
        restatement_reason=RestatementReason.LATE_BLOCKS,
    )
    history = engine.registry.measurement_history("obs:1")
    assert [o.measurement_id for o in history] == ["obs:1", "obs:2"]
    assert [o.value for o in history] == [100.0, 101.0]


def test_a_forked_supersession_chain_is_refused() -> None:
    engine, _, _ = _stack()
    _observe(engine, "obs:1", value=100.0)
    for child, value in (("obs:2a", 101.0), ("obs:2b", 102.0)):
        _observe(
            engine,
            child,
            value=value,
            at=T2,
            supersedes="obs:1",
            restatement_reason=RestatementReason.LATE_BLOCKS,
        )
    with pytest.raises(Book6RegistryError, match="supersession must be linear"):
        engine.registry.measurement_history("obs:1")


def test_history_is_retained_across_many_revisions() -> None:
    engine, _, _ = _stack()
    previous = None
    for index in range(5):
        measurement_id = f"obs:{index}"
        _observe(
            engine,
            measurement_id,
            value=100.0 + index,
            at=T1 + REV * index,
            supersedes=previous,
            restatement_reason=RestatementReason.SOURCE_BACKFILL,
        )
        previous = measurement_id
    history = engine.registry.measurement_history("obs:0")
    assert [o.value for o in history] == [100.0, 101.0, 102.0, 103.0, 104.0]
    assert len(history) == 5


def test_every_ratified_restatement_reason_is_representable() -> None:
    for reason in RestatementReason:
        engine, _, _ = _stack()
        _observe(engine, "obs:1", value=100.0)
        _observe(
            engine,
            "obs:2",
            value=101.0,
            at=T2,
            supersedes="obs:1",
            restatement_reason=reason,
        )
        assert engine.registry.registered_measurement("obs:2").restatement_reason is reason


def test_a_reorg_is_window_bounded() -> None:
    """A reorg restates its own interval; it may not rewrite the whole history."""

    assert RestatementReason.CHAIN_REORG in WINDOW_BOUNDED_RESTATEMENT_REASONS
    assert RestatementReason.SOURCE_BACKFILL not in WINDOW_BOUNDED_RESTATEMENT_REASONS
    assert RestatementReason.LATE_BLOCKS not in WINDOW_BOUNDED_RESTATEMENT_REASONS


def test_a_methodology_change_creates_a_new_version_not_an_edit() -> None:
    """A new methodology is a new metric definition, never an in-place edit."""

    from crypto_systems_intelligence_atlas.book6_definitions import (
        MeasurementMethodology,
        MetricDefinition,
    )

    engine, _, _ = _stack()
    _observe(engine, "obs:1", value=100.0, methodology_ref="book6-methodology")

    v2_method = MeasurementMethodology(
        methodology_ref="book6-methodology-v2",
        version="2",
        formula="x = declared alternative construction",
        window_rule="declared window class of the metric",
        filters=("no-fabricated-absence",),
        denominator_rule="explicit measured denominator or not applicable",
        source_selection="first-party Book 2-backed source",
        identity_rule="subject identity rule declared per metric",
    )
    base = engine.registry.definition(METRIC)
    register_definition(engine, 
        MetricDefinition(
            metric_id=f"{METRIC}_v2",
            name=f"{METRIC}_v2",
            semantic_definition=base.semantic_definition,
            subject_domain=base.subject_domain,
            category=base.category,
            unit=base.unit,
            role=base.role,
            window_class=base.window_class,
            aggregation=base.aggregation,
            denominator_rule=base.denominator_rule,
            allowed_source_families=base.allowed_source_families,
            required_evidence_semantics=base.required_evidence_semantics,
            methodology=v2_method,
            comparability_class=base.comparability_class,
        )
    )
    register_measurement(engine, 
        windowed_observation(
            "obs:2",
            f"{METRIC}_v2",
            value=200.0,
            missingness=MissingnessState.OBSERVED,
            claim_refs=(CLAIM,),
            valid_time=T2,
            methodology_ref="book6-methodology-v2",
            methodology_version="2",
            supersedes="obs:1",
            restatement_reason=RestatementReason.METHODOLOGY_CHANGE,
        )
    )
    assert (
        engine.registry.registered_measurement("obs:1").methodology_identity
        == "book6-methodology@1"
    )
    assert (
        engine.registry.registered_measurement("obs:2").methodology_identity
        == "book6-methodology-v2@2"
    )
    assert engine.registry.registered_measurement("obs:1").value == 100.0


def test_an_observation_cannot_be_registered_under_the_wrong_methodology() -> None:
    from crypto_systems_intelligence_atlas.book6_records import MeasurementRecordError

    engine, _, _ = _stack()
    with pytest.raises(MeasurementRecordError, match="is not the definition's methodology"):
        register_measurement(engine, 
            windowed_observation(
                "obs:wrong",
                METRIC,
                value=1.0,
                missingness=MissingnessState.OBSERVED,
                claim_refs=(CLAIM,),
                methodology_ref="book6-methodology-v2",
            )
        )


def test_a_superseded_record_may_be_marked_and_stays_queryable() -> None:
    engine, _, _ = _stack()
    _observe(engine, "obs:1", value=100.0)
    marked = engine.registry.registered_measurement("obs:1").model_copy(
        update={
            "status": ObservationStatus.SUPERSEDED,
            "supersedes_measurement_id": "obs:0",
            "restatement_reason": RestatementReason.LATE_BLOCKS,
        }
    )
    assert marked.status is ObservationStatus.SUPERSEDED
    assert marked.value == 100.0  # value preserved, not erased
    # the registry still holds the original, unfalsified
    assert engine.registry.registered_measurement("obs:1").status is ObservationStatus.OBSERVED


# -- window and calendar identity (Phase 9) ----------------------------------


def test_every_ratified_window_class_exists() -> None:
    assert {w.value for w in WindowClass} == {
        "INSTANTANEOUS",
        "BLOCK_EPOCH",
        "DAILY",
        "ROLLING",
        "CALENDAR_WEEK",
        "CALENDAR_MONTH",
        "QUARTER",
        "LIFETIME",
        "EVENT_BOUNDED",
        "CUSTOM",
    }


def _raw_observation(**overrides):
    """Build a record with full control of its window fields."""

    payload = {
        "measurement_id": "obs:x",
        "subject_ref": "fixture:chain:alpha",
        "metric_definition_ref": METRIC,
        "category": "STOCK",
        "missingness_state": "OBSERVED",
        "value": 1.0,
        "unit": "native-unit",
        "valid_time": T1,
        "observed_at": T1,
        "window_class": "INSTANTANEOUS",
        "methodology_ref": "book6-methodology",
        "methodology_version": "1",
        "source_claim_refs": (CLAIM,),
        "native_scope": "fixture:architecture:pos",
        "architecture_family": "POS",
    }
    payload.update(overrides)
    return MeasurementObservation(**payload)


@pytest.mark.parametrize(
    "window_class",
    sorted(INTERVAL_WINDOW_CLASSES, key=lambda w: w.value),
    ids=lambda w: w.value,
)
def test_an_interval_window_requires_an_explicit_closed_open_interval(
    window_class: WindowClass,
) -> None:
    with pytest.raises(ValidationError, match="explicit"):
        _raw_observation(window_class=window_class.value)


def test_an_instantaneous_window_may_not_declare_an_interval() -> None:
    observation = _raw_observation()
    assert observation.window_start is None
    with pytest.raises(ValidationError, match="may not declare an interval"):
        _raw_observation(window_start=T1, window_end=T2)


def test_a_window_may_not_end_before_it_starts() -> None:
    with pytest.raises(ValidationError, match="window_start must precede window_end"):
        _raw_observation(
            window_class="CALENDAR_MONTH", window_start=T2, window_end=T1
        )


def test_incompatible_windows_are_never_compared_silently() -> None:
    assert windows_are_comparable(WindowClass.ROLLING, WindowClass.CALENDAR_MONTH) is False
    with pytest.raises(Exception, match="not comparable"):
        check_windows_comparable("ROLLING", "CALENDAR_MONTH")


# -- Book 2 decay propagation (Phase 31) --------------------------------------


def test_a_current_measurement_is_authoritative() -> None:
    engine, _, _ = _stack(DECAYABLE)
    _observe(engine, "obs:1", value=7.0, claim=DECAYABLE)
    assert engine.current_value("obs:1") == 7.0
    assert engine.registry.is_authoritative_now("obs:1") is True


def test_a_stale_claim_decays_the_measurement_authority() -> None:
    engine, claim_store, service = _stack(DECAYABLE)
    _observe(engine, "obs:1", value=7.0, claim=DECAYABLE)
    decay_claim(service, claim_store, DECAYABLE, "STALE")
    assert engine.provenance.claim_is_current(DECAYABLE) is False
    assert engine.registry.is_authoritative_now("obs:1") is False
    with pytest.raises(Book6RegistryError, match="no current Book 2 authority"):
        engine.current_value("obs:1")


def test_a_contested_claim_decays_the_measurement_authority() -> None:
    engine, claim_store, service = _stack(DECAYABLE)
    _observe(engine, "obs:1", value=7.0, claim=DECAYABLE)
    decay_claim(service, claim_store, DECAYABLE, "CONTESTED")
    with pytest.raises(Book6RegistryError, match="no current Book 2 authority"):
        engine.current_value("obs:1")


def test_where_book_2_restores_authority_book_6_restores_too() -> None:
    """Rejection is not an irreversible tombstone."""

    engine, claim_store, service = _stack(DECAYABLE)
    _observe(engine, "obs:1", value=7.0, claim=DECAYABLE)
    assert engine.current_value("obs:1") == 7.0

    decay_claim(service, claim_store, DECAYABLE, "STALE")
    with pytest.raises(Book6RegistryError):
        engine.current_value("obs:1")

    decay_claim(service, claim_store, DECAYABLE, "OBSERVED", at=T2 + REV)
    assert engine.provenance.claim_is_current(DECAYABLE) is True
    assert engine.current_value("obs:1") == 7.0
    assert engine.registry.is_authoritative_now("obs:1") is True


def test_the_record_survives_the_decay_as_queryable_history() -> None:
    engine, claim_store, service = _stack(DECAYABLE)
    _observe(engine, "obs:1", value=7.0, claim=DECAYABLE)
    decay_claim(service, claim_store, DECAYABLE, "STALE")
    # authority is gone; the record is not deleted or zeroed
    record = engine.registry.registered_measurement("obs:1")
    assert record.value == 7.0
    assert record.measurement_id == "obs:1"
    assert engine.registry.registered_refs() == ("obs:1",)


def test_a_partial_authority_grants_nothing() -> None:
    engine, claim_store, service = _stack(CLAIM, DECAYABLE)
    _observe(engine, "obs:1", value=7.0, claim=CLAIM)
    _observe(engine, "obs:2", value=9.0, claim=DECAYABLE)
    decay_claim(service, claim_store, DECAYABLE, "STALE")
    assert engine.current_value("obs:1") == 7.0
    with pytest.raises(Book6RegistryError):
        engine.current_value("obs:2")


def test_decay_also_gates_normalized_products() -> None:
    from crypto_systems_intelligence_atlas.book6_normalization import (
        NormalizationRule,
        NormalizedMeasurement,
    )

    engine, claim_store, _, service = build_engine(DECAYABLE)
    native_metric = "metric.native.tx"
    normalized_metric = "metric.normalized.tx_per_user"
    register_definition(engine, definition(native_metric))
    register_definition(engine, definition(normalized_metric, unit="per-user"))
    register_measurement(engine, 
        windowed_observation(
            "obs:1",
            native_metric,
            value=7.0,
            missingness=MissingnessState.OBSERVED,
            claim_refs=(DECAYABLE,),
        )
    )
    from crypto_systems_intelligence_atlas.book6_grammar import NormalizationType

    # R1-D6: the divisor is a registered, Book 2-backed observation, so the
    # normalized product is recomputed (7.0 / 2.0 = 3.5) rather than asserted.
    register_measurement(engine,
        windowed_observation(
            "den:seconds",
            native_metric,
            value=2.0,
            missingness=MissingnessState.OBSERVED,
            claim_refs=(DECAYABLE,),
        )
    )
    engine.registry.register_methodology(normalization_methodology())

    rule = NormalizationRule(
        normalization_rule_id="normrule:1",
        input_metric_definition_ref=native_metric,
        input_measurement_refs=("obs:1",),
        normalization_type=NormalizationType.PER_TIME,
        transformation="x = value / seconds",
        denominator_ref="den:seconds",
        methodology_ref="book6-normalization@1",
        valid_time=T1,
        version="1",
        output_metric_definition_ref=normalized_metric,
    )
    engine.registry.register_normalization_rule(rule)
    product = NormalizedMeasurement(
        normalized_measurement_id="norm:1",
        normalization_rule_id="normrule:1",
        native_measurement_refs=("obs:1",),
        normalized_metric_definition_ref=normalized_metric,
        value=3.5,
        unit="per-user",
        valid_time=T1,
    )
    assert engine.normalize(product, rule) is product
    decay_claim(service, claim_store, DECAYABLE, "STALE")
    from crypto_systems_intelligence_atlas.book6_core import Book6EngineError

    with pytest.raises(Book6EngineError):
        engine.normalize(product, rule)


# -- bitemporal price staleness (Phase 32) -----------------------------------


def _valuation(price_class=PriceObservationClass.MARKET_OBSERVATION, *, price_at=NOW, read_at=NOW):
    purpose = next(
        p for p, admissible in PRICE_AUTHORITY_MATRIX.items() if price_class in admissible
    )
    return ValuationObservation(
        valuation_id="val:1",
        subject_ref="fixture:subject:alpha",
        native_quantity=10.0,
        native_unit="TOKEN",
        numeraire="USD",
        purpose=purpose,
        price=PriceObservation(
            price_observation_id="price:1",
            price_class=price_class,
            source_ref="source:venue:1",
            source_claim_refs=("fixture:claim:measurement",),
            price=1.0,
            valid_time=price_at,
            observed_at=price_at,
            coverage=1.0,
        ),
        conversion_methodology_ref="book6-methodology@1",
        valid_time=price_at,
        observed_at=read_at,
        coverage=1.0,
        staleness_bound_seconds=3600,
    )


def test_a_current_price_is_authoritative_now() -> None:
    valuation = _valuation()
    assert valuation.is_stale is False
    assert valuation.is_currently_fresh(valuation.observed_at) is True


def test_a_stale_price_makes_the_current_valuation_unavailable() -> None:
    valuation = _valuation(price_at=NOW, read_at=NOW + timedelta(hours=2))
    assert valuation.is_stale is True
    assert valuation.is_currently_fresh(valuation.observed_at) is False


def test_currently_unavailable_is_not_historically_invalid() -> None:
    historical = _valuation(price_at=NOW)
    read_today = _valuation(price_at=NOW, read_at=NOW + timedelta(days=3650))
    # the historical statement is untouched by today's missing price
    assert historical.is_currently_fresh(historical.observed_at) is True
    assert historical.native_quantity == 10.0
    assert historical.price.price == 1.0
    # and today's unavailability is a statement about today only
    assert read_today.is_currently_fresh(read_today.observed_at) is False
    assert read_today.native_quantity == historical.native_quantity


def test_a_price_from_a_different_purpose_still_diverges() -> None:
    redemption = _valuation(PriceObservationClass.OFFICIAL_REDEMPTION_VALUE)
    market = _valuation(PriceObservationClass.MARKET_OBSERVATION)
    assert redemption.purpose is ValuationPurpose.REDEMPTION_ACCOUNTING
    assert market.purpose is ValuationPurpose.MARKET_VALUATION
    assert redemption.is_currently_fresh(redemption.observed_at)
    assert market.is_currently_fresh(market.observed_at)


def test_a_source_unavailable_price_is_absent_not_zero() -> None:
    with pytest.raises(ValidationError):
        _valuation(price_at=NOW).model_copy(update={}).model_validate(
            {
                **_valuation(price_at=NOW).model_dump(),
                "price": {
                    "price_observation_id": "price:1",
                    "price_class": "MARKET_OBSERVATION",
                    "source_ref": "",
                    "price": 1.0,
                    "valid_time": NOW,
                    "observed_at": NOW,
                    "coverage": 1.0,
                },
            }
        )


def test_a_market_closed_price_is_stale_not_invalid() -> None:
    closed = _valuation(price_at=NOW, read_at=NOW + timedelta(days=3))
    assert closed.price.coverage == 1.0  # the observation is intact
    assert closed.is_stale is True
    assert closed.is_currently_fresh(closed.observed_at) is False


# -- replay determinism -------------------------------------------------------


def test_the_same_sequence_replays_to_the_same_history() -> None:
    def run():
        engine, _, _ = _stack()
        _observe(engine, "obs:1", value=100.0)
        _observe(
            engine,
            "obs:2",
            value=101.0,
            at=T2,
            supersedes="obs:1",
            restatement_reason=RestatementReason.LATE_BLOCKS,
        )
        return [
            (o.measurement_id, o.value, o.status.value, o.valid_time.isoformat())
            for o in engine.registry.measurement_history("obs:1")
        ]

    assert run() == run()


def test_replay_does_not_depend_on_wall_clock_time() -> None:
    engine, _, _ = _stack()
    _observe(engine, "obs:1", value=100.0)
    record = engine.registry.registered_measurement("obs:1")
    assert record.valid_time == T1
    assert record.observed_at == T1
    assert record.valid_time == datetime(2026, 9, 30, 12, tzinfo=NOW.tzinfo)


def test_observed_at_and_valid_time_are_independent_axes() -> None:
    late = windowed_observation(
        "obs:late",
        METRIC,
        value=100.0,
        missingness=MissingnessState.OBSERVED,
        claim_refs=(CLAIM,),
        valid_time=T1,
    ).model_copy(update={"observed_at": T1 + REV})
    assert late.valid_time == T1
    assert late.observed_at == T1 + REV
    assert late.observed_at > late.valid_time


def test_the_provenance_adapter_never_introduces_a_book_6_time_now() -> None:
    from datetime import UTC

    engine, _, _ = _stack()
    _observe(engine, "obs:1", value=7.0)
    assert engine.registry.registered_measurement("obs:1").observed_at == T1
    assert T1.tzinfo is UTC


def test_an_unknown_claim_ref_is_refused_rather_than_defaulted() -> None:
    engine, _, _ = _stack()
    with pytest.raises(Book6ProvenanceError, match="unknown Book 2 claim"):
        engine.provenance.resolve_claim("fixture:claim:never-registered")
