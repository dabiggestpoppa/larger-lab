"""Shared deterministic fixtures for Book 5 offline tests.

Mirrors the accepted Book 4 fixture pattern: a registered offline source,
captured evidence, and OBSERVED Book 2 claims so every canonical Book 5
record resolves through the real Book 2 engines. Economics claims carry the
``ECONOMIC_FACT`` qualifier so qualifier-specific resolution is exercised.
"""

from __future__ import annotations

from datetime import UTC, datetime

from crypto_systems_intelligence_atlas.book5_core import (
    AttributionState,
    EconomicLocation,
    EconomicSite,
    LocationType,
    PrincipalComponent,
    PrincipalComponentSet,
    SiteType,
)
from crypto_systems_intelligence_atlas.book5_lineage import (
    CapitalPrincipalLineageGraph,
    DebtLiability,
    PrincipalContribution,
    PrincipalLineageNode,
)
from crypto_systems_intelligence_atlas.book5_provenance import Book5Provenance
from crypto_systems_intelligence_atlas.claims import (
    Book2ClaimState,
    Claim,
    ClaimStore,
    Methodology,
    Proposition,
)
from crypto_systems_intelligence_atlas.evidence import EvidenceStore, EvidenceTier
from crypto_systems_intelligence_atlas.sources import (
    AccessMethod,
    LocatorMetadata,
    Source,
    SourceRegistry,
    VerificationStatus,
)
from crypto_systems_intelligence_atlas.types import AuthoritySeed, AuthorityTier, ClaimFamily, SourceClass

NOW = datetime(2026, 9, 29, 12, tzinfo=UTC)
LATER = datetime(2026, 9, 29, 18, tzinfo=UTC)
SOURCE_ID = "csia:source:book5-offline"
ECONOMICS_QUALIFIER = "ECONOMIC_FACT"


def source_fixture() -> Source:
    return Source(
        source_id=SOURCE_ID,
        source_class=SourceClass.NATIVE_TECHNICAL,
        canonical_name="deterministic offline Book 5 fixture",
        object_scope=(),
        locator=LocatorMetadata(
            base_locator="fixture://book5",
            access_method=AccessMethod.DOCUMENT,
            authentication="none",
        ),
        authority_metadata=(
            AuthoritySeed(
                claim_family=ClaimFamily.CHAIN_ARCHITECTURE,
                tier=AuthorityTier.PRIMARY,
                valid_from=NOW,
                policy_version="book5-fixture-v1",
            ),
        ),
        verification_status=VerificationStatus.VERIFIED,
        verification_evidence_refs=("book5-source-verification",),
        last_verified_at=NOW,
    )


def make_claim(
    claim_id: str,
    *,
    evidence_ref: str,
    qualifier: str | None = ECONOMICS_QUALIFIER,
    state: "Book2ClaimState | None" = None,
) -> Claim:
    from crypto_systems_intelligence_atlas.claims import ClaimState

    return Claim(
        claim_id=claim_id,
        evidence_refs=(evidence_ref,),
        source_refs=(SOURCE_ID,),
        proposition=Proposition(
            subject_refs=("fixture:economics",),
            predicate="has_economic_state",
            object_ref=claim_id,
            qualifier=qualifier,
        ),
        claim_family=ClaimFamily.CHAIN_ARCHITECTURE,
        claim_state=state if state is not None else ClaimState.OBSERVED,
        valid_time_hypothesis=NOW,
        observed_time=NOW,
        methodology=Methodology(
            methodology_ref="offline-book5-fixture",
            version="1",
            description="deterministic offline Book 5 test input",
        ),
    )


def make_evidence(evidence: EvidenceStore, tag: str) -> str:
    return evidence.capture(
        source_id=SOURCE_ID,
        retrieved_at=NOW,
        content=f"book5 evidence {tag}".encode(),
        content_locator=f"fixture://book5/{tag}",
        raw_snapshot_ref=f"snapshot://book5/{tag}",
        extractor_version="test",
        parser_version="test",
        evidence_tier=EvidenceTier.FIRST_PARTY_DOC,
    ).evidence_id


def kernel() -> tuple[ClaimStore, EvidenceStore, Book5Provenance]:
    """Claim store with one OBSERVED ECONOMIC_FACT claim per fixture tag."""

    sources = SourceRegistry()
    sources.register(source_fixture())
    evidence = EvidenceStore(sources)
    claims = ClaimStore()
    for tag in ("base", "eth", "usdc", "pool", "market", "vault", "lst"):
        claims.add_initial(make_claim(f"book5-claim-{tag}", evidence_ref=make_evidence(evidence, tag)))
    return claims, evidence, Book5Provenance(claims, evidence)


