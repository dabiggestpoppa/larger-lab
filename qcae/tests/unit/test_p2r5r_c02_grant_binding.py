"""P2-R5R-C02 — canonical live ApprovalBinding + current-verdict admission.

Operator law under test:

* one provider-neutral immutable ``ApprovalBinding`` with SEVEN semantic
  fields: principal, action, resource, scope, budget_ref,
  authority_requirement, policy_version (plus constraints);
* canonical serialization (JSON, sorted keys) — never ``'|'`` concatenation;
* ``binding_digest == sha256(canonical serialization)``;
* POLICY_VERSION_BOUND: an approval binds the policy version it was
  evaluated under; a policy-version change needs fresh approval;
* requests persist the full binding; decisions bind request_id + exact
  binding;
* legacy/incomplete approvals stay readable historical evidence and NEVER
  authorize.

Adversarial matrix (through actual admission, ``_grant_admits``):

1 same binding admitted once; 2 second use refused; 3 wrong principal;
4 changed action; 5 changed resource; 6 changed scope; 7 changed budget_ref;
8 changed authority_requirement; 9 changed policy_version; 10 expired;
11 denied; 12 every mismatch leaves the grant unconsumed; 13 fresh matching
request/grant executes after a mismatch; 14 restart preserves truth;
15 restore preserves truth.
"""

from __future__ import annotations

