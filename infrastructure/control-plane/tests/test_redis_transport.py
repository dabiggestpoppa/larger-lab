"""B2-R3: Redis transport tests.

Unit tests run anywhere against a stubbed Redis client (no server
needed). Container-backed integration tests are mandatory in CI (real
Redis + PostgreSQL via the B2 compose stack) and skip truthfully when
Docker is absent.

Proves: notification queues, lease mirrors (NX + TTL), worker
heartbeats, rate limiting, ephemeral cache, scheduler wakeups,
quarantine, and full reconstruction of Redis projections from
authoritative PostgreSQL.
"""
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))
sys.path.insert(0, str(BASE / "tests"))

import oce_b2_compose as oc
from oce_control import redis_transport as rt
from oce_control.redis_transport import RedisTransport, RedisUnavailable


# ---------------------------------------------------------------------------
# Stub Redis (decode_responses semantics; unit tests need no server)
# ---------------------------------------------------------------------------

class _FakePipeline:
    def __init__(self, r):
        self._r = r
        self._cmds = []

    def incr(self, key):
        self._cmds.append(("incr", key))
        return self

    def expire(self, key, ttl):
        self._cmds.append(("expire", key, ttl))
        return self

    def execute(self):
        out = []
        for cmd in self._cmds:
            if cmd[0] == "incr":
                out.append(self._r.incr(cmd[1]))
            elif cmd[0] == "expire":
                out.append(self._r.expire(cmd[1], cmd[2]))
        return out


class _FakeRedis:
    """Minimal in-memory Redis with decode_responses semantics."""

    def __init__(self):
        self._data = {}
        self._lists = {}

    def ping(self):
        return True

    # strings
    def set(self, key, value, nx=False, ex=None):
        if nx and key in self._data:
            return None
        self._data[key] = value
        return True

    def get(self, key):
        return self._data.get(key)

    def delete(self, *keys):
        n = 0
        for k in keys:
            if k in self._data:
                del self._data[k]
                n += 1
            if k in self._lists:
                del self._lists[k]
                n += 1
        return n

    def exists(self, key):
        return 1 if (key in self._data or key in self._lists) else 0

    def incr(self, key):
        cur = int(self._data.get(key, 0))
        self._data[key] = str(cur + 1)
        return cur + 1

    def expire(self, key, ttl):
        return 1 if (key in self._data or key in self._lists) else 0

    def pipeline(self):
        return _FakePipeline(self)

    def publish(self, channel, message):
        return 0

    # lists
    def lpush(self, key, *values):
        lst = self._lists.setdefault(key, [])
        for v in values:
            lst.insert(0, v)
        return len(lst)

    def rpush(self, key, *values):
        lst = self._lists.setdefault(key, [])
        lst.extend(values)
        return len(lst)

    def rpop(self, key):
        lst = self._lists.get(key)
        if not lst:
            return None
        return lst.pop()

    def brpop(self, key, timeout=0):
        lst = self._lists.get(key)
        if lst:
            return (key, lst.pop())
        return None

    def llen(self, key):
        return len(self._lists.get(key, []))

    def lrange(self, key, start, stop):
        lst = self._lists.get(key, [])
        if stop < 0:
            return lst[start:]
        return lst[start:stop + 1]

    def scan_iter(self, pattern):
        import fnmatch
        for k in list(self._data) + [k for k in self._lists]:
            if fnmatch.fnmatch(k, pattern):
                yield k


@pytest.fixture
def transport(monkeypatch):
    """RedisTransport wired to a fresh in-memory stub."""
    fake = _FakeRedis()

    class _FakeModule:
        class Redis:
            @staticmethod
            def from_url(url, **kwargs):
                return fake

    monkeypatch.setattr(rt, "redis_lib", _FakeModule)
    return RedisTransport("redis://stub:0")


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

def test_notify_receive_roundtrip(transport):
    transport.notify_job("job-1")
    transport.notify_job("job-2")
    transport.notify_job("job-3")
    assert transport.queue_depth("default") == 3
    got = set(transport.drain_queue())
    assert got == {"job-1", "job-2", "job-3"}
    assert transport.queue_depth("default") == 0


def test_lease_mirror_nx_and_ttl(transport):
    assert transport.mirror_lease("job-a", "L1", "worker-1", ttl_seconds=60) is True
    # duplicate mirror at transport level is rejected (NX)
    assert transport.mirror_lease("job-a", "L1", "worker-1", ttl_seconds=60) is False
    assert transport.read_lease("job-a") == {"lease_id": "L1", "worker_id": "worker-1"}
    assert transport.clear_lease("job-a") == 1
    assert transport.read_lease("job-a") is None


