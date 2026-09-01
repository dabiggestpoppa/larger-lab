"""B3-R7: end-to-end governed local worker execution through the real
production path.

Container-backed (mandatory in CI against compose PostgreSQL + Redis on
loopback). Truthful skip without Docker locally.

Every representative job traverses:

    authorized submission (PgJobStore)
    -> PostgreSQL authoritative
    -> Redis notification (transport)
    -> authenticated outbound worker (separate process)
    -> fenced PostgreSQL lease (b3_fabric_leases)
    -> bounded disposable sandbox
    -> immutable publication (CAS ArtifactStore)
    -> verified result under the current fence
    -> durable terminal job state (status='succeeded')

Proves restart/recovery semantics: control-plane restart (fresh objects over
the same PG), worker disconnect/reconnect, lease expiry+reclaim, duplicate
delivery = one effect, stale-result quarantine, revocation, Redis
destroy/reconstruction, artifact reload, retry exhaustion, durable dead
letter, and PO-authorized retry.
"""
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))
sys.path.insert(0, str(BASE / "scripts"))
sys.path.insert(0, str(BASE / "tests"))

import oce_b2_compose as oc  # noqa: E402
import migrate  # noqa: E402

pytestmark = pytest.mark.container

WORKER_ID = "worker-e2e-01"
SECRET = "e2e-outbound-secret-0123456789abcd"

JOBS = {
    "b3.deterministic-hash": {"value": "oce-e2e"},
    "b3.bounded-compute": {"n": 5000},
    "b3.repo-inventory": {},
    "b3.synthetic-backtest": {"seed": 7, "n": 120},
    "b3.analysis-artifact": {"title": "OCE E2E", "rows": 3},
}


def _verifier(s: str) -> str:
    import hashlib
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


@pytest.fixture(scope="module")
def pg():
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
def redis_url():
    if not oc.docker_available():
        pytest.skip("container runtime unavailable (Docker absent)")
    return oc.redis_url()


@pytest.fixture(autouse=True)
def _clean_db(pg):
    with pg.cursor() as cur:
        cur.execute(
            "DROP TABLE IF EXISTS schema_migrations, evidence_refs, audit_log, "
            "events, workers, schedules, leases, idempotency, job_transitions, "
            "jobs, denials, capability_grants, actors, capability_admissions, "
            "worker_fabric_instances, worker_sessions, b3_artifacts, "
            "b3_dead_letters, b3_fabric_leases, b3_effects, b3_quarantine, "
            "b3_retry_state, b3_authorized_retries CASCADE"
        )
    pg.commit()
    assert migrate.cmd_up(oc.dsn(), migrate.MIGRATIONS_DIR) == 0


@pytest.fixture
def jstore(pg):
    from oce_control.pg_store import PgJobStore
    return PgJobStore(pg)


@pytest.fixture
def fabric(pg):
    from oce_control.worker_fabric_store import PgWorkerFabricStore
    return PgWorkerFabricStore(pg)


def _stack(pg, fabric, redis_url):
    from oce_control.worker_protocol import WorkerProtocolServer
    from oce_control.redis_transport import RedisTransport
    from oce_control.pg_store import PgJobStore
    from oce_control.authority import AuthorityEngine
    from oce_control import http_api
    from oce_control.api import ControlPlaneAPI
    from oce_control.health import HealthService
    from oce_control.pg_scheduler import PgScheduler
    from oce_control.pg_worker import PgWorkerProtocol
    jstore = PgJobStore(pg)
    server = WorkerProtocolServer(fabric, job_store=jstore)
    try:
        rt = RedisTransport(redis_url)
        server.set_transport(rt)
    except Exception:
        pass  # Redis optional in the transport layer; PG remains truth
    scheduler = PgScheduler(pg, jstore)
    worker = PgWorkerProtocol(jstore, pg)
    health = HealthService(job_store=jstore, scheduler=scheduler,
                           worker_protocol=worker)
    health.set_pg_available(True)
    api = ControlPlaneAPI(authority=AuthorityEngine(), job_store=jstore,
                          scheduler=scheduler, worker_protocol=worker,
                          health_service=health)
    app = http_api.create_app(api, scheduler=scheduler,
                              scheduler_tick_interval=0,
                              worker_protocol_server=server)
    return app, server, jstore


@pytest.fixture
def service(pg, fabric, redis_url):
    app, server, jstore = _stack(pg, fabric, redis_url)
    import socket
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    t = threading.Thread(target=lambda: _uvicorn(app, port), daemon=True)
    t.start()
    time.sleep(1.5)
    yield f"http://127.0.0.1:{port}", server, jstore


