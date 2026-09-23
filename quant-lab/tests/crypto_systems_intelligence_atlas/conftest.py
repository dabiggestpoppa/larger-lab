"""Shared fixtures for CSIA Book 1 kernel tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from crypto_systems_intelligence_atlas.identity import (
    CanonicalObject,
    DeploymentIdentity,
    DeploymentMarkerKind,
    IdentityRegistry,
    ObjectType,
    mint_object_id,
)
from crypto_systems_intelligence_atlas.relationships import (
    ClaimBinding,
)
from crypto_systems_intelligence_atlas.temporal import RecordLifecycle


def ts(*args: int) -> datetime:
    """Build a UTC datetime: ts(y, m, d[, h, m, s])."""
    return datetime(*args, tzinfo=UTC)


NOW = ts(2026, 9, 23, 12, 0, 0)


@pytest.fixture()
def registry():
    """A registry pre-populated with chain objects used across pilots."""
    reg = IdentityRegistry()
    chains = {
        "bitcoin": ObjectType.BLOCKCHAIN,
        "ethereum": ObjectType.BLOCKCHAIN,
        "base": ObjectType.BLOCKCHAIN,
        "xrpl": ObjectType.LEDGER,
        "solana": ObjectType.BLOCKCHAIN,
        "cosmos_hub": ObjectType.BLOCKCHAIN,
        "osmosis": ObjectType.BLOCKCHAIN,
        "icp": ObjectType.BLOCKCHAIN,
        "dag_pilot": ObjectType.BLOCKCHAIN,
        "arbitrum": ObjectType.BLOCKCHAIN,
    }
    for slug, otype in chains.items():
        reg.mint(
            CanonicalObject(
                object_id=mint_object_id(otype, slug),
                object_type=otype,
                canonical_name=slug,
                valid_from=NOW,
            )
        )
    return reg


@pytest.fixture()
def claim():
    def _claim(claim_id: str = "claim-1", state: RecordLifecycle = RecordLifecycle.OBSERVED) -> ClaimBinding:
        return ClaimBinding(
            claim_id=claim_id,
            source_id="src-docs",
            claim_state=state,
        )

    return _claim


def make_chain(
    registry: IdentityRegistry, slug: str, otype: ObjectType = ObjectType.BLOCKCHAIN
) -> CanonicalObject:
    obj = CanonicalObject(
        object_id=mint_object_id(otype, slug),
        object_type=otype,
        canonical_name=slug,
        valid_from=NOW,
    )
    return registry.mint(obj)


def make_token(
    registry: IdentityRegistry,
    slug: str,
    name: str,
    otype: ObjectType = ObjectType.TOKEN,
    tickers: tuple[tuple[str, str], ...] = (),
) -> CanonicalObject:
    from crypto_systems_intelligence_atlas.identity import TickerSymbol

    obj = CanonicalObject(
        object_id=mint_object_id(otype, slug),
        object_type=otype,
        canonical_name=name,
        valid_from=NOW,
        ticker_symbols=tuple(
            TickerSymbol(symbol=s, context=c, valid_from=NOW, collision_group=c)
            for s, c in tickers
        ),
    )
    return registry.mint(obj)


def native_deployment(token: CanonicalObject, chain: CanonicalObject) -> DeploymentIdentity:
    from crypto_systems_intelligence_atlas.identity import mint_deployment_id

    return DeploymentIdentity(
        deployment_id=mint_deployment_id(token.object_id, chain.object_id, "NATIVE"),
        chain=chain.object_id,
        marker_kind=DeploymentMarkerKind.NATIVE,
        valid_from=NOW,
    )


def contract_deployment(
    token: CanonicalObject, chain: CanonicalObject, address: str
) -> DeploymentIdentity:
    from crypto_systems_intelligence_atlas.identity import mint_deployment_id

    return DeploymentIdentity(
        deployment_id=mint_deployment_id(
            token.object_id, chain.object_id, f"CONTRACT({address})"
        ),
        chain=chain.object_id,
        marker_kind=DeploymentMarkerKind.CONTRACT,
        marker_value=address,
        valid_from=NOW,
    )
