"""Book 2 deterministic kernel tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from crypto_systems_intelligence_atlas.acquisition import (
    AcquisitionContract,
    AcquisitionContractBook,
    AcquisitionObservation,
    AcquisitionType,
    AuthenticationKind,
    AuthenticationMetadata,
    CostMetadata,
    FailureState,
    RateLimitPolicy,
    RetrievalSemantics,
    RetryPolicy,
    SchemaDriftBehavior,
    SnapshotPolicy,
)
from crypto_systems_intelligence_atlas.authority import AuthorityPolicy
from crypto_systems_intelligence_atlas.claims import (
    Claim,
    ClaimService,
    ClaimState,
    InferenceEngine,
    Methodology,
    Proposition,
)
from crypto_systems_intelligence_atlas.changes import ChangeCandidateStore, ChangeClass
from crypto_systems_intelligence_atlas.evidence import (
    EvidenceStatus,
    EvidenceStore,
    EvidenceTier,
    content_hash_for,
)
from crypto_systems_intelligence_atlas.freshness import (
    FreshnessMode,
    FreshnessPolicy,
    FreshnessPolicyBook,
    StalenessKind,
)
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


def make_source(
    source_id: str,
    source_class: SourceClass,
    *,
    family: ClaimFamily = ClaimFamily.CHAIN_ARCHITECTURE,
    tier: AuthorityTier = AuthorityTier.PRIMARY,
) -> Source:
    return Source(
        source_id=source_id,
        source_class=source_class,
        canonical_name=source_id,
        object_scope=(),
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
                policy_version="authority-v1",
            ),
        ),
        verification_status=VerificationStatus.VERIFIED,
        verification_evidence_refs=(f"verification-{source_id}",),
        last_verified_at=NOW,
    )


def build_kernel():
    sources = SourceRegistry()
    authority = AuthorityPolicy()
    source = make_source("csia:source:spec", SourceClass.NATIVE_TECHNICAL)
    sources.register(source)
    authority.register_source(source)
    evidence = EvidenceStore(sources)
    service = ClaimService(evidence, authority_policy=authority)
    return sources, authority, evidence, service, source


def make_claim(
    service: ClaimService,
    evidence_store: EvidenceStore,
    source: Source,
    claim_id: str,
    *,
    state: ClaimState = ClaimState.OBSERVED,
    family: ClaimFamily = ClaimFamily.CHAIN_ARCHITECTURE,
    content: bytes = b"observed",
    locator: str = "fixture://claim",
) -> Claim:
    captured = evidence_store.capture(
        source_id=source.source_id,
        retrieved_at=NOW,
        content=content,
        content_locator=locator,
        raw_snapshot_ref=f"snapshot://{claim_id}",
        extractor_version="test-extractor",
        parser_version="test-parser",
        evidence_tier=EvidenceTier.FIRST_PARTY_DOC,
    )
    claim = Claim(
            claim_id=claim_id,
            evidence_refs=(captured.evidence_id,),
            source_refs=(source.source_id,),
            proposition=Proposition(
                subject_refs=(f"object-{claim_id}",), predicate="has_state", object_ref="true"
            ),
            claim_family=family,
            claim_state=state,
            valid_time_hypothesis=NOW,
            observed_time=NOW,
            methodology=Methodology(
                methodology_ref="direct-capture", version="v1", description="direct fixture observation"
            ),
        )
    return service.add_declared(claim) if claim.claim_state is ClaimState.DECLARED else service.add_observed(claim)


def test_source_locator_churn_preserves_identity_and_requires_evidence() -> None:
    sources = SourceRegistry()
    source = make_source("csia:source:docs", SourceClass.NATIVE_TECHNICAL)
    sources.register(source)
    updated = sources.update_locator(
        source.source_id,
        locator=LocatorMetadata(
            base_locator="fixture://docs-v2", access_method=AccessMethod.DOCUMENT, authentication="none"
        ),
        verification_evidence_refs=("evidence-locator",),
        at=LATER,
    )
    assert updated.source_id == source.source_id
    assert updated.version == 2
    assert len(sources.history(source.source_id)) == 2
    with pytest.raises(ValueError):
        sources.update_locator(
            source.source_id,
            locator=LocatorMetadata(
                base_locator="fixture://docs-v3", access_method=AccessMethod.DOCUMENT, authentication="none"
            ),
            verification_evidence_refs=(),
            at=LATER,
        )


def test_evidence_is_append_only_hash_stable_and_parser_upgrade_preserves_parent() -> None:
    sources, _, evidence, _, source = build_kernel()
    first = evidence.capture(
        source_id=source.source_id,
        retrieved_at=NOW,
        content=b"same",
        content_locator="fixture://v1",
        raw_snapshot_ref="snapshot://1",
        extractor_version="x",
        parser_version="p1",
        evidence_tier=EvidenceTier.FIRST_PARTY_DOC,
    )
    second = evidence.capture(
        source_id=source.source_id,
        retrieved_at=LATER,
        content=b"changed",
        content_locator="fixture://v2",
        raw_snapshot_ref="snapshot://2",
        extractor_version="x",
        parser_version="p1",
        evidence_tier=EvidenceTier.FIRST_PARTY_DOC,
    )
    assert first.content_hash == content_hash_for(b"same")
    assert first.evidence_id != second.evidence_id
    parsed = evidence.derive(
        first,
        evidence_id="csia:evidence:derived",
        retrieved_at=LATER,
        content=b"parsed",
        content_locator="fixture://parsed",
        raw_snapshot_ref="snapshot://parsed",
        extractor_version="x",
        parser_version="p2",
        evidence_tier=EvidenceTier.FIRST_PARTY_DOC,
    )
    assert first.parser_version == "p1"
    assert parsed.transformation_lineage == ("parse:" + first.evidence_id,)
    assert parsed.evidence_status is EvidenceStatus.PARSED
    assert sources.require(source.source_id).source_id == first.source_id
    with pytest.raises(ValueError):
        evidence.add(first)


@pytest.mark.parametrize("acquisition_type", tuple(AcquisitionType))
def test_acquisition_contract_covers_every_type_without_fetching(acquisition_type: AcquisitionType) -> None:
    contract = AcquisitionContract(
        contract_id=f"contract-{acquisition_type.value}",
        source_id="csia:source:spec",
        acquisition_type=acquisition_type,
        request_identity="method+params+block",
        retrieval_semantics=RetrievalSemantics.POINT_IN_TIME,
        snapshot_policy=SnapshotPolicy.CAPTURE_ON_CHANGE,
        freshness_expectation="SHORT",
        retry_semantics=RetryPolicy(max_attempts=2, backoff_seconds=(1,)),
        rate_limit_semantics=RateLimitPolicy(request_limit=10, window_seconds=60),
        schema_drift_behavior=SchemaDriftBehavior.RAW_FIRST_CAPTURE_AND_EVENT,
        authentication=AuthenticationMetadata(kind=AuthenticationKind.NONE, reference="none"),
        cost=CostMetadata(unit="request", estimated_cost=0, currency="USD"),
    )
    book = AcquisitionContractBook()
    book.register(contract)
    assert book.require(contract.contract_id).acquisition_type is acquisition_type
    failure = book.record(
        AcquisitionObservation(
            observation_id="obs-1",
            contract_id=contract.contract_id,
            attempted_at=NOW,
            succeeded=False,
            failure_state=FailureState.SCHEMA_DRIFT,
        )
    )
    assert failure.failure_state is FailureState.SCHEMA_DRIFT
    with pytest.raises(ValueError):
        book.record(
            AcquisitionObservation(
                observation_id="obs-2",
                contract_id=contract.contract_id,
                attempted_at=NOW,
                succeeded=True,
            )
        )


def test_create_inferred_preserves_parents_and_terminates_lineage() -> None:
    _, _, evidence, service, source = build_kernel()
    p1 = make_claim(service, evidence, source, "claim-p1", content=b"p1")
    p2 = make_claim(service, evidence, source, "claim-p2", content=b"p2")
    before = p1.model_dump(mode="json")
    inferred = InferenceEngine(service).create(
        parent_claim_refs=(p1.claim_id, p2.claim_id),
        methodology=Methodology(
            methodology_ref="dependency-risk",
            version="v1",
            description="derive qualified availability risk from dependency and outage claims",
        ),
        proposition=Proposition(
            subject_refs=("protocol-p",), predicate="may_have_degraded", object_ref="oracle-o"
        ),
        valid_time_hypothesis=NOW,
        valid_time_derivation="intersection of parent valid-time hypotheses",
        observed_time=LATER,
        claim_family=ClaimFamily.CHAIN_ARCHITECTURE,
    )
    assert inferred.claim_id not in (p1.claim_id, p2.claim_id)
    assert inferred.claim_state is ClaimState.INFERRED
    assert inferred.parent_claim_states == (ClaimState.OBSERVED, ClaimState.OBSERVED)
    assert p1.model_dump(mode="json") == before
    assert set(inferred.lineage_evidence_refs) == set(service.lineage_evidence(inferred))
    with pytest.raises(IllegalClaimTransition):
        ClaimStateEngine(service).transition(
            inferred.claim_id,
            ClaimState.OBSERVED,
            triggering_evidence_refs=(p1.evidence_refs[0],),
            transitioned_at=LATER,
        )


def test_inference_rejects_missing_parent_declared_parent_and_methodology() -> None:
    _, _, evidence, service, source = build_kernel()
    observed = make_claim(service, evidence, source, "claim-observed")
    declared = make_claim(
        service, evidence, source, "claim-declared", state=ClaimState.DECLARED, content=b"declared"
    )
    engine = InferenceEngine(service)
    kwargs = {
        "methodology": Methodology(methodology_ref="m", version="v1", description="description"),
        "proposition": Proposition(subject_refs=("x",), predicate="implies", object_ref="y"),
        "valid_time_hypothesis": NOW,
        "valid_time_derivation": "parent window",
        "observed_time": LATER,
    }
    with pytest.raises(ValueError):
        engine.create(parent_claim_refs=(), **kwargs)
    with pytest.raises(ValueError):
        engine.create(parent_claim_refs=(declared.claim_id,), **kwargs)
    with pytest.raises(ValueError):
        engine.create(
            parent_claim_refs=(observed.claim_id,),
            **{
                **kwargs,
                "methodology": Methodology(methodology_ref="", version="v1", description="description"),
            },
        )


def test_claim_state_transitions_preserve_history_and_reject_illegal_paths() -> None:
    _, _, evidence, service, source = build_kernel()
    claim = make_claim(service, evidence, source, "claim-transition")
    second = make_source("csia:source:second", SourceClass.RPC).model_copy(update={"owner_entity_ref": "owner:second"})
    sources, authority, evidence, service, source = build_kernel()
    claim = make_claim(service, evidence, source, "claim-transition")
    sources.register(second)
    authority.register_source(second)
    corroborating = make_claim(service, evidence, second, "claim-corroborating")
    engine = ClaimStateEngine(service)
    corroborated = engine.transition(
        claim.claim_id,
        ClaimState.CORROBORATED,
        triggering_evidence_refs=corroborating.evidence_refs,
        corroborating_claim_id=corroborating.claim_id,
        transitioned_at=LATER,
    )
    assert corroborated.claim_state is ClaimState.CORROBORATED
    assert len(service.claim_store.history(claim.claim_id)) == 2
    with pytest.raises(IllegalClaimTransition):
        engine.transition(
            claim.claim_id,
            ClaimState.OBSERVED,
            triggering_evidence_refs=claim.evidence_refs,
            transitioned_at=LATER,
        )


def test_authority_is_family_scoped_and_single_discrepancy_does_not_demote() -> None:
    sources = SourceRegistry()
    authority = AuthorityPolicy()
    docs = make_source("csia:source:docs", SourceClass.NATIVE_TECHNICAL, family=ClaimFamily.DEPLOYMENT_ACTIVATION, tier=AuthorityTier.SUPPORTING)
    chain = make_source("csia:source:rpc", SourceClass.RPC, family=ClaimFamily.DEPLOYMENT_ACTIVATION, tier=AuthorityTier.PRIMARY)
    sources.register(docs)
    sources.register(chain)
    authority.register_source(docs)
    authority.register_source(chain)
    assert authority.resolve(docs.source_id, ClaimFamily.DEPLOYMENT_ACTIVATION, NOW).tier is AuthorityTier.SUPPORTING
    assert authority.resolve(chain.source_id, ClaimFamily.DEPLOYMENT_ACTIVATION, NOW).tier is AuthorityTier.PRIMARY
    authority.record_discrepancy(
        source_id=docs.source_id,
        claim_family=ClaimFamily.DEPLOYMENT_ACTIVATION,
        valid_time=NOW,
        evidence_refs=("e1",),
        meta_claim_ref="meta-1",
        observed_at=LATER,
    )
    assert authority.resolve(docs.source_id, ClaimFamily.DEPLOYMENT_ACTIVATION, NOW).tier is AuthorityTier.SUPPORTING
    with pytest.raises(ValueError):
        authority.downgrade(
            source_id=docs.source_id,
            claim_family=ClaimFamily.DEPLOYMENT_ACTIVATION,
            valid_from=NOW,
            valid_to=None,
            new_tier=AuthorityTier.INSUFFICIENT,
            repeated_evidence_refs=("e1",),
            discrepancy_meta_claim_refs=("meta-1",),
            policy_version="v2",
            effective_at=LATER,
            operator_review_ref="review-1",
        )
    decision = authority.downgrade(
        source_id=docs.source_id,
        claim_family=ClaimFamily.DEPLOYMENT_ACTIVATION,
        valid_from=NOW,
        valid_to=None,
        new_tier=AuthorityTier.INSUFFICIENT,
        repeated_evidence_refs=("e1", "e2"),
        discrepancy_meta_claim_refs=("meta-1", "meta-2"),
        policy_version="v2",
        effective_at=LATER,
        operator_review_ref="review-1",
    )
    assert decision.reversible is True
    authority.restore(decision, evidence_refs=("e3",), effective_at=LATER + timedelta(hours=1), operator_review_ref="review-2")
    assert len(authority.decisions) == 2


def test_freshness_policies_are_versioned_and_historical_does_not_decay() -> None:
    book = FreshnessPolicyBook()
    book.register(
        FreshnessPolicy(
            policy_id="rpc", version="v1", kind=StalenessKind.EVIDENCE_STALE,
            mode=FreshnessMode.SHORT, max_age_seconds=60,
        )
    )
    book.register(
        FreshnessPolicy(
            policy_id="rpc", version="v2", kind=StalenessKind.EVIDENCE_STALE,
            mode=FreshnessMode.SHORT, max_age_seconds=120,
        )
    )
    book.register(
        FreshnessPolicy(
            policy_id="genesis", version="v1", kind=StalenessKind.CLAIM_STALE,
            mode=FreshnessMode.HISTORICAL_NO_DECAY,
        )
    )
    old = book.evaluate("rpc", observed_at=NOW, now=NOW + timedelta(seconds=61), version="v1")
    new = book.evaluate("rpc", observed_at=NOW, now=NOW + timedelta(seconds=61), version="v2")
    historical = book.evaluate("genesis", observed_at=NOW, now=NOW + timedelta(days=3650))
    assert old.stale is True
    assert new.stale is False
    assert historical.stale is False


def test_change_candidate_is_not_graph_truth_and_research_api_has_no_promotion() -> None:
    changes = ChangeCandidateStore()
    candidate = changes.detect(
        change_class=ChangeClass.NEW_DEPLOYMENT,
        before_evidence_refs=("before",),
        after_evidence_refs=("after",),
        valid_time_hint=NOW,
        detected_at=LATER,
    )
    assert changes.require(candidate.candidate_id).change_class is ChangeClass.NEW_DEPLOYMENT
    sources, _, evidence, service, source = build_kernel()
    research = ResearchInterface(source_registry=sources, evidence_store=evidence, claim_service=service)
    for forbidden in ("promote", "set_state", "set_authority", "mutate_graph", "mutate_time", "bypass_provenance"):
        assert not hasattr(research, forbidden)
    with pytest.raises(ValueError):
        research.discover(source)
