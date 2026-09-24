"""Adversarial Book 2 tests: prohibited paths must fail closed."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

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
from crypto_systems_intelligence_atlas.contradiction import ContradictionEngine, ResolutionKind
from crypto_systems_intelligence_atlas.evidence import EvidenceStore, EvidenceTier
from crypto_systems_intelligence_atlas.freshness import FreshnessMode, FreshnessPolicy, StalenessKind
from crypto_systems_intelligence_atlas.promotion import ClaimStateEngine, IllegalClaimTransition
from crypto_systems_intelligence_atlas.research_interface import ResearchInterface
from crypto_systems_intelligence_atlas.sources import (
    AccessMethod,
    LocatorMetadata,
    Source,
    SourceRegistry,
    VerificationStatus,
)
from crypto_systems_intelligence_atlas.types import AuthoritySeed, AuthorityTier, ClaimFamily, SourceClass

NOW = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
LATER = NOW + timedelta(hours=1)


def source(source_id: str, source_class: SourceClass, family: ClaimFamily, tier: AuthorityTier) -> Source:
    return Source(
        source_id=source_id,
        source_class=source_class,
        canonical_name=source_id,
        locator=LocatorMetadata(
            base_locator=f"fixture://{source_id}",
            access_method=AccessMethod.DOCUMENT,
            authentication="none",
        ),
        authority_metadata=(
            AuthoritySeed(
                claim_family=family,
                tier=tier,
                valid_from=NOW - timedelta(days=1),
                policy_version="v1",
            ),
        ),
        verification_status=VerificationStatus.VERIFIED,
        verification_evidence_refs=(f"verification-{source_id}",),
        last_verified_at=NOW,
    )


def kernel(source_class: SourceClass = SourceClass.NATIVE_TECHNICAL, family: ClaimFamily = ClaimFamily.CHAIN_ARCHITECTURE, tier: AuthorityTier = AuthorityTier.PRIMARY):
    sources = SourceRegistry()
    src = source("csia:source:test", source_class, family, tier)
    sources.register(src)
    policy = AuthorityPolicy()
    policy.register_source(src)
    evidence = EvidenceStore(sources)
    return sources, policy, evidence, ClaimService(evidence, authority_policy=policy), src


def observed_claim(service: ClaimService, evidence: EvidenceStore, src: Source, claim_id: str, state: ClaimState = ClaimState.OBSERVED, content: bytes = b"x") -> Claim:
    item = evidence.capture(
        source_id=src.source_id,
        retrieved_at=NOW,
        content=content,
        content_locator=f"fixture://{claim_id}",
        raw_snapshot_ref=f"snapshot://{claim_id}",
        extractor_version="x",
        parser_version="p1",
        evidence_tier=EvidenceTier.FIRST_PARTY_DOC,
    )
    return service.add(
        Claim(
            claim_id=claim_id,
            evidence_refs=(item.evidence_id,),
            source_refs=(src.source_id,),
            proposition=Proposition(subject_refs=(claim_id,), predicate="state", object_ref="true"),
            claim_family=ClaimFamily.CHAIN_ARCHITECTURE,
            claim_state=state,
            valid_time_hypothesis=NOW,
            observed_time=NOW,
            methodology=Methodology(methodology_ref="direct", version="v1", description="direct"),
        )
    )


def test_press_release_attempting_structural_promotion_fails() -> None:
    _, _, evidence, service, src = kernel(SourceClass.NEWS, ClaimFamily.NARRATIVE, AuthorityTier.PRIMARY)
    with pytest.raises(ValueError):
        observed_claim(service, evidence, src, "press-structural")


def test_aggregator_sole_structural_authority_fails() -> None:
    _, _, evidence, service, src = kernel(SourceClass.AGGREGATOR, ClaimFamily.CHAIN_ARCHITECTURE, AuthorityTier.PRIMARY)
    with pytest.raises(ValueError):
        observed_claim(service, evidence, src, "aggregator-structural")


def test_unregistered_source_has_no_authority_or_evidence_ingress() -> None:
    sources = SourceRegistry()
    evidence = EvidenceStore(sources)
    policy = AuthorityPolicy()
    assert policy.resolve("csia:source:unknown", ClaimFamily.CHAIN_ARCHITECTURE, NOW).tier is AuthorityTier.UNREGISTERED
    with pytest.raises(KeyError):
        evidence.capture(
            source_id="csia:source:unknown",
            retrieved_at=NOW,
            content=b"x",
            content_locator="fixture://x",
            raw_snapshot_ref="snapshot://x",
            extractor_version="x",
            parser_version="p1",
            evidence_tier=EvidenceTier.FIRST_PARTY_DOC,
        )


def test_inferred_without_parents_fails() -> None:
    _, _, _, service, _ = kernel()
    with pytest.raises(ValueError):
        InferenceEngine(service).create(
            parent_claim_refs=(),
            methodology=Methodology(methodology_ref="m", version="v1", description="d"),
            proposition=Proposition(subject_refs=("x",), predicate="p", object_ref="y"),
            valid_time_hypothesis=NOW,
            valid_time_derivation="d",
            observed_time=NOW,
        )


def test_inferred_with_declared_parent_fails() -> None:
    _, _, evidence, service, src = kernel()
    declared = observed_claim(service, evidence, src, "declared-parent", state=ClaimState.DECLARED, content=b"declared")
    with pytest.raises(ValueError):
        InferenceEngine(service).create(
            parent_claim_refs=(declared.claim_id,),
            methodology=Methodology(methodology_ref="m", version="v1", description="d"),
            proposition=Proposition(subject_refs=("x",), predicate="p", object_ref="y"),
            valid_time_hypothesis=NOW,
            valid_time_derivation="d",
            observed_time=NOW,
        )


def test_inferred_without_methodology_fails() -> None:
    _, _, evidence, service, src = kernel()
    parent = observed_claim(service, evidence, src, "method-parent", content=b"parent")
    with pytest.raises(ValueError):
        InferenceEngine(service).create(
            parent_claim_refs=(parent.claim_id,),
            methodology=Methodology(methodology_ref="", version="v1", description="d"),
            proposition=Proposition(subject_refs=("x",), predicate="p", object_ref="y"),
            valid_time_hypothesis=NOW,
            valid_time_derivation="d",
            observed_time=NOW,
        )


def test_lineage_not_terminating_in_raw_evidence_fails() -> None:
    _, _, evidence, service, src = kernel()
    fake = Claim(
        claim_id="fake-parent",
        evidence_refs=("csia:evidence:missing",),
        source_refs=(src.source_id,),
        proposition=Proposition(subject_refs=("x",), predicate="p", object_ref="y"),
        claim_family=ClaimFamily.CHAIN_ARCHITECTURE,
        claim_state=ClaimState.OBSERVED,
        valid_time_hypothesis=NOW,
        observed_time=NOW,
        methodology=Methodology(methodology_ref="direct", version="v1", description="d"),
    )
    service.claim_store.add(fake)
    with pytest.raises(KeyError):
        InferenceEngine(service).create(
            parent_claim_refs=(fake.claim_id,),
            methodology=Methodology(methodology_ref="m", version="v1", description="d"),
            proposition=Proposition(subject_refs=("x",), predicate="p", object_ref="y"),
            valid_time_hypothesis=NOW,
            valid_time_derivation="d",
            observed_time=NOW,
        )


def test_inferred_to_observed_attempt_fails_closed() -> None:
    _, _, evidence, service, src = kernel()
    parent = observed_claim(service, evidence, src, "inference-parent", content=b"parent")
    inferred = InferenceEngine(service).create(
        parent_claim_refs=(parent.claim_id,),
        methodology=Methodology(methodology_ref="m", version="v1", description="d"),
        proposition=Proposition(subject_refs=("x",), predicate="p", object_ref="y"),
        valid_time_hypothesis=NOW,
        valid_time_derivation="parent window",
        observed_time=NOW,
    )
    with pytest.raises(IllegalClaimTransition):
        ClaimStateEngine(service).transition(
            inferred.claim_id,
            ClaimState.OBSERVED,
            triggering_evidence_refs=parent.evidence_refs,
            transitioned_at=LATER,
        )


def test_illegal_claim_state_transition_fails_closed() -> None:
    _, _, evidence, service, src = kernel()
    claim = observed_claim(service, evidence, src, "illegal-transition", content=b"illegal")
    with pytest.raises(IllegalClaimTransition):
        ClaimStateEngine(service).transition(
            claim.claim_id, ClaimState.DECLARED,
            triggering_evidence_refs=claim.evidence_refs, transitioned_at=LATER,
        )


def test_global_trust_score_surface_does_not_exist() -> None:
    policy = AuthorityPolicy()
    assert not hasattr(policy, "global_trust_score")
    assert not hasattr(policy, "trust_score")


def test_stale_to_rejected_conflation_fails_closed() -> None:
    _, _, evidence, service, src = kernel()
    claim = observed_claim(service, evidence, src, "stale-claim", content=b"stale")
    engine = ClaimStateEngine(service)
    engine.transition(claim.claim_id, ClaimState.STALE, triggering_evidence_refs=claim.evidence_refs, transitioned_at=LATER)
    with pytest.raises(IllegalClaimTransition):
        engine.transition(claim.claim_id, ClaimState.REJECTED, triggering_evidence_refs=claim.evidence_refs, transitioned_at=LATER)


def test_universal_stale_window_attempt_fails_closed() -> None:
    with pytest.raises(ValueError):
        FreshnessPolicy(
            policy_id="universal",
            version="v1",
            kind=StalenessKind.CLAIM_STALE,
            mode=FreshnessMode.HISTORICAL_NO_DECAY,
            max_age_seconds=3600,
        )


def test_contradiction_midpoint_average_surface_does_not_exist() -> None:
    _, policy, evidence, service, src = kernel(SourceClass.RPC, ClaimFamily.CHAIN_ARCHITECTURE, AuthorityTier.PRIMARY)
    left = observed_claim(service, evidence, src, "left-conflict", content=b"left")
    right = observed_claim(service, evidence, src, "right-conflict", content=b"right")
    engine = ContradictionEngine(policy)
    assert not hasattr(engine, "average")
    result = engine.resolve(
        left=left,
        right=right,
        claim_family=ClaimFamily.CHAIN_ARCHITECTURE,
        left_source_id=src.source_id,
        right_source_id=src.source_id,
        at=NOW,
    )
    assert result.kind is ResolutionKind.CONTESTED


@pytest.mark.parametrize("actor", ["Research Mesh", "QCAE", "OCE"])
def test_research_systems_have_no_direct_promotion_api(actor: str) -> None:
    sources, policy, evidence, service, src = kernel()
    research = ResearchInterface(source_registry=sources, evidence_store=evidence, claim_service=service)
    for operation in ("promote", "set_state", "set_authority", "mutate_graph", "mutate_time", "bypass_provenance"):
        assert not hasattr(research, operation)
    with pytest.raises(AttributeError):
        getattr(research, "promote")
