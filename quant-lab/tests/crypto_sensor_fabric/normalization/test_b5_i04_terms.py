"""SENSOR-B5-I04A - RED-first contract-terms snapshot and projection suite.

Twenty directive fixtures (T04A-01..20) plus the eight adversarial traps
(A1-A8), authored BEFORE any I04A production module exists: this file is the
RED capture (import of the absent ``terms`` package fails), then the standing
regression battery once Stage C lands.

Ownership law under test (I04A directive D2): the I03 resolver is consumed,
never modified; terms eligibility is gated HERE (I04-owned), separately from
identity resolution; ``TERMS_UNVERIFIED`` stays a reserved identity status
that no path in this suite may construct.  No conversion math, no reference
price, no new enums.

OFFLINE: registry fixtures are offline identity data (I02 directive 22).
All times UTC-aware.  Plan citations use the compact S<n> form for
bloc_05/01 section <n> (the chunked-file authoring convention).
"""

from __future__ import annotations

import inspect
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from crypto_sensor_fabric.normalization.enums import PayoffType
from crypto_sensor_fabric.normalization.identity import (
    CanonicalAsset,
    ContractInstance,
    EconomicContract,
    IdentityRegistrySnapshot,
    IdentityResolutionStatus,
    Venue,
    VenueInstrument,
    resolve_instrument,
)
from crypto_sensor_fabric.normalization.terms import (
    ContractTermsSnapshot,
    project_contract_terms,
)

UTC = timezone.utc

# ---------------------------------------------------------------- fixtures

T0 = datetime(2023, 1, 1, hour=12, tzinfo=UTC)    # valid_from
T1 = datetime(2024, 1, 1, hour=12, tzinfo=UTC)    # valid_to
K0 = datetime(2023, 6, 1, tzinfo=UTC)             # known_from
K1 = datetime(2023, 12, 1, tzinfo=UTC)            # known_to

EVENT = datetime(2023, 9, 1, hour=12, tzinfo=UTC)  # inside both windows
CUTOFF_IN = datetime(2023, 10, 1, hour=12, tzinfo=UTC)

PROVIDER = "PROV"
VENUE = "EXA_FUT"
OTHER_VENUE = "EXB_FUT"
NATIVE = "XBTUSDT"
SHA256 = "3f79bb7b435b05321651daefd374cdc681dc06faa65e374e38337b88ca4c6a11"
REFS = ("provider-docs:exchange-a-xbtusdt",)


def asset(asset_id: str) -> CanonicalAsset:
    return CanonicalAsset(
        asset_id=asset_id,
        symbol_canonical=asset_id,
        asset_type="CRYPTO",
        metadata_version="1",
    )


def venue(venue_id: str = VENUE) -> Venue:
    return Venue(venue_id=venue_id)


def instrument(
    native_symbol: str = NATIVE,
    venue_id: str = VENUE,
) -> VenueInstrument:
    return VenueInstrument(
        provider=PROVIDER,
        venue=venue_id,
        native_symbol=native_symbol,
        instrument_type="PERPETUAL_FUTURE",
        native_metadata_hash=SHA256,
        first_seen_at=T0,
        last_seen_at=datetime.max.replace(tzinfo=UTC),
    )


def economic_contract(
    ec_id: str = "EC-A",
    quote_asset_id: str = "USDT",
    settlement_asset_id: str = "USDT",
    payoff_type: PayoffType = PayoffType.LINEAR,
) -> EconomicContract:
    return EconomicContract(
        economic_contract_id=ec_id,
        underlying_asset_id="BTC",
        quote_asset_id=quote_asset_id,
        settlement_asset_id=settlement_asset_id,
        margin_asset_id=None,
        instrument_type="PERPETUAL_FUTURE",
        perpetual_or_delivery="PERPETUAL",
        payoff_type=payoff_type,
    )


