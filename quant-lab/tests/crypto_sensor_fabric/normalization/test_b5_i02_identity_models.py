"""SENSOR-B5-I02 — N0 tests for the five identity models.

Bloc 5 identity records (bloc_05/01 §2) with the fail-closed laws the
checkpoint is authorized to enforce structurally: non-blank identifiers,
timezone-aware times, finite-interval ordering, exact symbol preservation,
SHA-256 metadata-hash syntax, distinct stablecoin/fiat assets, and the
INVERSE/QUANTO structural consistency checks named by the directive.

Everything here is OFFLINE: no network, no provider adapter, no filesystem.
The assets, venues and instruments in this file are OFFLINE IDENTITY FIXTURES
(directive §22), not production mapping claims.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from crypto_sensor_fabric.normalization.enums import PayoffType
from crypto_sensor_fabric.normalization.identity import (
    CanonicalAsset,
    ContractInstance,
    EconomicContract,
    Venue,
    VenueInstrument,
)

UTC = timezone.utc

SHA256 = "3f79bb7b435b05321651daefd374cdc681dc06faa65e374e38337b88ca4c6a11"
T0 = datetime(2024, 1, 1, tzinfo=UTC)
T1 = datetime(2024, 6, 1, tzinfo=UTC)
T2 = datetime(2024, 6, 2, tzinfo=UTC)


def asset(
    asset_id: str = "USDT",
    symbol: str = "USDT",
    asset_type: str = "STABLECOIN",
) -> CanonicalAsset:
    return CanonicalAsset(
        asset_id=asset_id,
        symbol_canonical=symbol,
        asset_type=asset_type,
        metadata_version="1",
    )


def venue(venue_id: str = "KRAKEN_FUTURES") -> Venue:
    return Venue(venue_id=venue_id)


def instrument(
    provider: str = "KRAKEN_FUTURES",
    venue_id: str = "KRAKEN_FUTURES",
    native_symbol: str = "PI_XBTUSD",
) -> VenueInstrument:
    return VenueInstrument(
        provider=provider,
        venue=venue_id,
        native_symbol=native_symbol,
        instrument_type="PERPETUAL_FUTURE",
        native_metadata_hash=SHA256,
        first_seen_at=T0,
        last_seen_at=T1,
    )


def economic_contract() -> EconomicContract:
    return EconomicContract(
        economic_contract_id="EC-BTCUSDT-PERP-LINEAR",
        underlying_asset_id="BTC",
        quote_asset_id="USDT",
        settlement_asset_id="USDT",
        margin_asset_id="USDT",
        instrument_type="PERPETUAL_FUTURE",
        perpetual_or_delivery="PERPETUAL",
        payoff_type=PayoffType.LINEAR,
    )


def instance(
    native_symbol: str = "PI_XBTUSD",
    provider: str = "KRAKEN_FUTURES",
    venue_id: str = "KRAKEN_FUTURES",
    payoff: PayoffType = PayoffType.LINEAR,
    inverse_flag: bool = False,
    quanto_flag: bool = False,
) -> ContractInstance:
    return ContractInstance(
        contract_instance_id=f"CI-{native_symbol}",
        provider=provider,
        venue=venue_id,
        native_symbol=native_symbol,
        economic_contract_id="EC-BTCUSDT-PERP-LINEAR",
        valid_from=T0,
        valid_to=None,
        known_from=T0,
        known_to=None,
        contract_multiplier=Decimal("1"),
        multiplier_unit="CONTRACT",
        price_unit="USDT",
        quantity_unit="BTC",
        settlement_asset_id="USDT",
        margin_asset_id=None,
        payoff_type=payoff,
        inverse_flag=inverse_flag,
        quanto_flag=quanto_flag,
        tick_size=Decimal("0.1"),
        lot_size=Decimal("0.0001"),
        expiry=None,
        contract_terms_version="1",
        source_evidence_refs=("provider-docs:kraken-futures:pi_xbtusd",),
    )


# ---------------------------------------------------------------------------
# CanonicalAsset (bloc_05/01 §2.1, directive §6)
# ---------------------------------------------------------------------------


def test_canonical_asset_constructs_minimally() -> None:
    a = asset()
    assert a.asset_id == "USDT"
    assert a.symbol_canonical == "USDT"
    assert a.chain_or_issuer_context is None
    assert a.valid_from is None
    assert a.valid_to is None
    assert a.metadata_version == "1"


def test_blank_asset_id_refused() -> None:
    with pytest.raises(ValidationError):
        asset(asset_id="")


def test_whitespace_padded_asset_id_refused() -> None:
    with pytest.raises(ValidationError):
        asset(asset_id=" USDT ")


def test_blank_symbol_canonical_refused() -> None:
    with pytest.raises(ValidationError):
        asset(symbol="")


def test_symbol_canonical_preserved_verbatim() -> None:
    a = asset(asset_id="BTC", symbol="BTC")
    assert a.symbol_canonical == "BTC"


def test_naive_valid_from_refused() -> None:
    with pytest.raises(ValidationError):
        CanonicalAsset(
            asset_id="USDT",
            symbol_canonical="USDT",
            asset_type="STABLECOIN",
            valid_from=datetime(2024, 1, 1),
            metadata_version="1",
        )


def test_aware_valid_from_normalized_to_utc() -> None:
    a = CanonicalAsset(
        asset_id="USDT",
        symbol_canonical="USDT",
        asset_type="STABLECOIN",
        valid_from=datetime(2024, 1, 1, 2, 0, tzinfo=timezone.utc),
        metadata_version="1",
    )
    assert a.valid_from == datetime(2024, 1, 1, 2, 0, tzinfo=UTC)


def test_valid_to_after_valid_from_enforced() -> None:
    with pytest.raises(ValidationError):
        CanonicalAsset(
            asset_id="USDT",
            symbol_canonical="USDT",
            asset_type="STABLECOIN",
            valid_from=T1,
            valid_to=T0,
            metadata_version="1",
        )


def test_valid_to_equal_valid_from_refused() -> None:
    with pytest.raises(ValidationError):
        CanonicalAsset(
            asset_id="USDT",
            symbol_canonical="USDT",
            asset_type="STABLECOIN",
            valid_from=T0,
            valid_to=T0,
            metadata_version="1",
        )


def test_valid_to_after_valid_from_accepted() -> None:
    a = CanonicalAsset(
        asset_id="USDT",
        symbol_canonical="USDT",
        asset_type="STABLECOIN",
        valid_from=T0,
        valid_to=T1,
        metadata_version="1",
    )
    assert a.valid_to == T1


def test_asset_type_is_opaque_token_not_closed_enum() -> None:
    """No frozen asset_type vocabulary exists (matrix row): any well-formed
    token is representable, and inventing an enum would be a directive §4
    violation."""
    for token in ("STABLECOIN", "CRYPTO", "FIAT", "COMMODITY"):
        assert asset(asset_type=token).asset_type == token


def test_metadata_version_required() -> None:
    with pytest.raises(ValidationError):
        CanonicalAsset(asset_id="USDT", symbol_canonical="USDT", asset_type="STABLECOIN")


# ---------------------------------------------------------------------------
# USD / USDT / USDC stablecoin identity law (bloc_05/01 §12, directive §7)
# ---------------------------------------------------------------------------


def test_usd_usdt_usdc_are_three_distinct_assets() -> None:
    usd = asset("USD", "USD", "FIAT")
    usdt = asset("USDT", "USDT", "STABLECOIN")
    usdc = asset("USDC", "USDC", "STABLECOIN")
    assert usd.asset_id != usdt.asset_id
    assert usdt.asset_id != usdc.asset_id
    assert usd.asset_id != usdc.asset_id
    assert usd != usdt != usdc


def test_no_usdt_to_usd_aliased_by_symbol_text() -> None:
    """Symbol text classifies nothing: 'USDT' and 'USD' differ by exact string
    comparison only, and no conversion/equality assumption exists."""
    usd = asset("USD", "USD", "FIAT")
    usdt = asset("USDT", "USDT", "STABLECOIN")
    assert usd.symbol_canonical != usdt.symbol_canonical
    assert usd != usdt


# ---------------------------------------------------------------------------
# Venue (bloc_05/01 §2.2, directive §8)
# ---------------------------------------------------------------------------


def test_venue_constructs_with_venue_id() -> None:
    v = venue()
    assert v.venue_id == "KRAKEN_FUTURES"


def test_blank_venue_id_refused() -> None:
    with pytest.raises(ValidationError):
        venue(venue_id="")


def test_padded_venue_id_refused() -> None:
    with pytest.raises(ValidationError):
        venue(venue_id="KRAKEN_FUTURES ")


def test_venues_distinct_by_identity() -> None:
    assert venue("KRAKEN_FUTURES") != venue("BINANCE_USDM")


def test_venue_is_not_frozen_enum_of_examples() -> None:
    """The plan's venue list (bloc_05/01 §2.2) is examples, not a closed enum
    (directive §8): any well-formed venue identifier is representable."""
    assert venue("SOME_FUTURE_VENUE").venue_id == "SOME_FUTURE_VENUE"


# ---------------------------------------------------------------------------
# VenueInstrument (bloc_05/01 §2.3, directive §9)
# ---------------------------------------------------------------------------


def test_venue_instrument_constructs_minimally() -> None:
    i = instrument()
    assert i.provider == "KRAKEN_FUTURES"
    assert i.venue == "KRAKEN_FUTURES"
    assert i.native_symbol == "PI_XBTUSD"
    assert i.provider_instrument_id is None
    assert i.instrument_type == "PERPETUAL_FUTURE"
    assert i.native_metadata_hash == SHA256


def test_provider_instrument_id_optional_and_preserved() -> None:
    i = instrument()
    i2 = VenueInstrument(
        provider="COINALYZE",
        venue="BINANCE_USDM",
        native_symbol="BTCUSDT",
        provider_instrument_id="BINANCE_INSTR-123",
        instrument_type="PERPETUAL_FUTURE",
        native_metadata_hash=SHA256,
        first_seen_at=T0,
        last_seen_at=T0,
    )
    assert i.provider_instrument_id is None
    assert i2.provider_instrument_id == "BINANCE_INSTR-123"
    # provider != venue: an aggregator provider may reference a venue it does
    # not operate (bloc_05/01 §13).
    assert i2.provider != i2.venue


def test_native_symbol_preserved_exactly() -> None:
    """No case folding, no separator normalization, no parsing (directive §10)."""
    for raw in ("PI_XBTUSD", "BTC-USDT-SWAP", "BTCUSDT", "btc_usdt"):
        assert instrument(native_symbol=raw).native_symbol == raw


def test_blank_native_symbol_refused() -> None:
    with pytest.raises(ValidationError):
        instrument(native_symbol="")


def test_padded_native_symbol_refused() -> None:
    with pytest.raises(ValidationError):
        instrument(native_symbol=" BTCUSDT ")


def test_blank_provider_refused() -> None:
    with pytest.raises(ValidationError):
        instrument(provider="")


def test_invalid_metadata_hash_refused() -> None:
    """Metadata hash is format-checked SHA-256 hex (bloc_05/01 §2.3)."""
    for bad_hash in ("", "short", SHA256[:-1], SHA256 + "0", SHA256.upper(), "z" * 64):
        with pytest.raises(ValidationError):
            VenueInstrument(
                provider="P",
                venue="V",
                native_symbol="SYM",
                instrument_type="PERPETUAL_FUTURE",
                native_metadata_hash=bad_hash,
                first_seen_at=T0,
                last_seen_at=T0,
            )


def test_naive_first_seen_at_refused() -> None:
    with pytest.raises(ValidationError):
        VenueInstrument(
            provider="P",
            venue="V",
            native_symbol="SYM",
            instrument_type="PERPETUAL_FUTURE",
            native_metadata_hash=SHA256,
            first_seen_at=datetime(2024, 1, 1),
            last_seen_at=T0,
        )


def test_last_seen_before_first_seen_refused() -> None:
    with pytest.raises(ValidationError):
        VenueInstrument(
            provider="P",
            venue="V",
            native_symbol="SYM",
            instrument_type="PERPETUAL_FUTURE",
            native_metadata_hash=SHA256,
            first_seen_at=T1,
            last_seen_at=T0,
        )


def test_last_seen_equal_first_seen_accepted() -> None:
    i = VenueInstrument(
        provider="P",
        venue="V",
        native_symbol="SYM",
        instrument_type="PERPETUAL_FUTURE",
        native_metadata_hash=SHA256,
        first_seen_at=T0,
        last_seen_at=T0,
    )
    assert i.last_seen_at == i.first_seen_at


# ---------------------------------------------------------------------------
# EconomicContract (bloc_05/01 §2.4, directive §11)
# ---------------------------------------------------------------------------


def test_economic_contract_constructs() -> None:
    ec = economic_contract()
    assert ec.economic_contract_id == "EC-BTCUSDT-PERP-LINEAR"
    assert ec.underlying_asset_id == "BTC"
    assert ec.quote_asset_id == "USDT"
    assert ec.settlement_asset_id == "USDT"
    assert ec.margin_asset_id == "USDT"
    assert ec.payoff_type is PayoffType.LINEAR
    assert ec.index_family is None


def test_margin_asset_optional_on_economic_contract() -> None:
    ec = EconomicContract(
        economic_contract_id="EC-X",
        underlying_asset_id="BTC",
        quote_asset_id="USD",
        settlement_asset_id="BTC",
        instrument_type="PERPETUAL_FUTURE",
        perpetual_or_delivery="PERPETUAL",
        payoff_type=PayoffType.INVERSE,
    )
    assert ec.margin_asset_id is None


def test_asset_reference_fields_stay_separate() -> None:
    """§11: underlying/quote/settlement/margin are separate fields, never a
    collapsed or derived asset (bloc_05/07 F6)."""
    ec = economic_contract()
    for distinct in (
        (ec.underlying_asset_id, ec.quote_asset_id),
        (ec.quote_asset_id, ec.settlement_asset_id),
    ):
        assert distinct[0] != distinct[1]


def test_payoff_type_unknown_representable() -> None:
    ec = EconomicContract(
        economic_contract_id="EC-U",
        underlying_asset_id="BTC",
        quote_asset_id="USDT",
        settlement_asset_id="USDT",
        instrument_type="PERPETUAL_FUTURE",
        perpetual_or_delivery="PERPETUAL",
        payoff_type=PayoffType.UNKNOWN,
    )
    assert ec.payoff_type is PayoffType.UNKNOWN


def test_blank_economic_contract_id_refused() -> None:
    with pytest.raises(ValidationError):
        EconomicContract(
            economic_contract_id="",
            underlying_asset_id="BTC",
            quote_asset_id="USDT",
            settlement_asset_id="USDT",
            instrument_type="PERPETUAL_FUTURE",
            perpetual_or_delivery="PERPETUAL",
            payoff_type=PayoffType.LINEAR,
        )


def test_payoff_type_is_the_reused_b5_i01_enum() -> None:
    ""§5: B5-I02 must not redefine PayoffType."""
    from crypto_sensor_fabric.normalization import enums as base_enums

    assert PayoffType is base_enums.PayoffType


