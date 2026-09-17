"""Durable job queue with lease semantics (P2-C03; Book V 13.6, directive §21-22).

Lease law (directive §22):

- a worker leases a READY step; only the current lease token may ack;
- two workers can never both own a lease (token-replacing UPDATE guarded by
  SQL predicate + uniqueness of claims inside one transaction);
- expired leases are recoverable by anyone;
- priority and not-before scheduling are honored, but priority never bypasses
  policy prerequisites (Book V 13.6 invariant 6) — the queue only surfaces
  steps whose state is READY.
"""

from __future__ import annotations

import secrets
import sqlite3
from dataclasses import dataclass
from typing import Iterable, List, Optional

from qcae.core.errors import QcaeValidationError
from qcae.core.jobs import deterministic_job_id  # re-export convenience
from qcae.orchestration.jobs.runtime import (
    LeaseInfo,
    RuntimeStep,
    RuntimeStepStatus,
)

__all__ = ["StepLease", "SqliteStepQueue", "QUEUE_INTEGRITY_DDL"]


@dataclass(frozen=True)
class StepLease:
    """A claimed step handed to exactly one worker."""

    step_id: str
    job_id: str
    lease_token: str
    lease_owner: str
    lease_expires_at: str


QUEUE_INTEGRITY_DDL = """
CREATE TABLE IF NOT EXISTS runtime_queue_claim (
    step_id           TEXT PRIMARY KEY,
    job_id            TEXT NOT NULL,
    lease_owner       TEXT NOT NULL,
    lease_token       TEXT NOT NULL,
    leased_at         TEXT NOT NULL,
    lease_expires_at  TEXT NOT NULL,
    acknowledged      INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_queue_claim_expiry
    ON runtime_queue_claim(lease_expires_at);
"""