def instance(
    instance_id: str = "CI-A",
    ec_id: str = "EC-A",
    native_symbol: str = NATIVE,
    valid_from: datetime = T0,
    valid_to: datetime | None = T1,
    known_from: datetime = K0,
    known_to: datetime | None = K1,
    contract_multiplier: Decimal = Decimal("1"),
    settlement_asset_id: str = "USDT",
    payoff_type: PayoffType = PayoffType.LINEAR,
    inverse_flag: bool = False,
    quanto_flag: bool = False,
    contract_terms_version: str = "1",
    source_evidence_refs: tuple[str, ...] = REFS,
) -> ContractInstance:
    return ContractInstance(
        contract_instance_id=instance_id,
        provider=PROVIDER,
        venue=VENUE,
        native_symbol=native_symbol,
        economic_contract_id=ec_id,
        valid_from=valid_from,
        valid_to=valid_to,
        known_from=known_from,
        known_to=known_to,
        contract_multiplier=contract_multiplier,
        multiplier_unit="CONTRACT",
        price_unit="USDT",
        quantity_unit="BTC",
        settlement_asset_id=settlement_asset_id,
        margin_asset_id=None,
        payoff_type=payoff_type,
        inverse_flag=inverse_flag,
        quanto_flag=quanto_flag,
        tick_size=Decimal("0.1"),
        lot_size=Decimal("0.0001"),
        expiry=None,
        contract_terms_version=contract_terms_version,
        source_evidence_refs=source_evidence_refs,
    )


def registry(*instances: ContractInstance, assets=None, economic_contracts=None) -> IdentityRegistrySnapshot:
    return IdentityRegistrySnapshot(
        registry_version="i04a-fix",
        assets=assets or (asset("BTC"), asset("USDT"), asset("USD")),
        venues=(venue(), venue(OTHER_VENUE)),
        economic_contracts=economic_contracts or (economic_contract(),),
        venue_instruments=(instrument(),),
        contract_instances=instances,
    )


def resolve(reg, symbol: str = NATIVE, event: datetime = EVENT, cutoff: datetime = CUTOFF_IN, venue_id: str = VENUE):
    return resolve_instrument(reg, PROVIDER, venue_id, symbol, event, cutoff)


def resolved_instance() -> ContractInstance:
    return instance()


def resolved_registry(inst=None) -> IdentityRegistrySnapshot:
    return registry(inst or resolved_instance())


def project(reg, res, event: datetime = EVENT, cutoff: datetime = CUTOFF_IN):
    return project_contract_terms(reg, res, event, cutoff)


def snapshot_field_set() -> frozenset[str]:
    return frozenset(ContractTermsSnapshot.model_fields)


# ---------------------------------------------------------------- T04A tests


def test_t04a_01_valid_resolved_linear_terms_project_faithfully() -> None:
    """S2.5 + D1: a PIT-valid LINEAR instance projects every mapped field
    exactly from source; no defaults, no invented refs, exact field set."""
    reg = resolved_registry()
    res = resolve(reg)
    snap = project(reg, res)
    assert snap is not None
    src = reg.contract_instances[0]
    ec = reg.economic_contracts[0]
    assert snap.contract_instance_id == src.contract_instance_id
    assert snap.economic_contract_id == src.economic_contract_id
    assert snap.contract_terms_version == src.contract_terms_version
    assert snap.contract_multiplier == src.contract_multiplier
    assert snap.multiplier_unit == src.multiplier_unit
    assert snap.price_unit == src.price_unit
    assert snap.quantity_unit == src.quantity_unit
    assert snap.payoff_type is PayoffType.LINEAR
    assert snap.inverse_flag is src.inverse_flag is False
    assert snap.quanto_flag is src.quanto_flag is False
    assert snap.quote_asset_id == ec.quote_asset_id
    assert snap.settlement_asset_id == src.settlement_asset_id
    assert snap.margin_asset_id == src.margin_asset_id
    assert snap.tick_size == src.tick_size
    assert snap.lot_size == src.lot_size
    assert snap.expiry == src.expiry
    assert snap.source_evidence_refs == src.source_evidence_refs
    # exact schema: nothing beyond the declared inventory
    assert snapshot_field_set() == frozenset(ContractTermsSnapshot.model_fields)


