"""SENSOR-B5-I03 - RED-first adversarial PIT/lifecycle/alias resolver suite.

Directive 42 enumerates twenty RED cases (1-20 below) and directive 43 the
temporal boundary axes; this suite is authored BEFORE any I03 production code
(the B5-I03A commit captures these failing) so no resolver behavior can be
shaped to pass a test written after the fact.

RED pairing protocol (B5-I03A, disclosed in the implementation evidence):
each I03-owned name is reached through a lazily-guarded factory, so while the
production surface is absent every test that transitively needs it FAILS on
its identity checks (this is the RED capture), while tests that only need the
sealed B5-I02 surface compile and run.  After B5-I03C the guards become vacuous
real imports and the whole suite is the standing regression battery.

The machines under test (I03A RED posture):

*   peer-surface pop           :: B5-I03 production symbol not yet present
*   knowledge-cutoff shield    :: known_from must precede the cutoff
*   listing echo               :: economically-valid symbol before/after window
*   breaker cutover            :: relisting/symbol-reuse new-instance law
*   alias interval gate        :: registered alias matched only seconds clear
*   ambiguity refactor         :: equally-valid candidates refuse to pick

OFFLINE: no network, no provider adapter, no filesystem.  The core registry
under test is OFFLINE IDENTITY FIXTURES (I02 directive 22), not production
mapping claims.  All times are UTC-aware; naive inputs get dedicated negative
cases.  No docstring below carries a section-mark glyph (the chunked-file
authoring hazard documented in the I02 ratification): plan citations use the
compact form S<n> for bloc_05/01 section <n> and I03D<n> for directive 42's
own numbering, so source scanners see plain ASCII here.
"""

from __future__ import annotations

import importlib
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
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
)

UTC = timezone.utc

# ----------------------------------------------------------------------------
# Timeline (all UTC-aware; deliberately many separate ticks so boundary axes
# never accidentally coincide)
# ----------------------------------------------------------------------------
T0 = datetime(2023, 1, 1, hour=12, tzinfo=UTC)   # instance A listing (valid_from)
T1 = datetime(2024, 1, 1, hour=12, tzinfo=UTC)   # instance A delisted (valid_to)
PAUSE = datetime(2024, 6, 1, tzinfo=UTC)         # inside the relist break
T2 = datetime(2025, 1, 1, hour=12, tzinfo=UTC)   # instance B relisting
FAR_FUTURE = datetime(2030, 1, 1, tzinfo=UTC)
MAX_INSTANT = datetime.max.replace(tzinfo=UTC)

INCLUDE_MARGIN = timedelta(microseconds=1)  # one tick past an exclusive bound

SHA256 = "3f79bb7b435b05321651daefd374cdc681dc06faa65e374e38337b88ca4c6a11"

PROVIDER = "PROV"
VENUE = "EXA_FUT"
NATIVE = "XBTUSDT"
PROVIDER_INSTRUMENT_ID = "00000000-0000-0000-0000-000000dp0001"

# ----------------------------------------------------------------------------
# I03 surface guards (lazily bound once the production modules exist)
# ----------------------------------------------------------------------------

_ALIAS_TYPE = None
_INSTRUMENT_ALIAS = None
_INSTRUMENT_LIFECYCLE = None
_LIFECYCLE_STATE = None
_RESOLVE = None
_RESOLUTION_STATUS = None


def _identity():
    return importlib.import_module("crypto_sensor_fabric.normalization.identity")


def _has(name: str) -> bool:
    return hasattr(_identity(), name)


def _require(name: str):
    if not _has(name):
        pytest.fail(
            "B5-I03 RED capture: " + name + " is not implemented yet; this "
            "test is wired to fail RED-first (directive 42)"
        )
    return getattr(_identity(), name)


def alias_type():
    global _ALIAS_TYPE
    if _ALIAS_TYPE is None:
        _ALIAS_TYPE = _require("AliasType")
    return _ALIAS_TYPE


def instrument_alias():
    global _INSTRUMENT_ALIAS
    if _INSTRUMENT_ALIAS is None:
        _INSTRUMENT_ALIAS = _require("InstrumentAlias")
    return _INSTRUMENT_ALIAS


