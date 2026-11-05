"""SENSOR-B5-I11F1 - semantic-admission security repair (A11-14).

Twenty independent probes (SEC-01..SEC-20) over the repaired authority
boundary.  Before the repair one caller-supplied boolean
(``provider_semantics_verified``) promoted the position, execution and
aggressor sides into their canonical slots with no registry row, no confidence
and no evidence reference -- F_I11R1_02.  These probes assert that the bypass has
no representation left and that admission is a property of the I09
``ProviderSemanticRegistry``, resolved one row per canonical field.

**Every registry built here is SYNTHETIC TEST AUTHORITY.**  It exercises the
admission MECHANISM and certifies no provider: the fixture text says so in every
row, and no production registry row may be derived from it (directive section 5).

The aggregation law these probes assume is the module's: because the frozen flag
vocabulary carries ONE semantic flag, a partly certified row is not representable
honestly, so either every supplied claim is admitted or none is promoted.  That
is why several probes assert an *admitted* decision that still does not reach the
canonical slot -- the authority existed and the row, correctly, still failed
closed rather than presenting a hybrid.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from crypto_sensor_fabric.contracts.enums import (
    AggressorSide,
    LiquidationRole,
    SemanticEquivalence,
    SensorFamily,
)
from crypto_sensor_fabric.normalization.common.semantic_registry import (
    PENDING_EVIDENCE_REFERENCE,
    IntervalDataScope,
    ProviderSemanticMapping,
    ProviderSemanticRegistry,
    SemanticConfidence,
    is_first_party_grade,
)
from crypto_sensor_fabric.normalization.enums import (
    NormalizationQualityFlag,
    NormalizationStatus,
    PayoffType,
    QuarantineReason,
)
from crypto_sensor_fabric.normalization.sensors import (
    LiquidationAdmissionRefusal,
    LiquidationAggregationScope,
    LiquidationCanonicalField,
    LiquidationObservationInput,
    LiquidationPositionSide,
    LiquidationSideAdmission,
    LiquidationZeroIntervalState,
    T1LiquidationRecord,
    admit_aggressor_side,
    apply_side_map,
    normalize_liquidation,
    resolve_side_mapping,
    SideEvidence,
)
from crypto_sensor_fabric.normalization.terms.conversion import (
    ReferencePriceEvidence,
    ReferencePriceType,
)
from crypto_sensor_fabric.normalization.terms.snapshot import ContractTermsSnapshot
from crypto_sensor_fabric.storage.enums import CoverageState, RevisionState

_DIGEST = "f" * 64
_AT = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
_CUTOFF = datetime(2026, 3, 1, 13, 0, tzinfo=timezone.utc)

#: Every row this module builds carries this label, twice, so a fixture can never
#: be mistaken for documentary evidence about a venue.
_SYNTH = "SYNTHETIC_TEST_AUTHORITY_NOT_PROVIDER_DOCUMENTATION"
_SYNTH_METHOD = "SYNTHETIC_TEST_LIQUIDATION_SIDE_V1"
_SYNTH_REGISTRY_VERSION = "SYNTHETIC_TEST_REGISTRY_V1"


# ---------------------------------------------------------------------------
# Synthetic test authority (the fixture, not a production registry)
# ---------------------------------------------------------------------------


def _mapping(
    provider_field: str,
    canonical_field: str,
    *,
    provider: str = "BINANCE_USDM",
    confidence: SemanticConfidence = SemanticConfidence.VERIFIED_FIRST_PARTY,
    evidence: str | None = f"{_SYNTH}:evidence",
    methodology: str | None = _SYNTH_METHOD,
    family: SensorFamily = SensorFamily.MECHANICAL_LIQUIDATION,
    equivalence: SemanticEquivalence = SemanticEquivalence.EXACT_EQUIVALENT,
    version: str = "1",
) -> ProviderSemanticMapping:
    return ProviderSemanticMapping(
        provider=provider,
        provider_field=provider_field,
        canonical_sensor=family,
        canonical_field=canonical_field,
        semantic_equivalence_class=equivalence,
        native_definition=f"{_SYNTH}:{provider_field}",
        transformation=f"{_SYNTH}:{provider_field}->{canonical_field}",
        methodology_id=methodology,
        blocking_assumptions=(f"{_SYNTH}:certifies-nothing-in-production",),
        known_limitations=(f"{_SYNTH}:fixture-only-authority",),
        source_endpoint_or_archive="synthetic://test-authority",
        data_type="EVENT",
        native_unit="ENUM",
        timestamp_meaning="EVENT_TIME",
        interval_data_scope=IntervalDataScope.INTERVAL_LOCAL,
        direction_side_convention=f"{_SYNTH}:{canonical_field}",
        evidence_reference=evidence,
        semantic_confidence=confidence,
        last_verified_date=None,
        version=version,
    )


def _registry(*rows: ProviderSemanticMapping) -> ProviderSemanticRegistry:
    return ProviderSemanticRegistry(
        schema_version=_SYNTH_REGISTRY_VERSION, mappings=rows
    )


def _row_for(canonical_field: str) -> ProviderSemanticMapping:
    """The synthetic row for one canonical field, keyed by its fixture field."""
    return _mapping(_FIELD_TOKEN[canonical_field], canonical_field)


_FIELD_TOKEN = {
    "position_side_liquidated": "side",
    "execution_side": "orderSide",
    "aggressor_side": "aggressor",
    "maker_taker_role": "role",
}


def _full_registry() -> ProviderSemanticRegistry:
    return _registry(*(_row_for(field) for field in _FIELD_TOKEN))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _payload(**overrides: object) -> LiquidationObservationInput:
    base: dict[str, object] = dict(
        provider="BINANCE_USDM",
        venue="BINANCE",
        native_instrument="BTCUSD_PERP",
        liquidation_event_id="liq-1",
        position_side_liquidated=LiquidationPositionSide.LONG,
        execution_side=AggressorSide.SELL,
        native_position_side_field="side",
        native_position_side_value="LONG",
        native_execution_side_field="orderSide",
        native_execution_side_value="SELL",
        quantity_native=Decimal("250"),
        quantity_native_unit="CONTRACTS",
        aggregation_scope=LiquidationAggregationScope.EVENT_LEVEL,
        source_revision_id="rev-1",
        source_revision_state=RevisionState.STABLE,
        source_coverage_state=CoverageState.COMPLETE_SOURCE_BOUNDARY,
        normalization_generation="gen-1",
        raw_projection_refs=("proj-1",),
        acquisition_refs=("acq-1",),
        evidence_blob_hashes=(_DIGEST,),
        code_version="code-1",
        config_version="cfg-1",
    )
    base.update(overrides)
    return LiquidationObservationInput(**base)  # type: ignore[arg-type]


def _flags(record: T1LiquidationRecord) -> set[str]:
    return {flag.value for flag in record.quality_flags}


def _admission(
    record: T1LiquidationRecord, field: LiquidationCanonicalField
) -> LiquidationSideAdmission:
    matches = [
        admission
        for admission in record.side_admissions
        if admission.canonical_field is field
    ]
    assert len(matches) == 1, f"expected one admission for {field.value}, got {matches}"
    return matches[0]


def _terms(**overrides: object) -> ContractTermsSnapshot:
    base: dict[str, object] = dict(
        contract_instance_id="ci-1",
        economic_contract_id="econ-1",
        contract_terms_version="terms-v1",
        contract_multiplier=Decimal("0.01"),
        multiplier_unit="CONTRACTS",
        price_unit="USDT",
        quantity_unit="BTC",
        payoff_type=PayoffType.LINEAR,
        inverse_flag=False,
        quanto_flag=False,
        quote_asset_id="USDT",
        settlement_asset_id="USDT",
        tick_size=Decimal("0.5"),
        lot_size=Decimal("1"),
        source_evidence_refs=("terms-ref-1",),
    )
    if "payoff" in overrides:
        overrides["payoff_type"] = overrides.pop("payoff")
    if "inverse" in overrides:
        overrides["inverse_flag"] = overrides.pop("inverse")
    if "multiplier" in overrides:
        overrides["contract_multiplier"] = Decimal(str(overrides.pop("multiplier")))
    base.update(overrides)
    return ContractTermsSnapshot(**base)  # type: ignore[arg-type]


def _price(
    value: str = "60000", *, price_unit: str = "USDT", base_unit: str = "BTC"
) -> ReferencePriceEvidence:
    return ReferencePriceEvidence(
        reference_price=Decimal(value),
        reference_price_type=ReferencePriceType.PROVIDER_INDEX,
        reference_price_time=_AT,
        reference_price_source="BINANCE_INDEX",
        market_available_at=_AT,
        reference_price_unit=price_unit,
        reference_price_base_unit=base_unit,
        source_evidence_refs=("px-ref-1",),
    )


# ---------------------------------------------------------------------------
# SEC-01 -- the caller boolean has no replacement
# ---------------------------------------------------------------------------


def test_sec_01_a_caller_boolean_cannot_promote_a_canonical_side() -> None:
    """The old bypass is unrepresentable at BOTH layers.

    The observation model refuses the field outright, and a hand-built record
    that claims a side without an admitted decision fails validation -- so
    F_I11R1_02 cannot be reconstructed by a caller who has the constructor.
    """
    with pytest.raises(ValueError):
        _payload(provider_semantics_verified=True)

    record = normalize_liquidation(_payload())
    assert record.position_side_liquidated is LiquidationPositionSide.UNKNOWN
    assert record.execution_side is AggressorSide.UNKNOWN

    forged = normalize_liquidation(_payload(), registry=_full_registry()).model_dump()
    forged["side_admissions"] = ()
    with pytest.raises(ValueError, match="no admitted registry mapping"):
        T1LiquidationRecord.model_validate(forged)


# ---------------------------------------------------------------------------
# SEC-02..SEC-06 -- each refusal names the first missing link
# ---------------------------------------------------------------------------


def test_sec_02_an_unknown_provider_field_stays_provisional() -> None:
    record = normalize_liquidation(
        _payload(native_position_side_field=None, native_position_side_value=None),
        registry=_full_registry(),
    )
    admission = _admission(
        record, LiquidationCanonicalField.POSITION_SIDE_LIQUIDATED
    )
    assert admission.admitted is False
    assert admission.refusal is LiquidationAdmissionRefusal.NO_NATIVE_FIELD
    assert record.position_side_liquidated is LiquidationPositionSide.UNKNOWN


def test_sec_03_a_missing_registry_mapping_stays_provisional() -> None:
    partial = _registry(_row_for("execution_side"))
    record = normalize_liquidation(_payload(), registry=partial)
    admission = _admission(
        record, LiquidationCanonicalField.POSITION_SIDE_LIQUIDATED
    )
    assert admission.refusal is LiquidationAdmissionRefusal.NO_REGISTRY_MAPPING
    assert record.position_side_liquidated is LiquidationPositionSide.UNKNOWN


def test_sec_04_an_ambiguous_mapping_cannot_promote() -> None:
    """03 section 13: ``AMBIGUOUS`` blocks use in critical T1 fields.

    The row cites real (non-pending) evidence and is still refused: the ladder,
    not the presence of a citation, is what admits.
    """
    ambiguous = _registry(
        _mapping(
            "side",
            "position_side_liquidated",
            confidence=SemanticConfidence.AMBIGUOUS,
        )
    )
    record = normalize_liquidation(_payload(), registry=ambiguous)
    admission = _admission(
        record, LiquidationCanonicalField.POSITION_SIDE_LIQUIDATED
    )
    assert admission.refusal is LiquidationAdmissionRefusal.AMBIGUOUS_MAPPING
    assert record.position_side_liquidated is LiquidationPositionSide.UNKNOWN


def test_sec_05_the_pending_probe_token_cannot_promote() -> None:
    pending = _registry(
        _mapping(
            "side",
            "position_side_liquidated",
            confidence=SemanticConfidence.AMBIGUOUS,
            evidence=PENDING_EVIDENCE_REFERENCE,
        )
    )
    record = normalize_liquidation(_payload(), registry=pending)
    admission = _admission(
        record, LiquidationCanonicalField.POSITION_SIDE_LIQUIDATED
    )
    assert admission.refusal is LiquidationAdmissionRefusal.PENDING_EVIDENCE
    assert record.position_side_liquidated is LiquidationPositionSide.UNKNOWN


def test_sec_06_an_absent_evidence_reference_cannot_promote() -> None:
    """Absent evidence is refused twice over.

    The I09 model itself will not build a VERIFIED_* row without a citation, so
    the shortcut is unrepresentable at the registry; and the one row that CAN
    omit the citation (still ``AMBIGUOUS``) is refused by the normalizer.
    """
    with pytest.raises(ValueError):
        _mapping("side", "position_side_liquidated", evidence=None)

    uncited = _registry(
        _mapping(
            "side",
            "position_side_liquidated",
            evidence=None,
            confidence=SemanticConfidence.AMBIGUOUS,
            equivalence=SemanticEquivalence.CORROBORATION_ONLY,
        ),
        _row_for("execution_side"),
    )
    record = normalize_liquidation(_payload(), registry=uncited)
    admission = _admission(
        record, LiquidationCanonicalField.POSITION_SIDE_LIQUIDATED
    )
    assert admission.refusal is LiquidationAdmissionRefusal.PENDING_EVIDENCE
    assert record.position_side_liquidated is LiquidationPositionSide.UNKNOWN


# ---------------------------------------------------------------------------
# SEC-07..SEC-09 -- the ladder is respected but never relabelled
# ---------------------------------------------------------------------------


def test_sec_07_community_documented_is_admitted_but_never_first_party() -> None:
    """The frozen ladder admits it; the record must not claim more.

    ``admits_critical_t1_use`` is the whole authority here, and the confidence
    travels verbatim so a reader cannot mistake community corroboration for
    first-party verification.
    """
    community = _registry(
        _mapping(
            "side",
            "position_side_liquidated",
            confidence=SemanticConfidence.COMMUNITY_DOCUMENTED,
        ),
        _row_for("execution_side"),
    )
    record = normalize_liquidation(_payload(), registry=community)
    admission = _admission(
        record, LiquidationCanonicalField.POSITION_SIDE_LIQUIDATED
    )
    assert admission.admitted is True
    assert admission.semantic_confidence is SemanticConfidence.COMMUNITY_DOCUMENTED
    assert is_first_party_grade(admission.semantic_confidence) is False
    assert record.position_side_liquidated is LiquidationPositionSide.LONG


def test_sec_08_another_venue_cannot_lend_its_mapping() -> None:
    record = normalize_liquidation(
        _payload(
            provider="OKX_SWAP",
            venue="OKX",
            native_position_side_field="side",
            native_execution_side_field="orderSide",
        ),
        registry=_full_registry(),
    )
    admission = _admission(
        record, LiquidationCanonicalField.POSITION_SIDE_LIQUIDATED
    )
    assert admission.refusal is LiquidationAdmissionRefusal.NO_REGISTRY_MAPPING
    assert record.position_side_liquidated is LiquidationPositionSide.UNKNOWN


def test_sec_09_another_sensor_family_cannot_authorize_liquidation() -> None:
    trade_family = _registry(
        _mapping(
            "side",
            "position_side_liquidated",
            family=SensorFamily.MECHANICAL_TRADE,
        ),
        _mapping(
            "orderSide",
            "execution_side",
            family=SensorFamily.MECHANICAL_TRADE,
        ),
    )
    record = normalize_liquidation(_payload(), registry=trade_family)
    admission = _admission(
        record, LiquidationCanonicalField.POSITION_SIDE_LIQUIDATED
    )
    assert admission.refusal is LiquidationAdmissionRefusal.NO_REGISTRY_MAPPING
    assert record.position_side_liquidated is LiquidationPositionSide.UNKNOWN


# ---------------------------------------------------------------------------
# SEC-10..SEC-11 -- one claim per row, never a shared authority
# ---------------------------------------------------------------------------


def test_sec_10_execution_side_authority_does_not_imply_position_side() -> None:
    only_execution = _registry(_row_for("execution_side"))
    record = normalize_liquidation(_payload(), registry=only_execution)
    assert (
        _admission(record, LiquidationCanonicalField.EXECUTION_SIDE).admitted is True
    )
    position = _admission(
        record, LiquidationCanonicalField.POSITION_SIDE_LIQUIDATED
    )
    assert position.refusal is LiquidationAdmissionRefusal.NO_REGISTRY_MAPPING
    assert record.position_side_liquidated is LiquidationPositionSide.UNKNOWN
    # ...and because one claim is uncertified, the certified sibling is withheld
    # too: the single SEMANTICS_UNVERIFIED flag cannot describe a hybrid.
    assert record.execution_side is AggressorSide.UNKNOWN

    # A row that declares the OTHER canonical field for this provider field is
    # refused by name, so authority cannot be borrowed across fields either.
    misdeclared = _registry(
        _mapping("side", "execution_side"),
        _row_for("execution_side"),
    )
    crossed = normalize_liquidation(_payload(), registry=misdeclared)
    assert (
        _admission(
            crossed, LiquidationCanonicalField.POSITION_SIDE_LIQUIDATED
        ).refusal
        is LiquidationAdmissionRefusal.FIELD_MISMATCH
    )
    assert crossed.position_side_liquidated is LiquidationPositionSide.UNKNOWN


def test_sec_11_position_side_authority_does_not_imply_aggressor_side() -> None:
    record = normalize_liquidation(
        _payload(
            aggressor_side=AggressorSide.BUY,
            native_aggressor_side_field="aggressor",
            native_aggressor_side_value="BUY",
        ),
        registry=_registry(
            _row_for("position_side_liquidated"), _row_for("execution_side")
        ),
    )
    aggressor = _admission(record, LiquidationCanonicalField.AGGRESSOR_SIDE)
    assert aggressor.refusal is LiquidationAdmissionRefusal.NO_REGISTRY_MAPPING
    assert record.aggressor_side is AggressorSide.UNKNOWN
    # the position row exists and admits, and still cannot lend the aggressor one
    assert (
        _admission(
            record, LiquidationCanonicalField.POSITION_SIDE_LIQUIDATED
        ).admitted
        is True
    )
    assert record.position_side_liquidated is LiquidationPositionSide.UNKNOWN


# ---------------------------------------------------------------------------
# SEC-12..SEC-14 -- conflicting evidence and contradictions fail closed
# ---------------------------------------------------------------------------


def test_sec_12_a_not_comparable_mapping_fails_closed() -> None:
    conflict = _registry(
        _mapping(
            "side",
            "position_side_liquidated",
            equivalence=SemanticEquivalence.NOT_COMPARABLE,
        ),
        _row_for("execution_side"),
    )
    record = normalize_liquidation(_payload(), registry=conflict)
    admission = _admission(
        record, LiquidationCanonicalField.POSITION_SIDE_LIQUIDATED
    )
    assert admission.refusal is LiquidationAdmissionRefusal.NOT_COMPARABLE_MAPPING
    assert record.position_side_liquidated is LiquidationPositionSide.UNKNOWN
    assert record.execution_side is AggressorSide.UNKNOWN


def test_sec_13_no_canonical_side_coexists_with_the_blocking_semantic_flag() -> None:
    record = normalize_liquidation(
        _payload(
            aggressor_side=AggressorSide.SELL,
            native_aggressor_side_field="aggressor",
            native_aggressor_side_value="SELL",
            maker_taker_role=LiquidationRole.TAKER,
            native_maker_taker_role_field="role",
            native_maker_taker_role_value="TAKER",
        ),
        registry=_full_registry(),
    )
    assert record.position_side_liquidated is LiquidationPositionSide.LONG
    assert record.execution_side is AggressorSide.SELL
    assert record.aggressor_side is AggressorSide.SELL
    assert record.maker_taker_role is LiquidationRole.TAKER
    assert NormalizationQualityFlag.SEMANTICS_UNVERIFIED.value not in _flags(record)
    assert all(admission.admitted for admission in record.side_admissions)

    # the converse: an uncertified row carries the flag and promotes nothing
    refused = normalize_liquidation(_payload())
    assert NormalizationQualityFlag.SEMANTICS_UNVERIFIED.value in _flags(refused)
    assert refused.position_side_liquidated is LiquidationPositionSide.UNKNOWN
    assert refused.execution_side is AggressorSide.UNKNOWN


def test_sec_14_a_contradiction_stays_quarantined_even_with_full_authority() -> None:
    record = normalize_liquidation(
        _payload(
            position_side_liquidated=LiquidationPositionSide.LONG,
            execution_side=AggressorSide.BUY,
            native_execution_side_value="BUY",
        ),
        registry=_full_registry(),
    )
    assert record.normalization_status is NormalizationStatus.QUARANTINED
    assert record.quarantine_reason is QuarantineReason.INVALID_SIDE_MAPPING
    assert record.position_side_liquidated is LiquidationPositionSide.UNKNOWN
    assert record.execution_side is AggressorSide.UNKNOWN
    assert record.provisional_position_side is LiquidationPositionSide.LONG
    assert all(
        admission.refusal is LiquidationAdmissionRefusal.CONTRADICTION
        for admission in record.side_admissions
    )


# ---------------------------------------------------------------------------
# SEC-15..SEC-16 -- evidence and determinism survive every refusal
# ---------------------------------------------------------------------------


def test_sec_15_native_fields_and_lineage_survive_every_refusal() -> None:
    record = normalize_liquidation(_payload())
    assert record.native_position_side_field == "side"
    assert record.native_position_side_value == "LONG"
    assert record.native_execution_side_field == "orderSide"
    assert record.native_execution_side_value == "SELL"
    assert record.provisional_position_side is LiquidationPositionSide.LONG
    assert record.provisional_execution_side is AggressorSide.SELL
    assert record.lineage.raw_projection_refs == ("proj-1",)
    assert record.lineage.acquisition_refs == ("acq-1",)
    assert record.lineage.evidence_blob_hashes == (_DIGEST,)
    assert record.lineage.code_version == "code-1"
    assert record.lineage.config_version == "cfg-1"


def test_sec_16_repeated_normalization_is_byte_identical() -> None:
    first = normalize_liquidation(_payload(), registry=_full_registry())
    second = normalize_liquidation(_payload(), registry=_full_registry())
    assert first.model_dump_json() == second.model_dump_json()
    assert first.canonical_json() == second.canonical_json()


# ---------------------------------------------------------------------------
# SEC-17..SEC-18 -- the accepted I10 layer and the retired expected failure
# ---------------------------------------------------------------------------


def test_sec_17_the_i10_side_map_authority_is_unchanged() -> None:
    """I10's provisional/admitted split still behaves exactly as ratified."""
    binance_row = _mapping(
        "isBuyerMaker",
        "aggressor_side",
        family=SensorFamily.MECHANICAL_TRADE,
        confidence=SemanticConfidence.AMBIGUOUS,
        evidence=PENDING_EVIDENCE_REFERENCE,
        methodology="AGGRESSOR_FROM_BUYER_MAKER_BINANCE_V1",
    )
    registry = _registry(binance_row)
    row = resolve_side_mapping(
        registry, "BINANCE_USDM", "isBuyerMaker", SensorFamily.MECHANICAL_TRADE
    )
    provisional = apply_side_map(
        SideEvidence.provider_boolean(
            "isBuyerMaker", True, provider="BINANCE_USDM"
        ),
        row,
    )
    assert provisional is not None
    assert provisional.mapped_side is AggressorSide.SELL
    assert provisional.canonical_admitted is False
    assert admit_aggressor_side(AggressorSide.SELL, binance_row.semantic_confidence) is False


