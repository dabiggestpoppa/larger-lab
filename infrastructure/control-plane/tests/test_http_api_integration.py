"""B2-R6: HTTP service integration tests (container-backed).

Mandatory in CI (real PostgreSQL + Redis via the B2 compose stack).
Truthful skip without Docker locally.

Proves gaps 7/8/9 over the REAL HTTP surface: the FastAPI service is
genuinely runnable, the console is served, health/readiness are
unauthenticated per the runtime contract, and every other endpoint
requires service-boundary authorization (X-OCE-Grant / X-OCE-Actor) —
read endpoints included.
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
            "capability_grants, actors CASCADE"
        )
    pg.commit()
    rc = migrate.cmd_up(oc.dsn(), migrate.MIGRATIONS_DIR)
    assert rc == 0, "migrations from empty DB must succeed"


@pytest.fixture
def client(pg, clock):
    """FastAPI TestClient over the durable control plane (real PG)."""
    from fastapi.testclient import TestClient
    from oce_control.api import ControlPlaneAPI
    from oce_control.authority import AuthorityEngine
    from oce_control.health import HealthService
    from oce_control.http_api import create_app
    from oce_control.pg_scheduler import PgScheduler
    from oce_control.pg_store import PgJobStore
    from oce_control.pg_worker import PgWorkerProtocol

    authority = AuthorityEngine()
    store = PgJobStore(pg)
    scheduler = PgScheduler(pg, store)
    worker = PgWorkerProtocol(store, pg)
    health = HealthService(job_store=store, scheduler=scheduler,
                           worker_protocol=worker)
    health.set_pg_available(True)
    api = ControlPlaneAPI(authority=authority, job_store=store,
                          scheduler=scheduler, worker_protocol=worker,
                          health_service=health)
    app = create_app(api, scheduler=scheduler, scheduler_tick_interval=0)
    with TestClient(app) as c:
        yield c, authority, store


READ_ACTOR = "operator-console"


def _headers(grant_id):
    return {"X-OCE-Grant": grant_id, "X-OCE-Actor": READ_ACTOR}


def test_health_and_readiness_unauthenticated(client):
    c, _, _ = client
    assert c.get("/api/health").status_code == 200
    assert c.get("/api/readiness").status_code == 200


def test_every_endpoint_requires_grant(client):
    c, _, _ = client
    assert c.get("/api/jobs/abc").status_code == 401
    assert c.get("/api/schedules").status_code == 401
    assert c.get("/api/workers").status_code == 401
    assert c.get("/api/system").status_code == 401
    assert c.get("/api/audit").status_code == 401


def test_invalid_grant_denied_403(client):
    c, _, _ = client
    r = c.get("/api/system", headers=_headers("forged-grant"))
    assert r.status_code == 403
    assert r.json()["status"] == "denied"


def test_submit_inspect_cancel_roundtrip(client):
    """Gap 7/9: real HTTP submit -> authorized inspect -> cancel."""
    c, authority, store = client
    submit = authority.issue_grant(actor_id="po-test01", action="submit_job",
                                   target="default")
    read = authority.issue_grant(actor_id=READ_ACTOR, action="read",
                                 target="default")

    r = c.post("/api/jobs", json={"job_type": "http_test", "payload": {"n": 1}},
               headers=_headers(submit.grant_id))
    assert r.status_code == 200, r.text
    job_id = r.json()["data"]["job_id"]
    # cancel/retry grants are targeted at the job id (façade contract)
    cancel = authority.issue_grant(actor_id="po-test01", action="cancel_job",
                                   target=job_id)

    # read endpoint denied without read grant
    denied = c.get(f"/api/jobs/{job_id}", headers=_headers(submit.grant_id))
    assert denied.status_code == 403

    ok = c.get(f"/api/jobs/{job_id}", headers=_headers(read.grant_id))
    assert ok.status_code == 200
    assert ok.json()["data"]["job_id"] == job_id
    assert ok.json()["data"]["status"] == "pending"
    assert store.get_job(job_id).status == "pending"

    r = c.post(f"/api/jobs/{job_id}/cancel", headers=_headers(cancel.grant_id))
    assert r.status_code == 200
    assert store.get_job(job_id).status == "cancelled"


def test_read_endpoints_with_grant(client):
    c, authority, _ = client
    read = authority.issue_grant(actor_id=READ_ACTOR, action="read",
                                 target="default")
    for path in ("/api/schedules", "/api/workers", "/api/system", "/api/audit"):
        r = c.get(path, headers=_headers(read.grant_id))
        assert r.status_code == 200, f"{path}: {r.text}"
        assert r.json()["ok"] is True


def test_console_served(client):
    c, _, _ = client
    r = c.get("/console")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "OCE Control Plane" in r.text
    root = c.get("/", follow_redirects=False)
    assert root.status_code in (302, 307)
    assert root.headers.get("location") == "/console"