def lifecycle_state():
    global _LIFECYCLE_STATE
    if _LIFECYCLE_STATE is None:
        _LIFECYCLE_STATE = _require("LifecycleState")
    return _LIFECYCLE_STATE


def instrument_lifecycle():
    global _INSTRUMENT_LIFECYCLE
    if _INSTRUMENT_LIFECYCLE is None:
        _require("InstrumentLifecycle")
        _INSTRUMENT_LIFECYCLE = _identity().InstrumentLifecycle
    return _INSTRUMENT_LIFECYCLE


def resolve():
    global _RESOLVE
    if _RESOLVE is None:
        _RESOLVE = _require("resolve_instrument")
    return _RESOLVE


def resolution_status():
    global _RESOLUTION_STATUS
    if _RESOLUTION_STATUS is None:
        _RESOLUTION_STATUS = _require("IdentityResolutionStatus")
    return _RESOLUTION_STATUS


# ----------------------------------------------------------------------------
# I02 fixture builders (exact source style validated by the I02 suite)
# ----------------------------------------------------------------------------


def asset(asset_id: str = "BTC", symbol: str = "BTC") -> CanonicalAsset:
    return CanonicalAsset(
        asset_id=asset_id,
        symbol_canonical=symbol,
        asset_type="CRYPTO",
        metadata_version="1",
    )


def usdt_asset() -> CanonicalAsset:
    return asset("USDT", "USDT")


def venue(venue_id: str = VENUE) -> Venue:
    return Venue(venue_id=venue_id)


def instrument(
    native_symbol: str = NATIVE,
    provider: str = PROVIDER,
    venue_id: str = VENUE,
    provider_instrument_id=PROVIDER_INSTRUMENT_ID,
) -> VenueInstrument:
    return VenueInstrument(
        provider=provider,
        venue=venue_id,
        native_symbol=native_symbol,
        provider_instrument_id=provider_instrument_id,
        instrument_type="PERPETUAL_FUTURE",
        native_metadata_hash=SHA256,
        first_seen_at=T0,
        last_seen_at=MAX_INSTANT,
    )


def economic_contract() -> EconomicContract:
    return EconomicContract(
        economic_contract_id="EC-BTCUSDT-PERP-A",
        underlying_asset_id="BTC",
        quote_asset_id="USDT",
        settlement_asset_id="USDT",
        margin_asset_id=None,
        instrument_type="PERPETUAL_FUTURE",
        perpetual_or_delivery="PERPETUAL",
        payoff_type=PayoffType.LINEAR,
    )


def instance2(
    native_symbol: str = NATIVE,
    instance_id: str = "CI-A",
    valid_from: datetime = T0,
    valid_to: datetime | None = T1,
    known_from: datetime | None = None,
    known_to: datetime | None = None,
) -> ContractInstance:
    kf = T0 - timedelta(days=2) if known_from is None else known_from
    return ContractInstance(
        contract_instance_id=instance_id,
        provider=PROVIDER,
        venue=VENUE,
        native_symbol=native_symbol,
        economic_contract_id="EC-BTCUSDT-PERP-A",
        valid_from=valid_from,
        valid_to=valid_to,
        known_from=kf,
        known_to=known_to,
        contract_multiplier=Decimal("1"),
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
        contract_terms_version="1",
        source_evidence_refs=("provider-docs:exchange-a-xbtusdt",),
    )


def registry_with_instances(*instances: ContractInstance) -> IdentityRegistrySnapshot:
    return IdentityRegistrySnapshot(
        registry_version="snap1",
        assets=(asset(), usdt_asset()),
        venues=(venue(),),
        economic_contracts=(economic_contract(),),
        venue_instruments=(instrument(),),
        contract_instances=instances,
    )


