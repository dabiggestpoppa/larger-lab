"""P2-R3-C04 — principal identity binding (operator-loop finding E).

Execution authority requires BOTH a proven identity and a policy grant:
an unregistered ``id-*`` string gains nothing from policy matching, a
worker cannot claim under A and execute under B, and identity semantics
survive restart through the durable store.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.core.jobs import deterministic_job_id
from qcae.governance.standalone.identity import (
    IdentityKind,
    LocalIdentity,
    LocalIdentityProvider,
)
from qcae.infrastructure.persistence.sqlite_runtime_store import (
    RUNTIME_DDL,
    SqliteRuntimeStore,
)
from qcae.infrastructure.persistence.store_factory import open_metadata_db
from qcae.infrastructure.queue.sqlite_step_queue import (
    QUEUE_INTEGRITY_DDL,
    SqliteStepQueue,
)
from qcae.orchestration.authority_gate import PermissiveStepAuthorityGate
from qcae.orchestration.jobs.runtime import RuntimeJob, RuntimeStep, RuntimeStepStatus
from qcae.orchestration.orchestrator.engine import OrchestratorEngine
from qcae.orchestration.workers.base import DeterministicSuccessWorker
from qcae.orchestration.workers.contracts import WorkerStatus

NOW = "2026-09-17T12:00:00Z"
JOB = "job-identity"


class _Clock:
    def __init__(self):
        self._t = datetime(2026, 9, 17, 12, 0, 0, tzinfo=timezone.utc)

    def __call__(self) -> str:
        return self._t.strftime("%Y-%m-%dT%H:%M:%SZ")

    def advance(self, seconds: int) -> None:
        self._t += timedelta(seconds=seconds)


def _job(job_id=JOB, **over):
    base = dict(
        job_id=job_id,
        deterministic_id=deterministic_job_id("discovery", "cap-id", "k-id"),
        job_type="DISCOVERY",
        subject_ref="cap-id",
        created_by="operator",
        created_at=NOW,
    )
    base.update(over)
    return RuntimeJob(**base)


def _step(step_id, job_id=JOB, **over):
    base = dict(
        step_id=step_id,
        job_id=job_id,
        step_type="GENERIC",
        dependencies=(),
        created_at=NOW,
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
    identity = LocalIdentityProvider()
    # Registered worker principal: id-worker-a executes; id-worker-b exists
    # but is refused by policy in the policy-matrix tests below.
    for wid, name in (("id-worker-a", "worker a"), ("id-worker-b", "worker b")):
        identity.register(LocalIdentity(identity_id=wid, kind=IdentityKind.WORKER,
                                        display_name=name))
    engine = OrchestratorEngine(
        store, queue, clock=clock, authority_gate=PermissiveStepAuthorityGate(),
        identity_provider=identity,
    )
    engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
    return store, queue, engine, clock, conn, identity


class TestClaimIdentity:
    def test_registered_worker_may_claim(self, env):
        store, queue, engine, clock, conn, identity = env
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps(JOB)
        lease = engine.lease_next(JOB, "id-worker-a")
        assert lease is not None
        assert lease.lease_owner == "id-worker-a"

    def test_unregistered_id_star_principal_refused_before_claim(self, env):
        store, queue, engine, clock, conn, identity = env
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps(JOB)
        # id-unknown matches the default policy's principal_match="id-*"
        # string — identity binding refuses it anyway.
        for attacker in ("id-unknown", "id-attacker", "arbitrary-id-x"):
            with pytest.raises(QcaeValidationError, match="unknown identity"):
                engine.lease_next(JOB, attacker)
        assert not queue.has_active_claim("s-1")
        assert store.get_step("s-1").status is RuntimeStepStatus.READY

    def test_no_claim_row_created_for_unknown_principal(self, env):
        store, queue, engine, clock, conn, identity = env
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps(JOB)
        with pytest.raises(QcaeValidationError):
            engine.lease_next(JOB, "id-attacker")
        rows = conn.execute(
            "SELECT COUNT(*) FROM runtime_queue_claim"
        ).fetchone()[0]
        assert rows == 0


class TestExecutionIdentity:
    def test_claim_and_execute_identity_must_match(self, env):
        store, queue, engine, clock, conn, identity = env
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps(JOB)
        lease = engine.lease_next(JOB, "id-worker-a")
        with pytest.raises(QcaeValidationError, match="lease"):
            engine.execute_step(lease, worker_id="id-worker-b")
        # Worker b is registered, so the failure is identity binding, not
        # registration: the swap is refused before any worker runs.

    def test_execute_as_unknown_principal_refused(self, env):
        store, queue, engine, clock, conn, identity = env
        engine.submit(_job(), [_step("s-1")])
        engine.ready_steps(JOB)
        lease = engine.lease_next(JOB, "id-worker-a")
        # Attacker holds the lease object but is not the durable owner.
        with pytest.raises(QcaeValidationError, match="lease"):
            engine.execute_step(lease, worker_id="id-attacker")


class TestRestartIdentity:
    def test_identity_semantics_survive_restart(self, env):
        store, queue, engine, clock, conn, identity = env
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "id.sqlite3"
            c1 = open_metadata_db(db)
            c1.executescript(RUNTIME_DDL)
            c1.executescript(QUEUE_INTEGRITY_DDL)
            store1 = SqliteRuntimeStore(c1)
            queue1 = SqliteStepQueue(c1, store1, now_fn=clock, lease_ttl_seconds=60)
            ident1 = LocalIdentityProvider()
            ident1.register(LocalIdentity(identity_id="id-worker-a",
                                          kind=IdentityKind.WORKER,
                                          display_name="worker a"))
            engine1 = OrchestratorEngine(
                store1, queue1, clock=clock,
                authority_gate=PermissiveStepAuthorityGate(),
                identity_provider=ident1,
            )
            engine1.register_worker_type("GENERIC", DeterministicSuccessWorker())
            engine1.submit(_job(), [_step("s-1")])
            engine1.ready_steps(JOB)
            lease = engine1.lease_next(JOB, "id-worker-a")
            c1.commit()
            c1.close()

            # Restart: durable state replays; identity is re-proven per call.
            c2 = open_metadata_db(db)
            c2.executescript(RUNTIME_DDL)
            c2.executescript(QUEUE_INTEGRITY_DDL)
            store2 = SqliteRuntimeStore(c2)
            queue2 = SqliteStepQueue(c2, store2, now_fn=clock, lease_ttl_seconds=60)
            ident2 = LocalIdentityProvider()
            ident2.register(LocalIdentity(identity_id="id-worker-a",
                                          kind=IdentityKind.WORKER,
                                          display_name="worker a"))
            engine2 = OrchestratorEngine(
                store2, queue2, clock=clock,
                authority_gate=PermissiveStepAuthorityGate(),
                identity_provider=ident2,
            )
            engine2.register_worker_type("GENERIC", DeterministicSuccessWorker())
            # Durable lease survives; the same proven principal executes.
            result = engine2.execute_step(lease, worker_id="id-worker-a")
            assert result.status is WorkerStatus.SUCCESS
            assert store2.get_step("s-1").status is RuntimeStepStatus.SUCCEEDED
            c2.close()