# ---------------------------------------------------------------------------
# ContractInstance (bloc_05/01 §2.5, directive §13/§15/§16/§17)
# ---------------------------------------------------------------------------


def test_contract_instance_constructs_with_all_frozen_fields() -> None:
    ci = instance()
    assert ci.contract_instance_id == "CI-PI_XBTUSD"
    assert ci.native_symbol == "PI_XBTUSD"
    assert ci.economic_contract_id == "EC-BTCUSDT-PERP-LINEAR"
    assert ci.valid_from == T0
    assert ci.valid_to is None  # open interval: still-active instance
    assert ci.known_from == T0
    assert ci.known_to is None
    assert ci.contract_multiplier == Decimal("1")
    assert ci.tick_size == Decimal("0.1")
    assert ci.lot_size == Decimal("0.0001")
    assert ci.expiry is None
    assert ci.contract_terms_version == "1"


def test_contract_instance_has_no_default_terms() -> None:
    """Terms fields carry no defaults: a fabricated zero would be invented
    economics (directive §13: data model only)."""
    for omitted in (
        {"contract_multiplier"},
        {"tick_size"},
        {"lot_size"},
        {"multiplier_unit"},
        {"price_unit"},
        {"quantity_unit"},
        {"inverse_flag"},
        {"contract_terms_version"},
    ):
        kwargs: dict[str, object] = dict(
            contract_instance_id="CI-X",
            provider="P",
            venue="V",
            native_symbol="S",
            economic_contract_id="EC",
            valid_from=T0,
            known_from=T0,
            settlement_asset_id="USDT",
            payoff_type=PayoffType.LINEAR,
            contract_multiplier=Decimal("1"),
            multiplier_unit="CONTRACT",
            price_unit="USDT",
            quantity_unit="BTC",
            inverse_flag=False,
            quanto_flag=False,
            tick_size=Decimal("0.1"),
            lot_size=Decimal("0.0001"),
            contract_terms_version="1",
            source_evidence_refs=("ref",),
        )
        for key in omitted:
            del kwargs[key]  # type: ignore[arg-type]
        with pytest.raises(ValidationError):
            ContractInstance(**kwargs)  # type: ignore[arg-type]


