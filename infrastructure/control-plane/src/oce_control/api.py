"""API boundary for OCE control plane.

B2 API/UI boundary — health, readiness, job submission, job inspection,
cancellation, retry, schedules, workers, system state, audit history,
evidence links, operational blockers.

Permission checks at the service boundary — not only in the UI.
Binds locally by default. Does not expose the service publicly.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, Any
from dataclasses import dataclass, field, asdict
import json

from .clocks import get_clock
from .hashes import generate_id
from .authority import AuthorityEngine
from .job_store import JobStore
from .scheduler import Scheduler
from .worker import WorkerProtocol
from .health import HealthService


@dataclass
class APIResponse:
    ok: bool
    status: str  # success, denied, error, not_found
    data: dict = field(default_factory=dict)
    error: str = ""
    request_id: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class ControlPlaneAPI:
    """Local API for the OCE control plane. Permission checks at service boundary."""

    def __init__(self, *, authority: AuthorityEngine, job_store: JobStore,
                 scheduler: Scheduler, worker_protocol: WorkerProtocol,
                 health_service: HealthService):
        self._authority = authority
        self._job_store = job_store
        self._scheduler = scheduler
        self._worker_protocol = worker_protocol
        self._health = health_service
        self._audit_log: list[dict] = []

    def _check_permission(self, grant_id: str, action: str, target: str,
                          environment: str = "local") -> bool:
        """Permission check at the service boundary."""
        try:
            self._authority.verify_grant(grant_id, action, target, environment)
            return True
        except PermissionError:
            return False

    def _audit(self, action: str, actor: str, target: str, success: bool,
               error: str = "") -> None:
        clock = get_clock()
        self._audit_log.append({
            "audit_id": generate_id(),
            "action": action,
            "actor": actor,
            "target": target,
            "success": success,
            "error": error,
            "timestamp": clock.now().isoformat(),
        })

    def health(self) -> APIResponse:
        """Health endpoint."""
        status = self._health.check_health()
        return APIResponse(ok=status.overall in ("healthy", "degraded"),
                          status="success",
                          data=status.to_dict(),
                          request_id=generate_id())

    def readiness(self) -> APIResponse:
        """Readiness endpoint."""
        ready, msg = self._health.check_readiness()
        return APIResponse(ok=ready, status="success" if ready else "not_ready",
                          data={"ready": ready, "message": msg},
                          request_id=generate_id())

    def submit_job(self, *, grant_id: str, actor_id: str, job_type: str,
                   payload: dict, **kwargs) -> APIResponse:
        """Submit a job. Permission checked at service boundary."""
        if not self._check_permission(grant_id, "submit_job",
                                       kwargs.get("resource_scope", "default")):
            denial = self._authority.record_denial(
                reason_code="missing_authority",
                actor_id=actor_id,
                requested_action="submit_job",
                requested_target=kwargs.get("resource_scope", "default"),
            )
            self._audit("submit_job", actor_id, "job", False, "denied")
            return APIResponse(ok=False, status="denied",
                              data={"denial": denial.to_dict()},
                              error="missing_authority",
                              request_id=generate_id())
        try:
            job = self._job_store.submit_job(
                job_type=job_type, submitting_actor=actor_id,
                grant_id=grant_id, payload=payload, **kwargs
            )
            self._audit("submit_job", actor_id, job.job_id, True)
            return APIResponse(ok=True, status="success",
                              data=job.to_dict(),
                              request_id=generate_id())
        except Exception as e:
            self._audit("submit_job", actor_id, "job", False, str(e))
            return APIResponse(ok=False, status="error",
                              error=str(e), request_id=generate_id())

    def _deny(self, action: str, actor_id: str, target: str) -> APIResponse:
        """Record a denial + audit entry and return the denied response."""
        denial = self._authority.record_denial(
            reason_code="missing_authority",
            actor_id=actor_id,
            requested_action=action,
            requested_target=target,
        )
        self._audit(action, actor_id, target, False, "denied")
        return APIResponse(ok=False, status="denied",
                          data={"denial": denial.to_dict()},
                          error="missing_authority",
                          request_id=generate_id())

    def inspect_job(self, *, grant_id: str, actor_id: str, job_id: str) -> APIResponse:
        """Inspect a job. Read authorization required at the service boundary (gap 9)."""
        if not self._check_permission(grant_id, "read", "default"):
            return self._deny("inspect_job", actor_id, job_id)
        job = self._job_store.get_job(job_id)
        if job is None:
            return APIResponse(ok=False, status="not_found",
                              error="Job not found",
                              request_id=generate_id())
        self._audit("inspect_job", actor_id, job_id, True)
        return APIResponse(ok=True, status="success",
                          data=job.to_dict(),
                          request_id=generate_id())

    def cancel_job(self, *, grant_id: str, actor_id: str, job_id: str) -> APIResponse:
        """Cancel a job."""
        if not self._check_permission(grant_id, "cancel_job", job_id):
            denial = self._authority.record_denial(
                reason_code="missing_authority",
                actor_id=actor_id,
                requested_action="cancel_job",
                requested_target=job_id,
            )
            return APIResponse(ok=False, status="denied",
                              data={"denial": denial.to_dict()},
                              error="missing_authority",
                              request_id=generate_id())
        try:
            job = self._job_store.cancel_job(job_id)
            self._audit("cancel_job", actor_id, job_id, True)
            return APIResponse(ok=True, status="success",
                              data=job.to_dict(),
                              request_id=generate_id())
        except Exception as e:
            return APIResponse(ok=False, status="error",
                              error=str(e), request_id=generate_id())

    def retry_job(self, *, grant_id: str, actor_id: str, job_id: str) -> APIResponse:
        """Retry a failed job."""
        if not self._check_permission(grant_id, "submit_job", job_id):
            return APIResponse(ok=False, status="denied",
                              error="missing_authority",
                              request_id=generate_id())
        job = self._job_store.get_job(job_id)
        if job is None:
            return APIResponse(ok=False, status="not_found", request_id=generate_id())
        try:
            job = self._job_store.transition(job_id, "pending")
            self._audit("retry_job", actor_id, job_id, True)
            return APIResponse(ok=True, status="success",
                              data=job.to_dict(),
                              request_id=generate_id())
        except Exception as e:
            return APIResponse(ok=False, status="error",
                              error=str(e), request_id=generate_id())

    def list_schedules(self, *, grant_id: str, actor_id: str) -> APIResponse:
        """List schedules. Read authorization required (gap 9)."""
        if not self._check_permission(grant_id, "read", "default"):
            return self._deny("list_schedules", actor_id, "schedules")
        self._audit("list_schedules", actor_id, "schedules", True)
        return APIResponse(ok=True, status="success",
                          data={"schedules": {k: v.__dict__ for k, v in self._scheduler.schedules.items()}},
                          request_id=generate_id())

    def list_workers(self, *, grant_id: str, actor_id: str) -> APIResponse:
        """List workers. Read authorization required (gap 9)."""
        if not self._check_permission(grant_id, "read", "default"):
            return self._deny("list_workers", actor_id, "workers")
        self._audit("list_workers", actor_id, "workers", True)
        return APIResponse(ok=True, status="success",
                          data={"workers": {k: v.__dict__ for k, v in self._worker_protocol.workers.items()}},
                          request_id=generate_id())

    def system_state(self, *, grant_id: str, actor_id: str) -> APIResponse:
        """System state endpoint. Read authorization required (gap 9)."""
        if not self._check_permission(grant_id, "read", "default"):
            return self._deny("system_state", actor_id, "system")
        health = self._health.check_health()
        self._audit("system_state", actor_id, "system", True)
        return APIResponse(ok=True, status="success",
                          data={
                              "health": health.to_dict(),
                              "total_jobs": len(self._job_store.all_jobs),
                              "total_schedules": len(self._scheduler.schedules),
                              "total_workers": len(self._worker_protocol.workers),
                          },
                          request_id=generate_id())

    def audit_history(self, *, grant_id: str, actor_id: str) -> APIResponse:
        """Audit history. Read authorization required (gap 9)."""
        if not self._check_permission(grant_id, "read", "default"):
            return self._deny("audit_history", actor_id, "audit")
        self._audit("audit_history", actor_id, "audit", True)
        return APIResponse(ok=True, status="success",
                          data={"audit_log": self._audit_log},
                          request_id=generate_id())

    @property
    def audit_log(self) -> list:
        return list(self._audit_log)