def test_heartbeat_and_worker_alive(transport):
    assert transport.worker_alive("w1") is False
    transport.heartbeat("w1", ttl_seconds=30)
    assert transport.worker_alive("w1") is True


def test_rate_check_limit(transport):
    assert transport.rate_check("actor-1", limit=3) is True
    assert transport.rate_check("actor-1", limit=3) is True
    assert transport.rate_check("actor-1", limit=3) is True
    assert transport.rate_check("actor-1", limit=3) is False


def test_ephemeral_cache_roundtrip(transport):
    transport.cache_set("jobs:hot", {"ids": ["a", "b"]}, ttl_seconds=60)
    assert transport.cache_get("jobs:hot") == {"ids": ["a", "b"]}
    assert transport.cache_invalidate("jobs:hot") == 1
    assert transport.cache_get("jobs:hot") is None


def test_scheduler_wakeup(transport):
    assert transport.wake_scheduler() == 0  # no subscribers in stub


def test_quarantine_roundtrip(transport):
    transport.quarantine("b2:lease:job-x", {"lease_id": "FORGED"}, "disagrees")
    records = transport.quarantined_records()
    assert len(records) == 1
    assert records[0]["key"] == "b2:lease:job-x"
    assert records[0]["reason"] == "disagrees"


class _StubJob:
    def __init__(self, job_id, status):
        self.job_id = job_id
        self.status = status


class _StubPg:
    def __init__(self, pending, active, auth):
        self._pending = pending
        self._active = active
        self._auth = auth

    def jobs_by_status(self, status):
        return [j for j in self._pending if j.status == status]

    def active_leases(self):
        return self._active

    def authoritative_lease(self, job_id):
        return self._auth.get(job_id)


def test_reconstruct_from_pg_rebuilds_and_quarantines(transport):
    pg = _StubPg(
        pending=[_StubJob("job-a", "pending"), _StubJob("job-b", "pending")],
        active=[
            {"job_id": "job-c", "lease_id": "L1", "worker_id": "w1", "ttl_seconds": 60},
            {"job_id": "job-d", "lease_id": "L2", "worker_id": "w2", "ttl_seconds": 60},
        ],
        auth={
            "job-c": {"lease_id": "L1", "worker_id": "w1"},
            "job-d": {"lease_id": "L2", "worker_id": "w2"},
        },
    )
    # Pre-existing mirrors: one forged (disagrees with PG), one correct
    transport.mirror_lease("job-c", "FORGED-TOKEN", "w9", ttl_seconds=60)
    transport.mirror_lease("job-d", "L2", "w2", ttl_seconds=60)
    # Stale cache + heartbeat should be wiped by reconstruction
    transport.cache_set("stale", 1)
    transport.heartbeat("ghost-worker", ttl_seconds=30)

    receipt = transport.reconstruct_from_pg(pg)

    assert receipt["rebuilt"] is True
    assert receipt["notifications"] == 2
    assert receipt["leases"] == 2
    assert receipt["quarantined"] == 1
    assert receipt["heartbeats_restored"] == 0

    # PG truth won: forged mirror replaced, correct mirror preserved
    assert transport.read_lease("job-c") == {"lease_id": "L1", "worker_id": "w1"}
    assert transport.read_lease("job-d") == {"lease_id": "L2", "worker_id": "w2"}
    # Notifications repopulated for pending jobs
    assert transport.queue_depth("default") == 2
    assert set(transport.drain_queue()) == {"job-a", "job-b"}
    # Disposable projections wiped
    assert transport.cache_get("stale") is None
    assert transport.worker_alive("ghost-worker") is False
    # Conflict recorded
    records = transport.quarantined_records()
    assert any(r["key"] == "b2:lease:job-c"
               and r["reason"] == "lease_mirror_disagrees_with_pg" for r in records)


def test_reconstruct_reports_failure_without_raising(transport):
    class _BrokenPg:
        def jobs_by_status(self, status):
            raise RuntimeError("pg gone")

    transport.notify_job("job-a")
    receipt = transport.reconstruct_from_pg(_BrokenPg())
    assert receipt["rebuilt"] is False
    assert "pg gone" in receipt["error"]


def test_transport_unavailable_on_downstream_failure(monkeypatch):
    class _BrokenRedis:
        def ping(self):
            raise ConnectionError("refused")

    class _FakeModule:
        class Redis:
            @staticmethod
            def from_url(url, **kwargs):
                return _BrokenRedis()

    monkeypatch.setattr(rt, "redis_lib", _FakeModule)
    with pytest.raises(RedisUnavailable):
        RedisTransport("redis://stub:0")