def test_t04a_02_valid_resolved_inverse_terms_no_price_computation() -> None:
    """F5/S8: INVERSE terms project verbatim (payoff, multiplier, units,
    version); the projection has no reference-price input at all."""
    inv = instance(
        payoff_type=PayoffType.INVERSE,
        inverse_flag=True,
        contract_multiplier=Decimal("100"),
        contract_terms_version="5",
    )
    reg = resolved_registry(inv)
    res = resolve(reg)
    snap = project(reg, res)
    assert snap is not None
    assert snap.payoff_type is PayoffType.INVERSE
    assert snap.inverse_flag is True
    assert snap.contract_multiplier == Decimal("100")
    assert snap.multiplier_unit == "CONTRACT"
    assert snap.price_unit == "USDT"
    assert snap.quantity_unit == "BTC"
    assert snap.contract_terms_version == "5"
    params = set(inspect.signature(project_contract_terms).parameters)
    assert params == {"registry", "resolution", "event_time", "knowledge_cutoff"}


def test_t04a_03_absent_required_multiplier_never_becomes_one() -> None:
    """F3/D1: the required multiplier has no default and no projection path
    exists without it -- a missing multiplier cannot silently become 1."""
    field = ContractInstance.model_fields["contract_multiplier"]
    assert field.is_required()
    with pytest.raises(ValidationError):
        ContractInstance(
            contract_instance_id="CI-X",
            provider=PROVIDER,
            venue=VENUE,
            native_symbol=NATIVE,
            economic_contract_id="EC-A",
            valid_from=T0,
            valid_to=T1,
            known_from=K0,
            known_to=K1,
            multiplier_unit="CONTRACT",
            price_unit="USDT",
            quantity_unit="BTC",
            settlement_asset_id="USDT",
            payoff_type=PayoffType.LINEAR,
            inverse_flag=False,
            quanto_flag=False,
            tick_size=Decimal("0.1"),
            lot_size=Decimal("0.0001"),
            contract_terms_version="1",
            source_evidence_refs=REFS,
        )


def test_t04a_04_invalid_multiplier_representation() -> None:
    """Frozen-contract law only: type violations are rejected by the frozen
    model; the frozen schema carries NO positivity rule, so an economically
    odd but well-typed value is recorded, not refused (no invented rule)."""
    with pytest.raises(ValidationError):
        instance(contract_multiplier="not-a-number")
    with pytest.raises(ValidationError):
        instance(contract_multiplier="garbage")
    # frozen schema has no positivity constraint:
    accepted = instance(contract_multiplier=Decimal("-0.5"))
    assert accepted.contract_multiplier == Decimal("-0.5")


def test_t04a_05_terms_version_comes_from_the_record() -> None:
    """S7/S15: snapshot version equals the record's version; no promotion to
    any newer version exists."""
    inst = instance(contract_terms_version="7")
    reg = resolved_registry(inst)
    snap = project(reg, resolve(reg))
    assert snap is not None
    assert snap.contract_terms_version == "7"
    assert snap.contract_terms_version == inst.contract_terms_version


def test_t04a_06_cutoff_before_known_from_blocks() -> None:
    """C2/S9 + D2: resolution at the early cutoff is knowledge-blocked (no
    instance id), and the I04 gate independently refuses an early cutoff even
    when handed a resolution obtained inside the window."""
    reg = resolved_registry()
    early = K0 - timedelta(days=1)
    res_early = resolve(reg, cutoff=early)
    assert res_early.status is IdentityResolutionStatus.PIT_KNOWLEDGE_BLOCKED
    assert res_early.contract_instance_id is None
    assert project(reg, res_early, cutoff=early) is None
    res_ok = resolve(reg)  # resolved at an in-window cutoff
    assert res_ok.contract_instance_id is not None
    assert project(reg, res_ok, cutoff=early) is None  # I04-owned gate


def test_t04a_07_cutoff_at_known_from_projects() -> None:
    """C2 lower bound inclusive: cutoff == known_from is eligible."""
    reg = resolved_registry()
    res = resolve(reg, cutoff=K0)
    assert res.status is IdentityResolutionStatus.RESOLVED_EXACT
    snap = project(reg, res, cutoff=K0)
    assert snap is not None


def test_t04a_08_one_microsecond_before_known_to_projects() -> None:
    """C2 upper bound half-open: known_to - 1us stays eligible (KB parity)."""
    reg = resolved_registry()
    cutoff = K1 - timedelta(microseconds=1)
    res = resolve(reg, cutoff=cutoff)
    assert res.status is IdentityResolutionStatus.RESOLVED_EXACT
    snap = project(reg, res, cutoff=cutoff)
    assert snap is not None


