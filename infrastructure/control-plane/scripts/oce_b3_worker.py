#!/usr/bin/env python3
"""OCE Book 3 — outbound worker process (B3-R3).

Runs in a SEPARATE operating-system process: dials OUT to the loopback
control-plane service (never listens), authenticates over the shared secret,
heartbeats, runs a governed job inside a bounded/disposable workspace,
publishes immutable artifacts, and delivers the result with a fencing-proof
effect key (one material effect per logical job).

Env:
    OCE_CP_URL       compatibility ASSERTION only (must equal the canonical
                     loopback endpoint derived from the validated effective
                     config; external/noncanonical targets fail closed)
    OCE_WORKER_ID    admitted worker id
    OCE_WORKER_SECRET shared secret (never the identity-row verifier)
    OCE_JOB_FILE     JSON file describing the job {job_type, params, ...}

Exits 0 on success, 2 on protocol denial, nonzero on execution failure.
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))

from oce_control.worker_client import OutboundWorkerClient  # noqa: E402
from oce_control.execution_runtime import (  # noqa: E402
    BoundedRunner, SandboxPolicy, JobResourceEnvelope, ArtifactStore)
from oce_control.representative_jobs import program_for, prepare_workspace  # noqa: E402


def _pick_eligible(client) -> str:
    """Discover a governed job for this worker through the control plane."""
    jobs = client.eligible_jobs()
    if not jobs:
        raise SystemExit(3)  # no eligible work this round
    return jobs[0]


def _test_mode() -> bool:
    """Authenticated CI/test seam (B4-CXR5R6).

    Only the CI runner / explicit test harness sets ``OCE_CI_MODE=true``;
    production launches never carry it. TEST_ONLY inputs (OCE_JOB_FILE, the
    ambient OCE_WORKER_SECRET fallback) are reachable ONLY under this seam.
    """
    return os.environ.get("OCE_CI_MODE", "").lower() == "true"


def _worker_shared_secret() -> str:
    """Worker credential from the APPROVED secret authority (B4-CXR5R6).

    The governed local secret store (``.runtime/secrets.json`` worker_token,
    materialized once by the explicit initialization phase) is the ONLY
    authority in production. The ambient ``OCE_WORKER_SECRET`` is a TEST
    seam only — reachable exclusively under ``OCE_CI_MODE=true`` — so an
    ambient value can never self-authorize a production worker.
    """
    from oce_control.local_secrets import read_worker_token
    try:
        return read_worker_token()
    except RuntimeError:
        pass
    if _test_mode() and os.environ.get("OCE_WORKER_SECRET"):
        return os.environ["OCE_WORKER_SECRET"]
    raise SystemExit(
        "FAIL: outbound worker shared secret unavailable — approved secret "
        "store has no worker token and no authenticated test seam is present "
        "(B4-CXR5R6)")


def _contained_path(name: str, value: str, default: str) -> Path:
    """Resolve a worker path input with containment enforcement (B4-CXR5R6).

    Workspace / attempt / artifact paths are authority-bearing (they select
    where execution and durable artifacts land). Accepted ONLY when the
    resolved path stays beneath the process working root and NEVER points
    into the governed control-plane package (repository overwrite) or its
    secret store (``.runtime``). Rejects traversal (``..``), absolute
    external targets and symlink escapes (``resolve()`` then containment).
    """
    if not value:
        return Path(default)
    p = Path(value)
    if ".." in p.parts:
        raise SystemExit(
            f"FAIL: {name} contains traversal segments — refused (B4-CXR5R6)")
    try:
        resolved = p.resolve()
    except OSError as exc:
        raise SystemExit(
            f"FAIL: {name} cannot be resolved safely: {exc} (B4-CXR5R6)") from exc
    root = Path.cwd().resolve()
    if resolved != root and root not in resolved.parents:
        raise SystemExit(
            f"FAIL: {name} escapes the working root {root} — refused "
            f"(B4-CXR5R6): {resolved}")
    base = BASE.resolve()
    if resolved == base or base in resolved.parents:
        raise SystemExit(
            f"FAIL: {name} overlaps the governed control-plane package or its "
            f"secret store — refused (B4-CXR5R6): {resolved}")
    return p


def main() -> int:
    # B4-CXR3R3: the Book 4 activation gate runs FIRST (regardless of whether
    # OCE_CP_URL is set). The worker target is the canonical loopback endpoint
    # derived from the validated effective config; OCE_CP_URL, when present,
    # is accepted ONLY as an exact compatibility assertion of that endpoint.
    # An external/divergent URL or a forbidden config blocks before any
    # socket activity — no worker session can start under a bypass.
    #
    # B4-CXR4R3: the worker freezes ONE immutable ActivationContext and the
    # target comes from the PINNED config — a later environment mutation
    # cannot move the worker to a different control plane.
    from oce_control.config_startup import create_activation_context, outbound_cp_url
    ctx = create_activation_context()
    url = outbound_cp_url(ctx=ctx)
    worker_id = os.environ.get("OCE_WORKER_ID", "worker-local01")
    # OCE_JOB_FILE is TEST_ONLY (B4-CXR5R6): a local file must never replace
    # the authoritative job detail fetched from the control plane in
    # production. Rejected BEFORE any job/workspace/process activity unless
    # the authenticated CI/test seam is present.
    job_file = os.environ.get("OCE_JOB_FILE", "")
    if job_file and not _test_mode():
        raise SystemExit(
            "FAIL: OCE_JOB_FILE is TEST_ONLY — production workers must fetch "
            "authoritative job detail from the control plane (B4-CXR5R6)")
    spec = None
    if job_file:
        spec = json.loads(Path(job_file).read_text(encoding="utf-8"))
    secret = _worker_shared_secret()

    client = OutboundWorkerClient(url, worker_id, secret)
    try:
        client.connect()          # hello + respond (challenge/response)
        client.heartbeat()

        # B3-R7: discover and fetch a governed job through the control plane.
        job_id = spec["job_id"] if spec else _pick_eligible(client)
        if spec is None:
            detail = client.fetch_job(job_id)
            spec = {
                "job_id": detail["job_id"],
                "job_type": detail["job_type"],
                "required_capabilities": detail.get("required_capabilities", ["hash"]),
                "params": detail.get("payload", {}) or {},
                "timeout_s": detail.get("timeout", 60),
            }
        params = spec.get("params", {})
        job = {
            "job_id": spec["job_id"],
            "job_type": spec["job_type"],
            "required_capabilities": spec.get("required_capabilities", ["hash"]),
            "trust_zone": spec.get("trust_zone", "worker-local"),
            "resource_envelope": spec.get("resource_envelope",
                                          {"cpu_limit": 1, "memory_bytes":
                                           512 * 1024 * 1024,
                                           "disk_bytes": 256 * 1024 * 1024,
                                           "timeout_s": 60}),
        }
        lease = client.claim(job)
        lease_id = lease["lease_id"]
        fence = lease["fence"]

        # bounded, disposable execution in a fresh workspace

        fence_id = lease_id[:8]
        # B4-CXR5R6: workspace/attempt paths are authority-bearing — contained
        # beneath the working root, never into the governed package/secret store.
        ws_base = _contained_path("OCE_WS_BASE", os.environ.get("OCE_WS_BASE", ""),
                                  str(Path.cwd() / "b3-workspace"))
        runner = BoundedRunner(workspace_base=ws_base,
                               policy=SandboxPolicy(strict=True))
        ws = _contained_path("OCE_ATTEMPT_WS", os.environ.get("OCE_ATTEMPT_WS", ""),
                             str(Path.cwd() / f"attempt-{fence_id}"))
        prepare_workspace(ws, spec["job_type"], params)
        prog = program_for(spec["job_type"])
        env = JobResourceEnvelope(timeout_s=int(spec.get("timeout_s", 60)))
        result = runner.run(["python", "-c", prog], envelope=env, workspace=ws)

        if not result.ok:
            client.surrender(job["job_id"], lease_id, fence)
            print(json.dumps({"worker_id": worker_id, "job_id": spec["job_id"],
                              "ok": False, "stderr": result.stderr[-2000:]}))
            return 1

        # immutable publication (CAS) before any effect
        artifacts = {}
        for name in Path(ws / "output").iterdir():
            if name.is_file():
                artifacts[name.name] = name
        store_base = _contained_path("OCE_ARTIFACT_BASE",
                                     os.environ.get("OCE_ARTIFACT_BASE", ""),
                                     str(Path.cwd() / "b3-cas"))
        store = ArtifactStore(store_base)
        manifest = store.create_manifest(
            job_id=spec["job_id"], attempt=fence, producer_identity=worker_id,
            worker_id=worker_id, artifact_paths=artifacts)
        assert store.verify_reference(manifest["manifest_id"]), "artifact verify failed"

        effect_key = f"{job['job_id']}::{lease_id}::effect"
        out = client.deliver_result(
            job_id=job["job_id"], lease_id=lease_id, fence=fence,
            effect_key=effect_key, manifest=manifest)
        print(json.dumps({"worker_id": worker_id, "job_id": spec["job_id"],
                          "ok": True, "delivered": out.get("delivered"),
                          "manifest_id": manifest["manifest_id"]}))
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())