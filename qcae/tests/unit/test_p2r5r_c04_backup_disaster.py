"""P2-R5R-C04 — backup/restore carries the expanded durable authority truth.

The backup manifest must include the post-v4 durable authority tables
(``runtime_execution``, ``governance_approval_use``) and the full approval
binding, so a disaster restore cannot resurrect a consumed grant or lose a
COMMITTED execution.

Journeys (each destroys the source and restores from the backup):

A. matching grant -> consume -> COMMITTED execution -> backup -> destroy ->
   restore: consumption stays consumed, execution stays COMMITTED, and the
   step cannot be re-executed.
B. unconsumed matching grant -> backup -> destroy -> restore: the current
   binding still matches and the grant is usable EXACTLY once.
C. legacy/incomplete grant -> backup -> restore: it survives as historical
   evidence and cannot authorize a strengthened R5R execution.
"""

from __future__ import annotations

import json

import pytest

from qcae.governance.standalone.approvals import (
    ApprovalDecision,
    ApprovalRequest,
    ApprovalState,
)
from qcae.governance.standalone.identity import (
    IdentityKind,
    LocalIdentity,
    LocalIdentityProvider,
)
from qcae.governance.standalone.runtime_service import LocalRuntimeService
from qcae.governance.standalone.step_gate import ApprovalRegistrySink
from qcae.infrastructure.persistence.backup_restore import (
    BACKUP_MANIFEST_NAME,
    BackupService,
    RestoreService,
)
from qcae.infrastructure.persistence.sqlite_approval_registry import (
    BACKUP_AUTHORITY_TABLES,
    SqliteApprovalRegistry,
)
from qcae.infrastructure.persistence.store_factory import open_metadata_db
from qcae.infrastructure.queue.sqlite_step_queue import SqliteStepQueue
from qcae.orchestration.authority_gate import StaticStepAuthorityGate
from qcae.orchestration.jobs.runtime import RuntimeStepStatus
from qcae.orchestration.orchestrator.engine import OrchestratorEngine
from qcae.orchestration.orchestrator.execution import ExecutionState
from qcae.orchestration.workers.base import DeterministicSuccessWorker
from qcae.tests.unit.test_p2_recovery import _Clock, _job, _step

STEP = "s-1"
JOB = "job-12345678"
PRINCIPAL = "id-worker-runtime"
KEY = f"{JOB}:{STEP}"


def _identities() -> LocalIdentityProvider:
    ids = LocalIdentityProvider.__new__(LocalIdentityProvider)
    ids._identities = {}
    ids._current = None
    ids.register(LocalIdentity(identity_id="id-operator-1",
                               kind=IdentityKind.OPERATOR))
    ids.register(LocalIdentity(identity_id=PRINCIPAL, kind=IdentityKind.WORKER))
    return ids


class Rig:
    """One wired runtime over a real DB file."""

    def __init__(self, db_path, clock=None):
        from qcae.infrastructure.persistence.sqlite_runtime_store import (
            SqliteRuntimeStore,
        )

        self.clock = clock or _Clock()
        self.path = db_path
        self.conn = open_metadata_db(db_path)
        self.stack = SqliteRuntimeStore(self.conn)
        self.approvals = SqliteApprovalRegistry(self.conn)
        self.queue = SqliteStepQueue(self.conn, self.stack, now_fn=self.clock,
                                     lease_ttl_seconds=60)
        self.gate = StaticStepAuthorityGate(require_approval=("execute.GENERIC",))
        self.engine = OrchestratorEngine(
            self.stack, self.queue, clock=self.clock, authority_gate=self.gate,
            authority_request_sink=ApprovalRegistrySink(self.approvals,
                                                        clock=self.clock),
            approval_registry=self.approvals,
        )
        self.engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        self.service = LocalRuntimeService(
            runtime_store=self.stack, queue=self.queue, engine=self.engine,
            identity_provider=_identities(), policy_provider=None,
            approval_registry=self.approvals, clock=self.clock,
            schema_version=5, policy_version="static-1",
            storage_location=str(db_path),
        )

    # -- lifecycle ------------------------------------------------------

    def reach_waiting_policy(self):
        self.engine.submit(_job(job_id=JOB),
                           [_step(STEP, idempotency_key=KEY)])
        self.engine.ready_steps(JOB)
        lease = self.engine.lease_next(JOB, PRINCIPAL)
        result = self.engine.execute_step(lease, worker_id=PRINCIPAL)
        assert result.status.value == "BLOCKED_POLICY"
        rid = self.engine._resolver.latest_for_step(JOB, STEP)
        assert rid
        return rid

    def grant(self, rid):
        self.service.decide_approval(
            request_id=rid, decision="GRANTED", decided_by="id-operator-1",
            job_id=JOB, reason="ok",
        )
        self.service.release_granted_step(JOB, STEP)
        return self.approvals.decisions_for_request(rid)[-1]

    def run_step(self):
        """Drive the released step to a terminal record via the real engine."""
        self.engine.ready_steps(JOB)
        lease = self.engine.lease_next(JOB, PRINCIPAL)
        assert lease is not None, "released step should be claimable"
        return self.engine.execute_step(lease, worker_id=PRINCIPAL)

    def live_verdict(self):
        return self.gate.evaluate_step_authority(
            self.stack.get_step(STEP), self.stack.get_job(JOB),
            worker_id=PRINCIPAL)

    def commit(self) -> None:
        self.stack.flush()
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()


