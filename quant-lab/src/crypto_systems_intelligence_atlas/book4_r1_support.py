"""Deterministic R1 support: fact-qualified canonical Book 2 claims for Book 4 hardening."""

from __future__ import annotations

from datetime import UTC, datetime

from crypto_systems_intelligence_atlas.authority import AuthorityPolicy
from crypto_systems_intelligence_atlas.claims import (
    Claim,
    ClaimService,
    ClaimState,
    ClaimStore,
    Methodology,
    Proposition,
)
from crypto_systems_intelligence_atlas.dependency import (
    FallbackState,
    HardRuntimeEvidence,
    HardRuntimeFact,
    HardRuntimeFactContextBinding,
)
from crypto_systems_intelligence_atlas.dependency_provenance import Book4Provenance
from crypto_systems_intelligence_atlas.evidence import EvidenceStore, EvidenceTier
from crypto_systems_intelligence_atlas.failure_domains import (
    FailureDomain,
    FailureDomainType,
    IndependenceClaimBinding,
)
from crypto_systems_intelligence_atlas.redundancy import (
    ActivationMode,
    RedundancyAssessment,
    RedundancyState,
)
from crypto_systems_intelligence_atlas.sources import (
    AccessMethod,
    LocatorMetadata,
    Source,
    SourceRegistry,
    VerificationStatus,
)
from crypto_systems_intelligence_atlas.types import AuthoritySeed, AuthorityTier, ClaimFamily, SourceClass

NOW = datetime(2026, 9, 25, 12, tzinfo=UTC)
SOURCE_ID = "csia:source:book4-r1"

R1_CONSUMER = "fixture:r1-consumer"
R1_PROVIDER = "fixture:r1-provider"
R1_FUNCTION = "submit liquidation transaction"
R1_SCOPE = "production liquidation"

GENERIC_CLAIM = "r1-generic-claim"
IDENTITY_CLAIM = "r1-fact-identity"
DEPLOYMENT_CLAIM = "r1-fact-deployment"
NECESSITY_CLAIM = "r1-fact-necessity"
FAILURE_CLAIM = "r1-fact-failure-consequence"
NO_FALLBACK_CLAIM = "r1-fact-no-active-fallback"
VALID_TIME_CLAIM = "r1-fact-valid-time"
ACTIVE_FALLBACK_CLAIM = "r1-fact-active-fallback"
MECHANISM_SHARED_CLAIM = "r1-mechanism-shared-backend"
MECHANISM_LEFT_CLAIM = "r1-mechanism-left"
MECHANISM_RIGHT_CLAIM = "r1-mechanism-right"
INDEPENDENCE_CLAIM = "r1-positive-independence"
INDEPENDENCE_CONTESTED_CLAIM = "r1-positive-independence-contested"

ALL_FACT_CLAIMS: dict[HardRuntimeFact, str] = {
    HardRuntimeFact.IDENTITY: IDENTITY_CLAIM,
    HardRuntimeFact.DEPLOYED_CONFIGURATION: DEPLOYMENT_CLAIM,
    HardRuntimeFact.RUNTIME_NECESSITY: NECESSITY_CLAIM,
    HardRuntimeFact.FAILURE_CONSEQUENCE: FAILURE_CLAIM,
    HardRuntimeFact.NO_ACTIVE_EQUIVALENT_FALLBACK: NO_FALLBACK_CLAIM,
    HardRuntimeFact.VALID_TIME: VALID_TIME_CLAIM,
}


def source_fixture() -> Source:
    return Source(
        source_id=SOURCE_ID,
        source_class=SourceClass.NATIVE_TECHNICAL,
        canonical_name="deterministic offline Book 4 R1 fixture",
        object_scope=(),
        locator=LocatorMetadata(
            base_locator="fixture://book4-r1",
            access_method=AccessMethod.DOCUMENT,
            authentication="none",
        ),
        authority_metadata=(
            AuthoritySeed(
                claim_family=ClaimFamily.CHAIN_ARCHITECTURE,
                tier=AuthorityTier.PRIMARY,
                valid_from=NOW,
                policy_version="book4-r1-fixture-v1",
            ),
        ),
        verification_status=VerificationStatus.VERIFIED,
        verification_evidence_refs=("r1-source-verification",),
        last_verified_at=NOW,
    )


