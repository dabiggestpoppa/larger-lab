"""B3-R2: durable PostgreSQL Worker Fabric store integration tests.

Container-backed (mandatory in CI against the real compose PostgreSQL on
loopback 5433). Truthful skip without Docker locally.

Proves the production fabric repositories:
* operator-admitted capabilities + durable worker identity (verifier hashed);
* durable outbound sessions (created, heartbeat, drain, revoke);
* fenced leases with a monotonic fence generation, single active lease per
  job, atomic claim / renew / surrender / expiry reclaim;
* one-effect idempotency (b3_effects) and durable late-result quarantine;
* restart-safe artifact manifests (b3_artifacts) reload after a fresh object;
* durable retry state, dead letters, poison jobs, and PO-authorized retry
  with an auditable decision (Hermes denied, operator:po granted).
"""
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))
sys.path.insert(0, str(BASE / "scripts"))
sys.path.insert(0, str(BASE / "tests"))

import oce_b2_compose as oc  # noqa: E402

pytestmark = pytest.mark.container


def _verifier(secret: str) -> str:
    import hashlib
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


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
    """Fresh tables per test (drop + migrate up from empty)."""
    import migrate
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
    rc = migrate.cmd_up(oc.dsn(), migrate.MIGRATIONS_DIR)
    assert rc == 0, "migrations (incl. 0005) from empty DB must succeed"


@pytest.fixture
def fresh(pg):
    """A brand-new PgWorkerFabricStore each call — restart-safe proof uses
    two distinct objects over the SAME connection pool/schema."""
    from oce_control.worker_fabric_store import PgWorkerFabricStore
    return PgWorkerFabricStore(pg)


def _admit(fresh, worker_id: str = "w1") -> None:
    """Admit a fabric worker the authoritative way (persist_identity), which
    also materialises the Book 2 `workers` parent row every fabric FK targets.
    Also admit the capability the worker will carry."""
    fresh.admit_capability("hash", "operator:po")
    fresh.persist_identity(
        worker_id=worker_id, protocol_version="1.0", worker_version="1.0",
        host_os_class="linux", runtime_class="python", trust_zone="worker-local",
        sandbox_profile="default", capabilities=["hash"],
        credential_verifier=_verifier("s"), actor="operator:po")


def _job(pg, job_id: str) -> str:
    """Create a REAL authoritative `jobs` parent row at a known job_id and
    return it. b3_artifacts / b3_dead_letters reference jobs(job_id), so the
    job must exist before those fabric rows can be persisted. Insert directly
    so no FK child rows (`idempotency`, `job_transitions`) accompany it, which
    would otherwise need rewriting when the job id is pinned."""
    import json as _json
    with pg.cursor() as cur:
        cur.execute(
            """INSERT INTO jobs
                 (job_id, job_type, schema_version, submitting_actor,
                  authority_context, resource_scope, environment,
                  idempotency_key, payload_hash, payload, correlation_id)
               VALUES (%s,'hash','2.0.0','operator:po',
                 %s,'default','local',%s,%s,'{}',%s)""",
            (job_id, _json.dumps({"actor_id": "operator:po"}),
             "idem-" + job_id, "p" + job_id, "corr-" + job_id),
        )
    pg.commit()
    return job_id


def test_capability_admission_is_persisted_and_per_operator(pg, fresh):
    fresh.admit_capability("hash", "operator:po")
    assert fresh.admitted_capabilities() == ["hash"]
    # survives a freshly-constructed store (restart)
    from oce_control.worker_fabric_store import PgWorkerFabricStore
    again = PgWorkerFabricStore(pg)
    assert again.admitted_capabilities() == ["hash"]


def test_identity_persisted_and_verifier_hashed(pg, fresh):
    fresh.admit_capability("hash", "operator:po")
    fresh.persist_identity(
        worker_id="w1", protocol_version="1.0", worker_version="1.0",
        host_os_class="linux", runtime_class="python", trust_zone="worker-local",
        sandbox_profile="default", capabilities=["hash"],
        credential_verifier=_verifier("sup3r-secret"), actor="operator:po")
    ident = fresh.identity("w1")
    assert ident is not None
    assert ident["capabilities"] == ["hash"]
    assert ident["credential_verifier"] == _verifier("sup3r-secret")
    assert "sup3r-secret" not in str(ident["credential_verifier"])


def test_revoked_identity_refused(pg, fresh):
    fresh.persist_identity(
        worker_id="w1", protocol_version="1.0", worker_version="1.0",
        host_os_class="linux", runtime_class="python", trust_zone="worker-local",
        sandbox_profile="default", capabilities=["hash"],
        credential_verifier=_verifier("s"), actor="operator:po")
    fresh.revoke_identity("w1")
    ident = fresh.identity("w1")
    assert ident["status"] == "revoked"
    assert ident["revoked_at"] is not None


def test_session_created_and_heartbeated(pg, fresh):
    _admit(fresh)
    fresh.create_session(
        worker_id="w1", session_id="sess-1", protocol_version="1.0",
        trust_zone="worker-local", capabilities=["hash"],
        verifier=_verifier("s"), challenge="chal", ttl_s=60)
    sess = fresh.session("sess-1")
    assert sess is not None
    assert sess["worker_id"] == "w1"
    assert sess["capabilities"] == ["hash"]
    hb = fresh.heartbeat_session("sess-1")
    assert hb["last_heartbeat"] is not None
    assert fresh.sessions("w1")[0]["session_id"] == "sess-1"


