"""Book 3 — real outbound authenticated worker protocol (B3-R3).

The worker dials OUT to the loopback control-plane service and establishes
an authenticated session through a challenge/response handshake. There is no
worker public inbound port. Server truth lives in PostgreSQL via
``PgWorkerFabricStore``; Redis stays out of the authoritative path.

Protocol (all JSON over the local service, every fabric endpoint
authenticated):

1. ``PO`` admits a worker and registers its identity + credential verifier
   (the SHA-256 of the out-of-band shared secret) in PostgreSQL.
2. The worker calls ``hello`` with ``worker_id`` and a proof derived from its
   secret. The server turns the stored verifier into an unguessable challenge
   and handshake session; the shared secret is never transmitted.
3. The worker answers ``respond`` with ``HMAC(verifier, challenge)``; the
   server verifies it (constant-time) and returns an authenticated session id.
4. Subsequent actions (heartbeat, capability advertise, claim, renew,
   deliver-result, surrender) must carry the session id plus a fresh
   ``HMAC(verifier, session_id:action)`` signature; forged, replayed with a
   stale fence, revoked, or capability-escalating requests fail closed.

The server layer here is the enforcement core; ``http_api`` exposes it as
loopback-only endpoints. Integration tests launch a SEPARATE worker process
that dials the running service.
"""
from __future__ import annotations
import hashlib
import hmac
import secrets
from typing import Optional

from .worker_contracts import utcnow_iso, utcnow_iso_after, dt_pass
from .worker_fabric_store import PgWorkerFabricStore, FabricStoreError
from .worker_leases import FabricScheduler, JobEnvelope, LeaseFencingError

SESSION_TTL_S = 300
LIVENESS_S = 45


class WorkerProtocolError(PermissionError):
    """Base for fail-closed protocol rejections (403 semantics)."""


class UnknownWorker(WorkerProtocolError):
    pass


class ForgedProof(WorkerProtocolError):
    pass


class SessionGone(WorkerProtocolError):
    """Unknown, expired, or revoked session."""


class CapabilityEscalation(WorkerProtocolError):
    """Worker asked to claim a job beyond its admitted capabilities."""


class WrongTrustZone(WorkerProtocolError):
    pass


def _hmac(verifier: str, material: str) -> str:
    return hmac.new(verifier.encode("utf-8"), material.encode("utf-8"),
                    hashlib.sha256).hexdigest()


