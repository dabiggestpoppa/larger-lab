"""Book 3 — bounded runtime (B3-C4), immutable artifacts (B3-C5),
retry/dead-letter (B3-C6) tests."""
from __future__ import annotations
import json
import platform
from pathlib import Path
import pytest

from oce_control.execution_runtime import (BoundedRunner, SandboxPolicy, JobResourceEnvelope,
                                          ArtifactStore, RetryCoordinator, RetryPolicy,
                                          AttemptResult, ExecutionPolicyError,
                                          OutputLimitExceeded, PathEscapeError,
                                          classify_exit, backoff_delay,
                                          RETRYABLE, TERMINAL)

ENV = JobResourceEnvelope(cpu_limit=1, memory_bytes=512 * 1024 * 1024,
                          disk_bytes=64 * 1024 * 1024, timeout_s=30,
                          max_output_bytes=4 * 1024 * 1024)


def _run(tmp_path, argv, env=ENV, policy=None, **kw):
    r = BoundedRunner(workspace_base=tmp_path, policy=policy or SandboxPolicy())
    return r, r.run(argv, envelope=env, **kw)


class TestBoundedRunner:
    def test_allowed_executable_ok(self, tmp_path):
        code = "print('hello oce')"
        _, r = _run(tmp_path, ["python", "-c", code])
        assert r.exit_code == 0 and "hello oce" in r.stdout

    def test_forbidden_executable_fails_closed(self, tmp_path):
        policy = SandboxPolicy(allowed_executables=("python",))
        with pytest.raises(ExecutionPolicyError):
            _run(tmp_path, ["bash", "-c", "echo hi"], policy=policy)

    def test_forbidden_env_var_rejected(self, tmp_path):
        runner = BoundedRunner(workspace_base=tmp_path)
        with pytest.raises(ExecutionPolicyError):
            runner.run(["python", "-c", "print(1)"], envelope=ENV,
                       env_override={"AWS_SECRET_ACCESS_KEY": "leak"})

    def test_timeout_enforced(self, tmp_path):
        env = JobResourceEnvelope(timeout_s=1)
        _, r = _run(tmp_path, ["python", "-c", "import time; time.sleep(60)"], env=env)
        assert r.timed_out is True
        assert r.resource_violation == "timeout"  # blank
        assert r.ok is False

    def test_output_size_limit(self, tmp_path):
        env = JobResourceEnvelope(timeout_s=30, max_output_bytes=1024)
        _, r = _run(tmp_path, ["python", "-c", "print('y'*200000)"], env=env)
        assert r.resource_violation == "output_size_limit"

    def test_path_escape_blocked(self, tmp_path):
        runner = BoundedRunner(workspace_base=tmp_path)
        outside = tmp_path.parent / "outside.txt"
        with pytest.raises(PathEscapeError):
            runner.run(["python", "-c", "pass"], envelope=ENV,
                       input_paths=[outside])

    def test_fresh_workspace_per_attempt(self, tmp_path):
        runner = BoundedRunner(workspace_base=tmp_path)
        a1 = runner.run(["python", "-c", "pass"], envelope=ENV)
        a2 = runner.run(["python", "-c", "pass"], envelope=ENV)
        assert a1.workspace != a2.workspace
        assert (tmp_path / "attempt-1").exists()
        assert (tmp_path / "attempt-2").exists()

    def test_cleanup_removes_workspaces(self, tmp_path):
        runner, a = _run(tmp_path, ["python", "-c", "pass"])
        runner.cleanup()
        assert not any(tmp_path.iterdir())