def test_sec_18_the_former_strict_xfail_passes_as_an_ordinary_test() -> None:
    """F_I11R1_02's expected failure is retired by behaviour, not by a marker.

    The assertion the I11R1 audit could only record as an xfail now holds with
    no marker at all, and the reason is visible on the record: authority was
    never granted.
    """
    assert "provider_semantics_verified" not in LiquidationObservationInput.model_fields
    record = normalize_liquidation(_payload())
    assert record.position_side_liquidated is LiquidationPositionSide.UNKNOWN
    assert record.execution_side is AggressorSide.UNKNOWN
    assert record.side_admissions
    assert all(
        admission.refusal is LiquidationAdmissionRefusal.NO_NATIVE_FIELD
        or admission.refusal is LiquidationAdmissionRefusal.NO_REGISTRY
        for admission in record.side_admissions
    )


# ---------------------------------------------------------------------------
# SEC-19..SEC-20 -- PIT arithmetic, zero honesty and the USD block are intact
# ---------------------------------------------------------------------------


def test_sec_19_linear_and_inverse_pit_conversion_are_unchanged() -> None:
    linear = normalize_liquidation(
        _payload(),
        terms=_terms(
            payoff=PayoffType.LINEAR,
            multiplier="0.01",
            inverse=False,
            price_unit="USDT",
            quantity_unit="BTC",
        ),
        reference_price=_price("60000"),
        knowledge_cutoff=_CUTOFF,
    )
    assert linear.quantity_base is not None
    assert linear.quantity_base.value == Decimal("2.5")  # 250 x 0.01
    assert linear.liquidation_quote_notional is not None
    assert linear.liquidation_quote_notional.value == Decimal("150000")  # 2.5 x 60000

    inverse = normalize_liquidation(
        _payload(quantity_native=Decimal("2.5")),
        terms=_terms(
            payoff=PayoffType.INVERSE,
            multiplier="100",
            inverse=True,
            price_unit="USD",
            quantity_unit="BTC",
        ),
        reference_price=_price("60000", price_unit="USD"),
        knowledge_cutoff=_CUTOFF,
    )
    assert inverse.liquidation_quote_notional is not None
    assert inverse.liquidation_quote_notional.value == Decimal("250")  # 2.5 x 100
    assert inverse.quantity_base is not None
    assert inverse.quantity_base.value == Decimal("250") / Decimal("60000")


