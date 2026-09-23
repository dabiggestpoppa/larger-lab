"""Bloc 1A/1B pilot tests — the seven architecture pilots + USDC anchor.

Contract references: Book 1 plan v0.3 §1A/§1B; pilot stress matrix rows
P1–P7 + USDC cross-cutting anchor. These are executable tests, not prose.
"""

from __future__ import annotations

import pytest

from crypto_systems_intelligence_atlas.identity import (
    CanonicalObject,
    DeploymentIdentity,
    DeploymentMarkerKind,
    DeploymentStatus,
    ObjectType,
    RealizationIdentity,
    RealizationRoute,
    RealizationStatus,
    RepresentationMechanism,
    RouteHop,
    mint_object_id,
    mint_realization_id,
)
from crypto_systems_intelligence_atlas.ontology import RoleTag, validate_role_tags
from datetime import timedelta

from .conftest import NOW, contract_deployment, make_token, native_deployment


# --------------------------------------------------------------------------
# P1 — BITCOIN: no contract required; native BTC; no EVM assumptions
# --------------------------------------------------------------------------


def test_bitcoin_native_identity_no_contracts(registry):
    btc = make_token(registry, "btc", "Bitcoin", tickers=(("BTC", "spot"),))
    btc_chain = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "bitcoin"))
    registry.attach_deployment(btc.object_id, native_deployment(btc, btc_chain))

    obj = registry.get(btc.object_id)
    assert obj.deployments[0].marker_kind is DeploymentMarkerKind.NATIVE
    assert obj.deployments[0].marker_value is None  # no contract address exists
    # BTC the asset is not the chain: distinct objects, distinct ids
    assert obj.object_id != btc_chain.object_id
    assert obj.object_type is ObjectType.TOKEN
    assert btc_chain.object_type is ObjectType.BLOCKCHAIN


def test_bitcoin_pow_not_pos_tagged(registry):
    """E-1: security mechanism is data on edges, not class assumptions."""
    from crypto_systems_intelligence_atlas.relationships import (
        SecurityMechanism,
        TypedEdge,
        edge_spec,
    )
    from crypto_systems_intelligence_atlas.temporal import ClaimBinding

    btc_chain = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "bitcoin"))
    valsys = registry.mint(
        CanonicalObject(
            object_id=mint_object_id(ObjectType.VALIDATOR_SYSTEM, "bitcoin-miners"),
            object_type=ObjectType.VALIDATOR_SYSTEM,
            canonical_name="Bitcoin miner set",
            valid_from=NOW,
        )
    )
    edge = TypedEdge(
        edge_id="e1",
        edge_type=__import__(
            "crypto_systems_intelligence_atlas.relationships", fromlist=["EdgeType"]
        ).EdgeType.SECURED_BY,
        subject_id=btc_chain.object_id,
        object_id=valsys.object_id,
        mechanism=SecurityMechanism.POW,
        claim_binding=ClaimBinding(claim_id="c1", source_id="s1"),
        observed_at=NOW,
        valid_from=NOW,
    )
    assert edge.mechanism is SecurityMechanism.POW
    # and the dictionary demands a mechanism (IR-11)
    assert edge_spec(
        __import__(
            "crypto_systems_intelligence_atlas.relationships", fromlist=["EdgeType"]
        ).EdgeType.SECURED_BY
    ).requires_mechanism


# --------------------------------------------------------------------------
# P2 — ETHEREUM: Ethereum != ETH != EVM; L2 settles; token contracts distinct
# --------------------------------------------------------------------------


def test_ethereum_eth_evm_distinctions(registry):
    eth_chain = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "ethereum"))
    eth = make_token(registry, "eth", "Ether", tickers=(("ETH", "gas"),))
    evm = registry.mint(
        CanonicalObject(
            object_id=mint_object_id(ObjectType.VM, "evm"),
            object_type=ObjectType.VM,
            canonical_name="Ethereum Virtual Machine",
            valid_from=NOW,
        )
    )
    # three distinct objects: chain, native asset, VM
    assert len({eth_chain.object_id, eth.object_id, evm.object_id}) == 3

    usdc = make_token(
        registry, "usdc", "USD Coin", otype=ObjectType.STABLECOIN, tickers=(("USDC", "spot"),)
    )
    registry.attach_deployment(
        usdc.object_id,
        contract_deployment(
            usdc, eth_chain, "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
        ),
    )
    obj = registry.get(usdc.object_id)
    assert obj.deployments[0].marker_kind is DeploymentMarkerKind.CONTRACT
    # USDC is not ETH is not Ethereum
    assert obj.object_id != eth.object_id != eth_chain.object_id