def snapshot_with_aliases(aliases, *instances, lifecycle=(), registry_version="work", extra_venue_ids=()):
    """Snapshot builder: registers every venue an alias row references plus the
    extra venues given in extra_venue_ids, so nested-fixtures produce
    well-formed snapshots (wrong-venue/wrong-provider negatives exercise the
    RESOLVER side, never a registry shape error)."""
    venue_ids = [VENUE]
    for al in aliases:
        if not isinstance(al, str) and al.venue != VENUE and al.venue not in venue_ids:
            venue_ids.append(al.venue)
    for vid in extra_venue_ids:
        if vid not in venue_ids:
            venue_ids.append(vid)
    return IdentityRegistrySnapshot(
        registry_version=registry_version,
        assets=(asset(), usdt_asset()),
        venues=tuple(venue(vid) for vid in venue_ids),
        economic_contracts=(economic_contract(),),
        venue_instruments=(instrument(),),
        contract_instances=instances,
        aliases=tuple(aliases),
        lifecycle_events=tuple(lifecycle),
    )


def alias(
    alias_text: str,
    alias_type_value=None,
    instance_id: str = "CI-A",
    valid_from: datetime = T0,
    valid_to: datetime | None = T1,
    known_from: datetime = T0 - timedelta(days=1),
    provider: str = PROVIDER,
    venue_id: str = VENUE,
):
    return instrument_alias()(
        alias_id="AL:" + instance_id + ":" + alias_text,
        provider=provider,
        venue=venue_id,
        alias_text=alias_text,
        alias_type=alias_type_value or alias_type().API_SYMBOL,
        contract_instance_id=instance_id,
        valid_from=valid_from,
        valid_to=valid_to,
        known_from=known_from,
        source_evidence_refs=("provider-docs:alias-registration",),
        confidence="operator-curated",
    )


def lifecycle_event(
    state,
    state_from: datetime = T0,
    state_to: datetime | None = None,
    known_from: datetime = T0 - timedelta(days=1),
    instance_id: str = "CI-A",
):
    return instrument_lifecycle()(
        provider=PROVIDER,
        venue=VENUE,
        contract_instance_id=instance_id,
        lifecycle_state=state,
        valid_from=state_from,
        valid_to=state_to,
        known_from=known_from,
        source_evidence_refs=("provider-docs:lifecycle-notices",),
    )


def resolve_instrument(snapshot, native_symbol, event_time, knowledge_cutoff, **kw):
    """Directive-35-shaped call adapter (keyword names are frozen in I03C)."""
    return resolve()(
        snapshot,
        provider=PROVIDER,
        venue=VENUE,
        native_symbol=native_symbol,
        event_time=event_time,
        knowledge_cutoff=knowledge_cutoff,
        **kw,
    )


# ----------------------------------------------------------------------------
# 42/1-42/3: future knowledge must not leak backward
# ----------------------------------------------------------------------------


def test_case_1_future_known_exact_symbol_must_not_resolve_backward() -> None:
    snap = registry_with_instances(instance2())
    st = resolution_status()
    out = resolve_instrument(
        snap, NATIVE, T0, T0 - timedelta(days=5)  # cutoff before any knowledge
    )
    assert out.status is st.PIT_KNOWLEDGE_BLOCKED
    assert out.contract_instance_id is None
    assert out.economic_contract_id is None
    assert out.canonical_asset_id is None


def test_case_2_future_known_provider_instrument_id_must_not_resolve_backward() -> None:
    snap = registry_with_instances(instance2())
    st = resolution_status()
    out = resolve()(
        snap,
        provider=PROVIDER,
        venue=VENUE,
        native_symbol=NATIVE,
        event_time=T0,
        knowledge_cutoff=T0 - timedelta(days=5),
        optional_provider_instrument_id=PROVIDER_INSTRUMENT_ID,
    )
    assert out.status is st.PIT_KNOWLEDGE_BLOCKED
    assert out.contract_instance_id is None


def test_case_3_future_known_alias_must_not_resolve_backward() -> None:
    at = alias_type()
    al = alias("BTCA1", alias_type_value=at.API_SYMBOL, known_from=FAR_FUTURE)
    snap = snapshot_with_aliases((al,), instance2())
    st = resolution_status()
    out = resolve_instrument(snap, "BTCA1", T0, PAUSE)
    assert out.status is st.PIT_KNOWLEDGE_BLOCKED
    assert out.matched_alias_id is None


