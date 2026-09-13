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

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from qcae.core.errors import QcaeValidationError
from qcae.core.jobs import deterministic_job_id
from qcae.governance.standalone.approvals import ApprovalState
from qcae.governance.standalone.identity import LocalIdentityProvider
from qcae.orchestration.jobs.graph import StepGraph
from qcae.orchestration.jobs.runtime import (
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
            registered_workers=tuple(sorted(self._engine._workers)),
            storage_location=self._storage_location,
        )

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

    def execute_step(self, lease, *, authority_ok: bool = True):
        return self._engine.execute_step(lease, authority_ok=authority_ok)

    def resume(self, job_id: str) -> dict:
        """Recover a job after interruption (directive §23)."""
        return self._engine.recover_job(job_id)

    def recover_expired_leases(self) -> List[str]:
        return self._queue.expire_stale_leases()

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
        self._store.append_event(
            JobEvent(
                event_seq=0,
                event_id=self._engine._next_event_id(),
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
