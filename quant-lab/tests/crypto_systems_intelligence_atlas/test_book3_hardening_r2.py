"""Book 3 Hardening R2 — negative identity evidence and temporal supersession."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from crypto_systems_intelligence_atlas.architecture import (
    ArchitectureDossier,
    ArchitectureProvenanceError,
    Book2ArchitectureProvenance,
)
from crypto_systems_intelligence_atlas.architecture_registry import (
    AdmissionOutcome,
    ArchitectureRegistryBook,
    RegistryAdmission,
    RegistryStatus,
    mint_registry_id,
)
from crypto_systems_intelligence_atlas.claims import (
    Claim,
    ClaimService,
    ClaimState,
    ClaimStore,
    Methodology,
    Proposition,
)
from crypto_systems_intelligence_atlas.evidence import EvidenceStore, RawEvidence
from crypto_systems_intelligence_atlas.network_identity import (
    NetworkIdentityEngine,
    NetworkIdentityEvidence,
    NetworkIdentityOutcome,
)
from crypto_systems_intelligence_atlas.promotion import ClaimStateEngine
from crypto_systems_intelligence_atlas.temporal import UnknownBound
from crypto_systems_intelligence_atlas.types import ClaimFamily

NOW = datetime(2026, 9, 24, 12, tzinfo=UTC)
LATER = NOW + timedelta(days=1)
AFTER_LATER = LATER + timedelta(days=1)


def make_kernel() -> tuple[ClaimStore, EvidenceStore, Book2ArchitectureProvenance]:
    evidence_store = EvidenceStore()
    claims = ClaimStore()

    def add_claim(claim_id: str, family: ClaimFamily) -> Claim:
        evidence_id = f"evidence:{claim_id}"
        evidence_store.add(
            RawEvidence(
                evidence_id=evidence_id,
                source_id="csia:source:r2",
                retrieved_at=NOW,
                content_locator=f"fixture://{claim_id}",
                content_hash="sha256:" + claim_id,
                raw_snapshot_ref=f"snapshot://{claim_id}",
                extractor_version="r2-test",
                parser_version="r2-test",
                evidence_tier="FIRST_PARTY_DOC",
            )
        )
        claim = Claim(
            claim_id=claim_id,
            evidence_refs=(evidence_id,),
            source_refs=("csia:source:r2",),
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
                methodology_ref="r2-offline-fixture",
                version="1",
                description="deterministic offline R2 fixture",
            ),
        )
        claims.add_initial(claim)
        return claim

    add_claim("claim:identity", ClaimFamily.IDENTITY_ATTRIBUTES)
    add_claim("claim:architecture", ClaimFamily.CHAIN_ARCHITECTURE)
    add_claim("claim:deployment", ClaimFamily.DEPLOYMENT_ACTIVATION)
    return claims, evidence_store, Book2ArchitectureProvenance(claims, evidence_store)


def identity_bundle(**updates: object) -> NetworkIdentityEvidence:
    data: dict[str, object] = {
        "evidence_id": "identity:r2",
        "prior_object_id": "object:prior",
        "candidate_object_id": "object:candidate",
        "canonical_network_continues": True,
        "state_history_continuity": True,
        "consensus_continuity": True,
        "deployment_continuity": True,
        "persistent_divergence": False,
        "temporary_ambiguous_split": False,
        "canonical_network_continuation_claim_refs": ("claim:identity",),
        "state_continuity_claim_refs": ("claim:architecture",),
        "consensus_continuity_claim_refs": ("claim:architecture",),
        "deployment_continuity_claim_refs": ("claim:deployment",),
    }
    data.update(updates)
    return NetworkIdentityEvidence.model_validate(data)


def test_unsigned_non_divergence_cannot_produce_same_object() -> None:
    _, _, provenance = make_kernel()
    with pytest.raises(ArchitectureProvenanceError, match="non-divergence"):
        NetworkIdentityEngine(provenance).decide(identity_bundle())


def test_unsigned_resolved_split_cannot_produce_same_object() -> None:
    _, _, provenance = make_kernel()
    with pytest.raises(ArchitectureProvenanceError, match="split resolution"):
        NetworkIdentityEngine(provenance).decide(identity_bundle())


def test_six_canonically_supported_dimensions_produce_same_object() -> None:
    _, _, provenance = make_kernel()
    decision = NetworkIdentityEngine(provenance).decide(
        identity_bundle(
            non_divergence_claim_refs=("claim:identity",),
            split_resolved_claim_refs=("claim:identity",),
        )
    )
    assert decision.outcome is NetworkIdentityOutcome.SAME_OBJECT
    assert decision.resulting_object_ids == ("object:prior",)


def test_divergence_claim_cannot_be_reused_as_non_divergence_evidence() -> None:
    _, _, provenance = make_kernel()
    with pytest.raises(ArchitectureProvenanceError, match="cannot support both"):
        NetworkIdentityEngine(provenance).decide(
            identity_bundle(
                divergence_claim_refs=("claim:identity",),
                non_divergence_claim_refs=("claim:identity",),
            )
        )


@pytest.mark.parametrize(
    "target_state",
    [
        ClaimState.CONTESTED,
        ClaimState.REJECTED,
        ClaimState.STALE,
        ClaimState.SUPERSEDED,
        ClaimState.UNRESOLVED,
    ],
)
def test_non_current_claim_cannot_establish_negative_identity_fact(
    target_state: ClaimState,
) -> None:
    claims, evidence, _ = make_kernel()
    claim_id = f"claim:negative:{target_state.value.lower()}"
    prior_state = (
        ClaimState.DECLARED
        if target_state is ClaimState.UNRESOLVED
        else ClaimState.OBSERVED
    )
    claim = Claim(
        claim_id=claim_id,
        evidence_refs=("evidence:claim:identity",),
        source_refs=("csia:source:r2",),
        proposition=Proposition(
            subject_refs=("network:fixture",),
            predicate="establishes_absence",
            object_ref=target_state.value.lower(),
        ),
        claim_family=ClaimFamily.IDENTITY_ATTRIBUTES,
        claim_state=prior_state,
        valid_time_hypothesis=NOW,
        observed_time=NOW,
        methodology=Methodology(
            methodology_ref="r2-offline-fixture",
            version="1",
            description="deterministic offline R2 fixture",
        ),
    )
    claims.add_initial(claim)
    engine = ClaimStateEngine(ClaimService(evidence, claim_store=claims))
    transition: dict[str, object] = {
        "triggering_evidence_refs": claim.evidence_refs,
        "transitioned_at": LATER,
    }
    if target_state is ClaimState.SUPERSEDED:
        transition.update(
            replacement_claim_id="claim:identity",
            supersession_reason="R2 non-current support fixture",
        )
    engine.transition(claim_id, target_state, **transition)
    provenance = Book2ArchitectureProvenance(claims, evidence)
    with pytest.raises(ArchitectureProvenanceError, match="graph-promotable"):
        NetworkIdentityEngine(provenance).decide(
            identity_bundle(
                non_divergence_claim_refs=(claim_id,),
                split_resolved_claim_refs=("claim:identity",),
            )
        )


def admit_value(
    book: ArchitectureRegistryBook,
    claims: ClaimStore,
    name: str,
    *,
    semantic_key: str = "evolving",
    supersedes: str | None = None,
    valid_from: datetime | UnknownBound = NOW,
) -> str:
    registry_id = mint_registry_id("EXECUTION_MODEL", "EXECUTION_MODEL", name)
    book.add(
        RegistryAdmission(
            value={
                "registry_id": registry_id,
                "namespace": "EXECUTION_MODEL",
                "family": "EXECUTION_MODEL",
                "name": name,
                "definition": f"R2 execution fixture {name}",
                "semantic_key": semantic_key,
                "valid_from": valid_from,
                "source_claim_refs": ("claim:architecture",),
                "supersedes": supersedes,
            },
            decision_reason="R2 temporal supersession fixture",
        ),
        claims,
    )
    return registry_id


def make_dossier(
    registry_ref: str, *, valid_time: datetime = NOW
) -> ArchitectureDossier:
    return ArchitectureDossier.model_validate(
        {
            "object_id": "object:dossier:r2",
            "canonical_name": "R2 Fixture",
            "architecture_family": "FIXTURE_FAMILY",
            "network_namespace": "fixture:network",
            "network_identity_anchor_refs": ("anchor:identity",),
            "genesis_or_origin_anchor_refs": ("anchor:genesis",),
            "native_asset_refs": ("asset:fixture",),
            "network_identity_claim_refs": ("claim:identity",),
            "genesis_or_origin_claim_refs": ("claim:identity",),
            "native_asset_claim_refs": ("claim:identity",),
            "execution_model_ref": registry_ref,
            "source_claim_refs": ("claim:identity", "claim:architecture"),
            "field_claim_refs": {"execution_model_ref": ("claim:architecture",)},
            "valid_time": valid_time,
            "observed_time": valid_time,
        }
    )


def test_supersession_closes_projected_validity_without_mutating_old_record() -> None:
    claims, evidence, _ = make_kernel()
    book = ArchitectureRegistryBook()
    old_record = book.add(
        RegistryAdmission(
            value={
                "registry_id": mint_registry_id(
                    "EXECUTION_MODEL", "EXECUTION_MODEL", "OLD_EXEC"
                ),
                "namespace": "EXECUTION_MODEL",
                "family": "EXECUTION_MODEL",
                "name": "OLD_EXEC",
                "definition": "R2 old execution definition",
                "semantic_key": "evolving",
                "valid_from": NOW,
                "source_claim_refs": ("claim:architecture",),
            },
            decision_reason="R2 initial value",
        ),
        claims,
    )
    replacement_id = admit_value(
        book,
        claims,
        "NEW_EXEC",
        supersedes=old_record.registry_id,
        valid_from=LATER,
    )
    projected_old = book.require(old_record.registry_id)
    history = book.history("EXECUTION_MODEL", "evolving")
    validator = Book2ArchitectureProvenance(claims, evidence, book)

    assert old_record.valid_to is None
    assert old_record.status is RegistryStatus.ACTIVE
    assert projected_old.status is RegistryStatus.SUPERSEDED
    assert projected_old.superseded_by == replacement_id
    assert projected_old.valid_to == LATER
    assert [(item.registry_id, item.status) for item in history] == [
        (old_record.registry_id, RegistryStatus.SUPERSEDED),
        (replacement_id, RegistryStatus.ACTIVE),
    ]
    assert validator.validate_dossier(
        make_dossier(old_record.registry_id), historical=True
    )
    with pytest.raises(ArchitectureProvenanceError, match="does not hold"):
        validator.validate_dossier(
            make_dossier(old_record.registry_id, valid_time=LATER), historical=True
        )
    with pytest.raises(ArchitectureProvenanceError, match="superseded"):
        validator.validate_dossier(make_dossier(old_record.registry_id))
    assert validator.validate_dossier(make_dossier(replacement_id))


def test_replacement_must_move_temporal_state_forward() -> None:
    claims, _, _ = make_kernel()
    book = ArchitectureRegistryBook()
    old_id = admit_value(book, claims, "OLD_FORWARD")
    result = book.evaluate(
        RegistryAdmission(
            value={
                "registry_id": mint_registry_id(
                    "EXECUTION_MODEL", "EXECUTION_MODEL", "BACKWARD_EXEC"
                ),
                "namespace": "EXECUTION_MODEL",
                "family": "EXECUTION_MODEL",
                "name": "BACKWARD_EXEC",
                "definition": "R2 backward replacement",
                "semantic_key": "evolving",
                "valid_from": NOW,
                "source_claim_refs": ("claim:architecture",),
                "supersedes": old_id,
            },
            decision_reason="must reject non-forward replacement",
        ),
        claims,
    )
    assert result.outcome is AdmissionOutcome.REJECTED
    assert "forward" in result.reason


def test_unknownbound_supersession_fails_closed_across_uncertain_boundary() -> None:
    claims, evidence, _ = make_kernel()
    book = ArchitectureRegistryBook()
    old_id = admit_value(book, claims, "OLD_UNKNOWN_BOUND")
    admit_value(
        book,
        claims,
        "UNKNOWN_BOUND_EXEC",
        supersedes=old_id,
        valid_from=UnknownBound(earliest_bound=LATER, latest_bound=AFTER_LATER),
    )
    validator = Book2ArchitectureProvenance(claims, evidence, book)

    assert validator.validate_dossier(make_dossier(old_id), historical=True)
    with pytest.raises(ArchitectureProvenanceError, match="does not hold"):
        validator.validate_dossier(
            make_dossier(old_id, valid_time=LATER), historical=True
        )
    with pytest.raises(ArchitectureProvenanceError, match="does not hold"):
        validator.validate_dossier(
            make_dossier(old_id, valid_time=AFTER_LATER), historical=True
        )