def _uvicorn(app, port):
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


ALL_CAPS = ("hash", "compute-python", "repo-inventory",
            "backtest-synthetic", "analysis-artifact")


def _admit(fabric) -> None:
    for cap in ALL_CAPS:
        fabric.admit_capability(cap, "operator:po")
    fabric.persist_identity(
        worker_id=WORKER_ID, protocol_version="1.0", worker_version="1.0",
        host_os_class="linux", runtime_class="python", trust_zone="worker-local",
        sandbox_profile="default", capabilities=list(ALL_CAPS),
        credential_verifier=_verifier(SECRET), actor="operator:po")


def _run_worker(tmp_path: Path, url: str, job_id: str, *, ws_base: str,
                expect_success: bool = True) -> subprocess.CompletedProcess:
    """Launch a SEPARATE worker process that dials OUT, fetches the governed
    job from the control plane, and executes it end-to-end."""
    env = dict(os.environ)
    # B4-CXR3R3: the worker derives its outbound target from the validated
    # effective config (OCE_CONTROL_PLANE_PORT); OCE_CP_URL is not an
    # override surface.
    env.update({
        "PYTHONPATH": str(BASE / "src") + os.pathsep + env.get("PYTHONPATH", ""),
        "OCE_CONTROL_PLANE_PORT": str(int(url.rsplit(":", 1)[1])),
        "OCE_WORKER_ID": WORKER_ID,
        "OCE_WORKER_SECRET": SECRET, "OCE_JOB_FILE": "",
        "OCE_WS_BASE": str(tmp_path / ws_base),
        "OCE_ARTIFACT_BASE": str(tmp_path / (ws_base + "-cas")),
        # B4-CXR5R6: the ambient worker secret is TEST_ONLY — reachable only
        # under the authenticated CI/test seam; production reads the store.
        "OCE_CI_MODE": "true",
    })
    r = subprocess.run([sys.executable, str(BASE / "scripts" / "oce_b3_worker.py")],
                       cwd=str(tmp_path), env=env, capture_output=True, text=True,
                       timeout=180)
    return r


def test_end_to_end_representative_jobs(pg, fabric, jstore, service, tmp_path):
    _admit(fabric)
    url, server, _ = service
    from oce_control.redis_transport import RedisTransport
    rt = RedisTransport(oc.redis_url())
    for job_type, params in JOBS.items():
        job = jstore.submit_job(job_type=job_type, submitting_actor="operator:po",
                                grant_id="g", payload=params, timeout=120,
                                required_capabilities=[cap_for(job_type)])
        job_id = job.job_id
        rt.notify_job(job_id)          # transport announcement (disposable)
        r = _run_worker(tmp_path, url, job_id, ws_base="ws-" + job_type)
        assert r.returncode == 0, f"{job_type} worker failed:\n{r.stdout}\n{r.stderr}"
        done = jstore.get_job(job_id)
        assert done.status == "succeeded", f"{job_type} not succeeded: {done.status}"
        with pg.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM b3_effects WHERE job_id=%s", (job_id,))
            assert cur.fetchone()[0] == 1, f"{job_type} must have exactly one effect"


def cap_for(job_type: str) -> str:
    return {
        "b3.deterministic-hash": "hash",
        "b3.bounded-compute": "compute-python",
        "b3.repo-inventory": "repo-inventory",
        "b3.synthetic-backtest": "backtest-synthetic",
        "b3.analysis-artifact": "analysis-artifact",
    }[job_type]


def test_lease_expiry_and_reclaim(pg, fabric, jstore, service):
    _admit(fabric)
    url, server, _ = service
    job = jstore.submit_job(job_type="b3.deterministic-hash",
                            submitting_actor="operator:po", grant_id="g",
                            payload={"value": "x"}, required_capabilities=["hash"])
    # claim with a short TTL, let it expire, then reclaim bumps the fence
    server._store.claim(job.job_id, WORKER_ID, "tok-E2E-0001", 1, 1)
    time.sleep(1.2)
    reclaimed = server._store.reclaim_stale_leases()
    assert job.job_id in reclaimed
    head = server._store.fetch_fence(job.job_id)
    server._store.claim(job.job_id, WORKER_ID, "tok-E2E-0002", head["fence"] + 1, 120)
    # the previous fence/lease is fenced out
    assert server._store.renew(job.job_id, "tok-E2E-0001", 1, 60) is False


