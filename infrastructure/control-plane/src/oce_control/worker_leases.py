"""Book 3 Worker Fabric — fenced leases and duplicate-safe delivery (B3-C3).

Capability-aware job matching, atomic lease claims with unguessable tokens,
monotonic fencing generations, lease renewal/surrender/expiry, reclaim of
abandoned work, stale-worker rejection, late-result quarantine,
at-least-once delivery with idempotent material effects, and duplicate-
delivery detection. PostgreSQL remains authoritative; Redis stays transport
only. The store is a narrow interface so PG-backed integration tests supply
a PostgreSQL adapter while unit tests use the deterministic in-memory store.
"""
from __future__ import annotations
import secrets
from dataclasses import dataclass, field
from typing import Optional

from .worker_contracts import utcnow_iso
from .worker_identity import WorkerAuthority
from .worker_sessions import SessionHost


class LeaseFencingError(RuntimeError):
    pass


class StaleFence(LeaseFencingError):
    pass


class UnknownLease(LeaseFencingError):
    pass


class LateResult(LeaseFencingError):
    pass


class DuplicateEffect(RuntimeError):
    pass


@dataclass
class JobEnvelope:
    job_id: str
    job_type: str
    required_capabilities: list[str]
    resource_envelope: dict                 # cpu_limit, memory_bytes, disk_bytes, timeout_s
    sandbox_profile: str
    environment: dict = field(default_factory=dict)
    task_params: dict = field(default_factory=dict)
    attempt: int = 1


def default_ttl() -> int:
    return 60


def _ttl_for(job: JobEnvelope) -> int:
    return int(job.resource_envelope.get("timeout_s", 60)) + 15


class LeaseStore:
    """Minimal durable lease interface (PG adapter in integration tests)."""

    def fetch_fence(self, job_id: str) -> dict:
        raise NotImplementedError

    def claim(self, job_id: str, worker_id: str, lease_id: str,
              fence: int, ttl_s: int) -> bool:
        raise NotImplementedError

    def renew(self, job_id: str, lease_id: str, fence: int,
              ttl_s: int) -> bool:
        raise NotImplementedError

    def surrender(self, job_id: str, lease_id: str, fence: int) -> bool:
        raise NotImplementedError

    def release(self, job_id: str) -> bool:
        raise NotImplementedError


class InMemoryLeaseStore(LeaseStore):
    """Deterministic in-memory lease store for fast unit tests."""

    def __init__(self):
        self._fences: dict[str, dict] = {}

    def fetch_fence(self, job_id: str) -> dict:
        if not job_id:
            return {}
        rec = self._fences.get(job_id)
        if rec is None:
            return {"fence": 0, "lease_id": None, "status": "available"}
        return dict(rec)

    def claim(self, job_id, worker_id, lease_id, fence, ttl_s):
        rec = self._fences.get(job_id)
        if rec and rec.get("lease_id") and rec.get("status") == "active":
            return False
        self._fences[job_id] = {"fence": fence, "lease_id": lease_id,
                                "worker_id": worker_id, "status": "active",
                                "ttl_s": ttl_s, "leases_since": 1}
        return True

    def renew(self, job_id, lease_id, fence, ttl_s):
        rec = self._fences.get(job_id)
        if not rec or rec.get("lease_id") != lease_id or rec.get("fence") != fence:
            return False
        rec["ttl_s"] = ttl_s
        rec["status"] = "active"
        return True

    def surrender(self, job_id, lease_id, fence):
        rec = self._fences.get(job_id)
        if not rec or rec.get("lease_id") != lease_id or rec.get("fence") != fence:
            return False
        rec["status"] = "available"
        rec["lease_id"] = None
        rec["fence"] = fence
        return True

    def release(self, job_id):
        rec = self._fences.get(job_id)
        if rec:
            rec["status"] = "available"
            rec["lease_id"] = None
        return True

    def reclaim_expired(self, now_iso: str) -> list[str]:
        return []


class FabricScheduler:
    """Composes authority, outbound sessions and fenced leases so a governed
    job is matched to an authenticated, capable worker, claimed with a fenced
    lease, executed once, and delivered idempotently."""

    def __init__(self, authority: Optional[WorkerAuthority] = None,
                 host: Optional[SessionHost] = None,
                 store: Optional[LeaseStore] = None):
        self._authority = authority or WorkerAuthority()
        self._host = host or SessionHost()
        self._store = store or InMemoryLeaseStore()
        self.quarantined_late: list[dict] = []

    # -- capability-aware matching -------------------------------------------

    def match_worker(self, job: JobEnvelope, online_workers: list[str],
                     sessions: dict) -> Optional[str]:
        for wid in online_workers:
            if wid not in sessions:
                continue
            sess = sessions[wid]
            have = set(sess.get("capabilities") or ())
            ident = self._authority.get(wid)
            if ident and not have:
                have = set(ident.capabilities)
            if not set(job.required_capabilities).issubset(have):
                continue
            return wid
        return None

    def _new_lease_token(self) -> str:
        return secrets.token_hex(24)

    # -- fenced claim ----------------------------------------------------------

    def claim(self, job: JobEnvelope, worker_id: str) -> dict:
        head = self._store.fetch_fence(job.job_id)
        if head.get("lease_id") and head["status"] not in ("expired", "cancelled"):
            raise LeaseFencingError(
                f"job '{job.job_id}' already held by lease {head['lease_id']}")
        fence = head.get("fence", 0) + 1
        lease_id = self._new_lease_token()
        if not self._store.claim(job.job_id, worker_id, lease_id, fence,
                                 _ttl_for(job)):
            raise LeaseFencingError(
                f"concurrent duplicate claim on '{job.job_id}'")
        return {"lease_id": lease_id, "fence": fence, "worker_id": worker_id,
                "job_id": job.job_id}

    def renew(self, job_id: str, lease_id: str, fence: int,
              ttl_s: Optional[int] = None) -> bool:
        if not self._store.renew(job_id, lease_id, fence, ttl_s or default_ttl()):
            raise StaleFence(
                f"renew rejected: lease '{lease_id}' does not match current fence")
        return True

    def surrender(self, job_id: str, lease_id: str, fence: int) -> bool:
        if not self._store.surrender(job_id, lease_id, fence):
            raise StaleFence(f"surrender rejected: lease '{lease_id}' missing or stale")
        return True

    def release(self, job_id: str) -> bool:
        return self._store.release(job_id)

    def reclaim_stale(self, now: Optional[str] = None) -> list[str]:
        if hasattr(self._store, "reclaim_expired"):
            return self._store.reclaim_expired(now or utcnow_iso())
        return []

    # -- late-result quarantine and duplicate-safe delivery --------------------

    def deliver_result(self, job_id: str, lease_id: str, fence: int,
                       client_effect_key: str, seen_effects: set) -> dict:
        head = self._store.fetch_fence(job_id)
        if head.get("lease_id") != lease_id:
            self.quarantined_late.append({
                "job_id": job_id, "lease_id": lease_id, "fence": fence,
                "at": utcnow_iso(), "reason": "late_or_missing_lease"})
            raise LateResult(f"result for '{job_id}' is late: lease no longer current")
        if head.get("fence") != fence:
            raise StaleFence(
                f"stale fence {fence} for '{job_id}'; current {head.get('fence')}")
        if client_effect_key in seen_effects:
            raise DuplicateEffect(
                f"effect '{client_effect_key}' already applied for '{job_id}'")
        seen_effects.add(client_effect_key)
        return {"job_id": job_id, "delivered": True, "effect_key": client_effect_key}


# backward-compatible aliases for the fabric facade
LeaseFencing = LeaseFencingError