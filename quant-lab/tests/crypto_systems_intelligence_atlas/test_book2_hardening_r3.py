"""Book 2 Hardening R3 — canonical claim authority tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from crypto_systems_intelligence_atlas.claims import (
    Claim,
    ClaimState,
    GraphFactPromoter,
    can_promote_to_graph,
    promote_claim_to_graph,
)
from crypto_systems_intelligence_atlas.promotion import ClaimStateEngine
from crypto_systems_intelligence_atlas.relationships import EdgeType, GraphValidator, TypedEdge
from crypto_systems_intelligence_atlas.sources import AccessMethod, LocatorMetadata, Source
from crypto_systems_intelligence_atlas.types import AuthoritySeed, AuthorityTier, ClaimFamily, SourceClass

_spec = importlib.util.spec_from_file_location("r3_fixtures", Path(__file__).with_name("test_book2_integration.py"))
assert _spec is not None and _spec.loader is not None
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
NOW = _module.NOW
capture = _module.capture
setup_integration = _module.setup_integration


def make_claim(service, evidence, source, claim_id: str):
    ref = capture(service, evidence, source, claim_id, claim_id.encode())
    return service.add_observed(
        Claim(
            claim_id=claim_id,
            evidence_refs=(ref,),
            source_refs=(source.source_id,),
            proposition=__import__("crypto_systems_intelligence_atlas.claims", fromlist=["Proposition"]).Proposition(
                subject_refs=("subject",), predicate="relates", object_ref="object"
            ),
            claim_family=ClaimFamily.CHAIN_ARCHITECTURE,
            claim_state=ClaimState.OBSERVED,
            valid_time_hypothesis=NOW,
            observed_time=NOW,
            methodology=__import__("crypto_systems_intelligence_atlas.claims", fromlist=["Methodology"]).Methodology(
                methodology_ref="direct", version="v1", description="direct"
            ),
        )
    )


def edge_for(registry, protocol, oracle, binding, edge_id: str):
    return TypedEdge(
        edge_id=edge_id,
        edge_type=EdgeType.DEPENDS_ON,
        subject_id=protocol.object_id,
        object_id=oracle.object_id,
        claim_binding=binding,
        observed_at=NOW,
        valid_from=NOW,
    )


def test_detached_corroborated_copy_cannot_promote() -> None:
    registry, _, protocol, oracle, evidence, service, source = setup_integration()
    observed = make_claim(service, evidence, source, "r3-fake-corroborated")
    forged = observed.model_copy(update={"claim_state": ClaimState.CORROBORATED})
    assert not can_promote_to_graph(forged, service.claim_store)
    with pytest.raises(ValueError, match="canonical"):
        promote_claim_to_graph(forged, service.claim_store)
    binding = promote_claim_to_graph(observed, service.claim_store)
    edge = edge_for(registry, protocol, oracle, binding.book1, "r3-fake-corroborated-edge")
    with pytest.raises(ValueError, match="canonical"):
        GraphFactPromoter(GraphValidator(registry), service).add(claim=forged, edge=edge)
    assert forged.claim_id == observed.claim_id


def test_detached_inferred_with_forged_lineage_cannot_promote() -> None:
    registry, _, protocol, oracle, evidence, service, source = setup_integration()
    observed = make_claim(service, evidence, source, "r3-fake-inferred")
    forged = observed.model_copy(update={
        "claim_state": ClaimState.INFERRED,
        "parent_claim_refs": (observed.claim_id,),
        "parent_claim_states": (ClaimState.OBSERVED,),
        "methodology_ref": "forged",
        "lineage_evidence_refs": observed.evidence_refs,
        "valid_time_derivation": "forged",
    })
    assert not can_promote_to_graph(forged, service.claim_store)
    with pytest.raises(ValueError, match="canonical"):
        promote_claim_to_graph(forged, service.claim_store)
    binding = promote_claim_to_graph(observed, service.claim_store)
    edge = edge_for(registry, protocol, oracle, binding.book1, "r3-fake-inferred-edge")
    with pytest.raises(ValueError, match="canonical"):
        GraphFactPromoter(GraphValidator(registry), service).add(claim=forged, edge=edge)


def test_detached_claim_id_cannot_override_canonical_state() -> None:
    registry, _, protocol, oracle, evidence, service, source = setup_integration()
    observed = make_claim(service, evidence, source, "r3-detached-id")
    forged = observed.model_copy(update={"claim_state": ClaimState.REJECTED})
    binding = __import__("crypto_systems_intelligence_atlas.claims", fromlist=["promote_claim_to_graph"]).promote_claim_to_graph(observed, service.claim_store)
    edge = edge_for(registry, protocol, oracle, binding.book1, "r3-detached-id-edge")
    with pytest.raises(ValueError, match="canonical"):
        GraphFactPromoter(GraphValidator(registry), service).add(claim=forged, edge=edge)


def test_historical_version_cannot_promote_after_newer_current_version() -> None:
    registry, _, protocol, oracle, evidence, service, source = setup_integration()
    observed = make_claim(service, evidence, source, "r3-history")
    second = Source(
        source_id="csia:source:r3-history-second",
        source_class=SourceClass.RPC,
        canonical_name="R3 history second",
        owner_entity_ref="owner:second",
        locator=LocatorMetadata(base_locator="fixture://r3-history-second", access_method=AccessMethod.RPC, authentication="none"),
        authority_metadata=(AuthoritySeed(claim_family=ClaimFamily.CHAIN_ARCHITECTURE, tier=AuthorityTier.PRIMARY, valid_from=NOW, policy_version="v1"),),
        verification_evidence_refs=("r3-history-source",),
        last_verified_at=NOW,
    )
    evidence._source_registry.register(second)
    service.authority_policy.register_source(second)
    corroborating = make_claim(service, evidence, second, "r3-history-corroborating")
    current = ClaimStateEngine(service).transition(
        observed.claim_id,
        ClaimState.CORROBORATED,
        triggering_evidence_refs=corroborating.evidence_refs,
        corroborating_claim_id=corroborating.claim_id,
        transitioned_at=NOW,
    )
    historical = service.claim_store.history(observed.claim_id)[0]
    canonical_binding = __import__("crypto_systems_intelligence_atlas.claims", fromlist=["promote_claim_to_graph"]).promote_claim_to_graph(current, service.claim_store)
    edge = edge_for(registry, protocol, oracle, canonical_binding.book1, "r3-history-edge")
    with pytest.raises(ValueError, match="canonical"):
        GraphFactPromoter(GraphValidator(registry), service).add(claim=historical, edge=edge)
    assert GraphFactPromoter(GraphValidator(registry), service).add(claim=current, edge=edge).claim_binding.claim_id == current.claim_id


def test_claim_store_rejects_direct_promoted_state_insertion() -> None:
    _, _, _, _, evidence, service, source = setup_integration()
    observed = make_claim(service, evidence, source, "r3-direct-insertion")
    for state in (ClaimState.INFERRED, ClaimState.CORROBORATED):
        with pytest.raises(ValueError, match="initial insertion"):
            service.claim_store.add(observed.model_copy(update={"claim_state": state}))


def test_legitimate_observed_current_claim_promotes() -> None:
    registry, _, protocol, oracle, evidence, service, source = setup_integration()
    observed = make_claim(service, evidence, source, "r3-canonical-observed")
    binding = __import__("crypto_systems_intelligence_atlas.claims", fromlist=["promote_claim_to_graph"]).promote_claim_to_graph(observed, service.claim_store)
    edge = edge_for(registry, protocol, oracle, binding.book1, "r3-observed-edge")
    result = GraphFactPromoter(GraphValidator(registry), service).add(claim=observed, edge=edge)
    assert result.claim_binding.claim_id == observed.claim_id


def test_legitimate_inferred_current_claim_promotes() -> None:
    from crypto_systems_intelligence_atlas.claims import InferenceEngine, Methodology, Proposition
    registry, _, protocol, oracle, evidence, service, source = setup_integration()
    p1 = make_claim(service, evidence, source, "r3-inferred-p1")
    p2 = make_claim(service, evidence, source, "r3-inferred-p2")
    inferred = InferenceEngine(service).create(
        parent_claim_refs=(p1.claim_id, p2.claim_id),
        methodology=Methodology(methodology_ref="r3-inference", version="v1", description="inference"),
        proposition=Proposition(subject_refs=(protocol.object_id,), predicate="depends_on", object_ref=oracle.object_id),
        valid_time_hypothesis=NOW,
        valid_time_derivation="parent windows",
        observed_time=NOW,
        object_refs=(protocol.object_id, oracle.object_id),
        relationship_refs=(EdgeType.DEPENDS_ON.value,),
    )
    binding = __import__("crypto_systems_intelligence_atlas.claims", fromlist=["promote_claim_to_graph"]).promote_claim_to_graph(inferred, service.claim_store)
    edge = edge_for(registry, protocol, oracle, binding.book1, "r3-inferred-edge")
    result = GraphFactPromoter(GraphValidator(registry), service).add(claim=inferred, edge=edge)
    assert result.claim_binding.claim_id == inferred.claim_id


def test_legitimate_corroborated_current_claim_promotes() -> None:
    registry, _, protocol, oracle, evidence, service, source = setup_integration()
    second = Source(
        source_id="csia:source:r3-corroborated-second",
        source_class=SourceClass.RPC,
        canonical_name="R3 corroborated second",
        owner_entity_ref="owner:second",
        locator=LocatorMetadata(base_locator="fixture://r3-corroborated-second", access_method=AccessMethod.RPC, authentication="none"),
        authority_metadata=(AuthoritySeed(claim_family=ClaimFamily.CHAIN_ARCHITECTURE, tier=AuthorityTier.PRIMARY, valid_from=NOW, policy_version="v1"),),
        verification_evidence_refs=("r3-corroborated-source",),
        last_verified_at=NOW,
    )
    evidence._source_registry.register(second)
    service.authority_policy.register_source(second)
    left = make_claim(service, evidence, source, "r3-corroborated-left")
    right = make_claim(service, evidence, second, "r3-corroborated-right")
    current = ClaimStateEngine(service).transition(
        left.claim_id,
        ClaimState.CORROBORATED,
        triggering_evidence_refs=right.evidence_refs,
        corroborating_claim_id=right.claim_id,
        transitioned_at=NOW,
    )
    binding = __import__("crypto_systems_intelligence_atlas.claims", fromlist=["promote_claim_to_graph"]).promote_claim_to_graph(current, service.claim_store)
    edge = edge_for(registry, protocol, oracle, binding.book1, "r3-corroborated-edge")
    result = GraphFactPromoter(GraphValidator(registry), service).add(claim=current, edge=edge)
    assert "book2-state:CORROBORATED" in result.claim_binding.transformation_lineage


def test_old_corroborated_version_cannot_promote_after_rejection() -> None:
    registry, _, protocol, oracle, evidence, service, source = setup_integration()
    second = Source(
        source_id="csia:source:r3-reject-second",
        source_class=SourceClass.RPC,
        canonical_name="R3 reject second",
        owner_entity_ref="owner:second",
        locator=LocatorMetadata(base_locator="fixture://r3-reject-second", access_method=AccessMethod.RPC, authentication="none"),
        authority_metadata=(AuthoritySeed(claim_family=ClaimFamily.CHAIN_ARCHITECTURE, tier=AuthorityTier.PRIMARY, valid_from=NOW, policy_version="v1"),),
        verification_evidence_refs=("r3-reject-source",),
        last_verified_at=NOW,
    )
    evidence._source_registry.register(second)
    service.authority_policy.register_source(second)
    left = make_claim(service, evidence, source, "r3-reject-left")
    right = make_claim(service, evidence, second, "r3-reject-right")
    corroborated = ClaimStateEngine(service).transition(
        left.claim_id,
        ClaimState.CORROBORATED,
        triggering_evidence_refs=right.evidence_refs,
        corroborating_claim_id=right.claim_id,
        transitioned_at=NOW,
    )
    old_corroborated = service.claim_store.history(left.claim_id)[1]
    binding = __import__("crypto_systems_intelligence_atlas.claims", fromlist=["promote_claim_to_graph"]).promote_claim_to_graph(corroborated, service.claim_store)
    edge = edge_for(registry, protocol, oracle, binding.book1, "r3-old-corroborated-edge")
    rejected = ClaimStateEngine(service).transition(
        left.claim_id,
        ClaimState.REJECTED,
        triggering_evidence_refs=right.evidence_refs,
        transitioned_at=NOW,
    )
    with pytest.raises(ValueError, match="canonical"):
        GraphFactPromoter(GraphValidator(registry), service).add(claim=old_corroborated, edge=edge)
    assert rejected.claim_state is ClaimState.REJECTED