@pytest.fixture()
def rig_factory(tmp_path):
    made = []

    def make(name="disaster.sqlite3"):
        rig = Rig(tmp_path / name)
        made.append(rig)
        return rig

    yield make
    for rig in made:
        try:
            rig.conn.close()
        except Exception:
            pass


def _backup_and_destroy(rig, tmp_path, backup_name="backup"):
    """Snapshot, then destroy the source DB (the disaster)."""
    rig.commit()
    backup_dir = tmp_path / backup_name
    manifest = BackupService(rig.conn, None).backup(backup_dir)
    rig.close()
    rig.path.unlink()
    return backup_dir, manifest


def _restore(tmp_path, backup_dir, name="restored.sqlite3"):
    restored_db = tmp_path / "restored" / name
    RestoreService().restore(backup_dir, restored_db, tmp_path / "restored-art")
    return Rig(restored_db, clock=_Clock())


class TestManifestCoversDurableAuthority:
    def test_manifest_includes_execution_and_grant_use(self, rig_factory,
                                                       tmp_path) -> None:
        rig = rig_factory()
        rid = rig.reach_waiting_policy()
        rig.grant(rid)
        rig.run_step()
        rig.commit()
        backup_dir = tmp_path / "b"
        manifest = BackupService(rig.conn, None).backup(backup_dir)
        rows = manifest["registry_rows"]
        assert "runtime_execution" in rows
        assert "governance_approval_use" in rows
        assert rows["runtime_execution"] >= 1
        assert rows["governance_approval_use"] == 1
        written = json.loads((backup_dir / BACKUP_MANIFEST_NAME).read_text())
        assert written["registry_rows"]["governance_approval_use"] == 1

    def test_backup_authority_table_list_is_the_persisted_truth(self) -> None:
        # The registry exports the table list it owns so the manifest cannot
        # silently drop one again.
        assert set(BACKUP_AUTHORITY_TABLES) == {
            "runtime_execution", "governance_approval_use",
            "governance_approval_request", "governance_approval_decision",
        }


class TestJourneyAConsumedStaysConsumed:
    def test_consumed_grant_and_committed_execution_survive_disaster(
        self, rig_factory, tmp_path
    ) -> None:
        rig = rig_factory()
        rid = rig.reach_waiting_policy()
        decision = rig.grant(rid)
        result = rig.run_step()
        assert result.status.value == "SUCCESS"
        execution = rig.stack.get_execution_record(KEY)
        assert execution is not None and execution.state is ExecutionState.COMMITTED
        uses_before = rig.approvals.uses_for_decision(decision.decision_id)
        assert len(uses_before) == 1

        backup_dir, manifest = _backup_and_destroy(rig, tmp_path)
        restored = _restore(tmp_path, backup_dir)
        try:
            # Consumption survives.
            uses_after = restored.approvals.uses_for_decision(decision.decision_id)
            assert len(uses_after) == 1
            assert uses_after[0].step_id == STEP
            # Execution stays COMMITTED across the disaster.
            execution2 = restored.stack.get_execution_record(KEY)
            assert execution2 is not None
            assert execution2.state is ExecutionState.COMMITTED
            # And it cannot be replayed: the idempotency key stays reserved,
            # the grant stays consumed, and no new admission is possible.
            assert restored.stack.reserve_execution(
                KEY, JOB, STEP, execution2.replay_safety, restored.clock()
            ) is False
            assert not restored.engine._grant_admits(
                verdict=restored.live_verdict())
            assert len(restored.approvals.uses_for_decision(
                decision.decision_id)) == 1
        finally:
            restored.close()


