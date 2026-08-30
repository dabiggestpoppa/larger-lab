"""Book 3 — representative governed local worker execution proof (B3-C8).

Each representative job traverses the COMPLETE production path: it runs as
an allowlisted program inside a BoundedRunner workspace (bounded resource
envelope, disposable workspace, policy enforcement), writes artifacts, and
those artifacts are published immutably through the content-addressed
ArtifactStore and re-verified. No direct function substitution.
"""
from __future__ import annotations
import json
from pathlib import Path
import pytest

from oce_control.execution_runtime import BoundedRunner, SandboxPolicy, JobResourceEnvelope


SAFE_JOBS = [
    ("b3.deterministic-hash", {"value": "oce-b3"},
     "output/hash.json", ["sha256"]),
    ("b3.bounded-compute", {"n": 5000},
     "output/compute.json", ["sum_sqrt"]),
    ("b3.repo-inventory", {},
     "output/inventory.json", ["lines"]),
    ("b3.synthetic-backtest", {"seed": 7, "n": 120},
     "output/backtest.json", ["cumulative"]),
    ("b3.analysis-artifact", {"title": "OCE B3 Report", "rows": 3},
     "output/report.html", ["<html>"]),
]


@pytest.mark.parametrize("job_type,params,out_rel,needles", SAFE_JOBS)
def test_representative_safe_job_full_path(tmp_path, job_type, params, out_rel, needles):
    from oce_control.representative_jobs import program_for, prepare_workspace
    from oce_control.execution_runtime import BoundedRunner, JobResourceEnvelope

    env = JobResourceEnvelope(timeout_s=30)
    runner = BoundedRunner(workspace_base=tmp_path, policy=SandboxPolicy())
    prepare_workspace(tmp_path / "attempt-1", job_type, params)
    result = runner.run(["python", "-c", program_for(job_type)],
                        envelope=env, workspace=tmp_path / "attempt-1")
    assert result.ok, result.stderr
    out_file = tmp_path / "attempt-1" / out_rel
    assert out_file.exists()
    text = out_file.read_text(encoding="utf-8")
    for n in needles:
        assert n in text

    # immutable publication through the content-addressed store + verify
    from oce_control.execution_runtime import ArtifactStore
    store = ArtifactStore(tmp_path / "artifact-store")
    manifest = store.create_manifest(
        job_id=f"rep-{job_type}", attempt=1, producer_identity="operator:po",
        worker_id="local-worker", artifact_paths={out_rel: out_file})
    assert store.verify_reference(manifest["manifest_id"])
    assert store.read_artifact(out_rel, manifest["manifest_id"]) == out_file.read_bytes()


def test_cancellation_during_execution(tmp_path):
    """Long-running job is bounded — the runtime timeout cancels the tree."""
    from oce_control.representative_jobs import program_for, prepare_workspace
    env = JobResourceEnvelope(timeout_s=1)
    runner = BoundedRunner(workspace_base=tmp_path, policy=SandboxPolicy())
    prepare_workspace(tmp_path / "attempt-1", "b3.deterministic-hash", {"value": "x"})
    runner._attempts.clear()
    # run the cancel-during-exec programme, which sleeps indefinitely
    result = runner.run(["python", "-c", program_for("b3.cancel-during-exec")],
                        envelope=env, workspace=tmp_path / "attempt-1")
    assert result.timed_out is True or result.cancel_requested is True
    assert result.ok is False


def _job_spec():
    return [t for t, *_ in SAFE_JOBS]