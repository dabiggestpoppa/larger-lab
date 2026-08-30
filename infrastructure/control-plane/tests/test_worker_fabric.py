"""Book 3 — worker fabric tests (B3-C1 contracts+identity, B3-C2 outbound
sessions, B3-C3 fenced leases + duplicate-safe delivery)."""
from __future__ import annotations
import pytest

from oce_control.worker_contracts import (SUPPORTED_PROTOCOLS, KNOWN_CAPABILITIES,
                                           ensure_supported_protocol, validate_identity_fields)
from oce_control.worker_fabric import (WorkerAuthority, WorkerIdentity, CapabilityRegistry,
                                       CapabilityAdmissionError, AdmissionRequest,
                                       SessionHost, OutboundSession, SessionError,
                                       SessionExpired, SessionRevoked, WorkerDraining,
                                       FabricScheduler, JobEnvelope, InMemoryLeaseStore,
                                       StaleFence, LateResult, DuplicateEffect)


def _admitted_authority() -> WorkerAuthority:
    reg = CapabilityRegistry()
    for cap in KNOWN_CAPABILITIES:
        reg.admit_capability(cap, "operator:po")
    return WorkerAuthority(reg)


def _request(**kw):
    base = dict(worker_id="wkr-1", public_key_or_nonce="nonce-abc",
                requested_capabilities=["hash", "compute-python"],
                protocol_version="1.0", host_os_class="linux",
                runtime_class="python", trust_zone="worker-local",
                worker_version="1.0")
    base.update(kw)
    return AdmissionRequest(**base)


# -- B3-C1 contracts & identity ------------------------------------------------

class TestContracts:
    def test_unsupported_protocol_fails_closed(self):
        with pytest.raises(ValueError):
            ensure_supported_protocol("99.0", "worker")

    def test_supported_protocol_ok(self):
        ensure_supported_protocol(SUPPORTED_PROTOCOLS[0], "worker")

    def test_unknown_capability_fails_closed(self):
        reg = CapabilityRegistry()
        reg.admit_capability("hash", "operator:po")
        with pytest.raises(CapabilityAdmissionError):
            reg.admit_capability("magic-unknown", "operator:po")

    def test_worker_cannot_self_authorize_without_operator_admission(self):
        reg = CapabilityRegistry()
        # registry empty → capability not admitted
        with pytest.raises(CapabilityAdmissionError):
            reg.check(["hash"])

    def test_identity_immutable_and_valid_json(self):
        au = _admitted_authority()
        ident = au.approve(_request(), actor="operator:po")
        assert isinstance(ident, WorkerIdentity)
        ok, errs = validate_identity_fields(ident.to_dict())
        assert ok, errs
        # immutability: frozen dataclass
        with pytest.raises(Exception):
            ident.capabilities = ()  # type: ignore[misc]

    def test_capability_escalation_refused(self):
        au = _admitted_authority()
        with pytest.raises(CapabilityAdmissionError):
            au.approve(_request(requested_capabilities=["not-admitted"]), actor="operator:po")

    def test_wrong_trust_zone_fails_closed(self):
        au = _admitted_authority()
        with pytest.raises(ValueError):
            au.approve(_request(trust_zone="rogue-zone"), actor="operator:po")


# -- B3-C2 outbound sessions ---------------------------------------------------

