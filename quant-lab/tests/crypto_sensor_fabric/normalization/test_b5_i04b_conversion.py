"""SENSOR-B5-I04B - RED-first linear/inverse conversion suite.

Executable fixtures authored BEFORE any I04B conversion module exists: this
file is the RED capture (import of the absent conversion surface fails), then
the standing regression battery once Phases C/D land.

Contract law under test (I04B directive):
  * economic-truth invariant -- a value is emitted only when identity, PIT
    terms, dimensional compatibility, permitted formula, eligible price
    evidence, versioned lineage and methodology all hold; otherwise
    ``normalized_value is None`` + ``UNIT_CONVERSION_BLOCKED`` (bloc_05/03
    S8, G5, G9; directive Books 0.2/4).
  * dimensional authority (Book 2.1): every dimension check is a token
    equality against the contract's own recorded terms -- count denomination
    ``contracts_unit == multiplier_unit``; price dimension
    ``(price_unit, quantity_unit)``; outputs ``quantity_unit``/``price_unit``
    per bloc_05/03 S7/S8.  Never inferred from a number (Book 2.1 core
    prohibition), never 1-contract-1-base (S7 explicit).
  * reference-price truth (Book 3): five frozen types only (bloc_05/03 S8),
    no silent substitution, dimension + source + UTC + finite + domain +
    availability proven by frozen ``market_available_at`` (bloc_05/02 S4)
    at or before the requested knowledge cutoff -- observation time alone
    never proves availability.
  * payoff-family isolation (Book 2.4): LINEAR / INVERSE supported where the
    terms prove the formula; QUANTO / UNKNOWN / SPOT / inconsistent flags
    refused.  No universal formula (bloc_05/07 F5).

Ownership: I04B lives in ``normalization/terms/conversion.py`` -- NOT I08's
``common/conversion.py``, NOT I03 identity, NOT I05 time.  The top-level
normalization public surface stays the ratified 24 symbols (names reached
only through ``...normalization.terms``).

OFFLINE: all fixtures are deterministic local data; all times UTC-aware.
Plan citations use the compact S<n> form for bloc_05/0<n> sections.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from crypto_sensor_fabric.normalization.enums import (
    NormalizationQualityFlag,
    PayoffType,
)
from crypto_sensor_fabric.normalization.identity import (
    CanonicalAsset,
    ContractInstance,
    EconomicContract,
    IdentityRegistrySnapshot,
    IdentityResolution,
    IdentityResolutionStatus,
    Venue,
    VenueInstrument,
    resolve_instrument,
)
from crypto_sensor_fabric.normalization.models import canonical_json_bytes
from crypto_sensor_fabric.normalization.terms import (
    ContractTermsSnapshot,
    project_contract_terms,
)
from crypto_sensor_fabric.normalization.terms.conversion import (
    ConversionResult,
    ReferencePriceEvidence,
    ReferencePriceType,
    contracts_to_quote_notional,
    inverse_base_from_quote,
    inverse_quote_face,
    linear_base_exposure,
    quote_notional,
)

UTC = timezone.utc

# ---------------------------------------------------------------- constants

EVENT = datetime(2023, 9, 1, hour=12, tzinfo=UTC)
CUTOFF = datetime(2023, 10, 1, hour=12, tzinfo=UTC)
PRICE_AT = datetime(2023, 9, 1, hour=11, tzinfo=UTC)
AVAILABLE_AT = datetime(2023, 9, 1, hour=11, minute=1, tzinfo=UTC)

T0 = datetime(2023, 1, 1, hour=12, tzinfo=UTC)
T1 = datetime(2024, 1, 1, hour=12, tzinfo=UTC)
K0 = datetime(2023, 6, 1, tzinfo=UTC)
K1 = datetime(2023, 12, 1, tzinfo=UTC)

PROVIDER = "PROV"
VENUE = "EXA_FUT"
NATIVE = "XBTUSDT"
SHA256 = "3f79bb7b435b05321651daefd374cdc681dc06faa65e374e38337b88ca4c6a11"
REFS = ("provider-docs:exchange-a-xbtusdt",)
PRICE_REFS = ("provider-docs:exchange-a-index-price",)

BLOCKED = NormalizationQualityFlag.UNIT_CONVERSION_BLOCKED


# ---------------------------------------------------------------- fixtures


def terms_snapshot(
    *,
    instance_id: str = "CI-LIN",
    multiplier: Decimal = Decimal("0.001"),
    multiplier_unit: str = "CONTRACT",
    price_unit: str = "USDT",
    quantity_unit: str = "BTC",
    payoff: PayoffType = PayoffType.LINEAR,
    inverse_flag: bool = False,
    quanto_flag: bool = False,
    version: str = "1",
    settlement: str = "USDT",
    refs: tuple[str, ...] = REFS,
) -> ContractTermsSnapshot:
    """A directly-constructed snapshot (I04A frozen carrier, 17 fields)."""
    return ContractTermsSnapshot(
        contract_instance_id=instance_id,
        economic_contract_id="EC-A",
        contract_terms_version=version,
        contract_multiplier=multiplier,
        multiplier_unit=multiplier_unit,
        price_unit=price_unit,
        quantity_unit=quantity_unit,
        payoff_type=payoff,
        inverse_flag=inverse_flag,
        quanto_flag=quanto_flag,
        quote_asset_id="USDT",
        settlement_asset_id=settlement,
        margin_asset_id=None,
        tick_size=Decimal("0.1"),
        lot_size=Decimal("0.0001"),
        expiry=None,
        source_evidence_refs=refs,
    )


def inverse_terms(**kw) -> ContractTermsSnapshot:
    kw.setdefault("instance_id", "CI-INV")
    kw.setdefault("multiplier", Decimal("10000"))
    kw.setdefault("payoff", PayoffType.INVERSE)
    kw.setdefault("inverse_flag", True)
    kw.setdefault("settlement", "BTC")  # inverse settles in base (06 S4)
    return terms_snapshot(**kw)


def price_evidence(**kw) -> ReferencePriceEvidence:
    kw.setdefault("source", "exchange-a:index")
    kw.setdefault("base_unit", None)
    fields = {
        "reference_price": kw.pop("value", Decimal("25000")),
        "reference_price_type": kw.pop("ptype", ReferencePriceType.PROVIDER_INDEX),
        "reference_price_time": kw.pop("observed", PRICE_AT),
        "reference_price_source": kw.pop("source", "exchange-a:index"),
        "market_available_at": kw.pop("available", AVAILABLE_AT),
        "reference_price_unit": kw.pop("unit", "USDT"),
        "reference_price_base_unit": kw.pop("base_unit", None),
        "source_evidence_refs": kw.pop("refs", PRICE_REFS),
    }
    if fields["reference_price_base_unit"] is None:
        fields["reference_price_base_unit"] = "BTC"
    assert not kw, f"unexpected price_evidence kwargs: {sorted(kw)}"
    return ReferencePriceEvidence(**fields)


def price_payload(**kw) -> dict:
    """Raw caller-supplied price payload (engine must validate it)."""
    base = {
        "reference_price": Decimal("25000"),
        "reference_price_type": ReferencePriceType.PROVIDER_INDEX,
        "reference_price_time": PRICE_AT,
        "reference_price_source": "exchange-a:index",
        "market_available_at": AVAILABLE_AT,
        "reference_price_unit": "USDT",
        "reference_price_base_unit": "BTC",
        "source_evidence_refs": PRICE_REFS,
    }
    base.update(kw)
    return base


def assert_blocked(res: ConversionResult) -> None:
    assert res.normalized_value is None, (
        f"blocked conversion must emit NULL, got {res.normalized_value!r}"
    )
    assert BLOCKED in res.quality_flags, f"missing {BLOCKED}: {res.quality_flags}"
    assert res.reference_price is None, "blocked result must not consume price"
    assert res.conversion_inputs == (), "blocked result must not claim inputs"
    assert res.native_quantity is None or res.native_quantity.is_finite()


def assert_success(res: ConversionResult, expected: Decimal) -> None:
    assert res.normalized_value == expected, (
        f"expected {expected}, observed {res.normalized_value!r}"
    )
    assert res.quality_flags == ()
    assert BLOCKED not in res.quality_flags
    assert res.output_unit is not None
    assert res.methodology_version
    assert res.contract_instance_id is not None
    assert res.contract_terms_version is not None
    assert res.conversion_inputs


# ---------------------------------------------------------------- linear
# LIN-01..07 positive; LIN-R01..09 refusal (directive Book 6.1)


def test_lin_01_non_unit_multiplier_produces_base_exposure() -> None:
    """Non-unit multiplier: 3 contracts x 0.001 BTC/contract = 0.003 BTC
    (bloc_05/03 S7; never 1-contract-1-base)."""
    res = linear_base_exposure(
        contracts=Decimal("3"),
        contracts_unit="CONTRACT",
        terms=terms_snapshot(multiplier=Decimal("0.001")),
    )
    assert_success(res, Decimal("0.003"))
    assert res.output_unit == "BTC"


def test_lin_02_fractional_contracts_retain_decimal_precision() -> None:
    res_a = linear_base_exposure(
        contracts=Decimal("1.101"),
        contracts_unit="CONTRACT",
        terms=terms_snapshot(multiplier=Decimal("3")),
    )
    assert_success(res_a, Decimal("3.303"))
    res_b = linear_base_exposure(
        contracts=Decimal("0.5"),
        contracts_unit="CONTRACT",
        terms=terms_snapshot(multiplier=Decimal("0.001")),
    )
    assert_success(res_b, Decimal("0.0005"))
    assert isinstance(res_a.normalized_value, Decimal)


def test_lin_03_verified_price_produces_quote_notional_chain() -> None:
    """Contracts -> base -> quote notional through the complete supported
    chain (Book 2.2 op 3): 3 * 0.001 = 0.003 BTC x 25000 USDT/BTC = 75 USDT."""
    terms = terms_snapshot(multiplier=Decimal("0.001"))
    res = contracts_to_quote_notional(
        contracts=Decimal("3"),
        contracts_unit="CONTRACT",
        terms=terms,
        price=price_evidence(),
        knowledge_cutoff=CUTOFF,
    )
    assert_success(res, Decimal("75"))
    assert res.output_unit == "USDT"
    assert res.reference_price is not None
    assert res.reference_price.reference_price_type is ReferencePriceType.PROVIDER_INDEX
    assert res.reference_price.reference_price_source == "exchange-a:index"
    assert any(i.startswith("contract_multiplier_ref=") for i in res.conversion_inputs)
    assert any(i.startswith("price_observation_ref=") for i in res.conversion_inputs)


def test_lin_04_economically_valid_zero_contracts_produce_zero() -> None:
    res = linear_base_exposure(
        contracts=Decimal("0"),
        contracts_unit="CONTRACT",
        terms=terms_snapshot(multiplier=Decimal("0.001")),
    )
    assert res.normalized_value == Decimal("0")
    assert res.normalized_value is not None  # null != zero (S22 inv.5)
    assert res.quality_flags == ()
    res_n = linear_base_exposure(
        contracts=Decimal("-2.5"),  # short direction is recorded truth
        contracts_unit="CONTRACT",
        terms=terms_snapshot(multiplier=Decimal("0.001")),
    )
    assert_success(res_n, Decimal("-0.0025"))


def test_lin_05_base_valid_while_price_notional_blocks() -> None:
    terms = terms_snapshot(multiplier=Decimal("0.001"))
    base = linear_base_exposure(
        contracts=Decimal("3"),
        contracts_unit="CONTRACT",
        terms=terms,
    )
    assert_success(base, Decimal("0.003"))
    notional = quote_notional(
        base_exposure=base.normalized_value,
        base_unit="BTC",
        terms=terms,
        price=None,
        knowledge_cutoff=CUTOFF,
    )
    assert_blocked(notional)
    assert notional.output_unit == "USDT"
    assert notional.native_quantity == Decimal("0.003")  # native preserved
    assert notional.native_unit == "BTC"


def test_lin_06_quote_and_settlement_identities_remain_distinct() -> None:
    terms = terms_snapshot(multiplier=Decimal("0.001"), settlement="USD")
    assert terms.quote_asset_id == "USDT"
    assert terms.settlement_asset_id == "USD"
    res = quote_notional(
        base_exposure=Decimal("0.003"),
        base_unit="BTC",
        terms=terms,
        price=price_evidence(),
        knowledge_cutoff=CUTOFF,
    )
    assert_success(res, Decimal("75"))
    assert res.output_unit == "USDT"  # quote denomination, never settlement
    assert terms.settlement_asset_id == "USD"  # untouched (F6)


def test_lin_07_repeated_inputs_produce_identical_results() -> None:
    args = dict(
        contracts=Decimal("3"),
        contracts_unit="CONTRACT",
        terms=terms_snapshot(multiplier=Decimal("0.001")),
    )
    assert linear_base_exposure(**args) == linear_base_exposure(**args)


def test_lin_r01_incompatible_multiplier_dimension_blocks() -> None:
    res = linear_base_exposure(
        contracts=Decimal("3"),
        contracts_unit="LOT",  # not the recorded count denomination
        terms=terms_snapshot(multiplier_unit="CONTRACT"),
    )
    assert_blocked(res)


def test_lin_r02_unverified_terms_block() -> None:
    res = linear_base_exposure(
        contracts=Decimal("3"),
        contracts_unit="CONTRACT",
        terms=None,  # projection refused unverified/ineligible terms
    )
    assert_blocked(res)
    assert res.contract_instance_id is None
    assert res.contract_terms_version is None


def test_lin_r03_unknown_payoff_blocks() -> None:
    res = linear_base_exposure(
        contracts=Decimal("3"),
        contracts_unit="CONTRACT",
        terms=terms_snapshot(payoff=PayoffType.UNKNOWN),
    )
    assert_blocked(res)


def test_lin_r04_inverse_misrouted_to_linear_blocks() -> None:
    res = linear_base_exposure(
        contracts=Decimal("3"),
        contracts_unit="CONTRACT",
        terms=inverse_terms(),
    )
    assert_blocked(res)


def test_lin_r05_quanto_misrouted_to_linear_blocks() -> None:
    res = linear_base_exposure(
        contracts=Decimal("3"),
        contracts_unit="CONTRACT",
        terms=terms_snapshot(payoff=PayoffType.QUANTO, quanto_flag=True),
    )
    assert_blocked(res)


def test_lin_r06_wrong_reference_price_dimension_blocks() -> None:
    res = quote_notional(
        base_exposure=Decimal("0.003"),
        base_unit="BTC",
        terms=terms_snapshot(),
        price=price_evidence(base_unit="ETH"),  # base side mismatch (S4)
        knowledge_cutoff=CUTOFF,
    )
    assert_blocked(res)


def test_lin_r07_non_finite_numeric_input_blocks() -> None:
    res_nan = linear_base_exposure(
        contracts=Decimal("NaN"),
        contracts_unit="CONTRACT",
        terms=terms_snapshot(),
    )
    assert_blocked(res_nan)
    assert res_nan.native_quantity is None  # no lawful NaN storage: absence
    assert res_nan.native_unit == "CONTRACT"  # native unit still preserved
    res_inf = linear_base_exposure(
        contracts=Decimal("Infinity"),
        contracts_unit="CONTRACT",
        terms=terms_snapshot(),
    )
    assert_blocked(res_inf)
    assert res_inf.native_quantity is None


def test_lin_r08_inadequate_provenance_blocks() -> None:
    res = quote_notional(
        base_exposure=Decimal("0.003"),
        base_unit="BTC",
        terms=terms_snapshot(),
        price=price_payload(source_evidence_refs=()),  # no evidence ref (G5/S17)
        knowledge_cutoff=CUTOFF,
    )
    assert_blocked(res)


def test_lin_r09_unsupported_output_unit_blocks() -> None:
    res = linear_base_exposure(
        contracts=Decimal("3"),
        contracts_unit="CONTRACT",
        terms=terms_snapshot(),
        output_unit="ETH",  # not the recorded quantity denomination
    )
    assert_blocked(res)


# ---------------------------------------------------------------- inverse
# INV-01..16 (directive Book 6.2)


def test_inv_01_verified_quote_face_converts_under_permitted_formula() -> None:
    """base = quote_face / reference_price (Book 2.3 candidate relation,
    admitted: payoff INVERSE proven, face in quote denomination, PIT price)."""
    res = inverse_base_from_quote(
        quote_face_notional=Decimal("10000"),
        quote_face_unit="USDT",
        terms=inverse_terms(),
        price=price_evidence(),
        knowledge_cutoff=CUTOFF,
    )
    assert_success(res, Decimal("0.4"))
    assert res.output_unit == "BTC"


def test_inv_01b_contracts_to_face_to_base_chain() -> None:
    """Complete inverse chain: contracts -> quote face (no price) ->
    base equivalent with PIT price: 1 x 10000 USDT = 10000 USDT / 25000 = 0.4 BTC."""
    face = inverse_quote_face(
        contracts=Decimal("1"),
        contracts_unit="CONTRACT",
        terms=inverse_terms(),
    )
    assert_success(face, Decimal("10000"))
    assert face.output_unit == "USDT"
    base = inverse_base_from_quote(
        quote_face_notional=face.normalized_value,
        quote_face_unit=face.output_unit,
        terms=inverse_terms(),
        price=price_evidence(),
        knowledge_cutoff=CUTOFF,
    )
    assert_success(base, Decimal("0.4"))
    assert base.output_unit == "BTC"


def test_op_wrong_base_unit_blocks() -> None:
    """The base leg of a notional conversion must be denominated in the
    contract's recorded quantity unit (S4 dimensional identity)."""
    res = quote_notional(
        base_exposure=Decimal("0.003"),
        base_unit="ETH",
        terms=terms_snapshot(),
        price=price_evidence(),
        knowledge_cutoff=CUTOFF,
    )
    assert_blocked(res)


