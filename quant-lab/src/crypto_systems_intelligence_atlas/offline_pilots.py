"""Deterministic offline Book 4 pilot fixture catalogue; never live facts."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class OfflinePilotFixture(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    pilot_id: str = Field(min_length=1)
    family: str = Field(min_length=1)
    system_ref: str = Field(min_length=1)
    roles: tuple[str, ...] = Field(min_length=1)
    relation_families: tuple[str, ...] = ()
    fixture_only: bool = True
    live_current_claim: bool = False

    @property
    def is_deterministic_offline_fixture(self) -> bool:
        return self.fixture_only and not self.live_current_claim


OFFLINE_PILOTS: tuple[OfflinePilotFixture, ...] = tuple(
    OfflinePilotFixture(
        pilot_id=pilot_id,
        family=family,
        system_ref=f"fixture:{pilot_id}",
        roles=roles,
        relation_families=relations,
    )
    for pilot_id, family, roles, relations in (
        ("chainlink-like-oracle", "ORACLE", ("ORACLE_NETWORK", "DATA_PUBLISHER", "FEED"), ("ORACLE_FOR", "DATA_FROM")),
        ("pyth-like-publisher", "ORACLE", ("DATA_PUBLISHER", "PRICE_FEED", "ATTESTATION_SERVICE"), ("ORACLE_FOR", "DATA_FROM")),
        ("ibc-like-route", "INTEROPERABILITY", ("MESSAGE_TRANSPORT", "CHANNEL", "RELAYER_LAYER"), ("MESSAGES_TO", "BRIDGES_TO")),
        ("ccip-like-route", "MESSAGING", ("MESSAGE_TRANSPORT", "ENDPOINT", "RELAYER_LAYER"), ("MESSAGES_TO",)),
        ("layerzero-like-route", "MESSAGING", ("ENDPOINT", "MESSAGE_TRANSPORT"), ("MESSAGES_TO",)),
        ("wormhole-like-route", "GUARDIAN", ("GUARDIAN_VERIFIER", "MESSAGE_TRANSPORT"), ("MESSAGES_TO", "BRIDGES_TO")),
        ("axelar-like-route", "VALIDATOR_GATEWAY", ("VALIDATOR_VERIFIER", "RELAYER_LAYER"), ("MESSAGES_TO", "BRIDGES_TO")),
        ("celestia-like-da", "DA", ("DA_NETWORK", "DA_PROVIDER", "BLOB_DATA_PUBLICATION"), ("USES_DA",)),
        ("eigenda-like-da", "DA", ("DA_NETWORK", "DA_PROVIDER", "SAMPLING_AVAILABILITY_MECHANISM"), ("USES_DA",)),
        ("avail-like-da", "DA", ("DA_NETWORK", "DA_PROVIDER", "RETRIEVAL_SERVICE"), ("USES_DA",)),
        ("ethereum-native-da-like", "DA", ("DA_NETWORK", "BLOB_DATA_PUBLICATION", "RETRIEVAL_SERVICE"), ("USES_DA",)),
        ("alchemy-like-rpc", "RPC", ("RPC_PROVIDER", "NODE_INFRASTRUCTURE"), ("DEPENDS_ON",)),
        ("infura-like-rpc", "RPC", ("RPC_PROVIDER", "NODE_INFRASTRUCTURE"), ("DEPENDS_ON",)),
        ("quicknode-like-rpc", "RPC", ("RPC_PROVIDER", "NODE_INFRASTRUCTURE"), ("DEPENDS_ON",)),
        ("the-graph-like-indexer", "INDEXING", ("INDEXER", "DATA_API"), ("DATA_FROM", "DEPENDS_ON")),
        ("sdk-build-time", "BUILD", ("SDK", "FRAMEWORK", "DEVELOPER_TOOL"), ("BUILT_WITH",)),
        ("canonical-rollup-bridge", "ROLLUP", ("CANONICAL_BRIDGE", "SEQUENCER", "DA_PROVIDER", "SETTLEMENT_LAYER"), ("SETTLES_TO", "USES_DA", "SEQUENCED_BY")),
        ("third-party-asset-bridge", "BRIDGE", ("ASSET_BRIDGE", "LIQUIDITY_BRIDGE", "MESSAGE_TRANSPORT"), ("BRIDGES_TO", "MESSAGES_TO")),
    )
)


__all__ = ["OFFLINE_PILOTS", "OfflinePilotFixture"]
