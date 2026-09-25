"""CSIA Book 3 — deterministic network identity and fork decisions."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .architecture import ArchitectureProvenanceError, Book2ArchitectureProvenance
from .types import ClaimFamily

IDENTITY_CLAIM_FAMILIES: tuple[ClaimFamily, ...] = (
    ClaimFamily.IDENTITY_ATTRIBUTES,
    ClaimFamily.HISTORICAL_GENESIS_SPEC,
    ClaimFamily.CHAIN_ARCHITECTURE,
    ClaimFamily.DEPLOYMENT_ACTIVATION,
)
CONTINUITY_CLAIM_FAMILIES: dict[str, tuple[ClaimFamily, ...]] = {
    "canonical-network continuation": IDENTITY_CLAIM_FAMILIES,
    "state continuation": (ClaimFamily.CHAIN_ARCHITECTURE, ClaimFamily.HISTORICAL_GENESIS_SPEC),
    "consensus continuation": (ClaimFamily.CHAIN_ARCHITECTURE, ClaimFamily.HISTORICAL_GENESIS_SPEC),
    "deployment continuation": (
        ClaimFamily.DEPLOYMENT_ACTIVATION,
        ClaimFamily.CHAIN_ARCHITECTURE,
        ClaimFamily.GOVERNANCE_EXECUTION,
    ),
    "migration": IDENTITY_CLAIM_FAMILIES,
    "temporary split": IDENTITY_CLAIM_FAMILIES,
    "non-divergence": IDENTITY_CLAIM_FAMILIES,
    "split resolution": IDENTITY_CLAIM_FAMILIES,
    "family-native continuation": IDENTITY_CLAIM_FAMILIES,
}


class NetworkIdentityOutcome(str, Enum):
    SAME_OBJECT = "SAME_OBJECT"
    NEW_OBJECT = "NEW_OBJECT"
    FORK = "FORK"
    MIGRATION = "MIGRATION"
    SUPERSESSION = "SUPERSESSION"
    UNKNOWN = "UNKNOWN"


class NetworkIdentityEvidence(BaseModel):
    """Decision assertions and their fact-specific canonical claim support."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    evidence_id: str = Field(min_length=1)
    prior_object_id: str | None = None
    candidate_object_id: str | None = None
    genesis_or_origin_anchor_refs: tuple[str, ...] = ()
    family_native_identity_refs: tuple[str, ...] = ()
    chain_or_network_id_refs: tuple[str, ...] = ()
    ticker_refs: tuple[str, ...] = ()
    name_refs: tuple[str, ...] = ()

    canonical_network_continues: bool | None = None
    state_history_continuity: bool | None = None
    consensus_continuity: bool | None = None
    deployment_continuity: bool | None = None
    persistent_divergence: bool | None = None
    temporary_ambiguous_split: bool | None = None
    unrelated_network_evidence: bool = False
    new_genesis: bool | None = None
    migration_evidence_refs: tuple[str, ...] = ()
    family_native_continuation: bool | None = None
    operator_reviewed_family_native_continuation: bool = False

    canonical_network_continuation_claim_refs: tuple[str, ...] = ()
    state_continuity_claim_refs: tuple[str, ...] = ()
    consensus_continuity_claim_refs: tuple[str, ...] = ()
    deployment_continuity_claim_refs: tuple[str, ...] = ()
    shared_ancestry_claim_refs: tuple[str, ...] = ()
    divergence_claim_refs: tuple[str, ...] = ()
    non_divergence_claim_refs: tuple[str, ...] = ()
    unrelated_network_claim_refs: tuple[str, ...] = ()
    genesis_claim_refs: tuple[str, ...] = ()
    migration_claim_refs: tuple[str, ...] = ()
    temporary_split_claim_refs: tuple[str, ...] = ()
    split_resolved_claim_refs: tuple[str, ...] = ()
    family_native_continuation_claim_refs: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _bundle_rules(self) -> "NetworkIdentityEvidence":
        if self.prior_object_id and self.candidate_object_id and self.prior_object_id == self.candidate_object_id:
            raise ValueError("comparison requires distinct prior and candidate object IDs")
        if self.persistent_divergence and self.canonical_network_continues:
            raise ValueError("persistent divergence cannot also have one continuing canonical network")
        if self.family_native_continuation and not self.family_native_identity_refs:
            raise ValueError("family-native continuation requires family-native evidence")
        return self


class NetworkIdentityDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    decision_id: str = Field(min_length=1)
    evidence_id: str = Field(min_length=1)
    outcome: NetworkIdentityOutcome
    prior_object_id: str | None = None
    resulting_object_ids: tuple[str, ...] = ()
    relation_refs: tuple[str, ...] = ()
    reason: str = Field(min_length=1)
    operator_review_required: bool = False


class NetworkIdentityEngine:
    """Pure decision function over canonical Book 2 identity evidence."""

    def __init__(self, provenance: Book2ArchitectureProvenance) -> None:
        self.provenance = provenance

    def decide(self, evidence: NetworkIdentityEvidence) -> NetworkIdentityDecision:
        self._validate_assertions(evidence)
        candidate = evidence.candidate_object_id
        prior = evidence.prior_object_id
        if evidence.temporary_ambiguous_split:
            return self._unknown(
                evidence,
                "temporary split is unresolved; shared history does not establish identity",
                operator_review_required=False,
            )
        if evidence.unrelated_network_evidence:
            if not prior or not candidate:
                return self._unknown(evidence, "unrelated-network evidence lacks both object identities")
            return NetworkIdentityDecision(
                decision_id=f"identity-decision:{evidence.evidence_id}",
                evidence_id=evidence.evidence_id,
                prior_object_id=prior,
                outcome=NetworkIdentityOutcome.NEW_OBJECT,
                resulting_object_ids=(candidate,),
                reason="independent network evidence defeats ticker/name-based identity collapse",
            )
        if evidence.persistent_divergence:
            if not prior or not candidate:
                return self._unknown(evidence, "persistent fork lacks both object identities")
            return NetworkIdentityDecision(
                decision_id=f"identity-decision:{evidence.evidence_id}",
                evidence_id=evidence.evidence_id,
                prior_object_id=prior,
                outcome=NetworkIdentityOutcome.FORK,
                resulting_object_ids=(prior, candidate),
                relation_refs=(f"{candidate}:FORKED_FROM:{prior}",),
                reason="persistent divergent branches are separate objects",
            )
        if evidence.new_genesis:
            if not candidate:
                return self._unknown(evidence, "new genesis lacks a candidate object identity")
            return NetworkIdentityDecision(
                decision_id=f"identity-decision:{evidence.evidence_id}",
                evidence_id=evidence.evidence_id,
                prior_object_id=prior,
                outcome=NetworkIdentityOutcome.NEW_OBJECT,
                resulting_object_ids=(candidate,),
                reason="new genesis creates a new object by default",
            )
        if evidence.migration_evidence_refs or evidence.migration_claim_refs:
            if not prior or not candidate:
                return self._unknown(evidence, "migration evidence is incomplete")
            same = self._continuity_complete(evidence)
            return NetworkIdentityDecision(
                decision_id=f"identity-decision:{evidence.evidence_id}",
                evidence_id=evidence.evidence_id,
                prior_object_id=prior,
                outcome=NetworkIdentityOutcome.MIGRATION,
                resulting_object_ids=(prior if same else candidate,),
                reason=(
                    "migration preserves the object when continuity is complete"
                    if same
                    else "migration evidence without complete continuity requires review"
                ),
                operator_review_required=not same,
            )
        if evidence.family_native_continuation:
            if not evidence.operator_reviewed_family_native_continuation:
                return self._unknown(
                    evidence,
                    "family-native continuation cannot auto-pass without operator review",
                )
            if not self._continuity_complete(evidence):
                return self._unknown(evidence, "reviewed family-native continuation lacks continuity")
            return self._same(evidence, "operator-reviewed family-native continuation")
        if self._continuity_complete(evidence):
            return self._same(
                evidence,
                "canonical, state, consensus, and deployment continuity with no persistent branch",
            )
        return self._unknown(evidence, "insufficient canonical continuity evidence")

    def _validate_assertions(self, evidence: NetworkIdentityEvidence) -> None:
        if set(evidence.divergence_claim_refs) & set(evidence.non_divergence_claim_refs):
            raise ArchitectureProvenanceError(
                "a divergence claim cannot support both divergence and non-divergence"
            )
        continuity_asserted = all(
            assertion is True
            for assertion in (
                evidence.canonical_network_continues,
                evidence.state_history_continuity,
                evidence.consensus_continuity,
                evidence.deployment_continuity,
            )
        )
        checks = (
            (evidence.persistent_divergence is True, evidence.divergence_claim_refs, "divergence"),
            (evidence.unrelated_network_evidence, evidence.unrelated_network_claim_refs, "unrelated-network"),
            (evidence.new_genesis is True, evidence.genesis_claim_refs, "genesis"),
            (
                evidence.canonical_network_continues is True,
                evidence.canonical_network_continuation_claim_refs,
                "canonical-network continuation",
            ),
            (evidence.state_history_continuity is True, evidence.state_continuity_claim_refs, "state continuation"),
            (evidence.consensus_continuity is True, evidence.consensus_continuity_claim_refs, "consensus continuation"),
            (evidence.deployment_continuity is True, evidence.deployment_continuity_claim_refs, "deployment continuation"),
            (bool(evidence.migration_evidence_refs) or bool(evidence.migration_claim_refs), evidence.migration_claim_refs, "migration"),
            (evidence.temporary_ambiguous_split is True, evidence.temporary_split_claim_refs, "temporary split"),
            (
                continuity_asserted and evidence.persistent_divergence is False,
                evidence.non_divergence_claim_refs,
                "non-divergence",
            ),
            (
                continuity_asserted and evidence.temporary_ambiguous_split is False,
                evidence.split_resolved_claim_refs,
                "split resolution",
            ),
            (
                evidence.family_native_continuation is True,
                evidence.family_native_continuation_claim_refs,
                "family-native continuation",
            ),
        )
        for asserted, refs, label in checks:
            if asserted and not refs:
                raise ArchitectureProvenanceError(f"{label} assertion lacks canonical Book 2 claim support")
            allowed_families = CONTINUITY_CLAIM_FAMILIES.get(label, IDENTITY_CLAIM_FAMILIES)
            for claim_ref in refs:
                self.provenance.resolve_claim(
                    claim_ref,
                    allowed_families=allowed_families,
                )
        if evidence.persistent_divergence is True:
            for refs, label in (
                (evidence.shared_ancestry_claim_refs, "shared ancestry"),
                (evidence.unrelated_network_claim_refs, "distinct network identity"),
            ):
                if not refs:
                    raise ArchitectureProvenanceError(f"{label} lacks canonical Book 2 claim support")
                for claim_ref in refs:
                    self.provenance.resolve_claim(
                        claim_ref,
                        allowed_families=IDENTITY_CLAIM_FAMILIES,
                    )

    @staticmethod
    def _continuity_complete(evidence: NetworkIdentityEvidence) -> bool:
        return bool(
            evidence.prior_object_id
            and evidence.candidate_object_id
            and evidence.canonical_network_continues is True
            and evidence.state_history_continuity is True
            and evidence.consensus_continuity is True
            and evidence.deployment_continuity is True
            and evidence.persistent_divergence is False
            and evidence.temporary_ambiguous_split is False
        )

    def _same(self, evidence: NetworkIdentityEvidence, reason: str) -> NetworkIdentityDecision:
        prior = evidence.prior_object_id
        if not prior:
            return self._unknown(evidence, reason)
        return NetworkIdentityDecision(
            decision_id=f"identity-decision:{evidence.evidence_id}",
            evidence_id=evidence.evidence_id,
            prior_object_id=prior,
            outcome=NetworkIdentityOutcome.SAME_OBJECT,
            resulting_object_ids=(prior,),
            reason=reason,
        )

    @staticmethod
    def _unknown(
        evidence: NetworkIdentityEvidence,
        reason: str,
        *,
        operator_review_required: bool = True,
    ) -> NetworkIdentityDecision:
        return NetworkIdentityDecision(
            decision_id=f"identity-decision:{evidence.evidence_id}",
            evidence_id=evidence.evidence_id,
            prior_object_id=evidence.prior_object_id,
            outcome=NetworkIdentityOutcome.UNKNOWN,
            reason=reason,
            operator_review_required=operator_review_required,
        )


__all__ = [
    "CONTINUITY_CLAIM_FAMILIES",
    "IDENTITY_CLAIM_FAMILIES",
    "NetworkIdentityDecision",
    "NetworkIdentityEngine",
    "NetworkIdentityEvidence",
    "NetworkIdentityOutcome",
]
