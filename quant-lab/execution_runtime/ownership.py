"""QL-EXEC-R1 — deterministic logical ownership identity.

Logical ownership truth is the durable ledger. Broker tags (magic/comment)
are lookup keys, never the sole ownership authority.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

_OWNERSHIP_VERSION = "QL1"
_MAGIC_MODULUS = (1 << 31) - 1  # keep within positive 32-bit broker range


def _short(prefix: str, *parts: str, n: int = 8) -> str:
    canonical = "|".join(str(p) for p in parts)
    return f"{prefix}{hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:n]}"


@dataclass(frozen=True)
class OwnershipNamespace:
    """Binding-level ownership scope (no intent_id yet)."""

    account_id: str
    runtime_id: str
    strategy_id: str
    deployment_generation: str


@dataclass(frozen=True)
class LogicalOwnershipId:
    """Canonical logical ownership identity (full executable-event scope)."""

    account_id: str
    runtime_id: str
    strategy_id: str
    deployment_generation: str
    intent_id: str

    def canonical(self) -> str:
        return (
            f"{_OWNERSHIP_VERSION}|{self.account_id}|{self.runtime_id}|"
            f"{self.strategy_id}|{self.deployment_generation}|{self.intent_id}"
        )

    def id(self) -> str:
        """Deterministic, collision-resistant, versioned logical id."""
        return hashlib.sha256(self.canonical().encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class BrokerOwnershipTag:
    """Compact broker-side encoding. Lookup key only, not sole authority."""

    magic: int
    comment: str
    encoding_version: str = _OWNERSHIP_VERSION


def magic_for_namespace(ns: OwnershipNamespace) -> int:
    """Stable per-binding magic (NOT a global magic, NOT strategy_id alone).

    Scoped by account_id + strategy_id + deployment_generation so two
    bindings cannot collide on a shared account.
    """
    h = hashlib.sha256(
        (
            f"{_OWNERSHIP_VERSION}|magic|{ns.account_id}|{ns.strategy_id}|"
            f"{ns.deployment_generation}"
        ).encode("utf-8")
    ).hexdigest()
    return (int(h, 16) % _MAGIC_MODULUS) + 1


def encode_broker_ownership(logical: LogicalOwnershipId) -> BrokerOwnershipTag:
    """Deterministic, collision-resistant, versioned broker tag.

    The comment is recoverable to the logical record only through the durable
    ledger mapping (full ids live in the ledger; the tag is compact).
    """
    ns = OwnershipNamespace(
        account_id=logical.account_id,
        runtime_id=logical.runtime_id,
        strategy_id=logical.strategy_id,
        deployment_generation=logical.deployment_generation,
    )
    comment = "|".join(
        [
            _OWNERSHIP_VERSION,
            _short("A", logical.account_id),
            _short("R", logical.runtime_id),
            _short("S", logical.strategy_id),
            _short("G", logical.deployment_generation),
            _short("I", logical.intent_id),
        ]
    )
    return BrokerOwnershipTag(magic=magic_for_namespace(ns), comment=comment)
