"""P2-R5-C05 — backup/restore disaster tests for grant truth.

Disaster A: a consumed grant cannot replay after restore.
Disaster B: an unconsumed grant is still eligible exactly once after restore.

The manifest (backup/restore) covers ``runtime_execution`` and
``governance_approval_use`` so grant consumption state survives disaster.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.governance.standalone.approvals import ApprovalDecision, ApprovalState
from qcae.governance.standalone.runtime_service import LocalRuntimeService
from qcae.governance.standalone.step_gate import ApprovalRegistrySink
from qcae.infrastructure.persistence.backup_restore import BackupService, RestoreService
from qcae.infrastructure.persistence.sqlite_approval_registry import (
    APPROVAL_DDL,
    SqliteApprovalRegistry,
)
from qcae.infrastructure.persistence.sqlite_budget_ledger import BUDGET_DDL
from qcae.infrastructure.persistence.sqlite_policy_log import GOVERNANCE_DDL
from qcae.infrastructure.persistence.sqlite_runtime_store import (
    RUNTIME_DDL,
    SqliteRuntimeStore,
)
from qcae.infrastructure.persistence.store_factory import open_metadata_db
from qcae.infrastructure.queue.sqlite_step_queue import (
    QUEUE_INTEGRITY_DDL,
    SqliteStepQueue,
)
from qcae.orchestration.authority_gate import StaticStepAuthorityGate
from qcae.orchestration.jobs.runtime import RuntimeStepStatus
from qcae.orchestration.orchestrator.engine import OrchestratorEngine
from qcae.orchestration.workers.base import DeterministicSuccessWorker
from qcae.tests.unit.test_p2_recovery import _Clock, _job, _step

STEP = "s-1"
JOB = "job-12345678"


def _identities():
    from qcae.governance.standalone.identity import (
        IdentityKind,
        LocalIdentity,
        LocalIdentityProvider,
    )

    ids = LocalIdentityProvider.__new__(LocalIdentityProvider)
    ids._identities = {}
    ids._current = None
    ids.register(LocalIdentity(identity_id="id-operator-1", kind=IdentityKind.OPERATOR))
    ids.register(LocalIdentity(identity_id="id-worker-runtime", kind=IdentityKind.WORKER))
    return ids


def _build_stack(db_path, clock):
    conn = open_metadata_db(db_path)
    for ddl in (RUNTIME_DDL, QUEUE_INTEGRITY_DDL, BUDGET_DDL, GOVERNANCE_DDL,
                APPROVAL_DDL):
        conn.executescript(ddl)
    store = SqliteRuntimeStore(conn)
    queue = SqliteStepQueue(conn, store, now_fn=clock, lease_ttl_seconds=60)
    approvals = SqliteApprovalRegistry(conn)
    engine = OrchestratorEngine(
        store, queue, clock=clock,
        authority_gate=StaticStepAuthorityGate(require_approval=("execute.GENERIC",)),
        authority_request_sink=ApprovalRegistrySink(approvals, clock=clock),
        approval_registry=approvals,
        identity_provider=_identities(),
    )
    engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
    return conn, store, queue, engine, approvals


def _reach_and_grant(engine, store, approvals, service, clock):
    """Drive step to WAITING_POLICY, grant it, release it; return request id."""
    engine.submit(_job(job_id=JOB), [_step(STEP, idempotency_key=f"{JOB}:{STEP}")])
    engine.ready_steps(JOB)
    lease = engine.lease_next(JOB, "id-worker-runtime")
    result = engine.execute_step(lease, worker_id="id-worker-runtime")
    assert result.status.value == "BLOCKED_POLICY"
    assert store.get_step(STEP).status is RuntimeStepStatus.WAITING_POLICY
    rid = engine._resolver.latest_for_step(JOB, STEP)
    service.decide_approval(
        request_id=rid, decision="GRANTED", decided_by="id-operator-1",
        job_id=JOB, reason="ok",
    )
    service.release_granted_step(JOB, STEP)
    return rid


def _admission_verdict(store):
    gate = StaticStepAuthorityGate(require_approval=("execute.GENERIC",))
    return gate.evaluate_step_authority(
        store.get_step(STEP), store.get_job(JOB), worker_id="id-worker-runtime")


def _backup_restore(db_path, backup_dir):
    """Backup live DB, destroy it, restore; return restored connection."""
    conn = open_metadata_db(db_path)
    manifest = BackupService(conn).backup(backup_dir)
    conn.close()
    db_path.unlink()
    restored = db_path.parent / "restored.sqlite3"
    RestoreService().restore(backup_dir, restored, db_path.parent / "artifacts")
    return open_metadata_db(restored)


class TestDisasterA_ConsumedGrantCannotReplay:
    def test_consumed_grant_cannot_replay_after_restore(self, tmp_path):
        db = tmp_path / "a.sqlite3"
        backup_dir = tmp_path / "backup"
        clock = _Clock()
        conn, store, queue, engine, approvals = _build_stack(db, clock)
        service = LocalRuntimeService(
            runtime_store=store, queue=queue, engine=engine,
            identity_provider=_identities(), policy_provider=None,
            approval_registry=approvals, clock=clock, schema_version=5,
            policy_version="t", storage_location=str(db),
        )
        rid = _reach_and_grant(engine, store, approvals, service, clock)
        # Consume the grant BEFORE the disaster.
        assert engine._grant_admits(verdict=_admission_verdict(store))
        conn.commit()
        conn.close()

        # Disaster: destroy + restore.
        rconn = _backup_restore(db, backup_dir)
        rstore = SqliteRuntimeStore(rconn)
        approvals2 = SqliteApprovalRegistry(rconn)
        # Consumption state survived: exactly one use row, replay refused.
        decision = approvals2.decisions_for_request(rid)[-1]
        assert len(approvals2.uses_for_decision(decision.decision_id)) == 1
        assert not approvals2.consume_grant(
            use_id="use-replay", decision_ref=decision.decision_id,
            step_id=STEP, used_at=clock(),
        )
        rconn.close()


class TestDisasterB_UnconsumedGrantEligibleOnce:
    def test_unconsumed_grant_eligible_once_after_restore(self, tmp_path):
        db = tmp_path / "b.sqlite3"
        backup_dir = tmp_path / "backup"
        clock = _Clock()
        conn, store, queue, engine, approvals = _build_stack(db, clock)
        service = LocalRuntimeService(
            runtime_store=store, queue=queue, engine=engine,
            identity_provider=_identities(), policy_provider=None,
            approval_registry=approvals, clock=clock, schema_version=5,
            policy_version="t", storage_location=str(db),
        )
        rid = _reach_and_grant(engine, store, approvals, service, clock)
        # Grant NOT consumed before the disaster.
        conn.commit()
        conn.close()

        # Disaster: destroy + restore.
        rconn = _backup_restore(db, backup_dir)
        rstore = SqliteRuntimeStore(rconn)
        approvals2 = SqliteApprovalRegistry(rconn)
        # Grant still eligible exactly once post-restore.
        decision = approvals2.decisions_for_request(rid)[-1]
        assert len(approvals2.uses_for_decision(decision.decision_id)) == 0
        assert approvals2.consume_grant(
            use_id="use-1", decision_ref=decision.decision_id,
            step_id=STEP, used_at=clock(),
        )
        assert not approvals2.consume_grant(
            use_id="use-2", decision_ref=decision.decision_id,
            step_id=STEP, used_at=clock(),
        )
        rconn.close()