def test_inv_02_price_type_and_source_captured() -> None:
    res = inverse_base_from_quote(
        quote_face_notional=Decimal("10000"),
        quote_face_unit="USDT",
        terms=inverse_terms(),
        price=price_evidence(
            ptype=ReferencePriceType.TRADE_PRICE,
            source="exchange-a:trades",
        ),
        knowledge_cutoff=CUTOFF,
    )
    assert_success(res, Decimal("0.4"))
    assert res.reference_price is not None
    assert res.reference_price.reference_price_type is ReferencePriceType.TRADE_PRICE
    assert res.reference_price.reference_price_source == "exchange-a:trades"


def test_inv_03_decimal_arithmetic_exact() -> None:
    res = inverse_base_from_quote(
        quote_face_notional=Decimal("10000.01"),
        quote_face_unit="USDT",
        terms=inverse_terms(),
        price=price_evidence(value=Decimal("2500")),
        knowledge_cutoff=CUTOFF,
    )
    assert_success(res, Decimal("4.000004"))  # terminating, exact


def test_inv_04_distinct_quote_and_settlement_assets_preserved() -> None:
    terms = inverse_terms()  # quote=USDT, settlement=BTC (06 S4 inverse row)
    assert terms.quote_asset_id == "USDT"
    assert terms.settlement_asset_id == "BTC"
    assert terms.quote_asset_id != terms.settlement_asset_id
    res = inverse_base_from_quote(
        quote_face_notional=Decimal("10000"),
        quote_face_unit="USDT",
        terms=terms,
        price=price_evidence(),
        knowledge_cutoff=CUTOFF,
    )
    assert_success(res, Decimal("0.4"))
    assert terms.quote_asset_id == "USDT"
    assert terms.settlement_asset_id == "BTC"