def test_l2_settles_to_ethereum(registry):
    from crypto_systems_intelligence_atlas.relationships import (
        EdgeType,
        GraphValidator,
        TypedEdge,
    )
    from crypto_systems_intelligence_atlas.temporal import ClaimBinding

    eth_chain = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "ethereum"))
    arb = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "arbitrum"))
    validator = GraphValidator(registry)
    validator.add_edge(
        TypedEdge(
            edge_id="settle-1",
            edge_type=EdgeType.SETTLES_TO,
            subject_id=arb.object_id,
            object_id=eth_chain.object_id,
            claim_binding=ClaimBinding(claim_id="c2", source_id="s2"),
            observed_at=NOW,
            valid_from=NOW,
        )
    )
    # settlement must be a DAG (IR-4): validate no cycle
    assert validator.validate_acyclic(EdgeType.SETTLES_TO)


# --------------------------------------------------------------------------
# P3 — XRPL: XRP != XRPL; issued assets without ERC-20 assumptions
# --------------------------------------------------------------------------


def test_xrpl_issued_asset_issuer_account_marker(registry):
    """T-1A-11 (E-6): trustline issuance via ISSUER_ACCOUNT — no contracts."""
    xrpl = registry.require(mint_object_id(ObjectType.LEDGER, "xrpl"))
    xrp = make_token(registry, "xrp", "XRP", tickers=(("XRP", "native"),))
    registry.attach_deployment(xrp.object_id, native_deployment(xrp, xrpl))

    rlusd = make_token(registry, "rlusd", "RLUSD", tickers=(("RLUSD", "xrpl-issued"),))
    dep = DeploymentIdentity(
        deployment_id=f"{rlusd.object_id}@{xrpl.object_id}:ISSUER_ACCOUNT(rIssuer1)",
        chain=xrpl.object_id,
        marker_kind=DeploymentMarkerKind.ISSUER_ACCOUNT,
        marker_value="rIssuer1",
        valid_from=NOW,
    )
    registry.attach_deployment(rlusd.object_id, dep)
    obj = registry.get(rlusd.object_id)
    assert obj.deployments[0].marker_kind is DeploymentMarkerKind.ISSUER_ACCOUNT
    # XRP the token is not XRPL the ledger
    assert xrp.object_id != xrpl.object_id


# --------------------------------------------------------------------------
# P4 — SOLANA: program/mint identities, no EVM semantics
# --------------------------------------------------------------------------


def test_solana_program_and_mint_markers(registry):
    sol = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "solana"))
    wsol = make_token(registry, "wsol", "Wrapped SOL")
    program_dep = DeploymentIdentity(
        deployment_id=f"{wsol.object_id}@{sol.object_id}:PROGRAM(Prog9x)",
        chain=sol.object_id,
        marker_kind=DeploymentMarkerKind.PROGRAM,
        marker_value="Prog9x",
        valid_from=NOW,
    )
    registry.attach_deployment(wsol.object_id, program_dep)
    mint_dep = DeploymentIdentity(
        deployment_id=f"{wsol.object_id}@{sol.object_id}:MINT_ACCOUNT(So1111)",
        chain=sol.object_id,
        marker_kind=DeploymentMarkerKind.MINT_ACCOUNT,
        marker_value="So1111",
        valid_from=NOW,
    )
    registry.attach_deployment(wsol.object_id, mint_dep)
    obj = registry.get(wsol.object_id)
    kinds = {d.marker_kind for d in obj.deployments}
    assert kinds == {DeploymentMarkerKind.PROGRAM, DeploymentMarkerKind.MINT_ACCOUNT}
    # same object, two deployment identities on one chain — legal (multi-deployment)


