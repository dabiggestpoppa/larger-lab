"""Policy-backed step authority gate + approval sink (P2-R2-C01/C02).

Binds the standalone governance stack (Book V 13.2 policy engine, durable
policy decision log, approval registry) into the orchestrator's execution
path. The orchestrator depends only on the ports in
``qcae.orchestration.authority_gate``; this adapter lives in governance
where the mapping is defined (ADR-0009).

Mapping law: the policy engine's decision vocabulary IS the gate's decision
vocabulary (both are the Book V 13.2 set); any unknown policy decision fails
closed (DENY) rather than widening authority.

The gate evaluates with the full binding (principal -> action -> resource ->
scope -> requirement) as a PolicyRequest, so the durable policy log records
the exact question asked. The sink turns REQUIRE_APPROVAL verdicts into
durable ApprovalRequest records bound to the verdict's exact
action/resource/scope — the same binding a grant must restate (no approval
laundering, directive §14).
"""

from __future__ import annotations

import hashlib
import secrets

from qcae.core.errors import QcaeValidationError
from qcae.governance.standalone.approvals import ApprovalRequest
from qcae.governance.standalone.authority import LocalAuthorityProvider
from qcae.governance.standalone.policy import (
    LocalPolicyEngine,
    PolicyDecisionType,
    PolicyRequest,
)
from qcae.orchestration.authority_gate import (
    StepAuthorityDecision,
    StepAuthorityVerdict,
)

__all__ = ["PolicyStepAuthorityGate", "ApprovalRegistrySink"]


class PolicyStepAuthorityGate:
    """StepAuthorityGate over the local policy engine + decision log."""

    def __init__(
        self,
        policy_engine: LocalPolicyEngine,
        authority_provider: LocalAuthorityProvider,
        *,
        clock,
    ) -> None:
        self._policy = policy_engine
        self._authority = authority_provider
        self._clock = clock

    def evaluate_step_authority(self, step, job, *, worker_id: str) -> StepAuthorityVerdict:
        declared = (step.authority_requirement or "").strip()
        action = declared or f"execute.{step.step_type}"
        scope = job.authority_context_ref or f"job:{job.job_id}"

        policy_request = PolicyRequest(
            principal=worker_id,
            action=action,
            resource=job.subject_ref,
            scope=scope,
            environment="local",
            risk_class="",
        )
        request_ref = f"stepauth:{job.job_id}:{step.step_id}:{step.attempt}"
        decision = self._authority.evaluate_policy(
            policy_request, request_ref=request_ref
        )

        if decision.decision is PolicyDecisionType.ALLOW:
            gate_decision = StepAuthorityDecision.ALLOW
            constraints: tuple = ()
        elif decision.decision is PolicyDecisionType.ALLOW_WITH_CONSTRAINTS:
            gate_decision = StepAuthorityDecision.ALLOW_WITH_CONSTRAINTS
            constraints = tuple(decision.constraints)
        elif decision.decision is PolicyDecisionType.REQUIRE_APPROVAL:
            gate_decision = StepAuthorityDecision.REQUIRE_APPROVAL
            constraints = ()
        elif decision.decision is PolicyDecisionType.DENY:
            gate_decision = StepAuthorityDecision.DENY
            constraints = ()
        else:
            # Unknown policy decision: fail closed (never widen authority).
            gate_decision = StepAuthorityDecision.DENY
            constraints = ()

        return StepAuthorityVerdict(
            step_id=step.step_id,
            job_id=job.job_id,
            principal=worker_id,
            action=action,
            resource=job.subject_ref,
            scope=scope,
            decision=gate_decision,
            decision_ref=decision.decision_id,
            policy_version=decision.policy_version,
            evaluated_at=self._clock(),
            reason=decision.reason,
            constraints=constraints,
            requirement=declared,
        )


class ApprovalRegistrySink:
    """Persist REQUIRE_APPROVAL verdicts as durable, exact-bound requests.

    Every request carries an explicit approval window (directive §13-14:
    grants are bounded, never indefinite). The default window is 24h;
    ``effective_grant`` returns None past it, so stale grants cannot execute.
    """

    DEFAULT_WINDOW_SECONDS = 24 * 3600

    def __init__(self, approval_registry, *, clock,
                 window_seconds: int = DEFAULT_WINDOW_SECONDS) -> None:
        self._registry = approval_registry
        self._clock = clock
        self._window = window_seconds

    def _expires_at(self) -> str:
        from datetime import datetime, timedelta, timezone

        now = self._clock()
        try:
            base = datetime.strptime(now, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            return ""  # non-ISO clock: caller must manage windows explicitly
        return (base + timedelta(seconds=self._window)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

    def record_authority_request(self, verdict: StepAuthorityVerdict) -> str:
        # P2-R4-C03 (directive §8): request identity is RESTART-SAFE — an
        # in-memory counter resets on restart and can collide with durable
        # rows. The id is a digest over the request's exact semantics plus a
        # uniqueness suffix for genuinely distinct repeat requests (retry
        # after failure); it never depends on process-local state.
        semantics = (
            f"{verdict.step_id}|{verdict.principal}|{verdict.action}|"
            f"{verdict.resource}|{verdict.scope}"
        )
        semantic_digest = hashlib.sha256(semantics.encode("utf-8")).hexdigest()[:12]
        request_id = f"authreq-{verdict.step_id}-{semantic_digest}-{secrets.token_hex(4)}"
        self._registry.add_request(
            ApprovalRequest(
                request_id=request_id,
                principal=verdict.principal,
                action=verdict.action,
                resource=verdict.resource,
                scope=verdict.scope,
                budget_ref=verdict.scope,  # exact binding; budget joins scope
                justification=verdict.reason or "step requires approval",
                created_at=self._clock(),
                expires_at=self._expires_at(),
            )
        )
        return request_id