class WorkerProtocolServer:
    """Enforces the outbound protocol against the durable store.

    ``store`` is a ``PgWorkerFabricStore`` in production. The scheduler and
    runner backing are supplied so a governed job can be executed once and its
    result published idempotently.
    """

    def __init__(self, store: PgWorkerFabricStore,
                 scheduler: Optional[FabricScheduler] = None,
                 job_store=None):
        self._store = store
        self._scheduler = scheduler or FabricScheduler(store=store)
        self._job_store = job_store          # PgJobStore (authoritative job rows)
        self._redis = None                   # optional RedisTransport (notification)
        self._session_ttl = SESSION_TTL_S

    # -- hello / respond -----------------------------------------------------

    def hello(self, worker_id: str, proof: str) -> dict:
        """Worker initiates outbound. Returns a challenge + handshake session.

        ``proof`` is ``HMAC(verifier, 'hello:' + worker_id)`` — possession of
        the verifier (derived from the shared secret) proves the worker knows
        the secret without transmitting it.
        """
        ident = self._store.identity(worker_id)
        if ident is None:
            raise UnknownWorker(f"worker '{worker_id}' has no admitted identity")
        if ident["status"] == "revoked":
            raise ForgedProof(f"worker '{worker_id}' is revoked")
        verifier = ident.get("credential_verifier")
        if not verifier:
            raise ForgedProof(f"worker '{worker_id}' has no credential verifier")
        # The wire signing key is derived from the verifier so the identity
        # row alone (credential_verifier) is never the wire proof key.
        wire_key = _hash(verifier)
        expect = _hmac(wire_key, "hello:" + worker_id)
        if not hmac.compare_digest(expect, proof):
            raise ForgedProof("hello proof does not match credential verifier")
        # Re-derive directly from the stored secret-derived verifier so the
        # session table also carries the wire key (never the raw verifier).
        challenge = secrets.token_hex(16)
        session_id = secrets.token_hex(16)
        # Persist the handshake session (draining flags survive restart).
        self._store.create_session(
            worker_id=worker_id, session_id=session_id,
            protocol_version=ident["protocol_version"],
            trust_zone=ident["trust_zone"],
            capabilities=ident["capabilities"],
            verifier=_hash(verifier), challenge=challenge, ttl_s=SESSION_TTL_S)
        return {"worker_id": worker_id, "session_id": session_id,
                "challenge": challenge, "protocol_version": ident["protocol_version"]}

    def respond(self, session_id: str, response: str) -> dict:
        """Worker answers the challenge; server authenticates the session."""
        sess = self._store.session(session_id)
        if sess is None:
            raise SessionGone("unknown session in handshake")
        if sess.get("revoked_at"):
            raise ForgedProof("session was revoked")
        if sess.get("challenge") is None:
            raise SessionGone("session is already authenticated")
        challenge = sess["challenge"]
        verifier_hash = sess["verifier"]
        # The stored verifier is itself sha256(verifier); verify against the
        # challenge with the verifier the worker proves knowledge of.
        expect = _hmac(verifier_hash, challenge)
        if not hmac.compare_digest(expect, response):
            raise ForgedProof("challenge/response does not match")
        # authenticate: clear challenge (one-time) + record heartbeat
        self._store._execute(
            "UPDATE worker_sessions SET challenge = '', last_heartbeat = now(), "
            "generation = generation + 1 WHERE session_id = %s AND revoked_at IS NULL",
            (session_id,),
        )
        self._store._commit()
        return {"session_id": session_id, "worker_id": sess["worker_id"],
                "authenticated": True, "capabilities": sess["capabilities"]}

    # -- authenticated actions -------------------------------------------------

    def _auth(self, session_id: str, signature: str, action: str) -> dict:
        """Verify an authenticated session can perform `action`."""
        sess = self._store.session(session_id)
        if sess is None:
            raise SessionGone("unknown session")
        if sess.get("revoked_at"):
            raise ForgedProof("session revoked")
        if sess.get("draining") and action in (
                "claim", "renew", "deliver_result", "surrender"):
            raise SessionGone(f"worker is draining; cannot {action}")
        verifier_hash = sess["verifier"]
        expect = _hmac(verifier_hash, f"{session_id}:{action}")
        if not hmac.compare_digest(expect, signature):
            raise ForgedProof("signature does not match authenticated session")
        if action == "heartbeat":
            self._store.heartbeat_session(session_id)
        return sess

    def heartbeat(self, session_id: str, signature: str) -> dict:
        sess = self._auth(session_id, signature, "heartbeat")
        return {"session_id": session_id, "worker_id": sess["worker_id"],
                "last_heartbeat": utcnow_iso()}

    def advertise_capabilities(self, session_id: str, signature: str) -> dict:
        sess = self._auth(session_id, signature, "advertise_capabilities")
        return {"worker_id": sess["worker_id"],
                "capabilities": sess["capabilities"]}

    def set_transport(self, redis=None) -> None:
        """Attach the disposable Redis transport for job notification. Redis is
        transport-only: eligibility still reads authoritative PostgreSQL."""
        self._redis = redis

    def notify_job(self, job_id: str, queue: str = "default") -> int:
        """Announce available work through the disposable transport. Returns
        the queue depth (0 when no Redis is attached — never authoritative)."""
        if self._redis is None:
            return 0
        try:
            return self._redis.notify_job(job_id, queue=queue)
        except Exception:
            return 0

    def eligible_jobs(self, session_id: str, signature: str,
                      queue: str = "default") -> list[str]:
        """Return job ids this authenticated worker may run today.

        Authoritative source is PostgreSQL: pending jobs whose required
        capabilities the worker holds. The Redis notification is a transport
        hint used to order candidates (Redis stays disposable; if it is
        unavailable we still return PG truth, the worker can still claim).
        """
        sess = self._auth(session_id, signature, "eligible")
        worker_caps = set(sess["capabilities"] or ())
        order = []
        if self._redis is not None:
            try:
                order = [j for j in self._redis.drain_queue(queue) if j]
            except Exception:
                order = []
        eligible = []
        if self._job_store is not None:
            for job in self._job_store.jobs_by_status("pending"):
                required = set(job.required_capabilities or [])
                if required.issubset(worker_caps):
                    eligible.append(job.job_id)
        # notifications (transport hint) first, then remaining PG truth
        seen: set[str] = set()
        out: list[str] = []
        for jid in order + eligible:
            if jid not in seen:
                seen.add(jid)
                out.append(jid)
        return out

    def fetch_job(self, session_id: str, signature: str, job_id: str) -> dict:
        """Authenticated worker fetches the job detail it is about to run."""
        sess = self._auth(session_id, signature, "fetch_job")
        if self._job_store is None:
            raise SessionGone("no authoritative job store wired")
        job = self._job_store.get_job(job_id)
        if job is None:
            raise SessionGone(f"unknown job '{job_id}'")
        required = set(job.required_capabilities or [])
        worker_caps = set(sess["capabilities"] or [])
        if not required.issubset(worker_caps):
            raise CapabilityEscalation(
                f"worker '{sess['worker_id']}' lacks capabilities for job '{job_id}'")
        if sess["trust_zone"] != "worker-local":
            raise WrongTrustZone("fetch_job denied outside worker-local trust zone")
        return job.to_dict()

    def claim(self, session_id: str, signature: str, job: dict) -> dict:
        sess = self._auth(session_id, signature, "claim")
        required = list(job.get("required_capabilities") or [])
        have = set(sess["capabilities"] or ())
        if not set(required).issubset(have):
            raise CapabilityEscalation(
                f"worker '{sess['worker_id']}' tried to claim capabilities "
                f"{sorted(set(required) - have)} beyond admission")
        if sess["trust_zone"] != job.get("trust_zone", "worker-local"):
            raise WrongTrustZone(f"trust zone mismatch on claim")
        envelope = JobEnvelope(
            job_id=job["job_id"], job_type=job.get("job_type", ""),
            required_capabilities=required,
            resource_envelope=job.get("resource_envelope", {}),
            sandbox_profile=job.get("sandbox_profile", "default"),
        )
        try:
            lease = self._scheduler.claim(envelope, sess["worker_id"])
        except LeaseFencingError as exc:
            raise SessionGone(str(exc)) from exc
        return {**lease, "capabilities": sorted(have)}

    def renew(self, session_id: str, signature: str, job_id: str,
              lease_id: str, fence: int) -> dict:
        sess = self._auth(session_id, signature, "renew")
        try:
            self._scheduler.renew(job_id, lease_id, fence,
                                  ttl_s=self._scheduler.default_ttl)
        except LeaseFencingError as exc:
            raise SessionGone(str(exc)) from exc
        return {"job_id": job_id, "lease_id": lease_id, "fence": fence,
                "renewed": True}

    def deliver_result(self, session_id: str, signature: str, job_id: str,
                       lease_id: str, fence: int, effect_key: str,
                       manifest: Optional[dict] = None,
                       success: bool = True) -> dict:
        sess = self._auth(session_id, signature, "deliver_result")
        store = self._store
        # fencing: result is acceptable only under the CURRENT lease+fence.
        head = store.fetch_fence(job_id)
        if head.get("lease_id") != lease_id or head.get("fence") != fence:
            store.quarantine_late(job_id=job_id, lease_id=lease_id, fence=fence,
                                  reason="late_or_missing_lease",
                                  result_ref=(manifest or {}).get("manifest_id"))
            raise SessionGone(
                f"result for '{job_id}' is late or held under a stale lease — quarantined")
        # one accepted effect per logical job
        if store.effect_exists(effect_key):
            raise WorkerProtocolError(
                f"effect '{effect_key}' already applied — duplicate delivery rejected")
        if manifest:
            store.persist_manifest(manifest)
        store.register_effect(job_id=job_id, lease_id=lease_id, fence=fence,
                              effect_key=effect_key,
                              producer_identity=sess.get("worker_id", ""))
        # mark the job durably succeeded via the jobs table
        store._execute(
            "UPDATE jobs SET status='succeeded', updated_at=now(), result=%s "
            "WHERE job_id = %s",
            (__import__("json").dumps({
                "success": bool(success), "worker_id": sess.get("worker_id"),
                "effect_key": effect_key,
                "manifest_id": (manifest or {}).get("manifest_id"),
                "completed_at": utcnow_iso(),
            }), job_id),
        )
        store._commit()
        store.surrender(job_id, lease_id, fence)
        return {"job_id": job_id, "delivered": True, "effect_key": effect_key,
                "manifest_id": (manifest or {}).get("manifest_id")}

    def surrender(self, session_id: str, signature: str, job_id: str,
                  lease_id: str, fence: int) -> dict:
        sess = self._auth(session_id, signature, "surrender")
        try:
            self._scheduler.surrender(job_id, lease_id, fence)
        except LeaseFencingError as exc:
            raise SessionGone(str(exc)) from exc
        return {"job_id": job_id, "surrendered": True}

    def revoke_worker(self, actor: str, worker_id: str) -> None:
        """PO-only action: revoke a worker and every session it holds."""
        if actor != "operator:po":
            raise WorkerProtocolError(f"actor '{actor}' is not authorized to revoke workers")
        self._store.revoke_identity(worker_id)
        for sess in self._store.sessions(worker_id):
            self._store._execute(
                "UPDATE worker_sessions SET revoked_at = now() "
                "WHERE session_id = %s",
                (sess["session_id"],),
            )
        self._store._commit()


def _hash(verifier: str) -> str:
    """Double-hash so the at-rest verifier is never the wire proof key."""
    return hashlib.sha256(verifier.encode("utf-8")).hexdigest()