"""CSIA Book 2 — Bloc 2G: versioned freshness and staleness policies."""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .temporal import normalize_utc


class FreshnessOutcome(str, Enum):
    FRESH = "FRESH"
    STALE = "STALE"
    REQUIRES_CHAIN_CONTEXT = "REQUIRES_CHAIN_CONTEXT"


class ChainFreshnessContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    window_id: str = Field(min_length=1)
    observed_window: str = Field(min_length=1)
    current_window: str = Field(min_length=1)


class StalenessKind(str, Enum):
    SOURCE_STALE = "SOURCE_STALE"
    EVIDENCE_STALE = "EVIDENCE_STALE"
    CLAIM_STALE = "CLAIM_STALE"
    RELATIONSHIP_STALE = "RELATIONSHIP_STALE"


class FreshnessMode(str, Enum):
    SHORT = "SHORT"
    MEDIUM = "MEDIUM"
    FAST_DECAY = "FAST_DECAY"
    EVENT_DRIVEN = "EVENT_DRIVEN"
    SUPERSESSION_ORIENTED = "SUPERSESSION_ORIENTED"
    CHAIN_SPECIFIC = "CHAIN_SPECIFIC"
    HISTORICAL_NO_DECAY = "HISTORICAL_NO_DECAY"


class FreshnessPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    policy_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    kind: StalenessKind
    mode: FreshnessMode
    max_age_seconds: int | None = Field(default=None, ge=0)
    chain_specific_window: str | None = None

    @model_validator(mode="after")
    def _policy_shape(self) -> "FreshnessPolicy":
        if self.mode in (FreshnessMode.EVENT_DRIVEN, FreshnessMode.SUPERSESSION_ORIENTED, FreshnessMode.HISTORICAL_NO_DECAY):
            if self.max_age_seconds is not None or self.chain_specific_window is not None:
                raise ValueError("non-decaying policies cannot carry a duration")
        if self.mode is FreshnessMode.CHAIN_SPECIFIC and not self.chain_specific_window:
            raise ValueError("chain-specific policy requires a named window")
        if self.mode in (FreshnessMode.SHORT, FreshnessMode.MEDIUM, FreshnessMode.FAST_DECAY) and self.max_age_seconds is None:
            raise ValueError("decaying policy requires an explicit max age")
        return self


class FreshnessEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: StalenessKind
    policy_id: str
    policy_version: str
    stale: bool | None
    outcome: FreshnessOutcome
    evaluated_at: datetime
    reason: str

    def model_post_init(self, __context: object) -> None:
        normalize_utc(self.evaluated_at)


class FreshnessPolicyBook:
    def __init__(self) -> None:
        self._policies: dict[str, list[FreshnessPolicy]] = {}

    def register(self, policy: FreshnessPolicy) -> FreshnessPolicy:
        history = self._policies.setdefault(policy.policy_id, [])
        if any(item.version == policy.version for item in history):
            raise ValueError("policy version already registered")
        history.append(policy)
        return policy

    def require(self, policy_id: str, version: str | None = None) -> FreshnessPolicy:
        history = self._policies.get(policy_id)
        if not history:
            raise KeyError(f"unknown freshness policy {policy_id}")
        if version is not None:
            for policy in history:
                if policy.version == version:
                    return policy
            raise KeyError(f"unknown policy version {policy_id}:{version}")
        return history[-1]

    def evaluate(
        self,
        policy_id: str,
        *,
        observed_at: datetime,
        now: datetime,
        version: str | None = None,
        chain_context: ChainFreshnessContext | None = None,
    ) -> FreshnessEvaluation:
        policy = self.require(policy_id, version)
        observed_at = normalize_utc(observed_at)
        now = normalize_utc(now)
        if now < observed_at:
            raise ValueError("evaluation time cannot precede observed time")
        if policy.mode is FreshnessMode.CHAIN_SPECIFIC:
            if chain_context is None:
                stale = None
                outcome = FreshnessOutcome.REQUIRES_CHAIN_CONTEXT
                reason = "chain-specific policy requires deterministic chain context"
            elif chain_context.window_id != policy.chain_specific_window:
                stale = None
                outcome = FreshnessOutcome.REQUIRES_CHAIN_CONTEXT
                reason = "chain context does not match the policy window"
            else:
                stale = chain_context.observed_window != chain_context.current_window
                outcome = FreshnessOutcome.STALE if stale else FreshnessOutcome.FRESH
                reason = "chain window changed" if stale else "chain window unchanged"
        elif policy.mode in (FreshnessMode.EVENT_DRIVEN, FreshnessMode.SUPERSESSION_ORIENTED, FreshnessMode.HISTORICAL_NO_DECAY):
            stale = False
            outcome = FreshnessOutcome.FRESH
            reason = f"{policy.mode.value} does not decay by elapsed time"
        else:
            assert policy.max_age_seconds is not None
            stale = now > observed_at + timedelta(seconds=policy.max_age_seconds)
            outcome = FreshnessOutcome.STALE if stale else FreshnessOutcome.FRESH
            reason = "elapsed time exceeds policy max age" if stale else "within policy max age"
        return FreshnessEvaluation(
            kind=policy.kind,
            policy_id=policy.policy_id,
            policy_version=policy.version,
            stale=stale,
            outcome=outcome,
            evaluated_at=now,
            reason=reason,
        )


__all__ = [
    "ChainFreshnessContext",
    "FreshnessEvaluation",
    "FreshnessOutcome",
    "FreshnessMode",
    "FreshnessPolicy",
    "FreshnessPolicyBook",
    "StalenessKind",
]