def test_inv_05_missing_price_blocks() -> None:
    res = inverse_base_from_quote(
        quote_face_notional=Decimal("10000"),
        quote_face_unit="USDT",
        terms=inverse_terms(),
        price=None,
        knowledge_cutoff=CUTOFF,
    )
    assert_blocked(res)


def test_inv_06_zero_price_blocks_division() -> None:
    res = inverse_base_from_quote(
        quote_face_notional=Decimal("10000"),
        quote_face_unit="USDT",
        terms=inverse_terms(),
        price=price_payload(reference_price=Decimal("0")),
        knowledge_cutoff=CUTOFF,
    )
    assert_blocked(res)


def test_inv_07_invalid_price_domain_blocks() -> None:
    res = inverse_base_from_quote(
        quote_face_notional=Decimal("10000"),
        quote_face_unit="USDT",
        terms=inverse_terms(),
        price=price_payload(reference_price=Decimal("-5")),
        knowledge_cutoff=CUTOFF,
    )
    assert_blocked(res)


def test_inv_08_missing_price_source_blocks() -> None:
    res = inverse_base_from_quote(
        quote_face_notional=Decimal("10000"),
        quote_face_unit="USDT",
        terms=inverse_terms(),
        price=price_payload(reference_price_source="   "),
        knowledge_cutoff=CUTOFF,
    )
    assert_blocked(res)


