"""Control Plane assembly — wires all components together.

This is the one-command local startup path for the OCE control plane.
"""
from __future__ import annotations
from typing import Optional

from .clocks import get_clock, set_test_clock, TestClock, reset_clock
from .authority import AuthorityEngine
from .job_store import JobStore
from .scheduler import Scheduler
from .worker import WorkerProtocol
from .health import HealthService
from .api import ControlPlaneAPI
from .boundaries import POOrchestrator, HermesBoundary
from .events import EventStore
from .recovery import RecoveryCoordinator
from .evidence import EvidenceBuilder, TruthPromotionLedger, ReplayHarness


class ControlPlane:
    """The assembled OCE control plane — all components wired together."""

    def __init__(self, *, test_clock: Optional[TestClock] = None):
        # Set up clock
        if test_clock:
            set_test_clock(test_clock)

        # Core components
        self.authority = AuthorityEngine()
        self.job_store = JobStore(self.authority)
        self.scheduler = Scheduler(self.job_store)
        self.worker_protocol = WorkerProtocol(self.job_store)
        self.event_store = EventStore()

        # Services
        self.health_service = HealthService(
            job_store=self.job_store,
            scheduler=self.scheduler,
            worker_protocol=self.worker_protocol,
        )

        # API boundary
        self.api = ControlPlaneAPI(
            authority=self.authority,
            job_store=self.job_store,
            scheduler=self.scheduler,
            worker_protocol=self.worker_protocol,
            health_service=self.health_service,
        )

        # Agent boundaries
        self.po = POOrchestrator(self.authority, self.job_store)
        self.hermes = HermesBoundary(self.po)

        # Recovery
        self.recovery = RecoveryCoordinator(
            self.job_store, self.scheduler, self.worker_protocol
        )

        # Evidence
        self.truth_ledger = TruthPromotionLedger()
        self.replay = ReplayHarness(self.job_store)

    def startup(self, environ: Optional[dict] = None) -> dict:
        """Start the control plane. Returns startup status.

        Before activating, the effective configuration is validated fail-closed
        (Book 4 surface C). A malformed / incomplete / forbidden effective
        config refuses to start and returns a BLOCKED status with an
        operator-legible, secret-free message instead of {"status": "started"}.
        """
        from .config_startup import require_startable, startup_report

        report = None
        try:
            require_startable(environ)
        except SystemExit as exc:
            report = str(exc) or startup_report(environ)
        if report:
            return {
                "status": "blocked",
                "reason": report,
                "health": None,
                "components": [],
            }
        health = self.health_service.check_health()
        return {
            "status": "started",
            "health": health.to_dict(),
            "components": [
                "authority", "job_store", "scheduler", "worker_protocol",
                "event_store", "health_service", "api", "po", "hermes",
                "recovery", "truth_ledger", "replay",
            ],
        }

    def shutdown(self) -> dict:
        """Shutdown the control plane cleanly."""
        # Disconnect all workers
        for wid in list(self.worker_protocol.workers.keys()):
            self.worker_protocol.disconnect_worker(wid)
        return {"status": "shutdown", "workers_disconnected": True}

    def smoke_test(self) -> dict:
        """Run a smoke test of the control plane."""
        results = {}

        # 1. Health check
        health = self.api.health()
        results["health"] = {"ok": health.ok, "status": health.status}

        # 2. Readiness check
        ready = self.api.readiness()
        results["readiness"] = {"ok": ready.ok, "status": ready.status}

        # 3. Submit a test job
        grant = self.authority.issue_grant(
            actor_id="operator-smoke-test",
            action="submit_job",
            target="default",
        )
        job_resp = self.api.submit_job(
            grant_id=grant.grant_id,
            actor_id="operator-smoke-test",
            job_type="smoke_test",
            payload={"test": True},
        )
        results["job_submit"] = {"ok": job_resp.ok, "status": job_resp.status}

        # 4. Inspect the job (read authorization at the service boundary)
        read_grant = self.authority.issue_grant(
            actor_id="operator-smoke-test",
            action="read",
            target="default",
        )
        if job_resp.ok:
            inspect = self.api.inspect_job(
                grant_id=read_grant.grant_id,
                actor_id="operator-smoke-test",
                job_id=job_resp.data["job_id"],
            )
            results["job_inspect"] = {"ok": inspect.ok, "status": inspect.status}

        # 5. Worker admit and claim
        worker = self.worker_protocol.admit_worker(
            worker_id="worker-smoke-test",
            capabilities=["smoke_test"],
        )
        results["worker_admit"] = {"ok": True, "worker_id": worker.worker_id}

        # 6. System state (read authorization)
        state = self.api.system_state(
            grant_id=read_grant.grant_id,
            actor_id="operator-smoke-test",
        )
        results["system_state"] = {"ok": state.ok, "status": state.status}

        return results

    @property
    def is_local(self) -> bool:
        """The control plane is always local-first."""
        return True

    @property
    def cloud_enabled(self) -> bool:
        """Cloud is never enabled in Book 2."""
        return False
