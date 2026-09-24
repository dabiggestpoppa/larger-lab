"""CSIA Book 2 — Bloc 2E: claim state transition engine."""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Final

from .claims import Claim, ClaimService, ClaimState, ClaimStore, SupersessionLineage, TransitionEvent
from .temporal import normalize_utc

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
    ClaimState.VERIFIED: frozenset(),
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
            )
        )
        event = TransitionEvent(
            transition_id="csia:transition:" + hashlib.sha256(transition_payload.encode("utf-8")).hexdigest()[:24],
            claim_id=claim_id,
            prior_state=current.claim_state,
            new_state=new_state,
            triggering_evidence_refs=triggering_evidence_refs,
            transitioned_at=transitioned_at,
            operator_involvement=operator_involvement,
        )
        return self.store.append_transition(updated, event)


__all__ = ["ClaimStateEngine", "IllegalClaimTransition", "LEGAL_TRANSITIONS"]