def test_blank_contract_instance_id_refused() -> None:
    base = instance()
    fields = base.model_dump()
    fields["contract_instance_id"] = ""
    with pytest.raises(ValidationError):
        ContractInstance(**fields)


def test_naive_valid_from_refused() -> None:
    base = instance()
    fields = base.model_dump()
    fields["valid_from"] = datetime(2024, 1, 1)
    with pytest.raises(ValidationError):
        ContractInstance(**fields)


def test_naive_known_from_refused() -> None:
    base = instance()
    fields = base.model_dump()
    fields["known_from"] = datetime(2024, 1, 1)
    with pytest.raises(ValidationError):
        ContractInstance(**fields)


def test_finite_valid_to_before_valid_from_refused() -> None:
    base = instance()
    fields = base.model_dump()
    fields["valid_to"] = T0 - timedelta(days=1)
    with pytest.raises(ValidationError):
        ContractInstance(**fields)


def test_finite_known_to_before_known_from_refused() -> None:
    base = instance()
    fields = base.model_dump()
    fields["known_to"] = T0 - timedelta(days=1)
    with pytest.raises(ValidationError):
        ContractInstance(**fields)


def test_open_intervals_representable() -> None:
    """§15 'where finite': an active instance has no known end; None is the
    honest open-interval representation, never a fabricated far-future date."""
    ci = instance()
    assert ci.valid_to is None and ci.known_to is None


