"""B2-R2: PostgreSQL integration tests (container-backed).

Mandatory in CI (real PostgreSQL via compose). Truthful skip without
Docker locally; the independent gate requires zero skips in CI mode.
Proves: migrations from empty DB, restart durability, idempotency
collision rejection, lease fencing, fail-closed on PG unavailability.
"""
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))
sys.path.insert(0, str(BASE / "scripts"))
sys.path.insert(0, str(BASE / "tests"))

import oce_b2_compose as oc

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
            "capability_grants, actors, config_override_audit CASCADE"
        )
    pg.commit()
    rc = migrate.cmd_up(oc.dsn(), migrate.MIGRATIONS_DIR)
    assert rc == 0, "migrations from empty DB must succeed"


def test_migrations_from_empty_db(pg):
    with pg.cursor() as cur:
        cur.execute("SELECT version FROM schema_migrations ORDER BY version")
        versions = [r[0] for r in cur.fetchall()]
    assert "0001" in versions and "0002" in versions


def test_job_persists_and_survives_reconnect(pg):
    from oce_control.pg_store import PgJobStore
    store = PgJobStore(pg)
    job = store.submit_job(
        job_type="unit_test", submitting_actor="po-test01",
        grant_id="grant-x", payload={"n": 1},
    )
    assert job.status == "pending"
    # simulate process restart: new connection, new store instance
    import psycopg2
    conn2 = psycopg2.connect(oc.dsn())
    store2 = PgJobStore(conn2)
    job2 = store2.get_job(job.job_id)
    assert job2 is not None and job2.payload_hash == job.payload_hash
    conn2.close()


def test_exact_replay_returns_same_job(pg):
    from oce_control.pg_store import PgJobStore
    store = PgJobStore(pg)
    job1 = store.submit_job(
        job_type="unit_test", submitting_actor="po-test01",
        grant_id="g", payload={"n": 2}, idempotency_key="a" * 64,
    )
    job2 = store.submit_job(
        job_type="unit_test", submitting_actor="po-test01",
        grant_id="g", payload={"n": 2}, idempotency_key="a" * 64,
    )
    assert job1.job_id == job2.job_id
    assert len(store.all_jobs) == 1


def test_idempotency_key_reuse_with_changed_payload_rejected(pg):
    from oce_control.pg_store import PgJobStore, IdempotencyConflict
    store = PgJobStore(pg)
    store.submit_job(
        job_type="unit_test", submitting_actor="po-test01",
        grant_id="g", payload={"n": 1}, idempotency_key="b" * 64,
    )
    with pytest.raises(IdempotencyConflict):
        store.submit_job(
            job_type="unit_test", submitting_actor="po-test01",
            grant_id="g", payload={"n": 999}, idempotency_key="b" * 64,
        )


def test_idempotency_key_reuse_by_other_actor_rejected(pg):
    from oce_control.pg_store import PgJobStore, IdempotencyConflict
    store = PgJobStore(pg)
    store.submit_job(
        job_type="unit_test", submitting_actor="po-test01",
        grant_id="g", payload={"n": 1}, idempotency_key="c" * 64,
    )
    with pytest.raises(IdempotencyConflict):
        store.submit_job(
            job_type="unit_test", submitting_actor="po-other02",
            grant_id="g", payload={"n": 1}, idempotency_key="c" * 64,
        )


def test_stale_lease_fenced_on_commit(pg):
    from oce_control.pg_store import PgJobStore
    store = PgJobStore(pg)
    job = store.submit_job(
        job_type="unit_test", submitting_actor="po-test01",
        grant_id="g", payload={"n": 3},
    )
    store.claim_lease(job.job_id, "worker-a", lease_ttl=5)
    lease_id = store._one("SELECT lease_id FROM leases WHERE job_id=%s", (job.job_id,))[0]
    from oce_control.clocks import get_clock
    get_clock().advance(30)
    with pytest.raises(PermissionError):
        store.complete_job(job.job_id, lease_id, "worker-a", {"ok": True})


def test_wrong_lease_token_fenced(pg):
    from oce_control.pg_store import PgJobStore
    store = PgJobStore(pg)
    job = store.submit_job(
        job_type="unit_test", submitting_actor="po-test01",
        grant_id="g", payload={"n": 4},
    )
    store.claim_lease(job.job_id, "worker-a", lease_ttl=60)
    with pytest.raises(PermissionError):
        store.complete_job(job.job_id, "forged-lease-token", "worker-b", {"ok": True})


def test_pg_unavailable_fails_closed(pg):
    # Use a DEDICATED connection so the module-shared `pg` fixture survives
    # for the following tests (closing it poisoned _clean_db at setup).
    import psycopg2
    from oce_control.pg_store import PgJobStore
    conn2 = psycopg2.connect(oc.dsn())
    conn2.autocommit = False
    store = PgJobStore(conn2)
    # simulate real service failure: terminate this connection
    conn2.close()
    with pytest.raises(Exception):
        store.submit_job(
            job_type="unit_test", submitting_actor="po-test01",
            grant_id="g", payload={"n": 5},
        )