def claim_ref_for(provenance: Book5Provenance, tag: str) -> str:
    """Return the canonical claim ref for a fixture tag, or synthesize one.

    The fixture kernel seeds a fixed tag set; tests needing more claims
    register them on the same stores through :func:`add_claim`.
    """

    claim_id = f"book5-claim-{tag}"
    try:
        provenance.claim_store.require(claim_id)
    except KeyError:
        add_claim(provenance, tag)
    return claim_id


def add_claim(
    provenance: Book5Provenance,
    tag: str,
    *,
    state: "Book2ClaimState | None" = None,
    with_evidence: bool = True,
) -> str:

    claim_id = f"book5-claim-{tag}"
    evidence_ref = make_evidence(
        provenance.evidence_store, tag
    ) if with_evidence else "book5-detached-evidence"
    provenance.claim_store.add_initial(
        make_claim(claim_id, evidence_ref=evidence_ref, state=state)
    )
    if state is None:
        # normalize: add_initial defaults to OBSERVED via make_claim
        pass
    return claim_id


def site(
    site_id: str = "csia:site:pool-1",
    site_type: SiteType = SiteType.AMM_POOL,
    protocol_ref: str = "csia:protocol:fixture-amm",
    location_type: LocationType = LocationType.POOL,
) -> EconomicSite:
    return EconomicSite(
        site_id=site_id,
        site_type=site_type,
        protocol_ref=protocol_ref,
        deployment_ref="csia:protocol:fixture-amm@chain-1:0xamm",
        location=EconomicLocation(location_type=location_type, ref="fixture:location"),
        valid_from=NOW,
    )


def component(
    asset_ref: str = "csia:token:eth",
    *,
    quantity: str = "3",
    unit: str = "ETH",
    attribution: AttributionState = AttributionState.EXACT,
    claim_ref: str = "book5-claim-eth",
    realization_ref: str | None = None,
    share_fraction: str | None = None,
) -> PrincipalComponent:
    return PrincipalComponent(
        asset_ref=asset_ref,
        realization_ref=realization_ref,
        quantity=quantity,
        unit=unit,
        attribution_state=attribution,
        book2_claim_refs=(claim_ref,),
        valid_time=NOW,
        share_fraction=share_fraction,
    )


def component_set(*components: PrincipalComponent) -> PrincipalComponentSet:
    return PrincipalComponentSet(components=components)


def lineage_node(
    lineage_id: str = "lineage:eth-1",
    *,
    asset_ref: str = "csia:token:eth",
    unit: str = "ETH",
    claim_ref: str = "book5-claim-eth",
    realization_ref: str | None = None,
) -> PrincipalLineageNode:
    return PrincipalLineageNode(
        lineage_id=lineage_id,
        asset_ref=asset_ref,
        realization_ref=realization_ref,
        unit=unit,
        book2_claim_refs=(claim_ref,),
        valid_time=NOW,
    )


def contribution(
    source: str,
    target: str,
    *,
    attribution: AttributionState = AttributionState.EXACT,
    quantity: str | None = "3",
    unit: str | None = "ETH",
    claim_ref: str = "book5-claim-eth",
    methodology_id: str | None = None,
    share_fraction: str | None = None,
) -> PrincipalContribution:
    return PrincipalContribution(
        source_lineage_id=source,
        target_record_id=target,
        attribution_state=attribution,
        quantity=quantity,
        unit=unit,
        share_fraction=share_fraction,
        methodology_id=methodology_id,
        valid_time=NOW,
        book2_claim_refs=(claim_ref,),
    )


def debt_liability(
    liability_id: str = "liability:usdc-1",
    *,
    quantity: str = "800",
) -> DebtLiability:
    return DebtLiability(
        liability_id=liability_id,
        market_site_id="csia:site:market-1",
        asset_ref="csia:token:usdc",
        quantity=quantity,
        unit="USDC",
        book2_claim_refs=("book5-claim-pool",),
        valid_time=NOW,
    )


def graph(*edges: PrincipalContribution, nodes: tuple[PrincipalLineageNode, ...] | None = None) -> CapitalPrincipalLineageGraph:
    g = CapitalPrincipalLineageGraph()
    for node in nodes or ():
        g.add_node(node)
    for edge in edges:
        g.add_edge(edge)
    return g


__all__ = [
    "ECONOMICS_QUALIFIER",
    "LATER",
    "NOW",
    "SOURCE_ID",
    "add_claim",
    "claim_ref_for",
    "component",
    "component_set",
    "contribution",
    "debt_liability",
    "graph",
    "kernel",
    "lineage_node",
    "make_claim",
    "make_evidence",
    "site",
    "source_fixture",
]
