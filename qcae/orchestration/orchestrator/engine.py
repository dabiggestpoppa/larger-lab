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

import secrets
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
from qcae.governance.standalone.approvals import GrantUse
from qcae.orchestration.authority_gate import (
    AuthorityRequestSink,
    FailClosedStepAuthorityGate,
    StepAuthorityDecision,
    StepAuthorityGate,
    StepAuthorityVerdict,
)
from qcae.orchestration.orchestrator.worker_availability import WorkerUnavailableError
from qcae.orchestration.workers.base import Worker
from qcae.orchestration.workers.contracts import WorkerRequest, WorkerResult, WorkerStatus

__all__ = [
    "OrchestratorEngine",
    "RETRYABLE_FAILURE_CLASSES",
    "NON_RETRYABLE_FAILURE_CLASSES",
    "WorkerUnavailableError",
]

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
        identity_provider=None,
        approval_registry=None,
    ) -> None:
        self._store = runtime_store
        self._queue = queue
        self._clock = clock
        self._workers = workers or {}
        self._emit = event_emitter or (lambda event, payload: None)
        self._budgets = budget_service
        # P2-R3-C04 (finding E): identity provenance for lease/execute. The
        # provider is duck-typed (a ``require(identity_id)`` method) so the
        # orchestrator does not import governance; the composition root
        # wires the real provider. Unknown principals fail closed BEFORE
        # any claim or state mutation — string matching is not identity.
        self._identity = identity_provider
        # P2-R2-C01: authority is part of the execution path. No gate means
        # nothing executes (fail closed) — governance is wired explicitly at
        # the composition root, never implicitly absent.
        self._authority_gate: StepAuthorityGate = (
            authority_gate or FailClosedStepAuthorityGate()
        )
        self._authority_sink = authority_request_sink
        # P2-R4-C03 (finding G): approval authority is a DURABLE grant
        # consumed atomically at admission — never process-memory state.
        # The registry is duck-typed (effective_grant / mark_grant_used) so
        # the orchestrator does not import infrastructure; the composition
        # root wires the real one.
        self._approvals = approval_registry

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
        # Return the committed truth (QUEUED), not the caller's pre-submit
        # object — the snapshot and every reported view must agree (P2-R3-C01).
        return self._store.get_job(job.job_id) if self._store.get_job(job.job_id) is not None else queued

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

    # -- identity ------------------------------------------------------------

    def require_worker_identity(self, worker_id: str) -> None:
        """Prove ``worker_id`` exists in the identity provider (P2-R3-C04).

        Called before lease creation and before execution. With no provider
        wired (bare engine in legacy composition), identity binding still
        holds through the lease-owner/principal equality check in
        ``execute_step`` — the provider is defense in depth, not the only
        gate.
        """
        if self._identity is not None:
            self._identity.require(worker_id)

    def eligible_steps_for_claim(self, job_id: str) -> List[RuntimeStep]:
        """READY steps of one job a lease could currently grant.

        Readiness derivation (``ready_steps``) is the caller's first move;
        this is the authoritative "what could actually be leased now" view:
        READY, not_before elapsed, and no active claim. Public so worker
        availability and the CLI can classify the surface without touching
        lease state (P2-R3-C02).
        """
        now = self._clock()
        out: List[RuntimeStep] = []
        for step in self._store.list_steps_for_job(job_id):
            if step.status is not RuntimeStepStatus.READY:
                continue
            if step.not_before and step.not_before > now:
                continue
            if self._queue.has_active_claim(step.step_id):
                continue
            out.append(step)
        return out

    def lease_next(self, job_id: str, worker_id: str) -> Optional:
        """Claim the next READY step of this job for ``worker_id``.

        Budget gate: an exhausted job budget blocks leasing (BudgetExhausted
        is surfaced as an explicit failure, never silent continuation).
        Identity gate (P2-R3-C04): an unregistered principal fails closed
        BEFORE any claim row exists — policy string-matching never confers
        execution authority on an unknown identity.
        """
        self.require_worker_identity(worker_id)
        if self._budgets is not None:
            job_budget = self._budgets.snapshot(f"bud-{job_id}")
            if job_budget is not None and job_budget.state is BudgetState.EXHAUSTED:
                raise BudgetExhaustedError(
                    f"job {job_id!r} budget is exhausted; refusing to lease work"
                )
        steps = self._store.list_steps_for_job(job_id)
        ready = [s for s in steps if s.status is RuntimeStepStatus.READY]
        if not ready:
            return None
        # P2-R3-C02 (operator-loop finding B): worker availability is known
        # BEFORE any ownership or state mutation. Leasing without a
        # compatible worker would strand the step RUNNING; instead the step
        # stays READY and the caller gets a typed outcome. Coverage is
        # per-step: covered work proceeds while uncovered steps wait READY.
        covered_ids = {
            s.step_id for s in ready if s.step_type in self._workers
        }
        if not covered_ids:
            missing = sorted({s.step_type for s in ready})
            raise WorkerUnavailableError(
                f"no registered worker for step type(s) {missing}; "
                f"nothing leased, step remains READY"
            )
        # P2-C07R1 (directive §2.1): eligibility is enforced inside the atomic
        # claim — the queue can only ever hand back a step from this job's
        # ready set. No global claim-then-filter, no claim-then-release.
        lease = self._queue.claim_next(
            worker_id, eligible_step_ids=covered_ids, job_id=job_id
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
        # P2-R4-C01 (crash window A): lease + RUNNING + attempt + budget
        # charge are durable BEFORE any execution is attempted. A process
        # death here leaves exactly that truth; recovery (P2-R3-C03 law)
        # reconciles the expired lease without repeating committed work.
        self._store.flush()
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
        # P2-R3-C04: claim principal == execution principal. A worker cannot
        # claim under A and execute under B; the durable lease owner is the
        # provenance of authority for this attempt.
        current_owner_check = self._store.read_lease_columns(step.step_id)
        if current_owner_check is not None and current_owner_check["lease_owner"] \
                and principal != current_owner_check["lease_owner"]:
            raise QcaeValidationError(
                f"execution principal {principal!r} does not match the lease "
                f"owner {current_owner_check['lease_owner']!r}; identity binding "
                "refuses the swap"
            )
        self.require_worker_identity(principal)
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
            self._store.flush()
            return WorkerResult(
                step_id=step.step_id, job_id=step.job_id,
                status=WorkerStatus.FAILED,
                failure_class=FailureClass.POLICY_DENIED.value,
                error_summary=f"authority denied: {verdict.reason}",
            )
        if verdict.decision is StepAuthorityDecision.REQUIRE_APPROVAL:
            if not self._grant_admits(job_id=step.job_id, step_id=step.step_id,
                                      principal=principal):
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
                self._store.flush()
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
                self._store.flush()
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
                self._store.flush()
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

        # P2-R4-C01 PRE-EFFECT DURABLE COMMIT (directive §3, crash windows
        # B/C): the idempotency reservation, EXECUTING execution state, and
        # every admission write (lease, RUNNING, attempt, authority verdict
        # event) are committed HERE — the write transaction is closed before
        # the worker performs external work. No DB write transaction spans
        # worker.execute(); a process death mid-effect leaves the durable
        # EXECUTING truth from which recovery classifies the outcome.
        self._store.flush()

        result = worker.execute(request, _minimal_packet(step))

        # P2-R4-C01 POST-EFFECT DURABLE COMMIT (crash windows D-I): result,
        # COMMITTED execution record, step finalization, outputs/evidence,
        # checkpoint, and job finalization are written and flushed as one
        # semantic group before this method returns.
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
        self._store.flush()
        return result

    def _persist_authority_request(self, verdict: StepAuthorityVerdict) -> str:
        """Durable AuthorityRequest for a REQUIRE_APPROVAL verdict (P2-R2-C02)."""
        if self._authority_sink is None:
            # No sink configured: the wait is still durable in the step row
            # and the event log; there is simply no request artifact to grant.
            return "unsinked"
        return self._authority_sink.record_authority_request(verdict)

    def _latest_authority_request_for_step(
        self, job_id: str, step_id: str
    ) -> Optional[str]:
        """The request id from the step's latest APPROVAL_REQUESTED event.

        Same truth the runtime service verifies grants against (P2-R2-C02);
        the engine reads it so grant admission consumes the RIGHT durable
        request, never a memory-cached key.
        """
        import json

        for _seq, _ev, payload in reversed(self._store.events_for_job(job_id)):
            if (
                _ev.event_type is JobEventType.APPROVAL_REQUESTED
                and _ev.step_id == step_id
                and payload
            ):
                try:
                    data = json.loads(payload)
                except ValueError:
                    continue
                rid = data.get("authority_request_id", "")
                if rid and rid != "unsinked":
                    return rid
        return None

    def record_exact_scope_grant(self, job_id: str, step_id: str) -> None:
        """Release one WAITING_POLICY step after an exact-scope operator grant.

        Called by the runtime service ONLY after it has verified the durable
        grant binds the same action/resource/scope the step requested (no
        approval laundering — P2-R2-C02). P2-R4-C03 (finding G): the grant
        itself stays in the durable approval registry — this method records
        NO execution-side authority; the single-use consumption happens
        atomically inside ``_grant_admits`` when the admitted attempt begins.
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
        # Clear any stale queue claim so the released step is claimable now
        # (the WAITING_POLICY entry cleared the step's lease columns but the
        # claim row may persist until TTL; release law mirrors the retry path).
        self._queue.expire_stale_leases_for([step_id])
        self._record(
            JobEventType.APPROVAL_GRANTED, job_id, step_id,
            payload_json='{"release": "exact-scope grant"}',
        )
        self._store.flush()

    # -- P2-R4-C03: durable single-use grant admission -----------------------

    def _grant_admits(self, *, job_id: str, step_id: str, principal: str) -> bool:
        """Whether a durable grant admits this execution — consuming it if so.

        Law (directive §6/§7, finding G): authority comes from the durable
        approval registry, verified against the step's own recorded request
        and consumed atomically (single execution admission). With no
        registry wired the answer is NO — fail closed; grants cannot live
        in process memory.

        Consumption semantics: exactly one use row per grant decision.
        The first admitted attempt consumes it; a second attempt under the
        same grant is refused (a retry that still requires approval performs
        a new authority evaluation and needs a new grant).
        """
        if self._approvals is None:
            return False
        # The durable request this step raised (recorded by the sink).
        request_id = self._latest_authority_request_for_step(job_id, step_id)
        if not request_id:
            return False
        try:
            request = self._approvals.get_request(request_id)
        except QcaeValidationError:
            return False
        if request is None:
            return False
        try:
            grant = self._approvals.effective_grant(request_id, now=self._clock())
        except QcaeValidationError:
            return False
        if grant is None:
            # No GRANTED decision, or the approval window has expired.
            return False
        if request.principal != principal:
            # The grant admits the principal who requested it — never a
            # different execution identity (identity binding law).
            return False
        # Single-use consumption, atomically: the INSERT wins for exactly
        # one caller; concurrent/replayed admissions read it as consumed.
        use = GrantUse(
            use_id=f"use-{secrets.token_hex(8)}",
            decision_ref=grant.decision_id,
            step_id=step_id,
            used_at=self._clock(),
        )
        return self._approvals.mark_grant_used(use)

    def _complete(self, step: RuntimeStep, result: WorkerResult) -> None:
        # P2-C07R2: commit is durable and carries the result payload, closing
        # the crash window between effect and marker (directive §2.2, windows
        # C/D: effect committed + marker lost ⇒ reconstruct, never re-execute).
        key = step.idempotency_key or f"{step.job_id}:{step.step_id}"
        self._store.commit_execution(key, result, self._clock())
        self._store.record_idempotent_completion(
            key, step.job_id, step.step_id, self._clock()
        )
        # P2-R4-C02 (directive §11): the completion marker is supporting
        # evidence, never canonical state — a False return (marker already
        # present because the process died between marker and step-state
        # finalization) must NOT skip canonical reconstruction. The transition
        # assertion below is state-based: an already-SUCCEEDED step is a
        # no-op replay, a RUNNING/READY step is repaired to SUCCEEDED here.
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

    def recover_leased_steps(self, expired_step_ids) -> List[str]:
        """Reconcile steps whose leases TTL-expired (P2-R3-C03, finding C).

        ONE authoritative law: an expired-lease step returns to READY with
        its lease columns cleared, unless its execution record says the
        effect COMMITTED (then the step is finalized SUCCEEDED — committed
        work is never re-run) or the effect is NON_REPLAY_SAFE-ambiguous
        (then the step waits in WAITING_INPUT for explicit operator
        resolution — never a blind replay). Active (unexpired) leases are
        never touched by this method.
        """
        reconciled: List[str] = []
        for step_id in expired_step_ids:
            step = self._store.get_step(step_id)
            if step is None or step.status is not RuntimeStepStatus.RUNNING:
                continue
            key = step.idempotency_key or f"{step.job_id}:{step.step_id}"
            record = self._store.get_execution_record(key)
            if record is not None and record.state is ExecutionState.COMMITTED:
                result = record.reconstruct_result()
                self._complete(self._require_step(step_id), result)
                reconciled.append(step_id)
                continue
            if (
                record is not None
                and record.state is ExecutionState.EXECUTING
                and record.replay_safety is ReplaySafety.NON_REPLAY_SAFE
            ):
                assert_step_transition(step.status, RuntimeStepStatus.WAITING_INPUT)
                self._store.update_step(
                    dc_replace(step, status=RuntimeStepStatus.WAITING_INPUT),
                    lease_owner="", lease_token="", lease_expires_at="",
                )
                self._record(
                    JobEventType.APPROVAL_REQUESTED, step.job_id, step.step_id,
                    payload_json='{"reason": "expired lease with ambiguous '
                                 'non-replay-safe execution; operator recovery required"}',
                )
                reconciled.append(step_id)
                continue
            assert_step_transition(step.status, RuntimeStepStatus.RUNNING)
            self._store.update_step(
                dc_replace(
                    self._require_step(step_id),
                    status=RuntimeStepStatus.READY,
                    lease=None,
                ),
                lease_owner="", lease_token="", lease_expires_at="",
                not_before=self._clock(),
            )
            self._record(
                JobEventType.STEP_READY, step.job_id, step.step_id,
                payload_json='{"reason": "expired lease reconciled by recovery"}',
            )
            reconciled.append(step_id)
        return reconciled

    def recover_orphan_steps(self, job_id: str) -> dict:
        """Classify RUNNING steps with no queue claim (P2-R3-C03, case C).

        An orphan (RUNNING with no claim row) is never silently ignored: it
        is recovered through the same execution-record truth as expired
        leases, or held in WAITING_INPUT for explicit operator resolution.
        """
        steps = self._store.list_steps_for_job(job_id)
        orphans = [
            s for s in steps
            if s.status is RuntimeStepStatus.RUNNING
            and not self._queue.has_active_claim(s.step_id)
        ]
        recovered = self.recover_leased_steps([s.step_id for s in orphans])
        return {
            "job_id": job_id,
            "orphan_steps": [s.step_id for s in orphans],
            "reconciled": recovered,
        }

    def recover_job(self, job_id: str) -> dict:
        """Resume a job after process death (directive §23).

        P2-R3-C03: this is a DELEGATE to the single recovery law —
        ``recover_leased_steps`` owns expired-lease reconciliation (READY,
        COMMITTED finalization, or WAITING_INPUT escalation), so job-level
        recovery and the global surface can never disagree.

        - expired in-flight leases are recovered; active leases untouched;
        - SUCCEEDED steps are never re-executed;
        - job status is moved back into RUNNING only if it was interrupted
          (QUEUED/RUNNING/RETRY_PENDING).
        Returns a structured recovery report.
        """
        job = self._require_job(job_id)
        steps = self._store.list_steps_for_job(job_id)
        # P2-R3-C03/§6 (finding D): recovery NEVER steals an active lease.
        # Only claims whose TTL has actually elapsed are released — scoped
        # to THIS job — and only those steps are reconciled. Active leases
        # survive recover_job untouched.
        recovered_leases = self.recover_leased_steps(
            self._queue.expire_stale_leases(job_id=job_id)
        )
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
        # P2-R4-C02 (directive §10, finding H.A, refresh-after-reconcile law):
        # reconciliation above (recover_leased_steps → _complete) may have
        # finalized the last step and the job itself. The snapshot loaded at
        # entry is now stale — writing it back would regress terminal truth.
        # RELOAD and only apply the recovery transition to a non-terminal job.
        steps = self._store.list_steps_for_job(job_id)  # reload for truth
        completed = sorted({*completed, *(s.step_id for s in steps if s.status is RuntimeStepStatus.SUCCEEDED)})
        # P2-R4-C02 (directive §10, finding H.A, refresh-after-reconcile law):
        # reconciliation above (recover_leased_steps → _complete) may have
        # finalized the last step and the job itself. The snapshot loaded at
        # entry is now stale — writing it back would regress terminal truth.
        # RELOAD and only apply the recovery transition to a non-terminal job.
        job = self._store.get_job(job_id)  # reload after reconciliation
        if job is None:
            raise QcaeValidationError(f"job {job_id!r} vanished during recovery")
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
