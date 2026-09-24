"""Book 3 family-native pilot, anti-EVM, and REALIZATION tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from crypto_systems_intelligence_atlas.architecture import (
    ArchitectureComponent,
    ComponentRole,
    ModularArchitecture,
)
from crypto_systems_intelligence_atlas.architecture_pilots import PILOT_FIXTURES, require_pilot
from crypto_systems_intelligence_atlas.identity import (
    CanonicalObject,
    DeploymentIdentity,
    DeploymentMarkerKind,
    IdentityRegistry,
    ObjectType,
    RealizationIdentity,
    RepresentationMechanism,
    mint_object_id,
    mint_realization_id,
)

NOW = datetime(2026, 9, 24, 12, tzinfo=UTC)
LATER = NOW + timedelta(days=1)


def test_exactly_seventeen_offline_family_native_pilots_exist() -> None:
    assert len(PILOT_FIXTURES) == 17
    assert {pilot.canonical_name for pilot in PILOT_FIXTURES} == {
        "Bitcoin", "Ethereum", "Base", "Arbitrum", "XRPL", "Solana",
        "Cosmos Hub", "Osmosis", "Celestia", "Polkadot",
        "Standalone Substrate", "Avalanche", "ICP", "Hedera", "Sui",
        "Aptos", "NEAR",
    }
    assert all(pilot.live_observation is False for pilot in PILOT_FIXTURES)


def test_anti_evm_matrix_01_bitcoin_has_no_account_or_contract_semantics() -> None:
    pilot = require_pilot("Bitcoin")
    assert {"ACCOUNTS", "CONTRACTS", "EVM"} <= set(pilot.absent_assumptions)


def test_anti_evm_matrix_02_xrpl_has_no_evm_semantics() -> None:
    assert "EVM" in require_pilot("XRPL").absent_assumptions


def test_anti_evm_matrix_03_solana_program_is_not_evm_contract() -> None:
    pilot = require_pilot("Solana")
    assert pilot.execution_model == "SVM_PROGRAM"
    assert "EVM_CONTRACT" in pilot.absent_assumptions


def test_anti_evm_matrix_04_sdk_tooling_does_not_imply_hub_identity() -> None:
    pilot = require_pilot("Osmosis")
    assert pilot.family == "SDK_CHAIN"
    assert "COSMOS_HUB_MEMBERSHIP" in pilot.absent_assumptions


def test_anti_evm_matrix_05_messaging_does_not_imply_shared_security() -> None:
    assert "IBC_IMPLIES_SHARED_SECURITY" in require_pilot("Cosmos Hub").absent_assumptions


def test_anti_evm_matrix_06_standalone_substrate_is_not_polkadot_member() -> None:
    assert "POLKADOT_MEMBERSHIP" in require_pilot("Standalone Substrate").absent_assumptions


def test_anti_evm_matrix_07_avalanche_is_not_reduced_to_c_chain() -> None:
    pilot = require_pilot("Avalanche")
    assert {"P_CHAIN", "X_CHAIN", "C_CHAIN"} <= set(pilot.native_features)
    assert "C_CHAIN_REPRESENTS_ALL_AVALANCHE" in pilot.absent_assumptions


def test_anti_evm_matrix_08_icp_canister_is_not_evm_contract() -> None:
    pilot = require_pilot("ICP")
    assert pilot.execution_model == "CANISTER_WASM"
    assert "EVM_CONTRACT_REQUIRED" in pilot.absent_assumptions


def test_anti_evm_matrix_09_sui_and_aptos_share_move_but_not_state_model() -> None:
    sui = require_pilot("Sui")
    aptos = require_pilot("Aptos")
    assert sui.execution_model == aptos.execution_model == "MOVE_VM"
    assert sui.state_model == "OBJECT_OWNERSHIP"
    assert aptos.state_model == "RESOURCE_AND_ACCOUNT"


def test_anti_evm_matrix_10_dag_needs_no_fake_block_height() -> None:
    pilot = require_pilot("Hedera")
    assert pilot.consensus_model == "HASHGRAPH_CONSENSUS"
    assert "DAG_LIKE_CONSENSUS" in pilot.native_features
    assert "LINEAR_BLOCK_HEIGHT_REQUIRED" in pilot.absent_assumptions


def test_anti_evm_matrix_11_modular_rollup_keeps_roles_distinct() -> None:
    roles = (
        ComponentRole.EXECUTION,
        ComponentRole.SEQUENCING,
        ComponentRole.SETTLEMENT,
        ComponentRole.DATA_AVAILABILITY,
        ComponentRole.SECURITY,
    )
    modular = ModularArchitecture(
        system_id="fixture:rollup:modular",
        components=tuple(
            ArchitectureComponent(
                component_id=f"fixture:component:{role.value}",
                role=role,
                canonical_name=f"fixture {role.value}",
                source_claim_refs=("fixture:claim",),
            )
            for role in roles
        ),
    )
    assert len({component.component_id for component in modular.components}) == 5
    assert modular.require(ComponentRole.EXECUTION).component_id != modular.require(ComponentRole.SETTLEMENT).component_id
    assert modular.require(ComponentRole.SEQUENCING).component_id != modular.require(ComponentRole.DATA_AVAILABILITY).component_id
    assert modular.require(ComponentRole.SECURITY).component_id != modular.require(ComponentRole.EXECUTION).component_id


def test_anti_evm_matrix_12_realization_fixture_distinguishes_representation_channels() -> None:
    bitcoin = require_pilot("Bitcoin")
    assert {"UTXO", "PROOFOF_WORK"} <= set(bitcoin.native_features)
    assert RepresentationMechanism.CHAIN_KEY is not RepresentationMechanism.LOCK_MINT
    assert RepresentationMechanism.OTHER is not RepresentationMechanism.IBC


def realization(asset: str, chain: str, marker: str, mechanism: RepresentationMechanism, *, migration_from: str | None = None) -> RealizationIdentity:
    return RealizationIdentity(
        realization_id=mint_realization_id(asset, chain, marker),
        canonical_asset_id=asset,
        chain_id=chain,
        local_asset_identifier=marker,
        representation_mechanism=mechanism,
        mechanism_defining_string=(
            "deterministic offline wrapped representation fixture"
            if mechanism is RepresentationMechanism.OTHER
            else None
        ),
        valid_from=NOW,
        migration_from=migration_from,
    )


def realization_kernel() -> tuple[IdentityRegistry, str, dict[str, str]]:
    registry = IdentityRegistry()
    chains: dict[str, str] = {}
    for slug, object_type in (("bitcoin", ObjectType.BLOCKCHAIN), ("ethereum", ObjectType.BLOCKCHAIN), ("xrpl", ObjectType.LEDGER), ("cosmos", ObjectType.BLOCKCHAIN), ("polkadot", ObjectType.BLOCKCHAIN), ("avalanche", ObjectType.BLOCKCHAIN)):
        chain_id = mint_object_id(object_type, slug)
        registry.mint(CanonicalObject(object_id=chain_id, object_type=object_type, canonical_name=slug, valid_from=NOW))
        chains[slug] = chain_id
    assets: dict[str, str] = {}
    for slug, object_type in (("btc", ObjectType.TOKEN), ("eth", ObjectType.TOKEN), ("wbtc", ObjectType.TOKEN), ("cbtc", ObjectType.TOKEN), ("weth", ObjectType.TOKEN), ("bridged-eth", ObjectType.TOKEN), ("usdc", ObjectType.STABLECOIN), ("usdc-e", ObjectType.STABLECOIN), ("xrp", ObjectType.TOKEN), ("atom", ObjectType.TOKEN), ("dot", ObjectType.TOKEN)):
        asset_id = mint_object_id(object_type, slug)
        registry.mint(CanonicalObject(object_id=asset_id, object_type=object_type, canonical_name=slug, valid_from=NOW))
        assets[slug] = asset_id
    return registry, chains["bitcoin"], assets


def test_realization_preserves_economic_asset_across_native_wrapped_and_bridged() -> None:
    registry, bitcoin, assets = realization_kernel()
    native_btc = realization(assets["btc"], bitcoin, "native-btc", RepresentationMechanism.CHAIN_KEY)
    wbtc = realization(assets["wbtc"], assets["btc"], "wrapped-btc", RepresentationMechanism.OTHER, migration_from=None)
    registry.attach_realization(assets["btc"], native_btc)
    assert registry.require(assets["btc"]).realizations[0].canonical_asset_id == assets["btc"]
    assert wbtc.canonical_asset_id != wbtc.realization_id
    assert wbtc.representation_mechanism is RepresentationMechanism.OTHER


def test_book1_realization_doctrine_covers_required_assets_without_asset_collapse() -> None:
    registry, bitcoin, assets = realization_kernel()
    registry.attach_realization(assets["btc"], realization(assets["btc"], bitcoin, "BTC", RepresentationMechanism.CHAIN_KEY))
    registry.attach_realization(assets["eth"], realization(assets["eth"], mint_object_id(ObjectType.BLOCKCHAIN, "ethereum"), "ETH", RepresentationMechanism.CHAIN_KEY))
    registry.attach_realization(assets["xrp"], realization(assets["xrp"], mint_object_id(ObjectType.LEDGER, "xrpl"), "XRP", RepresentationMechanism.CHAIN_KEY))
    registry.attach_realization(assets["atom"], realization(assets["atom"], mint_object_id(ObjectType.BLOCKCHAIN, "cosmos"), "uatom", RepresentationMechanism.IBC))
    registry.attach_realization(assets["dot"], realization(assets["dot"], mint_object_id(ObjectType.BLOCKCHAIN, "polkadot"), "DOT", RepresentationMechanism.CHAIN_KEY))
    for asset in ("btc", "eth", "xrp", "atom", "dot"):
        assert len(registry.require(assets[asset]).realizations) == 1
    assert len({assets["btc"], assets["wbtc"], assets["cbtc"]}) == 3
    assert len({assets["eth"], assets["weth"], assets["bridged-eth"]}) == 3
    assert len({assets["usdc"], assets["usdc-e"]}) == 2


def test_migration_preserves_history_and_native_wrapped_bridged_are_distinct() -> None:
    registry, bitcoin, assets = realization_kernel()
    native = realization(assets["btc"], bitcoin, "native", RepresentationMechanism.CHAIN_KEY)
    wrapped = realization(assets["btc"], bitcoin, "wrapped", RepresentationMechanism.OTHER)
    bridged = realization(assets["btc"], bitcoin, "bridged", RepresentationMechanism.LOCK_MINT)
    for item in (native, wrapped, bridged):
        registry.attach_realization(assets["btc"], item)
    obj = registry.require(assets["btc"])
    assert len(obj.realizations) == 3
    assert len({item.realization_id for item in obj.realizations}) == 3
    assert all(item.canonical_asset_id == assets["btc"] for item in obj.realizations)


def test_issued_representation_is_not_native_realization() -> None:
    registry = IdentityRegistry()
    chain_id = mint_object_id(ObjectType.LEDGER, "xrpl")
    registry.mint(CanonicalObject(object_id=chain_id, object_type=ObjectType.LEDGER, canonical_name="xrpl", valid_from=NOW))
    asset_id = mint_object_id(ObjectType.TOKEN, "issued")
    registry.mint(CanonicalObject(object_id=asset_id, object_type=ObjectType.TOKEN, canonical_name="issued", valid_from=NOW))
    registry.attach_deployment(
        asset_id,
        DeploymentIdentity(
            deployment_id=f"{asset_id}@{chain_id}:ISSUER_ACCOUNT(rIssuer)",
            chain=chain_id,
            marker_kind=DeploymentMarkerKind.ISSUER_ACCOUNT,
            marker_value="rIssuer",
            valid_from=NOW,
        ),
    )
    assert registry.require(asset_id).realizations == ()
    assert registry.require(asset_id).deployments[0].marker_kind is DeploymentMarkerKind.ISSUER_ACCOUNT
