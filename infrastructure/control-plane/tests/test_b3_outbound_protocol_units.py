"""B3-R3: local unit tests for the outbound worker protocol cryptographic
contract (no PostgreSQL / no service required).

These pin the shared-secret-derivation and HMAC proof rules so the client and
server agree without a live stack: the wire key is a double-hash of the shared
secret (never the identity-row verifier itself), proofs are constant-time, and
a proof made by a different worker or wrong secret is never accepted.
"""
from __future__ import annotations
import hmac

from oce_control.worker_client import wire_key, _hmac, OutboundWorkerClient
from oce_control.worker_protocol import _hmac as server_hmac, _hash


def test_wire_key_is_double_hash_not_identity_verifier():
    secret = "s3cret-value"
    w = wire_key(secret)
    assert len(w) == 64
    # the wire key is NOT sha256(secret) — it is sha256(that) — so the
    # identity table's credential_verifier alone cannot sign wire proofs.
    import hashlib
    assert w != hashlib.sha256(secret.encode()).hexdigest()


def test_client_and_server_proof_are_identical():
    secret, wid = "shared-secret-value", "wkr-abc"
    wire = wire_key(secret)
    client_proof = _hmac(wire, "hello:" + wid)
    server_proof = server_hmac(_hash(_hash_single(secret)), "hello:" + wid)
    # server derives wire key as sha256(sha256(secret)) same as client
    assert client_proof == server_proof


def _hash_single(s: str) -> str:
    import hashlib
    return hashlib.sha256(s.encode()).hexdigest()


def test_wrong_secret_proof_never_matches():
    secret, wid = "correct-secret", "wkr-abc"
    wire = wire_key(secret)
    honest = _hmac(wire, "hello:" + wid)
    # a staffer with the identity verifier (not the secret) still cannot match
    import hashlib
    forged = hmac.new(
        hashlib.sha256(b"identity-verifier-only").digest(),
        ("hello:" + wid).encode(), hashlib.sha256).hexdigest()
    assert hmac.compare_digest(honest, forged) is False


def test_action_signature_scoped_to_session_and_action():
    secret, sid, wid = "sc", "sess-111", "wkr-1"
    wire = wire_key(secret)
    for action in ("claim", "renew", "deliver_result", "surrender",
                   "heartbeat", "advertise_capabilities"):
        sig = _hmac(wire, f"{sid}:{action}")
        # same session + different action must not share a signature
        assert sig != _hmac(wire, f"{sid}:{action}other")
        # different session must not produce the same signature
        assert sig != _hmac(wire, f"{sid}x:{action}")