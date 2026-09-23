"""CSIA Book 1 — Bloc 1B: Node ontology kernel.

Implements the ratified primary/role separation doctrine (Constitution §9.1,
plan v0.3 §1B): one primary class per node (INV-1B-1), many role tags that
never substitute for the class (INV-1B-2), family extension slots that extend
but never overwrite core slots (INV-1B-5), and the definition requirement
(INV-1B-6). Registry values come from the ratified plan; slot VALUE
population is Book 3B (INV-1B-7: reserve, don't declare).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .identity import CanonicalObject, ObjectType
from .temporal import UnknownBound


class RoleTag(str, Enum):
    """Role-tag registry (plan v0.1 §1B.6 + v0.2 additions).

    Architecture roles tag BLOCKCHAIN/LEDGER objects; functional roles tag
    PROTOCOL-class and similar objects. Tags never change primary class
    (INV-1B-2). Architecture-shaped items are tags, not classes (§9.1).
    """

    # -- architecture roles (on BLOCKCHAIN/LEDGER) --
    ROLLUP_OPTIMISTIC = "ROLLUP_OPTIMISTIC"
    ROLLUP_ZK = "ROLLUP_ZK"
    VALIDIUM = "VALIDIUM"
    L3 = "L3"
    SIDECHAIN = "SIDECHAIN"
    APPCHAIN = "APPCHAIN"
    DAG = "DAG"
    MODULAR = "MODULAR"
    MONOLITHIC = "MONOLITHIC"
    UTXO = "UTXO"
    EUTXO = "EUTXO"
    ACCOUNT = "ACCOUNT"
    EVM = "EVM"
    SVM = "SVM"
    MOVE_VM = "MOVE_VM"
    WASM_VM = "WASM_VM"
    CANISTER_COMPUTE = "CANISTER_COMPUTE"
    ACTOR_MODEL = "ACTOR_MODEL"
    HASHGRAPH_BFT = "HASHGRAPH_BFT"
    BRAIDED_POW = "BRAIDED_POW"
    PURE_POS_INSTANT_FINALITY = "PURE_POS_INSTANT_FINALITY"
    SHIELDED_POOL = "SHIELDED_POOL"
    PERMISSIONED = "PERMISSIONED"
    SUBSTRATE_RELAY = "SUBSTRATE_RELAY"
    IBC_SOVEREIGN = "IBC_SOVEREIGN"
    STATE_CHANNEL = "STATE_CHANNEL"  # E-2 / C-5

    # -- functional roles (on PROTOCOL-class etc.) --
    LIQUIDITY_ROUTER = "LIQUIDITY_ROUTER"
    DATA_DELIVERY = "DATA_DELIVERY"
    CROSS_CHAIN_MESSAGING = "CROSS_CHAIN_MESSAGING"
    AUTOMATION = "AUTOMATION"
    PROOF_OF_RESERVE = "PROOF_OF_RESERVE"
    MEV_INFRASTRUCTURE = "MEV_INFRASTRUCTURE"  # E-7 clarification: no family params
    COLLATERAL_HUB = "COLLATERAL_HUB"
    YIELD_AGGREGATOR = "YIELD_AGGREGATOR"
    PAYMENT_RAIL = "PAYMENT_RAIL"
    SETTLEMENT_ASSET = "SETTLEMENT_ASSET"


_ARCHITECTURE_ROLES = frozenset(
    {
        RoleTag.ROLLUP_OPTIMISTIC,
        RoleTag.ROLLUP_ZK,
        RoleTag.VALIDIUM,
        RoleTag.L3,
        RoleTag.SIDECHAIN,
        RoleTag.APPCHAIN,
        RoleTag.DAG,
        RoleTag.MODULAR,
        RoleTag.MONOLITHIC,
        RoleTag.UTXO,
        RoleTag.EUTXO,
        RoleTag.ACCOUNT,
        RoleTag.EVM,
        RoleTag.SVM,
        RoleTag.MOVE_VM,
        RoleTag.WASM_VM,
        RoleTag.CANISTER_COMPUTE,
        RoleTag.ACTOR_MODEL,
        RoleTag.HASHGRAPH_BFT,
        RoleTag.BRAIDED_POW,
        RoleTag.PURE_POS_INSTANT_FINALITY,
        RoleTag.SHIELDED_POOL,
        RoleTag.PERMISSIONED,
        RoleTag.SUBSTRATE_RELAY,
        RoleTag.IBC_SOVEREIGN,
        RoleTag.STATE_CHANNEL,
    }
)


def role_tag(tag: RoleTag) -> str:
    """Return the registry string for a role tag."""
    return tag.value


class ArchitectureSlot(str, Enum):
    """Family extension-slot registry (plan v0.2 §1B.6).

    Slots *reserve* where family-native attributes live (Book 3B populates
    them). They never overwrite core schema fields (INV-1B-5). The
    ``finality_device`` slot's value-set is reserved here (E-12 / C-6) with
    population deferred to Book 3B (INV-1B-7).
    """

    UTXO_SET_SEMANTICS = "UTXO_SET_SEMANTICS"
    XRPL_TRUSTLINES_UNL = "XRPL_TRUSTLINES_UNL"
    ICP_SUBNETS_CANISTERS = "ICP_SUBNETS_CANISTERS"
    SOLANA_STAKE_FEE_MARKETS = "SOLANA_STAKE_FEE_MARKETS"
    COSMOS_IBC_CHANNELS_ICS = "COSMOS_IBC_CHANNELS_ICS"
    SUBSTRATE_PARACHAIN_XCM = "SUBSTRATE_PARACHAIN_XCM"
    DAG_TIP_SELECTION_FINALITY = "DAG_TIP_SELECTION_FINALITY"
    TON_ACTOR_SHARDING = "TON_ACTOR_SHARDING"
    HEDERA_MIRROR_NODE = "HEDERA_MIRROR_NODE"
    EUTXO_VALIDATORS = "EUTXO_VALIDATORS"
    SHIELDED_POOL_PROOFS = "SHIELDED_POOL_PROOFS"
    PERMISSIONED_MEMBERSHIP = "PERMISSIONED_MEMBERSHIP"
    FINALITY_DEVICE = "FINALITY_DEVICE"


class FinalityDevice(str, Enum):
    """Reserved value-set of the finality_device slot (E-12 / C-6).

    Registry + semantics reserved in Book 1; Book 3B owns value population
    and family registration (INV-1B-7).
    """

    LINEAR_DETERMINISTIC = "LINEAR_DETERMINISTIC"
    PROBABILISTIC = "PROBABILISTIC"
    DECLARATIVE_DAG = "DECLARATIVE_DAG"
    BFT_INSTANT = "BFT_INSTANT"
    OPTIMISTIC = "OPTIMISTIC"
    ZK_ROLLUP = "ZK_ROLLUP"
    OTHER = "OTHER"


class FamilySlotRegistry:
    """Enforces slot reservation vs declaration (INV-1B-7).

    Family slots may *reserve* value-sets; declaring a concrete family value
    requires a family registration string (Book 3B will own these). This
    prevents slot inflation at the kernel level.
    """

    def __init__(self) -> None:
        self._reserved: dict[ArchitectureSlot, tuple[str, ...]] = {
            ArchitectureSlot.FINALITY_DEVICE: tuple(
                d.value for d in FinalityDevice
            ),
        }
        self._declared: dict[ArchitectureSlot, dict[str, str]] = {}

    def reserved_values(self, slot: ArchitectureSlot) -> tuple[str, ...]:
        return self._reserved.get(slot, ())

    def declare(
        self, slot: ArchitectureSlot, family: str, value: str
    ) -> None:
        if slot not in self._reserved:
            raise ValueError(
                f"slot {slot.value} has no reserved value-set; slots are declared "
                "via the extension mechanism, not ad hoc (INV-1B-7)"
            )
        allowed = self._reserved[slot]
        if value != FinalityDevice.OTHER.value and value not in allowed:
            raise ValueError(
                f"value {value!r} not in reserved value-set for slot "
                f"{slot.value} (INV-1B-7)"
            )
        self._declared.setdefault(slot, {})[family] = value

    def declared(self, slot: ArchitectureSlot) -> dict[str, str]:
        return dict(self._declared.get(slot, {}))


class RoleTagViolation(ValueError):
    """Raised when a role tag is applied to a class that cannot carry it."""


def validate_role_tags(obj: CanonicalObject) -> None:
    """INV-1B-2 helper: architecture roles only on chains; and T-1B-6 /
    ADV-1B-K support — no EVM-required field is mandatory for non-EVM
    objects (a chain without the EVM tag is fully valid)."""

    chain_classes = (ObjectType.BLOCKCHAIN, ObjectType.LEDGER)
    for tag in obj.role_tags:
        try:
            role = RoleTag(tag)
        except ValueError:
            raise RoleTagViolation(
                f"role tag {tag!r} is not in the ratified registry (INV-1B-2/6)"
            )
        if role in _ARCHITECTURE_ROLES and obj.object_type not in chain_classes:
            raise RoleTagViolation(
                f"architecture role {role.value} tags chains only, but "
                f"{obj.object_id} is {obj.object_type.value} (INV-1B-2)"
            )


__all__ = [
    "ArchitectureSlot",
    "FamilySlotRegistry",
    "FinalityDevice",
    "RoleTag",
    "RoleTagViolation",
    "role_tag",
    "validate_role_tags",
]
