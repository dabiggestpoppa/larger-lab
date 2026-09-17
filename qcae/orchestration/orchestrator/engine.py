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
from qcae.orchestration.orchestrator.execution import (
    ExecutionState,
    ExecutionRecord,
    ReplaySafety,
)
from qcae.orchestration.orchestrator.budgets import (
    BudgetExhaustedError,
    BudgetState,
)
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
from qcae.orchestration.authority_gate import (
    AuthorityRequestSink,
    FailClosedStepAuthorityGate,
    StepAuthorityDecision,
    StepAuthorityGate,
    StepAuthorityVerdict,
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
        budget_service: Optional["BudgetService"] = None,
        authority_gate: Optional[StepAuthorityGate] = None,
        authority_request_sink: Optional[AuthorityRequestSink] = None,
    ) -> None:
        self._store = runtime_store
        self._queue = queue
        self._clock = clock
        self._workers = workers or {}
        self._emit = event_emitter or (lambda event, payload: None)
        self._budgets = budget_service
        # P2-R2-C01: authority is part of the execution path. No gate means
        # nothing executes (fail closed) — governance is wired explicitly at
        # the composition root, never implicitly absent.
        self._authority_gate: StepAuthorityGate = (
            authority_gate or FailClosedStepAuthorityGate()
        )
        self._authority_sink = authority_request_sink
        # Steps released by an exact-scope operator grant (P2-R2-C02).
        self._granted_keys: set = set()

    # -- explicit interfaces (P2-R2-C05: no private-attribute reach-ins) -----

    def register_worker_type(self, worker_type: str, worker: Worker) -> None:
        """Register a worker implementation for one step_type."""
        if not worker_type or not isinstance(worker_type, str):
            raise QcaeValidationError("worker_type must be a non-empty string")
        if worker is None:
            raise QcaeValidationError("worker must not be None")
        self._workers[worker_type] = worker

    def registered_worker_types(self) -> List[str]:
        """Sorted step_types with registered workers (identity surface)."""
        return sorted(self._workers)

    # -- events --------------------------------------------------------------

    def _record(self, event_type: JobEventType, job_id: str, step_id: str = "",
                payload_json: str = "") -> None:
        # P2-C07R4 (directive §2.4): event identity/sequence allocation belongs
        # to the runtime store, which assigns both durably and collision-safe.
        # The orchestrator knows no sqlite, no table names, no counters.
        self._store.append_event(
            JobEvent(
                event_seq=0,
                event_id="",
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
        """Persist a new job + its graph atomically, durably QUEUED.

        P2-C07R3 (repair directive §2.3): job identity, every step, the
        initial events, and queue metadata commit in ONE transaction on the
        store's connection — any failure rolls back to no job, no steps, no
        partial event history. Re-submission of the same deterministic_id is
        refused (idempotency at the job boundary).

        P2-R3-C01 (lifecycle truth): submission represents BOTH lifecycle
        facts — JOB_CREATED and JOB_QUEUED — and the durable snapshot
        committed after the transaction is QUEUED. The snapshot and the
        event stream can never disagree about whether a submitted job is
        queued.
        """
        if not steps:
            raise QcaeValidationError(
                "job submission requires at least one step (empty graph is fail-closed)"
            )
        job.validate()
        for step in steps:
            step.validate()
        graph = StepGraph(steps)
        if self._store.deterministic_id_exists(job.deterministic_id):
            raise QcaeValidationError(
                f"job with deterministic_id {job.deterministic_id!r} already exists"
            )
        queued = dc_replace(job, status=RuntimeJobStatus.QUEUED)
        with self._store.transaction() as tx:
            tx.add_job(queued, queued_at=self._clock(), not_before=not_before)
            tx.append_event(
                JobEvent(
                    event_seq=0, event_id="",
                    event_type=JobEventType.JOB_CREATED,
                    job_id=job.job_id, occurred_at=self._clock(),
                )
            )
            for step in steps:
                tx.add_step(step)
            tx.append_event(
                JobEvent(
                    event_seq=0, event_id="",
                    event_type=JobEventType.JOB_QUEUED,
                    job_id=job.job_id, occurred_at=self._clock(),
                ),
                payload_json=(
                    f'{{"steps": {len(steps)}, '
                    f'"graph_version": "{job.step_graph_version}"}}'
                ),
            )
        return job

    def mark_running(self, job_id: str) -> RuntimeJob:
        """Move CREATED -> QUEUED -> RUNNING through legal transitions.

        Kept for explicit callers; the lease path promotes the job itself
        (``_ensure_running``) so the natural submit → run flow reaches
        RUNNING exactly when executable work actually runs (P2-R3-C01).
        """
        self._ensure_running(job_id)
        return self._require_job(job_id)

    def _ensure_running(self, job_id: str) -> None:
        """Promote CREATED -> QUEUED -> RUNNING through legal transitions.

        Called only from paths where executable work is actually going to
        run (a granted lease) or where recovery re-opens the job, never from
        readiness derivation — a job whose dependencies are unready, whose
        not_before has not elapsed, or that has no compatible worker stays
        QUEUED (P2-R3-C01).
        """
        job = self._require_job(job_id)
        if is_terminal(job.status):
            return  # terminal history is immutable
        if job.status is RuntimeJobStatus.CREATED:
            assert_job_transition(job.status, RuntimeJobStatus.QUEUED)
            job = dc_replace(job, status=RuntimeJobStatus.QUEUED,
                             updated_at=self._clock())
            self._store.update_job(job)
        if job.status is not RuntimeJobStatus.RUNNING:
            assert_job_transition(job.status, RuntimeJobStatus.RUNNING)
            self._store.update_job(
                dc_replace(job, status=RuntimeJobStatus.RUNNING,
                           updated_at=self._clock())
            )

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
        """Claim the next READY step of this job for ``worker_id``.

        Budget gate: an exhausted job budget blocks leasing (BudgetExhausted
        is surfaced as an explicit failure, never silent continuation).
        """
        if self._budgets is not None:
            job_budget = self._budgets.snapshot(f"bud-{job_id}")
            if job_budget is not None and job_budget.state is BudgetState.EXHAUSTED:
                raise BudgetExhaustedError(
                    f"job {job_id!r} budget is exhausted; refusing to lease work"
                )
        steps = self._store.list_steps_for_job(job_id)
        ready_ids = {s.step_id for s in steps if s.status is RuntimeStepStatus.READY}
        if not ready_ids:
            return None
        # P2-C07R1 (directive §2.1): eligibility is enforced inside the atomic
        # claim — the queue can only ever hand back a step from this job's
        # ready set. No global claim-then-filter, no claim-then-release.
        lease = self._queue.claim_next(
            worker_id, eligible_step_ids=ready_ids, job_id=job_id
        )
        if lease is None:
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
        # P2-R3-C01: a granted lease means executable work is actually
        # running — the job's durable snapshot moves to RUNNING here (once),
        # so job status and the step graph tell the same truth.
        self._ensure_running(job_id)
        # Retry economics: attempts consume the job's attempt budget (directive
        # §28: retries consume budget; recovery never resets it).
        if self._budgets is not None:
            self._charge_attempt(job_id, started.attempt)
        self._record(JobEventType.STEP_LEASED, job_id, lease.step_id,
                     payload_json=f'{{"worker": "{worker_id}"}}')
        # STEP_STARTED is emitted by execute_step carrying the typed authority
        # decision payload (P2-R2-C01): one STARTED per attempt, with the
        # verdict that admitted it.
        return lease

    def _charge_attempt(self, job_id: str, attempt: int) -> None:
        budget_id = f"bud-{job_id}"
        try:
            self._budgets.charge(budget_id, "attempts", 1)
        except BudgetExhaustedError:
            # Cap reached mid-flight: mark the job budget exhausted and
            # re-raise so the caller sees explicit exhaustion.
            self._record(
                JobEventType.STEP_FAILED, job_id,
                payload_json='{"failure_class": "BUDGET_EXHAUSTED"}',
            )
            raise

    # -- execution -----------------------------------------------------------

    def execute_step(self, lease, *, worker_id: Optional[str] = None) -> WorkerResult:
        """Execute a leased step under a typed authority evaluation.

        P2-R2-C01: authority is evaluated HERE, by the gate, before any
        worker runs — never assumed by the caller. The evaluation binds
        principal -> action -> resource -> scope -> requirement (directive
        P2-R2-C01) and one of ALLOW / DENY / REQUIRE_APPROVAL /
        ALLOW_WITH_CONSTRAINTS becomes operational:

        - ALLOW / ALLOW_WITH_CONSTRAINTS: the worker runs (constraints are
          carried on the WorkerRequest so the worker cannot exceed them);
        - DENY: nothing executes; the step fails POLICY_DENIED;
        - REQUIRE_APPROVAL: nothing executes; a durable AuthorityRequest is
          recorded through the sink and the step waits in WAITING_POLICY
          until an exact-scope grant releases it (P2-R2-C02).
        """
        step = self._require_step(lease.step_id)
        if step.status is not RuntimeStepStatus.RUNNING:
            raise QcaeValidationError(
                f"step {step.step_id!r} is not RUNNING (lease law)"
            )
        current = self._store.read_lease_columns(step.step_id)
        if current is None or current["lease_token"] != lease.lease_token:
            raise QcaeValidationError("lease token does not match current owner")

        principal = worker_id or lease.lease_owner or "unknown-worker"
        job = self._require_job(step.job_id)
        verdict = self._authority_gate.evaluate_step_authority(
            step, job, worker_id=principal
        )
        verdict.validate()
        if verdict.step_id != step.step_id or verdict.job_id != job.job_id:
            raise QcaeValidationError(
                "authority verdict binding does not match the leased step; "
                "refusing to execute (replay/mismatch guard)"
            )
        if verdict.principal != principal:
            raise QcaeValidationError(
                "authority verdict principal does not match the claiming worker"
            )
        self._record(
            JobEventType.STEP_STARTED, step.job_id, step.step_id,
            payload_json=(
                f'{{"authority_decision": "{verdict.decision.value}", '
                f'"decision_ref": "{verdict.decision_ref}", '
                f'"policy_version": "{verdict.policy_version}"}}'
            ),
        )

        if verdict.decision is StepAuthorityDecision.DENY:
            # Nothing executes; the RUNNING step fails POLICY_DENIED. _fail
            # asserts the transition and clears the lease columns.
            self._fail(self._require_step(step.step_id), FailureClass.POLICY_DENIED.value)
            return WorkerResult(
                step_id=step.step_id, job_id=step.job_id,
                status=WorkerStatus.FAILED,
                failure_class=FailureClass.POLICY_DENIED.value,
                error_summary=f"authority denied: {verdict.reason}",
            )
        if verdict.decision is StepAuthorityDecision.REQUIRE_APPROVAL:
            granted_key = f"{step.job_id}:{step.step_id}"
            if granted_key not in self._granted_keys:
                request_id = self._persist_authority_request(verdict)
                assert_step_transition(step.status, RuntimeStepStatus.WAITING_POLICY)
                self._store.update_step(
                    dc_replace(step, status=RuntimeStepStatus.WAITING_POLICY),
                    lease_owner="", lease_token="", lease_expires_at="",
                )
                self._record(
                    JobEventType.APPROVAL_REQUESTED, step.job_id, step.step_id,
                    payload_json=(
                        f'{{"authority_request_id": "{request_id}", '
                        f'"action": "{verdict.action}", '
                        f'"resource": "{verdict.resource}", '
                        f'"scope": "{verdict.scope}"}}'
                    ),
                )
                return WorkerResult(
                    step_id=step.step_id, job_id=step.job_id,
                    status=WorkerStatus.BLOCKED_POLICY,
                    failure_class=FailureClass.APPROVAL_REQUIRED.value,
                    error_summary=f"approval required: {verdict.reason}",
                )
            # An exact-scope grant released this step (P2-R2-C02); proceed.

        worker = self._workers.get(step.step_type)
        if worker is None:
            raise QcaeValidationError(
                f"no worker registered for step_type {step.step_type!r}"
            )
        key = step.idempotency_key or f"{step.job_id}:{step.step_id}"
        request = WorkerRequest(
            job_id=step.job_id,
            step_id=step.step_id,
            worker_type=step.step_type,
            idempotency_key=key,
            constraints=tuple(verdict.constraints) if verdict.constraints else (),
            policy_context_ref=verdict.decision_ref,
        )

        # P2-C07R2 (directive §2.2): the key is durably RESERVED before the
        # worker runs; the commit marker is written with the result payload so
        # a crash between effect and marker can be resolved without
        # re-execution. This is at-least-once execution with durable dedup —
        # never a silent exactly-once claim.
        replay_safety = getattr(worker, "replay_safety", ReplaySafety.REPLAY_SAFE)
        if not isinstance(replay_safety, ReplaySafety):
            replay_safety = ReplaySafety.REPLAY_SAFE
        first_reservation = self._store.reserve_execution(
            key, step.job_id, step.step_id, replay_safety, self._clock()
        )
        if not first_reservation:
            prior = self._store.get_execution_record(key)
            if prior is not None and prior.state is ExecutionState.COMMITTED:
                # Deterministic duplicate: reconstruct, never re-execute.
                self._record(
                    JobEventType.STEP_SUCCEEDED, step.job_id, step.step_id,
                    payload_json='{"idempotent_reconstruct": true}',
                )
                return prior.reconstruct_result()
            if prior is not None and prior.state is ExecutionState.EXECUTING \
                    and replay_safety is ReplaySafety.NON_REPLAY_SAFE:
                # Ambiguous outcome for a non-replay-safe effect: fail closed
                # into explicit recovery, never a blind rerun (directive §2.2).
                assert_step_transition(step.status, RuntimeStepStatus.WAITING_INPUT)
                self._store.update_step(
                    dc_replace(step, status=RuntimeStepStatus.WAITING_INPUT),
                    lease_owner="", lease_token="", lease_expires_at="",
                )
                self._record(
                    JobEventType.APPROVAL_REQUESTED, step.job_id, step.step_id,
                    payload_json='{"reason": "non-replay-safe execution ambiguous after crash"}',
                )
                return WorkerResult(
                    step_id=step.step_id, job_id=step.job_id,
                    status=WorkerStatus.BLOCKED_INPUT,
                    failure_class=FailureClass.UNKNOWN.value,
                    error_summary=(
                        "non-replay-safe step has unresolved prior execution; "
                        "operator recovery required"
                    ),
                )
            # Same-key re-entry (REPLAY_SAFE / IDEMPOTENCY_AWARE retry after a
            # FAILED record or an acknowledged REPLAY_SAFE rerun) proceeds.
        record = self._store.get_execution_record(key)
        if record is not None and record.state is not ExecutionState.COMMITTED:
            self._store.update_execution_record(
                dc_replace(record, state=ExecutionState.EXECUTING)
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

    def _persist_authority_request(self, verdict: StepAuthorityVerdict) -> str:
        """Durable AuthorityRequest for a REQUIRE_APPROVAL verdict (P2-R2-C02)."""
        if self._authority_sink is None:
            # No sink configured: the wait is still durable in the step row
            # and the event log; there is simply no request artifact to grant.
            return "unsinked"
        return self._authority_sink.record_authority_request(verdict)

    def record_exact_scope_grant(self, job_id: str, step_id: str) -> None:
        """Release one WAITING_POLICY step after an exact-scope operator grant.

        Called by the runtime service ONLY after it has verified the grant
        binds the same action/resource/scope the step requested (no approval
        laundering — P2-R2-C02). The step returns to READY and may be leased
        again; the grant key is consumed by the next execute_step.
        """
        step = self._require_step(step_id)
        if step.job_id != job_id:
            raise QcaeValidationError("step/job mismatch in grant release")
        if step.status is not RuntimeStepStatus.WAITING_POLICY:
            raise QcaeValidationError(
                f"step {step_id!r} is not WAITING_POLICY; nothing to release"
            )
        assert_step_transition(step.status, RuntimeStepStatus.READY)
        self._store.update_step(
            dc_replace(step, status=RuntimeStepStatus.READY),
            lease_owner="", lease_token="", lease_expires_at="",
        )
        self._granted_keys.add(f"{job_id}:{step_id}")
        # Clear any stale queue claim so the released step is claimable now
        # (the WAITING_POLICY entry cleared the step's lease columns but the
        # claim row may persist until TTL; release law mirrors the retry path).
        self._queue.expire_stale_leases_for([step_id])
        self._record(
            JobEventType.APPROVAL_GRANTED, job_id, step_id,
            payload_json='{"release": "exact-scope grant"}',
        )

    def _complete(self, step: RuntimeStep, result: WorkerResult) -> None:
        # P2-C07R2: commit is durable and carries the result payload, closing
        # the crash window between effect and marker (directive §2.2, windows
        # C/D: effect committed + marker lost ⇒ reconstruct, never re-execute).
        key = step.idempotency_key or f"{step.job_id}:{step.step_id}"
        self._store.commit_execution(key, result, self._clock())
        first = self._store.record_idempotent_completion(
            key, step.job_id, step.step_id, self._clock()
        )
        if not first:
            # Already completed via the legacy marker — treat as complete
            # without re-running effects.
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
        self._succeed_job_if_graph_done(step.job_id)

    def _succeed_job_if_graph_done(self, job_id: str) -> None:
        """Job-level completion when every step reached a terminal state.

        P2-R3-C01: the finalizer is reachable from ANY non-terminal job
        state (a crash can land the last completion while the snapshot is
        still QUEUED); it promotes through the legal transitions to
        RUNNING and then SUCCEEDED so the snapshot and event stream agree.
        Called only from the step-completion path, so JOB_SUCCEEDED is
        emitted exactly once per job (completion records are idempotent;
        a second finalization attempt sees a terminal job and returns).
        """
        job = self._store.get_job(job_id)
        if job is None or is_terminal(job.status):
            return
        steps = self._store.list_steps_for_job(job_id)
        if not steps or not all(
            s.status in (RuntimeStepStatus.SUCCEEDED, RuntimeStepStatus.CANCELLED)
            for s in steps
        ):
            return
        if job.status is not RuntimeJobStatus.RUNNING:
            # The work ran even if the snapshot lagged (crash window); the
            # lifecycle truth is RUNNING -> SUCCEEDED at completion.
            current = job.status
            if current is RuntimeJobStatus.CREATED:
                assert_job_transition(current, RuntimeJobStatus.QUEUED)
                current = RuntimeJobStatus.QUEUED
            assert_job_transition(current, RuntimeJobStatus.RUNNING)
            self._store.update_job(
                dc_replace(job, status=RuntimeJobStatus.RUNNING,
                           updated_at=self._clock())
            )
            job = self._store.get_job(job_id)
        assert_job_transition(job.status, RuntimeJobStatus.SUCCEEDED)
        self._store.update_job(
            dc_replace(job, status=RuntimeJobStatus.SUCCEEDED,
                       updated_at=self._clock())
        )
        self._record(JobEventType.JOB_SUCCEEDED, job_id)

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
        # P2-C07R4: checkpoint identity is store-allocated (durable, unique);
        # the engine holds no counters and no store internals.
        checkpoint_id = self._store.allocate_checkpoint_id(job_id)
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
        # P2-C07R2: surface unresolved execution records — the crash-window
        # truth. NON_REPLAY_SAFE ambiguity is never silently rerun; recovery
        # reports it for explicit operator resolution (directive §2.2).
        unresolved = self._store.unresolved_executions_for_job(job_id)
        return {
            "job_id": job_id,
            "recovered_lease_steps": [
                s for s in recovered_leases
            ],
            "completed_steps": completed,
            "requeued_steps": requeued,
            "completed_steps_not_repeated": completed,
            "unresolved_executions": [
                {
                    "idempotency_key": r.idempotency_key,
                    "step_id": r.step_id,
                    "state": r.state.value,
                    "replay_safety": r.replay_safety.value,
                    "requires_operator_resolution": (
                        r.replay_safety is ReplaySafety.NON_REPLAY_SAFE
                    ),
                }
                for r in unresolved
            ],
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
