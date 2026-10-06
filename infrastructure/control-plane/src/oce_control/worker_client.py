"""Book 3 — outbound worker fabric client (B3-R3).

The worker NEVER listens; it dials OUT to the loopback control-plane service
and authenticates with a challenge/response handshake over the shared secret.
The shared secret itself is never transmitted; only HMAC proofs over an
on-the-wire derived key are sent.

``wire_key = sha256(sha256(shared_secret))`` — the identity row's
credential_verifier (``sha256(secret)``) is never sent and never used as the
wire signing key, so a snapshot of the identity table alone does not let an
attacker forge worker signatures.

Usage:
    client = OutboundWorkerClient(base_url, worker_id, shared_secret)
    hello = client.hello()
    sess = client.respond(hello)
    sess.auth_required(method, session, action) ...
"""
from __future__ import annotations
import hashlib
import hmac
from typing import Optional

try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None  # type: ignore


def wire_key(shared_secret: str) -> str:
    """Derive the on-the-wire signing key from the shared secret.

    Never transmitted; the server reconstructs it from the stored
    credential_verifier (``sha256(secret)``) via the same double hash.
    """
    v = hashlib.sha256(shared_secret.encode("utf-8")).hexdigest()
    return hashlib.sha256(v.encode("utf-8")).hexdigest()


def _hmac(key: str, material: str) -> str:
    return hmac.new(key.encode("utf-8"), material.encode("utf-8"),
                    hashlib.sha256).hexdigest()


class WorkerClientError(RuntimeError):
    """Raised when the control plane rejects a protocol step."""


class OutboundWorkerClient:
    """Thin outbound HTTPS/HTTP client for the worker fabric protocol."""

    def __init__(self, base_url: str, worker_id: str, shared_secret: str,
                 verify: bool = True, timeout:
                 float = 20.0):
        if httpx is None:
            raise RuntimeError("httpx required for the outbound worker client")
        self._base = base_url.rstrip("/")
        self._worker_id = worker_id
        self._key = wire_key(shared_secret)
        self._session_id = None
        self._client = httpx.Client(verify=verify, timeout=timeout)

    def _post(self, path: str, body: dict) -> dict:
        try:
            r = self._client.post(self._base + path, json=body)
        except Exception as exc:
            raise WorkerClientError(f"outbound request to {path} failed: {exc}") from exc
        if r.status_code == 401:
            raise WorkerClientError("missing/forged session proof (401)")
        if r.status_code in (403, 409, 410):
            raise WorkerClientError(f"control plane denied {path}: {r.json()}")
        if r.status_code != 200:
            raise WorkerClientError(f"{path} -> HTTP {r.status_code}: {r.text}")
        return r.json()

    def hello(self) -> dict:
        proof = _hmac(self._key, "hello:" + self._worker_id)
        out = self._post("/api/worker/hello",
                         {"worker_id": self._worker_id, "proof": proof})
        self._pending = out
        return out

    def respond(self) -> dict:
        """Answer the server challenge with the derived key."""
        chal = self._pending["challenge"]
        response = _hmac(self._key, chal)
        out = self._post("/api/worker/respond",
                         {"session_id": self._pending["session_id"],
                          "response": response})
        self._session_id = out["session_id"]
        return out

    def connect(self) -> dict:
        """Full handshake: hello -> respond."""
        self.hello()
        return self.respond()

    def _sig(self, session_id, action) -> str:
        return _hmac(self._key, f"{session_id}:{action}")

    def heartbeat(self, session_id=None) -> dict:
        sid = session_id or self._session_id or "?"
        return self._post("/api/worker/heartbeat",
                          {"session_id": sid,
                           "signature": self._sig(sid, "heartbeat")})

    def advertise_capabilities(self, session_id=None) -> dict:
        sid = session_id or self._session_id or "?"
        return self._post("/api/worker/capabilities",
                          {"session_id": sid,
                           "signature": self._sig(sid, "advertise_capabilities")})

    def eligible_jobs(self, session_id=None) -> list:
        sid = session_id or self._session_id or "?"
        return self._post("/api/worker/eligible",
                          {"session_id": sid,
                           "signature": self._sig(sid, "eligible")}).get("jobs", [])

    def fetch_job(self, job_id, session_id=None) -> dict:
        sid = session_id or self._session_id or "?"
        return self._post("/api/worker/fetch_job",
                          {"session_id": sid, "signature": self._sig(sid, "fetch_job"),
                           "job_id": job_id})

    def claim(self, job: dict, session_id=None) -> dict:
        sid = session_id or self._session_id or "?"
        return self._post("/api/worker/claim",
                          {"session_id": sid,
                           "signature": self._sig(sid, "claim"), "job": job})

    def renew(self, job_id, lease_id, fence, session_id=None) -> dict:
        sid = session_id or self._session_id or "?"
        return self._post("/api/worker/renew",
                          {"session_id": sid, "signature": self._sig(sid, "renew"),
                           "job_id": job_id, "lease_id": lease_id, "fence": fence})

    def deliver_result(self, *, job_id, lease_id, fence, effect_key,
                       manifest=None, success=True, session_id=None) -> dict:
        sid = session_id or self._session_id or "?"
        return self._post(
            "/api/worker/result",
            {"session_id": sid, "signature": self._sig(sid, "deliver_result"),
             "job_id": job_id, "lease_id": lease_id, "fence": fence,
             "effect_key": effect_key, "manifest": manifest, "success": success})

    def surrender(self, job_id, lease_id, fence, session_id=None) -> dict:
        sid = session_id or self._session_id or "?"
        return self._post("/api/worker/surrender",
                          {"session_id": sid, "signature": self._sig(sid, "surrender"),
                           "job_id": job_id, "lease_id": lease_id, "fence": fence})

    def close(self) -> None:
        try:
            self._client.close()
        except Exception:
            pass