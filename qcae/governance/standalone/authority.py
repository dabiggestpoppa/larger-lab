"""Local AuthorityProvider (P2-C04; ADR-0009, Book V 13.2/14).

Implements the frozen P0 ``AuthorityProvider`` Protocol (``qcae.core.
decisions.authority``) over the local policy engine. Governance code is
engine-agnostic: durable request/decision persistence goes through the
``PolicyDecisionLog`` port; the SQLite adapter lives in infrastructure
(governance/standalone must not import storage engines — architecture guard,
canon 15.2).

Approvals are separate records, never edits of the original request
(P2 directive §13).

Mapping (ADR-0009): ALLOW/ALLOW_WITH_CONSTRAINTS -> GRANT,
REQUIRE_APPROVAL -> REQUEST_MORE_EVIDENCE, DENY -> DENY.
"""

from __future__ import annotations

from typing import List, Optional, Protocol

from qcae.core.decisions.authority import (
    AuthorityDecision,
    AuthorityOutcome,
    AuthorityProvider,
    AuthorityRequest,
)
from qcae.core.errors import QcaeValidationError
from qcae.governance.standalone.policy import (
    PolicyDecision,
    PolicyDecisionType,
    PolicyRequest,
)

__all__ = [
    "PolicyDecisionLog",
    "LocalAuthorityProvider",
    "policy_outcome_to_authority_outcome",
]


class PolicyDecisionLog(Protocol):
    """Port for durable policy request/decision persistence."""

    def record_request(self, request_ref: str, request: PolicyRequest) -> None: ...

    def record_decision(self, request_ref: str, decision: PolicyDecision) -> None: ...

    def decisions_for_request(self, request_ref: str) -> List[PolicyDecision]: ...

    def get_decision(self, decision_id: str) -> Optional[PolicyDecision]: ...


def policy_outcome_to_authority_outcome(decision: PolicyDecision) -> AuthorityOutcome:
    """ADR-0009 mapping; any future unmapped value fails closed."""
    if decision.decision in (PolicyDecisionType.ALLOW, PolicyDecisionType.ALLOW_WITH_CONSTRAINTS):
        return AuthorityOutcome.GRANT
    if decision.decision is PolicyDecisionType.REQUIRE_APPROVAL:
        return AuthorityOutcome.REQUEST_MORE_EVIDENCE
    if decision.decision is PolicyDecisionType.DENY:
        return AuthorityOutcome.DENY
    raise QcaeValidationError(
        f"unmapped policy decision {decision.decision!r}; refusing to widen authority"
    )


class LocalAuthorityProvider(AuthorityProvider):
    """Standalone authority: policy engine + durable decision log."""

    def __init__(self, policy_engine, decision_log: PolicyDecisionLog, *, clock) -> None:
        self._engine = policy_engine
        self._log = decision_log
        self._clock = clock
        self._counter = 0

    def _next_id(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}-{self._counter:08d}"

    def decide(self, request: AuthorityRequest) -> AuthorityDecision:
        """P0 Protocol entry point (lifecycle-level)."""
        request.validate()
        now = self._clock()
        policy_request = PolicyRequest(
            principal=request.requested_by,
            action=request.action.value,
            resource=request.subject_id,
            scope=str(request.context.get("scope", "")),
            classification=str(request.context.get("classification", "")),
            budget_ref=str(request.context.get("budget_ref", "")),
            risk_class=str(request.context.get("risk_class", "")),
        )
        decision = self.evaluate_policy(policy_request, request_ref=request.request_id)
        outcome = policy_outcome_to_authority_outcome(decision)
        return AuthorityDecision(
            decision_id=self._next_id("authdec"),
            request_ref=request.request_id,
            action=request.action,
            outcome=outcome,
            decided_by="local-policy",
            decided_at=now,
            reason=decision.reason,
        )

    def evaluate_policy(
        self, request: PolicyRequest, *, request_ref: str
    ) -> PolicyDecision:
        """13.2-level evaluation with durable request/decision records."""
        now = self._clock()
        self._log.record_request(request_ref, request)
        decision = self._engine.evaluate(
            request, decision_id=self._next_id("poldec"), created_at=now
        )
        self._log.record_decision(request_ref, decision)
        return decision

    def logged_decisions_for(self, request_ref: str) -> List[PolicyDecision]:
        return self._log.decisions_for_request(request_ref)

    def logged_decision(self, decision_id: str) -> Optional[PolicyDecision]:
        return self._log.get_decision(decision_id)