class TestArtifactStore:
    def test_cas_idempotency(self, tmp_path):
        st = ArtifactStore(tmp_path)
        d1 = st.publish_blob(b"hello")
        d2 = st.publish_blob(b"hello")
        assert d1 == d2
        assert (tmp_path / "cas" / d1).exists()

    def test_size_enforcement(self, tmp_path):
        st = ArtifactStore(tmp_path, max_artifact_bytes=16)
        with pytest.raises(OutputLimitExceeded):
            st.publish_blob(b"x" * 100)

    def test_partial_upload_tmp_cleaned(self, tmp_path):
        st = ArtifactStore(tmp_path)
        st.publish_blob(b"data")
        assert list((tmp_path / "tmp").iterdir()) == []

    def test_manifest_verify_and_read(self, tmp_path):
        st = ArtifactStore(tmp_path)
        out = tmp_path / "out1.txt"
        out.write_text("artifact body", encoding="utf-8")
        m = st.create_manifest(job_id="j1", attempt=1, producer_identity="po",
                               worker_id="wkr-1", artifact_paths={"out1.txt": out})
        assert st.verify_reference(m["manifest_id"])
        assert st.read_artifact("out1.txt", m["manifest_id"]) == b"artifact body"
        assert st.read_artifact("nope", m["manifest_id"]) is None

    def test_tampered_artifact_detected(self, tmp_path):
        st = ArtifactStore(tmp_path)
        out = tmp_path / "out2.txt"
        out.write_text("secret-body", encoding="utf-8")
        m = st.create_manifest(job_id="j2", attempt=1,
                               producer_identity="po", worker_id="w",
                               artifact_paths={"out2.txt": out})
        # corrupt a blob on disk
        blob_file = tmp_path / "cas" / m["artifacts"][0]["sha256"]
        blob_file.write_bytes(b"tampered")
        assert st.verify_reference(m["manifest_id"]) is False
        with pytest.raises(RuntimeError):
            st.read_artifact("out2.txt", m["manifest_id"])

    def test_duplicate_result_single_provenance(self, tmp_path):
        st = ArtifactStore(tmp_path)
        out = tmp_path / "r.json"
        out.write_text("{}", encoding="utf-8")
        m1 = st.create_manifest(job_id="j3", attempt=1, producer_identity="po",
                                worker_id="w", artifact_paths={"r.json": out})
        m2 = st.create_manifest(job_id="j3", attempt=1, producer_identity="po",
                                worker_id="w", artifact_paths={"r.json": out})
        # identical content → same content-addressed manifest ref
        assert m1["manifest_id"] == m2["manifest_id"]


class TestRetryCoordinator:
    def test_classification(self):
        assert classify_exit(0, False, None) == "ok"
        assert classify_exit(1, True, None) == TERMINAL  # timeout
        assert classify_exit(1, False, "memory") == TERMINAL

    def test_backoff_deterministic(self):
        assert backoff_delay(1) == 1.0
        assert backoff_delay(2) == 2.0
        assert backoff_delay(3) == 4.0

    def test_terminal_no_retry_and_dead_letter(self):
        rc = RetryCoordinator(policy=RetryPolicy(max_retries=3))
        def run_once(a):
            return AttemptResult(exit_code=137, stdout="", stderr="",
                                 raise_fired=False, timed_out=False,
                                 cancel_requested=False)
        out = rc.run_with_retry("job-x", "wkr", run_once)
        assert out["dead_lettered"] is True
        assert out["attempts"] == 1  # terminal → no retry
        assert rc.is_poison("job-x")

    def test_retry_exhaustion(self):
        rc = RetryCoordinator(policy=RetryPolicy(max_retries=3))
        attempts = []
        def run_once(a):
            attempts.append(a)
            return AttemptResult(exit_code=None, stdout="", stderr="boom",
                                 raise_fired=True, timed_out=False,
                                 cancel_requested=False)
        out = rc.run_with_retry("job-y", "wkr", run_once)
        assert out["dead_lettered"] is True
        assert len(attempts) == 3  # all retries consumed
        assert rc.dead_letter("job-y")["reason"] == "retry_exhausted"

    def test_success_has_one_material_effect(self):
        rc = RetryCoordinator(policy=RetryPolicy(max_retries=3))
        calls = []
        def run_once(a):
            return AttemptResult(exit_code=0, stdout="ok", stderr="",
                                 raise_fired=False, timed_out=False,
                                 cancel_requested=False)
        out = rc.run_with_retry("job-z", "wkr", run_once, effect_committer=calls.append)
        assert out["result"] == "success"
        assert out["material_effect"] is True
        assert len(calls) == 1  # exactly one material effect

    def test_operator_authorized_retry(self):
        rc = RetryCoordinator(policy=RetryPolicy(max_retries=1))
        rc.run_with_retry("job-r", "wkr",
                          lambda a: AttemptResult(exit_code=None, stdout="", stderr="x",
                                                  raise_fired=True, timed_out=False,
                                                  cancel_requested=False))
        assert rc.is_poison("job-r")
        assert rc.operator_authorized_retry("job-r") is True
        assert rc.is_poison("job-r") is False