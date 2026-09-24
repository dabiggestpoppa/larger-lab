"""Book 2 → Book 1 provenance integration tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from crypto_systems_intelligence_atlas.authority import AuthorityPolicy
from crypto_systems_intelligence_atlas.claims import (
    Claim,
    ClaimService,
    ClaimState,
    InferenceEngine,
    Methodology,
    Proposition,
)
from crypto_systems_intelligence_atlas.evidence import EvidenceStore, EvidenceTier
from crypto_systems_intelligence_atlas.identity import (
    CanonicalObject,
    IdentityRegistry,
    ObjectType,
    mint_object_id,
)
from crypto_systems_intelligence_atlas.relationships import EdgeType, GraphValidator, TypedEdge
from crypto_systems_intelligence_atlas.sources import (
    AccessMethod,
    LocatorMetadata,
    Source,
    SourceRegistry,
    VerificationStatus,
)
from crypto_systems_intelligence_atlas.temporal import ClaimBinding
from crypto_systems_intelligence_atlas.types import AuthoritySeed, AuthorityTier, ClaimFamily, SourceClass

NOW = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)


def setup_integration():
    registry = IdentityRegistry()
    chain = registry.mint(
        CanonicalObject(
            object_id=mint_object_id(ObjectType.BLOCKCHAIN, "integration-chain"),
            object_type=ObjectType.BLOCKCHAIN,
            canonical_name="Integration Chain",
            valid_from=NOW,
        )
    )
    protocol = registry.mint(
        CanonicalObject(
            object_id=mint_object_id(ObjectType.PROTOCOL, "integration-protocol"),
            object_type=ObjectType.PROTOCOL,
            canonical_name="Integration Protocol",
            valid_from=NOW,
        )
    )
    oracle = registry.mint(
        CanonicalObject(
            object_id=mint_object_id(ObjectType.ORACLE_NETWORK, "integration-oracle"),
            object_type=ObjectType.ORACLE_NETWORK,
            canonical_name="Integration Oracle",
            valid_from=NOW,
        )
    )
    sources = SourceRegistry()
    source = Source(
        source_id="csia:source:integration",
        source_class=SourceClass.NATIVE_TECHNICAL,
        canonical_name="Integration Spec",
        locator=LocatorMetadata(
            base_locator="fixture://integration-spec",
            access_method=AccessMethod.DOCUMENT,
            authentication="none",
        ),
        authority_metadata=(
            AuthoritySeed(
                claim_family=ClaimFamily.CHAIN_ARCHITECTURE,
                tier=AuthorityTier.PRIMARY,
                valid_from=NOW,
                policy_version="v1",
            ),
        ),
        verification_status=VerificationStatus.VERIFIED,
        verification_evidence_refs=("verification-integration",),
        last_verified_at=NOW,
    )
    sources.register(source)
    policy = AuthorityPolicy()
    policy.register_source(source)
    evidence = EvidenceStore(sources)
    service = ClaimService(evidence, identity_registry=registry, authority_policy=policy)
    return registry, chain, protocol, oracle, evidence, service, source


def capture(service: ClaimService, evidence: EvidenceStore, source: Source, claim_id: str, content: bytes) -> str:
    return evidence.capture(
        source_id=source.source_id,
        retrieved_at=NOW,
        content=content,
        content_locator=f"fixture://{claim_id}",
        raw_snapshot_ref=f"snapshot://{claim_id}",
        extractor_version="integration-extractor",
        parser_version="integration-parser",
        evidence_tier=EvidenceTier.FIRST_PARTY_DOC,
    ).evidence_id


def test_raw_evidence_claim_binding_and_typed_edge_chain_is_reconstructable() -> None:
    registry, chain, protocol, _, evidence, service, source = setup_integration()
    evidence_id = capture(service, evidence, source, "direct", b"direct")
    claim = service.add(
        Claim(
            claim_id="direct-claim",
            evidence_refs=(evidence_id,),
            source_refs=(source.source_id,),
            object_refs=(protocol.object_id, chain.object_id),
            relationship_refs=(EdgeType.RUNS_ON.value,),
            proposition=Proposition(
                subject_refs=(protocol.object_id,), predicate="runs_on", object_ref=chain.object_id
            ),
            claim_family=ClaimFamily.CHAIN_ARCHITECTURE,
            claim_state=ClaimState.OBSERVED,
            valid_time_hypothesis=NOW,
            observed_time=NOW,
            methodology=Methodology(methodology_ref="direct", version="v1", description="direct capture"),
        )
    )
    binding = ClaimBinding(
        claim_id=claim.claim_id,
        source_id=source.source_id,
        source_locator=evidence.require(evidence_id).content_locator,
        evidence_type="RAW_EVIDENCE",
        retrieval_time=NOW,
        extractor_version="integration-extractor",
        transformation_lineage=(evidence_id,),
        claim_state=ClaimState.OBSERVED,
    )
    edge = TypedEdge(
        edge_id="edge-direct",
        edge_type=EdgeType.RUNS_ON,
        subject_id=protocol.object_id,
        object_id=chain.object_id,
        claim_binding=binding,
        observed_at=NOW,
        valid_from=NOW,
    )
    GraphValidator(registry).add_edge(edge)
    assert edge.claim_binding.claim_id == claim.claim_id
    assert edge.claim_binding.transformation_lineage == (evidence_id,)
    assert service.require(claim.claim_id).evidence_refs == (evidence_id,)
    assert evidence.require(evidence_id).raw_snapshot_ref == "snapshot://direct"


def test_inferred_claim_binding_preserves_methodology_parent_and_raw_lineage() -> None:
    _, _, protocol, oracle, evidence, service, source = setup_integration()
    p1_ref = capture(service, evidence, source, "dependency", b"dependency")
    p2_ref = capture(service, evidence, source, "outage", b"outage")
    p1 = service.add(
        Claim(
            claim_id="parent-dependency",
            evidence_refs=(p1_ref,),
            source_refs=(source.source_id,),
            object_refs=(protocol.object_id, oracle.object_id),
            proposition=Proposition(subject_refs=(protocol.object_id,), predicate="depends_on", object_ref=oracle.object_id),
            claim_family=ClaimFamily.CHAIN_ARCHITECTURE,
            claim_state=ClaimState.OBSERVED,
            valid_time_hypothesis=NOW,
            observed_time=NOW,
            methodology=Methodology(methodology_ref="direct", version="v1", description="direct"),
        )
    )
    p2 = service.add(
        Claim(
            claim_id="parent-outage",
            evidence_refs=(p2_ref,),
            source_refs=(source.source_id,),
            object_refs=(oracle.object_id,),
            proposition=Proposition(subject_refs=(oracle.object_id,), predicate="stopped_serving", object_ref="chain"),
            claim_family=ClaimFamily.CHAIN_ARCHITECTURE,
            claim_state=ClaimState.OBSERVED,
            valid_time_hypothesis=NOW,
            observed_time=NOW,
            methodology=Methodology(methodology_ref="direct", version="v1", description="direct"),
        )
    )
    inferred = InferenceEngine(service).create(
        parent_claim_refs=(p1.claim_id, p2.claim_id),
        methodology=Methodology(
            methodology_ref="oracle-risk",
            version="v1",
            description="derive qualified availability risk from dependency and outage",
        ),
        proposition=Proposition(subject_refs=(protocol.object_id,), predicate="may_have_degraded", object_ref=oracle.object_id),
        valid_time_hypothesis=NOW,
        valid_time_derivation="overlap of parent windows; severity UNKNOWN",
        observed_time=NOW,
        object_refs=(protocol.object_id, oracle.object_id),
        relationship_refs=(EdgeType.DEPENDS_ON.value,),
    )
    binding = ClaimBinding(
        claim_id=inferred.claim_id,
        source_id=source.source_id,
        source_locator="fixture://inference",
        evidence_type="DERIVED_CLAIM",
        retrieval_time=NOW,
        extractor_version="integration-extractor",
        transformation_lineage=(*inferred.lineage_evidence_refs, inferred.methodology_ref),
        claim_state=ClaimState.INFERRED,
    )
    assert binding.claim_state is ClaimState.INFERRED
    assert inferred.parent_claim_refs == (p1.claim_id, p2.claim_id)
    assert set(service.lineage_evidence(inferred)) == {p1_ref, p2_ref}
    assert binding.transformation_lineage[-1] == "oracle-risk"
    assert (evidence.require(p1_ref).content_hash, evidence.require(p2_ref).content_hash) == (
        evidence.require(p1_ref).content_hash,
        evidence.require(p2_ref).content_hash,
    )


def test_claim_service_does_not_auto_mint_unknown_book1_objects() -> None:
    _, _, _, _, evidence, service, source = setup_integration()
    evidence_id = capture(service, evidence, source, "unknown-object", b"unknown")
    with pytest.raises(KeyError):
        service.add(
            Claim(
                claim_id="unknown-object-claim",
                evidence_refs=(evidence_id,),
                source_refs=(source.source_id,),
                object_refs=("csia:protocol:not-minted",),
                proposition=Proposition(subject_refs=("csia:protocol:not-minted",), predicate="state", object_ref="true"),
                claim_family=ClaimFamily.CHAIN_ARCHITECTURE,
                claim_state=ClaimState.OBSERVED,
                valid_time_hypothesis=NOW,
                observed_time=NOW,
                methodology=Methodology(methodology_ref="direct", version="v1", description="direct"),
            )
        )
