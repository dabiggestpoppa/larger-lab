"""SENSOR-B5-I14 - book snapshot / book metric semantics (frozen clauses + adversarial).

Each test maps to a frozen clause of bloc_05/04 sections 6 and 7.  Assertions are
on observable record fields only.  Offline, deterministic, provider-import free.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from crypto_sensor_fabric.contracts.enums import SemanticEquivalence, SensorFamily
from crypto_sensor_fabric.normalization.models import canonical_json_bytes
from crypto_sensor_fabric.normalization.sensors import (
    BookLevelInput,
    BookMetricObservationInput,
    BookMetricSource,
    BookQuantityUnit,
    BookSequenceStatus,
    BookSide,
    BookSnapshotObservationInput,
    BookUpdateSemantics,
    classify_sequence,
    normalize_book_metric,
    normalize_book_snapshot,
)
from crypto_sensor_fabric.storage.enums import CoverageState, RevisionState

_DIGEST = "c" * 64
_SNAPSHOT_FAMILY = SensorFamily.MECHANICAL_BOOK_SNAPSHOT
_METRIC_FAMILY = SensorFamily.MECHANICAL_BOOK_METRIC


def _level(
    side: BookSide,
    price: str,
    quantity: str,
    *,
    token: str = "CONTRACTS",
    reading: BookQuantityUnit = BookQuantityUnit.CONTRACTS,
) -> BookLevelInput:
    return BookLevelInput(
        side=side,
        price_native=Decimal(price),
        quantity_native=Decimal(quantity),
        native_unit_token=token,
        unit_reading=reading,
    )


def _book(wave1, **overrides: object) -> BookSnapshotObservationInput:
    base: dict[str, object] = dict(
        provider="DERIBIT",
        venue="DERIBIT",
        native_instrument="BTC-PERPETUAL",
        contract_instance_id="CANON:BTCUSDT:PERP:LINEAR:1",
        snapshot_id="BOOK-1",
        sequence="100",
        previous_sequence="99",
        update_semantics=BookUpdateSemantics.FULL_SNAPSHOT,
        bids=(
            _level(BookSide.BID, "61230.0", "4200"),
            _level(BookSide.BID, "61220.0", "9100"),
        ),
        asks=(
            _level(BookSide.ASK, "61231.5", "3800"),
            _level(BookSide.ASK, "61240.0", "7600"),
        ),
        provider_level_count=2,
        source_depth_definition="L2_TOP_50_LEVELS",
        native_unit_field="contracts",
        is_full_depth=False,
        source_revision_id="rev-1",
        source_revision_state=RevisionState.STABLE,
        source_coverage_state=CoverageState.COMPLETE_SOURCE_BOUNDARY,
        normalization_generation="gen-1",
        raw_projection_refs=("proj-1",),
        acquisition_refs=("acq-1",),
        evidence_blob_hashes=(_DIGEST,),
        code_version="code-1",
        config_version="cfg-1",
        event_at=wave1.AT,
    )
    base.update(overrides)
    return BookSnapshotObservationInput(**base)  # type: ignore[arg-type]


def _metric(wave1, **overrides: object) -> BookMetricObservationInput:
    base: dict[str, object] = dict(
        provider="DERIBIT",
        venue="DERIBIT",
        native_instrument="BTC-PERPETUAL",
        native_metric_id="BM-1",
        metric_name="SPREAD_BPS",
        metric_value_native=Decimal("0.245"),
        metric_unit="BPS",
        semantic_equivalence=SemanticEquivalence.CORROBORATION_ONLY,
        provider_methodology_ref=None,
        metric_source=BookMetricSource.PROVIDER_NATIVE,
        source_revision_id="rev-1",
        source_revision_state=RevisionState.STABLE,
        source_coverage_state=CoverageState.COMPLETE_SOURCE_BOUNDARY,
        normalization_generation="gen-1",
        raw_projection_refs=("proj-1",),
        acquisition_refs=("acq-1",),
        evidence_blob_hashes=(_DIGEST,),
        code_version="code-1",
        config_version="cfg-1",
        event_at=wave1.AT,
    )
    base.update(overrides)
    return BookMetricObservationInput(**base)  # type: ignore[arg-type]


def _admitted(wave1):
    registry = wave1.registry(
        (
            wave1.row(
                "contracts",
                "quantity_native_unit",
                family=_SNAPSHOT_FAMILY,
                provider="DERIBIT",
            ),
        )
    )
    return wave1.authority(registry)


# ---------------------------------------------------------------------------
# 04 6.2 -- sequence guardrails
# ---------------------------------------------------------------------------


def test_contiguous_full_snapshot_is_certified(wave1) -> None:
    record = normalize_book_snapshot(_book(wave1))
    assert record.sequence_status is BookSequenceStatus.CONTIGUOUS
    assert record.is_full_snapshot is True
    assert record.book_state_certified is True
    assert record.best_bid == Decimal("61230.0")
    assert record.best_ask == Decimal("61231.5")


def test_a_sequence_gap_uncertifies_the_book(wave1) -> None:
    record = normalize_book_snapshot(_book(wave1, sequence="105"))
    assert record.sequence_status is BookSequenceStatus.GAP_DETECTED
    assert record.book_state_certified is False


def test_an_unprovable_sequence_uncertifies_the_book(wave1) -> None:
    record = normalize_book_snapshot(_book(wave1, previous_sequence=None))
    assert record.sequence_status is BookSequenceStatus.UNKNOWN_SEQUENCE
    assert record.book_state_certified is False


def test_a_delta_update_is_never_a_book(wave1) -> None:
    record = normalize_book_snapshot(
        _book(wave1, update_semantics=BookUpdateSemantics.DELTA_UPDATE)
    )
    assert record.is_full_snapshot is False
    assert record.book_state_certified is False


def test_a_non_increasing_sequence_is_refused() -> None:
    with pytest.raises(ValueError, match="did not advance"):
        classify_sequence("99", "99")
    with pytest.raises(ValueError, match="did not advance"):
        classify_sequence("98", "99")


def test_non_numeric_sequences_stay_unknown() -> None:
    assert (
        classify_sequence("abc", "abd") is BookSequenceStatus.UNKNOWN_SEQUENCE
    )


# ---------------------------------------------------------------------------
# 04 6.1 -- level semantics
# ---------------------------------------------------------------------------


def test_a_crossed_book_is_refused() -> None:
    with pytest.raises(ValueError, match="crossed book"):
        _book(
            type("W", (), {"AT": None})(),
            bids=(_level(BookSide.BID, "100", "1"),),
            asks=(_level(BookSide.ASK, "99", "1"),),
        )


def test_unordered_levels_are_refused(wave1) -> None:
    with pytest.raises(ValueError, match="strictly descending"):
        _book(
            wave1,
            bids=(
                _level(BookSide.BID, "61220.0", "1"),
                _level(BookSide.BID, "61230.0", "1"),
            ),
        )


def test_mixed_units_in_one_book_are_refused(wave1) -> None:
    with pytest.raises(ValueError, match="one quantity unit reading"):
        _book(
            wave1,
            asks=(
                _level(BookSide.ASK, "61231.5", "3.8", token="BTC", reading=BookQuantityUnit.BASE_ASSET),
            ),
        )


def test_levels_preserve_native_price_and_quantity(wave1) -> None:
    record = normalize_book_snapshot(_book(wave1))
    assert record.bids[0].price_native == Decimal("61230.0")
    assert record.bids[0].quantity_native == Decimal("4200")
    assert record.bids[0].quantity_native_unit == "CONTRACTS"
    assert record.snapshot_depth_levels == 2
    assert record.source_depth_definition == "L2_TOP_50_LEVELS"


def test_contract_levels_convert_only_with_terms_and_admission(wave1) -> None:
    record = normalize_book_snapshot(
        _book(wave1),
        registry=_admitted(wave1),
        terms=wave1.terms(multiplier="0.001"),
        reference_price=wave1.price(value="61230"),
        knowledge_cutoff=wave1.CUTOFF,
    )
    assert record.bids[0].quantity_base is not None
    assert record.bids[0].quantity_base.blocked is False
    assert record.bids[0].quantity_base.value == Decimal("4.200")
    assert record.bids[0].quote_notional is not None
    assert record.bids[0].quote_notional.blocked is False


def test_without_admission_levels_stay_native_only(wave1) -> None:
    record = normalize_book_snapshot(_book(wave1), terms=wave1.terms())
    assert record.level_unit_admission is not None
    assert record.level_unit_admission.admitted is False
    assert record.bids[0].quantity_base.blocked is True
    assert record.bids[0].quantity_native == Decimal("4200")


def test_book_snapshot_is_byte_deterministic(wave1) -> None:
    assert canonical_json_bytes(normalize_book_snapshot(_book(wave1))) == (
        canonical_json_bytes(normalize_book_snapshot(_book(wave1)))
    )


# ---------------------------------------------------------------------------
# 04 7 -- book metrics
# ---------------------------------------------------------------------------


def test_an_undocumented_provider_score_is_corroboration_only(wave1) -> None:
    record = normalize_book_metric(_metric(wave1))
    assert record.semantic_equivalence is SemanticEquivalence.CORROBORATION_ONLY
    assert record.canonical_metric_family is None
    assert record.metric_value_native == Decimal("0.245")


def test_an_equivalence_claim_needs_a_methodology(wave1) -> None:
    with pytest.raises(ValueError, match="documented provider_methodology_ref"):
        _metric(wave1, semantic_equivalence=SemanticEquivalence.EXACT_EQUIVALENT)


def test_reconstruction_requires_a_certified_source_book(wave1) -> None:
    with pytest.raises(ValueError, match="source_book_state_certified"):
        _metric(
            wave1,
            metric_source=BookMetricSource.RECONSTRUCTED_INTERNAL,
            provider_methodology_ref="DEPTH_BPS_RECONSTRUCTION_V1",
        )


def test_a_reconstruction_over_an_uncertified_book_is_refused(wave1) -> None:
    with pytest.raises(ValueError, match="uncertified book state"):
        normalize_book_metric(
            _metric(
                wave1,
                metric_source=BookMetricSource.RECONSTRUCTED_INTERNAL,
                provider_methodology_ref="DEPTH_BPS_RECONSTRUCTION_V1",
                source_book_state_certified=False,
            )
        )


def test_a_reconstruction_over_a_certified_book_is_accepted(wave1) -> None:
    record = normalize_book_metric(
        _metric(
            wave1,
            metric_name="DEPTH_BID_5BPS",
            metric_value_native=Decimal("2400000.0"),
            metric_unit="USD",
            side=BookSide.BID,
            distance_bps=Decimal("5.0"),
            semantic_equivalence=SemanticEquivalence.NORMALIZABLE_COMPARABLE,
            provider_methodology_ref="DEPTH_BPS_RECONSTRUCTION_V1",
            metric_source=BookMetricSource.RECONSTRUCTED_INTERNAL,
            source_book_state_certified=True,
        )
    )
    assert record.metric_source is BookMetricSource.RECONSTRUCTED_INTERNAL
    assert record.source_book_state_certified is True
    assert record.distance_bps == Decimal("5.0")


def test_a_depth_distance_needs_a_side(wave1) -> None:
    with pytest.raises(ValueError, match="distance_bps requires side"):
        _metric(wave1, distance_bps=Decimal("5"))


def test_book_metric_native_value_is_never_a_fabric_metric(wave1) -> None:
    record = normalize_book_metric(_metric(wave1))
    # Only the provider's own number is stored; no canonical liquidity value.
    assert not hasattr(record, "liquidity_state")
    assert not hasattr(record, "spread_bps_canonical")
