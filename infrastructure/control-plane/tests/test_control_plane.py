"""OCE Control Plane comprehensive tests."""
import pytest
from oce_control.plane import ControlPlane
from oce_control.clocks import get_clock
from oce_control.authority import AuthorityEngine, RISK_CLASSES
from oce_control.job_store import JobStore
from oce_control.scheduler import Scheduler
from oce_control.worker import WorkerProtocol
from oce_control.events import EventStore
from oce_control.recovery import RecoveryCoordinator
from oce_control.evidence import EvidenceBuilder, TruthPromotionLedger, ReplayHarness
from oce_control.boundaries import POOrchestrator, HermesBoundary, PO_ONLY_ACTIONS, ENVIRONMENT_LOCKS
from oce_control.state_machines import is_valid_transition, assert_transition, is_terminal
from oce_control.openclaw_adapter import OpenClawAdapter
from oce_control.hashes import payload_hash, generate_id, generate_idempotency_key

class TestStateMachines:
    def test_job_transitions_legal(self):
        assert is_valid_transition("job", "pending", "scheduled")
        assert is_valid_transition("job", "scheduled", "leased")
        assert is_valid_transition("job", "leased", "running")
        assert is_valid_transition("job", "running", "succeeded")
    def test_job_transitions_illegal(self):
        assert not is_valid_transition("job", "pending", "running")
        assert not is_valid_transition("job", "succeeded", "pending")
    def test_illegal_transition_raises(self):
        with pytest.raises(ValueError, match="Illegal"):
            assert_transition("job", "pending", "running")
    def test_terminal_states(self):
        assert is_terminal("job", "succeeded")
        assert is_terminal("job", "cancelled")
        assert not is_terminal("job", "pending")
    def test_grant_transitions(self):
        assert is_valid_transition("grant", "active", "revoked")
        assert not is_valid_transition("grant", "revoked", "active")
        assert is_terminal("grant", "revoked")
    def test_artifact_transitions(self):
        assert is_valid_transition("artifact", "provisional", "verified")
        assert is_valid_transition("artifact", "verified", "promoted")
        assert not is_valid_transition("artifact", "provisional", "promoted")