def test_sec_20_zero_missing_and_the_usd_block_are_unchanged() -> None:
    zero = normalize_liquidation(
        _payload(
            liquidation_event_id=None,
            quantity_native=Decimal("0"),
            quantity_native_unit="BTC",
            aggregation_scope=LiquidationAggregationScope.INTERVAL_AGGREGATE,
            count=0,
            provider_reports_completed_intervals=True,
            interval_closed=True,
            source_coverage_state=CoverageState.KNOWN_GAP,
        )
    )
    assert zero.zero_interval_state is LiquidationZeroIntervalState.UNVERIFIED_MISSING
    assert zero.quantity_native == Decimal("0")

    with pytest.raises(ValueError, match="must not carry liquidation_event_id"):
        _payload(
            aggregation_scope=LiquidationAggregationScope.INTERVAL_AGGREGATE,
            count=2,
            liquidation_event_id="liq-agg",
        )

    usd = normalize_liquidation(
        _payload(),
        terms=_terms(payoff=PayoffType.LINEAR, multiplier="0.01", inverse=False),
        reference_price=_price("60000"),
        knowledge_cutoff=_CUTOFF,
    )
    assert usd.liquidation_usd is not None
    assert usd.liquidation_usd.blocked is True
    assert usd.liquidation_usd.value is None
    assert usd.liquidation_usd.unresolved_citation == "B5_I08_UNITS_V1"
