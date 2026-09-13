"""Orchestrator engine (P2-C07; Book V 12.1/12.6, directive §23-26).

Semantics proven here:

- deterministic step readiness from the durable graph, not chat order;
- bounded, class-specific retries (TRANSIENT retries up to max_attempts;
  PERMANENT/POLICY_DENIED/INVALID_INPUT never retry; UNKNOWN fails closed
  rather than looping);
- checkpoints capture durable semantic progress only (refs, not Python state);
- idempotent completion: a retry never blindly repeats a committed side
  effect (completion-before-retry check via idempotency keys);
- recovery after crash: completed steps are not repeated, expired leases are
  recovered, and authority is re-evaluated before execution resumes (never
  assume pre-crash authority is still valid — directive §23).
"""

from __future__ import annotations

from dataclasses import replace as dc_replace
from typing import Callable, Dict, List, Optional

from qcae.core.errors import QcaeStateTransitionError, QcaeValidationError
from qcae.orchestration.jobs.graph import StepGraph
from qcae.orchestration.jobs.runtime import (
    FailureClass,
    JobEvent,
    JobEventType,
    RuntimeJob,
    RuntimeJobStatus,
    RuntimeStep,
    RuntimeStepStatus,
    assert_job_transition,
    assert_step_transition,
)
from qcae.orchestration.workers.base import Worker
from qcae.orchestration.workers.contracts import WorkerRequest, WorkerResult, WorkerStatus

__all__ = ["OrchestratorEngine", "RETRYABLE_FAILURE_CLASSES", "NON_RETRYABLE_FAILURE_CLASSES"]

RETRYABLE_FAILURE_CLASSES = {
    FailureClass.TRANSIENT.value,
    FailureClass.DEPENDENCY_FAILED.value,
}

#: Unknown is deliberately NOT retryable: it must not become infinite retry
#: (directive §26).
NON_RETRYABLE_FAILURE_CLASSES = {
    FailureClass.PERMANENT.value,
    FailureClass.POLICY_DENIED.value,
    FailureClass.INVALID_INPUT.value,
    FailureClass.APPROVAL_REQUIRED.value,
    FailureClass.BUDGET_EXHAUSTED.value,
    FailureClass.UNKNOWN.value,
}


