"""Book 3 Hardening R1 — identity provenance and dossier integrity tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from crypto_systems_intelligence_atlas.architecture import (
    ArchitectureDossier,
    ArchitectureProvenanceError,
    Book2ArchitectureProvenance,
)
from crypto_systems_intelligence_atlas.architecture_registry import (
    ArchitectureRegistryBook,
    RegistryAdmission,
    RegistryStatus,
    mint_registry_id,
)
from crypto_systems_intelligence_atlas.claims import Claim, ClaimState, ClaimStore, Methodology, Proposition
from crypto_systems_intelligence_atlas.evidence import EvidenceStore, RawEvidence
from crypto_systems_intelligence_atlas.network_identity import (
    NetworkIdentityEngine,
    NetworkIdentityEvidence,
    NetworkIdentityOutcome,
)
from crypto_systems_intelligence_atlas.types import ClaimFamily

NOW = datetime(2026, 9, 24, 12, tzinfo=UTC)
LATER = NOW + timedelta(days=1)


def make_kernel() -> tuple[ClaimStore, EvidenceStore, Book2ArchitectureProvenance]:
    evidence_store = EvidenceStore()
    claims = ClaimStore()

    def add_claim(claim_id: str, family: ClaimFamily) -> Claim:
        evidence_id = f"evidence:{claim_id}"
        evidence_store.add(
            RawEvidence(
                evidence_id=evidence_id,
                source_id="csia:source:r1",
                retrieved_at=NOW,
                content_locator=f"fixture://{claim_id}",
                content_hash="sha256:" + claim_id,
                raw_snapshot_ref=f"snapshot://{claim_id}",
                extractor_version="r1-test",
                parser_version="r1-test",
                evidence_tier="FIRST_PARTY_DOC",
            )
        )
        claim = Claim(
            claim_id=claim_id,
            evidence_refs=(evidence_id,),
            source_refs=("csia:source:r1",),
            proposition=Proposition(
                subject_refs=("network:fixture",),
                predicate=claim_id,
                object_ref="supported-object",
            ),
            claim_family=family,
            claim_state=ClaimState.OBSERVED,
            valid_time_hypothesis=NOW,
            observed_time=NOW,
            methodology=Methodology(
                methodology_ref="r1-offline-fixture",
                version="1",
                description="deterministic offline hardening fixture",
            ),
        )
        claims.add_initial(claim)
        return claim

    add_claim("claim:identity", ClaimFamily.IDENTITY_ATTRIBUTES)
    add_claim("claim:genesis", ClaimFamily.HISTORICAL_GENESIS_SPEC)
    add_claim("claim:architecture", ClaimFamily.CHAIN_ARCHITECTURE)
    add_claim("claim:deployment", ClaimFamily.DEPLOYMENT_ACTIVATION)
    add_claim("claim:governance", ClaimFamily.GOVERNANCE_EXECUTION)
    add_claim("claim:token", ClaimFamily.TOKEN_ROLE_MECHANICS)
    add_claim("claim:narrative", ClaimFamily.NARRATIVE)
    return claims, evidence_store, Book2ArchitectureProvenance(claims, evidence_store)


def identity_bundle(**updates) -> NetworkIdentityEvidence:
    data = {
        "evidence_id": "identity:r1",
        "prior_object_id": "object:prior",
        "candidate_object_id": "object:candidate",
        "canonical_network_continues": False,
        "state_history_continuity": False,
        "consensus_continuity": False,
        "deployment_continuity": False,
        "persistent_divergence": False,
        "temporary_ambiguous_split": False,
        "new_genesis": False,
    }
    data.update(updates)
    return NetworkIdentityEvidence.model_validate(data)


@pytest.mark.parametrize(
    ("evidence", "error"),
    [
        (identity_bundle(persistent_divergence=True), "divergence"),
        (identity_bundle(unrelated_network_evidence=True), "unrelated"),
        (identity_bundle(new_genesis=True, genesis_or_origin_anchor_refs=("genesis:fake",)), "genesis"),
        (
            identity_bundle(
                canonical_network_continues=True,
                state_history_continuity=True,
                consensus_continuity=True,
                deployment_continuity=True,
            ),
            "continuation",
        ),
        (identity_bundle(migration_evidence_refs=("fake",)), "migration"),
    ],
)
def test_forged_identity_assertions_are_rejected_without_book2_support(
    evidence: NetworkIdentityEvidence, error: str
) -> None:
    _, _, provenance = make_kernel()
    with pytest.raises(ArchitectureProvenanceError, match=error):
        NetworkIdentityEngine(provenance).decide(evidence)


def test_canonical_persistent_fork_support_produces_fork_and_forked_from() -> None:
    _, _, provenance = make_kernel()
    evidence = identity_bundle(
        evidence_id="identity:fork-r1",
        persistent_divergence=True,
        shared_ancestry_claim_refs=("claim:genesis",),
        divergence_claim_refs=("claim:identity",),
        unrelated_network_claim_refs=("claim:architecture",),
    )
    decision = NetworkIdentityEngine(provenance).decide(evidence)
    assert decision.outcome is NetworkIdentityOutcome.FORK
    assert decision.resulting_object_ids == ("object:prior", "object:candidate")
    assert decision.relation_refs == ("object:candidate:FORKED_FROM:object:prior",)


def test_canonical_continuation_support_produces_same_object() -> None:
    _, _, provenance = make_kernel()
    evidence = identity_bundle(
        evidence_id="identity:continuation-r1",
        canonical_network_continues=True,
        state_history_continuity=True,
        consensus_continuity=True,
        deployment_continuity=True,
        canonical_network_continuation_claim_refs=("claim:identity",),
        state_continuity_claim_refs=("claim:architecture",),
        consensus_continuity_claim_refs=("claim:architecture",),
        deployment_continuity_claim_refs=("claim:deployment",),
    )
    assert NetworkIdentityEngine(provenance).decide(evidence).outcome is NetworkIdentityOutcome.SAME_OBJECT


def test_canonical_new_genesis_support_produces_new_object() -> None:
    _, _, provenance = make_kernel()
    evidence = identity_bundle(
        evidence_id="identity:new-genesis-r1",
        new_genesis=True,
        genesis_claim_refs=("claim:genesis",),
    )
    decision = NetworkIdentityEngine(provenance).decide(evidence)
    assert decision.outcome is NetworkIdentityOutcome.NEW_OBJECT
    assert decision.resulting_object_ids == ("object:candidate",)


def test_identity_support_rejects_narrative_and_wrong_claim_families() -> None:
    _, _, provenance = make_kernel()
    evidence = identity_bundle(
        evidence_id="identity:narrative-r1",
        persistent_divergence=True,
        shared_ancestry_claim_refs=("claim:narrative",),
        divergence_claim_refs=("claim:governance",),
        unrelated_network_claim_refs=("claim:identity",),
    )
    with pytest.raises(ArchitectureProvenanceError, match="family"):
        NetworkIdentityEngine(provenance).decide(evidence)


def admit_value(
    book: ArchitectureRegistryBook,
    claims: ClaimStore,
    namespace: str,
    name: str,
    *,
    semantic_key: str | None = None,
    supersedes: str | None = None,
    valid_from: datetime = NOW,
) -> str:
    registry_id = mint_registry_id(namespace, namespace, name)
    book.add(
        RegistryAdmission(
            value={
                "registry_id": registry_id,
                "namespace": namespace,
                "family": namespace,
                "name": name,
                "definition": f"R1 {namespace} fixture {name}",
                "semantic_key": semantic_key or name.casefold(),
                "valid_from": valid_from,
                "source_claim_refs": ("claim:architecture",),
                "supersedes": supersedes,
            },
            decision_reason="R1 referential-integrity fixture",
        ),
        claims,
    )
    return registry_id


def make_registry(claims: ClaimStore) -> tuple[ArchitectureRegistryBook, dict[str, str]]:
    book = ArchitectureRegistryBook()
    execution = admit_value(book, claims, "EXECUTION_MODEL", "UTXO")
    state = admit_value(book, claims, "STATE_MODEL", "UTXO")
    old_execution = admit_value(book, claims, "EXECUTION_MODEL", "LEGACY_EXEC", semantic_key="evolving")
    current_execution = admit_value(
        book,
        claims,
        "EXECUTION_MODEL",
        "CURRENT_EXEC",
        semantic_key="evolving",
        supersedes=old_execution,
        valid_from=LATER,
    )
    unknown = book.admit_unknown(
        namespace="EXECUTION_MODEL",
        family="EXECUTION_MODEL",
        claim_store=claims,
        claim_ref="claim:architecture",
        at=NOW,
    ).registry_id
    return book, {
        "execution": execution,
        "state": state,
        "old_execution": old_execution,
        "current_execution": current_execution,
        "unknown": unknown,
    }


def make_dossier(registry: dict[str, str], **updates) -> ArchitectureDossier:
    data = {
        "object_id": "object:dossier",
        "canonical_name": "R1 Fixture",
        "architecture_family": "FIXTURE_FAMILY",
        "network_namespace": "fixture:network",
        "network_identity_anchor_refs": ("anchor:identity",),
        "genesis_or_origin_anchor_refs": ("anchor:genesis",),
        "native_asset_refs": ("asset:fixture",),
        "network_identity_claim_refs": ("claim:identity",),
        "genesis_or_origin_claim_refs": ("claim:genesis",),
        "native_asset_claim_refs": ("claim:token",),
        "execution_model_ref": registry["execution"],
        "source_claim_refs": (
            "claim:identity",
            "claim:genesis",
            "claim:token",
            "claim:architecture",
        ),
        "field_claim_refs": {"execution_model_ref": ("claim:architecture",)},
        "valid_time": NOW,
        "observed_time": NOW,
    }
    data.update(updates)
    return ArchitectureDossier.model_validate(data)


def test_dossier_rejects_nonexistent_registry_reference() -> None:
    claims, evidence, _ = make_kernel()
    book, registry = make_registry(claims)
    validator = Book2ArchitectureProvenance(claims, evidence, book)
    with pytest.raises(ArchitectureProvenanceError, match="unknown registry"):
        validator.validate_dossier(make_dossier(registry, execution_model_ref="made-up-value"))


def test_dossier_rejects_registry_value_from_wrong_namespace() -> None:
    claims, evidence, _ = make_kernel()
    book, registry = make_registry(claims)
    validator = Book2ArchitectureProvenance(claims, evidence, book)
    with pytest.raises(ArchitectureProvenanceError, match="namespace"):
        validator.validate_dossier(make_dossier(registry, execution_model_ref=registry["state"]))


def test_dossier_rejects_superseded_registry_value_as_current_truth() -> None:
    claims, evidence, _ = make_kernel()
    book, registry = make_registry(claims)
    validator = Book2ArchitectureProvenance(claims, evidence, book)
    with pytest.raises(ArchitectureProvenanceError, match="superseded"):
        validator.validate_dossier(make_dossier(registry, execution_model_ref=registry["old_execution"]))
    historical = validator.validate_dossier(
        make_dossier(registry, execution_model_ref=registry["old_execution"]),
        historical=True,
    )
    assert historical.execution_model_ref == registry["old_execution"]


def test_dossier_accepts_explicit_unknown_and_active_execution_and_state_values() -> None:
    claims, evidence, _ = make_kernel()
    book, registry = make_registry(claims)
    validator = Book2ArchitectureProvenance(claims, evidence, book)
    assert validator.validate_dossier(make_dossier(registry, execution_model_ref=registry["unknown"]))
    assert validator.validate_dossier(make_dossier(registry, execution_model_ref=registry["execution"]))
    both = make_dossier(
        registry,
        state_model_ref=registry["state"],
        source_claim_refs=("claim:identity", "claim:genesis", "claim:token", "claim:architecture"),
        field_claim_refs={
            "execution_model_ref": ("claim:architecture",),
            "state_model_ref": ("claim:architecture",),
        },
    )
    assert validator.validate_dossier(both)


def test_dossier_anchor_refs_require_explicit_claim_bindings_and_allowed_families() -> None:
    claims, evidence, _ = make_kernel()
    book, registry = make_registry(claims)
    validator = Book2ArchitectureProvenance(claims, evidence, book)
    with pytest.raises(ValueError, match="network identity"):
        ArchitectureDossier.model_validate(
            make_dossier(registry, network_identity_claim_refs=()).model_dump()
        )
    narrative = make_dossier(
        registry,
        network_identity_claim_refs=("claim:narrative",),
        source_claim_refs=("claim:narrative", "claim:genesis", "claim:token", "claim:architecture"),
    )
    with pytest.raises(ArchitectureProvenanceError, match="family"):
        validator.validate_dossier(narrative)
    assert validator.validate_dossier(make_dossier(registry))


def test_supersession_history_exposes_old_as_superseded_and_current_as_active() -> None:
    claims, _, _ = make_kernel()
    book, registry = make_registry(claims)
    history = book.history("EXECUTION_MODEL", "evolving")
    assert [item.status for item in history] == [RegistryStatus.SUPERSEDED, RegistryStatus.ACTIVE]
    assert history[0].superseded_by == history[1].registry_id
