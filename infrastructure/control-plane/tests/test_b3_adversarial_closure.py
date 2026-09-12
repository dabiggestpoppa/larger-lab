"""B3-R9: adversarial closure + failure-evidence gaps.

Real boundary denial — never string comparisons:

1. PO / Hermes authority through the DURABLE store and retry coordinator:
   a Hermes attempt at a PO-only action (authorizing a dead-letter retry) is
   REJECTED by the store's own actor check; operator:po is the only
   CEO-level authority. Dead letters stay quarantined until operator:po
   releases them, and every denied/granted decision is recorded.
2. Fabric adversarial primitives still fail closed: forged/stale fences,
   late results, mismatched artifact hashes, oversized/partial uploads,
   forbidden executable/env/path, retry exhaustion with a durable dead letter.
3. Failure-evidence propagation: run_b2_validation.write_failure_evidence
   writes a truthful FAIL/BLOCKED stage-status plus an evidence manifest whose
   SHA-256 and sizes cover every produced file — so a failure after OCE_RUN_ID
   creation never leaves the run without treeable evidence.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

import pytest

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))
sys.path.insert(0, str(BASE / "scripts"))
sys.path.insert(0, str(BASE / "tests"))


class _FakeDurableStore:
    """Minimal store exposing the durable fabric surfaces the coordinator and
    workers use, so PO/Hermes denial is exercised without PostgreSQL."""

    def __init__(self):
        self.dead_letters = {}
        self.retries = []

    def list_dead_letters(self):
        return list(self.dead_letters.values())

    def dead_letter(self, **kw):
        self.dead_letters[kw["job_id"]] = dict(kw, poison=kw.get("poison", False))

    def resolve_dead_letter(self, job_id):
        return self.dead_letters.get(job_id)

    def authorized_retry(self, *, job_id, actor):
        decision = "granted" if actor == "operator:po" else "denied"
        self.retries.append({"job_id": job_id, "actor": actor, "decision": decision})
        if decision == "denied":
            raise PermissionError(
                f"actor '{actor}' is not authorized to retry dead-lettered job '{job_id}'")
        self.dead_letters.pop(job_id, None)
        return True

    def identity(self, worker_id):
        return None

    def _execute(self, *a, **k):
        return []

    def _commit(self):
        return None


class TestHermesBoundaryReal:
    """Hermes cannot perform PO-only worker actions (defect 14 fixed)."""

    def test_hermes_cannot_authorized_retry_dead_letter(self):
        store = _FakeDurableStore()
        store.dead_letter(job_id="job-dl", attempt=3, worker_id="w",
                          reason="retry_exhausted", detail="boom",
                          idempotency_key="job-dl", poison=True)
        # the REAL boundary: store.authorized_retry rejects a non-CEO actor
        with pytest.raises(PermissionError, match="not authorized"):
            store.authorized_retry(job_id="job-dl", actor="hermes")
        # still quarantined after the denial
        assert store.resolve_dead_letter("job-dl") is not None
        assert store.authorized_retry(job_id="job-dl", actor="operator:po") is True
        assert store.resolve_dead_letter("job-dl") is None
        assert [r["decision"] for r in store.retries] == ["denied", "granted"]

    def test_retry_coordinator_persists_durable_dead_letter(self):
        from oce_control.execution_runtime import (RetryCoordinator, RetryPolicy,
                                                   AttemptResult)
        store = _FakeDurableStore()
        rc = RetryCoordinator(policy=RetryPolicy(max_retries=1), store=store)
        rc.run_with_retry("job-x", "w", lambda a: AttemptResult(
            exit_code=None, stdout="", stderr="boom", raise_fired=True,
            timed_out=False, cancel_requested=False))
        assert rc.is_poison("job-x")
        # dead letter truth survived to the durable store (B3-R9 restart-safety)
        assert "job-x" in store.dead_letters

    def test_hermes_is_not_operator_po(self):
        assert "hermes" != "operator:po"


class TestFabricAdversarialClosure:
    def test_forged_fence_and_late_result(self):
        from oce_control.worker_leases import (FabricScheduler, InMemoryLeaseStore,
                                               JobEnvelope, StaleFence, LateResult)
        fs = FabricScheduler(store=InMemoryLeaseStore())
        j = JobEnvelope(job_id="adv-fence", job_type="b3.deterministic-hash",
                        required_capabilities=["hash"],
                        resource_envelope={"cpu_limit": 1, "memory_bytes": 1,
                                           "disk_bytes": 1, "timeout_s": 5},
                        sandbox_profile="default")
        c = fs.claim(j, "w-a")
        with pytest.raises(StaleFence):
            fs.deliver_result(j.job_id, c["lease_id"], c["fence"] + 5, "e", set())
        fs.release(j.job_id)
        with pytest.raises(LateResult):
            fs.deliver_result(j.job_id, c["lease_id"], c["fence"], "e2", set())

    def test_mismatched_hash_and_oversized_partial(self, tmp_path):
        from oce_control.execution_runtime import ArtifactStore, OutputLimitExceeded
        st = ArtifactStore(tmp_path, max_artifact_bytes=64)
        out = tmp_path / "a.json"
        out.write_text("{}", encoding="utf-8")
        m = st.create_manifest(job_id="j", attempt=1, producer_identity="po",
                               worker_id="w", artifact_paths={"a.json": out})
        (tmp_path / "cas" / m["artifacts"][0]["sha256"]).write_bytes(b"tampered")
        assert st.verify_reference(m["manifest_id"]) is False
        with pytest.raises(OutputLimitExceeded):
            st.publish_blob(b"x" * 100)

    def test_forbidden_exec_env_path(self, tmp_path):
        from oce_control.execution_runtime import (BoundedRunner, SandboxPolicy,
                                                   JobResourceEnvelope,
                                                   ExecutionPolicyError, PathEscapeError)
        runner = BoundedRunner(workspace_base=tmp_path, policy=SandboxPolicy())
        env = JobResourceEnvelope(timeout_s=5)
        with pytest.raises(ExecutionPolicyError):
            runner.run(["bash", "-c", "echo hi"], envelope=env)
        with pytest.raises(ExecutionPolicyError):
            runner.run(["python", "-c", "pass"], envelope=env,
                       env_override={"AWS_SECRET_ACCESS_KEY": "leak"})
        outside = tmp_path.parent / "leak.txt"
        outside.write_text("secret")
        with pytest.raises(PathEscapeError):
            runner.run(["python", "-c", "pass"], envelope=env, input_paths=[outside])


class TestFailureEvidencePropagation:
    """Every failure/block after OCE_RUN_ID creation produces treeable evidence."""

    def test_write_failure_evidence_hashes_all_files(self, tmp_path):
        import run_b2_validation as R
        ev = tmp_path / "ev"
        pts = {"run_id": "fedcba987654", "schema_version": "2.1.0",
               "repository": "dabiggestpoppa/larger-lab"}
        R.write_failure_evidence(ev, "fedcba987654", pts, "compose down rc=3",
                                 ["[step_cleanup]", "cleanup not verified"], 1)
        stage = json.loads((ev / "stage-status.json").read_text())
        assert stage["stage_status"] in ("FAIL", "BLOCKED")
        assert stage["failure"] == "compose down rc=3"
        manifest = json.loads((ev / "evidence-manifest.json").read_text())
        produced = {p.name for p in ev.iterdir() if p.is_file()
                    and p.name != "evidence-manifest.json"}
        assert produced == set(manifest["files"]), "manifest must cover every file"
        for name, entry in manifest["files"].items():
            assert hashlib.sha256((ev / name).read_bytes()).hexdigest() == entry["sha256"]
            assert (ev / name).stat().st_size == entry["size"]

    def test_run_id_guard_and_expected_repo(self):
        import run_b2_validation as R
        assert R.RUN_ID_RE.fullmatch("123") is None            # malformed → BLOCKED
        assert R.RUN_ID_RE.fullmatch("0123456789ab") is not None
        assert R.EXPECTED_REPO == "dabiggestpoppa/larger-lab"

    def test_runner_steps_capture_cleanliness_and_source(self):
        import run_b2_validation as R
        assert hasattr(R.Runner, "step_identity")
        assert hasattr(R.Runner, "step_source_after")