import json
from dataclasses import replace

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.governance.standalone.approvals import (
    POLICY_VERSION_BOUND,
    ApprovalBinding,
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
from qcae.infrastructure.persistence.backup_restore import BackupService, RestoreService
from qcae.infrastructure.persistence.sqlite_approval_registry import SqliteApprovalRegistry
from qcae.infrastructure.persistence.store_factory import open_metadata_db
from qcae.infrastructure.queue.sqlite_step_queue import SqliteStepQueue
from qcae.orchestration.authority_gate import (
    StaticStepAuthorityGate,
    StepAuthorityDecision,
    StepAuthorityVerdict,
)
from qcae.orchestration.jobs.runtime import RuntimeStepStatus
from qcae.orchestration.orchestrator.engine import OrchestratorEngine
from qcae.orchestration.workers.base import DeterministicSuccessWorker
from qcae.tests.unit.test_p2_recovery import _Clock, _job, _step

STEP = "s-1"
JOB = "job-12345678"
PRINCIPAL = "id-worker-runtime"


def _identities() -> LocalIdentityProvider:
    ids = LocalIdentityProvider.__new__(LocalIdentityProvider)
    ids._identities = {}
    ids._current = None
    ids.register(LocalIdentity(identity_id="id-operator-1",
                               kind=IdentityKind.OPERATOR))
    ids.register(LocalIdentity(identity_id=PRINCIPAL,
                               kind=IdentityKind.WORKER))
    return ids


def _gate(policy_version: str = "static-1") -> StaticStepAuthorityGate:
    return StaticStepAuthorityGate(
        require_approval=("execute.GENERIC",), policy_version=policy_version,
    )


def _engine(stack, queue, clock, approvals, *, gate=None):
    return OrchestratorEngine(
        stack, queue, clock=clock,
        authority_gate=gate or _gate(),
        authority_request_sink=ApprovalRegistrySink(approvals, clock=clock),
        approval_registry=approvals,
    )


def _service(stack, queue, clock, engine, approvals) -> LocalRuntimeService:
    return LocalRuntimeService(
        runtime_store=stack, queue=queue, engine=engine,
        identity_provider=_identities(), policy_provider=None,
        approval_registry=approvals, clock=clock, schema_version=5,
        policy_version="static-1", storage_location=":memory:",
    )


def _record_request_event(env, request_id: str) -> None:
    """Append the APPROVAL_REQUESTED event the resolver reads (engine shape)."""
    from qcae.orchestration.jobs.runtime import JobEvent, JobEventType

    env.stack.append_event(
        JobEvent(
            event_seq=0, event_id="", event_type=JobEventType.APPROVAL_REQUESTED,
            job_id=JOB, step_id=STEP, occurred_at=env.clock(),
        ),
        payload_json=json.dumps({"authority_request_id": request_id}),
    )
    env.stack.flush()


def _live(stack, job_id=JOB, step_id=STEP, principal=PRINCIPAL, *, gate=None):
    gate = gate or _gate()
    return gate.evaluate_step_authority(
        stack.get_step(step_id), stack.get_job(job_id), worker_id=principal)


class Env:
    def __init__(self, db_path):
        self.clock = _Clock()
        self.conn = open_metadata_db(db_path)
        from qcae.infrastructure.persistence.sqlite_runtime_store import SqliteRuntimeStore

        self.stack = SqliteRuntimeStore(self.conn)
        self.approvals = SqliteApprovalRegistry(self.conn)
        self.queue = SqliteStepQueue(self.conn, self.stack, now_fn=self.clock,
                                     lease_ttl_seconds=60)
        self.engine = _engine(self.stack, self.queue, self.clock, self.approvals)
        self.engine.register_worker_type("GENERIC", DeterministicSuccessWorker())
        self.service = _service(self.stack, self.queue, self.clock,
                                self.engine, self.approvals)

    def reach_waiting_policy(self):
        self.engine.submit(_job(job_id=JOB),
                           [_step(STEP, idempotency_key=f"{JOB}:{STEP}")])
        self.engine.ready_steps(JOB)
        lease = self.engine.lease_next(JOB, PRINCIPAL)
        result = self.engine.execute_step(lease, worker_id=PRINCIPAL)
        assert result.status.value == "BLOCKED_POLICY"
        assert self.stack.get_step(STEP).status is RuntimeStepStatus.WAITING_POLICY
        rid = self.engine._resolver.latest_for_step(JOB, STEP)
        assert rid
        return rid

    def grant_and_release(self, rid):
        self.service.decide_approval(
            request_id=rid, decision="GRANTED", decided_by="id-operator-1",
            job_id=JOB, reason="ok",
        )
        self.service.release_granted_step(JOB, STEP)
        return self.approvals.decisions_for_request(rid)[-1]

    def close(self):
        self.conn.close()


@pytest.fixture()
def env(tmp_path):
    e = Env(tmp_path / "grant.sqlite3")
    yield e
    e.close()


# ---------------------------------------------------------------------------
# Binding schema
# ---------------------------------------------------------------------------


class TestApprovalBindingSchema:
    def test_binding_is_canonical_json_not_pipe_concatenation(self) -> None:
        binding = ApprovalBinding(
            principal="p", action="a", resource="r", scope="s",
            budget_ref="b", authority_requirement="q", policy_version="1.0.0",
        )
        payload = json.dumps(binding.canonical_dict(), ensure_ascii=False,
                             sort_keys=True, separators=(",", ":"))
        import hashlib

        expected = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        assert binding.binding_digest() == expected
        # The old four-field concatenation digest must not match.
        legacy = hashlib.sha256("p|a|r|s".encode("utf-8")).hexdigest()
        assert binding.binding_digest() != legacy

    def test_binding_has_all_seven_semantic_fields(self) -> None:
        fields = set(ApprovalBinding.__dataclass_fields__)
        for required in ("principal", "action", "resource", "scope",
                         "budget_ref", "authority_requirement",
                         "policy_version"):
            assert required in fields
        binding = ApprovalBinding(
            principal="p", action="a", resource="r", scope="s",
            budget_ref="b", authority_requirement="q", policy_version="1",
        )
        assert binding.is_complete()

    def test_incomplete_binding_is_never_complete(self) -> None:
        binding = ApprovalBinding(
            principal="p", action="a", resource="r", scope="s",
            budget_ref="", authority_requirement="q", policy_version="1",
        )
        assert not binding.is_complete()

    def test_policy_version_bound_law_is_documented(self) -> None:
        assert "policy version" in POLICY_VERSION_BOUND
        assert ApprovalRequest.SCHEMA_VERSION == 2
        assert ApprovalDecision.SCHEMA_VERSION == 2
        assert StepAuthorityVerdict.SCHEMA_VERSION == 2

    def test_request_persists_full_binding(self, env) -> None:
        rid = env.reach_waiting_policy()
        request = env.approvals.get_request(rid)
        assert request.authority_requirement == ""  # baseline action
        assert request.policy_version == "static-1"
        assert request.budget_ref
        assert request.is_complete_binding()

    def test_verdict_and_decision_digests_agree(self, env) -> None:
        rid = env.reach_waiting_policy()
        decision = env.grant_and_release(rid)
        verdict = _live(env.stack)
        assert verdict.binding_digest() == decision.binding_digest(PRINCIPAL)

    def test_legacy_request_is_readable_but_incomplete(self, env) -> None:
        env.reach_waiting_policy()
        legacy = ApprovalRequest(
            request_id="req-legacy-approval", principal=PRINCIPAL,
            action="execute.GENERIC", resource="subject-1", scope=f"job:{JOB}",
            budget_ref=f"job:{JOB}", justification="pre-R5R request",
            created_at=env.clock(),
        )
        env.approvals.add_request(legacy)
        assert env.approvals.get_request("req-legacy-approval") is not None
        assert not legacy.is_complete_binding()
        assert legacy.policy_version == ""


# ---------------------------------------------------------------------------
# Live-binding adversarial matrix
# ---------------------------------------------------------------------------


class TestLiveBindingAdmission:
    def test_01_same_binding_admitted_once(self, env) -> None:
        rid = env.reach_waiting_policy()
        env.grant_and_release(rid)
        assert env.engine._grant_admits(verdict=_live(env.stack))
        assert not env.engine._grant_admits(verdict=_live(env.stack))

    def test_02_second_use_refused_and_single_use_row(self, env) -> None:
        rid = env.reach_waiting_policy()
        decision = env.grant_and_release(rid)
        assert env.engine._grant_admits(verdict=_live(env.stack))
        assert not env.engine._grant_admits(verdict=_live(env.stack))
        assert len(env.approvals.uses_for_decision(decision.decision_id)) == 1

    def test_03_wrong_principal_refused(self, env) -> None:
        rid = env.reach_waiting_policy()
        decision = env.grant_and_release(rid)
        assert not env.engine._grant_admits(
            verdict=_live(env.stack, principal="id-worker-other"))
        assert env.approvals.uses_for_decision(decision.decision_id) == []

    @pytest.mark.parametrize(
        "field, value",
        [
            ("action", "execute.OTHER"),
            ("resource", "subject-2"),
            ("scope", "job:another-job"),
            ("budget_ref", "budget-B2"),
            ("requirement", "requirement-Q2"),
            ("policy_version", "2.0.0"),
        ],
    )
    def test_04_09_changed_binding_field_refused_and_unconsumed(
        self, env, field, value
    ) -> None:
        rid = env.reach_waiting_policy()
        decision = env.grant_and_release(rid)
        verdict = replace(_live(env.stack), **{field: value})
        assert not env.engine._grant_admits(verdict=verdict)
        # Mismatch never consumes the grant.
        assert env.approvals.uses_for_decision(decision.decision_id) == []
        # And the unchanged live verdict still admits exactly once.
        assert env.engine._grant_admits(verdict=_live(env.stack))

    def test_10_expired_grant_refused_without_consumption(self, env) -> None:
        rid = env.reach_waiting_policy()
        decision = env.grant_and_release(rid)
        env.clock.advance(25 * 3600)
        assert not env.engine._grant_admits(verdict=_live(env.stack))
        assert env.approvals.uses_for_decision(decision.decision_id) == []

    def test_11_denied_grant_refused(self, env) -> None:
        rid = env.reach_waiting_policy()
        env.service.decide_approval(
            request_id=rid, decision="DENIED", decided_by="id-operator-1",
            job_id=JOB, reason="no",
        )
        assert not env.engine._grant_admits(verdict=_live(env.stack))

    def test_12_every_mismatch_leaves_grant_unconsumed(self, env) -> None:
        rid = env.reach_waiting_policy()
        decision = env.grant_and_release(rid)
        mismatches = [
            replace(_live(env.stack), action="execute.OTHER"),
            replace(_live(env.stack), resource="r2"),
            replace(_live(env.stack), scope="s2"),
            replace(_live(env.stack), budget_ref="b2"),
            replace(_live(env.stack), requirement="q2"),
            replace(_live(env.stack), policy_version="9.9.9"),
        ]
        for verdict in mismatches:
            assert not env.engine._grant_admits(verdict=verdict)
        assert env.approvals.uses_for_decision(decision.decision_id) == []
        assert env.engine._grant_admits(verdict=_live(env.stack))

    def test_13_fresh_matching_grant_after_mismatch_executes(self, env) -> None:
        rid = env.reach_waiting_policy()
        old = env.grant_and_release(rid)
        # A live verdict under a NEW policy version is refused, unconsumed.
        new_gate = _gate(policy_version="static-2")
        stale = new_gate.evaluate_step_authority(
            env.stack.get_step(STEP), env.stack.get_job(JOB), worker_id=PRINCIPAL)
        assert not env.engine._grant_admits(verdict=stale)
        assert env.approvals.uses_for_decision(old.decision_id) == []
        # A fresh request under the new policy version + fresh grant admits.
        sink = ApprovalRegistrySink(env.approvals, clock=env.clock)
        new_rid = sink.record_authority_request(stale)
        _record_request_event(env, new_rid)
        env.approvals.record_decision(ApprovalDecision(
            decision_id="dec-fresh-policy",
            request_ref=new_rid,
            state=ApprovalState.GRANTED,
            decided_by="id-operator-1",
            decided_at=env.clock(),
            bound_action=stale.action,
            bound_resource=stale.resource,
            bound_scope=stale.scope,
            bound_budget_ref=stale.budget_ref,
            bound_authority_requirement=stale.requirement,
            bound_policy_version=stale.policy_version,
            reason="fresh approval under static-2",
        ))
        engine2 = _engine(env.stack, env.queue, env.clock, env.approvals,
                          gate=new_gate)
        assert engine2._grant_admits(verdict=stale)

    def test_14_restart_preserves_binding_and_use_truth(self, tmp_path) -> None:
        db = tmp_path / "restart.sqlite3"
        first = Env(db)
        rid = first.reach_waiting_policy()
        first.grant_and_release(rid)
        assert first.engine._grant_admits(verdict=_live(first.stack))
        first.stack.flush()
        first.conn.commit()
        first.conn.close()

        second = Env(db)
        try:
            # Consumed before restart: still consumed, still binding-bound.
            assert not second.engine._grant_admits(verdict=_live(second.stack))
            decision = second.approvals.decisions_for_request(rid)[-1]
            assert len(second.approvals.uses_for_decision(decision.decision_id)) == 1
            verdict = _live(second.stack)
            assert verdict.binding_digest() == decision.binding_digest(PRINCIPAL)
        finally:
            second.close()

    def test_15_restore_preserves_binding_and_use_truth(self, tmp_path) -> None:
        db = tmp_path / "disaster.sqlite3"
        artifacts = tmp_path / "artifacts"
        src = Env(db)
        rid = src.reach_waiting_policy()
        decision = src.grant_and_release(rid)
        assert src.engine._grant_admits(verdict=_live(src.stack))
        src.stack.flush()
        src.conn.commit()
        BackupService(src.conn, None).backup(tmp_path / "backup")
        src.conn.close()
        db.unlink()

        restored_db = tmp_path / "restored" / "meta.sqlite3"
        RestoreService().restore(tmp_path / "backup", restored_db, artifacts)
        restore_conn = open_metadata_db(restored_db)
        from qcae.infrastructure.persistence.sqlite_runtime_store import SqliteRuntimeStore

        restored = SqliteRuntimeStore(restore_conn)
        approvals = SqliteApprovalRegistry(restore_conn)
        restored_decision = approvals.decisions_for_request(rid)[-1]
        assert restored_decision.decision_id == decision.decision_id
        assert len(approvals.uses_for_decision(decision.decision_id)) == 1
        gate = _gate()
        verdict = gate.evaluate_step_authority(
            restored.get_step(STEP), restored.get_job(JOB), worker_id=PRINCIPAL)
        assert verdict.binding_digest() == restored_decision.binding_digest(PRINCIPAL)
        restore_conn.close()


class TestLegacyApprovalNeverAuthorizes:
    def test_legacy_request_and_grant_cannot_admit(self, env) -> None:
        # A pre-R5R request/grant pair (no policy version) is historical only.
        legacy_request = ApprovalRequest(
            request_id="req-legacy-1", principal=PRINCIPAL,
            action="execute.GENERIC", resource="subject-1",
            scope=f"job:{JOB}", budget_ref=f"job:{JOB}",
            justification="legacy", created_at=env.clock(),
            expires_at="2099-01-01T00:00:00Z",
        )
        env.approvals.add_request(legacy_request)
        env.approvals.record_decision(ApprovalDecision(
            decision_id="dec-legacy-1", request_ref="req-legacy-1",
            state=ApprovalState.GRANTED, decided_by="id-operator-1",
            decided_at=env.clock(), bound_action=legacy_request.action,
            bound_resource=legacy_request.resource,
            bound_scope=legacy_request.scope,
            bound_budget_ref=legacy_request.budget_ref,
            reason="legacy grant",
        ))
        grant = env.approvals.effective_grant("req-legacy-1", now=env.clock())
        assert grant is not None
        assert not grant.is_complete_binding(PRINCIPAL)

    def test_release_refuses_legacy_request_binding(self, env) -> None:
        env.reach_waiting_policy()
        legacy = ApprovalRequest(
            request_id="authreq-legacy-release", principal=PRINCIPAL,
            action="execute.GENERIC", resource="subject-1", scope=f"job:{JOB}",
            budget_ref=f"job:{JOB}", justification="pre-R5R request",
            created_at=env.clock(), expires_at="2099-01-01T00:00:00Z",
        )
        env.approvals.add_request(legacy)
        _record_request_event(env, legacy.request_id)
        env.approvals.record_decision(ApprovalDecision(
            decision_id="dec-legacy-release", request_ref=legacy.request_id,
            state=ApprovalState.GRANTED, decided_by="id-operator-1",
            decided_at=env.clock(), bound_action=legacy.action,
            bound_resource=legacy.resource, bound_scope=legacy.scope,
            bound_budget_ref=legacy.budget_ref, reason="legacy",
        ))
        with pytest.raises(QcaeValidationError, match="legacy/incomplete"):
            env.service.release_granted_step(JOB, STEP)

    def test_registry_rejects_requirement_swap(self, env) -> None:
        rid = env.reach_waiting_policy()
        request = env.approvals.get_request(rid)
        with pytest.raises(QcaeValidationError, match="laundering"):
            env.approvals.record_decision(ApprovalDecision(
                decision_id="dec-swap-req", request_ref=rid,
                state=ApprovalState.GRANTED, decided_by="id-operator-1",
                decided_at=env.clock(), bound_action=request.action,
                bound_resource=request.resource, bound_scope=request.scope,
                bound_budget_ref=request.budget_ref,
                bound_authority_requirement="requirement-WIDENED",
                bound_policy_version=request.policy_version, reason="widen",
            ))

    def test_registry_rejects_policy_version_swap(self, env) -> None:
        rid = env.reach_waiting_policy()
        request = env.approvals.get_request(rid)
        with pytest.raises(QcaeValidationError, match="laundering"):
            env.approvals.record_decision(ApprovalDecision(
                decision_id="dec-swap-pol", request_ref=rid,
                state=ApprovalState.GRANTED, decided_by="id-operator-1",
                decided_at=env.clock(), bound_action=request.action,
                bound_resource=request.resource, bound_scope=request.scope,
                bound_budget_ref=request.budget_ref,
                bound_authority_requirement=request.authority_requirement,
                bound_policy_version="999.0.0", reason="policy swap",
            ))
