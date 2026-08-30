"""PostgreSQL-backed worker protocol (B2-R4).

Closes audit gaps 10 and 11 for the durable path:
- Gap 10: admission requires a signed token; only its SHA-256 hash is
  stored (workers table). Re-admission with a different token fails.
  Revoked workers are refused at every action.
- Gap 11: claims enforce the job's `required_capabilities` against the
  worker's declared capabilities; lacking workers are denied.
- Lease identity: renew/commit require the lease TOKEN (fencing), not
  just the worker id — matching PgJobStore's lease table.

The in-memory WorkerProtocol remains the fast unit-test model; this is
the authoritative PostgreSQL path (runtime-contract `worker` section).
"""
from __future__ import annotations
import hashlib
import json
from typing import Optional

from .clocks import get_clock
from .pg_store import PgJobStore, PgStoreUnavailable
from .schema_validator import validate


def hash_admission_token(token: str) -> str:
    """SHA-256 of the admission token. Only the hash is ever persisted."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def capabilities_satisfied(required: list, have: list) -> bool:
    """True when the worker's declared capabilities cover every required one."""
    return set(required or []).issubset(set(have or []))


_WORKER_MANIFEST_SCHEMA = None


def _manifest_schema() -> dict:
    global _WORKER_MANIFEST_SCHEMA
    if _WORKER_MANIFEST_SCHEMA is None:
        import json as _json
        from pathlib import Path
        schema_path = (Path(__file__).resolve().parent.parent.parent
                       / "contracts" / "worker-capability-manifest.schema.json")
        _WORKER_MANIFEST_SCHEMA = _json.loads(schema_path.read_text(encoding="utf-8"))
    return _WORKER_MANIFEST_SCHEMA


def validate_capability_manifest(manifest: dict) -> tuple[bool, list[str]]:
    """Validate a capability manifest against the frozen contract schema."""
    return validate(manifest, _manifest_schema())


