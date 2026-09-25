"""Shared deterministic fixtures for Book 4 offline tests."""

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
    DependencyClass,
    DependencyRecord,
    DependencyStrengthDescriptor,
    DependencyStrengthState,
    FallbackState,
    HardRuntimeEvidence,
    RuntimeScope,
)
from crypto_systems_intelligence_atlas.dependency_paths import DependencyPath, PathRelation
from crypto_systems_intelligence_atlas.dependency_provenance import Book4Provenance
from crypto_systems_intelligence_atlas.evidence import EvidenceStore, EvidenceTier
from crypto_systems_intelligence_atlas.failure_domains import FailureDomain, FailureDomainType
from crypto_systems_intelligence_atlas.infrastructure_context import InfrastructureContext
from crypto_systems_intelligence_atlas.protocol_roles import ProtocolRole, RoleAssignment, RoleState
from crypto_systems_intelligence_atlas.redundancy import (
    ActivationMode,
    RedundancyAssessment,
    RedundancyState,
)
from crypto_systems_intelligence_atlas.relationships import EdgeType
from crypto_systems_intelligence_atlas.sources import (
    AccessMethod,
    LocatorMetadata,
    Source,
    SourceRegistry,
    VerificationStatus,
)
from crypto_systems_intelligence_atlas.substitutability import (
    ChangeClass,
    SubstitutabilityAssessment,
    SubstitutabilityDirection,
)
from crypto_systems_intelligence_atlas.types import AuthoritySeed, AuthorityTier, ClaimFamily, SourceClass

NOW = datetime(2026, 9, 25, 12, tzinfo=UTC)
CLAIM_REF = "book4-claim-current"


def source_fixture() -> Source:
    return Source(
        source_id="csia:source:book4-offline",
        source_class=SourceClass.NATIVE_TECHNICAL,
        canonical_name="deterministic offline Book 4 fixture",
        object_scope=(),
        locator=LocatorMetadata(
            base_locator="fixture://book4",
            access_method=AccessMethod.DOCUMENT,
            authentication="none",
        ),
        authority_metadata=(
            AuthoritySeed(
                claim_family=ClaimFamily.CHAIN_ARCHITECTURE,
                tier=AuthorityTier.PRIMARY,
                valid_from=NOW,
                policy_version="book4-fixture-v1",
            ),
        ),
        verification_status=VerificationStatus.VERIFIED,
        verification_evidence_refs=("book4-source-verification",),
        last_verified_at=NOW,
    )


def make_claim(claim_id: str = CLAIM_REF, evidence_ref: str = "book4-evidence") -> Claim:
    return Claim(
        claim_id=claim_id,
        evidence_refs=(evidence_ref,),
        source_refs=("csia:source:book4-offline",),
        proposition=Proposition(
            subject_refs=("fixture:system",),
            predicate="has_infrastructure_role",
            object_ref=claim_id,
        ),
        claim_family=ClaimFamily.CHAIN_ARCHITECTURE,
        claim_state=ClaimState.OBSERVED,
        valid_time_hypothesis=NOW,
        observed_time=NOW,
        methodology=Methodology(
            methodology_ref="offline-book4-fixture",
            version="1",
            description="deterministic offline Book 4 test input",
        ),
    )


def kernel() -> tuple[ClaimStore, EvidenceStore, Book4Provenance]:
    sources = SourceRegistry()
    sources.register(source_fixture())
    evidence = EvidenceStore(sources)
    evidence_ref = evidence.capture(
        source_id="csia:source:book4-offline",
        retrieved_at=NOW,
        content=b"book4 deterministic evidence",
        content_locator="fixture://book4/evidence",
        raw_snapshot_ref="snapshot://book4/evidence",
        extractor_version="test",
        parser_version="test",
        evidence_tier=EvidenceTier.FIRST_PARTY_DOC,
    ).evidence_id
    claims = ClaimStore()
    claims.add_initial(make_claim(evidence_ref=evidence_ref))
    return claims, evidence, Book4Provenance(claims, evidence)


def service_kernel() -> ClaimService:
    sources = SourceRegistry()
    source = source_fixture()
    sources.register(source)
    authority = AuthorityPolicy()
    authority.register_source(source)
    service = ClaimService(EvidenceStore(sources), authority_policy=authority)
    evidence_ref = service.evidence_store.capture(
        source_id=source.source_id,
        retrieved_at=NOW,
        content=b"transition evidence",
        content_locator="fixture://book4/transition",
        raw_snapshot_ref="snapshot://book4/transition",
        extractor_version="test",
        parser_version="test",
        evidence_tier=EvidenceTier.FIRST_PARTY_DOC,
    ).evidence_id
    service.add_observed(make_claim("book4-transition", evidence_ref))
    return service


def descriptor(
    *, state: DependencyStrengthState = DependencyStrengthState.PRIMARY
) -> DependencyStrengthDescriptor:
    return DependencyStrengthDescriptor(
        state=state,
        function="execute liquidation",
        scope="liquidation execution",
        mechanism="configured oracle call",
        valid_time=NOW,
        book2_claim_refs=(CLAIM_REF,),
    )


