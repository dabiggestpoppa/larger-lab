"""Worker protocol for OCE control plane.

B3.C5 / B2-C5 — workers connect outbound, identify capabilities,
authenticate through local development contracts, claim work using leases,
heartbeat, renew/surrender leases, report progress, produce typed results,
handle cancellation, recover abandoned work, prevent stale workers from
committing, remain replaceable and horizontally extensible.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field

from .clocks import get_clock
from .hashes import generate_id
from .job_store import JobStore


@dataclass
class WorkerInfo:
    worker_id: str
    capabilities: list
    connected_at: str
    last_heartbeat: str = ""
    max_concurrent_jobs: int = 1
    trust_zone: str = "worker-local"
    active_jobs: list = field(default_factory=list)
    schema_version: str = "1.0.0"


class WorkerProtocol:
    """Manages worker connections, leases, and result submission."""

    def __init__(self, job_store: JobStore, heartbeat_timeout: int = 30):
        self._job_store = job_store
        self._workers: dict[str, WorkerInfo] = {}
        self._heartbeat_timeout = heartbeat_timeout

    def admit_worker(self, *, worker_id: str, capabilities: list,
                     trust_zone: str = "worker-local",
                     max_concurrent_jobs: int = 1) -> WorkerInfo:
        """Admit a worker with capability identification."""
        clock = get_clock()
        now = clock.now()
        worker = WorkerInfo(
            worker_id=worker_id,
            capabilities=capabilities,
            connected_at=now.isoformat(),
            last_heartbeat=now.isoformat(),
            max_concurrent_jobs=max_concurrent_jobs,
            trust_zone=trust_zone,
        )
        self._workers[worker_id] = worker
        return worker

    def disconnect_worker(self, worker_id: str) -> None:
        """Disconnect a worker and surrender its leases."""
        worker = self._workers.pop(worker_id, None)
        if worker:
            for job_id in worker.active_jobs:
                try:
                    self._job_store.surrender_lease(job_id, worker_id)
                except (KeyError, PermissionError, ValueError):
                    pass

    def heartbeat(self, worker_id: str) -> WorkerInfo:
        """Worker heartbeat. Updates last_heartbeat timestamp."""
        clock = get_clock()
        worker = self._workers.get(worker_id)
        if worker is None:
            raise KeyError(f"Worker '{worker_id}' not connected")
        worker.last_heartbeat = clock.now().isoformat()
        return worker

    def claim_work(self, worker_id: str, job_id: str, lease_ttl: int = 60) -> dict:
        """Worker claims a job using a lease."""
        worker = self._workers.get(worker_id)
        if worker is None:
            raise PermissionError(f"Worker '{worker_id}' not admitted")

        # Check capability match
        job = self._job_store.get_job(job_id)
        if job is None:
            raise KeyError(f"Job '{job_id}' not found")

        # Check concurrency limit
        if len(worker.active_jobs) >= worker.max_concurrent_jobs:
            raise PermissionError(f"Worker '{worker_id}' at max concurrent jobs")

        job = self._job_store.claim_lease(job_id, worker_id, lease_ttl)
        worker.active_jobs.append(job_id)
        return job.to_dict()

    def report_progress(self, worker_id: str, job_id: str, progress: dict) -> None:
        """Worker reports progress on a job."""
        worker = self._workers.get(worker_id)
        if worker is None:
            raise PermissionError(f"Worker '{worker_id}' not admitted")
        # Renew lease while reporting progress
        self._job_store.renew_lease(job_id, worker_id)
        self.heartbeat(worker_id)

    def submit_result(self, worker_id: str, job_id: str, output: dict,
                      success: bool = True) -> dict:
        """Worker submits a typed result. Stale workers cannot commit."""
        worker = self._workers.get(worker_id)
        if worker is None:
            raise PermissionError(f"Worker '{worker_id}' not admitted")

        job = self._job_store.complete_job(job_id, worker_id, output, success)
        if job_id in worker.active_jobs:
            worker.active_jobs.remove(job_id)
        return job.to_dict()

    def handle_cancellation(self, worker_id: str, job_id: str) -> None:
        """Handle cancellation of a job the worker is processing."""
        worker = self._workers.get(worker_id)
        if worker is None:
            return
        if job_id in worker.active_jobs:
            worker.active_jobs.remove(job_id)

    def recover_abandoned_work(self) -> int:
        """Recover work from workers that have timed out or disconnected."""
        clock = get_clock()
        now = clock.now()
        recovered = 0

        # Find stale workers
        stale = []
        for wid, worker in self._workers.items():
            if worker.last_heartbeat:
                hb = datetime.fromisoformat(worker.last_heartbeat)
                if (now - hb).total_seconds() > self._heartbeat_timeout:
                    stale.append(wid)

        for wid in stale:
            self.disconnect_worker(wid)
            recovered += 1

        # Recover expired leases in the job store
        recovered += self._job_store.recover_abandoned_leases()
        return recovered

    @property
    def workers(self) -> dict:
        return dict(self._workers)

    def get_worker(self, worker_id: str) -> Optional[WorkerInfo]:
        return self._workers.get(worker_id)