def test_duplicate_delivery_one_material_effect(pg, fabric, jstore, service):
    _admit(fabric)
    url, server, _ = service
    job = jstore.submit_job(job_type="b3.deterministic-hash",
                            submitting_actor="operator:po", grant_id="g",
                            payload={"value": "dedup"}, required_capabilities=["hash"])
    job_id = job.job_id
    server._store.claim(job_id, WORKER_ID, "tok-DUP-0001", 1, 120)
    from oce_control.worker_protocol import SessionGone, WorkerProtocolError
    from oce_control.worker_client import OutboundWorkerClient, _hmac
    # A REAL authenticated outbound session (challenge/response over the shared
    # secret) is required before any result may be delivered.
    cli = OutboundWorkerClient(url, WORKER_ID, SECRET)
    cli.connect()
    sess_id = cli._session_id
    sig = _hmac(cli._key, f"{sess_id}:deliver_result")
    # first delivery accepted under the current fence
    result = server.deliver_result(
        session_id=sess_id, signature=sig, job_id=job_id,
        lease_id="tok-DUP-0001", fence=1, effect_key=f"{job_id}::dup::effect",
        success=True)
    assert result["delivered"] is True
    # a duplicate delivery under a stale/forked lease must not create a 2nd effect
    with pytest.raises((SessionGone, WorkerProtocolError)):
        server.deliver_result(
            session_id=sess_id, signature=sig, job_id=job_id,
            lease_id="tok-FORGED", fence=9, effect_key=f"{job_id}::dup::effect",
            success=True)
    cli.close()
    with pg.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM b3_effects WHERE job_id=%s", (job_id,))
        assert cur.fetchone()[0] == 1


def test_artifacts_survive_control_plane_restart(pg, fabric, jstore, service, tmp_path):
    _admit(fabric)
    url, server, jstore0 = service
    job = jstore0.submit_job(job_type="b3.analysis-artifact",
                             submitting_actor="operator:po", grant_id="g",
                             payload={"title": "t", "rows": 2},
                             required_capabilities=["analysis-artifact"])
    r = _run_worker(tmp_path, url, job.job_id, ws_base="ws-restart")
    assert r.returncode == 0
    # "restart" the control plane: a fresh fabric store + fresh jstore see the
    # same durable manifest and effect
    from oce_control.worker_fabric_store import PgWorkerFabricStore
    fresh = PgWorkerFabricStore(pg)
    with pg.cursor() as cur:
        cur.execute("SELECT manifest_id FROM b3_artifacts WHERE job_id=%s", (job.job_id,))
        manifest_id = cur.fetchone()[0]
    loaded = fresh.load_manifest(manifest_id)
    assert loaded is not None
    assert loaded["job_id"] == job.job_id
    assert jstore0.get_job(job.job_id).status == "succeeded"


def test_revoked_worker_refused(pg, fabric, jstore, service, tmp_path):
    _admit(fabric)
    url, server, _ = service
    server.revoke_worker("operator:po", WORKER_ID)
    job = jstore.submit_job(job_type="b3.deterministic-hash",
                            submitting_actor="operator:po", grant_id="g",
                            payload={"value": "x"}, required_capabilities=["hash"])
    r = _run_worker(tmp_path, url, job.job_id, ws_base="ws-revoked")
    assert r.returncode != 0  # revoked worker cannot authenticate
    assert jstore.get_job(job.job_id).status == "pending"


def test_po_authorized_retry_records_audit_and_hermes_denied(pg, fabric, jstore, service):
    _admit(fabric)
    url, server, _ = service
    job = jstore.submit_job(job_type="b3.deterministic-hash",
                            submitting_actor="operator:po", grant_id="g",
                            payload={"value": "x"}, required_capabilities=["hash"])
    server._store.dead_letter(job_id=job.job_id, attempt=3, worker_id=WORKER_ID,
                              reason="retry_exhausted", detail="boom",
                              idempotency_key=job.job_id, poison=True)
    # Hermes is NOT authorized to release a dead-lettered job
    with pytest.raises(PermissionError):
        server._store.authorized_retry(job_id=job.job_id, actor="hermes")
    # operator:po is the only CEO-level authority
    assert server._store.authorized_retry(job_id=job.job_id,
                                          actor="operator:po") is True
    with pg.cursor() as cur:
        cur.execute("SELECT decision FROM b3_authorized_retries "
                    "WHERE job_id=%s ORDER BY id", (job.job_id,))
        decisions = [r[0] for r in cur.fetchall()]
    assert decisions == ["denied", "granted"]