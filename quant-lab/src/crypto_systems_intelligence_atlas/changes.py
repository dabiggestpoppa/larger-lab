"""CSIA Book 2 — Bloc 2H: deterministic change candidates."""

from __future__ import annotations

import hashlib
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .temporal import Timestamp, UnknownBound, normalize_utc


class ChangeClass(str, Enum):
    NEW_OBJECT = "NEW_OBJECT"
    NEW_RELATIONSHIP = "NEW_RELATIONSHIP"
    REMOVED_RELATIONSHIP = "REMOVED_RELATIONSHIP"
    MIGRATION = "MIGRATION"
    DEPRECATION = "DEPRECATION"
    UPGRADE = "UPGRADE"
    NEW_DEPLOYMENT = "NEW_DEPLOYMENT"
    BRIDGE_CHANGE = "BRIDGE_CHANGE"
    ORACLE_CHANGE = "ORACLE_CHANGE"
    STABLECOIN_CHANGE = "STABLECOIN_CHANGE"
    GOVERNANCE_CHANGE = "GOVERNANCE_CHANGE"
    SECURITY_CHANGE = "SECURITY_CHANGE"
    TOKEN_ROLE_CHANGE = "TOKEN_ROLE_CHANGE"


class ChangeCandidate(BaseModel):
    """A detected diff, never a promoted graph fact."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_id: str = Field(min_length=1)
    change_class: ChangeClass
    evidence_refs: tuple[str, ...] = ()
    claim_context_refs: tuple[str, ...] = ()
    before_evidence_refs: tuple[str, ...] = ()
    after_evidence_refs: tuple[str, ...] = ()
    object_refs: tuple[str, ...] = ()
    relationship_refs: tuple[str, ...] = ()
    valid_time_hint: Timestamp | UnknownBound
    detected_at: datetime

    @model_validator(mode="after")
    def _context_required(self) -> "ChangeCandidate":
        if not self.evidence_refs and not self.claim_context_refs and not self.before_evidence_refs and not self.after_evidence_refs:
            raise ValueError("change candidates require evidence or claim context")
        if not self.before_evidence_refs and not self.after_evidence_refs:
            raise ValueError("change candidates require before/after evidence context")
        normalize_utc(self.detected_at)
        return self


class ChangeCandidateStore:
    def __init__(self) -> None:
        self._candidates: dict[str, ChangeCandidate] = {}

    def add(self, candidate: ChangeCandidate) -> ChangeCandidate:
        if candidate.candidate_id in self._candidates:
            raise ValueError(f"change candidate {candidate.candidate_id} already exists")
        self._candidates[candidate.candidate_id] = candidate
        return candidate

    def detect(
        self,
        *,
        change_class: ChangeClass,
        before_evidence_refs: tuple[str, ...],
        after_evidence_refs: tuple[str, ...],
        valid_time_hint: Timestamp | UnknownBound,
        detected_at: datetime,
        evidence_refs: tuple[str, ...] = (),
        claim_context_refs: tuple[str, ...] = (),
        object_refs: tuple[str, ...] = (),
        relationship_refs: tuple[str, ...] = (),
    ) -> ChangeCandidate:
        context = (*evidence_refs, *claim_context_refs, *before_evidence_refs, *after_evidence_refs)
        payload = "|".join((change_class.value, *sorted(context), normalize_utc(detected_at).isoformat()))
        candidate = ChangeCandidate(
            candidate_id="csia:change:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24],
            change_class=change_class,
            evidence_refs=evidence_refs,
            claim_context_refs=claim_context_refs,
            before_evidence_refs=before_evidence_refs,
            after_evidence_refs=after_evidence_refs,
            object_refs=object_refs,
            relationship_refs=relationship_refs,
            valid_time_hint=valid_time_hint,
            detected_at=detected_at,
        )
        return self.add(candidate)

    def require(self, candidate_id: str) -> ChangeCandidate:
        try:
            return self._candidates[candidate_id]
        except KeyError as exc:
            raise KeyError(f"unknown change candidate {candidate_id}") from exc

    @property
    def candidates(self) -> dict[str, ChangeCandidate]:
        return dict(self._candidates)


__all__ = ["ChangeCandidate", "ChangeCandidateStore", "ChangeClass"]
