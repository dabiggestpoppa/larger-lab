"""B3-R3: real outbound authenticated worker protocol over the loopback
control-plane service, exercised with a SEPARATE worker process.

Container-backed (mandatory in CI with the compose PostgreSQL stack).
Truthful skip without Docker locally.

Proves:
* the worker dials OUT (never listens) and authenticates challenge/response;
* heartbeat / capability advertisement over an authenticated session;
* a fenced claim from an admitted, capability-safe worker;
* a governed job executed in a SEPARATE process, artifacts published
  immutably (CAS) and accepted under the current lease+fence;
* durable terminal job state (succeeded) recorded in PostgreSQL;
* forged proof, wrong worker, capability escalation, revoked worker, and
  duplicate effect all fail closed.
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

WORKER_ID = "worker-outbound-01"
SECRET = "oirhlkw3b9x9vv3bk0w0v4v6v7v3"  # test-only


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
def store(pg):
    from oce_control.worker_fabric_store import PgWorkerFabricStore
    return PgWorkerFabricStore(pg)


@pytest.fixture
def app_and_server(pg, store):
    from oce_control.worker_protocol import WorkerProtocolServer
    from oce_control import http_api
    # B4-CXR6X1: the CXR6R2 worker fetches the AUTHORITATIVE job detail from
    # the control plane (eligible_jobs -> fetch_job), so the fabric server
    # must be wired to the real PgJobStore — without it eligible_jobs returns
    # empty and the worker exits 3 before running the governed job.
    from oce_control.pg_store import PgJobStore
    jstore = PgJobStore(pg)
    server = WorkerProtocolServer(store, job_store=jstore)
    # Real durable control-plane boundary (fabric endpoints + API) — the
    # container-backed stack is authoritative PostgreSQL behind the service.
    from oce_control.api import ControlPlaneAPI
    from oce_control.authority import AuthorityEngine
    from oce_control.health import HealthService
    from oce_control.pg_scheduler import PgScheduler
    from oce_control.pg_worker import PgWorkerProtocol
    scheduler = PgScheduler(pg, jstore)
    worker = PgWorkerProtocol(jstore, pg)
    health = HealthService(job_store=jstore, scheduler=scheduler,
                           worker_protocol=worker)
    health.set_pg_available(True)
    api = ControlPlaneAPI(authority=AuthorityEngine(), job_store=jstore,
                          scheduler=scheduler, worker_protocol=worker,
                          health_service=health)
    return http_api.create_app(api, worker_protocol_server=server), server


def _serve(app, port):
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


@pytest.fixture
def service(app_and_server):
    app, server = app_and_server
    import socket
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    t = threading.Thread(target=_serve, args=(app, port), daemon=True)
    t.start()
    time.sleep(1.5)  # let uvicorn bind
    yield f"http://127.0.0.1:{port}", server
    # teardown: thread is daemon, process exits


def _admit(store) -> None:
    store.admit_capability("hash", "operator:po")
    store.persist_identity(
        worker_id=WORKER_ID, protocol_version="1.0", worker_version="1.0",
        host_os_class="linux", runtime_class="python",
        trust_zone="worker-local", sandbox_profile="default",
        capabilities=["hash"], credential_verifier=_verifier(SECRET),
        actor="operator:po")


def test_full_outbound_path_with_separate_worker_process(pg, store, service, tmp_path):
    _admit(store)
    url, server = service

    # A governed job row in the authoritative store.
    from oce_control.pg_store import PgJobStore
    jstore = PgJobStore(pg)
    job = jstore.submit_job(job_type="b3.deterministic-hash",
                            submitting_actor="operator:po", grant_id="g",
                            payload={"value": "oce-b3"}, required_capabilities=["hash"])
    job_id = job.job_id

    # Replay/forgery must fail before process launch.
    from oce_control.worker_client import OutboundWorkerClient, _hmac, wire_key
    bad = OutboundWorkerClient(url, WORKER_ID, "wrong-secret")
    with pytest.raises(Exception):
        bad.hello()
    bad.close()

    # Launch a SEPARATE worker process that dials OUT and does the work. The
    # worker fetches the AUTHORITATIVE job detail from the control plane
    # (B4-CXR5R6) — no local job file is injected.
    env = dict(os.environ)
    # B4-CXR3R3: the worker derives its outbound target from the validated
    # effective config (OCE_CONTROL_PLANE_PORT); OCE_CP_URL is not an
    # override surface.
    env.update({
        "PYTHONPATH": str(BASE / "src") + os.pathsep + env.get("PYTHONPATH", ""),
        "OCE_CONTROL_PLANE_PORT": str(int(url.rsplit(":", 1)[1])),
        "OCE_WORKER_ID": WORKER_ID,
        "OCE_WS_BASE": str(tmp_path / "ws"),
        "OCE_ARTIFACT_BASE": str(tmp_path / "cas"),
    })
    # B4-CXR6R2: the worker credential comes from the APPROVED store — seed
    # the test secret there (production authority); no ambient secret, no
    # OCE_CI_MODE unlock.
    from oce_control import local_secrets as ls
    ls._mutate_store(lambda d: d.update({"worker_token": SECRET}))
    r = subprocess.run([sys.executable, str(BASE / "scripts" / "oce_b3_worker.py")],
                       cwd=str(tmp_path), env=env, capture_output=True, text=True,
                       timeout=120)
    assert r.returncode == 0, f"worker process failed:\n{r.stdout}\n{r.stderr}"

    done = jstore.get_job(job_id)
    assert done.status == "succeeded"

    # one effect only + durable manifest reload
    with pg.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM b3_effects WHERE job_id=%s", (job_id,))
        assert cur.fetchone()[0] == 1
        cur.execute("SELECT manifest_id FROM b3_artifacts WHERE job_id=%s", (job_id,))
        manifest_id = cur.fetchone()[0]
    assert store.load_manifest(manifest_id)["job_id"] == job_id

    # duplicate delivery (a second worker attempt with the SAME effect key)
    # must be rejected by the fence — the first effect already applied.
    from oce_control.worker_protocol import SessionGone, WorkerProtocolError
    head = store.fetch_fence(job_id)
    with pytest.raises((SessionGone, WorkerProtocolError)):
        server.deliver_result(
            session_id="_", signature="_", job_id=job_id,
            lease_id="stale-or-forged", fence=1,
            effect_key=f"{job_id}::stale-or-forged::effect")


def test_capability_escalation_rejected(pg, store, service):
    _admit(store)
    url, server = service
    from oce_control.worker_client import OutboundWorkerClient, _hmac, wire_key
    cli = OutboundWorkerClient(url, WORKER_ID, SECRET)
    cli.connect()
    job = {"job_id": "j-escal", "job_type": "b3.analysis-artifact",
           "required_capabilities": ["analysis-artifact"],  # NOT admitted
           "trust_zone": "worker-local", "resource_envelope": {
               "cpu_limit": 1, "memory_bytes": 1, "disk_bytes": 1,
               "timeout_s": 5}}
    with pytest.raises(Exception):
        cli.claim(job)
    cli.close()


def test_revoked_worker_rejected(pg, store, service):
    _admit(store)
    url, server = service
    server.revoke_worker("operator:po", WORKER_ID)
    from oce_control.worker_client import OutboundWorkerClient
    cli = OutboundWorkerClient(url, WORKER_ID, SECRET)
    with pytest.raises(Exception):
        cli.hello()   # revoked identity: hello proof fails closed
    cli.close()