# ----------------------------------------------------------------------------
# 42/4-42/5: pre-listing / post-delisting
# ----------------------------------------------------------------------------


def test_case_4_before_listing_is_not_yet_listed() -> None:
    snap = registry_with_instances(instance2())
    st = resolution_status()
    out = resolve_instrument(snap, NATIVE, T0 - timedelta(days=1), T2)
    assert out.status is st.NOT_YET_LISTED
    assert out.contract_instance_id is None


def test_case_5_after_delisting_is_delisted() -> None:
    snap = registry_with_instances(instance2())
    st = resolution_status()
    out = resolve_instrument(snap, NATIVE, T1 + INCLUDE_MARGIN, T2 + INCLUDE_MARGIN)
    assert out.status is st.DELISTED
    assert out.contract_instance_id is None


# ----------------------------------------------------------------------------
# 42/6-42/8: symbol reuse, relisting, break interval
# ----------------------------------------------------------------------------


def test_case_6_symbol_reuse_selects_old_instance_historically() -> None:
    a = instance2(instance_id="CI-A", valid_from=T0, valid_to=T1)
    b = instance2(
        instance_id="CI-B", valid_from=T2, valid_to=None, known_from=T2 - timedelta(days=2)
    )
    snap = registry_with_instances(a, b)
    st = resolution_status()
    out = resolve_instrument(snap, NATIVE, T0 + timedelta(days=30), T2 + timedelta(days=30))
    assert out.status is st.RESOLVED_EXACT
    assert out.contract_instance_id == "CI-A"
    assert out.economic_contract_id == "EC-BTCUSDT-PERP-A"
    assert out.terms_version == "1"


def test_case_7_relisting_selects_new_instance_only_after_new_valid_from() -> None:
    snap = registry_with_instances(instance2(), instance2(
        instance_id="CI-B", valid_from=T2, valid_to=None, known_from=T2 - timedelta(days=2)
    ))
    st = resolution_status()
    out = resolve_instrument(snap, NATIVE, T2 + timedelta(days=5), T2 + timedelta(days=5))
    assert out.status is st.RESOLVED_EXACT
    assert out.contract_instance_id == "CI-B"


def test_case_8_break_interval_does_not_silently_choose_latest() -> None:
    snap = registry_with_instances(
        instance2(),
        instance2(instance_id="CI-B", valid_from=T2, valid_to=None, known_from=T2 - timedelta(days=2)),
    )
    st = resolution_status()
    out = resolve_instrument(snap, NATIVE, PAUSE, T2 + timedelta(days=5))  # inside the break
    assert out.status is not st.RESOLVED_EXACT
    assert out.contract_instance_id is None


# ----------------------------------------------------------------------------
# 42/9-42/10: BTC/XBT law
# ----------------------------------------------------------------------------


def test_case_9_btc_xbt_without_alias_does_not_resolve() -> None:
    """Registry knows only the native XBTUSDT instance; BTCUSDT is asked for
    and must NOT be inferred (S10: BTC and XBT are distinct without an
    explicitly registered alias)."""
    st = resolution_status()
    out = resolve_instrument(
        base_aliasless_snapshot("XBTUSDT"), "BTCUSDT", T0 + timedelta(days=3), T2
    )
    assert out.status is st.UNKNOWN_SYMBOL
    assert out.contract_instance_id is None


def base_aliasless_snapshot(native_symbol: str) -> IdentityRegistrySnapshot:
    return IdentityRegistrySnapshot(
        registry_version="snap9",
        assets=(asset(), usdt_asset()),
        venues=(venue(),),
        economic_contracts=(economic_contract(),),
        venue_instruments=(instrument(native_symbol=native_symbol),),
        contract_instances=(
            instance2(native_symbol=native_symbol),
        ),
    )


# ----------------------------------------------------------------------------
# 42/11-42/13: alias registration discipline
# ----------------------------------------------------------------------------