def snapshot_ref(claim_id: str) -> str:
    return f"snapshot://book4-r1/{claim_id}"


_CONTEXT_QUALIFIERS = frozenset(
    {fact.value for fact in HardRuntimeFact} | {"ACTIVE_EQUIVALENT_FALLBACK"}
)


def make_claim(claim_id: str, qualifier: str | None) -> Claim:
    # Fact-class claims encode the assessment context in their proposition:
    # subject = consumer, object = provider (Book 2 has no function/scope
    # dimension; those live only in the typed Book 4 context binding).
    if qualifier in _CONTEXT_QUALIFIERS:
        subject_refs: tuple[str, ...] = (R1_CONSUMER,)
        object_ref = R1_PROVIDER
    else:
        subject_refs = ("fixture:r1-system",)
        object_ref = "fixture:r1-object"
    return Claim(
        claim_id=claim_id,
        evidence_refs=(f"evidence-{claim_id}",),
        source_refs=(SOURCE_ID,),
        proposition=Proposition(
            subject_refs=subject_refs,
            predicate="supports_book4_fact",
            object_ref=object_ref,
            qualifier=qualifier,
        ),
        claim_family=ClaimFamily.CHAIN_ARCHITECTURE,
        claim_state=ClaimState.OBSERVED,
        valid_time_hypothesis=NOW,
        observed_time=NOW,
        methodology=Methodology(
            methodology_ref="offline-book4-r1-fixture",
            version="1",
            description="deterministic offline Book 4 R1 test input",
        ),
    )


def claim_plan() -> tuple[tuple[str, str | None], ...]:
    return (
        (GENERIC_CLAIM, None),
        (IDENTITY_CLAIM, HardRuntimeFact.IDENTITY.value),
        (DEPLOYMENT_CLAIM, HardRuntimeFact.DEPLOYED_CONFIGURATION.value),
        (NECESSITY_CLAIM, HardRuntimeFact.RUNTIME_NECESSITY.value),
        (FAILURE_CLAIM, HardRuntimeFact.FAILURE_CONSEQUENCE.value),
        (NO_FALLBACK_CLAIM, HardRuntimeFact.NO_ACTIVE_EQUIVALENT_FALLBACK.value),
        (VALID_TIME_CLAIM, HardRuntimeFact.VALID_TIME.value),
        (ACTIVE_FALLBACK_CLAIM, "ACTIVE_EQUIVALENT_FALLBACK"),
        (MECHANISM_SHARED_CLAIM, "FAILURE_MECHANISM"),
        (MECHANISM_LEFT_CLAIM, "FAILURE_MECHANISM"),
        (MECHANISM_RIGHT_CLAIM, "FAILURE_MECHANISM"),
        (INDEPENDENCE_CLAIM, "POSITIVE_INDEPENDENCE"),
    )


def kernel() -> tuple[ClaimStore, EvidenceStore, Book4Provenance]:
    sources = SourceRegistry()
    sources.register(source_fixture())
    evidence = EvidenceStore(sources)
    claims = ClaimStore()
    for claim_id, qualifier in claim_plan():
        evidence_id = evidence.capture(
            source_id=SOURCE_ID,
            retrieved_at=NOW,
            content=f"book4 r1 evidence {claim_id}".encode(),
            content_locator=f"fixture://book4-r1/{claim_id}",
            raw_snapshot_ref=snapshot_ref(claim_id),
            extractor_version="test",
            parser_version="test",
            evidence_tier=EvidenceTier.FIRST_PARTY_DOC,
        ).evidence_id
        claim = make_claim(claim_id, qualifier)
        claim = claim.model_copy(update={"evidence_refs": (evidence_id,)})
        claims.add_initial(claim)
    return claims, evidence, Book4Provenance(claims, evidence)


