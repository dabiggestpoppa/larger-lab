"""PostgreSQL-backed authoritative job store (B2-R2).

Same surface as the in-memory JobStore, but every write lands in
PostgreSQL inside a transaction. Idempotency is enforced by the
idempotency table's primary key plus a full-tuple unique index: an exact
replay returns the existing job; a key reuse with a different
actor/action/target/job-type/payload-hash fails closed.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Any, Optional

from .clocks import get_clock
from .hashes import generate_id, generate_idempotency_key, generate_correlation_id, payload_hash
from .state_machines import assert_transition
from .job_store import JobEnvelope


class IdempotencyConflict(Exception):
    """Same idempotency key used with a different request identity."""

    def __init__(self, key: str):
        super().__init__(
            f"idempotency key '{key[:8]}…' reused with different "
            f"actor/action/target/job-type/payload — rejected"
        )
        self.key = key


class PgStoreUnavailable(RuntimeError):
    """PostgreSQL is unreachable — the durable path fails closed."""


class PgJobStore:
    """Authoritative PostgreSQL job store. Requires a live connection."""

    def __init__(self, conn, authority=None):
        self._conn = conn
        self._authority = authority

    # -- helpers ------------------------------------------------------------

    def _execute(self, sql: str, params: tuple = ()) -> list[tuple]:
        try:
            with self._conn.cursor() as cur:
                cur.execute(sql, params)
                if cur.description:
                    return cur.fetchall()
                return []
        except Exception:
            self._conn.rollback()
            raise

    def _one(self, sql: str, params: tuple = ()) -> Optional[tuple]:
        rows = self._execute(sql, params)
        return rows[0] if rows else None

    @staticmethod
    def _row_to_job(row: tuple) -> JobEnvelope:
        (job_id, job_type, schema_version, submitting_actor, authority_context,
         resource_scope, environment, priority, idempotency_key, payload_hash,
         payload, created_at, scheduled_at, attempt_number, retry_policy,
         timeout_seconds, correlation_id, parent_job_id, status, result,
         failure_envelope, evidence_refs) = row
        return JobEnvelope(
            job_id=job_id, job_type=job_type, schema_version=schema_version,
            submitting_actor=submitting_actor,
            authority_context=authority_context or {},
            resource_scope=resource_scope, environment=environment,
            priority=priority, idempotency_key=idempotency_key,
            payload_hash=payload_hash, payload=payload or {},
            created_at=created_at.isoformat() if isinstance(created_at, datetime) else str(created_at or ""),
            scheduled_at=scheduled_at.isoformat() if isinstance(scheduled_at, datetime) else str(scheduled_at or ""),
            attempt_number=attempt_number,
            retry_policy=retry_policy or {},
            timeout=timeout_seconds,
            correlation_id=correlation_id, parent_job_id=parent_job_id,
            status=status, result=result or {},
            failure_envelope=failure_envelope or {},
            evidence_refs=evidence_refs or [],
        )

    # -- submission ----------------------------------------------------------

    def submit_job(self, *, job_type: str, submitting_actor: str,
                   grant_id: str, payload: dict, resource_scope: str = "default",
                   environment: str = "local", priority: str = "normal",
                   idempotency_key: Optional[str] = None,
                   scheduled_at: Optional[str] = None,
                   parent_job_id: Optional[str] = None,
                   timeout: int = 300,
                   retry_policy: Optional[dict] = None,
                   schema_version: str = "2.0.0") -> JobEnvelope:
        clock = get_clock()
        now = clock.now()
        if idempotency_key is None:
            idempotency_key = generate_idempotency_key()
        p_hash = payload_hash(payload)
        job_id = generate_id()
        correlation_id = generate_correlation_id()
        authority_context = {
            "grant_id": grant_id, "actor_id": submitting_actor,
            "action": "submit_job", "target": resource_scope,
            "environment": environment,
        }

        try:
            with self._conn.cursor() as cur:
                # Exact replay? Same key + same request identity -> return existing.
                cur.execute(
                    """SELECT j.* FROM idempotency i
                       JOIN jobs j ON j.job_id = i.job_id
                       WHERE i.idempotency_key = %s
                         AND i.actor_id = %s AND i.action = 'submit_job'
                         AND i.target = %s AND i.job_type = %s
                         AND i.payload_hash = %s""",
                    (idempotency_key, submitting_actor, resource_scope,
                     job_type, p_hash),
                )
                row = cur.fetchone()
                if row:
                    self._conn.rollback()
                    return self._row_to_job(row)

                # Key used with a DIFFERENT identity -> conflict, fail closed.
                cur.execute(
                    "SELECT job_id FROM idempotency WHERE idempotency_key = %s",
                    (idempotency_key,),
                )
                if cur.fetchone():
                    self._conn.rollback()
                    raise IdempotencyConflict(idempotency_key)

                cur.execute(
                    """INSERT INTO jobs (job_id, job_type, schema_version,
                         submitting_actor, authority_context, resource_scope,
                         environment, priority, idempotency_key, payload_hash,
                         payload, created_at, scheduled_at, attempt_number,
                         retry_policy, timeout_seconds, correlation_id,
                         parent_job_id, status)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0,%s,%s,%s,%s,'pending')""",
                    (job_id, job_type, schema_version, submitting_actor,
                     __import__("json").dumps(authority_context), resource_scope,
                     environment, priority, idempotency_key, p_hash,
                     __import__("json").dumps(payload), now,
                     scheduled_at or now,
                     __import__("json").dumps(retry_policy or {"max_attempts": 3, "backoff_strategy": "exponential"}),
                     timeout, correlation_id, parent_job_id),
                )
                cur.execute(
                    """INSERT INTO idempotency (idempotency_key, actor_id, action,
                         target, job_type, payload_hash, job_id)
                       VALUES (%s,%s,'submit_job',%s,%s,%s,%s)""",
                    (idempotency_key, submitting_actor, resource_scope,
                     job_type, p_hash, job_id),
                )
                cur.execute(
                    """INSERT INTO job_transitions (job_id, from_state, to_state, actor_id)
                       VALUES (%s,'', 'pending', %s)""",
                    (job_id, submitting_actor),
                )
            self._conn.commit()
        except IdempotencyConflict:
            raise
        except Exception as exc:
            try:
                self._conn.rollback()
            except Exception:
                pass
            raise PgStoreUnavailable(f"job insert failed: {exc}") from exc

        job = self.get_job(job_id)
        if job is None:
            raise PgStoreUnavailable("job vanished after insert")
        return job

    # -- reads ---------------------------------------------------------------

    def get_job(self, job_id: str) -> Optional[JobEnvelope]:
        row = self._one("SELECT * FROM jobs WHERE job_id = %s", (job_id,))
        return self._row_to_job(row) if row else None
    def get_by_idempotency_key(self, key: str) -> Optional[JobEnvelope]:
        row = self._one(
            "SELECT j.* FROM idempotency i JOIN jobs j ON j.job_id = i.job_id WHERE i.idempotency_key = %s",
            (key,),
        )
        return self._row_to_job(row) if row else None

    @property
    def all_jobs(self) -> dict:
        rows = self._execute("SELECT * FROM jobs")
        return {r[0]: self._row_to_job(r) for r in rows}

    def jobs_by_status(self, status: str) -> list[JobEnvelope]:
        rows = self._execute("SELECT * FROM jobs WHERE status = %s", (status,))
        return [self._row_to_job(r) for r in rows]

    def jobs_by_correlation(self, correlation_id: str) -> list[JobEnvelope]:
        rows = self._execute("SELECT * FROM jobs WHERE correlation_id = %s", (correlation_id,))
        return [self._row_to_job(r) for r in rows]

    def transition(self, job_id: str, to_state: str, actor_id: str = "") -> JobEnvelope:
        job = self.get_job(job_id)
        if job is None:
            raise KeyError(f"Job '{job_id}' not found")
        assert_transition("job", job.status, to_state)
        clock = get_clock()
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "UPDATE jobs SET status = %s, updated_at = %s WHERE job_id = %s AND status = %s",
                    (to_state, clock.now(), job_id, job.status),
                )
                if cur.rowcount != 1:
                    raise PgStoreUnavailable(f"concurrent modification on job '{job_id}'")
                cur.execute(
                    "INSERT INTO job_transitions (job_id, from_state, to_state, actor_id) VALUES (%s,%s,%s,%s)",
                    (job_id, job.status, to_state, actor_id),
                )
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        return self.get_job(job_id)  # type: ignore[return-value]

    def claim_lease(self, job_id: str, worker_id: str, lease_ttl: int = 60) -> JobEnvelope:
        """Transactional lease acquisition: atomic INSERT on the leases PK."""
        clock = get_clock()
        now = clock.now()
        expires = now + timedelta(seconds=lease_ttl)
        lease_id = generate_id()
        job = self.get_job(job_id)
        if job is None:
            raise KeyError(f"Job '{job_id}' not found")
        if job.status not in ("pending", "scheduled"):
            raise ValueError(f"Job '{job_id}' in state '{job.status}' cannot be leased")
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO leases (job_id, lease_id, worker_id, leased_at, expires_at, heartbeat_at) VALUES (%s,%s,%s,%s,%s,%s)",
                    (job_id, lease_id, worker_id, now, expires, now),
                )
                cur.execute(
                    "UPDATE jobs SET status = 'leased', updated_at = %s WHERE job_id = %s AND status IN ('pending','scheduled')",
                    (now, job_id),
                )
                if cur.rowcount != 1:
                    raise PgStoreUnavailable(f"job '{job_id}' no longer claimable")
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        return self.get_job(job_id)  # type: ignore[return-value]

    def renew_lease(self, job_id: str, lease_id: str, lease_ttl: int = 60) -> JobEnvelope:
        """Renew requires the lease TOKEN (fencing), not just the worker id."""
        clock = get_clock()
        now = clock.now()
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "UPDATE leases SET expires_at = %s, heartbeat_at = %s WHERE job_id = %s AND lease_id = %s AND expires_at > %s",
                    (now + timedelta(seconds=lease_ttl), now, job_id, lease_id, now),
                )
                if cur.rowcount != 1:
                    raise PermissionError(f"lease '{lease_id}' invalid or expired for job '{job_id}'")
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        return self.get_job(job_id)  # type: ignore[return-value]

    def heartbeat_lease(self, job_id: str, lease_id: str) -> None:
        self.renew_lease(job_id, lease_id, lease_ttl=30)

    def surrender_lease(self, job_id: str, lease_id: str, worker_id: str) -> JobEnvelope:
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM leases WHERE job_id = %s AND lease_id = %s AND worker_id = %s",
                    (job_id, lease_id, worker_id),
                )
                if cur.rowcount != 1:
                    raise PermissionError("lease token mismatch - cannot surrender")
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        return self.transition(job_id, "pending")

    def is_lease_expired(self, job_id: str) -> bool:
        row = self._one("SELECT expires_at FROM leases WHERE job_id = %s", (job_id,))
        if row is None:
            return False
        return get_clock().now() > row[0]

    def authoritative_lease(self, job_id: str) -> Optional[dict]:
        """Authoritative lease row for a job. PostgreSQL is truth; Redis
        only mirrors this (B2-R3). Returns None when no lease exists."""
        row = self._one(
            "SELECT lease_id, worker_id, expires_at FROM leases WHERE job_id = %s",
            (job_id,),
        )
        if row is None:
            return None
        lease_id, worker_id, expires_at = row
        return {"job_id": job_id, "lease_id": lease_id,
                "worker_id": worker_id, "expires_at": expires_at}

    def active_leases(self) -> list[dict]:
        """All non-expired leases, for Redis mirror reconstruction (B2-R3)."""
        now = get_clock().now()
        rows = self._execute(
            "SELECT job_id, lease_id, worker_id, expires_at FROM leases WHERE expires_at > %s",
            (now,),
        )
        out = []
        for job_id, lease_id, worker_id, expires_at in rows:
            ttl = max(1, int((expires_at - now).total_seconds()))
            out.append({"job_id": job_id, "lease_id": lease_id,
                        "worker_id": worker_id, "ttl_seconds": ttl})
        return out

    def recover_abandoned_leases(self) -> int:
        """Expire leases past due; retry or fail the job per its policy."""
        clock = get_clock()
        now = clock.now()
        count = 0
        rows = self._execute(
            "SELECT l.job_id, j.attempt_number, j.retry_policy FROM leases l JOIN jobs j ON j.job_id = l.job_id WHERE l.expires_at < %s",
            (now,),
        )
        for job_id, attempt_number, retry_policy in rows:
            max_attempts = (retry_policy or {}).get("max_attempts", 3)
            try:
                with self._conn.cursor() as cur:
                    cur.execute("DELETE FROM leases WHERE job_id = %s", (job_id,))
                    if attempt_number >= max_attempts:
                        cur.execute(
                            "UPDATE jobs SET status='failed', updated_at=%s, failure_envelope=%s WHERE job_id=%s AND status IN ('leased','running')",
                            (now, __import__("json").dumps({"error_type": "lease_expired", "error_message": "Lease expired after %d attempts" % attempt_number, "failed_at": now.isoformat(), "retryable": False}), job_id),
                        )
                    else:
                        cur.execute(
                            "UPDATE jobs SET status='pending', updated_at=%s, attempt_number = attempt_number + 1 WHERE job_id=%s AND status IN ('leased','running')",
                            (now, job_id),
                        )
                self._conn.commit()
                count += 1
            except Exception:
                self._conn.rollback()
        return count

    def complete_job(self, job_id: str, lease_id: str, worker_id: str, output: dict, success: bool = True) -> JobEnvelope:
        """Commit requires the lease TOKEN. Stale/expired leases are fenced."""
        clock = get_clock()
        now = clock.now()
        job = self.get_job(job_id)
        if job is None:
            raise KeyError("Job not found")
        row = self._one(
            "SELECT worker_id, expires_at FROM leases WHERE job_id = %s AND lease_id = %s",
            (job_id, lease_id),
        )
        if row is None or row[0] != worker_id:
            raise PermissionError("stale or no lease - fenced")
        if now > row[1]:
            raise PermissionError("stale worker cannot commit - lease expired")
        try:
            with self._conn.cursor() as cur:
                if success:
                    cur.execute(
                        "UPDATE jobs SET status='succeeded', updated_at=%s, result=%s, failure_envelope=NULL WHERE job_id=%s AND status IN ('leased','running')",
                        (now, __import__("json").dumps({"success": True, "output_hash": payload_hash(output), "completed_at": now.isoformat(), "worker_id": worker_id}), job_id),
                    )
                else:
                    cur.execute(
                        "UPDATE jobs SET status='failed', updated_at=%s, failure_envelope=%s, result=NULL WHERE job_id=%s AND status IN ('leased','running')",
                        (now, __import__("json").dumps({"error_type": "execution_failed", "error_message": str(output.get("error", "unknown")), "failed_at": now.isoformat(), "retryable": job.attempt_number < (job.retry_policy or {}).get("max_attempts", 3)}), job_id),
                    )
                if cur.rowcount != 1:
                    raise PgStoreUnavailable("job '%s' not in a committable state" % job_id)
                cur.execute("DELETE FROM leases WHERE job_id = %s", (job_id,))
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        return self.get_job(job_id)  # type: ignore[return-value]

    def cancel_job(self, job_id: str) -> JobEnvelope:
        job = self.get_job(job_id)
        if job is None:
            raise KeyError("Job not found")
        assert_transition("job", job.status, "cancelled")
        try:
            with self._conn.cursor() as cur:
                cur.execute("DELETE FROM leases WHERE job_id = %s", (job_id,))
                cur.execute(
                    "UPDATE jobs SET status='cancelled', updated_at=%s WHERE job_id=%s AND status = %s",
                    (clock.now(), job_id, job.status),
                )
                if cur.rowcount != 1:
                    raise PgStoreUnavailable("concurrent modification")
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        return self.get_job(job_id)  # type: ignore[return-value]

    def quarantine_job(self, job_id: str, reason: str) -> JobEnvelope:
        job = self.get_job(job_id)
        if job is None:
            raise KeyError("Job not found")
        if job.status not in ("running", "failed", "pending"):
            return job
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "UPDATE jobs SET status='quarantined', updated_at=%s, failure_envelope=%s WHERE job_id=%s",
                    (clock.now(), __import__("json").dumps({"error_type": "quarantined", "error_message": reason, "failed_at": clock.now().isoformat(), "retryable": True}), job_id),
                )
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        return self.get_job(job_id)  # type: ignore[return-value]
