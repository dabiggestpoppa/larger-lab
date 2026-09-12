"""Redis-backed disposable transport (B2-R3).

Redis is TRANSPORT ONLY: job notifications, worker coordination, leases
(short-TTL duplicates of the authoritative row), heartbeats, rate
limiting, ephemeral cache, invalidation, scheduler wakeups.

Redis is NEVER sole durable truth. Every projection here is
reconstructable from PostgreSQL via `reconstruct_from_pg`. On
Redis/PostgreSQL disagreement, PostgreSQL wins and conflicting Redis
state is quarantined.
"""
from __future__ import annotations
import json
from typing import Any, Optional

try:
    import redis as redis_lib
except ImportError:  # pragma: no cover
    redis_lib = None  # type: ignore[assignment]

from .clocks import get_clock

# Redis key namespace (all keys prefixed so a shared instance stays clean)
K_NOTIFY = "b2:notify:{queue}"          # job notification list (LPUSH/BRPOP)
K_LEASE = "b2:lease:{job_id}"           # short-TTL lease mirror
K_HEARTBEAT = "b2:hb:{worker_id}"       # worker heartbeat
K_RATE = "b2:rate:{actor_id}"           # rate limiting counter
K_CACHE = "b2:cache:{key}"              # ephemeral cache
K_SCHED_WAKE = "b2:sched:wake"          # scheduler wakeup channel
K_QUARANTINE = "b2:quarantine"          # conflicting Redis state quarantine

# Lease mirror keys live under this prefix (used for PG reconciliation).
_LEASE_PREFIX = "b2:lease:"


class RedisUnavailable(RuntimeError):
    """Redis is unreachable — transport degrades but PG truth persists."""