class TestOutboundSessions:
    def test_challenge_response_secret_never_transmitted(self):
        import oce_control.worker_fabric as wf
        import hashlib, hmac
        host = SessionHost(secret_ttl_seconds=300)
        au = _admitted_authority()
        ident = au.approve(_request(), actor="operator:po")
        secret = "the-shared-secret"
        sess = host.begin(ident, shared_secret=secret)
        # correct response proves knowledge of the secret (off-band):
        # response = hmac(sha256(secret), server_challenge)
        resp = hmac.new(wf._hash_secret(secret).encode("utf-8"),
                        sess.challenge.encode("utf-8"), hashlib.sha256).hexdigest()
        out = host.respond(sess.session_id, resp)
        assert out["authenticated"] is True
        # wrong response → reject
        wrong = hmac.new(b"wrong", sess.challenge.encode("utf-8"), hashlib.sha256).hexdigest()
        with pytest.raises(SessionError):
            host.respond(sess.session_id, wrong)
        # credential stored hashed (verifier = sha256(secret)), never plaintext
        stored = host._sessions[sess.session_id].secret_hash
        assert stored != secret
        assert stored == wf._hash_secret(secret)

    def test_session_expiration(self):
        host = SessionHost(secret_ttl_seconds=1)
        au = _admitted_authority()
        ident = au.approve(_request(), actor="operator:po")

        import oce_control.worker_contracts as wc
        sess = host.begin(ident, shared_secret="s2")
        s = host._sessions[sess.session_id]
        # simulate time passing beyond expiry
        s.expires_at = wc.utcnow_iso_after(-5)
        with pytest.raises(SessionExpired):
            host.heartbeat(sess.session_id)

    def test_revocation_kills_sessions(self):
        host = SessionHost()
        au = _admitted_authority()
        ident = au.approve(_request(), actor="operator:po")
        sess = host.begin(ident, shared_secret="s3")
        revoked = host.revoke("wkr-1")
        assert sess.session_id in revoked
        with pytest.raises(SessionRevoked):
            host.heartbeat(sess.session_id)

    def test_duplicate_session_bumps_generation(self):
        host = SessionHost()
        au = _admitted_authority()
        ident = au.approve(_request(), actor="operator:po")
        s1 = host.begin(ident, shared_secret="s")
        host.begin(ident, shared_secret="s")
        remaining = [s for s in host._sessions.values() if s.worker_id == "wkr-1"]
        assert len(remaining) == 1  # stale session dropped (duplicate-session handling)

    def test_drain_mode_blocks_work(self):
        host = SessionHost()
        au = _admitted_authority()
        ident = au.approve(_request(), actor="operator:po")
        sess = host.begin(ident, shared_secret="s")
        host.set_draining("wkr-1", True)
        with pytest.raises(WorkerDraining):
            host.heartbeat(sess.session_id)

    def test_unsupported_protocol_rejected_at_admission(self):
        au = _admitted_authority()
        with pytest.raises(ValueError):
            au.approve(_request(protocol_version="9.0"), actor="operator:po")


# -- B3-C3 fenced leases + duplicate-safe delivery ------------------------------

def _job(**kw):
    base = dict(job_id="job-1", job_type="b3.deterministic-hash",
                required_capabilities=["hash"],
                resource_envelope={"cpu_limit": 1, "memory_bytes": 1,
                                   "disk_bytes": 1, "timeout_s": 10},
                sandbox_profile="default")
    base.update(kw)
    return JobEnvelope(**base)


class TestFencedLeases:
    def test_atomic_claim_and_monotonic_fence(self):
        fs = FabricScheduler(store=InMemoryLeaseStore())
        j = _job()
        c1 = fs.claim(j, "wkr-1")
        assert c1["fence"] == 1
        assert len(c1["lease_id"]) >= 32
        # concurrent duplicate claim rejected
        with pytest.raises(Exception):
            fs.claim(j, "wkr-2")

    def test_stale_fence_rejected(self):
        fs = FabricScheduler(store=InMemoryLeaseStore())
        j = _job()
        fs.claim(j, "wkr-1")
        # an old/different token should not renew
        with pytest.raises(StaleFence):
            fs.renew(j.job_id, "forged-token", 999, ttl_s=30)

    def test_surrender_and_reclaim(self):
        fs = FabricScheduler(store=InMemoryLeaseStore())
        j = _job()
        c = fs.claim(j, "wkr-1")
        fs.surrender(j.job_id, c["lease_id"], c["fence"])
        # releasable again with a higher fence
        c2 = fs.claim(j, "wkr-2")
        assert c2["fence"] == c["fence"] + 1

    def test_late_result_quarantined(self):
        fs = FabricScheduler(store=InMemoryLeaseStore())
        j = _job()
        c = fs.claim(j, "wkr-1")
        fs.release(j.job_id)  # lease gone → result is late
        with pytest.raises(LateResult):
            fs.deliver_result(j.job_id, c["lease_id"], c["fence"], "e1", set())
        assert any(q["job_id"] == j.job_id for q in fs.quarantined_late)

    def test_duplicate_delivery_has_one_material_effect(self):
        fs = FabricScheduler(store=InMemoryLeaseStore())
        j = _job()
        c = fs.claim(j, "wkr-1")
        seen = set()
        r1 = fs.deliver_result(j.job_id, c["lease_id"], c["fence"], "effect-key", seen)
        assert r1["delivered"]
        # duplicate delivery of the same effect key → one material effect
        with pytest.raises(DuplicateEffect):
            fs.deliver_result(j.job_id, c["lease_id"], c["fence"], "effect-key", seen)

    def test_wrong_fence_is_stale_rejection(self):
        fs = FabricScheduler(store=InMemoryLeaseStore())
        j = _job()
        c = fs.claim(j, "wkr-1")
        # correct lease id but forged/stale generation → stale fence
        with pytest.raises(StaleFence):
            fs.deliver_result(j.job_id, c["lease_id"], 0, "e", set())

    def test_forged_lease_token_rejected(self):
        fs = FabricScheduler(store=InMemoryLeaseStore())
        j = _job()
        fs.claim(j, "wkr-1")
        with pytest.raises(LateResult):
            fs.deliver_result(j.job_id, "forged-token", 1, "e", set())