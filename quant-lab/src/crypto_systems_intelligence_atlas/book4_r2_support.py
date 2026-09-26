"""Deterministic R2 support: context-bound Book 4 bindings for hardening R2.

Book 4 scoped only.  No Book 2 mutation, no second epistemic engine, and no
Sensor changes.  Canonical Book 2 claims remain the only authority; the typed
Book 4 records here merely declare the exact comparison or fact context a
canonical claim supports.

Proposition encoding used by these fixtures (the fields Book 4 can actually
check):

- HARD_RUNTIME fact claims: ``subject_refs = (consumer,)``,
  ``object_ref = provider``.  Function/scope have no Proposition dimension,
  so they live only in the typed ``HardRuntimeFactContextBinding``.
- Pair FAILURE_MECHANISM claims: ``subject_refs = (left, right)``,
  ``object_ref = "r2-shared-mechanism"``.
- Pair POSITIVE_INDEPENDENCE claims: ``subject_refs = (left_system,)``,
  ``object_ref = right_system``.
- Redundancy POSITIVE_INDEPENDENCE claims: ``subject_refs = (subject,)``,
  ``object_ref = subject`` (the provider pair lives in the binding).
"""

from __future__ import annotations

from crypto_systems_intelligence_atlas.book4_r1_support import NOW as R2_NOW
from crypto_systems_intelligence_atlas.book4_r1_support import SOURCE_ID
from crypto_systems_intelligence_atlas.claims import (
    Claim,
    ClaimState,
    ClaimStore,
    Methodology,
    Proposition,
)
from crypto_systems_intelligence_atlas.dependency import (
    HardRuntimeFact,
    HardRuntimeFactContextBinding,
)
from crypto_systems_intelligence_atlas.dependency_provenance import Book4Provenance
from crypto_systems_intelligence_atlas.evidence import EvidenceStore, EvidenceTier
from crypto_systems_intelligence_atlas.failure_domains import (
    FAILURE_MECHANISM_QUALIFIER,
    FailureDomain,
    FailureDomainType,
    IndependenceClaimBinding,
)
from crypto_systems_intelligence_atlas.redundancy import (
    ActivationMode,
    RedundancyAssessment,
    RedundancyState,
)
from crypto_systems_intelligence_atlas.sources import SourceRegistry
from crypto_systems_intelligence_atlas.types import ClaimFamily

R2_KERNEL_ID = "r2-kernel"
GENERIC_PLACEHOLDER = "r2-generic-claim"
INDEPENDENT_SUFFIX = "independent"
SHARED_SUFFIX = "shared"
R2_MECHANISM_OBJECT = "r2-shared-mechanism"
R2_FACT_CONSUMER = "consumer-a"
R2_FACT_PROVIDER = "provider-a"
R2_FACT_FUNCTION = "function-a"
R2_FACT_SCOPE = "scope-a"
R2_REDUNDANCY_SUBJECT = "fixture:redundancy-subject"
R2_REDUNDANCY_FUNCTION = "liquidation execution"


def snapshot_ref(claim_id: str) -> str:
    return f"snapshot://book4-r2/{claim_id}"


def mechanism_claim(left: str, right: str, *, variant: str = INDEPENDENT_SUFFIX) -> str:
    return f"r2-mechanism-{left.lower()}-{right.lower()}-{variant}"


def independence_claim(left: str, right: str, *, variant: str = INDEPENDENT_SUFFIX) -> str:
    return f"r2-independence-{left.lower()}-{right.lower()}-{variant}"


def redundancy_independence_claim(subject: str = R2_REDUNDANCY_SUBJECT) -> str:
    return f"r2-redundancy-independence-{subject}"


def fact_claim_for(
    fact: HardRuntimeFact,
    *,
    consumer: str,
    provider: str,
    function: str,
    scope: str,
) -> str:
    """Deterministic canonical claim ID for an exact HARD_RUNTIME context."""

    return f"{fact.value.lower()}-{consumer}-{provider}-{function}-{scope}"


