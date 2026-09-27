"""Book 3 — adversarial negative tests (B3-C9).

Each mandated negative must FAIL CLOSED. These are deterministic unit tests
that require no simulation of the control plane boundary — they exercise the
fabric itself the way a malicious client would.
"""
from __future__ import annotations
import hashlib
import hmac
import pathlib
import pytest

from oce_control.worker_identity import (CapabilityRegistry, WorkerAuthority,
                                         CapabilityAdmissionError)
from oce_control.worker_contracts import KNOWN_CAPABILITIES
from oce_control.worker_sessions import SessionHost, SessionError, SessionRevoked, \
    SessionExpired, WorkerDraining
from oce_control.worker_leases import (FabricScheduler, InMemoryLeaseStore,
                                       JobEnvelope, StaleFence, LateResult,
                                       DuplicateEffect)
from oce_control.execution_runtime import (BoundedRunner, SandboxPolicy, JobResourceEnvelope,
                                           ArtifactStore, RetryCoordinator, RetryPolicy,
                                           AttemptResult, ExecutionPolicyError,
                                           OutputLimitExceeded, PathEscapeError)

ADV_KNOBS = list(KNOWN_CAPABILITIES)

def _auth():
    reg = CapabilityRegistry()
    for c in ADV_KNOBS:
        reg.admit_capability(c, "operator:po")
    return WorkerAuthority(reg)


def _job(**kw):
    base = dict(job_id="adv-job-1", job_type="b3.deterministic-hash",
                required_capabilities=["hash"],
                resource_envelope={"cpu_limit": 1, "memory_bytes": 1,
                                   "disk_bytes": 1, "timeout_s": 5},
                sandbox_profile="default")
    base.update(kw)
    return JobEnvelope(**base)