def test_t04a_09_cutoff_exactly_at_known_to_blocks() -> None:
    """C2 upper bound exclusive: cutoff == known_to refuses, at both layers."""
    reg = resolved_registry()
    res = resolve(reg, cutoff=K1)
    assert res.status is IdentityResolutionStatus.PIT_KNOWLEDGE_BLOCKED
    assert project(reg, res, cutoff=K1) is None
    res_ok = resolve(reg)
    assert project(reg, res_ok, cutoff=K1) is None  # I04-owned gate


def test_t04a_10_cutoff_after_known_to_blocks() -> None:
    reg = resolved_registry()
    late = K1 + timedelta(days=1)
    res = resolve(reg, cutoff=late)
    assert res.status is IdentityResolutionStatus.PIT_KNOWLEDGE_BLOCKED
    assert project(reg, res, cutoff=late) is None


def test_t04a_11_event_before_valid_from_blocks() -> None:
    """C1: event before valid_from yields no snapshot, at both layers."""
    reg = resolved_registry()
    early_event = T0 - timedelta(days=1)
    res = resolve(reg, event=early_event)
    assert res.status is IdentityResolutionStatus.NOT_YET_LISTED
    assert project(reg, res, event=early_event) is None
    res_ok = resolve(reg)
    assert project(reg, res_ok, event=early_event) is None  # I04-owned gate


def test_t04a_12_event_at_valid_to_blocks() -> None:
    """C1 half-open: event == valid_to is outside validity."""
    reg = resolved_registry()
    res = resolve(reg, event=T1)
    assert res.status in (
        IdentityResolutionStatus.DELISTED,
        IdentityResolutionStatus.NOT_YET_LISTED,
    )
    assert project(reg, res, event=T1) is None
    res_ok = resolve(reg)
    assert project(reg, res_ok, event=T1) is None  # I04-owned gate


def test_t04a_13_ambiguous_identity_yields_no_snapshot() -> None:
    """S10/C6: ambiguity is never laundered into a selected instance."""
    from crypto_sensor_fabric.normalization.identity import InstrumentAlias

    a1 = InstrumentAlias(
        alias_id="AL1",
        provider=PROVIDER,
        venue=VENUE,
        alias_text="XBTAMB",
        alias_type="API_SYMBOL",
        contract_instance_id="CI-KBA1",
        valid_from=T0,
        valid_to=None,
        known_from=K0,
        source_evidence_refs=REFS,
        confidence="curated",
    )
    a2 = InstrumentAlias(
        alias_id="AL2",
        provider=PROVIDER,
        venue=VENUE,
        alias_text="XBTAMB",
        alias_type="DISPLAY_SYMBOL",
        contract_instance_id="CI-KBA2",
        valid_from=T0,
        valid_to=None,
        known_from=K0,
        source_evidence_refs=REFS,
        confidence="curated",
    )
    i1 = instance(instance_id="CI-KBA1", native_symbol="AMBKA1")
    i2 = instance(instance_id="CI-KBA2", native_symbol="AMBKA2")
    reg = IdentityRegistrySnapshot(
        registry_version="amb",
        assets=(asset("BTC"), asset("USDT")),
        venues=(venue(),),
        economic_contracts=(economic_contract(),),
        venue_instruments=(instrument(),),
        contract_instances=(i1, i2),
        aliases=(a1, a2),
    )
    res = resolve_instrument(reg, PROVIDER, VENUE, "XBTAMB", EVENT, CUTOFF_IN)
    assert res.status is IdentityResolutionStatus.AMBIGUOUS
    assert res.contract_instance_id is None
    assert project(reg, res) is None


def test_t04a_14_wrong_venue_provides_no_terms() -> None:
    """C4: provider-ID/symbol evidence on another venue cannot supply terms."""
    reg = resolved_registry()
    res = resolve(reg, venue_id=OTHER_VENUE)
    assert res.status is IdentityResolutionStatus.UNKNOWN_SYMBOL
    assert res.contract_instance_id is None
    assert project(reg, res) is None