def test_inv_09_naive_timestamp_blocks() -> None:
    res = inverse_base_from_quote(
        quote_face_notional=Decimal("10000"),
        quote_face_unit="USDT",
        terms=inverse_terms(),
        price=price_payload(reference_price_time=datetime(2023, 9, 1, 11, 0)),
        knowledge_cutoff=CUTOFF,
    )
    assert_blocked(res)


def test_inv_10_future_known_price_blocks() -> None:
    """market_available_at (bloc_05/02 S4 availability clock) after the
    knowledge cutoff: an observation not knowable by the cutoff blocks."""
    res = inverse_base_from_quote(
        quote_face_notional=Decimal("10000"),
        quote_face_unit="USDT",
        terms=inverse_terms(),
        price=price_payload(
            market_available_at=CUTOFF.replace(microsecond=1)
        ),
        knowledge_cutoff=CUTOFF,
    )
    assert_blocked(res)


def test_inv_11_incorrect_price_dimension_blocks() -> None:
    res = inverse_base_from_quote(
        quote_face_notional=Decimal("10000"),
        quote_face_unit="USDT",
        terms=inverse_terms(),
        price=price_evidence(base_unit="ETH", unit="USDT"),
        knowledge_cutoff=CUTOFF,
    )
    assert_blocked(res)