def _r2_claim_plan() -> tuple[tuple[str, str | None, tuple[str, ...], str], ...]:
    """Every canonical R2 claim: ID, qualifier, subject_refs, object_ref."""

    plan: list[tuple[str, str | None, tuple[str, ...], str]] = [
        (GENERIC_PLACEHOLDER, None, (GENERIC_PLACEHOLDER,), GENERIC_PLACEHOLDER)
    ]
    for suffix in (INDEPENDENT_SUFFIX, SHARED_SUFFIX):
        for left in ("A", "B", "X", "Y"):
            for right in ("A", "B", "X", "Y"):
                if left == right:
                    continue
                left_system = f"system-{left.lower()}"
                right_system = f"system-{right.lower()}"
                plan.append(
                    (
                        mechanism_claim(left, right, variant=suffix),
                        FAILURE_MECHANISM_QUALIFIER,
                        (left_system, right_system),
                        R2_MECHANISM_OBJECT,
                    )
                )
                plan.append(
                    (
                        independence_claim(left, right, variant=suffix),
                        "POSITIVE_INDEPENDENCE",
                        (left_system,),
                        right_system,
                    )
                )
    plan.append(
        (
            redundancy_independence_claim(),
            "POSITIVE_INDEPENDENCE",
            (R2_REDUNDANCY_SUBJECT,),
            R2_REDUNDANCY_SUBJECT,
        )
    )
    for fact in HardRuntimeFact:
        for consumer in ("consumer-a", "consumer-b"):
            for provider in ("provider-a", "provider-b"):
                for function in ("function-a", "function-b"):
                    for scope in ("scope-a", "scope-b"):
                        plan.append(
                            (
                                fact_claim_for(
                                    fact,
                                    consumer=consumer,
                                    provider=provider,
                                    function=function,
                                    scope=scope,
                                ),
                                fact.value,
                                (consumer,),
                                provider,
                            )
                        )
    return tuple(plan)


def _r2_make_claim(
    claim_id: str,
    qualifier: str | None,
    subject_refs: tuple[str, ...],
    object_ref: str,
) -> Claim:
    """Canonical OBSERVED Book 2 claim with an explicit proposition."""

    return Claim(
        claim_id=claim_id,
        evidence_refs=(f"r2-evidence-{claim_id}",),
        source_refs=(SOURCE_ID,),
        proposition=Proposition(
            subject_refs=subject_refs,
            predicate="asserts_r2_context",
            object_ref=object_ref,
            qualifier=qualifier,
        ),
        claim_family=ClaimFamily.CHAIN_ARCHITECTURE,
        claim_state=ClaimState.OBSERVED,
        valid_time_hypothesis=R2_NOW,
        observed_time=R2_NOW,
        methodology=Methodology(
            methodology_ref="offline-book4-r2-fixture",
            version="1",
            description="deterministic offline Book 4 R2 test input",
        ),
    )


def kernel() -> tuple[ClaimStore, EvidenceStore, Book4Provenance]:
    """Build the deterministic context-distinct R2 claim kernel."""

    from crypto_systems_intelligence_atlas.book4_r1_support import source_fixture

    registry = SourceRegistry()
    registry.register(source_fixture())
    evidence = EvidenceStore(registry)
    claims = ClaimStore()
    for claim_id, qualifier, subject_refs, object_ref in _r2_claim_plan():
        evidence_id = evidence.capture(
            source_id=SOURCE_ID,
            retrieved_at=R2_NOW,
            content=f"book4 r2 evidence {claim_id}".encode(),
            content_locator=f"fixture://book4-r2/{claim_id}",
            raw_snapshot_ref=snapshot_ref(claim_id),
            extractor_version="test",
            parser_version="test",
            evidence_tier=EvidenceTier.FIRST_PARTY_DOC,
        ).evidence_id
        claims.add_initial(
            _r2_make_claim(claim_id, qualifier, subject_refs, object_ref).model_copy(
                update={"evidence_refs": (evidence_id,)}
            )
        )
    return claims, evidence, Book4Provenance(claims, evidence)


