"""B2-R4: durable scheduler integration tests (container-backed).

Mandatory in CI (real PostgreSQL via the B2 compose stack on loopback
port 5433). Truthful skip without Docker locally.

Proves audit gap 15: scheduler state persists in PostgreSQL, a restart
recovers it faithfully (not from memory), due jobs fire after restart,
pause/resume/cancel survive restarts, and duplicate firing is prevented
per schedule via PostgreSQL advisory locks.
"""
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))
sys.path.insert(0, str(BASE / "scripts"))
sys.path.insert(0, str(BASE / "tests"))

import oce_b2_compose as oc
from oce_control.clocks import get_clock
from oce_control.pg_scheduler import PgScheduler, advisory_lock_key

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


def _new_conn():
    import psycopg2
    conn = psycopg2.connect(oc.dsn())
    conn.autocommit = False
    return conn


def _scheduler(conn=None):
    conn = conn or _new_conn()
    from oce_control.pg_store import PgJobStore
    return PgScheduler(conn, PgJobStore(conn))


def _create(sched, kind="immediate", **kw):
    base = dict(job_type="test_job", payload={"n": 1},
                grant_id="g", submitting_actor="po-test01")
    base.update(kw)
    if kind == "recurring":
        return sched.create_recurring(interval_seconds=base.pop("interval_seconds", 60),
                                      **base)
    if kind == "delayed":
        return sched.create_delayed(delay_seconds=base.pop("delay_seconds", 10),
                                    **base)
    return sched.create_immediate(**base)


def test_schedules_persist_and_survive_restart(clock):
    """Audit gap 15: a restarted scheduler recovers schedules from PostgreSQL."""
    sched1 = _scheduler()
    _create(sched1, "immediate")
    _create(sched1, "delayed", delay_seconds=10)

    # simulate restart: brand-new connection + scheduler instance
    sched2 = _scheduler()
    recovered = sched2.recover_after_restart()
    assert len(sched2.schedules) == 2
    assert recovered >= 0

    # recovered schedule fires its due immediate job (delayed is not due yet)
    fired = sched2.tick()
    assert len(fired) == 1
    assert fired[0].status == "pending"


def test_restart_recovery_recomputes_recurring_next_run(clock):
    sched1 = _scheduler()
    sched1.create_recurring(job_type="test_job", payload={"n": 1},
                            grant_id="g", submitting_actor="po-test01",
                            interval_seconds=60)
    get_clock().advance(300)  # missed several runs while "down"

    sched2 = _scheduler()
    recovered = sched2.recover_after_restart()
    assert recovered == 1
    s = list(sched2.schedules.values())[0]
    # next run reconciled to the first run strictly after now (t0+300 -> t0+360)
    from datetime import datetime
    next_dt = datetime.fromisoformat(s.next_run_at)
    assert next_dt > get_clock().now()

    # after advancing past the reconciled next run, tick fires exactly one job
    get_clock().advance(120)
    fired = sched2.tick()
    assert len(fired) == 1


def test_delayed_job_fires_after_restart_when_due(clock):
    sched1 = _scheduler()
    _create(sched1, "delayed", delay_seconds=10)

    sched2 = _scheduler()
    sched2.recover_after_restart()
    assert sched2.tick() == []  # not due yet

    get_clock().advance(15)
    fired = sched2.tick()
    assert len(fired) == 1


def test_pause_resume_survive_restart(clock):
    sched1 = _scheduler()
    created = _create(sched1, "immediate")
    sched1.pause(created.schedule_id)

    sched2 = _scheduler()
    sched2.recover_after_restart()
    assert sched2.tick() == []  # still paused after restart

    sched2.resume(created.schedule_id)
    fired = sched2.tick()
    assert len(fired) == 1


def test_cancel_removes_schedule_from_pg(clock):
    sched1 = _scheduler()
    created = _create(sched1, "immediate")
    sched1.cancel(created.schedule_id)

    sched2 = _scheduler()
    sched2.recover_after_restart()
    assert len(sched2.schedules) == 0


def test_advisory_lock_prevents_duplicate_firing(clock):
    sched = _scheduler()
    created = _create(sched, "immediate")

    # another scheduler session holds the per-schedule advisory lock
    other = _new_conn()
    with other.cursor() as cur:
        cur.execute("SELECT pg_try_advisory_lock(%s)",
                    (advisory_lock_key(created.schedule_id),))
        assert cur.fetchone()[0] is True

    try:
        assert sched.tick() == []  # lock held -> must not fire
        from oce_control.pg_store import PgJobStore
        assert len(PgJobStore(sched._conn).all_jobs) == 0
    finally:
        with other.cursor() as cur:
            cur.execute("SELECT pg_advisory_unlock(%s)",
                        (advisory_lock_key(created.schedule_id),))
        other.close()

    fired = sched.tick()  # lock released -> fires exactly once
    assert len(fired) == 1


def test_concurrency_limit_respected(clock):
    sched = _scheduler()
    created = _create(sched, "recurring", interval_seconds=60, max_concurrent=1)
    fired = sched.tick()
    assert len(fired) == 1

    # worker takes the fired job -> running count 1 -> limit reached
    job = fired[0]
    from oce_control.pg_store import PgJobStore
    store = PgJobStore(sched._conn)
    store.claim_lease(job.job_id, "worker-a", lease_ttl=600)

    get_clock().advance(60)  # next run due
    assert sched.tick() == []  # concurrency limit blocks the next firing

    # job completes -> count drops -> next tick can fire again
    auth = store.authoritative_lease(job.job_id)
    store.complete_job(job.job_id, auth["lease_id"], "worker-a", {"ok": True})
    get_clock().advance(60)
    fired2 = sched.tick()
    assert len(fired2) == 1