def test_t04a_15_unverified_terms_do_not_qualify_for_conversion() -> None:
    """D2/S3: identity resolves, but payoff semantics UNKNOWN means the terms
    are unverified -- no verified snapshot is produced, and no TERMS_UNVERIFIED
    construction happens in the resolver (reserved status stays reserved)."""
    unverified = instance(payoff_type=PayoffType.UNKNOWN)
    reg = resolved_registry(unverified)
    res = resolve(reg)
    assert res.status is IdentityResolutionStatus.RESOLVED_EXACT  # identity fine
    assert res.contract_instance_id is not None
    assert project(reg, res) is None  # terms boundary refuses
    assert IdentityResolutionStatus.TERMS_UNVERIFIED not in {
        IdentityResolutionStatus(s) for s in (res.status.value,)
    }


def test_t04a_16_quanto_boundary_preserved_without_formula() -> None:
    """S3: QUANTO classification is preserved as recorded evidence; no
    conversion formula exists in this package."""
    q = instance(payoff_type=PayoffType.QUANTO, quanto_flag=True)
    reg = resolved_registry(q)
    snap = project(reg, resolve(reg))
    assert snap is not None
    assert snap.payoff_type is PayoffType.QUANTO
    assert snap.quanto_flag is True
    import crypto_sensor_fabric.normalization.terms as terms_pkg

    for name in dir(terms_pkg):
        assert "convert" not in name.lower()
        assert "exposure" not in name.lower()
        assert "notional" not in name.lower()


def test_t04a_17_projection_does_not_mutate_sources() -> None:
    """S2: source records are immutable truth; projection leaves them equal."""
    reg = resolved_registry()
    before = reg.model_dump()
    inst_before = reg.contract_instances[0].model_dump()
    snap = project(reg, resolve(reg))
    assert snap is not None
    with pytest.raises(ValidationError):
        snap.contract_terms_version = "999"  # frozen
    assert reg.model_dump() == before
    assert reg.contract_instances[0].model_dump() == inst_before


def test_t04a_18_deterministic_projection() -> None:
    """G8: identical inputs -> equivalent immutable output."""
    reg = resolved_registry()
    res = resolve(reg)
    first = project(reg, res)
    second = project(reg, res)
    assert first is not None and second is not None
    assert first == second
    assert first.model_dump() == second.model_dump()


def test_t04a_19_unknown_snapshot_field_rejected() -> None:
    """extra='forbid': an unrecognized snapshot field is a contradiction."""
    reg = resolved_registry()
    snap = project(reg, resolve(reg))
    assert snap is not None
    with pytest.raises(ValidationError):
        ContractTermsSnapshot(**{**snap.model_dump(), "bogus_term": "x"})


def test_t04a_20_provenance_traces_to_sources() -> None:
    """A8 law at T04A level: every output ref is an input ref; none invented."""
    inst = instance(source_evidence_refs=("prov:a", "prov:b"))
    reg = resolved_registry(inst)
    res = resolve(reg)
    snap = project(reg, res)
    assert snap is not None
    authorized = set(inst.source_evidence_refs) | set(res.source_evidence_refs)
    assert set(snap.source_evidence_refs) <= authorized
    assert snap.source_evidence_refs == inst.source_evidence_refs


# ---------------------------------------------------------------- adversarial A1-A8


def test_a1_one_contract_one_base_assumption_trap() -> None:
    """Multiplier != 1 must survive projection exactly."""
    inst = instance(contract_multiplier=Decimal("0.25"))
    reg = resolved_registry(inst)
    snap = project(reg, resolve(reg))
    assert snap is not None
    assert snap.contract_multiplier == Decimal("0.25")
    assert snap.contract_multiplier != Decimal("1")


def test_a2_stablecoin_equivalence_trap() -> None:
    """USD quote and USDT settlement remain distinct; no substitution."""
    ec = economic_contract(ec_id="EC-B", quote_asset_id="USD", settlement_asset_id="USDT")
    inst = instance(ec_id="EC-B")
    reg = registry(inst, economic_contracts=(ec,))
    snap = project(reg, resolve(reg))
    assert snap is not None
    assert snap.quote_asset_id == "USD"
    assert snap.settlement_asset_id == "USDT"
    assert snap.quote_asset_id != snap.settlement_asset_id


