"""CSIA Book 2 — Bloc 2E: claim state transition engine."""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Final

from .claims import (
    Claim,
    ClaimService,
    ClaimState,
    ClaimStore,
    SupersessionLineage,
    TransitionEvent,
    same_proposition,
)
from .temporal import UnknownBound, normalize_utc

LEGAL_TRANSITIONS: Final[dict[ClaimState, frozenset[ClaimState]]] = {
    ClaimState.DECLARED: frozenset({ClaimState.OBSERVED, ClaimState.REJECTED, ClaimState.UNRESOLVED}),
    ClaimState.OBSERVED: frozenset(
        {ClaimState.CORROBORATED, ClaimState.CONTESTED, ClaimState.STALE, ClaimState.SUPERSEDED, ClaimState.REJECTED}
    ),
    ClaimState.INFERRED: frozenset(
        {ClaimState.CORROBORATED, ClaimState.CONTESTED, ClaimState.REJECTED, ClaimState.SUPERSEDED}
    ),
    ClaimState.CORROBORATED: frozenset(
        {ClaimState.CONTESTED, ClaimState.STALE, ClaimState.SUPERSEDED, ClaimState.REJECTED}
    ),
    ClaimState.CONTESTED: frozenset(
        {ClaimState.CORROBORATED, ClaimState.REJECTED, ClaimState.UNRESOLVED, ClaimState.SUPERSEDED}
    ),
    ClaimState.UNRESOLVED: frozenset(
        {ClaimState.OBSERVED, ClaimState.CORROBORATED, ClaimState.CONTESTED, ClaimState.REJECTED, ClaimState.SUPERSEDED}
    ),
    ClaimState.STALE: frozenset({ClaimState.OBSERVED, ClaimState.SUPERSEDED}),
    ClaimState.REJECTED: frozenset(),
    ClaimState.SUPERSEDED: frozenset(),
}


class IllegalClaimTransition(ValueError):
    """Raised when a requested state change is not in the ratified table."""


class ClaimStateEngine:
    def __init__(self, service: ClaimService) -> None:
        self.service = service
        self.store: ClaimStore = service.claim_store

    def can_transition(self, prior: ClaimState, new: ClaimState) -> bool:
        return new in LEGAL_TRANSITIONS.get(prior, frozenset())

    def transition(
        self,
        claim_id: str,
        new_state: ClaimState,
        *,
        triggering_evidence_refs: tuple[str, ...],
        transitioned_at: datetime,
        replacement_claim_id: str | None = None,
        supersession_reason: str | None = None,
        operator_involvement: str | None = None,
        corroborating_claim_id: str | None = None,
    ) -> Claim:
        current = self.store.require(claim_id)
        if not self.can_transition(current.claim_state, new_state):
            raise IllegalClaimTransition(
                f"illegal claim transition {current.claim_state.value} -> {new_state.value}"
            )
        if not triggering_evidence_refs:
            raise ValueError("every transition requires triggering evidence")
        for evidence_ref in triggering_evidence_refs:
            self.service.evidence_store.require(evidence_ref)
        if new_state is ClaimState.CORROBORATED:
            if not corroborating_claim_id:
                raise ValueError("CORROBORATED requires a corroborating claim")
            corroborating = self.store.require(corroborating_claim_id)
            if corroborating.claim_id == claim_id:
                raise ValueError("a claim cannot corroborate itself")
            if not same_proposition(current.proposition, corroborating.proposition):
                raise ValueError("corroboration requires proposition equivalence")
            if current.claim_family is not corroborating.claim_family:
                raise ValueError("corroboration requires matching claim family")
            if corroborating.claim_state not in (ClaimState.OBSERVED, ClaimState.CORROBORATED):
                raise ValueError("corroborating claim state must be OBSERVED or CORROBORATED")
            if not set(triggering_evidence_refs).issubset(corroborating.evidence_refs):
                raise ValueError("triggering evidence must belong to the corroborating claim")
            if isinstance(current.valid_time_hypothesis, UnknownBound) or isinstance(
                corroborating.valid_time_hypothesis, UnknownBound
            ):
                raise ValueError("valid time compatibility is unknown")
            if current.valid_time_hypothesis != corroborating.valid_time_hypothesis:
                raise ValueError("corroboration requires compatible valid time")
            current_evidence = [self.service.evidence_store.require(ref) for ref in current.evidence_refs]
            corroborating_evidence = [self.service.evidence_store.require(ref) for ref in corroborating.evidence_refs]
            current_sources = {item.source_id for item in current_evidence}
            corroborating_sources = {item.source_id for item in corroborating_evidence}
            if current_sources & corroborating_sources:
                raise ValueError("P-4: corroboration requires a distinct source")
            if any(
                self.service.evidence_store.require(left_ref).content_hash
                == self.service.evidence_store.require(right_ref).content_hash
                and (
                    self.service.evidence_store.require(left_ref).evidence_tier.value == "NARRATIVE"
                    or self.service.evidence_store.require(right_ref).evidence_tier.value == "NARRATIVE"
                )
                for left_ref in current.evidence_refs
                for right_ref in corroborating.evidence_refs
            ):
                raise ValueError("P-4: narrative copies are not independent evidence")
            registry = self.service.source_registry
            if registry is None:
                raise ValueError("P-4: source ownership metadata is unavailable")
            # Ownership/mechanism are explicit source metadata, never URL counts.
            current_owners = {registry.require(source_id).owner_entity_ref for source_id in current_sources}
            corroborating_owners = {registry.require(source_id).owner_entity_ref for source_id in corroborating_sources}
            if current_owners & corroborating_owners:
                raise ValueError("P-4: corroboration requires distinct owners")
            current_mechanisms = {(registry.require(source_id).source_class, registry.require(source_id).locator.access_method) for source_id in current_sources}
            corroborating_mechanisms = {(registry.require(source_id).source_class, registry.require(source_id).locator.access_method) for source_id in corroborating_sources}
            if current_mechanisms & corroborating_mechanisms:
                raise ValueError("P-4: corroboration requires distinct mechanisms/providers")
        normalize_utc(transitioned_at)
        lineage = current.supersession_lineage
        if new_state is ClaimState.SUPERSEDED:
            if not replacement_claim_id or not supersession_reason:
                raise ValueError("supersession requires replacement id and reason")
            if replacement_claim_id == claim_id:
                raise ValueError("a claim cannot supersede itself")
            lineage = SupersessionLineage(
                superseded_claim_id=claim_id,
                replacement_claim_id=replacement_claim_id,
                reason=supersession_reason,
            )
        payload = current.model_dump(mode="python")
        payload["claim_state"] = new_state
        payload["supersession_lineage"] = lineage
        updated = Claim.model_validate(payload)
        transition_payload = "|".join(
            (
                claim_id,
                current.claim_state.value,
                new_state.value,
                *(sorted(triggering_evidence_refs)),
                normalize_utc(transitioned_at).isoformat(),
                replacement_claim_id or "",
                corroborating_claim_id or "",
            )
        )
        event = TransitionEvent(
            transition_id="csia:transition:" + hashlib.sha256(transition_payload.encode("utf-8")).hexdigest()[:24],
            claim_id=claim_id,
            prior_state=current.claim_state,
            new_state=new_state,
            triggering_evidence_refs=triggering_evidence_refs,
            resulting_claim=updated,
            corroborating_claim_id=corroborating_claim_id,
            transitioned_at=transitioned_at,
            operator_involvement=operator_involvement,
        )
        return self.store.append_transition(updated, event)


__all__ = ["ClaimStateEngine", "IllegalClaimTransition", "LEGAL_TRANSITIONS"]