def test_inv_12_wrong_payoff_family_blocks() -> None:
    res = inverse_base_from_quote(
        quote_face_notional=Decimal("10000"),
        quote_face_unit="USDT",
        terms=terms_snapshot(multiplier=Decimal("0.001")),  # LINEAR
        price=price_evidence(),
        knowledge_cutoff=CUTOFF,
    )
    assert_blocked(res)


def test_inv_13_wrong_multiplier_denomination_blocks() -> None:
    """The verified face must be denominated in the contract's quote unit
    (multiplier numerator for INVERSE is quote-face by S8); a base-denominated
    face is a different economic quantity (Book 2.3 proof 1)."""
    res = inverse_base_from_quote(
        quote_face_notional=Decimal("10000"),
        quote_face_unit="BTC",  # base denomination, not quote face
        terms=inverse_terms(),
        price=price_evidence(),
        knowledge_cutoff=CUTOFF,
    )
    assert_blocked(res)


def test_inv_14_price_type_substitution_blocks() -> None:
    res = inverse_base_from_quote(
        quote_face_notional=Decimal("10000"),
        quote_face_unit="USDT",
        terms=inverse_terms(),
        price=price_evidence(ptype=ReferencePriceType.PROVIDER_MARK),
        knowledge_cutoff=CUTOFF,
        required_price_type=ReferencePriceType.TRADE_PRICE,
    )
    assert_blocked(res)


def test_inv_15_native_inputs_unchanged() -> None:
    terms = inverse_terms()
    face = Decimal("10000")
    price = price_evidence()
    terms_before = terms.model_dump(mode="json")
    price_before = price.model_dump(mode="json")
    inverse_base_from_quote(
        quote_face_notional=face,
        quote_face_unit="USDT",
        terms=terms,
        price=price,
        knowledge_cutoff=CUTOFF,
    )
    assert terms.model_dump(mode="json") == terms_before
    assert price.model_dump(mode="json") == price_before
    assert face == Decimal("10000")


