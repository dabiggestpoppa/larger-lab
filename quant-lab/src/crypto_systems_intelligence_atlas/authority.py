"""CSIA Book 2 — Bloc 2E/F: source authority policy and discrepancy history."""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .sources import Source, SourceClass
from .temporal import Timestamp, UnknownBound, holds_at, normalize_utc
from .types import AuthorityTier, ClaimFamily


class AuthorityKey(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str = Field(min_length=1)
    claim_family: ClaimFamily
    valid_from: Timestamp | UnknownBound
    valid_to: Timestamp | UnknownBound | None = None

    def model_post_init(self, __context: object) -> None:
        if isinstance(self.valid_from, datetime):
            normalize_utc(self.valid_from)
        if isinstance(self.valid_to, datetime):
            normalize_utc(self.valid_to)
        if isinstance(self.valid_from, datetime) and isinstance(self.valid_to, datetime):
            if self.valid_from > self.valid_to:
                raise ValueError("authority valid_from > valid_to")

    def covers(self, at: datetime) -> bool:
        verdict = holds_at(self.valid_from, self.valid_to, normalize_utc(at))
        return verdict is True


class AuthorityAssignment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    key: AuthorityKey
    tier: AuthorityTier
    policy_version: str = Field(min_length=1)
    evidence_refs: tuple[str, ...] = ()


class DiscrepancyEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    discrepancy_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    claim_family: ClaimFamily
    valid_time: Timestamp | UnknownBound
    evidence_refs: tuple[str, ...] = Field(min_length=1)
    meta_claim_ref: str = Field(min_length=1)
    observed_at: datetime

    def model_post_init(self, __context: object) -> None:
        normalize_utc(self.observed_at)


class AuthorityDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    decision_id: str = Field(min_length=1)
    key: AuthorityKey
    tier_before: AuthorityTier
    tier_after: AuthorityTier
    supporting_evidence_refs: tuple[str, ...] = Field(min_length=1)
    discrepancy_meta_claim_refs: tuple[str, ...] = ()
    policy_version: str = Field(min_length=1)
    effective_at: datetime
    operator_review_ref: str | None = None
    supersedes_decision_id: str | None = None
    reversible: bool = True

    @model_validator(mode="after")
    def _downgrade_requires_review(self) -> "AuthorityDecision":
        if self.tier_before is not self.tier_after and self.operator_review_ref is None:
            raise ValueError("authority tier changes require operator review")
        return self


class AuthorityResolution(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str
    claim_family: ClaimFamily
    valid_time: Timestamp | UnknownBound
    tier: AuthorityTier
    policy_version: str | None = None
    evidence_refs: tuple[str, ...] = ()


_STRUCTURAL_FAMILIES = frozenset(
    {
        ClaimFamily.CHAIN_ARCHITECTURE,
        ClaimFamily.DEPLOYMENT_ACTIVATION,
        ClaimFamily.GOVERNANCE_EXECUTION,
        ClaimFamily.GOVERNANCE_PROPOSAL,
        ClaimFamily.INTEGRATION,
        ClaimFamily.SECURITY_EVENT,
        ClaimFamily.TOKEN_ROLE_MECHANICS,
        ClaimFamily.BRIDGE_ROUTE_STATE,
        ClaimFamily.VALIDATOR_SET_EPOCH_STATE,
    }
)


class AuthorityPolicy:
    """No method accepts a scalar global trust score."""

    def __init__(self) -> None:
        self._registered: dict[str, SourceClass] = {}
        self._assignments: dict[str, list[AuthorityAssignment]] = {}
        self._discrepancies: list[DiscrepancyEvent] = []
        self._decisions: list[AuthorityDecision] = []

    def register_source(self, source: Source) -> None:
        if source.source_id in self._registered:
            return
        self._registered[source.source_id] = source.source_class
        for seed in source.authority_metadata:
            self._assignments.setdefault(source.source_id, []).append(
                AuthorityAssignment(
                    key=AuthorityKey(
                        source_id=source.source_id,
                        claim_family=seed.claim_family,
                        valid_from=seed.valid_from,
                        valid_to=seed.valid_to,
                    ),
                    tier=seed.tier,
                    policy_version=seed.policy_version,
                    evidence_refs=seed.evidence_refs,
                )
            )

    def require_registered(self, source_id: str) -> SourceClass:
        try:
            return self._registered[source_id]
        except KeyError as exc:
            raise KeyError(f"unregistered source {source_id}") from exc

    def assign(
        self,
        *,
        source_id: str,
        claim_family: ClaimFamily,
        tier: AuthorityTier,
        valid_from: Timestamp | UnknownBound,
        valid_to: Timestamp | UnknownBound | None,
        policy_version: str,
        evidence_refs: tuple[str, ...] = (),
    ) -> AuthorityAssignment:
        self.require_registered(source_id)
        assignment = AuthorityAssignment(
            key=AuthorityKey(
                source_id=source_id,
                claim_family=claim_family,
                valid_from=valid_from,
                valid_to=valid_to,
            ),
            tier=tier,
            policy_version=policy_version,
            evidence_refs=evidence_refs,
        )
        self._assignments.setdefault(source_id, []).append(assignment)
        return assignment

    def _current_assignment(self, source_id: str, family: ClaimFamily, at: datetime) -> AuthorityAssignment | None:
        candidates = [
            assignment
            for assignment in self._assignments.get(source_id, ())
            if assignment.key.claim_family is family and assignment.key.covers(at)
        ]
        if not candidates:
            return None
        return sorted(candidates, key=lambda item: item.policy_version)[-1]

    def resolve(self, source_id: str, claim_family: ClaimFamily, at: datetime) -> AuthorityResolution:
        if source_id not in self._registered:
            return AuthorityResolution(
                source_id=source_id,
                claim_family=claim_family,
                valid_time=normalize_utc(at),
                tier=AuthorityTier.UNREGISTERED,
            )
        assignment = self._current_assignment(source_id, claim_family, at)
        if assignment is None:
            tier = AuthorityTier.INSUFFICIENT
            policy_version = None
            evidence_refs: tuple[str, ...] = ()
        else:
            tier = assignment.tier
            if (
                self._registered[source_id] is SourceClass.AGGREGATOR
                and claim_family in _STRUCTURAL_FAMILIES
                and tier is AuthorityTier.PRIMARY
            ):
                tier = AuthorityTier.INSUFFICIENT
            policy_version = assignment.policy_version
            evidence_refs = assignment.evidence_refs
        return AuthorityResolution(
            source_id=source_id,
            claim_family=claim_family,
            valid_time=normalize_utc(at),
            tier=tier,
            policy_version=policy_version,
            evidence_refs=evidence_refs,
        )

    def resolve_conflict(
        self,
        source_ids: Iterable[str],
        claim_family: ClaimFamily,
        at: datetime,
    ) -> AuthorityResolution | None:
        resolutions = [self.resolve(source_id, claim_family, at) for source_id in source_ids]
        primary = [item for item in resolutions if item.tier is AuthorityTier.PRIMARY]
        if len(primary) == 1:
            return primary[0]
        if len(primary) > 1:
            # RPC is primary over explorer for live-state observations; this
            # tie-break is family-specific and never becomes a global score.
            rpc = [item for item in primary if self._registered[item.source_id] is SourceClass.RPC]
            if len(rpc) == 1 and claim_family in {
                ClaimFamily.DEPLOYMENT_ACTIVATION,
                ClaimFamily.BRIDGE_ROUTE_STATE,
                ClaimFamily.VALIDATOR_SET_EPOCH_STATE,
            }:
                return rpc[0]
        return None

    def record_discrepancy(
        self,
        *,
        source_id: str,
        claim_family: ClaimFamily,
        valid_time: Timestamp | UnknownBound,
        evidence_refs: tuple[str, ...],
        meta_claim_ref: str,
        observed_at: datetime,
    ) -> DiscrepancyEvent:
        self.require_registered(source_id)
        if not evidence_refs:
            raise ValueError("a discrepancy requires preserved evidence")
        payload = "|".join((source_id, claim_family.value, meta_claim_ref, observed_at.isoformat()))
        event = DiscrepancyEvent(
            discrepancy_id="csia:discrepancy:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24],
            source_id=source_id,
            claim_family=claim_family,
            valid_time=valid_time,
            evidence_refs=evidence_refs,
            meta_claim_ref=meta_claim_ref,
            observed_at=observed_at,
        )
        self._discrepancies.append(event)
        return event

    def downgrade(
        self,
        *,
        source_id: str,
        claim_family: ClaimFamily,
        valid_from: Timestamp | UnknownBound,
        valid_to: Timestamp | UnknownBound | None,
        new_tier: AuthorityTier,
        repeated_evidence_refs: tuple[str, ...],
        discrepancy_meta_claim_refs: tuple[str, ...],
        policy_version: str,
        effective_at: datetime,
        operator_review_ref: str,
    ) -> AuthorityDecision:
        self.require_registered(source_id)
        if len(set(repeated_evidence_refs)) < 2:
            raise ValueError("authority downgrade requires repeated evidence")
        current = self._current_assignment(source_id, claim_family, effective_at)
        before = current.tier if current else AuthorityTier.INSUFFICIENT
        if before is new_tier:
            raise ValueError("downgrade must change the family-scoped tier")
        decision = AuthorityDecision(
            decision_id="csia:authority:" + hashlib.sha256(
                f"{source_id}|{claim_family.value}|{effective_at.isoformat()}|{new_tier.value}".encode("utf-8")
            ).hexdigest()[:24],
            key=AuthorityKey(
                source_id=source_id,
                claim_family=claim_family,
                valid_from=valid_from,
                valid_to=valid_to,
            ),
            tier_before=before,
            tier_after=new_tier,
            supporting_evidence_refs=repeated_evidence_refs,
            discrepancy_meta_claim_refs=discrepancy_meta_claim_refs,
            policy_version=policy_version,
            effective_at=effective_at,
            operator_review_ref=operator_review_ref,
        )
        self._decisions.append(decision)
        self.assign(
            source_id=source_id,
            claim_family=claim_family,
            tier=new_tier,
            valid_from=valid_from,
            valid_to=valid_to,
            policy_version=policy_version,
            evidence_refs=repeated_evidence_refs,
        )
        return decision

    def restore(
        self,
        decision: AuthorityDecision,
        *,
        evidence_refs: tuple[str, ...],
        effective_at: datetime,
        operator_review_ref: str,
    ) -> AuthorityDecision:
        if not evidence_refs:
            raise ValueError("authority restoration requires evidence")
        restored = AuthorityDecision(
            decision_id="csia:authority:restore:" + hashlib.sha256(
                f"{decision.decision_id}|{effective_at.isoformat()}".encode("utf-8")
            ).hexdigest()[:24],
            key=decision.key,
            tier_before=decision.tier_after,
            tier_after=decision.tier_before,
            supporting_evidence_refs=evidence_refs,
            discrepancy_meta_claim_refs=decision.discrepancy_meta_claim_refs,
            policy_version=decision.policy_version,
            effective_at=effective_at,
            operator_review_ref=operator_review_ref,
            supersedes_decision_id=decision.decision_id,
        )
        self._decisions.append(restored)
        self.assign(
            source_id=decision.key.source_id,
            claim_family=decision.key.claim_family,
            tier=restored.tier_after,
            valid_from=decision.key.valid_from,
            valid_to=decision.key.valid_to,
            policy_version=decision.policy_version,
            evidence_refs=evidence_refs,
        )
        return restored

    def discrepancy_history(self, source_id: str, claim_family: ClaimFamily) -> tuple[DiscrepancyEvent, ...]:
        return tuple(
            event
            for event in self._discrepancies
            if event.source_id == source_id and event.claim_family is claim_family
        )

    @property
    def decisions(self) -> tuple[AuthorityDecision, ...]:
        return tuple(self._decisions)


__all__ = [
    "AuthorityAssignment",
    "AuthorityDecision",
    "AuthorityKey",
    "AuthorityPolicy",
    "AuthorityResolution",
    "DiscrepancyEvent",
]
