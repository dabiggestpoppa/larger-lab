#!/usr/bin/env python3
"""OCE Book 3 — outbound worker process (B3-R3).

Runs in a SEPARATE operating-system process: dials OUT to the loopback
control-plane service (never listens), authenticates over the shared secret,
heartbeats, runs a governed job inside a bounded/disposable workspace,
publishes immutable artifacts, and delivers the result with a fencing-proof
effect key (one material effect per logical job).

Env:
    OCE_CP_URL       control-plane base URL (default http://127.0.0.1:8080)
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


def main() -> int:
    url = os.environ.get("OCE_CP_URL", "http://127.0.0.1:8080")
    worker_id = os.environ.get("OCE_WORKER_ID", "worker-local01")
    secret = os.environ["OCE_WORKER_SECRET"]
    job_file = os.environ["OCE_JOB_FILE"]
    spec = json.loads(Path(job_file).read_text(encoding="utf-8"))

    client = OutboundWorkerClient(url, worker_id, secret)
    try:
        client.connect()          # hello + respond (challenge/response)
        client.heartbeat()

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
        params = spec.get("params", {})
        fence_id = lease_id[:8]
        runner = BoundedRunner(workspace_base=Path(os.environ.get(
            "OCE_WS_BASE", str(Path.cwd() / "b3-workspace"))),
            policy=SandboxPolicy(strict=True))   # B3-R5: fail closed on missing isolation
        ws = Path(os.environ.get("OCE_ATTEMPT_WS",
                                 str(Path.cwd() / f"attempt-{fence_id}")))
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
        store_base = Path(os.environ.get("OCE_ARTIFACT_BASE",
                                         str(Path.cwd() / "b3-cas")))
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