"""Health and readiness for OCE control plane.

B3.C5.S1 — separate process liveness, dependency readiness, capability
readiness, and safe-to-operate state. False-green and partial-dependency
tests return DEGRADED/BLOCKED.
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field, asdict
import json

from .clocks import get_clock


@dataclass
class HealthStatus:
    overall: str = "healthy"  # healthy, degraded, blocked, down
    postgresql: str = "up"    # up, down, degraded
    redis: str = "up"
    scheduler: str = "running"  # running, stopped, degraded
    workers: int = 0
    active_jobs: int = 0
    pending_jobs: int = 0
    failed_jobs: int = 0
    quarantined_jobs: int = 0
    timestamp: str = ""
    blockers: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class HealthService:
    """Health and readiness probes."""

    def __init__(self, job_store=None, scheduler=None, worker_protocol=None):
        self._job_store = job_store
        self._scheduler = scheduler
        self._worker_protocol = worker_protocol
        self._pg_available = True
        self._redis_available = True

    def set_pg_available(self, available: bool) -> None:
        self._pg_available = available

    def set_redis_available(self, available: bool) -> None:
        self._redis_available = available

    def check_health(self) -> HealthStatus:
        """Check full health. Returns DEGRADED/BLOCKED for partial states."""
        clock = get_clock()
        status = HealthStatus(timestamp=clock.now().isoformat())

        # PostgreSQL is authoritative — if down, we're blocked
        if not self._pg_available:
            status.postgresql = "down"
            status.overall = "blocked"
            status.blockers.append("postgresql_unavailable")
        else:
            status.postgresql = "up"

        # Redis is transient — if down, we're degraded but not blocked
        if not self._redis_available:
            status.redis = "down"
            if status.overall == "healthy":
                status.overall = "degraded"
            status.blockers.append("redis_unavailable_non_authoritative")

        # Job stats
        if self._job_store:
            status.active_jobs = len(self._job_store.jobs_by_status("running")) + \
                                 len(self._job_store.jobs_by_status("leased"))
            status.pending_jobs = len(self._job_store.jobs_by_status("pending"))
            status.failed_jobs = len(self._job_store.jobs_by_status("failed"))
            status.quarantined_jobs = len(self._job_store.jobs_by_status("quarantined"))

        # Worker count
        if self._worker_protocol:
            status.workers = len(self._worker_protocol.workers)

        # Scheduler
        if self._scheduler:
            status.scheduler = "running"
        else:
            status.scheduler = "stopped"
            if status.overall == "healthy":
                status.overall = "degraded"

        return status

    def check_readiness(self) -> tuple[bool, str]:
        """Check if the system is ready to operate."""
        status = self.check_health()
        if status.overall == "blocked":
            return (False, f"Blocked: {', '.join(status.blockers)}")
        if status.overall == "down":
            return (False, f"Down: {', '.join(status.blockers)}")
        return (True, "ready")