def contested_kernel() -> tuple[ClaimService, str]:
    """Canonical service plus a claim transitioned to CONTESTED."""

    sources = SourceRegistry()
    source = source_fixture()
    sources.register(source)
    authority = AuthorityPolicy()
    authority.register_source(source)
    service = ClaimService(EvidenceStore(sources), authority_policy=authority)
    evidence_id = service.evidence_store.capture(
        source_id=SOURCE_ID,
        retrieved_at=NOW,
        content=b"book4 r1 independence evidence",
        content_locator="fixture://book4-r1/independence-contested",
        raw_snapshot_ref=snapshot_ref(INDEPENDENCE_CONTESTED_CLAIM),
        extractor_version="test",
        parser_version="test",
        evidence_tier=EvidenceTier.FIRST_PARTY_DOC,
    ).evidence_id
    claim = make_claim(INDEPENDENCE_CONTESTED_CLAIM, "POSITIVE_INDEPENDENCE")
    service.add_observed(claim.model_copy(update={"evidence_refs": (evidence_id,)}))
    for claim_id, qualifier in (
        (GENERIC_CLAIM, None),
        (MECHANISM_SHARED_CLAIM, "FAILURE_MECHANISM"),
        (MECHANISM_LEFT_CLAIM, "FAILURE_MECHANISM"),
    ):
        mechanism_evidence = service.evidence_store.capture(
            source_id=SOURCE_ID,
            retrieved_at=NOW,
            content=f"book4 r1 mechanism evidence {claim_id}".encode(),
            content_locator=f"fixture://book4-r1/{claim_id}",
            raw_snapshot_ref=snapshot_ref(claim_id),
            extractor_version="test",
            parser_version="test",
            evidence_tier=EvidenceTier.FIRST_PARTY_DOC,
        ).evidence_id
        service.add_observed(
            make_claim(claim_id, qualifier).model_copy(
                update={"evidence_refs": (mechanism_evidence,)}
            )
        )
    return service, evidence_id


def fact_bindings(
    omit: frozenset[HardRuntimeFact] = frozenset(),
) -> tuple[HardRuntimeFactContextBinding, ...]:
    return tuple(
        HardRuntimeFactContextBinding(
            fact=fact,
            claim_refs=(claim_ref,),
            consumer_ref=R1_CONSUMER,
            provider_ref=R1_PROVIDER,
            function=R1_FUNCTION,
            scope=R1_SCOPE,
        )
        for fact, claim_ref in ALL_FACT_CLAIMS.items()
        if fact not in omit
    )


def all_snapshot_refs() -> tuple[str, ...]:
    return tuple(sorted(snapshot_ref(claim_id) for claim_id, _ in claim_plan()))


def hard_evidence_r1(
    *,
    bindings: tuple[HardRuntimeFactContextBinding, ...] | None = None,
    book2_claim_refs: tuple[str, ...] | None = None,
    source_snapshot_refs: tuple[str, ...] | None = None,
    fallback_state: FallbackState = FallbackState.NONE,
    deployed_configuration_evidenced: bool = True,
    runtime_necessity_evidenced: bool = True,
    removal_makes_function_unavailable: bool = True,
) -> HardRuntimeEvidence:
    resolved = fact_bindings() if bindings is None else bindings
    claim_refs = (
        tuple(sorted({ref for binding in resolved for ref in binding.claim_refs}))
        if book2_claim_refs is None
        else book2_claim_refs
    )
    return HardRuntimeEvidence(
        consumer_ref=R1_CONSUMER,
        provider_ref=R1_PROVIDER,
        function=R1_FUNCTION,
        scope=R1_SCOPE,
        deployed_configuration_evidenced=deployed_configuration_evidenced,
        runtime_necessity_evidenced=runtime_necessity_evidenced,
        removal_makes_function_unavailable=removal_makes_function_unavailable,
        fallback_state=fallback_state,
        valid_time=NOW,
        book2_claim_refs=claim_refs,
        source_snapshot_refs=(
            tuple(sorted(snapshot_ref(ref) for ref in claim_refs))
            if source_snapshot_refs is None
            else source_snapshot_refs
        ),
        fact_bindings=resolved,
    )