class PgWorkerProtocol:
    """Authoritative PostgreSQL worker protocol (B2-R4)."""

    def __init__(self, pg_store: PgJobStore, conn, heartbeat_timeout: int = 30):
        self._pg_store = pg_store
        self._conn = conn
        self._heartbeat_timeout = heartbeat_timeout
        # worker_id -> {job_id: lease_id} — lease tokens held by live workers
        self._leases: dict[str, dict[str, str]] = {}

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

    def _active_claim_count(self, worker_id: str) -> int:
        row = self._one(
            "SELECT COUNT(*) FROM leases WHERE worker_id = %s", (worker_id,))
        return row[0] if row else 0

    # -- admission (audit gap 10) ---------------------------------------------

    def admit_worker(self, *, worker_id: str, token: str, capabilities: list,
                     trust_zone: str = "worker-local",
                     max_concurrent_jobs: int = 1) -> dict:
        """Admit a worker. Token is REQUIRED; only its hash is stored.

        Re-admission with the same token is idempotent (refreshes the
        worker row). A different token for an existing worker is denied.
        """
        if not token:
            raise PermissionError("worker admission requires a token")
        manifest = {
            "worker_id": worker_id,
            "capabilities": capabilities,
            "trust_zone": trust_zone,
            "connected_at": get_clock().now().isoformat(),
            "schema_version": "1.0.0",
            "max_concurrent_jobs": max_concurrent_jobs,
        }
        ok, errors = validate_capability_manifest(manifest)
        if not ok:
            raise PermissionError(
                f"invalid capability manifest: {'; '.join(errors[:3])}")
        token_hash = hash_admission_token(token)
        clock = get_clock()
        now = clock.now()
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "SELECT admission_token_hash, revoked_at FROM workers WHERE worker_id = %s",
                    (worker_id,),
                )
                row = cur.fetchone()
                if row is not None:
                    stored_hash, revoked_at = row
                    if revoked_at is not None:
                        raise PermissionError(
                            f"worker '{worker_id}' is revoked and cannot be re-admitted")
                    if stored_hash != token_hash:
                        raise PermissionError(
                            f"worker '{worker_id}' already admitted with a different token")
                    cur.execute(
                        "UPDATE workers SET capabilities=%s, trust_zone=%s, "
                        "max_concurrent_jobs=%s, connected_at=%s, last_heartbeat=%s "
                        "WHERE worker_id=%s",
                        (json.dumps(capabilities), trust_zone, max_concurrent_jobs,
                         now, now, worker_id),
                    )
                else:
                    cur.execute(
                        "INSERT INTO workers (worker_id, capabilities, trust_zone, "
                        "admission_token_hash, max_concurrent_jobs, connected_at, "
                        "last_heartbeat) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (worker_id, json.dumps(capabilities), trust_zone, token_hash,
                         max_concurrent_jobs, now, now),
                    )
            self._conn.commit()
        except PermissionError:
            self._conn.rollback()
            raise
        except Exception as exc:
            self._conn.rollback()
            raise PgStoreUnavailable(f"worker admit failed: {exc}") from exc
        return self.worker_status(worker_id)

    def authenticate(self, worker_id: str, token: str) -> dict:
        """Verify a worker's token against the stored hash. Raises on failure."""
        if not token:
            raise PermissionError("worker authentication requires a token")
        row = self._one(
            "SELECT admission_token_hash, revoked_at FROM workers WHERE worker_id = %s",
            (worker_id,),
        )
        if row is None:
            raise PermissionError(f"worker '{worker_id}' not admitted")
        stored_hash, revoked_at = row
        if revoked_at is not None:
            raise PermissionError(f"worker '{worker_id}' is revoked")
        if stored_hash != hash_admission_token(token):
            raise PermissionError(f"worker '{worker_id}' authentication failed")
        return self.worker_status(worker_id)

    def worker_status(self, worker_id: str) -> Optional[dict]:
        row = self._one(
            "SELECT worker_id, capabilities, trust_zone, max_concurrent_jobs, "
            "connected_at, last_heartbeat, revoked_at FROM workers WHERE worker_id = %s",
            (worker_id,),
        )
        if row is None:
            return None
        wid, caps, tz, mcc, connected, hb, revoked = row
        return {
            "worker_id": wid,
            "capabilities": caps or [],
            "trust_zone": tz,
            "max_concurrent_jobs": mcc,
            "connected_at": connected.isoformat() if connected else "",
            "last_heartbeat": hb.isoformat() if hb else "",
            "revoked_at": revoked.isoformat() if revoked else None,
        }

    def revoke_worker(self, worker_id: str) -> None:
        """Revoke a worker: release its leases, then mark revoked."""
        rows = self._execute(
            "SELECT job_id FROM leases WHERE worker_id = %s", (worker_id,))
        for (job_id,) in rows:
            auth = self._pg_store.authoritative_lease(job_id)
            if auth:
                try:
                    self._pg_store.surrender_lease(
                        job_id, auth["lease_id"], worker_id)
                except Exception:
                    pass
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "UPDATE workers SET revoked_at = %s WHERE worker_id = %s",
                    (get_clock().now(), worker_id),
                )
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    # -- claims and lease fencing (audit gap 11) --------------------------------

    def claim_work(self, worker_id: str, token: str, job_id: str,
                   lease_ttl: int = 60) -> dict:
        """Claim a job. Authenticates, enforces required capabilities, then
        takes a transactional PG lease. Returns the lease TOKEN for fencing."""
        status = self.authenticate(worker_id, token)
        job = self._pg_store.get_job(job_id)
        if job is None:
            raise KeyError(f"Job '{job_id}' not found")
        required = job.required_capabilities or []
        if not capabilities_satisfied(required, status["capabilities"]):
            raise PermissionError(
                f"worker '{worker_id}' lacks required capabilities "
                f"{sorted(required)} for job '{job_id}'")
        if self._active_claim_count(worker_id) >= status["max_concurrent_jobs"]:
            raise PermissionError(
                f"worker '{worker_id}' at max concurrent jobs "
                f"({status['max_concurrent_jobs']})")
        self._pg_store.claim_lease(job_id, worker_id, lease_ttl)
        auth = self._pg_store.authoritative_lease(job_id)
        lease_id = auth["lease_id"] if auth else ""
        self._leases.setdefault(worker_id, {})[job_id] = lease_id
        claimed = self._pg_store.get_job(job_id)
        return {"job": claimed.to_dict(), "lease_id": lease_id}

    def _lease_token(self, worker_id: str, job_id: str) -> str:
        lease_id = self._leases.get(worker_id, {}).get(job_id)
        if not lease_id:
            raise PermissionError(
                f"worker '{worker_id}' holds no lease for job '{job_id}'")
        return lease_id

    def renew_lease(self, worker_id: str, token: str, job_id: str,
                    lease_ttl: int = 60) -> dict:
        self.authenticate(worker_id, token)
        lease_id = self._lease_token(worker_id, job_id)
        job = self._pg_store.renew_lease(job_id, lease_id, lease_ttl)
        return job.to_dict()

    def heartbeat(self, worker_id: str, token: str) -> dict:
        self.authenticate(worker_id, token)
        try:
            with self._conn.cursor() as cur:
                cur.execute(
                    "UPDATE workers SET last_heartbeat = %s WHERE worker_id = %s",
                    (get_clock().now(), worker_id),
                )
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        return self.worker_status(worker_id)

    def submit_result(self, worker_id: str, token: str, job_id: str,
                      output: dict, success: bool = True) -> dict:
        """Commit requires the lease TOKEN. Stale/expired leases are fenced."""
        self.authenticate(worker_id, token)
        lease_id = self._lease_token(worker_id, job_id)
        done = self._pg_store.complete_job(job_id, lease_id, worker_id,
                                           output, success)
        self._leases.get(worker_id, {}).pop(job_id, None)
        return done.to_dict()

    def surrender_lease(self, worker_id: str, token: str, job_id: str) -> dict:
        self.authenticate(worker_id, token)
        lease_id = self._lease_token(worker_id, job_id)
        job = self._pg_store.surrender_lease(job_id, lease_id, worker_id)
        self._leases.get(worker_id, {}).pop(job_id, None)
        return job.to_dict()

    # -- recovery ---------------------------------------------------------------

    def recover_abandoned_work(self) -> int:
        """Expire past-due PG leases; retry or fail the job per its policy."""
        return self._pg_store.recover_abandoned_leases()

    @property
    def workers(self) -> dict:
        rows = self._execute(
            "SELECT worker_id FROM workers WHERE revoked_at IS NULL")
        out = {}
        for (wid,) in rows:
            st = self.worker_status(wid)
            if st:
                out[wid] = st
        return out
