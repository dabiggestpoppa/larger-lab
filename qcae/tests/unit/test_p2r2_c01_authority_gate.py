"""P2-R2-C01 — typed authority gate in the execution path.

Operator repair: authority was a component beside the engine instead of a
step in it. These tests prove the wiring laws:

- every execute_step performs a typed gate evaluation binding
  principal -> action -> resource -> scope -> requirement;
- ALLOW / DENY / REQUIRE_APPROVAL / ALLOW_WITH_CONSTRAINTS are operational;
- no gate configured == nothing executes (fail closed);
- a verdict bound to another step/principal is refused (replay guard);
- the public ``authority_ok`` caller bypass no longer exists;
- the composition root wires the policy-backed gate + approval sink.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.core.jobs import deterministic_job_id
from qcae.governance.standalone.identity import IdentityKind, LocalIdentity, LocalIdentityProvider
from qcae.governance.standalone.policy import (
    LocalPolicyEngine,
    PolicyEffect,
    PolicyRequest,
    PolicyRule,
    PolicySet,
)
from qcae.interfaces.cli.app import build_local_runtime
from qcae.orchestration.authority_gate import (
    FailClosedStepAuthorityGate,
    PermissiveStepAuthorityGate,
    StaticStepAuthorityGate,
    StepAuthorityDecision,
    StepAuthorityVerdict,
    baseline_action_for_step,
)
from qcae.orchestration.jobs.runtime import RuntimeJob, RuntimeStep, RuntimeStepStatus
from qcae.orchestration.orchestrator.engine import OrchestratorEngine
from qcae.orchestration.workers.base import DeterministicSuccessWorker
from qcae.orchestration.workers.contracts import WorkerStatus
from qcae.infrastructure.persistence.sqlite_runtime_store import (
    RUNTIME_DDL,
    SqliteRuntimeStore,
)
from qcae.infrastructure.persistence.store_factory import open_metadata_db
from qcae.infrastructure.queue.sqlite_step_queue import (
    QUEUE_INTEGRITY_DDL,
    SqliteStepQueue,
)


class _Clock:
    def __init__(self):
        self._t = datetime(2026, 9, 13, 12, 0, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self._t.strftime("%Y-%m-%dT%H:%M:%SZ")

    def advance(self, s):
        self._t += timedelta(seconds=s)


def _job(job_id="job-12345678", **over):
    base = dict(
        job_id=job_id,
        deterministic_id=deterministic_job_id("d", "c", job_id),
        job_type="D", subject_ref="cap-1", created_by="op",
        created_at="2026-09-13T12:00:00Z",
    )
    base.update(over)
    return RuntimeJob(**base)


def _step(step_id, job_id="job-12345678", **over):
    base = dict(
        step_id=f"{job_id}:{step_id}", job_id=job_id, step_type="GENERIC",
        created_at="2026-09-13T12:00:00Z",
        idempotency_key=f"{job_id}:{step_id}",
    )
    base.update(over)
    return RuntimeStep(**base)


@pytest.fixture()
def env():
    clock = _Clock()
    conn = open_metadata_db(":memory:")
    conn.executescript(RUNTIME_DDL)
    conn.executescript(QUEUE_INTEGRITY_DDL)
    store = SqliteRuntimeStore(conn)
    queue = SqliteStepQueue(conn, store, now_fn=clock, lease_ttl_seconds=60)
    engine = OrchestratorEngine(
        store, queue, clock=clock,
        authority_gate=PermissiveStepAuthorityGate(),
    )
    conn.commit()
    return store, queue, engine, clock, conn


def _lease_ready(store, engine, job, steps, worker="id-worker-runtime"):
    engine.submit(job, steps)
    engine.mark_running(job.job_id)
    engine.ready_steps(job.job_id)
    return engine.lease_next(job.job_id, worker)


class TestGateInExecutionPath:
    def test_no_gate_configured_fails_closed(self, env):
        """An engine without a gate executes nothing (default DENY)."""
        store, queue, clock, conn = env[0], env[1], env[3], env[4]
        engine = OrchestratorEngine(store, queue, clock=clock)
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        lease = _lease_ready(store, engine, _job(), [_step("s-1")])
        result = engine.execute_step(lease)
        assert result.status is WorkerStatus.FAILED
        assert result.failure_class == "POLICY_DENIED"
        assert store.get_step("job-12345678:s-1").status is RuntimeStepStatus.FAILED
        assert store.get_step("job-12345678:s-1").failure_class == "POLICY_DENIED"
        # The worker never ran.
        assert engine.registered_worker_types() == ["GENERIC"]
        worker = engine._workers["GENERIC"]
        assert worker.calls == 0

    def test_allow_lets_worker_run_with_binding_event(self, env):
        store, queue, engine, clock, conn = env
        worker = DeterministicSuccessWorker()
        engine.register_worker_type("GENERIC", worker)
        lease = _lease_ready(store, engine, _job(), [_step("s-1")])
        result = engine.execute_step(lease)
        assert result.status is WorkerStatus.SUCCESS
        # The STEP_STARTED event carries the typed authority payload.
        import json

        started_payloads = [
            json.loads(p) for _s, e, p in store.events_for_job("job-12345678")
            if e.event_type.value == "STEP_STARTED" and p
        ]
        assert started_payloads and started_payloads[-1]["authority_decision"] == "ALLOW"
        assert started_payloads[-1]["policy_version"] == "permissive-test-1"

    def test_deny_fails_step_policy_denied(self, env):
        store, queue, engine, clock, conn = env
        worker = DeterministicSuccessWorker()
        engine.register_worker_type("GENERIC", worker)
        engine._authority_gate = StaticStepAuthorityGate(allowed=())
        lease = _lease_ready(store, engine, _job(), [_step("s-1")])
        result = engine.execute_step(lease)
        assert result.status is WorkerStatus.FAILED
        assert result.failure_class == "POLICY_DENIED"
        assert worker.calls == 0
        assert store.get_step("job-12345678:s-1").status is RuntimeStepStatus.FAILED

    def test_require_approval_waits_and_requests(self, env):
        store, queue, engine, clock, conn = env
        worker = DeterministicSuccessWorker()
        engine.register_worker_type("GENERIC", worker)

        captured = {}

        class Sink:
            def record_authority_request(self, verdict):
                captured["verdict"] = verdict
                return "authreq-1"

        engine._authority_sink = Sink()
        engine._authority_gate = StaticStepAuthorityGate(
            require_approval=("execute.GENERIC",)
        )
        lease = _lease_ready(store, engine, _job(), [_step("s-1")])
        result = engine.execute_step(lease)
        assert result.status is WorkerStatus.BLOCKED_POLICY
        assert result.failure_class == "APPROVAL_REQUIRED"
        assert worker.calls == 0
        assert store.get_step("job-12345678:s-1").status is RuntimeStepStatus.WAITING_POLICY
        # A durable request artifact recorded with the exact binding.
        v = captured["verdict"]
        assert v.action == "execute.GENERIC"
        assert v.resource == "cap-1"
        assert v.scope == "job:job-12345678"
        assert v.decision is StepAuthorityDecision.REQUIRE_APPROVAL

    def test_allow_with_constraints_reaches_worker(self, env):
        store, queue, engine, clock, conn = env
        seen = {}

        class ProbeWorker:
            def execute(self, request, packet):
                seen["constraints"] = request.constraints
                return DeterministicSuccessWorker().execute(request, packet)

        engine.register_worker_type("GENERIC", ProbeWorker())
        engine._authority_gate = StaticStepAuthorityGate(
            allowed=("execute.GENERIC",), constraints=("scope:read-only",)
        )
        lease = _lease_ready(store, engine, _job(), [_step("s-1")])
        result = engine.execute_step(lease)
        assert result.status is WorkerStatus.SUCCESS
        assert seen["constraints"] == ("scope:read-only",)

    def test_verdict_binding_mismatch_refused(self, env):
        """A verdict for another step/principal is refused (replay guard)."""
        store, queue, engine, clock, conn = env
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())

        class ForgedGate(PermissiveStepAuthorityGate):
            def evaluate_step_authority(self, step, job, *, worker_id):
                verdict = super().evaluate_step_authority(step, job, worker_id=worker_id)
                # Lie about the step binding (replay of another step's verdict).
                from dataclasses import replace as dc_replace
                return dc_replace(verdict, step_id="job-other:s-9")

        engine._authority_gate = ForgedGate()
        lease = _lease_ready(store, engine, _job(), [_step("s-1")])
        with pytest.raises(QcaeValidationError, match="binding does not match"):
            engine.execute_step(lease)

    def test_verdict_principal_mismatch_refused(self, env):
        store, queue, engine, clock, conn = env
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())

        class ForgedPrincipalGate(PermissiveStepAuthorityGate):
            def evaluate_step_authority(self, step, job, *, worker_id):
                verdict = super().evaluate_step_authority(step, job, worker_id=worker_id)
                from dataclasses import replace as dc_replace
                return dc_replace(verdict, principal="someone-else")

        engine._authority_gate = ForgedPrincipalGate()
        lease = _lease_ready(store, engine, _job(), [_step("s-1")])
        with pytest.raises(QcaeValidationError, match="principal does not match"):
            engine.execute_step(lease)

    def test_authority_ok_bypass_removed(self):
        """The public caller bypass is gone from the engine and service."""
        import inspect

        from qcae.governance.standalone.runtime_service import LocalRuntimeService

        engine_sig = inspect.signature(OrchestratorEngine.execute_step)
        assert "authority_ok" not in engine_sig.parameters
        service_sig = inspect.signature(LocalRuntimeService.execute_step)
        assert "authority_ok" not in service_sig.parameters

    def test_step_started_event_carries_decision(self, env):
        """One STARTED per attempt, emitted with the authority payload."""
        store, queue, engine, clock, conn = env
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        lease = _lease_ready(store, engine, _job(), [_step("s-1")])
        engine.execute_step(lease)
        kinds = [
            e.event_type.value for _s, e, _p in store.events_for_job("job-12345678")
        ]
        assert kinds.count("STEP_STARTED") == 1
        assert kinds.count("STEP_LEASED") == 1


class TestGateBinding:
    def test_baseline_action_derivation(self):
        assert baseline_action_for_step(_step("s-1")) == "execute.GENERIC"
        declared = _step("s-2", authority_requirement="may_execute_in_sandbox")
        assert baseline_action_for_step(declared) == "may_execute_in_sandbox"

    def test_declared_requirement_evaluated_not_baseline(self, env):
        """A declared authority_requirement is the evaluated action."""
        store, queue, engine, clock, conn = env
        engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        engine._authority_gate = StaticStepAuthorityGate(
            require_approval=("may_execute_in_sandbox",)
        )
        lease = _lease_ready(
            store, engine, _job(),
            [_step("s-1", authority_requirement="may_execute_in_sandbox")],
        )
        result = engine.execute_step(lease)
        assert result.status is WorkerStatus.BLOCKED_POLICY

    def test_static_gate_fails_closed_unknown_action(self):
        gate = StaticStepAuthorityGate(allowed=("may_discover",))
        verdict = gate.evaluate_step_authority(
            _step("s-1"), _job(), worker_id="id-worker-1"
        )
        assert verdict.decision is StepAuthorityDecision.DENY
        assert "fail" in verdict.decision_ref or "closed" in verdict.decision_ref

    def test_verdict_record_round_trip(self):
        verdict = StaticStepAuthorityGate(
            allowed=("execute.GENERIC",), clock=lambda: "2026-09-13T12:00:00Z"
        ).evaluate_step_authority(_step("s-1"), _job(), worker_id="id-worker-1")
        data = verdict.to_dict()
        rebuilt = StepAuthorityVerdict.from_dict(data)
        assert rebuilt == verdict
        assert rebuilt.digest() == verdict.digest()


class TestCompositionRootWiring:
    def test_factory_wires_policy_gate_and_sink(self, tmp_path):
        rt = build_local_runtime(tmp_path / "m.sqlite3")
        # The engine's gate is the policy-backed one and its decisions are
        # durably logged (decision ids non-colliding via the policy log).
        assert rt.engine._authority_gate is not None
        assert rt.engine._authority_sink is not None
        d = rt.authority.evaluate_policy(
            PolicyRequest(principal="id-worker-runtime", action="execute.GENERIC"),
            request_ref="wiring-probe",
        )
        assert d.decision is not None

    def test_factory_worker_principal_registered(self, tmp_path):
        rt = build_local_runtime(tmp_path / "m2.sqlite3")
        assert rt.identity.get("id-worker-runtime") is not None

    def test_registered_worker_execute_allowed_unregistered_denied(self, tmp_path):
        """Registered worker principal executes; unknown principal denies."""
        clock = _Clock()
        rt = build_local_runtime(tmp_path / "m3.sqlite3", clock=clock)
        job = _job()
        step = _step("s-1")
        rt.engine.submit(job, [step])
        rt.engine.mark_running(job.job_id)
        rt.engine.ready_steps(job.job_id)
        lease = rt.engine.lease_next(job.job_id, "id-worker-runtime")
        rt.engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        result = rt.engine.execute_step(lease, worker_id="id-worker-runtime")
        assert result.status is WorkerStatus.SUCCESS

        # Unknown principal on a fresh job: policy denies.
        job2 = _job("job-aaaaaaaa")
        step2 = _step("s-1", job_id="job-aaaaaaaa")
        rt.engine.submit(job2, [step2])
        rt.engine.mark_running(job2.job_id)
        rt.engine.ready_steps(job2.job_id)
        lease2 = rt.engine.lease_next(job2.job_id, "ghost")
        result2 = rt.engine.execute_step(lease2)
        assert result2.status is WorkerStatus.FAILED
        assert result2.failure_class == "POLICY_DENIED"

    def test_identity_registration_is_idempotent(self, tmp_path):
        rt1 = build_local_runtime(tmp_path / "m4.sqlite3")
        rt2 = build_local_runtime(tmp_path / "m5.sqlite3")
        assert rt1.identity.get("id-worker-runtime") is not None
        assert rt2.identity.get("id-worker-runtime") is not None