def test_case_11_expired_alias_does_not_resolve() -> None:
    at = alias_type()
    al = alias("OLDA2", alias_type_value=at.ARCHIVE_SYMBOL, valid_from=T0, valid_to=T1)
    snap = snapshot_with_aliases((al,), instance2())
    st = resolution_status()
    out = resolve_instrument(snap, "OLDA2", T1 + INCLUDE_MARGIN, T2)
    assert out.status is st.UNKNOWN_SYMBOL
    assert out.matched_alias_id is None


def test_case_12_wrong_venue_alias_does_not_resolve() -> None:
    at = alias_type()
    al = alias("OTHV1", alias_type_value=at.API_SYMBOL, venue_id="OTHER_FUT")
    snap = snapshot_with_aliases((al,), instance2())
    st = resolution_status()
    out = resolve_instrument(snap, "OTHV1", T0 + timedelta(days=3), T2)
    assert out.status is st.UNKNOWN_SYMBOL


def test_case_13_wrong_provider_alias_does_not_resolve() -> None:
    at = alias_type()
    al = alias("OTHP1", alias_type_value=at.WEBSOCKET_SYMBOL, provider="OTHER_PROV")
    snap = snapshot_with_aliases((al,), instance2())
    st = resolution_status()
    out = resolve_instrument(snap, "OTHP1", T0 + timedelta(days=3), T2)
    assert out.status is st.UNKNOWN_SYMBOL


# ----------------------------------------------------------------------------
# 42/14 + I03 24/32: alias ambiguity must fail closed (registry AND resolver)
# ----------------------------------------------------------------------------


def test_case_14_competing_alias_candidates_return_ambiguous() -> None:
    """I03 sections 24/32: two aliases of the same text, both PIT-valid, each
    pointing at a different instance, must surface AMBIGUOUS -- registry keeps
    the evidence, the resolver refuses to pick a winner."""
    at = alias_type()
    a1 = alias("AMBA1", alias_type_value=at.API_SYMBOL, instance_id="CI-AMBA1",
               valid_from=T0, valid_to=None)
    a2 = alias("AMBA1", alias_type_value=at.DISPLAY_SYMBOL, instance_id="CI-AMBA2",
               valid_from=T0, valid_to=None)
    snap = snapshot_with_aliases(
        (a1, a2),
        instance2(
            instance_id="CI-AMBA1",
            valid_from=T0,
            valid_to=T1,
            native_symbol="AMBAA1",
        ),
        instance2(
            instance_id="CI-AMBA2",
            valid_from=T2,
            valid_to=None,
            known_from=T2 - timedelta(days=2),
            native_symbol="AMBAA2",
        ),
        registry_version="work",
    )
    st = resolution_status()
    out = resolve_instrument(snap, "AMBA1", T0 + timedelta(days=3), T2 + timedelta(days=3))
    assert out.status is st.AMBIGUOUS
    assert out.contract_instance_id is None
    assert out.economic_contract_id is None
    assert out.matched_alias_id is None


# ----------------------------------------------------------------------------
# 42/15 + I03 20: fuzzy/prefix prohibition
# ----------------------------------------------------------------------------


@pytest.mark.parametrize("probe", ["BTCUSD", "BTCUSDTZ", "XBTUSDT1"])
def test_prefix_candidates_do_not_match(probe: str) -> None:
    snap = registry_with_instances(instance2())
    st = resolution_status()
    out = resolve_instrument(snap, probe, T0 + timedelta(days=3), T2)
    assert out.status is st.UNKNOWN_SYMBOL
    assert out.contract_instance_id is None


def test_fuzzy_one_char_deviation_cannot_resolve() -> None:
    snap = registry_with_instances(instance2())
    st = resolution_status()
    out = resolve_instrument(snap, "XBTIST", T0 + timedelta(days=3), T2)
    assert out.status is st.UNKNOWN_SYMBOL


def test_case_fold_cannot_resolve() -> None:
    snap = registry_with_instances(instance2())
    st = resolution_status()
    out = resolve_instrument(snap, "xbtusdt", T0 + timedelta(days=3), T2)
    assert out.status is st.UNKNOWN_SYMBOL


