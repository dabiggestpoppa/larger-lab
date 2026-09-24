"""Book 3 dossier, modular component, relation, and provenance tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from crypto_systems_intelligence_atlas.architecture import (
    ArchitectureComponent,
    ArchitectureDossier,
    ArchitectureProvenanceError,
    Book2ArchitectureProvenance,
    ComponentRole,
    ModularArchitecture,
)
from crypto_systems_intelligence_atlas.architecture_registry import (
    ArchitectureRegistryBook,
    RegistryAdmission,
    mint_registry_id,
)
from crypto_systems_intelligence_atlas.architecture_relations import (
    ArchitectureRelation,
    ArchitectureRelationBook,
    ArchitectureRelationType,
)
from crypto_systems_intelligence_atlas.authority import AuthorityPolicy
from crypto_systems_intelligence_atlas.claims import (
    Claim,
    ClaimService,
    ClaimState,
    ClaimStore,
    Methodology,
    Proposition,
)
from crypto_systems_intelligence_atlas.evidence import EvidenceStore
from crypto_systems_intelligence_atlas.promotion import ClaimStateEngine
from crypto_systems_intelligence_atlas.sources import (
    AccessMethod,
    LocatorMetadata,
    Source,
    SourceRegistry,
    VerificationStatus,
)
from crypto_systems_intelligence_atlas.types import AuthoritySeed, AuthorityTier, ClaimFamily, SourceClass

NOW = datetime(2026, 9, 24, 12, tzinfo=UTC)
LATER = NOW + timedelta(days=1)


def make_claim(
    claim_id: str,
    *,
    evidence_ref: str = "evidence-architecture",
    state: ClaimState = ClaimState.OBSERVED,
) -> Claim:
    return Claim(
        claim_id=claim_id,
        evidence_refs=(evidence_ref,),
        source_refs=("csia:source:architecture",),
        proposition=Proposition(
            subject_refs=("bitcoin",),
            predicate="uses_execution_model",
            object_ref=claim_id,
        ),
        claim_family="CHAIN_ARCHITECTURE",
        claim_state=state,
        valid_time_hypothesis=NOW,
        observed_time=NOW,
        methodology=Methodology(
            methodology_ref="offline-architecture-fixture",
            version="1",
            description="deterministic offline fixture",
        ),
    )


def capture_evidence(evidence: EvidenceStore, claim_id: str) -> str:
    return evidence.capture(
        source_id="csia:source:architecture",
        retrieved_at=NOW,
        content=claim_id.encode(),
        content_locator=f"fixture://{claim_id}",
        raw_snapshot_ref=f"snapshot://{claim_id}",
        extractor_version="test",
        parser_version="test",
        evidence_tier="FIRST_PARTY_DOC",
    ).evidence_id


def source_fixture() -> Source:
    return Source(
        source_id="csia:source:architecture",
        source_class=SourceClass.NATIVE_TECHNICAL,
        canonical_name="offline architecture fixture",
        object_scope=(),
        locator=LocatorMetadata(
            base_locator="fixture://architecture",
            access_method=AccessMethod.DOCUMENT,
            authentication="none",
        ),
        authority_metadata=(
            AuthoritySeed(
                claim_family=ClaimFamily.CHAIN_ARCHITECTURE,
                tier=AuthorityTier.PRIMARY,
                valid_from=NOW,
                policy_version="fixture-v1",
            ),
        ),
        verification_status=VerificationStatus.VERIFIED,
        verification_evidence_refs=("verification-fixture",),
        last_verified_at=NOW,
    )


def kernel():
    sources = SourceRegistry()
    source = source_fixture()
    sources.register(source)
    authority = AuthorityPolicy()
    authority.register_source(source)
    evidence = EvidenceStore(sources)
    claim_store = ClaimStore()
    evidence_ref = capture_evidence(evidence, "claim-current")
    claim_store.add_initial(make_claim("claim-current", evidence_ref=evidence_ref))
    registry = ArchitectureRegistryBook()
    for namespace, name in (("EXECUTION_MODEL", "utxo"), ("STATE_MODEL", "utxo"), ("CONSENSUS_MODEL", "pow")):
        registry.add(
            RegistryAdmission(
                value={
                    "registry_id": mint_registry_id(namespace, namespace, name),
                    "namespace": namespace,
                    "family": namespace,
                    "name": name,
                    "definition": f"fixture {name}",
                    "semantic_key": name,
                    "valid_from": NOW,
                    "source_claim_refs": ("claim-current",),
                },
                decision_reason="Book 3 fixture",
            ),
            claim_store,
        )
    return evidence, claim_store, Book2ArchitectureProvenance(claim_store, evidence, registry)


def service_with_evidence() -> ClaimService:
    sources = SourceRegistry()
    source = source_fixture()
    sources.register(source)
    authority = AuthorityPolicy()
    authority.register_source(source)
    return ClaimService(EvidenceStore(sources), authority_policy=authority)


def dossier(**updates) -> ArchitectureDossier:
    data = {
        "object_id": "csia:object:bitcoin",
        "canonical_name": "Bitcoin",
        "architecture_family": "UTXO_CHAIN",
        "network_namespace": "bitcoin-mainnet-fixture",
        "execution_model_ref": mint_registry_id("EXECUTION_MODEL", "EXECUTION_MODEL", "utxo"),
        "state_model_ref": mint_registry_id("STATE_MODEL", "STATE_MODEL", "utxo"),
        "consensus_model_ref": mint_registry_id("CONSENSUS_MODEL", "CONSENSUS_MODEL", "pow"),
        "source_claim_refs": ("claim-current",),
        "field_claim_refs": {
            "execution_model_ref": ("claim-current",),
            "state_model_ref": ("claim-current",),
            "consensus_model_ref": ("claim-current",),
        },
        "valid_time": NOW,
        "observed_time": NOW,
    }
    data.update(updates)
    return ArchitectureDossier.model_validate(data)


def test_dossier_allows_family_native_absence_and_explicit_unknown() -> None:
    item = dossier(
        execution_model_ref=None,
        state_model_ref=None,
        consensus_model_ref=None,
        source_claim_refs=(),
        field_claim_refs={},
    )
    assert item.execution_model_ref is None
    assert item.data_availability_model_ref is None
    assert item.sequencing_model_ref is None
    assert item.source_claim_refs == ()


def test_populated_fields_require_mapped_canonical_book2_claims() -> None:
    evidence, claims, validator = kernel()
    assert validator.validate_dossier(dossier()) is not None
    with pytest.raises(ValueError, match="lack provenance"):
        dossier(field_claim_refs={"execution_model_ref": ("claim-current",)})
    with pytest.raises(ArchitectureProvenanceError, match="unknown claim"):
        validator.validate_dossier(
            dossier(
                source_claim_refs=("missing",),
                field_claim_refs={
                    "execution_model_ref": ("missing",),
                    "state_model_ref": ("missing",),
                    "consensus_model_ref": ("missing",),
                },
            )
        )
    with pytest.raises(ArchitectureProvenanceError, match="detached evidence"):
        detached = ClaimStore()
        detached.add_initial(make_claim("detached", evidence_ref="missing-evidence"))
        Book2ArchitectureProvenance(detached, evidence).resolve_claim("detached")


def test_provenance_rejects_forged_historical_and_non_current_claims() -> None:
    evidence, claims, validator = kernel()
    current = claims.require("claim-current")
    forged = current.model_copy(update={"observed_time": LATER})
    with pytest.raises(ArchitectureProvenanceError, match="forged or detached"):
        validator.resolve_claim("claim-current", expected_claim=forged)


@pytest.mark.parametrize("target", [ClaimState.STALE, ClaimState.REJECTED, ClaimState.CONTESTED])
def test_provenance_rejects_terminal_or_non_current_book2_states(target: ClaimState) -> None:
    service = service_with_evidence()
    evidence = service.evidence_store
    evidence_ref = capture_evidence(evidence, "claim-transition")
    service.add_observed(make_claim("claim-transition", evidence_ref=evidence_ref))
    ClaimStateEngine(service).transition(
        "claim-transition",
        target,
        triggering_evidence_refs=(evidence_ref,),
        transitioned_at=LATER,
    )
    validator = Book2ArchitectureProvenance(service.claim_store, evidence)
    with pytest.raises(ArchitectureProvenanceError, match="graph-promotable"):
        validator.resolve_claim("claim-transition")


def test_provenance_rejects_unresolved_and_superseded_claims() -> None:
    service = service_with_evidence()
    evidence = service.evidence_store
    declared_ref = capture_evidence(evidence, "claim-declared")
    replacement_ref = capture_evidence(evidence, "claim-replacement")
    service.add_declared(make_claim("claim-declared", evidence_ref=declared_ref, state=ClaimState.DECLARED))
    service.add_observed(make_claim("claim-replacement", evidence_ref=replacement_ref))
    engine = ClaimStateEngine(service)
    engine.transition(
        "claim-declared",
        ClaimState.UNRESOLVED,
        triggering_evidence_refs=(declared_ref,),
        transitioned_at=LATER,
    )
    engine.transition(
        "claim-replacement",
        ClaimState.SUPERSEDED,
        triggering_evidence_refs=(replacement_ref,),
        transitioned_at=LATER,
        replacement_claim_id="claim-declared",
        supersession_reason="fixture replacement",
    )
    validator = Book2ArchitectureProvenance(service.claim_store, evidence)
    for claim_ref in ("claim-declared", "claim-replacement"):
        with pytest.raises(ArchitectureProvenanceError, match="graph-promotable"):
            validator.resolve_claim(claim_ref)


def test_local_relations_are_temporal_provenanced_and_never_alias_depends_on() -> None:
    evidence, claims, validator = kernel()
    book = ArchitectureRelationBook(validator)
    for relation_type in ArchitectureRelationType:
        relation = ArchitectureRelation(
            relation_id=f"relation-{relation_type.value}",
            subject_id="component-rollup-execution",
            relation_type=relation_type,
            object_id=f"component-{relation_type.value}",
            claim_refs=("claim-current",),
            valid_time=NOW,
            observed_time=NOW,
        )
        book.add(relation)
        assert relation.relation_type.value in {"EXECUTES_WITH", "USES_DA", "SEQUENCED_BY"}
        with pytest.raises(ValueError, match="DEPENDS_ON"):
            book.project_to_book1(relation.relation_id)


def test_modular_rollup_preserves_execution_settlement_da_sequencer_and_bridge() -> None:
    roles = {
        ComponentRole.EXECUTION,
        ComponentRole.SEQUENCING,
        ComponentRole.SETTLEMENT,
        ComponentRole.DATA_AVAILABILITY,
        ComponentRole.SECURITY,
        ComponentRole.BRIDGE_MESSAGING,
    }
    components = tuple(
        ArchitectureComponent(
            component_id=f"component-{role.value}",
            role=role,
            canonical_name=f"{role.value} provider",
            source_claim_refs=("claim-current",),
        )
        for role in roles
    )
    modular = ModularArchitecture(system_id="fixture-rollup", components=components)
    ids = {component.component_id for component in modular.components}
    assert len(ids) == 6
    assert modular.require(ComponentRole.EXECUTION).component_id != modular.require(ComponentRole.SETTLEMENT).component_id
    assert modular.require(ComponentRole.SETTLEMENT).component_id != modular.require(ComponentRole.DATA_AVAILABILITY).component_id
    assert modular.require(ComponentRole.DATA_AVAILABILITY).component_id != modular.require(ComponentRole.SEQUENCING).component_id
    assert modular.require(ComponentRole.BRIDGE_MESSAGING).component_id not in {
        modular.require(ComponentRole.EXECUTION).component_id,
        modular.require(ComponentRole.SEQUENCING).component_id,
    }
