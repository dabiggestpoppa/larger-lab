"""Book 3 deterministic family-registry governance tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from crypto_systems_intelligence_atlas.architecture_registry import (
    RATIFIED_ARCHITECTURE_FAMILIES,
    AdmissionOutcome,
    ArchitectureRegistryBook,
    RegistryAdmission,
    RegistryNamespace,
    RegistryStatus,
    mint_registry_id,
)
from crypto_systems_intelligence_atlas.claims import (
    Claim,
    ClaimState,
    ClaimStore,
    Methodology,
    Proposition,
)

NOW = datetime(2026, 9, 24, 12, tzinfo=UTC)


def observed_claim(claim_id: str = "claim-registry") -> ClaimStore:
    claim = Claim(
        claim_id=claim_id,
        evidence_refs=("evidence-fixture",),
        source_refs=("source-fixture",),
        proposition=Proposition(
            subject_refs=("execution-model",),
            predicate="has_definition",
            object_ref=claim_id,
        ),
        claim_family="CHAIN_ARCHITECTURE",
        claim_state=ClaimState.OBSERVED,
        valid_time_hypothesis=NOW,
        observed_time=NOW,
        methodology=Methodology(
            methodology_ref="offline-fixture",
            version="1",
            description="deterministic offline architecture fixture",
        ),
    )
    store = ClaimStore()
    store.add_initial(claim)
    return store


def value(name: str, *, semantic_key: str | None = None, supersedes: str | None = None):
    return {
        "registry_id": mint_registry_id("EXECUTION_MODEL", "EXECUTION_MODEL", name),
        "namespace": "EXECUTION_MODEL",
        "family": "EXECUTION_MODEL",
        "name": name,
        "definition": f"Native {name} execution definition.",
        "semantic_key": semantic_key or name.casefold(),
        "valid_from": NOW,
        "source_claim_refs": ("claim-registry",),
        "supersedes": supersedes,
    }


def test_ratified_registry_namespaces_are_explicit_and_complete() -> None:
    book = ArchitectureRegistryBook()
    assert RATIFIED_ARCHITECTURE_FAMILIES == (
        "EXECUTION_MODEL",
        "STATE_MODEL",
        "CONSENSUS_MODEL",
        "FINALITY_MODEL",
        "DA_MODEL",
        "SETTLEMENT_MODEL",
        "VALIDATOR_MODEL",
        "PARTICIPANT_MODEL",
        "GOVERNANCE_MODEL",
        "FEE_MODEL",
        "UPGRADE_MODEL",
        "INTEROP_MODEL",
        "DEPLOYMENT_MODEL",
        "SEQUENCING_MODEL",
        "SECURITY_MODEL",
    )
    for family in RATIFIED_ARCHITECTURE_FAMILIES:
        assert book.namespace(family).ratified


def test_evidence_admitted_value_passes_and_collision_escalates() -> None:
    store = observed_claim()
    book = ArchitectureRegistryBook()
    admitted = book.add(
        RegistryAdmission(
            value=value("UTXO"),
            decision_reason="family-native evidence supports value",
        ),
        store,
    )
    assert admitted.status is RegistryStatus.ACTIVE
    result = book.evaluate(
        RegistryAdmission(
            value=value("UTXO_ALT", semantic_key="utxo"),
            semantic_collision=True,
            decision_reason="possible collision",
        ),
        store,
    )
    assert result.outcome is AdmissionOutcome.ESCALATED


def test_new_namespace_requires_operator_admission() -> None:
    store = observed_claim()
    book = ArchitectureRegistryBook()
    candidate = value("UTXO").copy()
    candidate["namespace"] = "CUSTOM_EXECUTION"
    candidate["family"] = "CUSTOM_EXECUTION"
    candidate["registry_id"] = mint_registry_id("CUSTOM_EXECUTION", "CUSTOM_EXECUTION", "UTXO")
    with pytest.raises(ValueError, match="operator admission"):
        RegistryNamespace(namespace="CUSTOM_EXECUTION", definition="custom")
    result = book.evaluate(
        RegistryAdmission(value=candidate, decision_reason="attempt unadmitted namespace"),
        store,
    )
    assert result.outcome is AdmissionOutcome.REJECTED
    book.admit_namespace(
        RegistryNamespace(
            namespace="CUSTOM_EXECUTION",
            definition="operator-defined custom execution namespace",
            operator_admission_ref="operator-decision-fixture",
        )
    )
    assert book.add(
        RegistryAdmission(value=candidate, decision_reason="operator admitted"),
        store,
    ).namespace == "CUSTOM_EXECUTION"


def test_vendor_only_label_is_rejected() -> None:
    result = ArchitectureRegistryBook().evaluate(
        RegistryAdmission(
            value=value("AcmeVM"),
            vendor_only_label=True,
            decision_reason="vendor assertion",
        ),
        observed_claim(),
    )
    assert result.outcome is AdmissionOutcome.REJECTED
    assert "vendor-only" in result.reason


def test_supersession_is_append_only_and_old_value_remains_queryable() -> None:
    store = observed_claim()
    book = ArchitectureRegistryBook()
    first = book.add(
        RegistryAdmission(value=value("LEGACY_EXEC"), decision_reason="initial"),
        store,
    )
    replacement_data = value(
        "LEGACY_EXEC_V2",
        semantic_key=first.semantic_key,
        supersedes=first.registry_id,
    )
    replacement_data["valid_from"] = NOW + timedelta(days=1)
    replacement = book.add(
        RegistryAdmission(value=replacement_data, decision_reason="evidence-backed revision"),
        store,
    )
    old = book.require(first.registry_id)
    assert old.status is RegistryStatus.SUPERSEDED
    assert old.superseded_by == replacement.registry_id
    assert book.current("EXECUTION_MODEL", first.semantic_key).registry_id == replacement.registry_id
    assert len(book.history("EXECUTION_MODEL", first.semantic_key)) == 2


def test_explicit_unknown_is_evidence_bound_and_does_not_add_other_bucket() -> None:
    store = observed_claim("claim-unknown")
    book = ArchitectureRegistryBook()
    unknown = book.admit_unknown(
        namespace="DA_MODEL",
        family="DA_MODEL",
        claim_store=store,
        claim_ref="claim-unknown",
        at=NOW,
    )
    assert unknown.status is RegistryStatus.UNKNOWN
    assert all(value.name != "OTHER" for value in book.values())