class TestAuthorityEngine:
    def test_issue_grant_succeeds(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        assert grant.status == "active"
    def test_verify_grant_succeeds(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        verified = plane.authority.verify_grant(grant.grant_id, "submit_job", "default")
        assert verified.grant_id == grant.grant_id
    def test_missing_grant_denied(self, plane):
        with pytest.raises(PermissionError, match="not found"):
            plane.authority.verify_grant("nonexistent", "submit_job", "default")
    def test_revoked_grant_denied(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        plane.authority.revoke_grant(grant.grant_id)
        with pytest.raises(PermissionError, match="revoked"):
            plane.authority.verify_grant(grant.grant_id, "submit_job", "default")
    def test_expired_grant_denied(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default", ttl_seconds=1)
        get_clock().advance(2)
        with pytest.raises(PermissionError, match="expired"):
            plane.authority.verify_grant(grant.grant_id, "submit_job", "default")
    def test_wrong_action_denied(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        with pytest.raises(PermissionError, match="authorizes"):
            plane.authority.verify_grant(grant.grant_id, "delete_job", "default")
    def test_wrong_target_denied(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        with pytest.raises(PermissionError, match="targets"):
            plane.authority.verify_grant(grant.grant_id, "submit_job", "wrong_target")
    def test_self_approval_blocked(self, plane):
        with pytest.raises(PermissionError, match="cannot approve"):
            plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default", risk_class="local-write", approved_by="po-test01")
    def test_hermes_blocked_from_po_actions(self, plane):
        for action in ["approve_capital", "authorize_deployment", "enable_trading"]:
            with pytest.raises(PermissionError):
                plane.authority.issue_grant(actor_id="hermes-test01", action=action, target="default", approved_by="operator-test01")
    def test_high_risk_requires_approval(self, plane):
        with pytest.raises(PermissionError, match="requires explicit"):
            plane.authority.issue_grant(actor_id="po-test01", action="approve_capital", target="capital", risk_class="capital")
    def test_denial_recorded(self, plane):
        denial = plane.authority.record_denial(reason_code="missing_authority", actor_id="unknown", requested_action="submit_job", requested_target="default")
        assert denial.denial_id
        assert len(plane.authority.denials) == 1
    def test_idempotency_replay_detected(self, plane):
        key = generate_idempotency_key()
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        assert not plane.authority.check_idempotency_replay(key, grant.grant_id)
        assert plane.authority.check_idempotency_replay(key, grant.grant_id)
class TestJobStore:
    def test_submit_job_succeeds(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        job = plane.job_store.submit_job(job_type="test_job", submitting_actor="po-test01", grant_id=grant.grant_id, payload={"data": "test"})
        assert job.status == "pending"
        assert job.job_id
        assert job.payload_hash
    def test_duplicate_job_submission_idempotent(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        key = generate_idempotency_key()
        job1 = plane.job_store.submit_job(job_type="test_job", submitting_actor="po-test01", grant_id=grant.grant_id, payload={"data": "test"}, idempotency_key=key)
        job2 = plane.job_store.submit_job(job_type="test_job", submitting_actor="po-test01", grant_id=grant.grant_id, payload={"data": "test"}, idempotency_key=key)
        assert job1.job_id == job2.job_id
    def test_conflicting_idempotency_keys(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        job1 = plane.job_store.submit_job(job_type="test_job", submitting_actor="po-test01", grant_id=grant.grant_id, payload={"data": "test"}, idempotency_key="a"*64)
        job2 = plane.job_store.submit_job(job_type="test_job", submitting_actor="po-test01", grant_id=grant.grant_id, payload={"data": "different"}, idempotency_key="b"*64)
        assert job1.job_id != job2.job_id
    def test_unauthorized_job_submission_denied(self, plane):
        with pytest.raises(PermissionError):
            plane.job_store.submit_job(job_type="test_job", submitting_actor="unknown-actor", grant_id="nonexistent-grant", payload={"data": "test"})
    def test_job_transition_legal(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        job = plane.job_store.submit_job(job_type="test_job", submitting_actor="po-test01", grant_id=grant.grant_id, payload={"data": "test"})
        plane.job_store.transition(job.job_id, "scheduled")
        assert plane.job_store.get_job(job.job_id).status == "scheduled"
    def test_invalid_lifecycle_transition_denied(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        job = plane.job_store.submit_job(job_type="test_job", submitting_actor="po-test01", grant_id=grant.grant_id, payload={"data": "test"})
        with pytest.raises(ValueError, match="Illegal"):
            plane.job_store.transition(job.job_id, "running")


class TestWorkerLeases:
    def test_worker_admit_and_claim(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        job = plane.job_store.submit_job(job_type="test_job", submitting_actor="po-test01", grant_id=grant.grant_id, payload={"data": "test"})
        plane.worker_protocol.admit_worker(worker_id="worker-local01", capabilities=["test_job"])
        claimed = plane.worker_protocol.claim_work("worker-local01", job.job_id)
        assert claimed["status"] == "leased"

    def test_stale_worker_cannot_commit(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        job = plane.job_store.submit_job(job_type="test_job", submitting_actor="po-test01", grant_id=grant.grant_id, payload={"data": "test"})
        plane.worker_protocol.admit_worker(worker_id="worker-local01", capabilities=["test_job"])
        plane.worker_protocol.claim_work("worker-local01", job.job_id)
        get_clock().advance(120)
        with pytest.raises(PermissionError, match="[Ss]tale"):
            plane.worker_protocol.submit_result("worker-local01", job.job_id, {"result": "done"})

    def test_expired_lease_blocks_result(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        job = plane.job_store.submit_job(job_type="test_job", submitting_actor="po-test01", grant_id=grant.grant_id, payload={"data": "test"})
        plane.worker_protocol.admit_worker(worker_id="worker-local01", capabilities=["test_job"])
        plane.worker_protocol.claim_work("worker-local01", job.job_id, lease_ttl=5)
        get_clock().advance(10)
        with pytest.raises(PermissionError):
            plane.worker_protocol.submit_result("worker-local01", job.job_id, {"result": "done"})

    def test_wrong_worker_cannot_complete(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        job = plane.job_store.submit_job(job_type="test_job", submitting_actor="po-test01", grant_id=grant.grant_id, payload={"data": "test"})
        plane.worker_protocol.admit_worker(worker_id="worker-local01", capabilities=["test_job"])
        plane.worker_protocol.admit_worker(worker_id="worker-local02", capabilities=["test_job"])
        plane.worker_protocol.claim_work("worker-local01", job.job_id)
        with pytest.raises(PermissionError):
            plane.worker_protocol.submit_result("worker-local02", job.job_id, {"result": "done"})

    def test_lease_renewal(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        job = plane.job_store.submit_job(job_type="test_job", submitting_actor="po-test01", grant_id=grant.grant_id, payload={"data": "test"})
        plane.worker_protocol.admit_worker(worker_id="worker-local01", capabilities=["test_job"])
        plane.worker_protocol.claim_work("worker-local01", job.job_id, lease_ttl=10)
        get_clock().advance(5)
        plane.job_store.renew_lease(job.job_id, "worker-local01", lease_ttl=10)
        get_clock().advance(7)
        result = plane.worker_protocol.submit_result("worker-local01", job.job_id, {"result": "done"})
        assert result["status"] == "succeeded"

    def test_abandoned_work_recovered(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        job = plane.job_store.submit_job(job_type="test_job", submitting_actor="po-test01", grant_id=grant.grant_id, payload={"data": "test"})
        plane.worker_protocol.admit_worker(worker_id="worker-local01", capabilities=["test_job"])
        plane.worker_protocol.claim_work("worker-local01", job.job_id, lease_ttl=10)
        get_clock().advance(100)
        recovered = plane.worker_protocol.recover_abandoned_work()
        assert recovered > 0

    def test_duplicate_delivery_protection(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        key = generate_idempotency_key()
        job1 = plane.job_store.submit_job(job_type="test_job", submitting_actor="po-test01", grant_id=grant.grant_id, payload={"data": "test"}, idempotency_key=key)
        job2 = plane.job_store.submit_job(job_type="test_job", submitting_actor="po-test01", grant_id=grant.grant_id, payload={"data": "test"}, idempotency_key=key)
        assert job1.job_id == job2.job_id
        assert len(plane.job_store.all_jobs) == 1
