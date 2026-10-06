"""SENSOR-B5-I02 — N0 tests for the versioned identity registry.

Registry laws (directive §19/§20/§31/§32/§33, bloc_05/01 §15/§17): explicit
version, deterministic serialization, stable canonical ordering, duplicate ID
refusal, referential integrity across assets/venues/economic contracts,
no-overlapping-active-terms for the same provider instrument, round-trip
equality, no silent overwrite, no wall-clock defaults.

OFFLINE. All entries are synthetic identity fixtures (directive §22).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from crypto_sensor_fabric.normalization.enums import PayoffType
from crypto_sensor_fabric.normalization.identity import (
    CanonicalAsset,
    ContractInstance,
    EconomicContract,
    IdentityRegistrySnapshot,
    Venue,
    VenueInstrument,
    parse_identity_registry_yaml,
    serialize_identity_registry_yaml,
    validate_registry_succession,
)

UTC = timezone.utc

SHA256 = "3f79bb7b435b05321651daefd374cdc681dc06faa65e374e38337b88ca4c6a11"
T0 = datetime(2024, 1, 1, tzinfo=UTC)
T1 = datetime(2024, 6, 1, tzinfo=UTC)
T2 = datetime(2024, 9, 1, tzinfo=UTC)


def asset(asset_id: str = "USDT") -> CanonicalAsset:
    return CanonicalAsset(
        asset_id=asset_id,
        symbol_canonical=asset_id,
        asset_type="STABLECOIN",
        metadata_version="1",
    )


def assets(*ids: str) -> tuple[CanonicalAsset, ...]:
    return tuple(asset(a) for a in ids)


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


def contract(contract_id: str = "EC-BTCUSDT-PERP") -> EconomicContract:
    return EconomicContract(
        economic_contract_id=contract_id,
        underlying_asset_id="BTC",
        quote_asset_id="USDT",
        settlement_asset_id="USDT",
        instrument_type="PERPETUAL_FUTURE",
        perpetual_or_delivery="PERPETUAL",
        payoff_type=PayoffType.LINEAR,
    )


def inst(
    instance_id: str = "CI-1",
    native_symbol: str = "PI_XBTUSD",
    provider: str = "KRAKEN_FUTURES",
    venue_id: str = "KRAKEN_FUTURES",
    valid_from: datetime = T0,
    valid_to: datetime | None = None,
    economic_contract_id: str = "EC-BTCUSDT-PERP",
) -> ContractInstance:
    return ContractInstance(
        contract_instance_id=instance_id,
        provider=provider,
        venue=venue_id,
        native_symbol=native_symbol,
        economic_contract_id=economic_contract_id,
        valid_from=valid_from,
        valid_to=valid_to,
        known_from=T0,
        known_to=None,
        contract_multiplier=1,
        multiplier_unit="CONTRACT",
        price_unit="USDT",
        quantity_unit="BTC",
        settlement_asset_id="USDT",
        margin_asset_id=None,
        payoff_type=PayoffType.LINEAR,
        inverse_flag=False,
        quanto_flag=False,
        tick_size=0.1,
        lot_size=0.0001,
        expiry=None,
        contract_terms_version="1",
        source_evidence_refs=("provider-docs:kraken-futures",),
    )


def full_snapshot(version: str = "1") -> IdentityRegistrySnapshot:
    return IdentityRegistrySnapshot(
        registry_version=version,
        assets=assets("BTC", "USD", "USDT", "USDC"),
        venues=(venue("BINANCE_USDM"), venue("KRAKEN_FUTURES")),
        venue_instruments=(
            instrument(),
            instrument(
                provider="COINALYZE", venue_id="BINANCE_USDM", native_symbol="BTCUSDT"
            ),
        ),
        economic_contracts=(contract(),),
        contract_instances=(inst(),),
    )


def empty_snapshot(version: str = "1") -> IdentityRegistrySnapshot:
    return IdentityRegistrySnapshot(registry_version=version)


# ---------------------------------------------------------------------------
# Duplicate identity refusal (directive §19/§30, RED case §35.1)
# ---------------------------------------------------------------------------


def test_duplicate_asset_id_refused() -> None:
    with pytest.raises(ValidationError):
        IdentityRegistrySnapshot(
            registry_version="1", assets=(asset("BTC"), asset("BTC"))
        )


def test_duplicate_venue_id_refused() -> None:
    with pytest.raises(ValidationError):
        IdentityRegistrySnapshot(
            registry_version="1", venues=(venue("V"), venue("V"))
        )


def test_duplicate_economic_contract_id_refused() -> None:
    with pytest.raises(ValidationError):
        IdentityRegistrySnapshot(
            registry_version="1",
            assets=assets("BTC", "USDT"),
            economic_contracts=(contract(), contract()),
        )


def test_duplicate_contract_instance_id_refused() -> None:
    with pytest.raises(ValidationError):
        IdentityRegistrySnapshot(
            registry_version="1",
            assets=assets("BTC", "USDT"),
            economic_contracts=(contract(),),
            contract_instances=(inst(), inst(instance_id="CI-1")),
        )


# ---------------------------------------------------------------------------
# Referential integrity (directive §31/§32/§33, RED cases §35.2/§35.3)
# ---------------------------------------------------------------------------


def test_dangling_economic_contract_underlying_refused() -> None:
    bad = EconomicContract(
        economic_contract_id="EC-X",
        underlying_asset_id="SOL",
        quote_asset_id="USDT",
        settlement_asset_id="USDT",
        instrument_type="PERPETUAL_FUTURE",
        perpetual_or_delivery="PERPETUAL",
        payoff_type=PayoffType.LINEAR,
    )
    with pytest.raises(ValidationError):
        IdentityRegistrySnapshot(
            registry_version="1", assets=assets("BTC", "USDT"), economic_contracts=(bad,)
        )


def test_dangling_economic_contract_quote_refused() -> None:
    bad = EconomicContract(
        economic_contract_id="EC-X",
        underlying_asset_id="BTC",
        quote_asset_id="USDC",
        settlement_asset_id="USDT",
        instrument_type="PERPETUAL_FUTURE",
        perpetual_or_delivery="PERPETUAL",
        payoff_type=PayoffType.LINEAR,
    )
    with pytest.raises(ValidationError):
        IdentityRegistrySnapshot(
            registry_version="1", assets=assets("BTC", "USDT"), economic_contracts=(bad,)
        )


def test_dangling_economic_contract_settlement_refused() -> None:
    bad = EconomicContract(
        economic_contract_id="EC-X",
        underlying_asset_id="BTC",
        quote_asset_id="USDT",
        settlement_asset_id="SOL",
        instrument_type="PERPETUAL_FUTURE",
        perpetual_or_delivery="PERPETUAL",
        payoff_type=PayoffType.LINEAR,
    )
    with pytest.raises(ValidationError):
        IdentityRegistrySnapshot(
            registry_version="1", assets=assets("BTC", "USDT"), economic_contracts=(bad,)
        )


def test_dangling_economic_contract_margin_refused() -> None:
    bad = EconomicContract(
        economic_contract_id="EC-X",
        underlying_asset_id="BTC",
        quote_asset_id="USDT",
        settlement_asset_id="USDT",
        margin_asset_id="SOL",
        instrument_type="PERPETUAL_FUTURE",
        perpetual_or_delivery="PERPETUAL",
        payoff_type=PayoffType.LINEAR,
    )
    with pytest.raises(ValidationError):
        IdentityRegistrySnapshot(
            registry_version="1", assets=assets("BTC", "USDT"), economic_contracts=(bad,)
        )


def test_dangling_contract_instance_economic_contract_refused() -> None:
    with pytest.raises(ValidationError):
        IdentityRegistrySnapshot(
            registry_version="1",
            assets=assets("BTC", "USDT"),
            contract_instances=(inst(economic_contract_id="EC-MISSING"),),
        )


def test_dangling_contract_instance_venue_refused() -> None:
    with pytest.raises(ValidationError):
        IdentityRegistrySnapshot(
            registry_version="1",
            assets=assets("BTC", "USDT"),
            economic_contracts=(contract(),),
            contract_instances=(inst(venue_id="UNKNOWN_VENUE"),),
        )


def test_dangling_contract_instance_settlement_asset_refused() -> None:
    base = inst()
    fields = base.model_dump()
    fields["settlement_asset_id"] = "SOL"
    bad = ContractInstance(**fields)
    with pytest.raises(ValidationError):
        IdentityRegistrySnapshot(
            registry_version="1",
            assets=assets("BTC", "USDT"),
            economic_contracts=(contract(),),
            contract_instances=(bad,),
        )


def test_dangling_contract_instance_margin_asset_refused() -> None:
    base = inst()
    fields = base.model_dump()
    fields["margin_asset_id"] = "SOL"
    bad = ContractInstance(**fields)
    with pytest.raises(ValidationError):
        IdentityRegistrySnapshot(
            registry_version="1",
            assets=assets("BTC", "USDT"),
            economic_contracts=(contract(),),
            contract_instances=(bad,),
        )


def test_dangling_venue_instrument_venue_refused() -> None:
    with pytest.raises(ValidationError):
        IdentityRegistrySnapshot(
            registry_version="1",
            assets=assets("BTC", "USDT"),
            venue_instruments=(instrument(venue_id="UNKNOWN_VENUE"),),
        )


def test_provider_does_not_have_to_be_a_venue() -> None:
    ""§33: provider is a separate provider identifier, never required to be a
    registered venue."""
    snap = IdentityRegistrySnapshot(
        registry_version="1",
        assets=assets("BTC", "USDT"),
        venues=(venue("BINANCE_USDM"),),
        venue_instruments=(
            instrument(provider="COINALYZE", venue_id="BINANCE_USDM"),
        ),
    )
    assert snap.venue_instruments[0].provider == "COINALYZE"