def test_empty_source_evidence_refs_refused() -> None:
    base = instance()
    fields = base.model_dump()
    fields["source_evidence_refs"] = ()
    with pytest.raises(ValidationError):
        ContractInstance(**fields)


def test_duplicate_source_evidence_refs_refused() -> None:
    base = instance()
    fields = base.model_dump()
    fields["source_evidence_refs"] = ("ref-a", "ref-a")
    with pytest.raises(ValidationError):
        ContractInstance(**fields)


def test_path_shaped_source_evidence_refused() -> None:
    ""§17: durable identifiers only - no filesystem paths, no local filenames."""
    base = instance()
    for bad_ref in (
        "/abs/path/evidence.json",
        "C:\\data\\evidence.json",
        "..\\secrets",
        "relative/file.json",
    ):
        fields = base.model_dump()
        fields["source_evidence_refs"] = (bad_ref,)
        with pytest.raises(ValidationError):
            ContractInstance(**fields)


def test_inverse_payoff_claiming_not_inverse_refused() -> None:
    ""§16: structural contradiction the frozen model explicitly supports."""
    with pytest.raises(ValidationError):
        instance(payoff=PayoffType.INVERSE, inverse_flag=False)


def test_quanto_payoff_claiming_not_quanto_refused() -> None:
    with pytest.raises(ValidationError):
        instance(payoff=PayoffType.QUANTO, quanto_flag=False)


