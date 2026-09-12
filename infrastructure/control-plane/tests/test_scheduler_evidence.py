import pytest
from oce_control.plane import ControlPlane
from oce_control.clocks import get_clock
from oce_control.evidence import EvidenceBuilder, TruthPromotionLedger
from oce_control.boundaries import POOrchestrator, HermesBoundary, PO_ONLY_ACTIONS, ENVIRONMENT_LOCKS
from oce_control.openclaw_adapter import OpenClawAdapter
from oce_control.hashes import payload_hash, generate_id, generate_idempotency_key


class TestScheduler:
    def test_immediate_job_scheduled(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        plane.scheduler.create_immediate(job_type="test_job", payload={"data": "test"}, grant_id=grant.grant_id, submitting_actor="po-test01")
        submitted = plane.scheduler.tick()
        assert len(submitted) == 1

    def test_delayed_job_not_ready(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        plane.scheduler.create_delayed(job_type="test_job", payload={"data": "test"}, grant_id=grant.grant_id, submitting_actor="po-test01", delay_seconds=100)
        submitted = plane.scheduler.tick()
        assert len(submitted) == 0

    def test_delayed_job_ready_after_advance(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        plane.scheduler.create_delayed(job_type="test_job", payload={"data": "test"}, grant_id=grant.grant_id, submitting_actor="po-test01", delay_seconds=100)
        get_clock().advance(101)
        submitted = plane.scheduler.tick()
        assert len(submitted) == 1

    def test_recurring_job(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        plane.scheduler.create_recurring(job_type="test_job", payload={"data": "test"}, grant_id=grant.grant_id, submitting_actor="po-test01", interval_seconds=60)
        submitted = plane.scheduler.tick()
        assert len(submitted) == 1
        get_clock().advance(61)
        submitted = plane.scheduler.tick()
        assert len(submitted) == 1

    def test_pause_resume(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        sched = plane.scheduler.create_immediate(job_type="test_job", payload={"data": "test"}, grant_id=grant.grant_id, submitting_actor="po-test01")
        plane.scheduler.pause(sched.schedule_id)
        submitted = plane.scheduler.tick()
        assert len(submitted) == 0
        plane.scheduler.resume(sched.schedule_id)
        submitted = plane.scheduler.tick()
        assert len(submitted) == 1

    def test_scheduler_restart_recovery(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        plane.scheduler.create_recurring(job_type="test_job", payload={"data": "test"}, grant_id=grant.grant_id, submitting_actor="po-test01", interval_seconds=60)
        get_clock().advance(300)
        recovered = plane.scheduler.recover_after_restart()
        assert recovered > 0

    def test_duplicate_prevention_same_tick(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        plane.scheduler.create_immediate(job_type="test_job", payload={"data": "test"}, grant_id=grant.grant_id, submitting_actor="po-test01")
        plane.scheduler.tick()
        submitted2 = plane.scheduler.tick()
        assert len(submitted2) == 0


class TestEvidenceSystem:
    def test_manifest_built_and_verified(self, plane, tmp_path):
        builder = EvidenceBuilder(run_id="test-run-01")
        f = tmp_path / "test.txt"
        f.write_text("test content")
        builder.add_artifact("test.txt", str(f))
        manifest = builder.build_manifest()
        ok, errors = builder.verify_manifest(manifest)
        assert ok

    def test_manifest_tamper_rejected(self, plane, tmp_path):
        builder = EvidenceBuilder(run_id="test-run-01")
        f = tmp_path / "test.txt"
        f.write_text("original content")
        builder.add_artifact("test.txt", str(f))
        manifest = builder.build_manifest()
        f.write_text("tampered content")
        ok, errors = builder.verify_manifest(manifest)
        assert not ok

    def test_missing_artifact_rejected(self, plane, tmp_path):
        builder = EvidenceBuilder(run_id="test-run-01")
        f = tmp_path / "test.txt"
        f.write_text("content")
        builder.add_artifact("test.txt", str(f))
        manifest = builder.build_manifest()
        f.unlink()
        ok, errors = builder.verify_manifest(manifest)
        assert not ok

    def test_truth_promotion(self, plane):
        ledger = plane.truth_ledger
        ledger.register("claim-1", "SCAFFOLDED")
        ledger.promote("claim-1", "SIMULATED", "test evidence")
        assert ledger.get_level("claim-1") == "SIMULATED"

    def test_truth_promotion_blocked_downward(self, plane):
        ledger = plane.truth_ledger
        ledger.register("claim-1", "OBSERVED")
        with pytest.raises(ValueError, match="not an increase"):
            ledger.promote("claim-1", "SIMULATED", "demotion")

    def test_replay_reconstructs(self, plane):
        grant = plane.authority.issue_grant(actor_id="po-test01", action="submit_job", target="default")
        job = plane.job_store.submit_job(job_type="test_job", submitting_actor="po-test01", grant_id=grant.grant_id, payload={"data": "test"})
        replay = plane.replay.replay_job(job.job_id)
        assert replay["job_id"] == job.job_id
        assert replay["replayable"] is True
