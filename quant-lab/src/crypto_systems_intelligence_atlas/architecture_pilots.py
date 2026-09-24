"""CSIA Book 3 — deterministic offline family-native pilot fixtures.

These are test fixtures, not live observations.  They encode only the
architecture distinctions needed to exercise the ratified anti-EVM matrix.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ArchitecturePilot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    fixture_id: str = Field(min_length=1)
    canonical_name: str = Field(min_length=1)
    family: str = Field(min_length=1)
    execution_model: str = Field(min_length=1)
    state_model: str = Field(min_length=1)
    consensus_model: str = Field(min_length=1)
    native_features: tuple[str, ...] = Field(min_length=1)
    absent_assumptions: tuple[str, ...] = ()
    component_roles: tuple[str, ...] = ()
    live_observation: bool = False

    @classmethod
    def make(cls, slug: str, name: str, family: str, execution: str, state: str, consensus: str, features: tuple[str, ...], absent: tuple[str, ...] = (), components: tuple[str, ...] = ()) -> "ArchitecturePilot":
        return cls(
            fixture_id=f"fixture:architecture:{slug}",
            canonical_name=name,
            family=family,
            execution_model=execution,
            state_model=state,
            consensus_model=consensus,
            native_features=features,
            absent_assumptions=absent,
            component_roles=components,
        )


PILOT_FIXTURES: tuple[ArchitecturePilot, ...] = (
    ArchitecturePilot.make("bitcoin", "Bitcoin", "UTXO", "UTXO_SCRIPT", "UTXO", "POW", ("UTXO", "SATOSHI", "PROOFOF_WORK"), ("ACCOUNTS", "CONTRACTS", "EVM", "POS", "SEQUENCERS", "SEPARATE_DA")),
    ArchitecturePilot.make("ethereum", "Ethereum", "ACCOUNT_STATE", "EVM", "WORLD_STATE", "POS_BFT", ("ACCOUNTS", "SMART_CONTRACTS", "EVM"), ("BLOCK_HEIGHT_REQUIRED_FOR_IDENTITY",)),
    ArchitecturePilot.make("base", "Base", "ROLLUP", "EVM", "L2_STATE", "ROLLUP_SEQUENCER", ("EVM", "SEQUENCER", "SETTLEMENT_TO_ETHEREUM", "EXTERNAL_DA"), ("NATIVE_IDENTITY_IS_ETHEREUM",)),
    ArchitecturePilot.make("arbitrum", "Arbitrum", "ROLLUP", "EVM", "L2_STATE", "ROLLUP_SEQUENCER", ("EVM", "SEQUENCER", "SETTLEMENT_TO_ETHEREUM", "EXTERNAL_DA")),
    ArchitecturePilot.make("xrpl", "XRPL", "LEDGER", "TRANSACTION_LEDGER", "ACCOUNT_STATE_LEDGER", "FEDERATED_CONSENSUS", ("LEDGERS", "TRUSTLINES", "ISSUER_ACCOUNTS"), ("EVM", "SMART_CONTRACTS_REQUIRED", "POS_REQUIRED")),
    ArchitecturePilot.make("solana", "Solana", "ACCOUNT_STATE", "SVM_PROGRAM", "ACCOUNTS_AND_PROGRAMS", "POS_BFT", ("PROGRAMS", "ACCOUNTS", "SVM"), ("EVM_CONTRACT", "BLOCK_REQUIRED_FOR_PROGRAM")),
    ArchitecturePilot.make("cosmos-hub", "Cosmos Hub", "SDK_CHAIN", "ABCI", "MULTISTORE", "TENDERMINT_BFT", ("POS", "STAKING", "IBC", "GOVERNANCE"), ("IBC_IMPLIES_SHARED_SECURITY", "SDK_TOOLING_IS_IDENTITY")),
    ArchitecturePilot.make("osmosis", "Osmosis", "SDK_CHAIN", "ABCI", "MULTISTORE", "TENDERMINT_BFT", ("POS", "IBC", "OSMOSIS_SPECIFIC_IDENTITY"), ("COSMOS_HUB_MEMBERSHIP",)),
    ArchitecturePilot.make("celestia", "Celestia", "DA_CHAIN", "ABCI", "DATA_ROOT_NAMESPACE", "TENDERMINT_BFT", ("DATA_AVAILABILITY", "DATA_ROOT", "POS"), ("EXECUTION_REQUIRED", "SMART_CONTRACTS_REQUIRED")),
    ArchitecturePilot.make("polkadot", "Polkadot", "PARACHAIN_COLLATION", "RUNTIME_WASM", "RUNTIME_STORAGE", "HYBRID_GRANDPA_BFT", ("RUNTIME_UPGRADES", "SHARED_SECURITY", "PARACHAINS"), ("ALL_PARACHAINS_IDENTICAL",)),
    ArchitecturePilot.make("standalone-substrate", "Standalone Substrate", "SOVEREIGN_SUBSTRATE", "RUNTIME_WASM", "RUNTIME_STORAGE", "CONFIGURABLE_CONSENSUS", ("RUNTIME_UPGRADES", "NATIVE_VALIDATOR_SET"), ("POLKADOT_MEMBERSHIP",)),
    ArchitecturePilot.make("avalanche", "Avalanche", "MULTI_SUBNET", "EVM_AND_NATIVE_VMS", "SUBNET_STATES", "AVALANCHE_CONSENSUS", ("MULTIPLE_SUBNETS", "C_CHAIN", "P_CHAIN", "X_CHAIN"), ("C_CHAIN_REPRESENTS_ALL_AVALANCHE",)),
    ArchitecturePilot.make("icp", "ICP", "INTERNET_COMPUTER", "CANISTER_WASM", "CANISTER_STATE", "INTERNET_COMPUTER_CONSENSUS", ("CANISTERS", "SUBNET_MESSAGING", "REQUEST_RESPONSE"), ("EVM_CONTRACT_REQUIRED", "ACCOUNT_ONLY_REQUIRED")),
    ArchitecturePilot.make("hedera", "Hedera", "ACCOUNT_STATE", "HEDERA_SMART_CONTRACT", "ACCOUNT_STATE", "HASHGRAPH_CONSENSUS", ("ACCOUNTS", "TOKENS", "DAG_LIKE_CONSENSUS", "HCS"), ("EVM_REQUIRED", "POS_REQUIRED", "LINEAR_BLOCK_HEIGHT_REQUIRED")),
    ArchitecturePilot.make("sui", "Sui", "OBJECT_STATE", "MOVE_VM", "OBJECT_OWNERSHIP", "POS_BFT", ("OBJECT_MODEL", "MOVE", "PARALLEL_EXECUTION"), ("EVM_CONTRACT", "ACCOUNT_STORAGE_EQUIVALENCE")),
    ArchitecturePilot.make("aptos", "Aptos", "RESOURCE_STATE", "MOVE_VM", "RESOURCE_AND_ACCOUNT", "APTOS_BFT", ("RESOURCE_MODEL", "MOVE", "ACCOUNTS"), ("SUI_STATE_MODEL", "EVM_CONTRACT")),
    ArchitecturePilot.make("near", "NEAR", "ACCOUNT_STATE", "WASM", "ACCOUNT_STATE", "NIGHTWATCH", ("SHARDS", "WASM", "ACCOUNTS"), ("EVM", "BLOCK_HEIGHT_AS_IDENTITY")),
)

PILOTS_BY_NAME = {pilot.canonical_name: pilot for pilot in PILOT_FIXTURES}


def require_pilot(name: str) -> ArchitecturePilot:
    try:
        return PILOTS_BY_NAME[name]
    except KeyError as exc:
        raise KeyError(f"unknown architecture pilot {name}") from exc


__all__ = ["ArchitecturePilot", "PILOTS_BY_NAME", "PILOT_FIXTURES", "require_pilot"]
