#!/usr/bin/env python3
"""OCE Book 3 — outbound worker process (B3-R3).

Runs in a SEPARATE operating-system process: dials OUT to the loopback
control-plane service (never listens), authenticates over the shared secret,
heartbeats, runs a governed job inside a bounded/disposable workspace,
publishes immutable artifacts, and delivers the result with a fencing-proof
effect key (one material effect per logical job).

Env (production):
    OCE_CP_URL       compatibility ASSERTION only (must equal the canonical
                     loopback endpoint derived from the validated effective
                     config; external/noncanonical targets fail closed)
    OCE_WORKER_ID    admitted worker id

B4-CXR6R2: OCE_CI_MODE carries ZERO authority — it is evidence labeling
only. The production entrypoint REJECTS OCE_JOB_FILE and OCE_WORKER_SECRET
regardless of any environment value. Test injection (a local job spec or a
fixed credential) happens ONLY through the private dependency seam
(TestWorkerDependencies), constructed directly by test code — never
selected by an environment string and unreachable from the production CLI
or environment construction.

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


class WorkerDependencies:
    """Production worker dependency contract (B4-CXR6R2).

    The production CLI constructs ONLY ProductionWorkerDependencies. Test
    code supplies TestWorkerDependencies directly — the dependency is an
    explicit object, never an environment-selected switch.
    """

    def shared_secret(self) -> str:
        raise NotImplementedError

    def resolve_job(self, client) -> dict:
        """Return the authoritative job spec dict for this round."""
        raise NotImplementedError


class ProductionWorkerDependencies(WorkerDependencies):
    """Production authority (B4-CXR6R2): worker credential from the APPROVED
    secret store, job detail fetched from the control plane."""

    def shared_secret(self) -> str:
        from oce_control import local_secrets as ls
        try:
            return ls.read_worker_token()
        except RuntimeError as exc:
            raise SystemExit(
                "FAIL: outbound worker shared secret unavailable — the "
                "approved secret store has no worker token (run `oce_local "
                "configure`); ambient worker-secret values are NEVER consumed "
                "(B4-CXR6R2)") from exc

    def resolve_job(self, client) -> dict:
        """Authoritative job detail comes ONLY from the control plane — a
        local file can never replace job type/params/resource envelope/
        trust zone/required capabilities (B4-CXR5R6/CXR6R2)."""
        job_id = _pick_eligible(client)
        detail = client.fetch_job(job_id)
        return {
            "job_id": detail["job_id"],
            "job_type": detail["job_type"],
            "required_capabilities": detail.get("required_capabilities", ["hash"]),
            "params": detail.get("payload", {}) or {},
            "timeout_s": detail.get("timeout", 60),
        }


def _pick_eligible(client) -> str:
    """Discover a governed job for this worker through the control plane."""
    jobs = client.eligible_jobs()
    if not jobs:
        raise SystemExit(3)  # no eligible work this round
    return jobs[0]


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


def run(deps: WorkerDependencies, *, ctx, url: str,
        worker_id: str, environ: dict | None = None) -> int:
    """Execute one outbound worker round under an explicit dependency
    object (B4-CXR6R2). The production CLI calls this with
    ProductionWorkerDependencies; tests call it with
    TestWorkerDependencies. No environment string can select the
    dependency."""
    secret = deps.shared_secret()

    client = OutboundWorkerClient(url, worker_id, secret)
    try:
        client.connect()          # hello + respond (challenge/response)
        client.heartbeat()

        # B3-R7: the AUTHORITATIVE job spec comes from the dependency
        # (production: fetched through the control plane; tests: an explicit
        # injected object).
        spec = deps.resolve_job(client)
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


def main(argv: list[str] | None = None) -> int:
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
    #
    # B4-CXR6R1: this process declares the OUTBOUND_WORKER role; a
    # lifecycle-launched worker must present an authenticated capability
    # role-bound to 'outbound_worker'.
    from oce_control.config_startup import create_activation_context, outbound_cp_url
    ctx = create_activation_context(role="outbound_worker")
    url = outbound_cp_url(ctx=ctx)
    worker_id = os.environ.get("OCE_WORKER_ID", "worker-local01")

    # B4-CXR6R2: OCE_JOB_FILE and OCE_WORKER_SECRET are REJECTED in the
    # production entrypoint REGARDLESS of OCE_CI_MODE or any other ambient
    # value — an environment string can never unlock test authority. These
    # checks run before any job/workspace/process/socket activity.
    if os.environ.get("OCE_JOB_FILE"):
        raise SystemExit(
            "FAIL: OCE_JOB_FILE is TEST_ONLY and unreachable in the "
            "production worker — authoritative job detail must be fetched "
            "from the control plane; test injection is available only "
            "through the private dependency seam (B4-CXR6R2)")
    if os.environ.get("OCE_WORKER_SECRET"):
        raise SystemExit(
            "FAIL: ambient OCE_WORKER_SECRET is never consumed — the "
            "approved secret store is the only worker-credential authority; "
            "test injection is available only through the private dependency "
            "seam (B4-CXR6R2)")
    return run(ProductionWorkerDependencies(), ctx=ctx, url=url,
               worker_id=worker_id)


if __name__ == "__main__":
    sys.exit(main())