class SqliteStepQueue:
    """Lease-based claim layer over the runtime_step table."""

    def __init__(self, conn: sqlite3.Connection, runtime_store, *, now_fn, lease_ttl_seconds: int = 300) -> None:
        self._conn = conn
        self._store = runtime_store
        self._now = now_fn
        self._ttl = lease_ttl_seconds

    def _expires_at(self) -> str:
        """Expiry derived from the injected clock so tests/recovery agree."""
        from datetime import datetime, timedelta, timezone

        dt = datetime.strptime(self._now(), "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        ) + timedelta(seconds=self._ttl)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def enqueue_ready_step(self, step: RuntimeStep, *, not_before: str = "") -> None:
        """Mark a step READY (queue entry) with optional delayed availability."""
        if step.status is not RuntimeStepStatus.READY:
            raise QcaeValidationError(
                f"only READY steps are enqueued, got {step.status.value}"
            )
        self._store.update_step(step, not_before=not_before)

    def _not_before_passed(self, nb: str) -> bool:
        return (not nb) or (nb <= self._now())

    def claim_next(
        self,
        worker_id: str,
        *,
        step_types: Optional[List[str]] = None,
        priority_hint: bool = False,
        eligible_step_ids: Optional[Iterable[str]] = None,
        job_id: Optional[str] = None,
        now: Optional[str] = None,
    ) -> Optional[StepLease]:
        """Lease the next READY, unclaimed (or expired-claim) step.

        Eligibility is enforced *inside* the atomic claim selection (P2-C07R1,
        repair directive §2.1): a worker never obtains ownership of an
        ineligible step merely to discover afterward that it was ineligible.

        ``job_id`` restricts the claim to one job's steps; ``eligible_step_ids``
        restricts it to an explicit candidate set (empty set => nothing to
        claim, no claim rows created); ``now`` overrides the queue clock for
        the caller that already holds a consistent timestamp. Candidates are
        attempted in order and the guarded UPDATE is the single arbitration
        point, so two concurrent claimers can never both own a step
        (directive §22; Book V 13.6) and a lost race falls through to the next
        eligible candidate instead of stranding it.
        """
        if eligible_step_ids is not None:
            eligible = list(eligible_step_ids)
            if not eligible:
                return None  # invalid/empty eligibility: no claim rows, ever
        else:
            eligible = None

        params: List[object] = [RuntimeStepStatus.READY.value]
        eligibility_sql = ""
        if job_id is not None:
            eligibility_sql += " AND s.job_id = ?"
            params.append(job_id)
        if eligible is not None:
            placeholders = ",".join("?" for _ in eligible)
            eligibility_sql += f" AND s.step_id IN ({placeholders})"
            params.extend(eligible)

        now = now or self._now()
        rows = self._conn.execute(
            "SELECT s.step_id, s.job_id, c.lease_token, c.lease_expires_at,"
            " s.not_before"
            " FROM runtime_step s"
            " LEFT JOIN runtime_queue_claim c ON c.step_id = s.step_id"
            " WHERE s.status = ?" + eligibility_sql +
            " ORDER BY s.not_before ASC, s.step_id ASC",
            params,
        ).fetchall()

        for r in rows:
            step_id, step_job_id, claim_token, claim_expiry, s_nb = r
            if step_types and self._store.get_step(step_id).step_type not in step_types:
                continue
            if not self._not_before_passed(s_nb):
                continue
            # Active unexpired, unacknowledged claim blocks a new owner.
            if claim_token and claim_expiry > now and not self._acknowledged(step_id):
                continue
            token = f"lease-{secrets.token_hex(12)}"
            expires = self._expires_at()
            cur = self._conn.execute(
                "INSERT INTO runtime_queue_claim (step_id, job_id, lease_owner,"
                " lease_token, leased_at, lease_expires_at, acknowledged)"
                " VALUES (?, ?, ?, ?, ?, ?, 0)"
                " ON CONFLICT(step_id) DO UPDATE SET"
                " lease_owner=excluded.lease_owner, lease_token=excluded.lease_token,"
                " leased_at=excluded.leased_at, lease_expires_at=excluded.lease_expires_at,"
                " acknowledged=0"
                " WHERE runtime_queue_claim.acknowledged = 1"
                "    OR runtime_queue_claim.lease_expires_at <= ?",
                (step_id, step_job_id, worker_id, token, now, expires, now),
            )
            if cur.rowcount != 1:
                # Lost the race for THIS candidate (another claimer won between
                # selection and claim) — fall through to the next candidate.
                continue

            step = self._store.get_step(step_id)
            leased = _with_lease(step, LeaseInfo(
                lease_owner=worker_id, lease_token=token,
                leased_at=now, lease_expires_at=expires,
            ))
            self._store.update_step(
                leased, lease_owner=worker_id, lease_token=token, lease_expires_at=expires
            )
            return StepLease(
                step_id=step_id, job_id=step_job_id, lease_token=token,
                lease_owner=worker_id, lease_expires_at=expires,
            )
        return None

    def _acknowledged(self, step_id: str) -> bool:
        row = self._conn.execute(
            "SELECT acknowledged FROM runtime_queue_claim WHERE step_id = ?",
            (step_id,),
        ).fetchone()
        return bool(row and row[0])

    def acknowledge(self, step_id: str, lease_token: str) -> None:
        """Finalize a completed step; only the lease owner may ack."""
        row = self._conn.execute(
            "SELECT lease_token, acknowledged FROM runtime_queue_claim WHERE step_id = ?",
            (step_id,),
        ).fetchone()
        if row is None:
            raise QcaeValidationError(f"step {step_id!r} has no active claim")
        if row[0] != lease_token:
            raise QcaeValidationError(
                f"lease token mismatch for step {step_id!r}: caller is not the owner"
            )
        if row[1]:
            raise QcaeValidationError(f"step {step_id!r} claim already acknowledged")
        self._conn.execute(
            "UPDATE runtime_queue_claim SET acknowledged = 1 WHERE step_id = ?",
            (step_id,),
        )

    def release(self, step_id: str, lease_token: str, *, back_to: RuntimeStepStatus) -> None:
        """Release a lease without completing the step (crash/cancel path)."""
        row = self._conn.execute(
            "SELECT lease_token FROM runtime_queue_claim WHERE step_id = ?",
            (step_id,),
        ).fetchone()
        if row is None or row[0] != lease_token:
            raise QcaeValidationError(
                f"lease token mismatch for step {step_id!r}: caller is not the owner"
            )
        self._conn.execute(
            "DELETE FROM runtime_queue_claim WHERE step_id = ?", (step_id,)
        )
        step = self._store.get_step(step_id)
        self._store.update_step(step, lease_owner="", lease_token="", lease_expires_at="")

    def expire_stale_leases(self, job_id: Optional[str] = None) -> List[str]:
        """Release TTL-expired claims; returns expired step ids (P2-R3-C03).

        This is the ONLY recovery expiry path: it checks the TTL, so an
        active lease is never stolen. ``job_id`` scopes the release to one
        job's claims (job-scoped recovery must not touch other jobs).
        Callers MUST reconcile the returned steps through
        ``OrchestratorEngine.recover_leased_steps`` — a claim deletion
        alone leaves the durable step RUNNING (that is exactly the
        recovery-surface split this method exists to end).
        """
        now = self._now()
        if job_id is not None:
            rows = self._conn.execute(
                "SELECT step_id FROM runtime_queue_claim"
                " WHERE acknowledged = 0 AND lease_expires_at <= ? AND job_id = ?",
                (now, job_id),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT step_id FROM runtime_queue_claim"
                " WHERE acknowledged = 0 AND lease_expires_at <= ?",
                (now,),
            ).fetchall()
        recovered: List[str] = []
        for (step_id,) in rows:
            self._conn.execute(
                "DELETE FROM runtime_queue_claim WHERE step_id = ?", (step_id,)
            )
            step = self._store.get_step(step_id)
            # RUNNING -> READY only via expiry; state stays RUNNING until the
            # recovery driver moves it (directive §23: restart resumes B safely).
            recovered.append(step_id)
        return recovered

    def expire_stale_leases_for(self, step_ids) -> List[str]:
        """Force-release claim rows for specific steps (retry/recovery path).

        The steps' lease columns are cleared by the caller first; this only
        removes the queue claim so a new lease can be taken immediately
        instead of waiting for TTL expiry.
        """
        released: List[str] = []
        for step_id in step_ids:
            cur = self._conn.execute(
                "DELETE FROM runtime_queue_claim WHERE step_id = ?", (step_id,)
            )
            if cur.rowcount:
                released.append(step_id)
        return released

    def lease_owner_of(self, step_id: str) -> Optional[str]:
        row = self._conn.execute(
            "SELECT lease_owner FROM runtime_queue_claim WHERE step_id = ?",
            (step_id,),
        ).fetchone()
        return row[0] if row else None

    def has_active_claim(self, step_id: str) -> bool:
        row = self._conn.execute(
            "SELECT lease_expires_at, acknowledged FROM runtime_queue_claim"
            " WHERE step_id = ?",
            (step_id,),
        ).fetchone()
        if row is None:
            return False
        return row[1] == 0 and row[0] > self._now()


def _with_lease(step: RuntimeStep, lease: LeaseInfo) -> RuntimeStep:
    from dataclasses import replace as dc_replace

    return dc_replace(step, lease=lease)
