"""Book 2 Hardening R4 — corroboration semantic seal tests."""

from __future__ import annotations

import importlib.util
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from crypto_systems_intelligence_atlas.claims import (
    Claim,
    ClaimState,
    GraphFactPromoter,
    Methodology,
    Proposition,
    promote_claim_to_graph,
)
from crypto_systems_intelligence_atlas.promotion import ClaimStateEngine
from crypto_systems_intelligence_atlas.relationships import EdgeType, GraphValidator, TypedEdge
from crypto_systems_intelligence_atlas.sources import AccessMethod, LocatorMetadata, Source
from crypto_systems_intelligence_atlas.temporal import UnknownBound
from crypto_systems_intelligence_atlas.types import AuthoritySeed, AuthorityTier, ClaimFamily, SourceClass

_spec = importlib.util.spec_from_file_location("r4_fixtures", Path(__file__).with_name("test_book2_integration.py"))
assert _spec is not None and _spec.loader is not None
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
NOW = _module.NOW
LATER = NOW + timedelta(days=1)
capture = _module.capture
setup_integration = _module.setup_integration


def independent_source() -> Source:
    return Source(
        source_id="csia:source:r4-second",
        source_class=SourceClass.RPC,
        canonical_name="R4 second source",
        owner_entity_ref="owner:r4-second",
        locator=LocatorMetadata(
            base_locator="fixture://r4-second",
            access_method=AccessMethod.RPC,
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
        verification_evidence_refs=("r4-second-source",),
        last_verified_at=NOW,
    )


def make_claim(
    service,
    evidence,
    source: Source,
    claim_id: str,
    proposition: Proposition,
    *,
    claim_family: ClaimFamily = ClaimFamily.CHAIN_ARCHITECTURE,
    state: ClaimState = ClaimState.OBSERVED,
    valid_time: datetime | UnknownBound = NOW,
):
    ref = capture(service, evidence, source, claim_id, claim_id.encode())
    claim = Claim(
        claim_id=claim_id,
        evidence_refs=(ref,),
        source_refs=(source.source_id,),
        proposition=proposition,
        claim_family=claim_family,
        claim_state=state,
        valid_time_hypothesis=valid_time,
        observed_time=NOW,
        methodology=Methodology(methodology_ref="direct", version="v1", description="direct"),
    )
    if state is ClaimState.DECLARED:
        return service.add_declared(claim)
    return service.add_observed(claim)


def proposition(
    subject: str = "protocol",
    predicate: str = "runs_on",
    object_ref: str = "chain-a",
    qualifier: str | None = None,
) -> Proposition:
    return Proposition(
        subject_refs=(subject,),
        predicate=predicate,
        object_ref=object_ref,
        qualifier=qualifier,
    )


def transition(service, left, right, *, evidence_refs=None):
    return ClaimStateEngine(service).transition(
        left.claim_id,
        ClaimState.CORROBORATED,
        triggering_evidence_refs=evidence_refs or right.evidence_refs,
        corroborating_claim_id=right.claim_id,
        transitioned_at=LATER,
    )


def attach_service(claim, service):
    return claim


def test_unrelated_proposition_cannot_corroborate() -> None:
    _, _, _, _, evidence, service, source = setup_integration()
    second = independent_source()
    evidence._source_registry.register(second)
    service.authority_policy.register_source(second)
    left = attach_service(make_claim(service, evidence, source, "r4-unrelated-left", proposition()), service)
    right = attach_service(
        make_claim(service, evidence, second, "r4-unrelated-right", proposition("oracle", "serves", "chain-b")),
        service,
    )
    with pytest.raises(ValueError, match="proposition"):
        transition(service, left, right)


def test_same_subject_different_predicate_cannot_corroborate() -> None:
    _, _, _, _, evidence, service, source = setup_integration()
    second = independent_source()
    evidence._source_registry.register(second)
    service.authority_policy.register_source(second)
    left = attach_service(make_claim(service, evidence, source, "r4-predicate-left", proposition()), service)
    right = attach_service(make_claim(service, evidence, second, "r4-predicate-right", proposition(predicate="depends_on")), service)
    with pytest.raises(ValueError, match="proposition"):
        transition(service, left, right)


def test_same_predicate_different_object_cannot_corroborate() -> None:
    _, _, _, _, evidence, service, source = setup_integration()
    second = independent_source()
    evidence._source_registry.register(second)
    service.authority_policy.register_source(second)
    left = attach_service(make_claim(service, evidence, source, "r4-object-left", proposition()), service)
    right = attach_service(make_claim(service, evidence, second, "r4-object-right", proposition(object_ref="chain-b")), service)
    with pytest.raises(ValueError, match="proposition"):
        transition(service, left, right)


def test_different_claim_family_cannot_corroborate() -> None:
    _, _, _, _, evidence, service, source = setup_integration()
    second = independent_source()
    evidence._source_registry.register(second)
    service.authority_policy.register_source(second)
    left = attach_service(make_claim(service, evidence, source, "r4-family-left", proposition()), service)
    right = attach_service(
        make_claim(service, evidence, second, "r4-family-right", proposition(), claim_family=ClaimFamily.NARRATIVE),
        service,
    )
    with pytest.raises(ValueError, match="claim family"):
        transition(service, left, right)


def test_declared_corroborator_cannot_corroborate() -> None:
    _, _, _, _, evidence, service, source = setup_integration()
    second = independent_source()
    evidence._source_registry.register(second)
    service.authority_policy.register_source(second)
    left = attach_service(make_claim(service, evidence, source, "r4-declared-left", proposition()), service)
    right = attach_service(make_claim(service, evidence, second, "r4-declared-right", proposition(), state=ClaimState.DECLARED), service)
    with pytest.raises(ValueError, match="state"):
        transition(service, left, right)


@pytest.mark.parametrize(
    "state", [ClaimState.CONTESTED, ClaimState.REJECTED, ClaimState.STALE, ClaimState.SUPERSEDED]
)
def test_non_observation_corroborator_states_are_rejected(state: ClaimState) -> None:
    _, _, _, _, evidence, service, source = setup_integration()
    second = independent_source()
    evidence._source_registry.register(second)
    service.authority_policy.register_source(second)
    left = attach_service(make_claim(service, evidence, source, f"r4-{state.value.lower()}-left", proposition()), service)
    right = attach_service(make_claim(service, evidence, second, f"r4-{state.value.lower()}-right", proposition()), service)
    engine = ClaimStateEngine(service)
    if state is ClaimState.SUPERSEDED:
        replacement = make_claim(service, evidence, source, f"r4-{state.value.lower()}-replacement", proposition())
        engine.transition(
            right.claim_id,
            state,
            triggering_evidence_refs=right.evidence_refs,
            transitioned_at=LATER,
            replacement_claim_id=replacement.claim_id,
            supersession_reason="test replacement",
        )
    else:
        engine.transition(right.claim_id, state, triggering_evidence_refs=right.evidence_refs, transitioned_at=LATER)
    with pytest.raises(ValueError, match="state"):
        transition(service, left, right)


def test_historical_corroborator_cannot_corroborate() -> None:
    _, _, _, _, evidence, service, source = setup_integration()
    second = independent_source()
    evidence._source_registry.register(second)
    service.authority_policy.register_source(second)
    left = attach_service(make_claim(service, evidence, source, "r4-historical-left", proposition()), service)
    right = attach_service(make_claim(service, evidence, second, "r4-historical-right", proposition()), service)
    ClaimStateEngine(service).transition(
        right.claim_id,
        ClaimState.CONTESTED,
        triggering_evidence_refs=right.evidence_refs,
        transitioned_at=LATER,
    )
    with pytest.raises(ValueError, match="state"):
        transition(service, left, right)


def test_triggering_evidence_must_belong_to_corroborator() -> None:
    _, _, _, _, evidence, service, source = setup_integration()
    second = independent_source()
    evidence._source_registry.register(second)
    service.authority_policy.register_source(second)
    left = attach_service(make_claim(service, evidence, source, "r4-evidence-left", proposition()), service)
    right = attach_service(make_claim(service, evidence, second, "r4-evidence-right", proposition()), service)
    unrelated = make_claim(service, evidence, source, "r4-evidence-unrelated", proposition())
    with pytest.raises(ValueError, match="evidence"):
        transition(service, left, right, evidence_refs=unrelated.evidence_refs)


def test_incompatible_valid_time_cannot_corroborate() -> None:
    _, _, _, _, evidence, service, source = setup_integration()
    second = independent_source()
    evidence._source_registry.register(second)
    service.authority_policy.register_source(second)
    left = attach_service(make_claim(service, evidence, source, "r4-time-left", proposition()), service)
    right = attach_service(make_claim(service, evidence, second, "r4-time-right", proposition(), valid_time=LATER), service)
    with pytest.raises(ValueError, match="valid time"):
        transition(service, left, right)


def test_unknown_valid_time_cannot_corroborate() -> None:
    _, _, _, _, evidence, service, source = setup_integration()
    second = independent_source()
    evidence._source_registry.register(second)
    service.authority_policy.register_source(second)
    left = attach_service(make_claim(service, evidence, source, "r4-unknown-time-left", proposition()), service)
    right = attach_service(
        make_claim(
            service,
            evidence,
            second,
            "r4-unknown-time-right",
            proposition(),
            valid_time=UnknownBound(earliest_bound=NOW, latest_bound=LATER),
        ),
        service,
    )
    with pytest.raises(ValueError, match="valid time"):
        transition(service, left, right)


def test_legitimate_corroboration_and_graph_promotion_pass() -> None:
    registry, chain, protocol, _, evidence, service, source = setup_integration()
    second = independent_source()
    evidence._source_registry.register(second)
    service.authority_policy.register_source(second)
    same = proposition(protocol.object_id, EdgeType.RUNS_ON.value, chain.object_id)
    left = make_claim(service, evidence, source, "r4-legitimate-left", same)
    right = make_claim(service, evidence, second, "r4-legitimate-right", same)
    current = ClaimStateEngine(service).transition(
        left.claim_id,
        ClaimState.CORROBORATED,
        triggering_evidence_refs=right.evidence_refs,
        corroborating_claim_id=right.claim_id,
        transitioned_at=LATER,
    )
    binding = promote_claim_to_graph(current, service.claim_store)
    edge = TypedEdge(
        edge_id="r4-legitimate-edge",
        edge_type=EdgeType.RUNS_ON,
        subject_id=protocol.object_id,
        object_id=chain.object_id,
        claim_binding=binding.book1,
        observed_at=NOW,
        valid_from=NOW,
    )
    result = GraphFactPromoter(GraphValidator(registry), service).add(claim=current, edge=edge)
    assert result.claim_binding.claim_id == current.claim_id
    assert service.claim_store.transitions[-1].corroborating_claim_id == right.claim_id


def test_historical_corroborator_provenance_remains_graph_recheckable() -> None:
    registry, chain, protocol, _, evidence, service, source = setup_integration()
    second = independent_source()
    evidence._source_registry.register(second)
    service.authority_policy.register_source(second)
    same = proposition(protocol.object_id, EdgeType.RUNS_ON.value, chain.object_id)
    left = make_claim(service, evidence, source, "r4-provenance-left", same)
    right = make_claim(service, evidence, second, "r4-provenance-right", same)
    engine = ClaimStateEngine(service)
    current = engine.transition(
        left.claim_id,
        ClaimState.CORROBORATED,
        triggering_evidence_refs=right.evidence_refs,
        corroborating_claim_id=right.claim_id,
        transitioned_at=LATER,
    )
    engine.transition(
        right.claim_id,
        ClaimState.CONTESTED,
        triggering_evidence_refs=right.evidence_refs,
        transitioned_at=LATER,
    )
    binding = promote_claim_to_graph(current, service.claim_store)
    edge = TypedEdge(
        edge_id="r4-provenance-edge",
        edge_type=EdgeType.RUNS_ON,
        subject_id=protocol.object_id,
        object_id=chain.object_id,
        claim_binding=binding.book1,
        observed_at=NOW,
        valid_from=NOW,
    )
    result = GraphFactPromoter(GraphValidator(registry), service).add(claim=current, edge=edge)
    assert result.claim_binding.claim_id == current.claim_id


def test_graph_promoter_rejects_missing_corroboration_provenance() -> None:
    registry, chain, protocol, _, evidence, service, source = setup_integration()
    second = independent_source()
    evidence._source_registry.register(second)
    service.authority_policy.register_source(second)
    same = proposition(protocol.object_id, EdgeType.RUNS_ON.value, chain.object_id)
    left = make_claim(service, evidence, source, "r4-missing-provenance-left", same)
    right = make_claim(service, evidence, second, "r4-missing-provenance-right", same)
    current = ClaimStateEngine(service).transition(
        left.claim_id,
        ClaimState.CORROBORATED,
        triggering_evidence_refs=right.evidence_refs,
        corroborating_claim_id=right.claim_id,
        transitioned_at=LATER,
    )
    service.claim_store._transitions.clear()
    binding = promote_claim_to_graph(current, service.claim_store)
    edge = TypedEdge(
        edge_id="r4-missing-provenance-edge",
        edge_type=EdgeType.RUNS_ON,
        subject_id=protocol.object_id,
        object_id=chain.object_id,
        claim_binding=binding.book1,
        observed_at=NOW,
        valid_from=NOW,
    )
    with pytest.raises(ValueError, match="recorded transition"):
        GraphFactPromoter(GraphValidator(registry), service).add(claim=current, edge=edge)