def test_production_sources_carry_no_fuzzy_imports() -> None:
    import crypto_sensor_fabric.normalization.identity as identity

    pkg_dir = identity.__file__.rsplit("/", 1)[0]
    import pathlib

    for path in pathlib.Path(pkg_dir).glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for banned in ("difflib", "rapidfuzz", "fuzzywuzzy", "Levenshtein"):
            assert banned not in text, (path.name, banned)


# ----------------------------------------------------------------------------
# 42/16-42/17: tier precedence
# ----------------------------------------------------------------------------


def test_case_16_provider_id_tier_outranks_symbol_tier() -> None:
    """Tier 1 wins only with PIT-valid evidence, anchored through the
    ID-matched instrument's native symbol pipeline (the winner is the exact
    instance the ID denotes at event_time)."""
    snap = registry_with_instances(instance2())
    st = resolution_status()
    out = resolve()(
        snap,
        provider=PROVIDER,
        venue=VENUE,
        native_symbol=NATIVE,
        event_time=T0,
        knowledge_cutoff=T2,
        optional_provider_instrument_id=PROVIDER_INSTRUMENT_ID,
    )
    assert out.status is st.RESOLVED_EXACT
    assert out.contract_instance_id == "CI-A"
    assert "provider-docs:exchange-a-xbtusdt" in out.source_evidence_refs
    flag_values = {flag.value for flag in out.quality_flags}
    assert "IDENTITY_PROVIDER_ID_MISSING" in flag_values


def test_case_17_exact_symbol_tier_outranks_alias_tier() -> None:
    at = alias_type()
    aliased = alias("SOMEA", alias_type_value=at.API_SYMBOL)
    snap = snapshot_with_aliases((aliased,), instance2())
    st = resolution_status()
    out = resolve_instrument(snap, NATIVE, T0 + timedelta(days=3), T2)
    assert out.status is st.RESOLVED_EXACT
    assert out.matched_alias_id is None


# ----------------------------------------------------------------------------
# 42/18: unresolved output carries no fabricated identity
# ----------------------------------------------------------------------------


def test_case_18_unresolved_output_contains_no_fabricated_ids() -> None:
    snap = registry_with_instances(instance2())
    st = resolution_status()
    for symbol, when in (
        ("GHOST", T0 + timedelta(days=3)),          # unknown symbol
        (NATIVE, T0 - timedelta(days=30)),          # pre-listing
        (NATIVE, T1 + timedelta(days=30)),          # post-delisting
    ):
        out = resolve_instrument(snap, symbol, when, T2)
        assert out.status is not st.RESOLVED_EXACT
        assert out.contract_instance_id is None
        assert out.economic_contract_id is None
        assert out.canonical_asset_id is None
        assert out.terms_version is None
        assert out.matched_alias_id is None
        assert out.source_evidence_refs == ()


# ----------------------------------------------------------------------------
# 42/19-42/20: naive-time refusal (I03 35)
# ----------------------------------------------------------------------------


def test_case_19_naive_event_time_refused() -> None:
    snap = registry_with_instances(instance2())
    with pytest.raises(Exception):
        resolve_instrument(snap, NATIVE, datetime(2024, 1, 1), T2)


def test_case_20_naive_knowledge_cutoff_refused() -> None:
    snap = registry_with_instances(instance2())
    with pytest.raises(Exception):
        resolve_instrument(snap, NATIVE, T0, datetime(2024, 1, 1))


# ----------------------------------------------------------------------------
# 43 boundary matrix
# ----------------------------------------------------------------------------


def test_boundary_valid_from_inclusive() -> None:
    snap = registry_with_instances(instance2())
    st = resolution_status()
    out = resolve_instrument(snap, NATIVE, T0, T2)          # event == valid_from
    assert out.status is st.RESOLVED_EXACT
    assert out.contract_instance_id == "CI-A"


def test_boundary_valid_to_exclusive() -> None:
    snap = registry_with_instances(instance2())
    st = resolution_status()
    out = resolve_instrument(snap, NATIVE, T1, T2)          # event == valid_to
    assert out.status is st.DELISTED


def test_boundary_known_from_inclusive() -> None:
    snap = registry_with_instances(instance2())             # known_from = T0-2d
    st = resolution_status()
    out = resolve_instrument(
        snap, NATIVE, T0 + timedelta(days=5), T0 - timedelta(days=2)
    )                                                        # cutoff == known_from
    assert out.status is st.RESOLVED_EXACT


