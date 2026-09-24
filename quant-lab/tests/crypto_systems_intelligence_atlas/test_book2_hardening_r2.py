"""Book 2 Hardening R2 — projection and graph-fact boundary tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from crypto_systems_intelligence_atlas.claims import (
    Book2ClaimBinding,
    Claim,
    ClaimState,
    GraphFactPromoter,
    can_promote_to_graph,
    promote_claim_to_graph,
)
from crypto_systems_intelligence_atlas.relationships import EdgeType, GraphValidator, TypedEdge
from crypto_systems_intelligence_atlas.temporal import RecordLifecycle
_integration_spec = importlib.util.spec_from_file_location(
    "r2_integration_fixtures",
    Path(__file__).with_name("test_book2_integration.py"),
)
assert _integration_spec is not None and _integration_spec.loader is not None
_integration = importlib.util.module_from_spec(_integration_spec)
_integration_spec.loader.exec_module(_integration)
NOW = _integration.NOW
capture = _integration.capture
setup_integration = _integration.setup_integration


def make_claim(service, evidence, source, claim_id: str, state: ClaimState = ClaimState.OBSERVED):
    evidence_id = capture(service, evidence, source, claim_id, claim_id.encode())
    return service.add_observed(
        Claim(
            claim_id=claim_id,
            evidence_refs=(evidence_id,),
            source_refs=(source.source_id,),
            proposition=__import__("crypto_systems_intelligence_atlas.claims", fromlist=["Proposition"]).Proposition(subject_refs=("subject",), predicate="relates", object_ref="object"),
            claim_family=__import__("crypto_systems_intelligence_atlas.types", fromlist=["ClaimFamily"]).ClaimFamily.CHAIN_ARCHITECTURE,
            claim_state=state,
            valid_time_hypothesis=NOW,
            observed_time=NOW,
            methodology=__import__("crypto_systems_intelligence_atlas.claims", fromlist=["Methodology"]).Methodology(methodology_ref="direct", version="v1", description="direct capture"),
        )
    )


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        (ClaimState.DECLARED, RecordLifecycle.DECLARED),
        (ClaimState.OBSERVED, RecordLifecycle.OBSERVED),
        (ClaimState.CONTESTED, RecordLifecycle.CONTESTED),
        (ClaimState.REJECTED, RecordLifecycle.REJECTED),
    ],
)
def test_projection_preserves_all_faithful_book1_equivalent_states(state, expected) -> None:
    _, _, _, _, _, service, source = setup_integration()
    observed = make_claim(service, service.evidence_store, source, f"projection-{state.value.lower()}")
    candidate = observed.model_copy(update={"claim_state": state})
    binding = Book2ClaimBinding.from_claim(candidate)
    assert binding.book1.claim_state is expected
    assert binding.book2_claim_state is state


def test_projection_is_faithful_for_book1_equivalent_states() -> None:
    _, _, _, _, _, service, source = setup_integration()
    evidence_id = capture(service, service.evidence_store, source, "projection-observed", b"observed")
    claim = service.add_observed(
        Claim(
            claim_id="projection-observed",
            evidence_refs=(evidence_id,),
            source_refs=(source.source_id,),
            proposition=service and __import__("crypto_systems_intelligence_atlas.claims", fromlist=["Proposition"]).Proposition(subject_refs=("x",), predicate="p", object_ref="y"),
            claim_family=__import__("crypto_systems_intelligence_atlas.types", fromlist=["ClaimFamily"]).ClaimFamily.CHAIN_ARCHITECTURE,
            claim_state=ClaimState.OBSERVED,
            valid_time_hypothesis=NOW,
            observed_time=NOW,
            methodology=__import__("crypto_systems_intelligence_atlas.claims", fromlist=["Methodology"]).Methodology(methodology_ref="direct", version="v1", description="direct"),
        )
    )
    binding = Book2ClaimBinding.from_claim(claim)
    assert binding.book1.claim_state is RecordLifecycle.OBSERVED
    assert binding.book2_claim_state is ClaimState.OBSERVED


@pytest.mark.parametrize("state", [ClaimState.INFERRED, ClaimState.CORROBORATED, ClaimState.UNRESOLVED, ClaimState.STALE, ClaimState.SUPERSEDED])
def test_non_equivalent_states_require_graph_promotion_adapter(state: ClaimState) -> None:
    _, _, _, _, _, service, source = setup_integration()
    evidence_id = capture(service, service.evidence_store, source, f"projection-{state.value.lower()}", state.value.encode())
    claim = service.add_observed(
        Claim(
            claim_id=f"projection-{state.value.lower()}",
            evidence_refs=(evidence_id,),
            source_refs=(source.source_id,),
            proposition=__import__("crypto_systems_intelligence_atlas.claims", fromlist=["Proposition"]).Proposition(subject_refs=("x",), predicate="p", object_ref="y"),
            claim_family=__import__("crypto_systems_intelligence_atlas.types", fromlist=["ClaimFamily"]).ClaimFamily.CHAIN_ARCHITECTURE,
            claim_state=ClaimState.OBSERVED,
            valid_time_hypothesis=NOW,
            observed_time=NOW,
            methodology=__import__("crypto_systems_intelligence_atlas.claims", fromlist=["Methodology"]).Methodology(methodology_ref="direct", version="v1", description="direct"),
        )
    ).model_copy(update={"claim_state": state})
    with pytest.raises(ValueError, match="graph promotion adapter"):
        Book2ClaimBinding.from_claim(claim)
    if state is ClaimState.CORROBORATED:
        assert Book2ClaimBinding.for_graph(claim).book2_claim_state is state
    else:
        with pytest.raises(ValueError, match="cannot create a current graph fact"):
            Book2ClaimBinding.for_graph(claim)


def test_graph_promotion_gate_rejects_non_promotable_states() -> None:
    _, _, _, _, _, service, source = setup_integration()
    evidence_id = capture(service, service.evidence_store, source, "gate", b"gate")
    claim = service.add_observed(
        Claim(
            claim_id="gate",
            evidence_refs=(evidence_id,),
            source_refs=(source.source_id,),
            proposition=__import__("crypto_systems_intelligence_atlas.claims", fromlist=["Proposition"]).Proposition(subject_refs=("x",), predicate="p", object_ref="y"),
            claim_family=__import__("crypto_systems_intelligence_atlas.types", fromlist=["ClaimFamily"]).ClaimFamily.CHAIN_ARCHITECTURE,
            claim_state=ClaimState.OBSERVED,
            valid_time_hypothesis=NOW,
            observed_time=NOW,
            methodology=__import__("crypto_systems_intelligence_atlas.claims", fromlist=["Methodology"]).Methodology(methodology_ref="direct", version="v1", description="direct"),
        )
    )
    for state in (ClaimState.DECLARED, ClaimState.CONTESTED, ClaimState.UNRESOLVED, ClaimState.STALE, ClaimState.REJECTED, ClaimState.SUPERSEDED):
        candidate = claim.model_copy(update={"claim_state": state})
        assert not can_promote_to_graph(candidate)
        with pytest.raises(ValueError, match="cannot create a current graph fact"):
            promote_claim_to_graph(candidate)


def test_graph_fact_promoter_rejects_non_promotable_claim_before_graph_insertion() -> None:
    registry, _, protocol, oracle, evidence, service, source = setup_integration()
    claim = make_claim(service, evidence, source, "promoter-reject")
    edge = TypedEdge(
        edge_id="promoter-reject-edge",
        edge_type=EdgeType.DEPENDS_ON,
        subject_id=protocol.object_id,
        object_id=oracle.object_id,
        claim_binding=Book2ClaimBinding.from_claim(claim).book1,
        observed_at=NOW,
        valid_from=NOW,
    )
    rejected = claim.model_copy(update={"claim_state": ClaimState.REJECTED})
    with pytest.raises(ValueError, match="cannot create a current graph fact"):
        GraphFactPromoter(GraphValidator(registry)).add(claim=rejected, edge=edge)


def test_inferred_graph_fact_preserves_book2_origin_and_lineage() -> None:
    registry, chain, protocol, oracle, evidence, service, source = setup_integration()
    p1_ref = capture(service, evidence, source, "r2-p1", b"p1")
    p2_ref = capture(service, evidence, source, "r2-p2", b"p2")
    from crypto_systems_intelligence_atlas.claims import InferenceEngine, Methodology, Proposition
    parents = []
    for claim_id, ref, subject, obj in (("r2-p1-claim", p1_ref, protocol.object_id, oracle.object_id), ("r2-p2-claim", p2_ref, oracle.object_id, chain.object_id)):
        parents.append(service.add_observed(Claim(claim_id=claim_id, evidence_refs=(ref,), source_refs=(source.source_id,), object_refs=(subject, obj), proposition=Proposition(subject_refs=(subject,), predicate="relates", object_ref=obj), claim_family=__import__("crypto_systems_intelligence_atlas.types", fromlist=["ClaimFamily"]).ClaimFamily.CHAIN_ARCHITECTURE, claim_state=ClaimState.OBSERVED, valid_time_hypothesis=NOW, observed_time=NOW, methodology=Methodology(methodology_ref="direct", version="v1", description="direct"))))
    inferred = InferenceEngine(service).create(parent_claim_refs=tuple(p.claim_id for p in parents), methodology=Methodology(methodology_ref="r2-method", version="v1", description="qualified inference"), proposition=Proposition(subject_refs=(protocol.object_id,), predicate="depends_on", object_ref=oracle.object_id), valid_time_hypothesis=NOW, valid_time_derivation="parent windows", observed_time=NOW, object_refs=(protocol.object_id, oracle.object_id), relationship_refs=(EdgeType.DEPENDS_ON.value,))
    binding = promote_claim_to_graph(inferred)
    edge = TypedEdge(edge_id="r2-inferred-edge", edge_type=EdgeType.DEPENDS_ON, subject_id=protocol.object_id, object_id=oracle.object_id, claim_binding=binding.book1, observed_at=NOW, valid_from=NOW)
    GraphFactPromoter(GraphValidator(registry)).add(claim=inferred, edge=edge)
    assert binding.book2_claim_state is ClaimState.INFERRED
    assert edge.claim_binding.claim_id == inferred.claim_id
    assert set(inferred.parent_claim_refs) == {p.claim_id for p in parents}
    assert inferred.methodology_ref == "r2-method"
    assert set(inferred.lineage_evidence_refs) == {p1_ref, p2_ref}


def test_inferred_without_lineage_cannot_promote() -> None:
    _, _, _, _, _, service, source = setup_integration()
    evidence_id = capture(service, service.evidence_store, source, "bad-inferred", b"bad")
    from crypto_systems_intelligence_atlas.claims import Methodology, Proposition
    claim = service.add_observed(Claim(claim_id="bad-inferred", evidence_refs=(evidence_id,), source_refs=(source.source_id,), proposition=Proposition(subject_refs=("x",), predicate="p", object_ref="y"), claim_family=__import__("crypto_systems_intelligence_atlas.types", fromlist=["ClaimFamily"]).ClaimFamily.CHAIN_ARCHITECTURE, claim_state=ClaimState.OBSERVED, valid_time_hypothesis=NOW, observed_time=NOW, methodology=Methodology(methodology_ref="direct", version="v1", description="direct"))).model_copy(update={"claim_state": ClaimState.INFERRED})
    with pytest.raises(ValueError):
        promote_claim_to_graph(claim)
