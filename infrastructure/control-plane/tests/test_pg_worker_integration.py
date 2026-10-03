"""B2-R4: worker protocol integration tests (container-backed).

Mandatory in CI (real PostgreSQL via the B2 compose stack on loopback
port 5433). Truthful skip without Docker locally.

Proves audit gap 10 (worker admission authenticates: token required,
only its hash stored, wrong-token re-admit denied, revoked workers
refused) and audit gap 11 (worker claim enforces required job
capabilities; lease-token fencing on renew/commit).
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
from oce_control.pg_worker import PgWorkerProtocol, hash_admission_token

pytestmark = pytest.mark.container

TOKEN_A = "tok-worker-a-001"
TOKEN_B = "tok-worker-b-002"


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
def protocol(pg, clock):
    from oce_control.pg_store import PgJobStore
    return PgWorkerProtocol(PgJobStore(pg), pg)


@pytest.fixture
def store(pg, clock):
    from oce_control.pg_store import PgJobStore
    return PgJobStore(pg)


def test_admission_requires_token(protocol):
    with pytest.raises(PermissionError, match="requires a token"):
        protocol.admit_worker(worker_id="worker-local01", token="",
                              capabilities=["gpu"])


def test_admission_persists_token_hash_not_token(pg, protocol):
    protocol.admit_worker(worker_id="worker-local01", token=TOKEN_A,
                          capabilities=["gpu"])
    with pg.cursor() as cur:
        cur.execute("SELECT admission_token_hash FROM workers WHERE worker_id=%s",
                    ("worker-local01",))
        stored = cur.fetchone()[0]
    assert stored == hash_admission_token(TOKEN_A)
    assert TOKEN_A not in stored


def test_reauthmit_with_different_token_rejected(protocol):
    protocol.admit_worker(worker_id="worker-local01", token=TOKEN_A,
                          capabilities=["gpu"])
    with pytest.raises(PermissionError, match="different token"):
        protocol.admit_worker(worker_id="worker-local01", token=TOKEN_B,
                              capabilities=["gpu"])


def test_claim_requires_valid_token(protocol, store):
    job = store.submit_job(job_type="gpu_job", submitting_actor="po-test01",
                           grant_id="g", payload={"n": 1},
                           required_capabilities=["gpu"])
    protocol.admit_worker(worker_id="worker-local01", token=TOKEN_A,
                          capabilities=["gpu"])
    with pytest.raises(PermissionError, match="authentication failed"):
        protocol.claim_work("worker-local01", "forged-token", job.job_id)
    with pytest.raises(PermissionError, match="not admitted"):
        protocol.claim_work("worker-nobody", TOKEN_A, job.job_id)


def test_claim_enforces_required_capabilities(protocol, store):
    """Audit gap 11: worker without the required capability is denied."""
    job = store.submit_job(job_type="gpu_job", submitting_actor="po-test01",
                           grant_id="g", payload={"n": 1},
                           required_capabilities=["gpu"])
    protocol.admit_worker(worker_id="worker-cpu01", token=TOKEN_A,
                          capabilities=["cpu"])
    with pytest.raises(PermissionError, match="lacks required capabilities"):
        protocol.claim_work("worker-cpu01", TOKEN_A, job.job_id)
    # and the job is untouched
    assert store.get_job(job.job_id).status == "pending"


def test_claim_allows_matching_capabilities(protocol, store):
    job = store.submit_job(job_type="gpu_job", submitting_actor="po-test01",
                           grant_id="g", payload={"n": 1},
                           required_capabilities=["gpu"])
    protocol.admit_worker(worker_id="worker-gpu01", token=TOKEN_A,
                          capabilities=["gpu", "cpu"])
    claimed = protocol.claim_work("worker-gpu01", TOKEN_A, job.job_id)
    assert claimed["job"]["status"] == "leased"
    assert claimed["lease_id"]


def test_claim_without_required_capabilities_any_worker(protocol, store):
    job = store.submit_job(job_type="plain_job", submitting_actor="po-test01",
                           grant_id="g", payload={"n": 1})
    protocol.admit_worker(worker_id="worker-cpu01", token=TOKEN_A,
                          capabilities=["cpu"])
    claimed = protocol.claim_work("worker-cpu01", TOKEN_A, job.job_id)
    assert claimed["job"]["status"] == "leased"


def test_lease_token_fencing_on_commit(protocol, store):
    """Lease identity requires the token — forged/absent lease is fenced."""
    job = store.submit_job(job_type="gpu_job", submitting_actor="po-test01",
                           grant_id="g", payload={"n": 1},
                           required_capabilities=["gpu"])
    protocol.admit_worker(worker_id="worker-a01", token=TOKEN_A,
                          capabilities=["gpu"])
    protocol.admit_worker(worker_id="worker-b02", token=TOKEN_B,
                          capabilities=["gpu"])
    protocol.claim_work("worker-a01", TOKEN_A, job.job_id)
    # other worker (valid token, no lease) cannot commit
    with pytest.raises(PermissionError, match="holds no lease"):
        protocol.submit_result("worker-b02", TOKEN_B, job.job_id, {"ok": True})


def test_stale_lease_fenced_on_commit(protocol, store):
    job = store.submit_job(job_type="gpu_job", submitting_actor="po-test01",
                           grant_id="g", payload={"n": 1},
                           required_capabilities=["gpu"])
    protocol.admit_worker(worker_id="worker-a01", token=TOKEN_A,
                          capabilities=["gpu"])
    protocol.claim_work("worker-a01", TOKEN_A, job.job_id, lease_ttl=5)
    get_clock().advance(30)
    with pytest.raises(PermissionError):
        protocol.submit_result("worker-a01", TOKEN_A, job.job_id, {"ok": True})


def test_renew_and_complete_roundtrip(protocol, store):
    job = store.submit_job(job_type="gpu_job", submitting_actor="po-test01",
                           grant_id="g", payload={"n": 1},
                           required_capabilities=["gpu"])
    protocol.admit_worker(worker_id="worker-a01", token=TOKEN_A,
                          capabilities=["gpu"])
    protocol.claim_work("worker-a01", TOKEN_A, job.job_id, lease_ttl=30)
    protocol.renew_lease("worker-a01", TOKEN_A, job.job_id, lease_ttl=60)
    done = protocol.submit_result("worker-a01", TOKEN_A, job.job_id, {"ok": True})
    assert done["status"] == "succeeded"


def test_surrender_then_reclaim(protocol, store):
    job = store.submit_job(job_type="gpu_job", submitting_actor="po-test01",
                           grant_id="g", payload={"n": 1},
                           required_capabilities=["gpu"])
    protocol.admit_worker(worker_id="worker-a01", token=TOKEN_A,
                          capabilities=["gpu"])
    protocol.claim_work("worker-a01", TOKEN_A, job.job_id)
    surrendered = protocol.surrender_lease("worker-a01", TOKEN_A, job.job_id)
    assert surrendered["status"] == "pending"
    claimed = protocol.claim_work("worker-a01", TOKEN_A, job.job_id)
    assert claimed["job"]["status"] == "leased"


def test_revoked_worker_refused_everywhere(protocol, store):
    job = store.submit_job(job_type="gpu_job", submitting_actor="po-test01",
                           grant_id="g", payload={"n": 1},
                           required_capabilities=["gpu"])
    protocol.admit_worker(worker_id="worker-a01", token=TOKEN_A,
                          capabilities=["gpu"])
    protocol.revoke_worker("worker-a01")
    with pytest.raises(PermissionError, match="revoked"):
        protocol.claim_work("worker-a01", TOKEN_A, job.job_id)
    with pytest.raises(PermissionError, match="revoked"):
        protocol.authenticate("worker-a01", TOKEN_A)
    with pytest.raises(PermissionError, match="revoked and cannot be re-admitted"):
        protocol.admit_worker(worker_id="worker-a01", token=TOKEN_A,
                              capabilities=["gpu"])


def test_recover_abandoned_lease_returns_job_to_pending(protocol, store):
    job = store.submit_job(job_type="gpu_job", submitting_actor="po-test01",
                           grant_id="g", payload={"n": 1},
                           required_capabilities=["gpu"])
    protocol.admit_worker(worker_id="worker-a01", token=TOKEN_A,
                          capabilities=["gpu"])
    protocol.claim_work("worker-a01", TOKEN_A, job.job_id, lease_ttl=5)
    get_clock().advance(30)
    recovered = protocol.recover_abandoned_work()
    assert recovered == 1
    assert store.get_job(job.job_id).status == "pending"