def add_derived_evidence_claim(
    claims: ClaimStore,
    evidence: EvidenceStore,
    *,
    claim_id: str,
    parent_claim_ref: str,
) -> str:
    """Add a canonical claim whose evidence derives from the parent's snapshot.

    The derived evidence record carries the same ``raw_snapshot_ref`` as its
    parent, so two distinct canonical claims can share one raw snapshot.
    """

    parent_claim = claims.require(parent_claim_ref)
    parent = evidence.require(parent_claim.evidence_refs[0])
    child = evidence.derive(
        parent,
        evidence_id=f"r2-derived-evidence-{claim_id}",
        retrieved_at=R2_NOW,
        content=f"book4 r2 derived evidence {claim_id}".encode(),
        content_locator=f"fixture://book4-r2/derived/{claim_id}",
        raw_snapshot_ref=parent.raw_snapshot_ref,
        extractor_version="test",
        parser_version="test",
        evidence_tier=EvidenceTier.FIRST_PARTY_DOC,
    )
    claims.add_initial(
        _r2_make_claim(
            claim_id,
            None,
            (claim_id,),
            claim_id,
        ).model_copy(update={"evidence_refs": (child.evidence_id,)})
    )
    return claim_id


def context_binding(
    fact: HardRuntimeFact,
    *,
    claim_ref: str,
    consumer_ref: str,
    provider_ref: str,
    function: str,
    scope: str,
) -> HardRuntimeFactContextBinding:
    return HardRuntimeFactContextBinding(
        fact=fact,
        claim_refs=(claim_ref,),
        consumer_ref=consumer_ref,
        provider_ref=provider_ref,
        function=function,
        scope=scope,
    )


def context_bindings(
    *,
    consumer: str = R2_FACT_CONSUMER,
    provider: str = R2_FACT_PROVIDER,
    function: str = R2_FACT_FUNCTION,
    scope: str = R2_FACT_SCOPE,
) -> tuple[HardRuntimeFactContextBinding, ...]:
    """Canonical fact bindings for the exact assessment context."""

    return tuple(
        context_binding(
            fact,
            claim_ref=fact_claim_for(
                fact,
                consumer=consumer,
                provider=provider,
                function=function,
                scope=scope,
            ),
            consumer_ref=consumer,
            provider_ref=provider,
            function=function,
            scope=scope,
        )
        for fact in HardRuntimeFact
    )


def with_fact_claim(
    bindings: tuple[HardRuntimeFactContextBinding, ...],
    fact: HardRuntimeFact,
    claim_ref: str,
) -> tuple[HardRuntimeFactContextBinding, ...]:
    """Return bindings with ``fact`` re-bound to ``claim_ref``."""

    return tuple(
        (
            context_binding(
                binding.fact,
                claim_ref=claim_ref,
                consumer_ref=binding.consumer_ref,
                provider_ref=binding.provider_ref,
                function=binding.function,
                scope=binding.scope,
            )
            if binding.fact is fact
            else binding
        )
        for binding in bindings
    )


def pair_mechanism_domain(
    domain_id: str,
    *,
    left: str,
    right: str,
    left_system: str | None = None,
    right_system: str | None = None,
    variant: str = SHARED_SUFFIX,
    book2_claim_refs: tuple[str, ...] | None = None,
    correlation_scope: str = "fixture deployment",
) -> FailureDomain:
    """Failure domain whose mechanism claim is pair-scoped and canonical."""

    return r2_failure_domain(
        domain_id,
        system=left_system or f"system-{left.lower()}",
        mechanism_claim_refs=(mechanism_claim(left, right, variant=variant),),
        book2_claim_refs=book2_claim_refs,
        correlation_scope=correlation_scope,
        right_system=right_system or f"system-{right.lower()}",
    )