def test_inv_16_repeated_execution_deterministic() -> None:
    args = dict(
        quote_face_notional=Decimal("10000"),
        quote_face_unit="USDT",
        terms=inverse_terms(),
        price=price_evidence(),
        knowledge_cutoff=CUTOFF,
    )
    assert inverse_base_from_quote(**args) == inverse_base_from_quote(**args)


# ---------------------------------------------------------------- adversarial
# ADV-A..J (directive Book 6.3), each with forbidden-result assertion


def test_adv_a_multiplier_denomination_laundering() -> None:
    """A quote-denominated count unit cannot launder into the base formula:
    the recorded count denomination must match exactly (Book 2.1)."""
    res = linear_base_exposure(
        contracts=Decimal("3"),
        contracts_unit="USDT",
        terms=terms_snapshot(multiplier_unit="CONTRACT"),
    )
    assert_blocked(res)
    res_face = inverse_quote_face(
        contracts=Decimal("1"),
        contracts_unit="USDT",
        terms=inverse_terms(),
    )
    assert_blocked(res_face)


def test_adv_b_price_source_substitution() -> None:
    res = quote_notional(
        base_exposure=Decimal("0.003"),
        base_unit="BTC",
        terms=terms_snapshot(),
        price=price_evidence(ptype=ReferencePriceType.MID_PRICE),
        knowledge_cutoff=CUTOFF,
        required_price_type=ReferencePriceType.INTERVAL_CLOSE,
    )
    assert_blocked(res)  # no silent substitution (S8, Book 3.4)


def test_adv_c_future_information_leakage() -> None:
    res = contracts_to_quote_notional(
        contracts=Decimal("3"),
        contracts_unit="CONTRACT",
        terms=terms_snapshot(multiplier=Decimal("0.001")),
        price=price_payload(market_available_at=CUTOFF.replace(microsecond=1)),
        knowledge_cutoff=CUTOFF,
    )
    assert_blocked(res)


def test_adv_d_ambiguous_identity_laundering() -> None:
    ambiguous = IdentityResolution(status=IdentityResolutionStatus.AMBIGUOUS)
    reg = registry()
    snap = project_contract_terms(
        registry=reg,
        resolution=ambiguous,
        event_time=EVENT,
        knowledge_cutoff=CUTOFF,
    )
    assert snap is None
    res = linear_base_exposure(
        contracts=Decimal("3"),
        contracts_unit="CONTRACT",
        terms=snap,
    )
    assert_blocked(res)


def test_adv_e_usd_stablecoin_substitution() -> None:
    """USD-priced contract vs USDT-denominated observation: F7 distinctness;
    the dimension equality refuses the substitution."""
    terms = terms_snapshot(price_unit="USD")
    res = quote_notional(
        base_exposure=Decimal("0.003"),
        base_unit="BTC",
        terms=terms,
        price=price_evidence(unit="USDT"),
        knowledge_cutoff=CUTOFF,
    )
    assert_blocked(res)


def test_adv_f_payoff_family_confusion() -> None:
    quanto = terms_snapshot(payoff=PayoffType.QUANTO, quanto_flag=True)
    assert_blocked(
        linear_base_exposure(
            contracts=Decimal("1"), contracts_unit="CONTRACT", terms=quanto
        )
    )
    assert_blocked(
        inverse_quote_face(
            contracts=Decimal("1"), contracts_unit="CONTRACT", terms=quanto
        )
    )
    assert_blocked(
        inverse_base_from_quote(
            quote_face_notional=Decimal("10000"),
            quote_face_unit="USDT",
            terms=terms_snapshot(multiplier=Decimal("0.001")),
            price=price_evidence(),
            knowledge_cutoff=CUTOFF,
        )
    )
    assert_blocked(
        quote_notional(
            base_exposure=Decimal("1"),
            base_unit="BTC",
            terms=inverse_terms(),
            price=price_evidence(),
            knowledge_cutoff=CUTOFF,
        )
    )


def test_adv_g_null_to_zero_replacement() -> None:
    res = quote_notional(
        base_exposure=Decimal("1"),
        base_unit="BTC",
        terms=terms_snapshot(),
        price=None,
        knowledge_cutoff=CUTOFF,
    )
    assert res.normalized_value is None
    assert res.normalized_value != 0  # NULL is not numeric zero (S22 inv.5)


def test_adv_h_fabricated_lineage() -> None:
    terms = terms_snapshot(multiplier=Decimal("0.001"))
    res = contracts_to_quote_notional(
        contracts=Decimal("3"),
        contracts_unit="CONTRACT",
        terms=terms,
        price=price_evidence(),
        knowledge_cutoff=CUTOFF,
    )
    # every reference traces to an actual input (A8 / S17 lineage)
    assert "contract_multiplier_ref=CI-LIN#1" in res.conversion_inputs
    assert (
        "price_observation_ref=exchange-a:index@"
        + PRICE_AT.isoformat()
    ) in res.conversion_inputs
    allowed = set(terms.source_evidence_refs) | set(PRICE_REFS)
    assert set(res.source_evidence_refs) <= allowed
    assert len(res.source_evidence_refs) == len(set(res.source_evidence_refs))


