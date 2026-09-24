"""Book 3 identity/fork and append-only architecture history tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from crypto_systems_intelligence_atlas.architecture import Book2ArchitectureProvenance
from crypto_systems_intelligence_atlas.architecture_history import (
    ArchitectureChangeRecord,
    ArchitectureChangeType,
    ArchitectureHistory,
)
from crypto_systems_intelligence_atlas.claims import Claim, ClaimState, ClaimStore, Methodology, Proposition
from crypto_systems_intelligence_atlas.evidence import EvidenceStore, RawEvidence
from crypto_systems_intelligence_atlas.network_identity import (
    NetworkIdentityEngine,
    NetworkIdentityEvidence,
    NetworkIdentityOutcome,
)

NOW = datetime(2026, 9, 24, 12, tzinfo=UTC)


def bundle(**updates) -> NetworkIdentityEvidence:
    data = {
        "evidence_id": "identity-evidence",
        "prior_object_id": "object:prior",
        "candidate_object_id": "object:candidate",
        "canonical_network_continues": True,
        "state_history_continuity": True,
        "consensus_continuity": True,
        "deployment_continuity": True,
        "persistent_divergence": False,
        "temporary_ambiguous_split": False,
        "new_genesis": False,
    }
    data.update(updates)
    return NetworkIdentityEvidence.model_validate(data)


def test_a_same_genesis_continuing_upgrade_is_same_object() -> None:
    decision = NetworkIdentityEngine().decide(
        bundle(genesis_or_origin_anchor_refs=("genesis:one",))
    )
    assert decision.outcome is NetworkIdentityOutcome.SAME_OBJECT
    assert decision.resulting_object_ids == ("object:prior",)


def test_b_persistent_divergence_is_fork_with_separate_new_objects() -> None:
    decision = NetworkIdentityEngine().decide(
        bundle(
            evidence_id="persistent-fork",
            canonical_network_continues=False,
            persistent_divergence=True,
        )
    )
    assert decision.outcome is NetworkIdentityOutcome.FORK
    assert set(decision.resulting_object_ids) == {"object:prior", "object:candidate"}
    assert decision.relation_refs == ("object:candidate:FORKED_FROM:object:prior",)


def test_c_temporary_split_is_unknown() -> None:
    decision = NetworkIdentityEngine().decide(bundle(temporary_ambiguous_split=True))
    assert decision.outcome is NetworkIdentityOutcome.UNKNOWN


def test_d_new_genesis_is_new_object() -> None:
    decision = NetworkIdentityEngine().decide(
        bundle(new_genesis=True, genesis_or_origin_anchor_refs=("genesis:new",))
    )
    assert decision.outcome is NetworkIdentityOutcome.NEW_OBJECT
    assert decision.resulting_object_ids == ("object:candidate",)


def test_e_same_ticker_unrelated_networks_remain_distinct() -> None:
    evidence = bundle(
        evidence_id="same-ticker",
        ticker_refs=("ticker:XYZ",),
        canonical_network_continues=False,
        state_history_continuity=False,
        consensus_continuity=False,
        deployment_continuity=False,
        genesis_or_origin_anchor_refs=("genesis:left", "genesis:right"),
    )
    assert NetworkIdentityEngine().decide(evidence).outcome is NetworkIdentityOutcome.UNKNOWN
    assert evidence.ticker_refs  # retained as evidence, never used as a key


def test_f_rename_with_preserved_identity_evidence_remains_same() -> None:
    decision = NetworkIdentityEngine().decide(
        bundle(name_refs=("name:old", "name:renamed"), genesis_or_origin_anchor_refs=("genesis:one",))
    )
    assert decision.outcome is NetworkIdentityOutcome.SAME_OBJECT


def test_g_chain_id_change_with_migration_does_not_decide_from_chain_id_alone() -> None:
    decision = NetworkIdentityEngine().decide(
        bundle(
            chain_or_network_id_refs=("chain-id:old", "chain-id:new"),
            migration_evidence_refs=("migration:evidence",),
        )
    )
    assert decision.outcome is NetworkIdentityOutcome.MIGRATION
    assert decision.resulting_object_ids == ("object:prior",)


def test_h_security_provider_change_is_history_not_automatic_replacement() -> None:
    decision = NetworkIdentityEngine().decide(bundle())
    assert decision.outcome is NetworkIdentityOutcome.SAME_OBJECT


def test_family_native_continuation_requires_operator_review() -> None:
    evidence = bundle(
        evidence_id="family-native",
        family_native_continuation=True,
        family_native_identity_refs=("family-anchor:one",),
    )
    pending = NetworkIdentityEngine().decide(evidence)
    assert pending.outcome is NetworkIdentityOutcome.UNKNOWN
    assert pending.operator_review_required
    reviewed = NetworkIdentityEngine().decide(
        evidence.model_copy(update={"operator_reviewed_family_native_continuation": True})
    )
    assert reviewed.outcome is NetworkIdentityOutcome.SAME_OBJECT


def test_chain_id_name_and_ticker_alone_never_collapse_identity() -> None:
    weak = bundle(
        evidence_id="weak-identifiers",
        canonical_network_continues=None,
        state_history_continuity=None,
        consensus_continuity=None,
        deployment_continuity=None,
        ticker_refs=("same",),
        name_refs=("same",),
        chain_or_network_id_refs=("1",),
    )
    assert NetworkIdentityEngine().decide(weak).outcome is NetworkIdentityOutcome.UNKNOWN


def provenance() -> Book2ArchitectureProvenance:
    evidence_store = EvidenceStore()
    evidence_store.add(
        RawEvidence(
            evidence_id="evidence-history",
            source_id="csia:source:history",
            retrieved_at=NOW,
            content_locator="fixture://history",
            content_hash="sha256:history",
            raw_snapshot_ref="snapshot://history",
            extractor_version="test",
            parser_version="test",
            evidence_tier="FIRST_PARTY_DOC",
        )
    )
    claim = Claim(
        claim_id="claim-history",
        evidence_refs=("evidence-history",),
        source_refs=("source-history",),
        proposition=Proposition(
            subject_refs=("object:history",),
            predicate="changes",
            object_ref="architecture:new",
        ),
        claim_family="CHAIN_ARCHITECTURE",
        claim_state=ClaimState.OBSERVED,
        valid_time_hypothesis=NOW,
        observed_time=NOW,
        methodology=Methodology(
            methodology_ref="offline-history",
            version="1",
            description="offline fixture",
        ),
    )
    claims = ClaimStore()
    claims.add_initial(claim)
    return Book2ArchitectureProvenance(claims, evidence_store)


@pytest.mark.parametrize("change_type", tuple(ArchitectureChangeType))
def test_history_covers_every_change_class_and_preserves_old_truth(change_type: ArchitectureChangeType) -> None:
    history = ArchitectureHistory(provenance())
    record = ArchitectureChangeRecord(
        record_id=f"history:{change_type.value}",
        object_id="object:history",
        change_type=change_type,
        before_refs=("architecture:before",),
        after_refs=(),
        claim_refs=("claim-history",),
        valid_time=NOW,
        observed_time=NOW,
        reason="deterministic offline fixture",
    )
    history.append(record)
    assert history.require(record.record_id).before_refs == ("architecture:before",)
    assert history.for_object("object:history") == (record,)
    with pytest.raises(ValueError, match="immutable"):
        history.append(record)
