"""CSIA Book 3 — deterministic network identity and fork decisions."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class NetworkIdentityOutcome(str, Enum):
    SAME_OBJECT = "SAME_OBJECT"
    NEW_OBJECT = "NEW_OBJECT"
    FORK = "FORK"
    MIGRATION = "MIGRATION"
    SUPERSESSION = "SUPERSESSION"
    UNKNOWN = "UNKNOWN"


class NetworkIdentityEvidence(BaseModel):
    """Evidence bundle; names, tickers, and chain IDs are never identity keys."""

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
    new_genesis: bool | None = None
    migration_evidence_refs: tuple[str, ...] = ()
    family_native_continuation: bool | None = None
    operator_reviewed_family_native_continuation: bool = False

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
    """Pure deterministic decision function; no network or persistence."""

    def decide(self, evidence: NetworkIdentityEvidence) -> NetworkIdentityDecision:
        candidate = evidence.candidate_object_id
        prior = evidence.prior_object_id
        if evidence.temporary_ambiguous_split:
            return self._unknown(
                evidence,
                "temporary split is unresolved; shared history does not establish identity",
                operator_review_required=False,
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
        if evidence.migration_evidence_refs:
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

    def _same(
        self,
        evidence: NetworkIdentityEvidence,
        reason: str,
    ) -> NetworkIdentityDecision:
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
    "NetworkIdentityDecision",
    "NetworkIdentityEngine",
    "NetworkIdentityEvidence",
    "NetworkIdentityOutcome",
]
