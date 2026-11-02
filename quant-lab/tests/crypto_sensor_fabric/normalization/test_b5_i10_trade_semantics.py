"""SENSOR-B5-I10E1 - RED-first trade-normalizer + Binance side-map contract matrix.

Authority: ``BLOC_05_I10D1_DECISION_PACKAGE.md`` section 8.1 (frozen T10-01..T10-08)
and section 8.2 (operator-proposed adversarial cases OP-T10-A01..A14), read against
bloc_05/04 sections 2.1-2.3, bloc_05/06 sections 5-6 and 17-21, bloc_05/03
sections 2, 11-13, 17, 20, 22, and bloc_05/07 F14-F17, F24.

Two acceptance layers are kept structurally separate and are NEVER merged:

    LAYER_1 = BEHAVIORALLY_IMPLEMENTED          earnable at B5-I10
    LAYER_2 = PROVIDER_SEMANTICALLY_VERIFIED    NOT earnable at B5-I10 (I09-b deferred)

A green Layer 1 test is evidence of arithmetic and refusal discipline.  It is not
provider certification, and no test in this module upgrades
``SemanticConfidence`` out of ``AMBIGUOUS`` or writes the canonical
``aggressor_side`` of a T1 row.

OFFLINE.  No network, no wall clock, no filesystem writes.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from crypto_sensor_fabric.contracts.enums import (
    AggregationType,
    AggressorSide,
    SemanticEquivalence,
    SensorFamily,
)
from crypto_sensor_fabric.normalization.common.semantic_registry import (
    PENDING_EVIDENCE_REFERENCE,
    IntervalDataScope,
    ProviderSemanticMapping,
    ProviderSemanticRegistry,
    SemanticConfidence,
    admits_critical_t1_use,
)
from crypto_sensor_fabric.normalization.enums import (
    NormalizationQualityFlag,
    NormalizationStatus,
    TimestampPrecision,
)
from crypto_sensor_fabric.normalization.sensors.side_maps import (
    BINANCE_IS_BUYER_MAKER_METHODOLOGY_ID,
    SideEvidence,
    SideEvidenceKind,
    SideMappingStatus,
    UnsupportedSideMappingError,
    apply_side_map,
    binance_side_from_is_buyer_maker,
    require_side_mapping,
    resolve_side_mapping,
)
from crypto_sensor_fabric.normalization.sensors.trade import (
    I08_UNITS_METHODOLOGY_ID,
    I04B_METHODOLOGY_ID,
    TradeObservationInput,
    normalize_trade,
)
from crypto_sensor_fabric.normalization.terms.conversion import (
    METHODOLOGY_VERSION as I04B_MODULE_METHODOLOGY_VERSION,
    ReferencePriceEvidence,
    ReferencePriceType,
)
from crypto_sensor_fabric.normalization.common.conversion import (
    METHODOLOGY_VERSION as I08_MODULE_METHODOLOGY_VERSION,
)
from crypto_sensor_fabric.normalization.terms.snapshot import ContractTermsSnapshot
from crypto_sensor_fabric.normalization.enums import PayoffType
from crypto_sensor_fabric.registry.provider_registry import PROVIDER_IDS
from crypto_sensor_fabric.storage import CoverageState, RevisionState

_HERE = Path(__file__).resolve().parent
_QUANT_LAB = _HERE.parents[2]
_FIXTURES = _QUANT_LAB / "tests" / "crypto_sensor_fabric" / "fixtures"
_I10_FIXTURES = _FIXTURES / "i10"

BINANCE = "BINANCE_USDM"
EVENT_AT = datetime(2024, 3, 1, 12, 0, 0, tzinfo=timezone.utc)
OBSERVED_AT = datetime(2024, 3, 1, 12, 0, 1, tzinfo=timezone.utc)
INGESTED_AT = datetime(2024, 3, 5, 8, 0, 0, tzinfo=timezone.utc)
CUTOFF = datetime(2024, 3, 1, 12, 0, 5, tzinfo=timezone.utc)
BLOB_HASH = "c" * 64


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def _binance_row(**overrides: object) -> ProviderSemanticMapping:
    """The live Bloc 1 planning row projected into the frozen I09 shape.

    ``evidence_reference`` stays ``BLOC2_PROBE_PENDING``, so the I09 model itself
    forces ``semantic_confidence=AMBIGUOUS``; an override that tried to promote
    it would be refused at construction.
    """
    payload: dict[str, object] = {
        "provider": BINANCE,
        "provider_field": "isBuyerMaker",
        "canonical_sensor": SensorFamily.MECHANICAL_TRADE,
        "canonical_field": "aggressor_side",
        "semantic_equivalence_class": SemanticEquivalence.NORMALIZABLE_COMPARABLE,
        "native_definition": "Binance aggTrade isBuyerMaker boolean; true = buyer is maker.",
        "transformation": (
            "isBuyerMaker=true -> SELL; isBuyerMaker=false -> BUY (frozen SENSOR-B1-R01)"
        ),
        "methodology_id": BINANCE_IS_BUYER_MAKER_METHODOLOGY_ID,
        "blocking_assumptions": ("the boolean describes the maker side of the trade",),
        "known_limitations": ("unverified against a first-party provider capture",),
        "source_endpoint_or_archive": "binance-usdm:fapi/v1/aggTrades",
        "data_type": "BOOLEAN",
        "native_unit": "DIMENSIONLESS",
        "timestamp_meaning": "provider trade time, milliseconds since epoch",
        "interval_data_scope": IntervalDataScope.PROVIDER_NATIVE_UNKNOWN,
        "direction_side_convention": "maker-flag",
        "evidence_reference": PENDING_EVIDENCE_REFERENCE,
        "semantic_confidence": SemanticConfidence.AMBIGUOUS,
        "last_verified_date": None,
        "version": "1",
    }
    payload.update(overrides)
    return ProviderSemanticMapping.model_validate(payload)


def _registry(*rows: ProviderSemanticMapping) -> ProviderSemanticRegistry:
    return ProviderSemanticRegistry.model_validate(
        {"schema_version": "i10-contract-matrix", "mappings": list(rows)}
    )


def _payload(**overrides: object) -> TradeObservationInput:
    payload: dict[str, object] = {
        "provider": BINANCE,
        "venue": BINANCE,
        "native_instrument": "BTCUSDT",
        "contract_instance_id": "BINANCE_USDM:BTCUSDT:PERP:2024-01",
        "native_event_id": "400001",
        "native_sequence_id": "592-596",
        "price_native": Decimal("61234.50"),
        "quantity_native": Decimal("0.25000000"),
        "quantity_native_unit": "BTC",
        "side_evidence": SideEvidence.provider_boolean(
            "isBuyerMaker", True, provider=BINANCE
        ),
        "aggregation_type": AggregationType.INDIVIDUAL,
        "source_trade_count": None,
        "trade_flags": (),
        "event_at": EVENT_AT,
        "observed_at": OBSERVED_AT,
        "ingested_at": INGESTED_AT,
        "source_precision": TimestampPrecision.MILLISECOND,
        "source_revision_id": "rev-i10-1",
        "source_revision_state": RevisionState.STABLE,
        "source_coverage_state": CoverageState.COMPLETE_SOURCE_BOUNDARY,
        "normalization_generation": "gen-i10-1",
        "raw_projection_refs": ("proj:binance:aggtrades:1",),
        "acquisition_refs": ("acq:binance:rest:aggtrades:1",),
        "evidence_blob_hashes": (BLOB_HASH,),
        "code_version": "i10e1",
        "config_version": "cfg-bloc5-i10",
    }
    payload.update(overrides)
    return TradeObservationInput.model_validate(payload)


def _linear_terms(**overrides: object) -> ContractTermsSnapshot:
    payload: dict[str, object] = {
        "contract_instance_id": "BINANCE_USDM:BTCUSDT:PERP:2024-01",
        "economic_contract_id": "EC:BTCUSDT:PERP:LINEAR",
        "contract_terms_version": "terms-2024-01",
        "contract_multiplier": Decimal("0.001"),
        "multiplier_unit": "CONTRACTS",
        "price_unit": "USDT",
        "quantity_unit": "BTC",
        "payoff_type": PayoffType.LINEAR,
        "inverse_flag": False,
        "quanto_flag": False,
        "quote_asset_id": "USDT",
        "settlement_asset_id": "USDT",
        "margin_asset_id": None,
        "tick_size": Decimal("0.10"),
        "lot_size": Decimal("1"),
        "expiry": None,
        "source_evidence_refs": ("termsref:binance:2024-01",),
    }
    payload.update(overrides)
    return ContractTermsSnapshot.model_validate(payload)


def _reference_price(**overrides: object) -> ReferencePriceEvidence:
    payload: dict[str, object] = {
        "reference_price": Decimal("60000"),
        "reference_price_type": ReferencePriceType.TRADE_PRICE,
        "reference_price_time": datetime(2024, 3, 1, 11, 59, 59, tzinfo=timezone.utc),
        "reference_price_source": "binance-usdm:aggTrades",
        "market_available_at": datetime(2024, 3, 1, 11, 59, 59, tzinfo=timezone.utc),
        "reference_price_unit": "USDT",
        "reference_price_base_unit": "BTC",
        "source_evidence_refs": ("pxref:binance:aggTrades:2024-03-01T11:59:59Z",),
    }
    payload.update(overrides)
    return ReferencePriceEvidence.model_validate(payload)


def _fixture(name: str) -> dict:
    return json.loads((_I10_FIXTURES / name).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Group A -- behavioural mapping (T10-01, T10-02): LAYER 1 ONLY
# ---------------------------------------------------------------------------


def test_t10_01_is_buyer_maker_true_is_sell() -> None:
    """T10-01 / bloc_05/06 section 6 bullet 1 / bloc_05/04 section 2.2 / F17.

    LAYER_1 = BEHAVIORALLY_IMPLEMENTED: the pure transformation exists and is
    deterministic.  LAYER_2 = PROVIDER_SEMANTICALLY_VERIFIED: NOT EARNED.
    """
    mapping = _binance_row()
    provisional = apply_side_map(
        SideEvidence.provider_boolean("isBuyerMaker", True, provider=BINANCE), mapping
    )
    assert provisional is not None
    assert provisional.mapped_side is AggressorSide.SELL
    assert provisional.status is SideMappingStatus.BEHAVIORALLY_IMPLEMENTED
    assert provisional.canonical_admitted is False


def test_t10_02_is_buyer_maker_false_is_buy() -> None:
    """T10-02 / bloc_05/06 section 6 bullet 2 / bloc_05/04 section 2.2.

    Same two-layer separation as T10-01.
    """
    provisional = apply_side_map(
        SideEvidence.provider_boolean("isBuyerMaker", False, provider=BINANCE),
        _binance_row(),
    )
    assert provisional is not None
    assert provisional.mapped_side is AggressorSide.BUY
    assert provisional.status is SideMappingStatus.BEHAVIORALLY_IMPLEMENTED
    assert provisional.canonical_admitted is False


@pytest.mark.parametrize("case", _fixture("binance_aggtrades_side_cases.json")["cases"])
def test_frozen_side_case_fixture_matches_the_adapter(case: dict) -> None:
    """The operator-frozen fixture and the adapter agree on both booleans."""
    provisional = apply_side_map(
        SideEvidence.provider_boolean(
            "isBuyerMaker", case["is_buyer_maker"], provider=BINANCE
        ),
        _binance_row(),
    )
    assert provisional is not None
    assert provisional.mapped_side.value == case["expected_mapped_side"]
    assert case["layer_1_state"] == "BEHAVIORALLY_IMPLEMENTED"
    assert case["layer_2_state"].startswith("NOT_EARNED")


def test_layer_two_is_never_claimable_from_the_frozen_fixture() -> None:
    """§8.2 OP-T10-A12 sibling: a valid fixture is not permission to promote.

    The fixture's own provenance block must disclaim provider truth, and the
    mapping must still refuse a canonical claim.
    """
    fixture = _fixture("binance_aggtrades_side_cases.json")
    provenance = fixture["provenance"]
    assert provenance["source"] == "operator-frozen"
    assert "SYNTHETIC" in provenance["provenance_class"]
    assert any(
        "not a recorded Binance response" in item
        for item in provenance["not_authoritative_for"]
    )
    mapping = _binance_row()
    assert not admits_critical_t1_use(mapping.semantic_confidence)
    provisional = apply_side_map(
        SideEvidence.provider_boolean("isBuyerMaker", True, provider=BINANCE), mapping
    )
    assert provisional is not None
    assert provisional.status is not SideMappingStatus.PROVIDER_SEMANTICALLY_VERIFIED
    assert provisional.evidence_reference == PENDING_EVIDENCE_REFERENCE


# ---------------------------------------------------------------------------
# Group B -- provider semantic admission (R2)
# ---------------------------------------------------------------------------


def test_block2_probe_pending_stays_ambiguous() -> None:
    """R2: the pending token forces AMBIGUOUS in the I09 model itself."""
    row = _binance_row()
    assert row.evidence_reference == PENDING_EVIDENCE_REFERENCE
    assert row.semantic_confidence is SemanticConfidence.AMBIGUOUS

    with pytest.raises(Exception):
        _binance_row(semantic_confidence=SemanticConfidence.VERIFIED_FIRST_PARTY)


def test_canonical_side_stays_unknown_while_semantics_are_unverified() -> None:
    """§2.2 consequence + A10-10: provisional evidence never becomes canonical."""
    record = normalize_trade(_payload(), registry=_registry(_binance_row()))
    assert record.aggressor_side is AggressorSide.UNKNOWN
    assert record.provisional_side is not None
    assert record.provisional_side.mapped_side is AggressorSide.SELL
    assert record.provisional_side.canonical_admitted is False


def test_provisional_side_is_a_conspicuously_different_type_and_status() -> None:
    """The provisional slot must not be mistakable for the canonical field."""
    record = normalize_trade(_payload(), registry=_registry(_binance_row()))
    provisional = record.provisional_side
    assert provisional is not None
    assert type(provisional).__name__ == "ProvisionalSideMapping"
    assert provisional.status is SideMappingStatus.BEHAVIORALLY_IMPLEMENTED
    assert record.aggressor_side is not provisional.mapped_side
    assert record.normalization_status is NormalizationStatus.NATIVE_ONLY


def test_mapping_without_a_methodology_fails_closed() -> None:
    """A declared row that cannot be cited is refused, never cited with a URL."""
    row = _binance_row(
        semantic_equivalence_class=SemanticEquivalence.CORROBORATION_ONLY,
        methodology_id=None,
        evidence_reference="provider-docs:binance:placeholder",
        semantic_confidence=SemanticConfidence.COMMUNITY_DOCUMENTED,
    )
    assert row.methodology_id is None
    assert (
        apply_side_map(
            SideEvidence.provider_boolean("isBuyerMaker", True, provider=BINANCE), row
        )
        is None
    )


@pytest.mark.parametrize(
    "provider", [p for p in PROVIDER_IDS if p != BINANCE]
)
def test_unsupported_venue_never_inherits_binance_semantics(provider: str) -> None:
    """R4: Binance polarity is never extrapolated to another venue."""
    registry = _registry(_binance_row())
    assert resolve_side_mapping(registry, provider, "isBuyerMaker", SensorFamily.MECHANICAL_TRADE) is None
    with pytest.raises(UnsupportedSideMappingError):
        require_side_mapping(
            registry, provider, "isBuyerMaker", SensorFamily.MECHANICAL_TRADE
        )
    # Even handed the Binance row, evidence from another venue is refused.
    assert (
        apply_side_map(
            SideEvidence.provider_boolean("isBuyerMaker", True, provider=provider),
            _binance_row(),
        )
        is None
    )


def test_contradictory_provider_semantics_do_not_resolve_by_guessing() -> None:
    """A NOT_COMPARABLE row declares the fields incomparable; it is not applied."""
    row = _binance_row(
        semantic_equivalence_class=SemanticEquivalence.NOT_COMPARABLE,
        methodology_id=None,
        evidence_reference="provider-docs:binance:contradiction",
        semantic_confidence=SemanticConfidence.COMMUNITY_DOCUMENTED,
    )
    assert (
        apply_side_map(
            SideEvidence.provider_boolean("isBuyerMaker", True, provider=BINANCE), row
        )
        is None
    )


def test_evidence_field_that_disagrees_with_the_row_is_refused() -> None:
    """No cross-field fill: the evidence field must be the mapped field."""
    assert (
        apply_side_map(
            SideEvidence.provider_boolean("side", False, provider=BINANCE),
            _binance_row(),
        )
        is None
    )


def test_pin_consistency_across_probe_adapter_fixture_and_config() -> None:
    """OP-T10-A12: the probe pin, this adapter, the fixture and the config agree.

    Production code imports none of these; only this test compares them.
    """
    from crypto_sensor_fabric.providers.binance.probe import (
        aggressor_side_from_is_buyer_maker,
    )

    for value in (True, False):
        assert binance_side_from_is_buyer_maker(value) is aggressor_side_from_is_buyer_maker(value)

    fixture = _fixture("binance_aggtrades_side_cases.json")
    assert fixture["methodology_id"] == BINANCE_IS_BUYER_MAKER_METHODOLOGY_ID

    import yaml

    config = yaml.safe_load(
        (_QUANT_LAB / "config" / "crypto_sensor_fabric" / "semantic_equivalence.yaml").read_text(
            encoding="utf-8"
        )
    )
    rows = [
        row
        for row in config["mappings"]
        if row["provider"] == BINANCE and row["source_metric"] == "isBuyerMaker"
    ]
    assert len(rows) == 1
    row = rows[0]
    assert row["methodology_id"] == BINANCE_IS_BUYER_MAKER_METHODOLOGY_ID
    assert row["evidence_reference"] == PENDING_EVIDENCE_REFERENCE
    # The frozen direction, read out of the config TEXT (a citation, not a parse).
    assert "isBuyerMaker=true -> aggressor_side=SELL" in row["transformation_method"]
    assert "isBuyerMaker=false -> aggressor_side=BUY" in row["transformation_method"]
    # The adapter row's own transformation text must state the same direction.
    assert "isBuyerMaker=true -> SELL" in _binance_row().transformation
    assert "isBuyerMaker=false -> BUY" in _binance_row().transformation


def test_methodology_citation_constants_match_the_accepted_modules() -> None:
    """I10 cites accepted methodology identity verbatim; it mints nothing."""
    assert I04B_METHODOLOGY_ID == I04B_MODULE_METHODOLOGY_VERSION
    assert I08_UNITS_METHODOLOGY_ID == I08_MODULE_METHODOLOGY_VERSION


# ---------------------------------------------------------------------------
# Group C -- native trade truth, identity, lineage, economics
# ---------------------------------------------------------------------------


def test_t10_03_unknown_side_is_never_inferred() -> None:
    """T10-03 / bloc_05/06 section 6 bullet 3 / B1-T10 / F17."""
    for evidence in (
        SideEvidence.field_absent(provider=BINANCE),
        SideEvidence.semantics_undeclared("isBuyerMaker", provider=BINANCE),
    ):
        record = normalize_trade(
            _payload(side_evidence=evidence), registry=_registry(_binance_row())
        )
        assert record.aggressor_side is AggressorSide.UNKNOWN
        assert record.provisional_side is None
        assert NormalizationQualityFlag.SEMANTICS_UNVERIFIED in record.quality_flags


def test_t10_03b_rising_price_does_not_create_a_side() -> None:
    """OP-T10-A02: the mapping never reads price."""
    low = normalize_trade(
        _payload(
            price_native=Decimal("100"),
            side_evidence=SideEvidence.field_absent(provider=BINANCE),
        ),
        registry=_registry(_binance_row()),
    )
    high = normalize_trade(
        _payload(
            price_native=Decimal("999999"),
            side_evidence=SideEvidence.field_absent(provider=BINANCE),
        ),
        registry=_registry(_binance_row()),
    )
    assert low.aggressor_side is AggressorSide.UNKNOWN
    assert high.aggressor_side is AggressorSide.UNKNOWN
    assert low.provisional_side is None and high.provisional_side is None


def test_t10_04_provider_trade_id_preserved() -> None:
    """T10-04 / bloc_05/06 section 6 bullet 4 / bloc_05/04 section 2.3."""
    record = normalize_trade(_payload(), registry=_registry(_binance_row()))
    assert record.native_event_id == "400001"
    assert record.native_sequence_id == "592-596"


def test_t10_05_quantity_native_preserved_without_rounding() -> None:
    """T10-05 / bloc_05/03 section 1 and 3.1 / F12 / G3."""
    record = normalize_trade(_payload(), registry=_registry(_binance_row()))
    quantities = {value.native_field_name: value for value in record.native_values}
    assert quantities["qty"].native_value == Decimal("0.25000000")
    assert str(quantities["qty"].native_value) == "0.25000000"
    assert quantities["price"].native_value == Decimal("61234.50")
    assert str(quantities["price"].native_value) == "61234.50"


def test_t10_06_valid_pit_contract_to_base_and_quote() -> None:
    """T10-06 / bloc_05/06 section 6 bullet 6 / G5 / bloc_05/03 section 22 inv.7."""
    record = normalize_trade(
        _payload(
            quantity_native=Decimal("500"),
            quantity_native_unit="CONTRACTS",
            aggregation_type=AggregationType.INDIVIDUAL,
        ),
        registry=_registry(_binance_row()),
        terms=_linear_terms(),
        reference_price=_reference_price(),
        knowledge_cutoff=CUTOFF,
    )
    assert record.quantity_base is not None
    assert record.quantity_base.blocked is False
    assert record.quantity_base.value == Decimal("0.5")
    assert record.quantity_base.methodology_id == I04B_METHODOLOGY_ID
    assert record.quantity_base.conversion_lineage_refs

    assert record.notional_quote is not None
    assert record.notional_quote.blocked is False
    assert record.notional_quote.value == Decimal("30000")
    assert record.notional_quote.conversion_lineage_refs

    # The unresolved cross-family step stays blocked even when I04B succeeds.
    assert record.notional_usd is not None
    assert record.notional_usd.blocked is True
    assert record.notional_usd.value is None
    assert record.notional_usd.methodology_id == I08_UNITS_METHODOLOGY_ID


def test_t10_07a_lineage_input_is_complete_and_collapse_is_deferred() -> None:
    """T10-07 I10 half / bloc_05/04 section 2.3 / bloc_05/06 section 1 G7.

    Two acquisition observations of the same hard trade id stay two rows with
    full lineage.  The collapse assertion itself is I17's and is NOT made here.
    """
    rest = _payload(acquisition_refs=("acq:binance:rest:aggtrades:1",))
    archive = _payload(
        acquisition_refs=("acq:binance:archive:aggtrades:2024-03-01",),
        observed_at=datetime(2024, 3, 6, 0, 0, 0, tzinfo=timezone.utc),
        ingested_at=datetime(2024, 3, 6, 0, 5, 0, tzinfo=timezone.utc),
        raw_projection_refs=("proj:binance:archive:1",),
        evidence_blob_hashes=("d" * 64,),
    )
    first = normalize_trade(rest, registry=_registry(_binance_row()))
    second = normalize_trade(archive, registry=_registry(_binance_row()))

    assert first is not second
    assert first.native_event_id == second.native_event_id == "400001"
    assert first.lineage.acquisition_refs != second.lineage.acquisition_refs
    for record in (first, second):
        assert record.lineage.acquisition_refs
        assert record.lineage.raw_projection_refs
        assert record.lineage.evidence_blob_hashes
    # I10 must not assert a collapse it does not own.
    for record in (first, second):
        assert NormalizationQualityFlag.DUPLICATE_CONFIRMED not in record.quality_flags


def test_t10_08_cross_venue_rows_stay_distinct() -> None:
    """T10-08 / bloc_05/06 section 6 bullet 8 / F24: T1 stays venue-scoped."""
    a = normalize_trade(
        _payload(provider="KRAKEN_FUTURES", venue="KRAKEN_FUTURES"), registry=_registry()
    )
    b = normalize_trade(
        _payload(provider="OKX_SWAP", venue="OKX_SWAP"), registry=_registry()
    )
    assert a.venue != b.venue
    a_native = {value.native_field_name: value.native_value for value in a.native_values}
    b_native = {value.native_field_name: value.native_value for value in b.native_values}
    assert a_native == b_native
    assert a.time.source_event_at == b.time.source_event_at
    assert a.aggressor_side is AggressorSide.UNKNOWN
    assert b.aggressor_side is AggressorSide.UNKNOWN


# ---------------------------------------------------------------------------
# Group D -- operator-proposed adversarial matrix (OP-T10-A01..A14)
# ---------------------------------------------------------------------------


def test_op_a01_unknown_side_flags_semantics_unverified_without_inference() -> None:
    record = normalize_trade(
        _payload(side_evidence=SideEvidence.field_absent(provider=BINANCE)),
        registry=_registry(_binance_row()),
    )
    assert record.aggressor_side is AggressorSide.UNKNOWN
    assert NormalizationQualityFlag.SEMANTICS_UNVERIFIED in record.quality_flags


def test_op_a03_trailing_zero_quantity_is_byte_exact() -> None:
    record = normalize_trade(
        _payload(quantity_native=Decimal("1.23000000")), registry=_registry(_binance_row())
    )
    quantities = {value.native_field_name: value for value in record.native_values}
    assert str(quantities["qty"].native_value) == "1.23000000"


def test_op_a04_absent_provider_id_is_flagged_and_never_synthesized() -> None:
    record = normalize_trade(
        _payload(native_event_id=None), registry=_registry(_binance_row())
    )
    assert record.native_event_id is None
    assert NormalizationQualityFlag.IDENTITY_PROVIDER_ID_MISSING in record.quality_flags
    assert NormalizationQualityFlag.NO_SAFE_DEDUPE_KEY in record.quality_flags


def test_op_a05_identity_mismatch_is_refused() -> None:
    """F3: the payload's contract instance must be the terms' instance."""
    with pytest.raises(ValueError):
        normalize_trade(
            _payload(contract_instance_id="BINANCE_USDM:ETHUSDT:PERP:2024-01"),
            registry=_registry(_binance_row()),
            terms=_linear_terms(),
            reference_price=_reference_price(),
            knowledge_cutoff=CUTOFF,
        )


def test_op_a06_absent_pit_terms_block_the_derived_amount() -> None:
    """G5: I04B refuses without terms; native is retained."""
    record = normalize_trade(
        _payload(quantity_native=Decimal("500"), quantity_native_unit="CONTRACTS"),
        registry=_registry(_binance_row()),
        terms=None,
        reference_price=None,
        knowledge_cutoff=None,
    )
    assert record.quantity_base is not None
    assert record.quantity_base.blocked is True
    assert record.quantity_base.value is None
    assert NormalizationQualityFlag.UNIT_CONVERSION_BLOCKED in record.quality_flags
    quantities = {value.native_field_name: value for value in record.native_values}
    assert quantities["qty"].native_value == Decimal("500")


def test_op_a07_unsupported_denomination_is_blocked_not_guessed() -> None:
    record = normalize_trade(
        _payload(quantity_native_unit="ETH"),
        registry=_registry(_binance_row()),
        terms=_linear_terms(),
        reference_price=_reference_price(),
        knowledge_cutoff=CUTOFF,
    )
    assert record.quantity_base is not None
    assert record.quantity_base.blocked is True
    assert record.quantity_base.value is None


def test_op_a08_unknown_mapping_is_refused_without_substitution() -> None:
    record = normalize_trade(_payload(), registry=_registry())
    assert record.provisional_side is None
    assert record.aggressor_side is AggressorSide.UNKNOWN


def test_op_a09_provisional_evidence_never_leaves_native_only() -> None:
    record = normalize_trade(_payload(), registry=_registry(_binance_row()))
    assert record.normalization_status is NormalizationStatus.NATIVE_ONLY
    assert NormalizationQualityFlag.SEMANTICS_UNVERIFIED in record.quality_flags


def test_op_a10_cross_venue_identity_is_never_merged() -> None:
    kraken = normalize_trade(
        _payload(provider="KRAKEN_FUTURES", venue="KRAKEN_FUTURES"), registry=_registry()
    )
    binance = normalize_trade(_payload(), registry=_registry(_binance_row()))
    assert kraken.venue != binance.venue
    assert kraken.lineage.acquisition_refs
    assert binance.lineage.acquisition_refs


def test_op_a11_duplicate_candidate_is_never_asserted_as_confirmed() -> None:
    record = normalize_trade(_payload(), registry=_registry(_binance_row()))
    assert NormalizationQualityFlag.DUPLICATE_CONFIRMED not in record.quality_flags


def test_op_a13_version_identity_is_cited_not_rewritten() -> None:
    """F14: the reference carries the declared version; I10 never edits it."""
    v1 = apply_side_map(
        SideEvidence.provider_boolean("isBuyerMaker", True, provider=BINANCE),
        _binance_row(version="1"),
    )
    v2 = apply_side_map(
        SideEvidence.provider_boolean("isBuyerMaker", True, provider=BINANCE),
        _binance_row(version="2"),
    )
    assert v1 is not None and v2 is not None
    assert v1.methodology_ref.version == "1"
    assert v2.methodology_ref.version == "2"
    assert v1.methodology_ref.methodology_id == v2.methodology_ref.methodology_id


def test_op_a14_i10_records_revision_state_and_never_a_replay_verdict() -> None:
    """I06 owns replay eligibility; I10 publishes none."""
    record = normalize_trade(_payload(), registry=_registry(_binance_row()))
    assert record.source_revision_state is RevisionState.STABLE
    assert record.source_revision_id == "rev-i10-1"
    payload = record.as_canonical_dict()
    assert "replay_eligibility" not in payload


# ---------------------------------------------------------------------------
# Group E -- record laws and fixture provenance
# ---------------------------------------------------------------------------


def test_record_is_deterministic_across_constructions() -> None:
    first = normalize_trade(_payload(), registry=_registry(_binance_row()))
    second = normalize_trade(_payload(), registry=_registry(_binance_row()))
    assert first.canonical_json() == second.canonical_json()


def test_record_never_claims_a_canonical_status_at_i10() -> None:
    record = normalize_trade(_payload(), registry=_registry(_binance_row()))
    assert record.normalization_status is NormalizationStatus.NATIVE_ONLY
    assert record.normalization_status not in (
        NormalizationStatus.NORMALIZED,
        NormalizationStatus.PARTIALLY_NORMALIZED,
    )


def test_blocked_usd_amount_is_never_economic_zero() -> None:
    record = normalize_trade(_payload(), registry=_registry(_binance_row()))
    assert record.notional_usd is not None
    assert record.notional_usd.value is None
    assert record.notional_usd.blocked is True
    assert record.notional_usd.unresolved_citation == I08_UNITS_METHODOLOGY_ID


def test_both_refusal_fixture_cases_are_honoured() -> None:
    fixture = _fixture("trade_side_refusals.json")
    assert fixture["provider_neutral"] is True
    for case in fixture["cases"]:
        if case["side_evidence_kind"] == "SIDE_FIELD_ABSENT":
            evidence = SideEvidence.field_absent(provider=BINANCE)
            row = _binance_row()
        elif case["side_evidence_kind"] == "SIDE_SEMANTICS_UNDECLARED":
            evidence = SideEvidence.semantics_undeclared("isBuyerMaker", provider=BINANCE)
            row = _binance_row()
        else:
            evidence = SideEvidence.provider_boolean(
                case["provider_field"], True, provider=BINANCE
            )
            row = (
                _binance_row(
                    semantic_equivalence_class=SemanticEquivalence.CORROBORATION_ONLY,
                    methodology_id=None,
                    evidence_reference="provider-docs:binance:placeholder",
                    semantic_confidence=SemanticConfidence.COMMUNITY_DOCUMENTED,
                )
                if case.get("mapping_row_present")
                else None
            )
        provisional = None if row is None else apply_side_map(evidence, row)
        expected = case["expected_mapped_side"]
        assert (provisional.mapped_side.value if provisional else "UNKNOWN") == expected


def test_side_evidence_adt_refuses_contradictory_field_payloads() -> None:
    with pytest.raises(Exception):
        SideEvidence.model_validate(
            {"kind": SideEvidenceKind.SIDE_FIELD_ABSENT, "boolean_value": True}
        )
    with pytest.raises(Exception):
        SideEvidence.model_validate(
            {
                "kind": SideEvidenceKind.PROVIDER_BOOLEAN_FIELD,
                "provider_field": "isBuyerMaker",
            }
        )