def test_inverse_with_true_flag_accepted() -> None:
    ci = instance(payoff=PayoffType.INVERSE, inverse_flag=True)
    assert ci.inverse_flag is True


def test_expiry_representable() -> None:
    ci = instance()
    fields = ci.model_dump()
    fields["expiry"] = T1
    fields["contract_instance_id"] = "CI-DATED"
    dated = ContractInstance(**fields)
    assert dated.expiry == T1


def test_instance_roundtrip_preserves_native_symbol_exactly() -> None:
    ci = instance(native_symbol="BTC-USDT-SWAP")
    assert ci.native_symbol == "BTC-USDT-SWAP"


# ---------------------------------------------------------------------------
# Immutability + structural firewalls (directive §14/§20)
# ---------------------------------------------------------------------------


def test_identity_records_are_immutable() -> None:
    """Registry truth is immutable: mutation must produce a new versioned
    record, never silently rewrite (directive §20)."""
    a = asset()
    with pytest.raises(ValidationError):
        a.asset_id = "USD"  # type: ignore[misc]


def test_no_fiat_classification_field_exists() -> None:
    """No fiat/stablecoin classification may be derived from symbol text
    (directive §7): the model carries no such field at all."""
    for absent in ("is_fiat", "is_stablecoin", "usd_equivalent", "fiat_equivalent"):
        assert not hasattr(asset(), absent)


def test_no_conversion_behavior_exists() -> None:
    """Directive §13/§14: I02 stores terms; it computes nothing."""
    ci = instance()
    for absent in ("base_quantity", "quote_notional", "usd_value", "linear_exposure"):
        assert not hasattr(ci, absent)
        assert not callable(getattr(type(ci), absent, None))
