"""CSIA Book 2 — Bloc 2F: deterministic contradiction resolution."""

from __future__ import annotations

import hashlib
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from .authority import AuthorityPolicy
from .claims import Claim
from .temporal import normalize_utc
from .types import ClaimFamily


class ResolutionKind(str, Enum):
    TIME_SPLIT = "TIME_SPLIT"
    AUTHORITY = "AUTHORITY"
    CONTESTED = "CONTESTED"


class ContradictionResolution(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    resolution_id: str = Field(min_length=1)
    kind: ResolutionKind
    claim_family: ClaimFamily
    left_claim_id: str
    right_claim_id: str
    preserved_evidence_refs: tuple[str, ...] = Field(min_length=2)
    winning_source_id: str | None = None
    discrepancy_meta_claim_id: str | None = None
    resolved_at: datetime
    reason: str

    def model_post_init(self, __context: object) -> None:
        normalize_utc(self.resolved_at)


class ContradictionEngine:
    def __init__(self, authority: AuthorityPolicy) -> None:
        self.authority = authority

    def resolve(
        self,
        *,
        left: Claim,
        right: Claim,
        claim_family: ClaimFamily,
        left_source_id: str,
        right_source_id: str,
        at: datetime,
        time_split_confirmed: bool = False,
    ) -> ContradictionResolution:
        at = normalize_utc(at)
        if left.claim_id == right.claim_id:
            raise ValueError("a claim cannot contradict itself")
        preserved = tuple(sorted(set((*left.evidence_refs, *right.evidence_refs))))
        if len(preserved) < 2:
            raise ValueError("contradiction requires two preserved evidence lines")
        meta_payload = f"{left.claim_id}|{right.claim_id}|{claim_family.value}"
        meta_id = "csia:meta:" + hashlib.sha256(meta_payload.encode("utf-8")).hexdigest()[:24]
        if time_split_confirmed:
            return ContradictionResolution(
                resolution_id=meta_id,
                kind=ResolutionKind.TIME_SPLIT,
                claim_family=claim_family,
                left_claim_id=left.claim_id,
                right_claim_id=right.claim_id,
                preserved_evidence_refs=preserved,
                discrepancy_meta_claim_id=meta_id,
                resolved_at=at,
                reason="valid-time split is primary when both propositions can hold in distinct windows",
            )
        winner = self.authority.resolve_conflict((left_source_id, right_source_id), claim_family, at)
        if winner is not None:
            return ContradictionResolution(
                resolution_id=meta_id,
                kind=ResolutionKind.AUTHORITY,
                claim_family=claim_family,
                left_claim_id=left.claim_id,
                right_claim_id=right.claim_id,
                preserved_evidence_refs=preserved,
                winning_source_id=winner.source_id,
                discrepancy_meta_claim_id=meta_id,
                resolved_at=at,
                reason=f"claim-family authority selected {winner.source_id}",
            )
        return ContradictionResolution(
            resolution_id=meta_id,
            kind=ResolutionKind.CONTESTED,
            claim_family=claim_family,
            left_claim_id=left.claim_id,
            right_claim_id=right.claim_id,
            preserved_evidence_refs=preserved,
            discrepancy_meta_claim_id=meta_id,
            resolved_at=at,
            reason="authority tied; preserving both claims as CONTESTED rather than averaging",
        )


__all__ = ["ContradictionEngine", "ContradictionResolution", "ResolutionKind"]
