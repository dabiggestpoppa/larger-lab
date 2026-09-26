import pytest
from oce_control.plane import ControlPlane
from oce_control.clocks import get_clock
from oce_control.boundaries import POOrchestrator, HermesBoundary, PO_ONLY_ACTIONS, ENVIRONMENT_LOCKS
from oce_control.openclaw_adapter import OpenClawAdapter
from oce_control.hashes import payload_hash, generate_id, generate_idempotency_key


class TestHealthAndRecovery:
    def test_health_check_healthy(self, plane):
        health = plane.api.health()
        assert health.ok

    def test_pg_unavailable_blocks(self, plane):
        plane.health_service.set_pg_available(False)
        health = plane.api.health()
        assert health.data["overall"] == "blocked"
        ready = plane.api.readiness()
        assert not ready.ok

    def test_redis_unavailable_degraded(self, plane):
        plane.health_service.set_redis_available(False)
        health = plane.api.health()
        assert health.data["overall"] == "degraded"
        ready = plane.api.readiness()
        assert ready.ok

    def test_recovery_after_restart(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        job = plane.job_store.submit_job(job_type="test_job", submitting_actor="po-test01", grant_id=grant.grant_id, payload={"data": "test"})
        plane.worker_protocol.admit_worker(worker_id="worker-local01", capabilities=["test_job"])
        plane.worker_protocol.claim_work("worker-local01", job.job_id, lease_ttl=10)
        get_clock().advance(100)
        result = plane.recovery.recover_all()
        assert result.recovered_jobs > 0 or result.recovered_leases > 0

    def test_redis_loss_reconciled(self, plane):
        result = plane.recovery.reconcile_redis_loss()
        assert result["pg_authoritative"] is True
        assert result["data_loss"] == "none_redis_is_transient"

    def test_pg_unavailable_fail_closed(self, plane):
        result = plane.recovery.reconcile_pg_unavailable()
        assert result["action"] == "fail_closed"

    def test_no_duplicate_effects_after_recovery(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        plane.job_store.submit_job(job_type="test_job", submitting_actor="po-test01", grant_id=grant.grant_id, payload={"data": "test"})
        plane.recovery.recover_all()
        assert plane.recovery.verify_no_duplicate_effects()


class TestAPIPermissions:
    def test_api_submit_with_permission(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        resp = plane.api.submit_job(grant_id=grant.grant_id, actor_id="po-test01", job_type="test_job", payload={"data": "test"})
        assert resp.ok
        assert resp.status == "success"

    def test_api_submit_without_permission_denied(self, plane):
        resp = plane.api.submit_job(grant_id="nonexistent-grant", actor_id="unknown-actor", job_type="test_job", payload={"data": "test"})
        assert not resp.ok
        assert resp.status == "denied"

    def test_api_inspect_nonexistent_job(self, plane):
        read_grant = plane.authority.issue_grant(actor_id="po-test01", action="read", target="default")
        resp = plane.api.inspect_job(grant_id=read_grant.grant_id, actor_id="po-test01", job_id="nonexistent-job")
        assert not resp.ok
        assert resp.status == "not_found"

    def test_api_audit_history(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        plane.api.submit_job(grant_id=grant.grant_id, actor_id="po-test01", job_type="test_job", payload={"data": "test"})
        read_grant = plane.authority.issue_grant(actor_id="po-test01", action="read", target="default")
        resp = plane.api.audit_history(grant_id=read_grant.grant_id, actor_id="po-test01")
        assert resp.ok
        assert len(resp.data["audit_log"]) > 0

    def test_direct_api_permission_bypass_blocked(self, plane):
        resp = plane.api.submit_job(grant_id="invalid", actor_id="attacker", job_type="malicious", payload={"data": "steal"})
        assert resp.status == "denied"


class TestPOBoundary:
    def test_po_create_work_plan(self, plane):
        plan = plane.po.create_work_plan(po_agent_id="po-main01", plan_name="test-plan", steps=[{"step": 1}])
        assert plan["plan_id"]
        assert plan["status"] == "created"

    def test_po_submit_permitted_job(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-main01", action="submit_job", target="default")
        result = plane.po.submit_permitted_job(po_agent_id="po-main01", grant_id=grant.grant_id, job_type="test_job", payload={"data": "test"})
        assert result["status"] == "pending"

    def test_po_cannot_bypass_environment_lock(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-main01", action="submit_job", target="default")
        with pytest.raises(PermissionError, match="locked"):
            plane.po.submit_permitted_job(po_agent_id="po-main01", grant_id=grant.grant_id, job_type="test_job", payload={"data": "test"}, environment="cloud")

    def test_po_high_risk_requires_approval(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-main01", action="submit_job", target="default")
        with pytest.raises(PermissionError, match="approval"):
            plane.po.submit_permitted_job(po_agent_id="po-main01", grant_id=grant.grant_id, job_type="deploy_to_cloud", payload={"data": "test"}, environment="local")

    def test_po_spawn_subagent(self, plane):
        subagent = plane.po.spawn_subagent(po_agent_id="po-main01", subagent_type="research", task="analyze data", bounds={"timeout": 300})
        assert subagent["subagent_id"]

    def test_po_escalate_decision(self, plane):
        escalation = plane.po.escalate_decision(po_agent_id="po-main01", decision="operator_approval", context={"risk": "high"})
        assert escalation["status"] == "pending_operator"


class TestHermesBoundary:
    def test_hermes_receive_request(self, plane):
        req = plane.hermes.receive_request(sender_id="user-01", conversation_id="conv-01", request_text="hello")
        assert req.routing_destination == "hermes_direct"

    def test_hermes_routes_to_po_for_oce(self, plane):
        req = plane.hermes.receive_request(sender_id="user-01", conversation_id="conv-01", request_text="run OCE strategy research")
        assert req.routing_destination == "po"

    def test_hermes_escalates_capital_request(self, plane):
        req = plane.hermes.receive_request(sender_id="user-01", conversation_id="conv-01", request_text="approve capital for trading")
        assert req.risk_class == "capital"
        assert req.routing_destination == "po_escalation"
        escalation = plane.hermes.escalate_to_po(req.request_id)
        assert escalation.get("status") == "pending_operator"

    def test_hermes_cannot_perform_po_actions(self, plane):
        for action in PO_ONLY_ACTIONS:
            assert plane.hermes.check_hermes_boundary(action)

    def test_hermes_rate_limiting(self, plane):
        for i in range(10):
            plane.hermes.receive_request(sender_id="user-spam", conversation_id="conv-spam", request_text=f"message {i}")
        with pytest.raises(PermissionError, match="Rate limit"):
            plane.hermes.receive_request(sender_id="user-spam", conversation_id="conv-spam", request_text="message 11")