def r2_failure_domain(
    domain_id: str,
    *,
    system: str,
    mechanism_claim_refs: tuple[str, ...],
    book2_claim_refs: tuple[str, ...] | None = None,
    provider: str | None = None,
    correlation_scope: str = "fixture deployment",
    right_system: str | None = None,
) -> FailureDomain:
    return FailureDomain(
        domain_id=domain_id,
        domain_type=FailureDomainType.PROVIDER,
        provider_refs=(provider,) if provider else (),
        operator_refs=(),
        owner_refs=(),
        protocol_refs=(),
        affected_system_refs=(system, right_system) if right_system else (system,),
        mechanism=f"r2 mechanism for {domain_id}",
        mechanism_claim_refs=mechanism_claim_refs,
        mechanism_evidence_refs=(),
        correlation_scope=correlation_scope,
        valid_time=R2_NOW,
        book2_claim_refs=(
            (GENERIC_PLACEHOLDER, *mechanism_claim_refs)
            if book2_claim_refs is None
            else book2_claim_refs
        ),
    )


def domain_independence_binding(
    claim_ref: str,
    *,
    left_domain_id: str,
    right_domain_id: str,
    left_system: str,
    right_system: str,
    scope: str = "fixture deployment",
) -> IndependenceClaimBinding:
    return IndependenceClaimBinding(
        claim_ref=claim_ref,
        left_domain_ref=left_domain_id,
        right_domain_ref=right_domain_id,
        left_system_ref=left_system,
        right_system_ref=right_system,
        correlation_scope=scope,
    )


def provider_refs_for(pair: str) -> tuple[str, ...]:
    left, right = pair.split("/")
    return (f"provider-{left.lower()}", f"provider-{right.lower()}")


def redundancy_independence_binding(
    claim_ref: str,
    *,
    providers: tuple[str, ...],
    subject: str = R2_REDUNDANCY_SUBJECT,
    function: str = R2_REDUNDANCY_FUNCTION,
) -> IndependenceClaimBinding:
    left_provider, right_provider = providers[0], providers[1]
    return IndependenceClaimBinding(
        claim_ref=claim_ref,
        left_domain_ref=left_provider,
        right_domain_ref=right_provider,
        left_system_ref=subject,
        right_system_ref=subject,
        correlation_scope=function,
    )


def r2_redundancy(
    assessment_id: str,
    *,
    subject_ref: str = R2_REDUNDANCY_SUBJECT,
    function: str = R2_REDUNDANCY_FUNCTION,
    provider_refs: tuple[str, ...],
    state: RedundancyState = RedundancyState.UNKNOWN,
    positive_independence_claim_refs: tuple[str, ...] = (),
    book2_claim_refs: tuple[str, ...] | None = None,
    independence_bindings: tuple[IndependenceClaimBinding, ...] = (),
    failure_domain_refs: tuple[str, ...] = (),
    shared_upstreams: tuple[str, ...] = (),
) -> RedundancyAssessment:
    return RedundancyAssessment(
        redundancy_id=assessment_id,
        subject_ref=subject_ref,
        function=function,
        provider_refs=provider_refs,
        activation_mode=ActivationMode.DEPLOYED,
        shared_upstreams=shared_upstreams,
        failure_domain_refs=failure_domain_refs,
        independence_dimensions=("operator", "backend"),
        positive_independence_claim_refs=positive_independence_claim_refs,
        independence_bindings=independence_bindings,
        state=state,
        valid_time=R2_NOW,
        book2_claim_refs=(
            (GENERIC_PLACEHOLDER,) if book2_claim_refs is None else book2_claim_refs
        ),
    )


__all__ = [
    "GENERIC_PLACEHOLDER",
    "INDEPENDENT_SUFFIX",
    "R2_FACT_CONSUMER",
    "R2_FACT_FUNCTION",
    "R2_FACT_PROVIDER",
    "R2_FACT_SCOPE",
    "R2_KERNEL_ID",
    "R2_MECHANISM_OBJECT",
    "R2_NOW",
    "R2_REDUNDANCY_FUNCTION",
    "R2_REDUNDANCY_SUBJECT",
    "SHARED_SUFFIX",
    "add_derived_evidence_claim",
    "context_binding",
    "context_bindings",
    "domain_independence_binding",
    "fact_claim_for",
    "independence_claim",
    "kernel",
    "mechanism_claim",
    "pair_mechanism_domain",
    "provider_refs_for",
    "r2_failure_domain",
    "r2_redundancy",
    "redundancy_independence_binding",
    "redundancy_independence_claim",
    "snapshot_ref",
    "with_fact_claim",
]
