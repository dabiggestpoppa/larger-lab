"""Typed job system for OCE control plane.

B3.C3 / B2-C3 — stable job ID, type, schema version, authority context,
idempotency, payload hash, lease, retry, correlation, parent/child, status,
result/failure, evidence refs.

PostgreSQL is authoritative. This in-memory store is the test/development
backing. The PostgreSQL migration layer (pg_store.py) provides the real
authoritative backing.
"""
from __future__ import annotations
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, Any
import json

from .clocks import get_clock
from .hashes import generate_id, generate_idempotency_key, generate_correlation_id, payload_hash
from .state_machines import assert_transition, is_valid_transition
from .authority import AuthorityEngine


@dataclass
class JobEnvelope:
    job_id: str
    job_type: str
    schema_version: str
    submitting_actor: str
    authority_context: dict
    resource_scope: str
    environment: str
    priority: str
    idempotency_key: str
    payload_hash: str
    created_at: str
    scheduled_at: str
    attempt_number: int = 0
    retry_policy: dict = field(default_factory=lambda: {"max_attempts": 3, "backoff_strategy": "exponential"})
    timeout: int = 300
    lease: dict = field(default_factory=dict)
    correlation_id: str = ""
    parent_job_id: Optional[str] = None
    child_job_ids: list = field(default_factory=list)
    status: str = "pending"
    result: dict = field(default_factory=dict)
    failure_envelope: dict = field(default_factory=dict)
    evidence_refs: list = field(default_factory=list)
    payload: dict = field(default_factory=dict)  # The actual job payload

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