class RedisTransport:
    """Disposable Redis transport. Requires a live Redis connection."""

    def __init__(self, url: str, namespace_tenant: str = "default"):
        if redis_lib is None:
            raise RedisUnavailable("redis-py not installed")
        try:
            self._r = redis_lib.Redis.from_url(url, decode_responses=True,
                                               socket_connect_timeout=2,
                                               socket_timeout=2)
            self._r.ping()
        except Exception as exc:
            raise RedisUnavailable(f"redis connect failed: {exc}") from exc
        self._tenant = namespace_tenant

    # -- job notification ----------------------------------------------------

    def notify_job(self, job_id: str, queue: str = "default") -> int:
        """Push a job notification. Returns queue length after push."""
        try:
            return self._r.lpush(K_NOTIFY.format(queue=queue), job_id)
        except Exception as exc:
            raise RedisUnavailable(f"notify failed: {exc}") from exc

    def receive_job(self, queue: str = "default", timeout_s: int = 0) -> Optional[str]:
        """Pop a job notification (BRPOP with optional block)."""
        try:
            if timeout_s > 0:
                # BRPOP returns a (queue, value) tuple
                item = self._r.brpop(K_NOTIFY.format(queue=queue), timeout=timeout_s)
                return item[1] if item else None
            # RPOP returns the value string directly
            return self._r.rpop(K_NOTIFY.format(queue=queue))
        except Exception as exc:
            raise RedisUnavailable(f"receive failed: {exc}") from exc

    def queue_depth(self, queue: str = "default") -> int:
        try:
            return self._r.llen(K_NOTIFY.format(queue=queue))
        except Exception as exc:
            raise RedisUnavailable(f"depth failed: {exc}") from exc

    def drain_queue(self, queue: str = "default") -> list[str]:
        """Drain all pending notifications (duplicate-delivery testing)."""
        out = []
        while True:
            jid = self.receive_job(queue)
            if jid is None:
                return out
            out.append(jid)

    # -- lease mirror (short TTL; authoritative row lives in PG) -------------

    def mirror_lease(self, job_id: str, lease_id: str, worker_id: str,
                     ttl_seconds: int) -> bool:
        """Mirror a PG lease into Redis with a matching TTL. Fails if the
        key already exists (duplicate lease prevention at transport level)."""
        try:
            key = K_LEASE.format(job_id=job_id)
            val = json.dumps({"lease_id": lease_id, "worker_id": worker_id})
            return bool(self._r.set(key, val, nx=True, ex=ttl_seconds))
        except Exception as exc:
            raise RedisUnavailable(f"mirror_lease failed: {exc}") from exc

    def read_lease(self, job_id: str) -> Optional[dict]:
        try:
            val = self._r.get(K_LEASE.format(job_id=job_id))
            return json.loads(val) if val else None
        except Exception as exc:
            raise RedisUnavailable(f"read_lease failed: {exc}") from exc

    def clear_lease(self, job_id: str) -> int:
        try:
            return self._r.delete(K_LEASE.format(job_id=job_id))
        except Exception as exc:
            raise RedisUnavailable(f"clear_lease failed: {exc}") from exc

    # -- worker heartbeats ----------------------------------------------------

    def heartbeat(self, worker_id: str, ttl_seconds: int = 30) -> bool:
        try:
            return bool(self._r.set(K_HEARTBEAT.format(worker_id=worker_id),
                                    get_clock().isoformat(), ex=ttl_seconds))
        except Exception as exc:
            raise RedisUnavailable(f"heartbeat failed: {exc}") from exc

    def worker_alive(self, worker_id: str) -> bool:
        try:
            return self._r.exists(K_HEARTBEAT.format(worker_id=worker_id)) > 0
        except Exception as exc:
            raise RedisUnavailable(f"worker_alive failed: {exc}") from exc

    # -- rate limiting ---------------------------------------------------------

    def rate_check(self, actor_id: str, limit: int, window_s: int = 60) -> bool:
        """Sliding-window-ish counter. True if within limit."""
        try:
            key = K_RATE.format(actor_id=actor_id)
            pipe = self._r.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_s)
            count = pipe.execute()[0]
            return int(count) <= limit
        except Exception as exc:
            raise RedisUnavailable(f"rate_check failed: {exc}") from exc

    # -- ephemeral cache ---------------------------------------------------------

    def cache_set(self, key: str, value: Any, ttl_seconds: int = 60) -> bool:
        try:
            return bool(self._r.set(K_CACHE.format(key=key),
                                    json.dumps(value), ex=ttl_seconds))
        except Exception as exc:
            raise RedisUnavailable(f"cache_set failed: {exc}") from exc

    def cache_get(self, key: str) -> Optional[Any]:
        try:
            val = self._r.get(K_CACHE.format(key=key))
            return json.loads(val) if val else None
        except Exception as exc:
            raise RedisUnavailable(f"cache_get failed: {exc}") from exc

    def cache_invalidate(self, key: str) -> int:
        try:
            return self._r.delete(K_CACHE.format(key=key))
        except Exception as exc:
            raise RedisUnavailable(f"cache_invalidate failed: {exc}") from exc

    # -- scheduler wakeups ---------------------------------------------------------

    def wake_scheduler(self) -> int:
        try:
            return self._r.publish(K_SCHED_WAKE, get_clock().isoformat())
        except Exception as exc:
            raise RedisUnavailable(f"wake failed: {exc}") from exc

    # -- quarantine ----------------------------------------------------------------

    def quarantine(self, key: str, value: Any, reason: str) -> int:
        """Record Redis state that conflicts with PG truth before it is
        overwritten. Returns the quarantine list length after append."""
        try:
            record = {"key": key, "value": value, "reason": reason,
                      "at": get_clock().isoformat()}
            return self._r.rpush(K_QUARANTINE, json.dumps(record))
        except Exception as exc:
            raise RedisUnavailable(f"quarantine failed: {exc}") from exc

    def quarantined_records(self, limit: int = 100) -> list[dict]:
        """Read quarantine records (oldest first)."""
        try:
            items = self._r.lrange(K_QUARANTINE, 0, limit - 1)
            return [json.loads(i) for i in items if i]
        except Exception as exc:
            raise RedisUnavailable(f"quarantine read failed: {exc}") from exc

    # -- reconstruction and reconciliation ------------------------------------------

    def reconstruct_from_pg(self, pg_store) -> dict:
        """Rebuild Redis projections from authoritative PostgreSQL state.

        Returns a receipt describing what was rebuilt. Redis is wiped
        (this namespace only) and repopulated: pending job notifications,
        active lease mirrors. Worker heartbeats are NOT restored — workers
        must re-heartbeat against PG truth. Pre-existing lease mirrors that
        disagree with PG are quarantined before being overwritten.
        """
        receipt = {"rebuilt": True, "notifications": 0, "leases": 0,
                   "quarantined": 0, "pg_authoritative": True}
        try:
            # Quarantine lease mirrors that disagree with PG, then wipe the
            # B2 namespace (disposable by definition).
            for key in self._r.scan_iter("b2:*"):
                if key.startswith(_LEASE_PREFIX):
                    raw = self._r.get(key)
                    if raw:
                        job_id = key[len(_LEASE_PREFIX):]
                        mirror = json.loads(raw)
                        auth = pg_store.authoritative_lease(job_id)
                        if auth is None or auth["lease_id"] != mirror.get("lease_id"):
                            self.quarantine(key, mirror, "lease_mirror_disagrees_with_pg")
                            receipt["quarantined"] += 1
                self._r.delete(key)

            # Repopulate notifications for pending jobs
            for job in pg_store.jobs_by_status("pending"):
                self._r.lpush(K_NOTIFY.format(queue="default"), job.job_id)
                receipt["notifications"] += 1

            # Repopulate lease mirrors for active (non-expired) PG leases
            for lease in pg_store.active_leases():
                key = K_LEASE.format(job_id=lease["job_id"])
                val = json.dumps({"lease_id": lease["lease_id"],
                                  "worker_id": lease["worker_id"]})
                self._r.set(key, val, ex=lease["ttl_seconds"])
                receipt["leases"] += 1

            # Heartbeats are intentionally not restored: disposable transport,
            # workers must re-heartbeat against authoritative PG state.
            receipt["heartbeats_restored"] = 0
            return receipt
        except Exception as exc:  # fail closed: report, never half-rebuild
            receipt["rebuilt"] = False
            receipt["error"] = str(exc)
            return receipt