def failure_domain_r1(
    domain_id: str,
    *,
    mechanism_claim_refs: tuple[str, ...],
    provider: str | None = None,
    operator: str | None = None,
    mechanism: str = "shared backend",
    mechanism_evidence_refs: tuple[str, ...] = (),
    system: str | None = None,
) -> FailureDomain:
    return FailureDomain(
        domain_id=domain_id,
        domain_type=FailureDomainType.PROVIDER,
        provider_refs=(provider,) if provider else (),
        operator_refs=(operator,) if operator else (),
        owner_refs=(),
        protocol_refs=(),
        affected_system_refs=(system or f"fixture:{domain_id}:system",),
        mechanism=mechanism,
        mechanism_claim_refs=mechanism_claim_refs,
        mechanism_evidence_refs=mechanism_evidence_refs,
        correlation_scope="fixture deployment",
        valid_time=NOW,
        book2_claim_refs=(GENERIC_CLAIM, *mechanism_claim_refs),
    )


def redundancy_r1(
    assessment_id: str,
    *,
    state: RedundancyState = RedundancyState.UNKNOWN,
    failure_domain_refs: tuple[str, ...] = (),
    positive_independence_claim_refs: tuple[str, ...] = (),
    shared_upstreams: tuple[str, ...] = (),
) -> RedundancyAssessment:
    bindings = tuple(
        IndependenceClaimBinding(
            claim_ref=claim_ref,
            left_domain_ref="fixture:r1-provider-a",
            right_domain_ref="fixture:r1-provider-b",
            left_system_ref=R1_CONSUMER,
            right_system_ref=R1_CONSUMER,
            correlation_scope="liquidation execution",
        )
        for claim_ref in positive_independence_claim_refs
    )
    return RedundancyAssessment(
        redundancy_id=assessment_id,
        subject_ref=R1_CONSUMER,
        function="liquidation execution",
        provider_refs=("fixture:r1-provider-a", "fixture:r1-provider-b"),
        activation_mode=ActivationMode.DEPLOYED,
        shared_upstreams=shared_upstreams,
        failure_domain_refs=failure_domain_refs,
        independence_dimensions=("operator", "backend"),
        positive_independence_claim_refs=positive_independence_claim_refs,
        independence_bindings=bindings,
        state=state,
        valid_time=NOW,
        book2_claim_refs=(GENERIC_CLAIM, *positive_independence_claim_refs),
    )


__all__ = [
    "ACTIVE_FALLBACK_CLAIM",
    "ALL_FACT_CLAIMS",
    "DEPLOYMENT_CLAIM",
    "FAILURE_CLAIM",
    "GENERIC_CLAIM",
    "IDENTITY_CLAIM",
    "INDEPENDENCE_CLAIM",
    "INDEPENDENCE_CONTESTED_CLAIM",
    "MECHANISM_LEFT_CLAIM",
    "MECHANISM_RIGHT_CLAIM",
    "MECHANISM_SHARED_CLAIM",
    "NECESSITY_CLAIM",
    "NO_FALLBACK_CLAIM",
    "NOW",
    "R1_CONSUMER",
    "R1_FUNCTION",
    "R1_PROVIDER",
    "R1_SCOPE",
    "VALID_TIME_CLAIM",
    "all_snapshot_refs",
    "contested_kernel",
    "fact_bindings",
    "failure_domain_r1",
    "hard_evidence_r1",
    "kernel",
    "redundancy_r1",
    "snapshot_ref",
]