def test_cancel_and_quarantine_persist(pg):
    """cancel_job / quarantine_job must not blow up on real PG (B2-R6R2
    regression: both referenced an undefined `clock`, surfacing as a 400 on
    the HTTP cancel endpoint in CI)."""
    from oce_control.pg_store import PgJobStore
    store = PgJobStore(pg)
    job = store.submit_job(
        job_type="unit_test", submitting_actor="po-test01",
        grant_id="g", payload={"n": 6},
    )
    cancelled = store.cancel_job(job.job_id)
    assert cancelled.status == "cancelled"
    assert store.get_job(job.job_id).status == "cancelled"

    job2 = store.submit_job(
        job_type="unit_test", submitting_actor="po-test01",
        grant_id="g", payload={"n": 7},
    )
    quarantined = store.quarantine_job(job2.job_id, "regression test")
    assert quarantined.status == "quarantined"
    assert store.get_job(job2.job_id).status == "quarantined"


def test_migration_checksum_mismatch_detected(pg):
    """Tampering with an applied migration's recorded checksum must fail closed."""
    import migrate
    with pg.cursor() as cur:
        cur.execute("UPDATE schema_migrations SET checksum='tampered' WHERE version='0002'")
    pg.commit()
    rc = migrate.cmd_up(oc.dsn(), migrate.MIGRATIONS_DIR)
    assert rc == 2, "checksum mismatch must return nonzero"


# --------------------------------------------------------------------------- #
# B4-CXR5R5: durable override audit — append-only ledger + reloadable          #
# persistence through a FRESH connection (real PostgreSQL, mandatory in CI).   #
# --------------------------------------------------------------------------- #


def _audit_insert(pg, *, audit_id: str, request_id: str = "", actor: str = "operator:po",
                  setting: str = "control_plane.port", requested_change: str = "x",
                  reason: str = "r", previous: str = "8448", new: str = "9124",
                  decision: str = "granted", authorized: bool = True,
                  fingerprint_before: str = "fp-before",
                  fingerprint_after: str = "fp-after",
                  backend_identity: str = "postgres:config_override_audit") -> None:
    with pg.cursor() as cur:
        cur.execute(
            "INSERT INTO config_override_audit "
            "(audit_id, request_id, actor, setting, requested_change, reason, "
            " previous, new, decision, authorized, fingerprint_before, "
            " fingerprint_after, backend_identity) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
            "ON CONFLICT (audit_id) DO NOTHING",
            (audit_id, request_id or audit_id, actor, setting, requested_change,
             reason, previous, new, decision, authorized, fingerprint_before,
             fingerprint_after, backend_identity))
    pg.commit()


def test_audit_ledger_append_only_update_and_delete_refused(pg):
    """CXR5-05 #13 / proof V: UPDATE and DELETE on the committed override
    ledger are REFUSED IN THE DATABASE (migration 0007 trigger) — an
    accidental rewrite or a forged record can never be introduced through SQL.
    """
    _audit_insert(pg, audit_id="aud-append-only-1")
    for stmt in (
        "UPDATE config_override_audit SET reason='forged' "
        "WHERE audit_id='aud-append-only-1'",
        "DELETE FROM config_override_audit "
        "WHERE audit_id='aud-append-only-1'",
    ):
        try:
            with pg.cursor() as cur:
                cur.execute(stmt)
            pg.commit()
            raise AssertionError(
                f"statement must be refused by the append-only trigger: {stmt}")
        except Exception as exc:
            pg.rollback()  # aborted transaction after trigger RAISE
            assert "APPEND-ONLY" in str(exc)
    with pg.cursor() as cur:
        cur.execute("SELECT reason FROM config_override_audit "
                    "WHERE audit_id='aud-append-only-1'")
        assert cur.fetchone()[0] == "r"  # original row unchanged


def test_audit_record_reloadable_via_fresh_connection(pg):
    """CXR5-05 #13 / proof U+reload: a committed audit record is readable
    through a FRESH connection (restart-persistence proof) with every
    durable-record field intact.
    """
    import psycopg2
    from oce_control.audit_sink import PostgresAuditSink
    _audit_insert(pg, audit_id="aud-fresh-conn-1", request_id="req-fresh-1",
                  fingerprint_before="fp-b", fingerprint_after="fp-a")
    conn2 = psycopg2.connect(oc.dsn())
    try:
        back = PostgresAuditSink(conn2).read_back()
        rows = [r for r in back if r["audit_id"] == "aud-fresh-conn-1"]
        assert len(rows) == 1
        row = rows[0]
        assert row["request_id"] == "req-fresh-1"
        assert row["actor"] == "operator:po"
        assert row["fingerprint_before"] == "fp-b"
        assert row["fingerprint_after"] == "fp-a"
        assert row["backend_identity"] == "postgres:config_override_audit"
        assert row["recorded_at"] is not None
    finally:
        conn2.close()


def test_audit_append_idempotent_on_conflict(pg):
    """CXR5-05 #9: retrying the same request/correlation id yields exactly
    one ledger row (ON CONFLICT DO NOTHING) — an uncertain commit can be
    reconciled safely without duplicate decisions.
    """
    _audit_insert(pg, audit_id="aud-idem-1", request_id="req-idem-1")
    _audit_insert(pg, audit_id="aud-idem-1", request_id="req-idem-1")
    with pg.cursor() as cur:
        cur.execute("SELECT count(*) FROM config_override_audit "
                    "WHERE audit_id='aud-idem-1'")
        assert cur.fetchone()[0] == 1