def test_solana_svm_tag_no_evm(registry):
    sol = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "solana"))
    tagged = sol.model_copy(update={"role_tags": (RoleTag.SVM.value,)})
    validate_role_tags(tagged)  # must not raise
    # and a non-EVM chain is fully valid with NO tags at all (anti-EVM-bias)
    validate_role_tags(sol)


# --------------------------------------------------------------------------
# P5 — COSMOS: Hub != ATOM != IBC; multiple realizations; closure keeps history
# --------------------------------------------------------------------------


def _usdc(registry) -> CanonicalObject:
    usdc = make_token(
        registry, "usdc", "USD Coin", otype=ObjectType.STABLECOIN, tickers=(("USDC", "spot"),)
    )
    eth_chain = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "ethereum"))
    registry.attach_deployment(
        usdc.object_id,
        contract_deployment(
            usdc, eth_chain, "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
        ),
    )
    return usdc


def _realization(
    usdc: CanonicalObject,
    dest_chain: CanonicalObject,
    marker: str,
    denom: str,
    path: str,
    channels: list[str],
    mechanism: RepresentationMechanism = RepresentationMechanism.IBC,
) -> RealizationIdentity:
    return RealizationIdentity(
        realization_id=mint_realization_id(usdc.object_id, dest_chain.object_id, marker),
        canonical_asset_id=usdc.object_id,
        chain_id=dest_chain.object_id,
        local_asset_identifier=denom,
        representation_mechanism=mechanism,
        route=RealizationRoute(
            path=path,
            channel_sequence=channels,
            multi_hop_route=[
                RouteHop(chain_id=dest_chain.object_id, channel=ch)
                for ch in channels
            ],
        ),
        valid_from=NOW,
    )


def test_cosmos_distinctions(registry):
    hub = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "cosmos_hub"))
    atom = make_token(registry, "atom", "Atom", tickers=(("ATOM", "stake"),))
    ibc = registry.mint(
        CanonicalObject(
            object_id=mint_object_id(ObjectType.INTEROP_PROTOCOL, "ibc"),
            object_type=ObjectType.INTEROP_PROTOCOL,
            canonical_name="Inter-Blockchain Communication Protocol",
            valid_from=NOW,
        )
    )
    assert len({hub.object_id, atom.object_id, ibc.object_id}) == 3


def test_cosmos_multiple_realizations_same_asset(registry):
    """T-1A-13 / T-1C-14 (contractual, R-1A-5=C): many realizations, one asset."""
    usdc = _usdc(registry)
    osmosis = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "osmosis"))
    cosmos_hub = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "cosmos_hub"))

    r1 = _realization(usdc, osmosis, "ch20", "ibc/D189336", "channel-20", ["channel-20"])
    r2 = _realization(usdc, osmosis, "ch734", "ibc/other-hash", "channel-734", ["channel-734"])
    r3 = _realization(usdc, cosmos_hub, "ch1", "ibc/hub-hash", "channel-1", ["channel-1"])
    registry.attach_realization(usdc.object_id, r1)
    registry.attach_realization(usdc.object_id, r2)
    registry.attach_realization(usdc.object_id, r3)

    obj = registry.get(usdc.object_id)
    assert len(obj.realizations) == 3
    assert {r.realization_id for r in obj.realizations} == {
        r1.realization_id,
        r2.realization_id,
        r3.realization_id,
    }
    # distinct local denoms per channel on the SAME destination chain
    assert len({r.local_asset_identifier for r in obj.realizations if r.chain_id == osmosis.object_id}) == 2


def test_channel_closure_preserves_history(registry):
    usdc = _usdc(registry)
    osmosis = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "osmosis"))
    r1 = _realization(usdc, osmosis, "ch20", "ibc/D189336", "channel-20", ["channel-20"])
    r2 = _realization(usdc, osmosis, "ch734", "ibc/other-hash", "channel-734", ["channel-734"])
    registry.attach_realization(usdc.object_id, r1)
    registry.attach_realization(usdc.object_id, r2)

    # channel-20 closes: world-change on ONE realization only
    later = NOW + timedelta(days=30)
    closed = r1.model_copy(
        update={"status": RealizationStatus.CLOSED, "valid_to": later}
    )
    assert closed.status is RealizationStatus.CLOSED
    obj = registry.get(usdc.object_id)
    obj.realizations = tuple(
        closed if r.realization_id == r1.realization_id else r for r in obj.realizations
    )
    by_id = {r.realization_id: r for r in obj.realizations}
    assert by_id[r1.realization_id].valid_to == later  # history kept, not deleted
    assert by_id[r2.realization_id].valid_to is None  # other channel unaffected