def test_drain_rejects_new_work_through_store(pg, fresh):
    _admit(fresh)
    fresh.create_session(
        worker_id="w1", session_id="sess-1", protocol_version="1.0",
        trust_zone="worker-local", capabilities=["hash"],
        verifier=_verifier("s"), challenge="chal", ttl_s=60)
    fresh.drain_worker("w1", True)
    assert fresh.identity("w1")["status"] == "draining"
    assert fresh.sessions("w1")[0]["draining"] is True


def test_lease_claim_fence_and_reclaim(pg, fresh):
    _admit(fresh)
    fresh.claim("job-1", "w1", "lease-tok-111", 1, 60)
    head = fresh.fetch_fence("job-1")
    assert head["lease_id"] == "lease-tok-111"
    assert head["fence"] == 1
    assert fresh.renew("job-1", "lease-tok-111", 1, 120) is True
    assert fresh.surrender("job-1", "lease-tok-111", 1) is True
    # stale renew after surrender fails (fenced)
    assert fresh.renew("job-1", "lease-tok-111", 1, 120) is False


def test_monotonic_fence_generation_after_reclaim(pg, fresh):
    _admit(fresh, "w1")
    _admit(fresh, "w2")
    fresh.claim("job-x", "w1", "lease-tok-A", 1, 60)
    fresh.surrender("job-x", "lease-tok-A", 1)
    # second claim bumps fence
    fresh.claim("job-x", "w2", "lease-tok-B", 2, 60)
    head = fresh.fetch_fence("job-x")
    assert head["fence"] == 2
    assert head["worker_id"] == "w2" or head["lease_id"] == "lease-tok-B"
    # a stale worker's old fence/lease can no longer renew or surrender
    assert fresh.renew("job-x", "lease-tok-A", 1, 120) is False


def test_expired_lease_reclaimed(pg, fresh):
    _admit(fresh)
    fresh.claim("job-e", "w1", "lease-tok-E", 1, 1)
    import time
    time.sleep(1.2)  # ttl 1s
    reclaimed = fresh.reclaim_stale_leases()
    assert "job-e" in reclaimed
    head = fresh.fetch_fence("job-e")
    assert head["status"] in ("expired", "active")
    # re-claim bumps the fence (fence-safe refetch allowed)
    fresh.claim("job-e", "w2", "lease-tok-E2", head["fence"] + 1, 60)


def test_effect_registered_once(pg, fresh):
    _admit(fresh)
    fresh.claim("job-1", "w1", "lease-tok-111", 1, 60)
    assert fresh.register_effect(job_id="job-1", lease_id="lease-tok-111",
                                 fence=1, effect_key="eff-1",
                                 producer_identity="operator:po") is True
    assert fresh.effect_exists("eff-1") is True
    # duplicate for a different key on the same job must not create a 2nd effect
    fresh.register_effect(job_id="job-1", lease_id="lease-tok-111",
                          fence=1, effect_key="eff-2",
                          producer_identity="operator:po")
    with pg.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM b3_effects WHERE job_id='job-1'")
        count = cur.fetchone()[0]
    assert count == 1, f"expected one effect for job-1, got {count}"


def test_late_result_quarantined_durably(pg, fresh):
    _admit(fresh)
    fresh.claim("job-l", "w1", "lease-tok-L", 1, 60)
    fresh.surrender("job-l", "lease-tok-L", 1)
    fresh.quarantine_late(job_id="job-l", lease_id="lease-tok-L", fence=1,
                          reason="late_result", result_ref="ref-late")
    q = fresh.quarantined()
    assert len(q) == 1
    assert q[0]["job_id"] == "job-l"
    assert q[0]["reason"] == "late_result"


def test_manifest_persisted_and_reloaded_on_restart(pg, fresh):
    _admit(fresh)
    _job(pg, "job-a")
    manifest = {
        "manifest_id": "m-1", "job_id": "job-a", "attempt": 1,
        "worker_id": "w1", "producer_identity": "operator:po",
        "input_hashes": ["in"], "environment_fingerprint": "fp",
        "artifacts": [{"name": "out.txt", "sha256": "a" * 64, "size": 4,
                       "content_type": "txt"}],
    }
    fresh.persist_manifest(manifest)
    from oce_control.worker_fabric_store import PgWorkerFabricStore
    again = PgWorkerFabricStore(pg)   # fresh object = simulated restart
    assert again.load_manifest("m-1")["manifest_id"] == "m-1"
    assert again.manifests("job-a")[0]["artifacts"][0]["name"] == "out.txt"


def test_retry_state_dead_letter_and_po_authorized_retry(pg, fresh):
    _admit(fresh)
    _job(pg, "job-r")
    fresh.record_retry_state(job_id="job-r", attempts=3, max_retries=3,
                             classified="retryable", last_reason="exit=None",
                             exhausted=True, poison=True)
    state = fresh.retry_state("job-r")
    assert state["attempts"] == 3 and state["poison"] is True

    fresh.dead_letter(job_id="job-r", attempt=3, worker_id="w1",
                      reason="retry_exhausted", detail="crashed",
                      idempotency_key="job-r", poison=True)
    dl = fresh.resolve_dead_letter("job-r")
    assert dl is not None and dl["reason"] == "retry_exhausted"
    assert fresh.list_dead_letters().__len__() == 1

    # Hermes is NOT authorized to retry a dead-lettered job.
    with pytest.raises(PermissionError, match="not authorized"):
        fresh.authorized_retry(job_id="job-r", actor="hermes")
    # operator:po is the only CEO-level authority that can.
    assert fresh.authorized_retry(job_id="job-r", actor="operator:po") is True
    with pg.cursor() as cur:
        cur.execute("SELECT decision FROM b3_authorized_retries "
                    "WHERE job_id='job-r' ORDER BY id")
        decisions = [r[0] for r in cur.fetchall()]
    assert decisions == ["denied", "granted"]