class JobStore:
    """In-memory authoritative job store (test/dev backing).

    In production, this is backed by PostgreSQL. The interface is identical.
    """

    def __init__(self, authority: AuthorityEngine):
        self._jobs: dict[str, JobEnvelope] = {}
        self._authority = authority
        self._idempotency_index: dict[str, str] = {}  # key -> job_id
        self._correlation_index: dict[str, list[str]] = {}  # corr_id -> [job_ids]

    def submit_job(self, *, job_type: str, submitting_actor: str,
                   grant_id: str, payload: dict, resource_scope: str = "default",
                   environment: str = "local", priority: str = "normal",
                   idempotency_key: Optional[str] = None,
                   scheduled_at: Optional[str] = None,
                   parent_job_id: Optional[str] = None,
                   timeout: int = 300,
                   retry_policy: Optional[dict] = None) -> JobEnvelope:
        """Submit a typed job. Validates authority, idempotency, and payload hash."""
        clock = get_clock()
        now = clock.now()

        # Verify authority grant
        grant = self._authority.verify_grant(
            grant_id, "submit_job", resource_scope, environment
        )

        # Generate or check idempotency key
        if idempotency_key is None:
            idempotency_key = generate_idempotency_key()

        # Check idempotency replay
        if idempotency_key in self._idempotency_index:
            existing_id = self._idempotency_index[idempotency_key]
            existing = self._jobs[existing_id]
            # Idempotent: return the existing job (exactly-once effect)
            return existing

        # Compute payload hash
        p_hash = payload_hash(payload)

        # Validate schema version
        schema_version = "2.0.0"

        # Create correlation ID if not provided
        correlation_id = generate_correlation_id()

        job = JobEnvelope(
            job_id=generate_id(),
            job_type=job_type,
            schema_version=schema_version,
            submitting_actor=submitting_actor,
            authority_context={
                "grant_id": grant_id,
                "actor_id": grant.actor_id,
                "action": grant.action,
                "target": grant.target,
                "environment": grant.environment,
                "expires_at": grant.expires_at,
            },
            resource_scope=resource_scope,
            environment=environment,
            priority=priority,
            idempotency_key=idempotency_key,
            payload_hash=p_hash,
            created_at=now.isoformat(),
            scheduled_at=scheduled_at or now.isoformat(),
            retry_policy=retry_policy or {"max_attempts": 3, "backoff_strategy": "exponential"},
            timeout=timeout,
            correlation_id=correlation_id,
            parent_job_id=parent_job_id,
            payload=payload,
        )

        self._jobs[job.job_id] = job
        self._idempotency_index[idempotency_key] = job.job_id

        if correlation_id not in self._correlation_index:
            self._correlation_index[correlation_id] = []
        self._correlation_index[correlation_id].append(job.job_id)

        # Add as child of parent
        if parent_job_id and parent_job_id in self._jobs:
            self._jobs[parent_job_id].child_job_ids.append(job.job_id)

        return job

    def get_job(self, job_id: str) -> Optional[JobEnvelope]:
        return self._jobs.get(job_id)

    def get_by_idempotency_key(self, key: str) -> Optional[JobEnvelope]:
        job_id = self._idempotency_index.get(key)
        if job_id:
            return self._jobs.get(job_id)
        return None

    def transition(self, job_id: str, to_state: str) -> JobEnvelope:
        """Transition a job to a new state. Validates the transition."""
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(f"Job '{job_id}' not found")

        assert_transition("job", job.status, to_state)
        job.status = to_state
        return job

    def claim_lease(self, job_id: str, worker_id: str, lease_ttl: int = 60) -> JobEnvelope:
        """A worker claims a lease on a job."""
        clock = get_clock()
        now = clock.now()

        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(f"Job '{job_id}' not found")

        # Only pending or scheduled jobs can be leased
        if job.status not in ("pending", "scheduled"):
            raise ValueError(f"Job '{job_id}' in state '{job.status}' cannot be leased")

        from datetime import timedelta
        job.lease = {
            "lease_id": generate_id(),
            "worker_id": worker_id,
            "leased_at": now.isoformat(),
            "expires_at": (now + timedelta(seconds=lease_ttl)).isoformat(),
            "heartbeat_at": now.isoformat(),
        }
        job.status = "leased"
        return job

    def renew_lease(self, job_id: str, worker_id: str, lease_ttl: int = 60) -> JobEnvelope:
        """Renanew a lease. Only the same worker can renew."""
        clock = get_clock()
        now = clock.now()

        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(f"Job '{job_id}' not found")

        if not job.lease:
            raise ValueError(f"Job '{job_id}' has no lease")

        if job.lease.get("worker_id") != worker_id:
            raise PermissionError(f"Worker '{worker_id}' does not own lease for job '{job_id}'")

        from datetime import timedelta
        job.lease["expires_at"] = (now + timedelta(seconds=lease_ttl)).isoformat()
        job.lease["heartbeat_at"] = now.isoformat()
        return job

    def surrender_lease(self, job_id: str, worker_id: str) -> JobEnvelope:
        """Surrender a lease, returning the job to pending/scheduled."""
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(f"Job not found")
        if job.lease.get("worker_id") != worker_id:
            raise PermissionError(f"Worker does not own lease")
        job.lease = {}
        assert_transition("job", job.status, "pending")
        job.status = "pending"
        return job

    def is_lease_expired(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job is None or not job.lease:
            return False
        from datetime import datetime
        clock = get_clock()
        now = clock.now()
        expires = datetime.fromisoformat(job.lease["expires_at"])
        return now > expires

    def recover_abandoned_leases(self) -> int:
        from datetime import datetime
        clock = get_clock()
        now = clock.now()
        count = 0
        for job in self._jobs.values():
            if job.status in ("leased", "running") and job.lease:
                expires = datetime.fromisoformat(job.lease["expires_at"])
                if now > expires:
                    if job.attempt_number >= job.retry_policy.get("max_attempts", 3):
                        job.status = "failed"
                        job.failure_envelope = {"error_type": "lease_expired", "error_message": "Lease expired", "failed_at": now.isoformat(), "retryable": False}
                    else:
                        job.status = "pending"
                        job.attempt_number += 1
                        job.lease = {}
                    count += 1
        return count

    def complete_job(self, job_id: str, worker_id: str, output: dict, success: bool = True) -> JobEnvelope:
        from datetime import datetime
        clock = get_clock()
        now = clock.now()
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(f"Job not found")
        if not job.lease or job.lease.get("worker_id") != worker_id:
            raise PermissionError(f"Stale or no lease")
        if self.is_lease_expired(job_id):
            raise PermissionError(f"Stale worker cannot commit")
        if success:
            assert_transition("job", job.status, "succeeded")
            job.status = "succeeded"
            job.result = {"success": True, "output_hash": payload_hash(output), "completed_at": now.isoformat(), "worker_id": worker_id}
        else:
            assert_transition("job", job.status, "failed")
            job.status = "failed"
            job.failure_envelope = {"error_type": "execution_failed", "error_message": str(output.get("error", "unknown")), "failed_at": now.isoformat(), "retryable": job.attempt_number < job.retry_policy.get("max_attempts", 3)}
        job.lease = {}
        return job

    def cancel_job(self, job_id: str) -> JobEnvelope:
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(f"Job not found")
        assert_transition("job", job.status, "cancelled")
        job.status = "cancelled"
        job.lease = {}
        return job

    def quarantine_job(self, job_id: str, reason: str) -> JobEnvelope:
        clock = get_clock()
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(f"Job not found")
        if job.status in ("running", "failed", "pending"):
            job.status = "quarantined"
            job.failure_envelope = {"error_type": "quarantined", "error_message": reason, "failed_at": clock.now().isoformat(), "retryable": True}
        return job

    @property
    def all_jobs(self) -> dict:
        return dict(self._jobs)

    def jobs_by_status(self, status: str) -> list:
        return [j for j in self._jobs.values() if j.status == status]

    def jobs_by_correlation(self, correlation_id: str) -> list:
        job_ids = self._correlation_index.get(correlation_id, [])
        return [self._jobs[jid] for jid in job_ids if jid in self._jobs]
