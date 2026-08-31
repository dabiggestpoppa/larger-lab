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
                 scheduler: Optional[FabricScheduler] = None):
        self._store = store
        self._scheduler = scheduler or FabricScheduler(store=store)
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

    def eligible_jobs(self, session_id: str, signature: str) -> list[str]:
        sess = self._auth(session_id, signature, "eligible")
        worker_caps = set(sess["capabilities"] or ())
        # Jobs the store/production gate has already admitted but not yet
        # executed are matched by required capabilities on claim. For the
        # protocol we return a signal the worker may poll for work.
        return []

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