"""Standalone local runtime service (P2-C10; Book V 13.1/13.7, directive §31).

One process, durable local stores. Responsibilities (directive §31):

- submit job (with policy evaluation and durable identity)
- inspect / list jobs
- run eligible steps
- resume jobs (crash recovery)
- cancel job (safe cancellation)
- record approval decisions
- recover expired leases
- expose runtime identity (Book V 13.1 Runtime Identity)

OCE is absent by construction: no OCE import, no OCE service, no OCE
credentials (Book V 13.8; directive §35). Mode is explicitly OCE_ABSENT.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from qcae.core.errors import QcaeValidationError
from qcae.core.jobs import deterministic_job_id
from qcae.governance.standalone.approvals import ApprovalDecision, ApprovalState
from qcae.governance.standalone.identity import LocalIdentityProvider
from qcae.orchestration.jobs.graph import StepGraph
from qcae.orchestration.jobs.runtime import (
    JobEvent,
    JobEventType,
    RuntimeJob,
    RuntimeJobStatus,
    RuntimeStep,
    RuntimeStepStatus,
    assert_job_transition,
    assert_step_transition,
)
from qcae.orchestration.orchestrator.engine import OrchestratorEngine

__all__ = ["LocalRuntimeService", "OCE_MODE", "RuntimeIdentity"]

#: Book V 13.8 mode awareness: the standalone runtime is explicitly
#: OCE_ABSENT. P12 migrates this to OCE_GOVERNING behind the provider seam.
OCE_MODE = "OCE_ABSENT"


@dataclass(frozen=True)
class RuntimeIdentity:
    """Book V 13.1 Runtime Identity (inspectable)."""

    runtime_id: str
    version: str
    schema_version: int
    policy_version: str
    oce_mode: str
    registered_workers: tuple
    storage_location: str


class LocalRuntimeService:
    """Composition root for standalone QCAE job execution."""

    def __init__(
        self,
        *,
        runtime_store,
        queue,
        engine: OrchestratorEngine,
        identity_provider: LocalIdentityProvider,
        policy_provider,
        approval_registry,
        clock: Callable[[], str],
        schema_version: int,
        policy_version: str,
        storage_location: str,
        runtime_id: str = "runtime-local-1",
        version: str = "0.1.0",
    ) -> None:
        self._store = runtime_store
        self._queue = queue
        self._engine = engine
        self._identity = identity_provider
        self._authority = policy_provider
        self._approvals = approval_registry
        self._clock = clock
        self._schema_version = schema_version
        self._policy_version = policy_version
        self._storage_location = storage_location
        self._runtime_id = runtime_id
        self._version = version

    # -- identity ------------------------------------------------------------

    def identity(self) -> RuntimeIdentity:
        return RuntimeIdentity(
            runtime_id=self._runtime_id,
            version=self._version,
            schema_version=self._schema_version,
            policy_version=self._policy_version,
            oce_mode=OCE_MODE,
            # P2-R2-C05: public engine interface (registered_worker_types),
            # never a private attribute read.
            registered_workers=tuple(self._engine.registered_worker_types()),
            storage_location=self._storage_location,
        )

    def require_identity(self, identity_id: str) -> None:
        """Public identity check (P2-R2-C05): interfaces never reach into
        the identity provider directly."""
        self._identity.require(identity_id)

    def authority_decide(self, request):
        """Governance surface: one authority decision for one request."""
        return self._authority.decide(request)

    # -- job lifecycle -------------------------------------------------------

    def submit(
        self, job: RuntimeJob, steps: List[RuntimeStep], *,
        submitted_by: Optional[str] = None, not_before: str = "",
    ) -> RuntimeJob:
        """Submit a bounded job; fails closed on policy denial."""
        if submitted_by is not None:
            self._identity.require(submitted_by)
        return self._engine.submit(job, steps, not_before=not_before)

    def inspect(self, job_id: str) -> Optional[dict]:
        job = self._store.get_job(job_id)
        if job is None:
            return None
        steps = self._store.list_steps_for_job(job_id)
        return {
            "job": job,
            "steps": steps,
            "events": [
                {"seq": seq, "type": ev.event_type.value, "step_id": ev.step_id}
                for seq, ev, _payload in self._store.events_for_job(job_id)
            ],
            "checkpoint": self._store.latest_checkpoint_for_job(job_id),
        }

    def list_jobs(self, *, status: Optional[RuntimeJobStatus] = None) -> List[RuntimeJob]:
        return self._store.list_jobs(status=status)

    # -- execution -----------------------------------------------------------

    def ready_steps(self, job_id: str) -> List[RuntimeStep]:
        return self._engine.ready_steps(job_id)

    def lease_next(self, job_id: str, worker_id: str):
        return self._engine.lease_next(job_id, worker_id)

    def execute_step(self, lease, *, worker_id: Optional[str] = None):
        """Execute under the engine's typed authority gate (P2-R2-C01).

        Authority is evaluated by the gate inside the engine — the service
        neither bypasses nor pre-approves it.
        """
        return self._engine.execute_step(lease, worker_id=worker_id)

    def mark_running(self, job_id: str):
        """Public job-state driver (P2-R2-C05: no private-attribute reach-in)."""
        return self._engine.mark_running(job_id)

    def release_granted_step(self, job_id: str, step_id: str) -> None:
        """Release one WAITING_POLICY step after a verified exact-scope grant.

        The service verifies the grant binds the step's recorded request
        (action/resource/scope/budget) BEFORE delegating to the engine
        (P2-R2-C02; directive §14 — no approval laundering).
        """
        self._release_with_verified_grant(job_id, step_id)

    def resume(self, job_id: str) -> dict:
        """Recover a job after interruption (directive §23)."""
        return self._engine.recover_job(job_id)

    def recover_expired_leases(self) -> List[str]:
        """P2-R3-C03 (finding C): global recovery owns BOTH layers.

        TTL-expired queue claims are released AND their durable runtime
        steps are reconciled to a safe state by the same authoritative law
        (`OrchestratorEngine.recover_leased_steps`). A claim deletion that
        leaves the step RUNNING forever is not recovery. Returns the
        reconciled step ids.
        """
        expired = self._queue.expire_stale_leases()
        return self._engine.recover_leased_steps(expired)

    def recover_orphan_steps(self, job_id: str) -> dict:
        """Classify RUNNING steps with no queue claim (orphan state)."""
        return self._engine.recover_orphan_steps(job_id)

    # -- cancellation --------------------------------------------------------

    def cancel(self, job_id: str, *, reason: str = "") -> RuntimeJob:
        """Safe cancellation (directive §29).

        QUEUED/CREATED: immediate. RUNNING: cancels at the next safe
        boundary — running steps are released at the queue layer and move to
        CANCELLED; committed evidence is never touched. Terminal jobs are
        immutable history.
        """
        job = self._store.get_job(job_id)
        if job is None:
            raise QcaeValidationError(f"unknown job {job_id!r}")
        if job.status in (RuntimeJobStatus.SUCCEEDED, RuntimeJobStatus.FAILED,
                          RuntimeJobStatus.CANCELLED):
            raise QcaeValidationError(
                f"job {job_id!r} is terminal ({job.status.value}); history cannot be rewritten"
            )
        steps = self._store.list_steps_for_job(job_id)
        from dataclasses import replace as dc_replace

        for step in steps:
            if step.status in (
                RuntimeStepStatus.PENDING, RuntimeStepStatus.READY,
                RuntimeStepStatus.WAITING_INPUT, RuntimeStepStatus.RETRY_SCHEDULED,
                RuntimeStepStatus.WAITING_POLICY,
            ):
                assert_step_transition(step.status, RuntimeStepStatus.CANCELLED)
                self._store.update_step(
                    dc_replace(step, status=RuntimeStepStatus.CANCELLED),
                    lease_owner="", lease_token="", lease_expires_at="",
                )
            elif step.status is RuntimeStepStatus.RUNNING:
                # Safe boundary: release the lease; the step cannot complete
                # after cancellation because its token is gone.
                self._store.update_step(
                    dc_replace(step, status=RuntimeStepStatus.CANCELLED),
                    lease_owner="", lease_token="", lease_expires_at="",
                )
        assert_job_transition(job.status, RuntimeJobStatus.CANCELLED)
        from dataclasses import replace as dc_replace
        from qcae.orchestration.jobs.runtime import JobEvent

        updated = dc_replace(job, status=RuntimeJobStatus.CANCELLED,
                             updated_at=self._clock())
        self._store.update_job(updated)
        # P2-C07R4: event identity is store-allocated (no engine internals).
        self._store.append_event(
            JobEvent(
                event_seq=0,
                event_id="",
                event_type=JobEventType.JOB_CANCELLED,
                job_id=job_id,
                occurred_at=self._clock(),
            ),
            payload_json=f'{{"reason": "{reason}"}}',
        )
        return updated

    # -- approvals -----------------------------------------------------------

    def pending_approvals(self):
        return self._approvals.pending_requests()

    def record_approval(self, decision) -> None:
        self._approvals.record_decision(decision)

    # -- event log (P2-C11: operator-facing append-oriented history) ----------

    def job_events(self, job_id: str) -> List[dict]:
        """Append-oriented event stream for one job (facts, never commands)."""
        if self._store.get_job(job_id) is None:
            raise QcaeValidationError(f"unknown job {job_id!r}")
        return [
            {
                "seq": seq,
                "event_id": ev.event_id,
                "type": ev.event_type.value,
                "step_id": ev.step_id,
                "occurred_at": ev.occurred_at,
                "actor": ev.actor,
                "payload": payload,
            }
            for seq, ev, payload in self._store.events_for_job(job_id)
        ]

    def decide_approval(
        self, *, request_id: str, decision: str, decided_by: str,
        job_id: str = "", reason: str = "",
    ) -> dict:
        """Record a durable operator decision on one exact approval request.

        Grant/deny are separate durable artifacts bound to the request's
        exact scope (no approval laundering — directive §14). Service-side
        identity/consistency checks; not a CLI concern.
        """
        request = self._approvals.get_request(request_id)
        if request is None:
            raise QcaeValidationError(f"unknown approval request {request_id!r}")
        if self._already_decided(request_id):
            raise QcaeValidationError(
                f"approval request {request_id!r} already decided; "
                "decisions are immutable artifacts (no re-decision)"
            )
        if job_id:
            # The event must point at a real job the caller can see.
            if self._store.get_job(job_id) is None:
                raise QcaeValidationError(f"unknown job {job_id!r}")
        if decided_by:
            self._identity.require(decided_by)
        state = ApprovalState(decision)
        decision_id = f"dec-{len(request_id)}-{secrets.token_hex(6)}"
        bound = {
            "bound_action": request.action,
            "bound_resource": request.resource,
            "bound_scope": request.scope,
            "bound_budget_ref": request.budget_ref,
        }
        self._approvals.record_decision(
            ApprovalDecision(
                decision_id=decision_id,
                request_ref=request_id,
                state=state,
                decided_by=decided_by,
                decided_at=self._clock(),
                reason=reason,
                **bound,
            )
        )
        event_type = (
            JobEventType.APPROVAL_GRANTED
            if state is ApprovalState.GRANTED
            else JobEventType.APPROVAL_DENIED
        )
        self._store.append_event(
            JobEvent(
                event_seq=0, event_id="", event_type=event_type,
                job_id=job_id, occurred_at=self._clock(),
            ),
            payload_json=(
                f'{{"request_id": "{request_id}", '
                f'"decision": "{state.value}", "decided_by": "{decided_by}"}}'
            ),
        )
        return {"decision_id": decision_id, "state": state.value,
                "request_id": request_id}

    # -- P2-R2-C02: verified grant release -----------------------------------

    def _release_with_verified_grant(self, job_id: str, step_id: str) -> None:
        """Verify an exact-scope grant exists for the step's request, then release.

        The step's APPROVAL_REQUESTED event names the authority request; the
        registry must hold a GRANTED decision bound to the same
        (action, resource, scope, budget_ref) and not expired. Anything else
        fails closed.
        """
        from qcae.governance.standalone.approvals import ApprovalState

        step = self._store.get_step(step_id)
        if step is None or step.job_id != job_id:
            raise QcaeValidationError(f"unknown step {step_id!r} for job {job_id!r}")
        if step.status is not RuntimeStepStatus.WAITING_POLICY:
            raise QcaeValidationError(
                f"step {step_id!r} is not WAITING_POLICY; nothing to release"
            )
        # Find the durable authority request recorded for this step.
        request_id = self._latest_authority_request_for_step(job_id, step_id)
        if request_id is None:
            raise QcaeValidationError(
                f"no authority request recorded for step {step_id!r}; refusing release"
            )
        request = self._approvals.get_request(request_id)
        if request is None:
            raise QcaeValidationError(
                f"authority request {request_id!r} not found; refusing release"
            )
        grant = self._approvals.effective_grant(request_id, now=self._clock())
        if grant is None:
            raise QcaeValidationError(
                f"no effective grant for request {request_id!r} "
                "(pending, denied, or expired); refusing release"
            )
        if grant.state is not ApprovalState.GRANTED:
            raise QcaeValidationError("grant is not GRANTED; refusing release")
        # Exact binding (directive §14): every bound element must equal the
        # request the step raised. A grant for another action/scope/budget
        # cannot release this step.
        if (
            grant.bound_action != request.action
            or grant.bound_resource != request.resource
            or grant.bound_scope != request.scope
            or grant.bound_budget_ref != request.budget_ref
        ):
            raise QcaeValidationError(
                "grant binding does not match the step's request; "
                "approval laundering rejected"
            )
        self._engine.record_exact_scope_grant(job_id, step_id)

    def _latest_authority_request_for_step(
        self, job_id: str, step_id: str
    ) -> Optional[str]:
        """The request id from the step's latest APPROVAL_REQUESTED event."""
        for _seq, _ev, payload in reversed(self._store.events_for_job(job_id)):
            if (
                _ev.event_type is JobEventType.APPROVAL_REQUESTED
                and _ev.step_id == step_id
                and payload
            ):
                import json

                try:
                    data = json.loads(payload)
                except ValueError:
                    continue
                rid = data.get("authority_request_id", "")
                if rid and rid != "unsinked":
                    return rid
        return None

    def _already_decided(self, request_id: str) -> bool:
        """True if any durable decision exists for the request.

        Duck-typed: any registry exposing the P2-C11 decision-history
        accessor is consulted; a registry without it fails closed (no
        re-decision) rather than guessing.
        """
        accessor = getattr(self._approvals, "decisions_for_request", None)
        if accessor is None:
            return True  # fail closed: cannot prove it is undecided
        return bool(accessor(request_id))