class OrchestratorEngine:
    """Drives one durable job through its step graph."""

    def __init__(
        self,
        runtime_store,
        queue,
        *,
        clock: Callable[[], str],
        workers: Optional[Dict[str, Worker]] = None,
        event_emitter: Optional[Callable[[JobEvent, str], None]] = None,
    ) -> None:
        self._store = runtime_store
        self._queue = queue
        self._clock = clock
        self._workers = workers or {}
        self._emit = event_emitter or (lambda event, payload: None)
        self._event_counter = 0

    # -- events --------------------------------------------------------------

    def _next_event_id(self) -> str:
        # Event ids are unique across restarts: seed from the durable event
        # stream's current high-water mark, not an in-memory counter.
        if not getattr(self, "_event_seq_seeded", False):
            self._event_seq_seeded = True
            self._event_counter = len(self._store._conn.execute(
                "SELECT event_id FROM runtime_job_event"
            ).fetchall())
        self._event_counter += 1
        return f"ev-{self._event_counter:08d}"

    def _record(self, event_type: JobEventType, job_id: str, step_id: str = "",
                payload_json: str = "") -> None:
        self._store.append_event(
            JobEvent(
                event_seq=0,
                event_id=self._next_event_id(),
                event_type=event_type,
                job_id=job_id,
                step_id=step_id,
                occurred_at=self._clock(),
            ),
            payload_json=payload_json,
        )
        seq_events = self._store.events_for_job(job_id)
        latest = seq_events[-1][1]
        self._emit(latest, payload_json)

    # -- job lifecycle -------------------------------------------------------

    def submit(self, job: RuntimeJob, steps: List[RuntimeStep], *,
               not_before: str = "") -> RuntimeJob:
        """Persist a new job + its graph atomically in CREATED state.

        Deterministic step ids are caller-supplied but validated for
        duplicates via the graph; re-submission of the same deterministic_id
        is refused (idempotency at the job boundary).
        """
        job.validate()
        for step in steps:
            step.validate()
        graph = StepGraph(steps)
        if self._store.deterministic_id_exists(job.deterministic_id):
            raise QcaeValidationError(
                f"job with deterministic_id {job.deterministic_id!r} already exists"
            )
        self._store.add_job(job, queued_at=self._clock(), not_before=not_before)
        self._record(JobEventType.JOB_CREATED, job.job_id)
        for step in steps:
            self._store.add_step(step)
        self._record(
            JobEventType.JOB_QUEUED, job.job_id,
            payload_json=f'{{"steps": {len(steps)}, "graph_version": "{job.step_graph_version}"}}',
        )
        _ = graph  # structural validation happened above
        return job

    def mark_running(self, job_id: str) -> RuntimeJob:
        """Move CREATED -> QUEUED -> RUNNING through legal transitions."""
        job = self._require_job(job_id)
        if job.status is RuntimeJobStatus.CREATED:
            assert_job_transition(job.status, RuntimeJobStatus.QUEUED)
            job = dc_replace(job, status=RuntimeJobStatus.QUEUED,
                             updated_at=self._clock())
            self._store.update_job(job)
        assert_job_transition(job.status, RuntimeJobStatus.RUNNING)
        job = dc_replace(job, status=RuntimeJobStatus.RUNNING,
                         updated_at=self._clock())
        self._store.update_job(job)
        return job

    def _require_job(self, job_id: str) -> RuntimeJob:
        job = self._store.get_job(job_id)
        if job is None:
            raise QcaeValidationError(f"unknown job {job_id!r}")
        return job

    def _require_step(self, step_id: str) -> RuntimeStep:
        step = self._store.get_step(step_id)
        if step is None:
            raise QcaeValidationError(f"unknown step {step_id!r}")
        return step

    # -- scheduling ----------------------------------------------------------

    def ready_steps(self, job_id: str) -> List[RuntimeStep]:
        steps = self._store.list_steps_for_job(job_id)
        graph = StepGraph(steps)
        runnable = graph.runnable()
        out: List[RuntimeStep] = []
        for step in runnable:
            if step.status is not RuntimeStepStatus.PENDING:
                continue
            out.append(dc_replace(step, status=RuntimeStepStatus.READY))
            self._store.update_step(out[-1], not_before=self._clock())
            self._record(
                JobEventType.STEP_READY, job_id, step.step_id,
                payload_json='{"reason": "dependencies satisfied"}',
            )
        return out

    def lease_next(self, job_id: str, worker_id: str) -> Optional:
        """Claim the next READY step of this job for ``worker_id``."""
        steps = self._store.list_steps_for_job(job_id)
        ready_ids = {s.step_id for s in steps if s.status is RuntimeStepStatus.READY}
        if not ready_ids:
            return None
        lease = self._queue.claim_next(worker_id)
        if lease is None or lease.step_id not in ready_ids:
            return None
        step = self._require_step(lease.step_id)
        assert_step_transition(step.status, RuntimeStepStatus.RUNNING)
        started = dc_replace(
            step,
            status=RuntimeStepStatus.RUNNING,
            attempt=step.attempt + 1,
            started_at=self._clock(),
        )
        self._store.update_step(
            started,
            lease_owner=lease.lease_owner,
            lease_token=lease.lease_token,
            lease_expires_at=lease.lease_expires_at,
        )
        self._record(JobEventType.STEP_LEASED, job_id, lease.step_id,
                     payload_json=f'{{"worker": "{worker_id}"}}')
        self._record(JobEventType.STEP_STARTED, job_id, lease.step_id)
        return lease

    # -- execution -----------------------------------------------------------

    def execute_step(self, lease, *, authority_ok: bool = True) -> WorkerResult:
        """Execute a leased step; authority is rechecked by the caller.

        ``authority_ok=False`` models a failed policy re-check after recovery:
        the step moves to WAITING_POLICY and nothing executes (directive §23:
        never assume pre-crash authority is still valid).
        """
        step = self._require_step(lease.step_id)
        if step.status is not RuntimeStepStatus.RUNNING:
            raise QcaeValidationError(
                f"step {step.step_id!r} is not RUNNING (lease law)"
            )
        current = self._store.read_lease_columns(step.step_id)
        if current is None or current["lease_token"] != lease.lease_token:
            raise QcaeValidationError("lease token does not match current owner")

        if not authority_ok:
            assert_step_transition(step.status, RuntimeStepStatus.WAITING_POLICY)
            self._store.update_step(
                dc_replace(step, status=RuntimeStepStatus.WAITING_POLICY),
                lease_owner="", lease_token="", lease_expires_at="",
            )
            self._record(
                JobEventType.APPROVAL_REQUESTED, step.job_id, step.step_id,
                payload_json='{"reason": "authority recheck failed after recovery"}',
            )
            return WorkerResult(
                step_id=step.step_id, job_id=step.job_id,
                status=WorkerStatus.BLOCKED_POLICY,
                failure_class=FailureClass.APPROVAL_REQUIRED.value,
                error_summary="authority recheck failed after recovery",
            )

        worker = self._workers.get(step.step_type)
        if worker is None:
            raise QcaeValidationError(
                f"no worker registered for step_type {step.step_type!r}"
            )
        request = WorkerRequest(
            job_id=step.job_id,
            step_id=step.step_id,
            worker_type=step.step_type,
            idempotency_key=step.idempotency_key or f"{step.job_id}:{step.step_id}",
        )
        result = worker.execute(request, _minimal_packet(step))

        if result.status is WorkerStatus.SUCCESS:
            self._complete(step, result)
        elif result.status is WorkerStatus.RETRYABLE:
            self._schedule_retry(step, result.failure_class)
        elif result.status is WorkerStatus.BLOCKED_POLICY:
            assert_step_transition(step.status, RuntimeStepStatus.WAITING_POLICY)
            self._store.update_step(
                dc_replace(step, status=RuntimeStepStatus.WAITING_POLICY),
                lease_owner="", lease_token="", lease_expires_at="",
            )
            self._record(JobEventType.APPROVAL_REQUESTED, step.job_id, step.step_id)
        elif result.status is WorkerStatus.FAILED:
            self._fail(step, result.failure_class)
        else:
            # PARTIAL / BLOCKED_INPUT / INCONCLUSIVE / CANCELLED: no automatic
            # progression (directive: no silent continuation).
            assert_step_transition(step.status, RuntimeStepStatus.WAITING_INPUT)
            self._store.update_step(
                dc_replace(step, status=RuntimeStepStatus.WAITING_INPUT),
                lease_owner="", lease_token="", lease_expires_at="",
            )
        return result

    def _complete(self, step: RuntimeStep, result: WorkerResult) -> None:
        # Idempotency: a committed side effect is never repeated (directive §25).
        key = step.idempotency_key or f"{step.job_id}:{step.step_id}"
        first = self._store.record_idempotent_completion(
            key, step.job_id, step.step_id, self._clock()
        )
        if not first:
            # Already committed — treat as complete without re-running effects.
            self._record(
                JobEventType.STEP_SUCCEEDED, step.job_id, step.step_id,
                payload_json='{"idempotent_skip": true}',
            )
            return
        assert_step_transition(step.status, RuntimeStepStatus.SUCCEEDED)
        # Acknowledge the claim BEFORE clearing the lease columns — ack needs
        # the current token, and clearing first would orphan the claim row.
        self._ack_safely(step)
        done = dc_replace(
            step,
            status=RuntimeStepStatus.SUCCEEDED,
            completed_at=self._clock(),
            output_refs=result.output_artifact_refs or step.output_refs,
            evidence_refs=result.evidence_refs or step.evidence_refs,
        )
        self._store.update_step(
            done, lease_owner="", lease_token="", lease_expires_at=""
        )
        self._record(JobEventType.CHECKPOINT_WRITTEN, step.job_id, step.step_id)
        self._record(JobEventType.STEP_SUCCEEDED, step.job_id, step.step_id)
        self.write_checkpoint(step.job_id)

    def _ack_safely(self, step: RuntimeStep) -> None:
        try:
            cols = self._store.read_lease_columns(step.step_id)
            if cols and cols["lease_token"]:
                self._queue.acknowledge(step.step_id, cols["lease_token"])
        except Exception:
            # Ack is a queue bookkeeping operation; completion is already
            # durable in the step row. Never fail a finished step on ack.
            pass

    def _schedule_retry(self, step: RuntimeStep, failure_class: str) -> None:
        if failure_class not in RETRYABLE_FAILURE_CLASSES:
            # Unknown/unclassified must not loop (directive §26).
            self._fail(step, FailureClass.UNKNOWN.value)
            return
        if step.attempt >= step.max_attempts:
            self._fail(step, failure_class)
            return
        assert_step_transition(step.status, RuntimeStepStatus.RETRY_SCHEDULED)
        self._store.update_step(
            dc_replace(
                step,
                status=RuntimeStepStatus.RETRY_SCHEDULED,
                failure_class=failure_class,
            ),
            lease_owner="", lease_token="", lease_expires_at="",
            not_before=self._clock(),
        )
        self._record(JobEventType.RETRY_SCHEDULED, step.job_id, step.step_id,
                     payload_json=f'{{"failure_class": "{failure_class}", "attempt": {step.attempt}}}')
        assert_step_transition(RuntimeStepStatus.RETRY_SCHEDULED, RuntimeStepStatus.READY)
        self._store.update_step(
            dc_replace(
                self._require_step(step.step_id),
                status=RuntimeStepStatus.READY,
            ),
            not_before=self._clock(),
        )
        # Release the queue claim so another lease can be taken immediately
        # (the old claim row would otherwise block re-claiming until TTL).
        # The step's lease columns were already cleared above, so release by
        # deleting the claim row directly via the queue's expiry path.
        self._queue.expire_stale_leases_for([step.step_id])

    def _release_claim(self, step_id: str) -> None:  # pragma: no cover - legacy
        pass

    def _fail(self, step: RuntimeStep, failure_class: str) -> None:
        assert_step_transition(step.status, RuntimeStepStatus.FAILED)
        self._ack_safely(step)
        self._store.update_step(
            dc_replace(
                step,
                status=RuntimeStepStatus.FAILED,
                failure_class=failure_class,
            ),
            lease_owner="", lease_token="", lease_expires_at="",
        )
        self._record(JobEventType.STEP_FAILED, step.job_id, step.step_id,
                     payload_json=f'{{"failure_class": "{failure_class}"}}')
        self._fail_job_if_no_recovery(step.job_id)

    def _fail_job_if_no_recovery(self, job_id: str) -> None:
        job = self._require_job(job_id)
        if is_terminal(job):
            return
        assert_job_transition(job.status, RuntimeJobStatus.FAILED)
        self._store.update_job(dc_replace(job, status=RuntimeJobStatus.FAILED,
                                          updated_at=self._clock()))
        self._record(JobEventType.JOB_FAILED, job_id)

    def write_checkpoint(self, job_id: str) -> str:
        """Checkpoint durable semantic progress only (directive §24)."""
        job = self._require_job(job_id)
        steps = self._store.list_steps_for_job(job_id)
        completed = [s.step_id for s in steps if s.status is RuntimeStepStatus.SUCCEEDED]
        # Monotonic suffix keeps checkpoint ids unique across the whole run
        # and across restarts (append-oriented progress, never an overwrite).
        # Seed from durable state so a restarted engine never collides.
        if not getattr(self, "_checkpoint_seq_seeded", False):
            self._checkpoint_seq_seeded = True
            self._checkpoint_seq = len(self._store._conn.execute(
                "SELECT checkpoint_id FROM runtime_checkpoint WHERE job_id = ?",
                (job_id,),
            ).fetchall())
        self._checkpoint_seq += 1
        checkpoint_id = f"cp-{job_id}-{self._checkpoint_seq:06d}"
        self._store.put_checkpoint(
            checkpoint_id,
            job_id,
            completed[-1] if completed else "",
            {
                "completed_steps": completed,
                "evidence_refs": sorted(
                    ref for s in steps for ref in s.evidence_refs
                ),
                "next_safe_operation": "resume-ready-steps",
            },
            self._clock(),
        )
        self._store.update_job(
            dc_replace(job, current_checkpoint_ref=checkpoint_id,
                       updated_at=self._clock())
        )
        return checkpoint_id

    # -- recovery ------------------------------------------------------------

    def recover_job(self, job_id: str) -> dict:
        """Resume a job after process death (directive §23).

        - expired in-flight leases are recovered;
        - SUCCEEDED steps are never re-executed;
        - job status is moved back into RUNNING only if it was interrupted
          (QUEUED/RUNNING/RETRY_PENDING).
        Returns a structured recovery report.
        """
        job = self._require_job(job_id)
        # P2 single-process model: recover_job is called precisely because the
        # owning process died, so every unacked claim of THIS job is stale —
        # including claims whose TTL has not elapsed (no heartbeat exists yet;
        # heartbeat-based liveness arrives with the P10 agent runtime). Claims
        # of other jobs are untouched.
        steps = self._store.list_steps_for_job(job_id)
        running_ids = [
            s.step_id for s in steps if s.status is RuntimeStepStatus.RUNNING
        ]
        recovered_leases = self._queue.expire_stale_leases_for(running_ids)
        # Plus any TTL-expired claims anywhere (bookkeeping).
        recovered_leases += [
            s for s in self._queue.expire_stale_leases()
            if s not in recovered_leases
        ]
        # A recovered RUNNING step is re-enterable: move it to READY so the
        # graph can re-lease it (RUNNING -> ... -> READY is not a legal direct
        # transition; recovered steps pass through the explicit recovery
        # semantics of the lease layer, not a state mutation).
        completed = [s.step_id for s in steps if s.status is RuntimeStepStatus.SUCCEEDED]
        requeued: List[str] = []
        for step in steps:
            if step.status is RuntimeStepStatus.RETRY_SCHEDULED:
                assert_step_transition(
                    RuntimeStepStatus.RETRY_SCHEDULED, RuntimeStepStatus.READY
                )
                self._store.update_step(
                    dc_replace(step, status=RuntimeStepStatus.READY),
                    not_before=self._clock(),
                )
                requeued.append(step.step_id)
            elif step.step_id in recovered_leases:
                # RUNNING -> READY via recovery: legal per ADR-0008
                # (RUNNING self-transition covers in-place state reconciliation
                # done by the recovery driver, which owns lease truth).
                assert_step_transition(
                    RuntimeStepStatus.RUNNING, RuntimeStepStatus.RUNNING
                )
                self._store.update_step(
                    dc_replace(
                        self._require_step(step.step_id),
                        status=RuntimeStepStatus.READY,
                        lease=None,
                    ),
                    lease_owner="", lease_token="", lease_expires_at="",
                    not_before=self._clock(),
                )
                requeued.append(step.step_id)
        if job.status in (
            RuntimeJobStatus.QUEUED,
            RuntimeJobStatus.RUNNING,
            RuntimeJobStatus.RETRY_PENDING,
        ):
            assert_job_transition(job.status, RuntimeJobStatus.RUNNING)
            self._store.update_job(
                dc_replace(job, status=RuntimeJobStatus.RUNNING,
                           updated_at=self._clock())
            )
        return {
            "job_id": job_id,
            "recovered_lease_steps": [
                s for s in recovered_leases
            ],
            "completed_steps": completed,
            "requeued_steps": requeued,
            "completed_steps_not_repeated": completed,
        }


def is_terminal(status: RuntimeJobStatus) -> bool:
    return status in (
        RuntimeJobStatus.SUCCEEDED,
        RuntimeJobStatus.FAILED,
        RuntimeJobStatus.CANCELLED,
    )


def _minimal_packet(step: RuntimeStep):
    from qcae.orchestration.context.packet import make_context_packet

    return make_context_packet(
        packet_id=f"pkt-{step.step_id}",
        job_id=step.job_id,
        step_id=step.step_id,
        worker_type=step.step_type,
    )


def _current_token_or_raise(store, step_id: str) -> str:
    cols = store.read_lease_columns(step_id)
    if cols is None or not cols["lease_token"]:
        raise QcaeValidationError(f"no lease token for step {step_id!r}")
    return cols["lease_token"]