def test_multihop_route_representation(registry):
    usdc = _usdc(registry)
    osmosis = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "osmosis"))
    hub = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "cosmos_hub"))
    multi = RealizationIdentity(
        realization_id=mint_realization_id(usdc.object_id, osmosis.object_id, "multihop"),
        canonical_asset_id=usdc.object_id,
        chain_id=osmosis.object_id,
        local_asset_identifier="ibc/via-hub",
        representation_mechanism=RepresentationMechanism.IBC,
        route=RealizationRoute(
            path="eth-hub-osmo",
            channel_sequence=["channel-0", "channel-141"],
            multi_hop_route=[
                RouteHop(chain_id=hub.object_id, channel="channel-0", port="transfer"),
                RouteHop(chain_id=osmosis.object_id, channel="channel-141", port="transfer"),
            ],
        ),
        valid_from=NOW,
    )
    registry.attach_realization(usdc.object_id, multi)
    r = registry.get(usdc.object_id).realizations[-1]
    assert len(r.route.multi_hop_route) == 2  # multi-hop lives at record level
    assert r.route.channel_sequence == ["channel-0", "channel-141"]


# --------------------------------------------------------------------------
# P6 — ICP: canisters/subnets without EVM contract assumptions
# --------------------------------------------------------------------------


def test_icp_canister_marker_and_subnet_scope(registry):
    icp = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "icp"))
    ckbtc = make_token(registry, "ckbtc", "ckBTC")
    dep = DeploymentIdentity(
        deployment_id=f"{ckbtc.object_id}@{icp.object_id}:CANISTER(canister-id-1)",
        chain=icp.object_id,
        marker_kind=DeploymentMarkerKind.CANISTER,
        marker_value="canister-id-1",
        valid_from=NOW,
    )
    registry.attach_deployment(ckbtc.object_id, dep)
    obj = registry.get(ckbtc.object_id)
    assert obj.deployments[0].marker_kind is DeploymentMarkerKind.CANISTER

    # E-10: RUNS_ON/VALIDATED_BY subnet chain_scope
    from crypto_systems_intelligence_atlas.relationships import (
        ChainScope,
        ChainScopeKind,
        EdgeType,
        GraphValidator,
        TypedEdge,
    )
    from crypto_systems_intelligence_atlas.temporal import ClaimBinding

    app = registry.mint(
        CanonicalObject(
            object_id=mint_object_id(ObjectType.APPLICATION, "icp-app"),
            object_type=ObjectType.APPLICATION,
            canonical_name="ICP app",
            valid_from=NOW,
        )
    )
    v = GraphValidator(registry)
    v.add_edge(
        TypedEdge(
            edge_id="runs-subnet",
            edge_type=EdgeType.RUNS_ON,
            subject_id=app.object_id,
            object_id=icp.object_id,
            chain_scope=ChainScope(kind=ChainScopeKind.SUBNET, scope_ref="subnet-abc"),
            claim_binding=ClaimBinding(claim_id="c3", source_id="s3"),
            observed_at=NOW,
            valid_from=NOW,
        )
    )
    assert v.edge("runs-subnet").chain_scope.kind is ChainScopeKind.SUBNET


# --------------------------------------------------------------------------
# P7 — DAG-family pilot: no forced linear-block assumption
# --------------------------------------------------------------------------


def test_dag_network_role_tags_not_a_special_class(registry):
    """A DAG network is a BLOCKCHAIN with DAG role tag + finality slot — not a
    new primary class, not 'a chain with weird consensus' (§9.1, ADV-1B-J)."""
    dag = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "dag_pilot"))
    tagged = dag.model_copy(
        update={
            "role_tags": (
                RoleTag.DAG.value,
                RoleTag.HASHGRAPH_BFT.value,
            )
        }
    )
    validate_role_tags(tagged)
    assert tagged.object_type is ObjectType.BLOCKCHAIN  # class unchanged


