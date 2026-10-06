"""PRIVATE test-only dependency seam for the outbound worker (B4-CXR6R2).

This module lives in tests/ and is NEVER imported by production scripts or
src — the production CLI constructs only ProductionWorkerDependencies and no
environment string can select this object. Tests that need to inject a job
specification or a fixed credential construct TestWorkerDependencies
directly and call scripts.oce_b3_worker.run(deps, ...) in-process.
"""
from __future__ import annotations


class TestWorkerDependencies:
    """Explicit test dependency: fixed shared secret + injected job spec.

    Only test code constructs this. It is never reachable from the
    production CLI or from environment construction.
    """

    def __init__(self, *, secret: str, job_spec: dict | None = None,
                 eligible_job_ids: list[str] | None = None):
        self._secret = secret
        self._job_spec = job_spec
        self._eligible = eligible_job_ids or []

    def shared_secret(self) -> str:
        return self._secret

    def resolve_job(self, client) -> dict:
        """Return the injected job spec; when absent, pick the first eligible
        job through the control plane (like production)."""
        if self._job_spec is not None:
            return dict(self._job_spec)
        from scripts.oce_b3_worker import _pick_eligible
        job_id = self._eligible[0] if self._eligible else _pick_eligible(client)
        detail = client.fetch_job(job_id)
        return {
            "job_id": detail["job_id"],
            "job_type": detail["job_type"],
            "required_capabilities": detail.get("required_capabilities", ["hash"]),
            "params": detail.get("payload", {}) or {},
            "timeout_s": detail.get("timeout", 60),
        }
