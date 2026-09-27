"""Book 3 Worker Fabric — authenticated outbound worker sessions (B3-C2).

Workers dial OUT to a loopback control plane; there is no worker public
inbound port. Session establishment is challenge/response so the shared
secret is never transmitted, and credentials are stored hashed
(``verifier = sha256(secret)``). The protocol supports session expiration,
credential rotation and revocation, reconnect, heartbeat + liveness
timeout, duplicate-session handling, and worker drain mode.
"""
from __future__ import annotations
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from typing import Optional

from .worker_contracts import utcnow_iso, utcnow_iso_after, dt_pass
from .worker_identity import WorkerIdentity


def _hmac_sign(secret: str, material: str) -> str:
    return hmac.new(secret.encode("utf-8"), material.encode("utf-8"),
                    hashlib.sha256).hexdigest()


def _hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


class SessionError(RuntimeError):
    """Base for outbound-session protocol errors."""


class SessionExpired(SessionError):
    pass


class SessionRevoked(SessionError):
    pass


class WorkerDraining(SessionError):
    pass


@dataclass
class OutboundSession:
    """A server-side session record for one authenticated outbound worker."""
    session_id: str             # unguessable
    worker_id: str
    protocol_version: str
    trust_zone: str
    capabilities: tuple[str, ...]
    challenge: str              # server nonce
    secret_hash: str            # sha256(shared_secret) — hashed at rest
    created_at: str
    expires_at: str
    last_heartbeat: Optional[str] = None
    revoked_at: Optional[str] = None
    draining: bool = False
    generation: int = 1

    def expired(self, now: str) -> bool:
        return now >= self.expires_at

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "worker_id": self.worker_id,
            "protocol_version": self.protocol_version,
            "trust_zone": self.trust_zone,
            "capabilities": list(self.capabilities),
            "challenge": self.challenge,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "last_heartbeat": self.last_heartbeat,
            "revoked_at": self.revoked_at,
            "draining": self.draining,
            "generation": self.generation,
        }


class SessionHost:
    """Server side of the outbound-only session protocol (B3-C2)."""

    def __init__(self, secret_ttl_seconds: int = 300,
                 liveness_seconds: int = 45):
        self._ttl = secret_ttl_seconds
        self._liveness = liveness_seconds
        self._sessions: dict[str, OutboundSession] = {}

    # -- establishment --------------------------------------------------------

    def begin(self, identity: WorkerIdentity,
              shared_secret: Optional[str] = None) -> OutboundSession:
        """Initiate a session for an admitted worker sharing an out-of-band
        secret. The server returns an unguessable challenge (nonce)."""
        if not shared_secret:
            raise SessionError("session establishment requires a shared secret")
        return self._new_session(identity, shared_secret)

    def _new_session(self, identity: WorkerIdentity,
                     shared_secret: str) -> OutboundSession:
        verifier = _hash_secret(shared_secret)     # sha256(S) — hashed at rest
        challenge = secrets.token_hex(16)          # server nonce
        session = OutboundSession(
            session_id=secrets.token_hex(16),
            worker_id=identity.worker_id,
            protocol_version=identity.protocol_version,
            trust_zone=identity.trust_zone,
            capabilities=identity.capabilities,
            challenge=challenge,
            secret_hash=verifier,
            created_at=utcnow_iso(),
            expires_at=utcnow_iso_after(self._ttl),
        )
        # Duplicate session for the same worker: drop the stale one.
        stale = [s.session_id for s in self._sessions.values()
                 if s.worker_id == identity.worker_id]
        for sid in stale:
            self._sessions.pop(sid, None)
        self._sessions[session.session_id] = session
        return session

    def respond(self, session_id: str, response: str,
                now: Optional[str] = None) -> dict:
        """Verify the worker's challenge/response using the stored verifier."""
        sess = self._sessions.get(session_id)
        if sess is None:
            raise SessionError("unknown session")
        if sess.is_revoked:
            raise SessionRevoked(f"session for '{sess.worker_id}' revoked")
        now = now or utcnow_iso()
        if sess.expired(now):
            raise SessionExpired("session expired during handshake")
        expect = _hmac_sign(sess.secret_hash, sess.challenge)
        if not hmac.compare_digest(expect, response):
            raise SessionError("handshake response does not match challenge")
        sess.generation += 1
        sess.last_heartbeat = now
        return {"session_id": session_id, "worker_id": sess.worker_id,
                "generation": sess.generation, "authenticated": True}

    def heartbeat(self, session_id: str, now: Optional[str] = None) -> OutboundSession:
        sess = self._session_or_error(session_id)
        now = now or utcnow_iso()
        if sess.expired(now):
            raise SessionExpired(f"session for '{sess.worker_id}' expired")
        sess.last_heartbeat = now
        return sess

    def rotate_secret(self, session_id: str) -> dict:
        """Rotate the session secret; returns the NEW secret to deliver over an
        already-authenticated outbound channel (off-band)."""
        sess = self._session_or_error(session_id)
        new_secret = secrets.token_urlsafe(32)
        sess.secret_hash = _hash_secret(new_secret)
        sess.generation += 1
        return {"session_id": session_id, "new_secret": new_secret,
                "generation": sess.generation}

    def revoke(self, worker_id: str) -> list:
        """Revoke all sessions for a worker. Returns revoked session IDs."""
        revoked = []
        for sid in list(self._sessions):
            if self._sessions[sid].worker_id == worker_id:
                self._sessions[sid].revoked_at = utcnow_iso()
                self._sessions[sid].generation += 1
                revoked.append(sid)
        return revoked

    def set_draining(self, worker_id: str, draining: bool) -> None:
        for sid in list(self._sessions):
            if self._sessions[sid].worker_id == worker_id:
                self._sessions[sid].draining = draining

    def _session_or_error(self, session_id: str) -> OutboundSession:
        sess = self._sessions.get(session_id)
        if sess is None:
            raise SessionError("unknown session")
        if sess.is_revoked:
            raise SessionRevoked(f"session for '{sess.worker_id}' revoked")
        if sess.draining:
            raise WorkerDraining(f"worker '{sess.worker_id}' is draining")
        return sess

    def prune_expired(self, now: Optional[str] = None) -> int:
        """Drop sessions past their expiry or liveness window."""
        now = now or utcnow_iso()
        dropped = 0
        for sid in list(self._sessions):
            sess = self._sessions[sid]
            if sess.expired(now):
                self._sessions.pop(sid, None)
                dropped += 1
            elif sess.last_heartbeat and dt_pass(now, sess.last_heartbeat,
                                                 self._liveness):
                self._sessions.pop(sid, None)
                dropped += 1
        return dropped

    def sessions(self, worker_id: Optional[str] = None) -> list[dict]:
        out = [s.to_dict() for s in self._sessions.values()
               if worker_id is None or s.worker_id == worker_id]
        return sorted(out, key=lambda s: s["created_at"])