def test_adv_i_terms_version_mismatch() -> None:
    terms = terms_snapshot(version="1")
    res = linear_base_exposure(
        contracts=Decimal("3"),
        contracts_unit="CONTRACT",
        terms=terms,
    )
    assert res.contract_terms_version == terms.contract_terms_version
    assert res.contract_terms_version != "2"  # no silent version upgrade


def test_adv_j_nondeterministic_regeneration() -> None:
    args = dict(
        contracts=Decimal("3"),
        contracts_unit="CONTRACT",
        terms=terms_snapshot(multiplier=Decimal("0.001")),
    )
    a = linear_base_exposure(**args)
    b = linear_base_exposure(**args)
    assert canonical_json_bytes(a) == canonical_json_bytes(b)


# ---------------------------------------------------------------- integration
# Phase E: I03 resolution -> I04A terms -> I04B conversion, refusal chains


def asset(asset_id: str) -> CanonicalAsset:
    return CanonicalAsset(
        asset_id=asset_id,
        symbol_canonical=asset_id,
        asset_type="CRYPTO",
        metadata_version="1",
    )


def economic_contract() -> EconomicContract:
    return EconomicContract(
        economic_contract_id="EC-A",
        underlying_asset_id="BTC",
        quote_asset_id="USDT",
        settlement_asset_id="USDT",
        margin_asset_id=None,
        instrument_type="PERPETUAL_FUTURE",
        perpetual_or_delivery="PERPETUAL",
        payoff_type=PayoffType.LINEAR,
    )


def instance(
    instance_id: str = "CI-A",
    *,
    multiplier: Decimal = Decimal("0.001"),
    known_to: datetime | None = None,
    version: str = "1",
) -> ContractInstance:
    return ContractInstance(
        contract_instance_id=instance_id,
        provider=PROVIDER,
        venue=VENUE,
        native_symbol=NATIVE,
        economic_contract_id="EC-A",
        valid_from=T0,
        valid_to=T1,
        known_from=K0,
        known_to=known_to,
        contract_multiplier=multiplier,
        multiplier_unit="CONTRACT",
        price_unit="USDT",
        quantity_unit="BTC",
        settlement_asset_id="USDT",
        margin_asset_id=None,
        payoff_type=PayoffType.LINEAR,
        inverse_flag=False,
        quanto_flag=False,
        tick_size=Decimal("0.1"),
        lot_size=Decimal("0.0001"),
        expiry=None,
        contract_terms_version=version,
        source_evidence_refs=REFS,
    )


def registry(*instances: ContractInstance) -> IdentityRegistrySnapshot:
    return IdentityRegistrySnapshot(
        registry_version="i04b-fix",
        assets=(asset("BTC"), asset("USDT"), asset("USD")),
        venues=(Venue(venue_id=VENUE),),
        economic_contracts=(economic_contract(),),
        venue_instruments=(
            VenueInstrument(
                provider=PROVIDER,
                venue=VENUE,
                native_symbol=NATIVE,
                instrument_type="PERPETUAL_FUTURE",
                native_metadata_hash=SHA256,
                first_seen_at=T0,
                last_seen_at=datetime.max.replace(tzinfo=UTC),
            ),
        ),
        contract_instances=instances or (instance(),),
    )


def test_int_01_resolved_chain_produces_verified_exposure() -> None:
    reg = registry(instance(multiplier=Decimal("0.001")))
    resolution = resolve_instrument(
        snapshot=reg,
        provider=PROVIDER,
        venue=VENUE,
        native_symbol=NATIVE,
        event_time=EVENT,
        knowledge_cutoff=CUTOFF,
    )
    assert resolution.status is IdentityResolutionStatus.RESOLVED_EXACT
    snap = project_contract_terms(
        registry=reg,
        resolution=resolution,
        event_time=EVENT,
        knowledge_cutoff=CUTOFF,
    )
    assert snap is not None
    res = linear_base_exposure(
        contracts=Decimal("3"),
        contracts_unit="CONTRACT",
        terms=snap,
    )
    assert_success(res, Decimal("0.003"))
    # inputs untouched by the whole chain
    assert reg.contract_instances[0].contract_multiplier == Decimal("0.001")
    assert resolution.status is IdentityResolutionStatus.RESOLVED_EXACT