# ---------------------------------------------------------------------------
# No overlapping active terms (bloc_05/01 §17 invariant 3)
# ---------------------------------------------------------------------------


def test_overlapping_valid_intervals_for_same_instrument_refused() -> None:
    with pytest.raises(ValidationError):
        IdentityRegistrySnapshot(
            registry_version="1",
            assets=assets("BTC", "USDT"),
            economic_contracts=(contract(),),
            contract_instances=(
                inst(instance_id="CI-A", valid_from=T0, valid_to=T2),
                inst(instance_id="CI-B", valid_from=T1, valid_to=None),
            ),
        )


def test_adjacent_intervals_accepted() -> None:
    snap = IdentityRegistrySnapshot(
        registry_version="1",
        assets=assets("BTC", "USDT"),
        economic_contracts=(contract(),),
        contract_instances=(
            inst(instance_id="CI-A", valid_from=T0, valid_to=T1),
            inst(instance_id="CI-B", valid_from=T1, valid_to=None),
        ),
    )
    assert len(snap.contract_instances) == 2


def test_overlapping_intervals_for_distinct_symbols_accepted() -> None:
    snap = IdentityRegistrySnapshot(
        registry_version="1",
        assets=assets("BTC", "USDT"),
        economic_contracts=(contract(),),
        contract_instances=(
            inst(instance_id="CI-A", native_symbol="SYM-1", valid_from=T0),
            inst(instance_id="CI-B", native_symbol="SYM-2", valid_from=T0),
        ),
    )
    assert len(snap.contract_instances) == 2