def test_boundary_known_from_one_tick_before_cutoff_refused() -> None:
    """43 boundary: known_from is INCLUSIVE -> cutoff one tick BEFORE known_from
    must be refused via the alias-window negative (the instance's known_from is
    BEFORE its valid_from in the core fixture, so the symbol tier cannot
    produce a knowledge leak here by construction)."""
    at = alias_type()
    # alias with known_from strictly AFTER valid_from
    al = alias("KNLF1", alias_type_value=at.API_SYMBOL, valid_from=T0, known_from=T1)
    snap = snapshot_with_aliases((al,), instance2())
    st = resolution_status()
    out = resolve_instrument(
        snap,
        "KNLF1",
        T0 + timedelta(days=5),
        T1 - timedelta(microseconds=1),                      # 1 tick before known_from
    )
    assert out.status is st.PIT_KNOWLEDGE_BLOCKED


def test_boundary_alias_valid_from_inclusive() -> None:
    at = alias_type()
    al = alias("BNDA1", alias_type_value=at.API_SYMBOL, valid_from=T0, known_from=T0)
    snap = snapshot_with_aliases((al,), instance2())
    st = resolution_status()
    out = resolve_instrument(snap, "BNDA1", T0, T2)         # event == alias.valid_from
    assert out.status is st.RESOLVED_ALIAS


def test_boundary_alias_valid_to_exclusive() -> None:
    at = alias_type()
    al = alias("BNDA2", alias_type_value=at.API_SYMBOL, valid_from=T0, valid_to=T1)
    snap = snapshot_with_aliases((al,), instance2())
    st = resolution_status()
    out = resolve_instrument(snap, "BNDA2", T1, T2)         # event == alias.valid_to
    assert out.status is not st.RESOLVED_ALIAS


def test_boundary_open_ended_valid_to_supported() -> None:
    snap = registry_with_instances(
        instance2(),
        instance2(instance_id="CI-B", valid_from=T2, valid_to=None, known_from=T2 - timedelta(days=2)),
    )
    st = resolution_status()
    out = resolve_instrument(snap, NATIVE, FAR_FUTURE, MAX_INSTANT)
    assert out.status is st.RESOLVED_EXACT
    assert out.contract_instance_id == "CI-B"


# ----------------------------------------------------------------------------
# I03 15: provider-ID reuse across instances respects event_time
# ----------------------------------------------------------------------------


def test_provider_id_reused_does_not_cross_instances() -> None:
    snap = registry_with_instances(
        instance2(),
        instance2(instance_id="CI-B", valid_from=T2, valid_to=None, known_from=T2 - timedelta(days=2)),
    )
    out_old = resolve()(
        snap,
        provider=PROVIDER,
        venue=VENUE,
        native_symbol=NATIVE,
        event_time=T0 + timedelta(days=5),
        knowledge_cutoff=T2 + timedelta(days=5),
        optional_provider_instrument_id=PROVIDER_INSTRUMENT_ID,
    )
    assert out_old.contract_instance_id == "CI-A"
    out_new = resolve()(
        snap,
        provider=PROVIDER,
        venue=VENUE,
        native_symbol=NATIVE,
        event_time=T2 + timedelta(days=5),
        knowledge_cutoff=T2 + timedelta(days=5),
        optional_provider_instrument_id=PROVIDER_INSTRUMENT_ID,
    )
    assert out_new.contract_instance_id == "CI-B"


def test_provider_id_missing_id_returns_no_result() -> None:
    st = resolution_status()
    snap = registry_with_instances(instance2())
    out = resolve()(
        snap,
        provider=PROVIDER,
        venue=VENUE,
        native_symbol="NOSUCHINSTRUMENTID",
        event_time=T0 + timedelta(days=3),
        knowledge_cutoff=T2,
        optional_provider_instrument_id="00000000-0000-0000-0000-000000dpId0x",
    )
    assert out.status is st.UNKNOWN_SYMBOL