def test_int_02_knowledge_ineligible_terms_chain_blocks() -> None:
    """Terms PIT-ineligible at the cutoff (== known_to): projection refuses,
    so conversion cannot run on knowledge it may not have (G1/C2, P11)."""
    reg = registry(instance(known_to=K1))
    resolution = resolve_instrument(
        snapshot=reg,
        provider=PROVIDER,
        venue=VENUE,
        native_symbol=NATIVE,
        event_time=EVENT,
        knowledge_cutoff=K1,  # exactly at known_to -> outside eligibility
    )
    if resolution.status is IdentityResolutionStatus.RESOLVED_EXACT:
        snap = project_contract_terms(
            registry=reg,
            resolution=resolution,
            event_time=EVENT,
            knowledge_cutoff=K1,
        )
        assert snap is None
    res = linear_base_exposure(
        contracts=Decimal("3"),
        contracts_unit="CONTRACT",
        terms=None,
    )
    assert_blocked(res)


def test_int_03_unresolved_identity_chain_blocks() -> None:
    resolution = resolve_instrument(
        snapshot=registry(),
        provider=PROVIDER,
        venue=VENUE,
        native_symbol="NOSUCH",
        event_time=EVENT,
        knowledge_cutoff=CUTOFF,
    )
    assert resolution.status is IdentityResolutionStatus.UNKNOWN_SYMBOL
    snap = project_contract_terms(
        registry=registry(),
        resolution=resolution,
        event_time=EVENT,
        knowledge_cutoff=CUTOFF,
    )
    assert snap is None
    res = contracts_to_quote_notional(
        contracts=Decimal("1"),
        contracts_unit="CONTRACT",
        terms=snap,
        price=price_evidence(),
        knowledge_cutoff=CUTOFF,
    )
    assert_blocked(res)


def test_op_naive_knowledge_cutoff_blocks() -> None:
    """Fail-closed on a naive cutoff (G9): availability comparison against an
    unprovable clock is refused, never coerced."""
    res = quote_notional(
        base_exposure=Decimal("1"),
        base_unit="BTC",
        terms=terms_snapshot(),
        price=price_evidence(),
        knowledge_cutoff=datetime(2023, 10, 1, 12, 0),  # naive
    )
    assert_blocked(res)


# ---------------------------------------------------------------- schema laws
# N0-style impossible combinations (bloc_05/06 S3): must fail validation.


def _success_result(**over) -> ConversionResult:
    base = dict(
        native_quantity=Decimal("3"),
        native_unit="CONTRACT",
        normalized_value=Decimal("0.003"),
        output_unit="BTC",
        quality_flags=(),
        contract_instance_id="CI-LIN",
        contract_terms_version="1",
        methodology_version="B5_I04B_CONVERSION_V1",
        conversion_inputs=("contract_multiplier_ref=CI-LIN#1",),
        source_evidence_refs=REFS,
        reference_price=None,
    )
    base.update(over)
    return ConversionResult(**base)


def _blocked_result(**over) -> ConversionResult:
    base = dict(
        native_quantity=Decimal("3"),
        native_unit="CONTRACT",
        normalized_value=None,
        output_unit="BTC",
        quality_flags=(BLOCKED,),
        contract_instance_id="CI-LIN",
        contract_terms_version="1",
        methodology_version="B5_I04B_CONVERSION_V1",
        conversion_inputs=(),
        source_evidence_refs=(),
        reference_price=None,
    )
    base.update(over)
    return ConversionResult(**base)


def test_schema_01_success_with_blocked_flag_fails() -> None:
    with pytest.raises(ValidationError):
        _success_result(quality_flags=(BLOCKED,))


def test_schema_02_blocked_without_flag_fails() -> None:
    with pytest.raises(ValidationError):
        _blocked_result(quality_flags=())


def test_schema_03_blocked_with_conversion_inputs_fails() -> None:
    with pytest.raises(ValidationError):
        _blocked_result(conversion_inputs=("contract_multiplier_ref=CI-LIN#1",))


def test_schema_04_success_without_versions_or_lineage_fails() -> None:
    with pytest.raises(ValidationError):
        _success_result(contract_terms_version=None)
    with pytest.raises(ValidationError):
        _success_result(conversion_inputs=())
    with pytest.raises(ValidationError):
        _success_result(output_unit=None)


def test_schema_05_unknown_field_fails() -> None:
    with pytest.raises(ValidationError):
        ConversionResult(
            native_quantity=Decimal("1"),
            native_unit="CONTRACT",
            normalized_value=None,
            output_unit="BTC",
            quality_flags=(BLOCKED,),
            methodology_version="B5_I04B_CONVERSION_V1",
            invented_field="nope",  # extra="forbid"
        )


def test_schema_06_price_evidence_unknown_field_fails() -> None:
    with pytest.raises(ValidationError):
        ReferencePriceEvidence(
            reference_price=Decimal("25000"),
            reference_price_type=ReferencePriceType.PROVIDER_INDEX,
            reference_price_time=PRICE_AT,
            reference_price_source="exchange-a:index",
            market_available_at=AVAILABLE_AT,
            reference_price_unit="USDT",
            reference_price_base_unit="BTC",
            source_evidence_refs=PRICE_REFS,
            unexpected="x",  # extra="forbid"
        )