# ---------------------------------------------------------------------------
# Determinism, ordering, round trip (directive §19/§23/§30)
# ---------------------------------------------------------------------------


def test_empty_snapshot_valid() -> None:
    snap = empty_snapshot()
    assert snap.registry_version == "1"
    assert snap.assets == ()


def test_registry_version_required_and_nonblank() -> None:
    with pytest.raises(ValidationError):
        IdentityRegistrySnapshot(registry_version="")


def test_canonical_ordering_is_enforced() -> None:
    ""Input order is irrelevant: the snapshot stores a stable canonical order."""
    snap = IdentityRegistrySnapshot(
        registry_version="1",
        assets=(asset("USDT"), asset("BTC"), asset("USDC")),
    )
    assert [a.asset_id for a in snap.assets] == ["BTC", "USDC", "USDT"]


def test_serialization_is_byte_deterministic() -> None:
    snap = full_snapshot()
    assert serialize_identity_registry_yaml(snap) == serialize_identity_registry_yaml(snap)


def test_yaml_round_trip_equality() -> None:
    snap = full_snapshot()
    restored = parse_identity_registry_yaml(serialize_identity_registry_yaml(snap))
    assert restored == snap


def test_decimal_precision_survives_round_trip() -> None:
    from decimal import Decimal

    base = inst().model_dump()
    base["tick_size"] = Decimal("0.00000123")
    base["lot_size"] = Decimal("0.00000001")
    precise = ContractInstance(**base)
    snap = IdentityRegistrySnapshot(
        registry_version="1",
        assets=assets("BTC", "USDT"),
        economic_contracts=(contract(),),
        contract_instances=(precise,),
    )
    restored = parse_identity_registry_yaml(serialize_identity_registry_yaml(snap))
    assert restored == snap
    assert restored.contract_instances[0].tick_size == Decimal("0.00000123")


# ---------------------------------------------------------------------------
# Versioning / immutability (directive §20, RED case §35.6)
# ---------------------------------------------------------------------------


def test_succession_refuses_same_version_with_conflicting_content() -> None:
    v1 = full_snapshot("1")
    conflicting = IdentityRegistrySnapshot(
        registry_version="1",
        assets=(asset("BTC"),),
    )
    with pytest.raises(ValueError, match="same registry version"):
        validate_registry_succession(v1, conflicting)


def test_succession_accepts_new_version() -> None:
    v1 = full_snapshot("1")
    v2 = IdentityRegistrySnapshot(
        registry_version="2",
        assets=(asset("BTC"),),
    )
    validate_registry_succession(v1, v2)


def test_succession_accepts_identical_republish() -> None:
    v1 = full_snapshot("1")
    again = full_snapshot("1")
    validate_registry_succession(v1, again)


def test_registry_snapshot_is_immutable() -> None:
    snap = full_snapshot()
    with pytest.raises(ValidationError):
        snap.registry_version = "999"  # type: ignore[misc]


def test_v1_remains_loadable_after_v2_exists() -> None:
    v1 = full_snapshot("1")
    v1_text = serialize_identity_registry_yaml(v1)
    v2 = IdentityRegistrySnapshot(
        registry_version="2",
        assets=assets("BTC", "USD", "USDT", "USDC", "SOL"),
        venues=(venue("BINANCE_USDM"), venue("KRAKEN_FUTURES")),
        economic_contracts=(contract(),),
        contract_instances=(inst(),),
    )
    v2_text = serialize_identity_registry_yaml(v2)
    restored_v1 = parse_identity_registry_yaml(v1_text)
    restored_v2 = parse_identity_registry_yaml(v2_text)
    assert restored_v1 == v1
    assert restored_v2 == v2
    # v1 content was not silently rewritten by v2's existence.
    assert restored_v1.registry_version == "1"
    assert "SOL" not in serialize_identity_registry_yaml(restored_v1)


def test_no_wall_clock_defaults_anywhere() -> None:
    ""Constructing registries never mints timestamps: every datetime on every
    record was explicitly supplied."""
    snap = full_snapshot()
    for i in snap.venue_instruments:
        assert i.first_seen_at in (T0, T1)
    for ci in snap.contract_instances:
        assert ci.valid_from in (T0, T1)
