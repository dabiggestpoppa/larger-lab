"""Bloc 1A–1D adversarial tests (Phase 12).

Contract references: plan v0.3 adversarial catalogs ADV-1A/1B/1C/1D and
invariants. Each test names the adversarial case it exercises.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from crypto_systems_intelligence_atlas.identity import (
    CanonicalObject,
    DeploymentIdentity,
    DeploymentMarkerKind,
    DeploymentStatus,
    IdentityResolutionEvent,
    ObjectType,
    RealizationIdentity,
    RealizationRoute,
    RepresentationMechanism,
    TickerSymbol,
    mint_object_id,
)
from crypto_systems_intelligence_atlas.relationships import (
    EdgeType,
    GraphValidator,
    Hyperedge,
    HyperedgeClass,
    HyperedgeRole,
    RouteAttributes,
    RouteMechanism,
    TypedEdge,
)
from crypto_systems_intelligence_atlas.temporal import (
    ClaimBinding,
    RecordStore,
    TemporalRecord,
    UnknownBound,
)
from datetime import UTC, datetime

from .conftest import NOW, contract_deployment, make_chain, make_token


def _claim(cid: str = "c") -> ClaimBinding:
    return ClaimBinding(claim_id=cid, source_id="s")


def _edge(
    eid: str,
    etype: EdgeType,
    subj: str,
    obj: str,
    **kw,
) -> TypedEdge:
    return TypedEdge(
        edge_id=eid,
        edge_type=etype,
        subject_id=subj,
        object_id=obj,
        claim_binding=_claim(),
        observed_at=NOW,
        valid_from=NOW,
        **kw,
    )


# --------------------------------------------------------------------------
# ADV-1A-A: same ticker, unrelated assets
# --------------------------------------------------------------------------


def test_same_ticker_unrelated_assets_not_merged(registry):
    gas_on_eth = make_token(registry, "gas-dao", "Gas DAO", tickers=(("GAS", "eth"),))
    gas_fnx = make_token(registry, "gas-fonx", "FunctionX", tickers=(("GAS", "fx"),))
    hits = registry.find_by_ticker("GAS")
    assert len(hits) == 2  # collision visible, never silently merged
    assert gas_on_eth.object_id != gas_fnx.object_id
    # different collision groups recorded
    groups = {t.collision_group for o in hits for t in o.ticker_symbols if t.symbol == "GAS"}
    assert groups == {"eth", "fx"}


# --------------------------------------------------------------------------
# ADV-1A-B/L: rebrand preserves identity
# --------------------------------------------------------------------------


def test_rebrand_preserves_identity(registry):
    obj = make_token(registry, "rebrand-case", "Old Name", tickers=(("OLD", "spot"),))
    # rebrand = new ticker window on the SAME object_id (old window kept)
    rebranded = obj.model_copy(
        update={
            "ticker_symbols": obj.ticker_symbols
            + (
                TickerSymbol(symbol="NEW", context="spot", valid_from=NOW, collision_group="spot"),
            )
        }
    )
    registry._objects[obj.object_id] = rebranded
    got = registry.get(obj.object_id)
    assert got.canonical_name == "Old Name"  # same identity
    assert any(t.symbol == "OLD" for t in got.ticker_symbols)  # old window kept
    assert any(t.symbol == "NEW" for t in got.ticker_symbols)  # new window added


# --------------------------------------------------------------------------
# ADV-1A-E: fork creates distinct identity
# --------------------------------------------------------------------------


def test_fork_creates_distinct_identity(registry):
    chain_a = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "bitcoin"))
    chain_b = make_chain(registry, "bitcoin-cash")
    fork = make_token(registry, "bch", "Bitcoin Cash", tickers=(("BCH", "spot"),))
    validator = GraphValidator(registry)
    validator.add_edge(
        _edge(
            "fork-1",
            EdgeType.FORKED_FROM,
            chain_b.object_id,
            chain_a.object_id,
        )
    )
    assert fork.object_id != registry.get(chain_a.object_id).object_id
    assert validator.validate_acyclic(EdgeType.FORKED_FROM)


def test_forked_from_cycle_invalid(registry):
    """IR-3: FORKED_FROM must be acyclic — enforced at INSERTION (hardening
    R1: fail-closed, the cycle never becomes graph state)."""
    validator = GraphValidator(registry)
    a = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "bitcoin"))
    b = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "ethereum"))
    validator.add_edge(_edge("f1", EdgeType.FORKED_FROM, a.object_id, b.object_id))
    with pytest.raises(ValueError, match="cycle"):
        validator.add_edge(_edge("f2", EdgeType.FORKED_FROM, b.object_id, a.object_id))
    # graph intact: only f1 present, audit method confirms DAG
    assert set(validator.edges) == {"f1"}
    assert validator.validate_acyclic(EdgeType.FORKED_FROM)


# --------------------------------------------------------------------------
# Migration preserves lineage (realization + object level)
# --------------------------------------------------------------------------


def test_migration_creates_lineage_not_replacement(registry):
    """INV-1A-11: closure/migration keeps history queryable."""
    usdc = make_token(registry, "usdc-mig", "USD Coin", otype=ObjectType.STABLECOIN)
    osmosis = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "osmosis"))
    old = RealizationIdentity(
        realization_id=f"{usdc.object_id}@{osmosis.object_id}:old-ch",
        canonical_asset_id=usdc.object_id,
        chain_id=osmosis.object_id,
        local_asset_identifier="ibc/old",
        representation_mechanism=RepresentationMechanism.IBC,
        route=RealizationRoute(path="p-old", channel_sequence=["channel-1"]),
        valid_from=NOW,
        status="MIGRATED",
        migration_to=f"{usdc.object_id}@{osmosis.object_id}:new-ch",
        valid_to=NOW + timedelta(days=1),
    )
    new = RealizationIdentity(
        realization_id=f"{usdc.object_id}@{osmosis.object_id}:new-ch",
        canonical_asset_id=usdc.object_id,
        chain_id=osmosis.object_id,
        local_asset_identifier="ibc/new",
        representation_mechanism=RepresentationMechanism.IBC,
        route=RealizationRoute(path="p-new", channel_sequence=["channel-2"]),
        valid_from=NOW + timedelta(days=1),
        migration_from=f"{usdc.object_id}@{osmosis.object_id}:old-ch",
    )
    registry.attach_realization(usdc.object_id, old)
    registry.attach_realization(usdc.object_id, new)
    obj = registry.get(usdc.object_id)
    assert len(obj.realizations) == 2  # both kept — lineage, not replacement
    by_id = {r.realization_id: r for r in obj.realizations}
    assert by_id[old.realization_id].migration_to == new.realization_id
    assert by_id[new.realization_id].migration_from == old.realization_id


def test_migrated_realization_requires_lineage():
    """INV-1A-11: MIGRATED without lineage pointers is invalid."""
    usdc_id = "csia:stablecoin:x"
    with pytest.raises(ValueError, match="lineage|valid_to"):
        RealizationIdentity(
            realization_id="csia:stablecoin:x@chain:ch",
            canonical_asset_id=usdc_id,
            chain_id="csia:blockchain:chain",
            local_asset_identifier="denom",
            representation_mechanism=RepresentationMechanism.IBC,
            valid_from=NOW,
            status="MIGRATED",
        )


def test_migration_lineage_cycle_invalid(registry):
    """INV-1A-11: lineage cycles are rejected by the KERNEL at attach time
    (hardening R1: enforcement lives in production, not in test-local
    pointer-chasing)."""
    usdc = make_token(registry, "usdc-cyc", "USD Coin", otype=ObjectType.STABLECOIN)
    osmosis = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "osmosis"))
    a = f"{usdc.object_id}@{osmosis.object_id}:a"
    b = f"{usdc.object_id}@{osmosis.object_id}:b"
    ra = RealizationIdentity(
        realization_id=a,
        canonical_asset_id=usdc.object_id,
        chain_id=osmosis.object_id,
        local_asset_identifier="d1",
        representation_mechanism=RepresentationMechanism.IBC,
        valid_from=NOW,
        status="MIGRATED",
        migration_to=b,
        valid_to=NOW,
    )
    rb = RealizationIdentity(
        realization_id=b,
        canonical_asset_id=usdc.object_id,
        chain_id=osmosis.object_id,
        local_asset_identifier="d2",
        representation_mechanism=RepresentationMechanism.IBC,
        valid_from=NOW,
        status="MIGRATED",
        migration_to=a,  # cycle: a -> b -> a
        valid_to=NOW,
    )
    registry.attach_realization(usdc.object_id, ra)
    with pytest.raises(ValueError, match="cycle"):
        registry.attach_realization(usdc.object_id, rb)  # kernel rejects
    # graph intact: only the first realization was attached
    assert len(registry.get(usdc.object_id).realizations) == 1


# --------------------------------------------------------------------------
# Protocol deployed on many chains; same contract string on different chains
# --------------------------------------------------------------------------


def test_same_contract_address_on_different_chains_distinct(registry):
    """ADV-1A-I: identical address strings on different chains stay distinct."""
    eth = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "ethereum"))
    base = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "base"))
    addr = "0xsame-address-string"
    usdc_eth = make_token(registry, "usdc-eth", "USD Coin", otype=ObjectType.STABLECOIN)
    usdc_base = make_token(registry, "usdc-base", "USD Coin", otype=ObjectType.STABLECOIN)
    registry.attach_deployment(usdc_eth.object_id, contract_deployment(usdc_eth, eth, addr))
    registry.attach_deployment(usdc_base.object_id, contract_deployment(usdc_base, base, addr))
    d1 = registry.get(usdc_eth.object_id).deployments[0]
    d2 = registry.get(usdc_base.object_id).deployments[0]
    assert d1.deployment_id != d2.deployment_id  # chain namespace separates them


# --------------------------------------------------------------------------
# Token -RUNS_ON-> chain invalid (IR-2); domain/range enforcement (IR-1)
# --------------------------------------------------------------------------


def test_token_runs_on_chain_invalid(registry):
    eth = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "ethereum"))
    tok = make_token(registry, "tok-runson", "Token")
    v = GraphValidator(registry)
    with pytest.raises(ValueError, match="domain/range violation"):
        v.add_edge(_edge("bad-1", EdgeType.RUNS_ON, tok.object_id, eth.object_id))


def test_invalid_domain_range_rejected(registry):
    eth = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "ethereum"))
    gov = registry.mint(
        CanonicalObject(
            object_id=mint_object_id(ObjectType.GOVERNANCE_SYSTEM, "gov"),
            object_type=ObjectType.GOVERNANCE_SYSTEM,
            canonical_name="Gov",
            valid_from=NOW,
        )
    )
    v = GraphValidator(registry)
    # GOVERNANCE_SYSTEM cannot RUNS_ON a chain (domain does not include it)
    with pytest.raises(ValueError, match="domain/range"):
        v.add_edge(_edge("bad-2", EdgeType.RUNS_ON, gov.object_id, eth.object_id))


def test_self_edge_invalid_except_flagged_wraps(registry):
    dex_a = registry.mint(
        CanonicalObject(
            object_id=mint_object_id(ObjectType.DEX, "dex-a"),
            object_type=ObjectType.DEX,
            canonical_name="DEX A",
            valid_from=NOW,
        )
    )
    v = GraphValidator(registry)
    with pytest.raises(ValueError, match="self-edge"):
        v.add_edge(_edge("self-1", EdgeType.COMPETES_WITH, dex_a.object_id, dex_a.object_id))


# --------------------------------------------------------------------------
# Invalid EVM field on non-EVM object (anti-EVM bias)
# --------------------------------------------------------------------------


def test_no_evm_field_required_for_non_evm(registry):
    """T-1B-6 permanent regression: XRPL issued asset needs no contract fields."""
    xrpl = registry.require(mint_object_id(ObjectType.LEDGER, "xrpl"))
    dep = DeploymentIdentity(
        deployment_id=f"x@{xrpl.object_id}:ISSUER_ACCOUNT(rX)",
        chain=xrpl.object_id,
        marker_kind=DeploymentMarkerKind.ISSUER_ACCOUNT,
        marker_value="rX",
        valid_from=NOW,
    )
    assert dep.marker_kind is not DeploymentMarkerKind.CONTRACT
    # model has no contract-required field at all — extra="forbid" rejects them
    with pytest.raises(ValueError):
        DeploymentIdentity(
            deployment_id=f"x2@{xrpl.object_id}:NATIVE",
            chain=xrpl.object_id,
            marker_kind=DeploymentMarkerKind.NATIVE,
            valid_from=NOW,
            contract_address="0xnot-allowed",  # type: ignore[call-arg]
        )


# --------------------------------------------------------------------------
# Temporal adversarial cases (ADV-1D-A..G)
# --------------------------------------------------------------------------


def test_late_triple_discovery_consistent():
    """ADV-1D-A: observed today, true 3y ago, evidence published 2y ago."""
    store = RecordStore()
    rec = TemporalRecord(
        observed_at=NOW,
        valid_from=datetime(2023, 9, 23, tzinfo=UTC),
        source_published_at=datetime(2024, 9, 23, tzinfo=UTC),
    )
    store.add("r1", rec)
    assert store.get("r1").valid_from < store.get("r1").source_published_at < store.get("r1").observed_at


def test_unknown_bounded_valid_time_never_fabricated():
    """ADV-1D-D / R9: unknown valid time is explicit, not a fake date."""
    rec = TemporalRecord(
        observed_at=NOW,
        valid_from=UnknownBound(
            earliest_bound=datetime(2020, 1, 1, tzinfo=UTC),
            latest_bound=datetime(2020, 6, 1, tzinfo=UTC),
            confidence_ref="claim-7",
        ),
    )
    assert isinstance(rec.valid_from, UnknownBound)
    assert rec.valid_from.kind == "UNKNOWN"
    # as-of inside the start bounds is UNDECIDABLE (hardening R1 Finding B:
    # never fabricate certainty — 2020-03-01 may precede the actual start)
    from crypto_systems_intelligence_atlas.temporal import holds_at

    assert holds_at(rec.valid_from, rec.valid_to, datetime(2020, 3, 1, tzinfo=UTC)) is None
    assert holds_at(rec.valid_from, rec.valid_to, datetime(2020, 6, 1, tzinfo=UTC)) is True
    # inside a valid_from UNKNOWN bound the as-of answer is undecidable
    rec2 = TemporalRecord(
        observed_at=NOW,
        valid_from=UnknownBound(
            earliest_bound=datetime(2019, 1, 1, tzinfo=UTC),
            latest_bound=datetime(2021, 1, 1, tzinfo=UTC),
        ),
        valid_to=UnknownBound(
            earliest_bound=datetime(2022, 1, 1, tzinfo=UTC),
            latest_bound=datetime(2024, 1, 1, tzinfo=UTC),
        ),
    )
    assert holds_at(rec2.valid_from, rec2.valid_to, datetime(2020, 3, 1, tzinfo=UTC)) is None
    assert holds_at(rec.valid_from, rec.valid_to, datetime(2019, 1, 1, tzinfo=UTC)) is False


def test_superseded_records_queryable_forever():
    """ADV-1D-I / R4: supersession chain preserved, nothing rewritten."""
    store = RecordStore()
    store.add("r1", TemporalRecord(observed_at=NOW, valid_from=NOW))
    corrected = TemporalRecord(
        observed_at=NOW + timedelta(hours=1),
        valid_from=NOW - timedelta(days=1),  # corrected start
        supersedes="r1",
    )
    store.supersede("r1", "r2", corrected)
    # old record still queryable, marked superseded
    old = store.get("r1")
    assert old.superseded_at == corrected.observed_at
    # current view excludes it
    assert [rid for rid, _ in store.current()] == ["r2"]
    # as-known(k) before the correction shows the OLD record (RC-2)
    known = [rid for rid, _ in store.as_known(NOW + timedelta(minutes=30))]
    assert known == ["r1"]


def test_conflicting_valid_times_coexist():
    """ADV-1D-C: two sources, different valid_from — CONTESTED, no averaging."""
    store = RecordStore()
    a = TemporalRecord(
        observed_at=NOW, valid_from=datetime(2021, 1, 1, tzinfo=UTC)
    )
    b = TemporalRecord(
        observed_at=NOW, valid_from=datetime(2022, 5, 5, tzinfo=UTC)
    )
    store.add("src-a", a)
    store.add("src-b", b)
    assert store.get("src-a").valid_from != store.get("src-b").valid_from
    assert len(store.current()) == 2  # both candidates retained


def test_naive_datetimes_rejected():
    """No silent local-time assumptions (Bloc 1D)."""
    with pytest.raises(ValueError, match="naive"):
        TemporalRecord(observed_at=datetime(2026, 1, 1), valid_from=NOW)


def test_valid_from_after_valid_to_invalid():
    """IR-6 / R1."""
    with pytest.raises(ValueError, match="R1"):
        TemporalRecord(
            observed_at=NOW,
            valid_from=datetime(2026, 6, 1, tzinfo=UTC),
            valid_to=datetime(2026, 1, 1, tzinfo=UTC),
        )


# --------------------------------------------------------------------------
# Hyperedge decomposition protection (IR-9) + role coverage (INV-1C-5)
# --------------------------------------------------------------------------


def test_hyperedge_roles_required(registry):
    base = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "base"))
    eth = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "ethereum"))
    circle = registry.mint(
        CanonicalObject(
            object_id=mint_object_id(ObjectType.ENTITY, "circle"),
            object_type=ObjectType.ENTITY,
            canonical_name="Circle",
            valid_from=NOW,
        )
    )
    usdc = make_token(registry, "usdc-he", "USD Coin", otype=ObjectType.STABLECOIN)
    he = Hyperedge(
        hyperedge_id="he-usdc-base",
        hyperedge_class=HyperedgeClass.HE_ISSUANCE,
        participants={
            HyperedgeRole.ISSUER: circle.object_id,
            HyperedgeRole.HOST_CHAIN: base.object_id,
            HyperedgeRole.ASSET: usdc.object_id,
            HyperedgeRole.SETTLEMENT_CHAIN: eth.object_id,
        },
        claim_binding=_claim("he-c"),
        observed_at=NOW,
        valid_from=NOW,
    )
    projection = he.pairwise_projection()
    # IR-9: projection is an explicitly-derived view, not stored edges
    assert dict(projection) == {
        HyperedgeRole.ISSUER: circle.object_id,
        HyperedgeRole.HOST_CHAIN: base.object_id,
        HyperedgeRole.ASSET: usdc.object_id,
        HyperedgeRole.SETTLEMENT_CHAIN: eth.object_id,
    }
    # atomic truth preserved: one record, four roles
    assert len(he.participants) == 4


def test_hyperedge_missing_roles_rejected(registry):
    with pytest.raises(ValueError, match="missing required roles"):
        Hyperedge(
            hyperedge_id="he-bad",
            hyperedge_class=HyperedgeClass.HE_ISSUANCE,
            participants={HyperedgeRole.ISSUER: "csia:entity:circle"},
            claim_binding=_claim("he-c2"),
            observed_at=NOW,
            valid_from=NOW,
        )


def test_bridge_route_hyperedge_requires_route_attributes(registry):
    """IR-12 / E-8."""
    eth = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "ethereum"))
    arb = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "arbitrum"))
    bridge = registry.mint(
        CanonicalObject(
            object_id=mint_object_id(ObjectType.BRIDGE, "arb-bridge"),
            object_type=ObjectType.BRIDGE,
            canonical_name="Arbitrum Bridge",
            valid_from=NOW,
        )
    )
    with pytest.raises(ValueError, match="route_attributes"):
        Hyperedge(
            hyperedge_id="he-br",
            hyperedge_class=HyperedgeClass.HE_BRIDGE_ROUTE,
            participants={
                HyperedgeRole.BRIDGE: bridge.object_id,
                HyperedgeRole.CHAIN_A: eth.object_id,
                HyperedgeRole.CHAIN_B: arb.object_id,
            },
            claim_binding=_claim("he-c3"),
            observed_at=NOW,
            valid_from=NOW,
        )
    he = Hyperedge(
        hyperedge_id="he-br2",
        hyperedge_class=HyperedgeClass.HE_BRIDGE_ROUTE,
        participants={
            HyperedgeRole.BRIDGE: bridge.object_id,
            HyperedgeRole.CHAIN_A: eth.object_id,
            HyperedgeRole.CHAIN_B: arb.object_id,
        },
        route_attributes=RouteAttributes(
            route_spec="canonical-bridge",
            mechanism=RouteMechanism.LOCK_MINT,
        ),
        claim_binding=_claim("he-c4"),
        observed_at=NOW,
        valid_from=NOW,
    )
    assert he.route_attributes.mechanism is RouteMechanism.LOCK_MINT


def test_secured_by_without_mechanism_invalid(registry):
    """IR-11 / E-1."""
    eth = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "ethereum"))
    val = registry.mint(
        CanonicalObject(
            object_id=mint_object_id(ObjectType.VALIDATOR_SYSTEM, "v"),
            object_type=ObjectType.VALIDATOR_SYSTEM,
            canonical_name="V",
            valid_from=NOW,
        )
    )
    with pytest.raises(ValueError, match="mechanism"):
        _edge("sec-1", EdgeType.SECURED_BY, eth.object_id, val.object_id)


def test_secured_by_mechanism_change_preserves_history(registry):
    """ADV-1C-L: PoW->PoS transition is a WORLD change: the PoW record gains
    valid_to; the PoS record is a separate fact (not a record-replacement).
    Both records coexist; as-of picks the right one per valid time."""
    store = RecordStore()
    edge_old = TemporalRecord(
        observed_at=NOW,
        valid_from=datetime(2015, 1, 1, tzinfo=UTC),
        valid_to=datetime(2022, 9, 15, tzinfo=UTC),  # PoW ends (world change)
    )
    edge_new = TemporalRecord(
        observed_at=NOW + timedelta(days=1),
        valid_from=datetime(2022, 9, 15, tzinfo=UTC),  # PoS begins
    )
    store.add("pow", edge_old)
    store.add("pos", edge_new)
    assert store.get("pow").valid_to is not None  # world-change preserved
    as_of_pos = store.as_of(datetime(2023, 1, 1, tzinfo=UTC))
    assert [rid for rid, _ in as_of_pos] == ["pos"]
    as_of_pow = store.as_of(datetime(2020, 1, 1, tzinfo=UTC))
    assert [rid for rid, _ in as_of_pow] == ["pow"]
    # record-replacement path stays distinct (ADV-1D-B): correcting the PoS
    # start date supersedes the record without touching world-change history
    store.supersede(
        "pos",
        "pos-corrected",
        TemporalRecord(
            observed_at=NOW + timedelta(days=2),
            valid_from=datetime(2022, 9, 15, 8, 0, tzinfo=UTC),
            supersedes="pos",
        ),
    )
    assert [rid for rid, _ in store.as_of(datetime(2023, 1, 1, tzinfo=UTC))] == ["pos-corrected"]
    assert store.get("pos").superseded_at is not None  # chain preserved


# --------------------------------------------------------------------------
# Immutability / no-destruction (INV-1D-1, INV-1A-4)
# --------------------------------------------------------------------------


def test_record_store_has_no_delete_or_overwrite():
    store = RecordStore()
    store.add("r", TemporalRecord(observed_at=NOW, valid_from=NOW))
    with pytest.raises(ValueError, match="immutable"):
        store.add("r", TemporalRecord(observed_at=NOW, valid_from=NOW))
    # R4: superseded records stay queryable forever
    store.supersede(
        "r",
        "r2",
        TemporalRecord(observed_at=NOW + timedelta(hours=1), valid_from=NOW, supersedes="r"),
    )
    assert store.get("r").superseded_at is not None
    assert not hasattr(store, "delete")  # no delete path exists


def test_identity_merge_event_is_recorded(registry):
    """INV-1A-6: merge/split are operator-approved recorded events."""
    a = make_token(registry, "merge-a", "A")
    b = make_token(registry, "merge-b", "B")
    registry.record_resolution_event(
        IdentityResolutionEvent(
            event_id="ev-1",
            kind="MERGE",
            source_object_ids=[b.object_id],
            target_object_ids=[a.object_id],
            reason="duplicate identity confirmed by operator",
            evidence_refs=["claim-1"],
            occurred_at=NOW,
        )
    )
    assert registry.resolution_events[0].kind == "MERGE"


def test_ticker_never_merges_on_mint(registry):
    """INV-1A-2: same (type, slug) blocked; different slugs with same ticker coexist."""
    make_token(registry, "uni-1", "Uniswap", tickers=(("UNI", "spot"),))
    make_token(registry, "uni-2", "Unichain Token", tickers=(("UNI", "other"),))
    with pytest.raises(ValueError, match="minted once|INV-1A-2"):
        make_token(registry, "uni-1", "Duplicate Slug")


def test_marker_other_requires_defining_string():
    with pytest.raises(ValueError, match="INV-1A-8"):
        DeploymentIdentity(
            deployment_id="x@y:OTHER",
            chain="csia:blockchain:z",
            marker_kind=DeploymentMarkerKind.OTHER,
            valid_from=NOW,
        )


def test_wrapped_deployment_status_distinguishes_canonical(registry):
    """ADV-1A-F: bridged->native transition is a status change with history."""
    base = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "base"))
    usdc = make_token(registry, "usdc-status", "USD Coin", otype=ObjectType.STABLECOIN)
    bridged = DeploymentIdentity(
        deployment_id=f"{usdc.object_id}@{base.object_id}:CONTRACT(0xold)",
        chain=base.object_id,
        marker_kind=DeploymentMarkerKind.CONTRACT,
        marker_value="0xold",
        status=DeploymentStatus.BRIDGED_REPRESENTATIVE,
        valid_from=NOW,
    )
    native = DeploymentIdentity(
        deployment_id=f"{usdc.object_id}@{base.object_id}:CONTRACT(0xnew)",
        chain=base.object_id,
        marker_kind=DeploymentMarkerKind.CONTRACT,
        marker_value="0xnew",
        status=DeploymentStatus.CANONICAL,
        valid_from=NOW + timedelta(days=365),
    )
    registry.attach_deployment(usdc.object_id, bridged)
    registry.attach_deployment(usdc.object_id, native)
    deps = registry.get(usdc.object_id).deployments
    assert {d.status for d in deps} == {
        DeploymentStatus.BRIDGED_REPRESENTATIVE,
        DeploymentStatus.CANONICAL,
    }  # both retained — transition represented, not overwritten
