"""B2-R3: Redis transport integration tests (container-backed).

Mandatory in CI (real Redis + PostgreSQL via the B2 compose stack on
loopback ports 6380/5433). Truthful skip without Docker locally; the
independent gate requires zero skips in CI mode.

Proves: real notification queues, lease mirror NX/TTL, and full
reconstruction of Redis projections from authoritative PostgreSQL —
including quarantine of forged lease mirrors.
"""
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))
sys.path.insert(0, str(BASE / "scripts"))
sys.path.insert(0, str(BASE / "tests"))

import oce_b2_compose as oc
from oce_control.redis_transport import RedisTransport

pytestmark = pytest.mark.container


@pytest.fixture(scope="module")
def pg():
    """Real PostgreSQL from the B2 compose stack."""
    import psycopg2
    if not oc.docker_available():
        pytest.skip("container runtime unavailable (Docker absent)")
    oc.stack_up()
    conn = psycopg2.connect(oc.dsn())
    conn.autocommit = False
    yield conn
    try:
        conn.close()
    except Exception:
        pass


@pytest.fixture(scope="module")
def redis_conn():
    """Real Redis from the B2 compose stack (transport only)."""
    import redis as redis_lib
    if not oc.docker_available():
        pytest.skip("container runtime unavailable (Docker absent)")
    oc.stack_up()
    r = redis_lib.Redis.from_url(oc.redis_url(), decode_responses=True)
    r.ping()
    yield r


@pytest.fixture
def transport_real(redis_conn):
    """RedisTransport over the real compose Redis; DB flushed per test."""
    redis_conn.flushdb()
    return RedisTransport(oc.redis_url())


@pytest.fixture(autouse=True)
def _clean_db(pg):
    """Fresh tables per test: full drop then migrate up from empty DB."""
    import migrate
    with pg.cursor() as cur:
        cur.execute(
            "DROP TABLE IF EXISTS schema_migrations, evidence_refs, audit_log, events, "
            "workers, schedules, leases, idempotency, job_transitions, jobs, denials, "
            "capability_grants, actors CASCADE"
        )
    pg.commit()
    rc = migrate.cmd_up(oc.dsn(), migrate.MIGRATIONS_DIR)
    assert rc == 0, "migrations from empty DB must succeed"


def test_real_redis_notify_and_lease_mirror(transport_real):
    transport_real.notify_job("job-1")
    assert transport_real.receive_job() == "job-1"
    assert transport_real.mirror_lease("job-a", "L1", "w1", ttl_seconds=60) is True
    assert transport_real.read_lease("job-a")["lease_id"] == "L1"


def test_reconstruct_from_real_pg(pg, transport_real):
    from oce_control.pg_store import PgJobStore
    store = PgJobStore(pg)

    pending = store.submit_job(
        job_type="unit_test", submitting_actor="po-test01",
        grant_id="g", payload={"n": 1},
    )
    leased = store.submit_job(
        job_type="unit_test", submitting_actor="po-test01",
        grant_id="g", payload={"n": 2},
    )
    store.claim_lease(leased.job_id, "worker-a", lease_ttl=60)
    # Forged mirror that must be quarantined (real PG says lease_id differs)
    transport_real.mirror_lease(leased.job_id, "FORGED", "w9", ttl_seconds=60)

    receipt = transport_real.reconstruct_from_pg(store)

    assert receipt["rebuilt"] is True
    assert receipt["notifications"] == 1
    assert receipt["leases"] == 1
    assert receipt["quarantined"] == 1

    # PG truth restored the lease mirror
    mirror = transport_real.read_lease(leased.job_id)
    assert mirror is not None and mirror["lease_id"] != "FORGED"
    # Pending job re-notified
    assert transport_real.receive_job() == pending.job_id
    # Conflict recorded in quarantine
    records = transport_real.quarantined_records()
    assert any(r["key"].endswith(leased.job_id) for r in records)