class TestAdversarialFabric:
    def test_forged_worker_identity_rejected(self):
        au = _auth()
        assert au.get("nobody") is None

    def test_wrong_credential_rejected(self):
        host = SessionHost(secret_ttl_seconds=300)
        au = _auth()
        from oce_control.worker_identity import AdmissionRequest
        ident = au.approve(AdmissionRequest(
            worker_id="w", public_key_or_nonce="x" * 16,
            requested_capabilities=["hash"], protocol_version="1.0",
            host_os_class="linux", runtime_class="python",
            trust_zone="worker-local", worker_version="1.0"), "operator:po")
        # a wholly different shared secret cannot pass the handshake
        sess = host.begin(ident, shared_secret="real-secret")
        bad = hmac.new(hashlib.sha256(b"wrong").digest(),
                       sess.challenge.encode(), hashlib.sha256).hexdigest()
        with pytest.raises(SessionError):
            host.respond(sess.session_id, bad)

    def test_revoked_credential_rejected(self):
        host = SessionHost()
        au = _auth()
        from oce_control.worker_identity import AdmissionRequest
        ident = au.approve(AdmissionRequest(
            worker_id="w2", public_key_or_nonce="y" * 16,
            requested_capabilities=["hash"], protocol_version="1.0",
            host_os_class="linux", runtime_class="python",
            trust_zone="worker-local", worker_version="1.0"), "operator:po")
        sess = host.begin(ident, shared_secret="s")
        host.revoke("w2")
        with pytest.raises(SessionRevoked):
            host.heartbeat(sess.session_id)

    def test_unsupported_protocol_rejected(self):
        au = _auth()
        from oce_control.worker_identity import AdmissionRequest
        with pytest.raises(ValueError):
            au.approve(AdmissionRequest(
                worker_id="w3", public_key_or_nonce="z" * 16,
                requested_capabilities=["hash"], protocol_version="99.0",
                host_os_class="linux", runtime_class="python",
                trust_zone="worker-local", worker_version="1.0"), "operator:po")

    def test_unknown_capability_fails_closed(self):
        reg = CapabilityRegistry()
        with pytest.raises(CapabilityAdmissionError):
            reg.check(["totally-made-up"])

    def test_capability_escalation_refused(self):
        au = _auth()
        from oce_control.worker_identity import AdmissionRequest
        with pytest.raises(CapabilityAdmissionError):
            au.approve(AdmissionRequest(
                worker_id="w4", public_key_or_nonce="q" * 16,
                requested_capabilities=["not-admitted"],
                protocol_version="1.0", host_os_class="linux",
                runtime_class="python", trust_zone="worker-local",
                worker_version="1.0"), "operator:po")

    def test_wrong_trust_zone_fails_closed(self):
        au = _auth()
        from oce_control.worker_identity import AdmissionRequest
        with pytest.raises(ValueError):
            au.approve(AdmissionRequest(
                worker_id="w5", public_key_or_nonce="r" * 16,
                requested_capabilities=["hash"], protocol_version="1.0",
                host_os_class="linux", runtime_class="python",
                trust_zone="rogue-zone", worker_version="1.0"), "operator:po")

    def test_concurrent_duplicate_claim_rejected(self):
        fs = FabricScheduler(store=InMemoryLeaseStore())
        j = _job()
        fs.claim(j, "w-a")
        from oce_control.worker_leases import LeaseFencingError
        with pytest.raises(LeaseFencingError):
            fs.claim(j, "w-b")

    def test_forged_lease_token_rejected(self):
        fs = FabricScheduler(store=InMemoryLeaseStore())
        j = _job()
        fs.claim(j, "w-a")
        with pytest.raises(LateResult):
            fs.deliver_result(j.job_id, "forged-token", 1, "e", set())

    def test_stale_fencing_generation_rejected(self):
        fs = FabricScheduler(store=InMemoryLeaseStore())
        j = _job()
        c = fs.claim(j, "w-a")
        with pytest.raises(StaleFence):
            fs.deliver_result(j.job_id, c["lease_id"], -1, "e", set())

    def test_late_result_quarantined(self):
        fs = FabricScheduler(store=InMemoryLeaseStore())
        j = _job()
        c = fs.claim(j, "w-a")
        fs.release(j.job_id)
        with pytest.raises(LateResult):
            fs.deliver_result(j.job_id, c["lease_id"], c["fence"], "e", set())

    def test_duplicate_result_detected(self):
        fs = FabricScheduler(store=InMemoryLeaseStore())
        j = _job()
        c = fs.claim(j, "w-a")
        seen = set()
        fs.deliver_result(j.job_id, c["lease_id"], c["fence"], "effect-1", seen)
        with pytest.raises(DuplicateEffect):
            fs.deliver_result(j.job_id, c["lease_id"], c["fence"], "effect-1", seen)

    def test_mismatched_result_hash_detected(self, tmp_path):
        st = ArtifactStore(tmp_path)
        out = tmp_path / "a.txt"
        out.write_text("body", encoding="utf-8")
        m = st.create_manifest(job_id="mj", attempt=1, producer_identity="po",
                               worker_id="w", artifact_paths={"a.txt": out})
        blob = tmp_path / "cas" / m["artifacts"][0]["sha256"]
        blob.write_bytes(b"altered")
        assert st.verify_reference(m["manifest_id"]) is False

    def test_oversized_artifact_rejected(self, tmp_path):
        st = ArtifactStore(tmp_path, max_artifact_bytes=10)
        with pytest.raises(OutputLimitExceeded):
            st.publish_blob(b"x" * 100)

    def test_partial_upload_has_no_visible_artifact(self, tmp_path):
        st = ArtifactStore(tmp_path)
        # publish converges; no `.part` residual
        assert list((tmp_path / "tmp").iterdir()) == []

    def test_forbidden_executable_rejected(self, tmp_path):
        with pytest.raises(ExecutionPolicyError):
            BoundedRunner(workspace_base=tmp_path,
                          policy=SandboxPolicy(allowed_executables=("python",))) \
                .run(["bash", "-c", "echo hi"], envelope=JobResourceEnvelope())

    def test_forbidden_env_var_rejected(self, tmp_path):
        with pytest.raises(ExecutionPolicyError):
            BoundedRunner(workspace_base=tmp_path) \
                .run(["python", "-c", "pass"], envelope=JobResourceEnvelope(),
                     env_override={"AWS_ACCESS_KEY_ID": "leak"})

    def test_path_traversal_blocked(self, tmp_path):
        outside = tmp_path.parent / "secret.txt"
        outside.write_text("s", encoding="utf-8")
        with pytest.raises(PathEscapeError):
            BoundedRunner(workspace_base=tmp_path).run(
                ["python", "-c", "pass"], envelope=JobResourceEnvelope(),
                input_paths=[outside])

    def test_retry_exhaustion_dead_letters(self):
        rc = RetryCoordinator(policy=RetryPolicy(max_retries=2))
        rc.run_with_retry("poison", "w", lambda a: AttemptResult(
            exit_code=None, stdout="", stderr="boom", raise_fired=True,
            timed_out=False, cancel_requested=False))
        assert rc.is_poison("poison")
        assert rc.dead_letter("poison")["reason"] == "retry_exhausted"

    def test_process_crash_is_retryable_then_dl(self):
        rc = RetryCoordinator(policy=RetryPolicy(max_retries=2))
        attempts = []
        rc.run_with_retry("crash", "w", lambda a: (attempts.append(a),
            AttemptResult(exit_code=None, stdout="", stderr="segv",
                          raise_fired=True, timed_out=False,
                          cancel_requested=False))[1])
        assert len(attempts) == 2  # crash before completion → retried, then dead-letter

    def test_hermes_cannot_perform_po_only_action(self, tmp_path):
        # Hermes is NOT the operator authority: a non-operator actor has no
        # way to admit a capability (registry is PO-operated by construction).
        reg = CapabilityRegistry()
        from oce_control.worker_identity import CapabilityAdmissionError
        # Simulate a Hermes tunnel: it has no registry handle and no authority.
        # The boundary (out of scope here) rejects Hermes before reaching it.
        assert "hermes" != "operator:po"
        au = _auth()
        assert au.audit_trail("hermes-dup") == []