class TestJourneyBUnconsumedGrantUsableOnce:
    def test_unconsumed_grant_survives_and_is_usable_exactly_once(
        self, rig_factory, tmp_path
    ) -> None:
        rig = rig_factory()
        rid = rig.reach_waiting_policy()
        decision = rig.grant(rid)
        # Released but NOT yet admitted: nothing consumed.
        assert rig.approvals.uses_for_decision(decision.decision_id) == []

        backup_dir, _ = _backup_and_destroy(rig, tmp_path)
        restored = _restore(tmp_path, backup_dir)
        try:
            verdict = restored.live_verdict()
            restored_decision = restored.approvals.decisions_for_request(rid)[-1]
            # The current binding still matches after the disaster.
            assert verdict.binding_digest() == restored_decision.binding_digest(
                PRINCIPAL)
            # Usable exactly once.
            assert restored.engine._grant_admits(verdict=verdict)
            assert not restored.engine._grant_admits(verdict=verdict)
            assert len(restored.approvals.uses_for_decision(
                restored_decision.decision_id)) == 1
        finally:
            restored.close()


class TestJourneyCLegacyGrantStaysHistorical:
    def test_legacy_grant_restores_but_never_authorizes(
        self, rig_factory, tmp_path
    ) -> None:
        rig = rig_factory()
        rig.reach_waiting_policy()
        legacy = ApprovalRequest(
            request_id="authreq-legacy-disaster", principal=PRINCIPAL,
            action="execute.GENERIC", resource="subject-1", scope=f"job:{JOB}",
            budget_ref=f"job:{JOB}", justification="pre-R5R",
            created_at=rig.clock(), expires_at="2099-01-01T00:00:00Z",
        )
        rig.approvals.add_request(legacy)
        rig.approvals.record_decision(ApprovalDecision(
            decision_id="dec-legacy-disaster", request_ref=legacy.request_id,
            state=ApprovalState.GRANTED, decided_by="id-operator-1",
            decided_at=rig.clock(), bound_action=legacy.action,
            bound_resource=legacy.resource, bound_scope=legacy.scope,
            bound_budget_ref=legacy.budget_ref, reason="legacy grant",
        ))

        backup_dir, manifest = _backup_and_destroy(rig, tmp_path)
        assert manifest["registry_rows"]["governance_approval_use"] == 0
        restored = _restore(tmp_path, backup_dir)
        try:
            # Survives as historical evidence...
            restored_legacy = restored.approvals.get_request(legacy.request_id)
            assert restored_legacy is not None
            assert not restored_legacy.is_complete_binding()
            grant = restored.approvals.effective_grant(
                legacy.request_id, now=restored.clock())
            assert grant is not None
            # ...but cannot authorize a strengthened R5R execution.
            assert not grant.is_complete_binding(PRINCIPAL)
            assert restored.approvals.uses_for_decision(
                "dec-legacy-disaster") == []
        finally:
            restored.close()


class TestRestoredSchemaTruth:
    def test_restore_preserves_schema_version_and_v5_tables(
        self, rig_factory, tmp_path
    ) -> None:
        rig = rig_factory()
        rig.reach_waiting_policy()
        rig.commit()
        backup_dir, manifest = _backup_and_destroy(rig, tmp_path)
        assert manifest["schema_version"] == 5
        restored = _restore(tmp_path, backup_dir)
        try:
            assert int(restored.conn.execute(
                "PRAGMA user_version").fetchone()[0]) == 5
            assert restored.stack.get_step(STEP).status is (
                RuntimeStepStatus.WAITING_POLICY)
        finally:
            restored.close()