def record(
    record_id: str,
    *,
    relation: EdgeType = EdgeType.DEPENDS_ON,
    runtime_scope: RuntimeScope = RuntimeScope.SOFT_RUNTIME,
    strength: DependencyStrengthState = DependencyStrengthState.PRIMARY,
) -> DependencyRecord:
    return DependencyRecord(
        dependency_id=record_id,
        subject_ref=f"fixture:{record_id}:subject",
        object_ref=f"fixture:{record_id}:object",
        function="execute liquidation",
        scope="liquidation execution",
        relation_basis=relation,
        dependency_class=DependencyClass.DIRECT_RUNTIME,
        runtime_scope=runtime_scope,
        strength_descriptor=descriptor(state=strength),
        mechanism="configured service call",
        valid_time=NOW,
        book2_claim_refs=(CLAIM_REF,),
        source_snapshot_refs=("snapshot://book4/evidence",),
    )


def path(path_id: str = "path-abc") -> DependencyPath:
    return DependencyPath(
        path_id=path_id,
        subject_ref="A",
        target_ref="C",
        ordered_nodes=("A", "B", "C"),
        ordered_relations=(
            PathRelation(subject_ref="A", object_ref="B", relation=EdgeType.DEPENDS_ON),
            PathRelation(subject_ref="B", object_ref="C", relation=EdgeType.DEPENDS_ON),
        ),
        path_length=2,
        valid_time=NOW,
        book2_claim_refs=(CLAIM_REF,),
        source_snapshot_refs=("snapshot://book4/evidence",),
    )


def hard_evidence(**updates: object) -> HardRuntimeEvidence:
    values: dict[str, object] = {
        "consumer_ref": "fixture:liquidation-contract",
        "provider_ref": "fixture:rpc-primary",
        "function": "submit liquidation transaction",
        "scope": "production liquidation",
        "deployed_configuration_evidenced": True,
        "runtime_necessity_evidenced": True,
        "removal_makes_function_unavailable": True,
        "fallback_state": FallbackState.NONE,
        "valid_time": NOW,
        "book2_claim_refs": (CLAIM_REF,),
        "source_snapshot_refs": ("snapshot://book4/evidence",),
    }
    values.update(updates)
    return HardRuntimeEvidence.model_validate(values)


def failure_domain(
    domain_id: str,
    *,
    provider: str | None = None,
    operator: str | None = None,
    mechanism: str = "independent backend",
    evidence_ref: str = "mechanism-a",
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
        mechanism_evidence_refs=(evidence_ref,),
        correlation_scope="fixture deployment",
        valid_time=NOW,
        book2_claim_refs=(CLAIM_REF,),
    )


def redundancy(
    assessment_id: str,
    *,
    state: RedundancyState = RedundancyState.UNKNOWN,
    shared_upstreams: tuple[str, ...] = (),
    failure_domain_refs: tuple[str, ...] = (),
    positive: tuple[str, ...] = (),
) -> RedundancyAssessment:
    return RedundancyAssessment(
        redundancy_id=assessment_id,
        subject_ref="fixture:liquidation-contract",
        function="liquidation execution",
        provider_refs=("fixture:provider-a", "fixture:provider-b"),
        activation_mode=ActivationMode.DEPLOYED,
        shared_upstreams=shared_upstreams,
        failure_domain_refs=failure_domain_refs,
        independence_dimensions=("operator", "backend"),
        positive_independence_evidence_refs=positive,
        state=state,
        valid_time=NOW,
        book2_claim_refs=(CLAIM_REF,),
    )


def substitutability(
    assessment_id: str,
    incumbent: str,
    candidate: str,
    *,
    direction: SubstitutabilityDirection = SubstitutabilityDirection.INCUMBENT_TO_CANDIDATE,
) -> SubstitutabilityAssessment:
    return SubstitutabilityAssessment(
        assessment_id=assessment_id,
        function="serve read-only chain state",
        incumbent_ref=incumbent,
        candidate_ref=candidate,
        direction=direction,
        context="production read path",
        change_class=ChangeClass.CONFIG_CHANGE,
        technical_change="change endpoint configuration and credentials",
        governance_requirements=("change approval",),
        migration_requirements=("endpoint cutover",),
        state_impact="none after cutover",
        security_impact="endpoint trust policy must be reviewed",
        downtime_risk="brief cutover risk",
        valid_time=NOW,
        book2_claim_refs=(CLAIM_REF,),
    )


def role(
    assignment_id: str,
    role_type: ProtocolRole,
    *,
    system_ref: str = "fixture:system",
    state: RoleState = RoleState.CURRENT,
) -> RoleAssignment:
    return RoleAssignment(
        role_assignment_id=assignment_id,
        system_ref=system_ref,
        role_type=role_type,
        function="serve scoped protocol function",
        scope="fixture deployment",
        mechanism="explicit offline configuration fixture",
        consumes=(),
        provides=(),
        valid_from=NOW,
        valid_to=None,
        role_state=state,
        book2_claim_refs=(CLAIM_REF,),
        source_snapshot_refs=("snapshot://book4/evidence",),
    )


def context(context_id: str = "context-1") -> InfrastructureContext:
    return InfrastructureContext(
        context_id=context_id,
        system_ref="fixture:rollup",
        function="verify posted blobs",
        scope="rollup execution",
        role_assignment_ids=("role-sequencer", "role-da"),
        dependency_ids=("dependency-da",),
        path_ids=("path-abc",),
        failure_domain_ids=("domain-da",),
        redundancy_ids=("redundancy-da",),
        valid_time=NOW,
        book2_claim_refs=(CLAIM_REF,),
    )