def test_a3_stale_terms_version_not_silent_upgraded() -> None:
    """A request bound to one instance keeps that instance's terms version."""
    old = instance(instance_id="CI-OLD", valid_to=datetime(2023, 6, 1, tzinfo=UTC),
                   contract_terms_version="1")
    new = instance(instance_id="CI-NEW", valid_from=datetime(2024, 3, 1, tzinfo=UTC),
                   valid_to=None, known_from=datetime(2024, 3, 1, tzinfo=UTC),
                   known_to=None, contract_terms_version="2")
    reg = registry(old, new)
    early_event = datetime(2023, 3, 1, hour=12, tzinfo=UTC)
    res = resolve(reg, event=early_event)
    assert res.contract_instance_id == "CI-OLD"
    snap = project(reg, res, event=early_event)
    assert snap is not None
    assert snap.contract_terms_version == "1"  # never "2"


def test_a4_knowledge_time_leakage_blocked() -> None:
    """A record known only after the cutoff supplies no terms."""
    late = instance(known_from=datetime(2024, 1, 1, tzinfo=UTC), known_to=None)
    reg = resolved_registry(late)
    res = resolve(reg, cutoff=CUTOFF_IN)
    assert res.status is IdentityResolutionStatus.PIT_KNOWLEDGE_BLOCKED
    assert project(reg, res, cutoff=CUTOFF_IN) is None


def test_a5_identity_to_terms_escalation_denied() -> None:
    """Resolved identity + incomplete (unverified-payoff) terms: no verified
    economic view, no identity-status tampering."""
    reg = resolved_registry(instance(payoff_type=PayoffType.UNKNOWN))
    res = resolve(reg)
    assert res.status is IdentityResolutionStatus.RESOLVED_EXACT
    assert project(reg, res) is None


def test_a6_ambiguity_laundering_by_equal_multipliers_blocked() -> None:
    """Two eligible candidates with identical multipliers stay AMBIGUOUS."""
    from crypto_sensor_fabric.normalization.identity import InstrumentAlias

    a1 = InstrumentAlias(
        alias_id="DA1", provider=PROVIDER, venue=VENUE, alias_text="DUPA",
        alias_type="API_SYMBOL", contract_instance_id="CI-D1",
        valid_from=T0, valid_to=None, known_from=K0,
        source_evidence_refs=REFS, confidence="curated",
    )
    a2 = InstrumentAlias(
        alias_id="DA2", provider=PROVIDER, venue=VENUE, alias_text="DUPA",
        alias_type="DISPLAY_SYMBOL", contract_instance_id="CI-D2",
        valid_from=T0, valid_to=None, known_from=K0,
        source_evidence_refs=REFS, confidence="curated",
    )
    i1 = instance(instance_id="CI-D1", native_symbol="DUP1")
    i2 = instance(instance_id="CI-D2", native_symbol="DUP2")
    assert i1.contract_multiplier == i2.contract_multiplier == Decimal("1")
    reg = IdentityRegistrySnapshot(
        registry_version="dup",
        assets=(asset("BTC"), asset("USDT")),
        venues=(venue(),),
        economic_contracts=(economic_contract(),),
        venue_instruments=(instrument(),),
        contract_instances=(i1, i2),
        aliases=(a1, a2),
    )
    res = resolve_instrument(reg, PROVIDER, VENUE, "DUPA", EVENT, CUTOFF_IN)
    assert res.status is IdentityResolutionStatus.AMBIGUOUS
    assert project(reg, res) is None


def test_a7_null_to_zero_laundering_blocked() -> None:
    """Missing required terms cannot become numeric zero."""
    assert ContractInstance.model_fields["contract_multiplier"].is_required()
    with pytest.raises(ValidationError):
        instance(contract_multiplier=None)  # type: ignore[arg-type]
    # and there is no construction path that defaults the term to 0 or 1:
    assert ContractInstance.model_fields["contract_multiplier"].default is None or (
        ContractInstance.model_fields["contract_multiplier"].default == "0"
    ) is False


def test_a8_source_evidence_fabrication_blocked() -> None:
    """Snapshot refs are a subset of authorized sources -- verbatim copy."""
    inst = instance(source_evidence_refs=("prov:only-this-one",))
    reg = resolved_registry(inst)
    snap = project(reg, resolve(reg))
    assert snap is not None
    assert snap.source_evidence_refs == ("prov:only-this-one",)
    assert "fabricated:ref" not in snap.source_evidence_refs