# ----------------------------------------------------------------------------
# I03 21 + S12: stablecoin / quote-asset firewall
# ----------------------------------------------------------------------------


def test_case_stablecoin_never_usd_substituted() -> None:
    """A USDT-quoted contract resolves as exactly its registered identity;
    nothing turns USDT into USD, and nothing returns fabricated USD assets."""
    snap = registry_with_instances(instance2())
    st = resolution_status()
    out = resolve_instrument(snap, NATIVE, T0 + timedelta(days=3), T2)
    assert out.status is st.RESOLVED_EXACT
    assert out.canonical_asset_id == "BTC"          # underlying, never quote
    assert "USD" not in {out.canonical_asset_id}


# ----------------------------------------------------------------------------
# I03 37: determinism
# ----------------------------------------------------------------------------


def test_resolver_is_deterministic() -> None:
    at = alias_type()
    al = alias("DETA1", alias_type_value=at.API_SYMBOL, known_from=T0)
    snap = snapshot_with_aliases(
        (al,),
        instance2(),
        instance2(instance_id="CI-B", valid_from=T2, valid_to=None, known_from=T2 - timedelta(days=2)),
        registry_version="det1",
    )
    out1 = resolve_instrument(snap, "DETA1", T0 + timedelta(days=3), T2)
    out2 = resolve_instrument(snap, "DETA1", T0 + timedelta(days=3), T2)
    assert out1.model_dump_json() == out2.model_dump_json()
    assert serialize_identity_registry_yaml(snap) == serialize_identity_registry_yaml(snap)
    assert parse_identity_registry_yaml(serialize_identity_registry_yaml(snap)) == snap


# ----------------------------------------------------------------------------
# I03 33 + I03D red-team finding A12: lifecycle downgrade of an alias match
# ----------------------------------------------------------------------------


def test_alias_match_inside_suspended_window_downgrades_without_alias_id() -> None:
    """B5-I03D adversarial finding (red-team case A12): an alias match inside
    a knowledge-valid SUSPENDED window must DOWNGRADE to
    RESOLVED_WITH_WARNING, never crash on the matched_alias_id-only-on-
    RESOLVED_ALIAS validator law.  Provenance stays with the alias evidence
    refs, the confidence token and IDENTITY_ALIAS_USED; matched_alias_id stays
    None because that field is reserved for RESOLVED_ALIAS (I03 validator
    law: RESOLVED_WITH_WARNING carries its own lifecycle evidence)."""
    at = alias_type()
    al = alias("SUSP1", alias_type_value=at.API_SYMBOL, known_from=T0)
    lc = lifecycle_event(
        lifecycle_state().SUSPENDED, state_from=T0, state_to=None, known_from=T0
    )
    snap = snapshot_with_aliases((al,), instance2(), lifecycle=(lc,))
    st = resolution_status()
    out = resolve_instrument(snap, "SUSP1", T0 + timedelta(days=3), T2)
    assert out.status is st.RESOLVED_WITH_WARNING
    assert out.contract_instance_id == "CI-A"          # identity still selected
    assert out.matched_alias_id is None                # reserved for RESOLVED_ALIAS
    flag_values = {flag.value for flag in out.quality_flags}
    assert "IDENTITY_LIFECYCLE_BOUNDARY" in flag_values
    assert "IDENTITY_ALIAS_USED" in flag_values        # alias provenance retained
    assert "provider-docs:alias-registration" in out.source_evidence_refs
    assert out.confidence == "operator-curated"        # alias provenance retained


def test_alias_match_outside_warning_windows_keeps_matched_alias_id() -> None:
    """The paired law: with no lifecycle warning over the event, an alias
    match stays RESOLVED_ALIAS and keeps matched_alias_id (directive 17)."""
    at = alias_type()
    al = alias("KPA1", alias_type_value=at.API_SYMBOL, known_from=T0)
    snap = snapshot_with_aliases((al,), instance2())
    st = resolution_status()
    out = resolve_instrument(snap, "KPA1", T0 + timedelta(days=3), T2)
    assert out.status is st.RESOLVED_ALIAS
    assert out.matched_alias_id == "AL:CI-A:KPA1"