def test_dag_finality_device_slot_reserved(registry):
    """T-1B-8 (E-12): slot accepts reserved values, rejects unregistered."""
    from crypto_systems_intelligence_atlas.ontology import (
        ArchitectureSlot,
        FamilySlotRegistry,
    )

    slots = FamilySlotRegistry()
    reserved = slots.reserved_values(ArchitectureSlot.FINALITY_DEVICE)
    assert "DECLARATIVE_DAG" in reserved
    slots.declare(ArchitectureSlot.FINALITY_DEVICE, "dag-pilot", "DECLARATIVE_DAG")
    with pytest.raises(ValueError):
        slots.declare(ArchitectureSlot.FINALITY_DEVICE, "dag-pilot", "NOT_A_DEVICE")


# --------------------------------------------------------------------------
# USDC cross-cutting anchor: canonical aggregation + deployment/realization split
# --------------------------------------------------------------------------


def test_usdc_native_bridged_realization_coexistence(registry):
    """ADV-1A-N: canonical + native deployment + custodial bridge + realizations
    coexist without conflation."""
    usdc = _usdc(registry)  # native CONTRACT deployment on Ethereum
    base = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "base"))
    osmosis = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "osmosis"))

    # native USDC on Base (canonical deployment, contract marker)
    registry.attach_deployment(
        usdc.object_id,
        contract_deployment(
            usdc, base, "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
        ),
    )
    # bridged representative on some chain (WRAPS-style custodial)
    solana = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "solana"))
    bridged = DeploymentIdentity(
        deployment_id=f"{usdc.object_id}@{solana.object_id}:CONTRACT(bridged-usdc-mint)",
        chain=solana.object_id,
        marker_kind=DeploymentMarkerKind.CONTRACT,
        marker_value="bridged-usdc-mint",
        status=DeploymentStatus.BRIDGED_REPRESENTATIVE,
        valid_from=NOW,
    )
    registry.attach_deployment(usdc.object_id, bridged)
    # IBC realization on Osmosis
    registry.attach_realization(
        usdc.object_id,
        _realization(usdc, osmosis, "ch20", "ibc/D189336", "channel-20", ["channel-20"]),
    )

    obj = registry.get(usdc.object_id)
    assert len(obj.deployments) == 3  # Ethereum native + Base native + Solana bridged
    assert len(obj.realizations) == 1
    assert obj.realizations[0].canonical_asset_id == usdc.object_id


def test_realization_is_not_a_deployment_and_not_an_asset(registry):
    """INV-1B-8 / INV-1A-9 enforcement."""
    usdc = _usdc(registry)
    osmosis = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "osmosis"))
    real = _realization(usdc, osmosis, "ch20", "ibc/D189336", "channel-20", ["channel-20"])
    registry.attach_realization(usdc.object_id, real)

    # cannot attach a realization to a REALIZATION object (no chains)
    fake_real_object = CanonicalObject(
        object_id=mint_object_id(ObjectType.REALIZATION, "fake"),
        object_type=ObjectType.REALIZATION,
        canonical_name="fake",
        valid_from=NOW,
    )
    registry.mint(fake_real_object)
    with pytest.raises(ValueError, match="INV-1A-9"):
        registry.attach_realization(
            fake_real_object.object_id,
            _realization(fake_real_object, osmosis, "x", "denom", "p", ["c"]),
        )


def test_two_paths_one_destination_distinct_realizations(registry):
    """ADV-1A-O: two distinct paths to the same destination stay distinct."""
    usdc = _usdc(registry)
    osmosis = registry.require(mint_object_id(ObjectType.BLOCKCHAIN, "osmosis"))
    r_direct = _realization(usdc, osmosis, "direct", "ibc/direct", "path-direct", ["channel-20"])
    r_multihop = _realization(usdc, osmosis, "via-hub", "ibc/via-hub", "path-via-hub", ["channel-0", "channel-141"])
    assert r_direct.realization_id != r_multihop.realization_id
    assert r_direct.route.path != r_multihop.route.path
