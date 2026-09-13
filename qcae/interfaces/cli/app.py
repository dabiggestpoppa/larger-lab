"""Runtime composition factory + application service (P2-C11; Book V 13.7).

``build_local_runtime`` wires one local process: metadata DB, runtime store,
queue, policy engine, authority provider, approvals, identity, engine, and
service. ``QcaeApp`` is the stable application boundary future HTTP/OCE
adapters call — interfaces stay thin; domain logic lives in the services.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Optional, Union

from qcae.governance.standalone.approvals import ApprovalRequest
from qcae.governance.standalone.authority import LocalAuthorityProvider
from qcae.governance.standalone.identity import LocalIdentityProvider
from qcae.governance.standalone.policy import LocalPolicyEngine, PolicySet
from qcae.governance.standalone.runtime_service import LocalRuntimeService
from qcae.infrastructure.persistence.sqlite_approval_registry import (
    APPROVAL_DDL,
    SqliteApprovalRegistry,
)
from qcae.infrastructure.persistence.sqlite_budget_ledger import BUDGET_DDL
from qcae.infrastructure.persistence.sqlite_policy_log import (
    GOVERNANCE_DDL,
    SqlitePolicyDecisionLog,
)
from qcae.infrastructure.persistence.sqlite_runtime_store import (
    RUNTIME_DDL,
    SqliteRuntimeStore,
)
from qcae.infrastructure.persistence.store_factory import open_metadata_db
from qcae.infrastructure.queue.sqlite_step_queue import (
    QUEUE_INTEGRITY_DDL,
    SqliteStepQueue,
)
from qcae.orchestration.orchestrator.engine import OrchestratorEngine
from qcae.orchestration.workers.base import Worker

__all__ = ["LocalRuntime", "build_local_runtime", "QcaeApp"]


@dataclass
class LocalRuntime:
    """All wired components of one local runtime instance."""

    # Metadata DB connection (engine type owned by the infrastructure factory).
    conn: object
    store: SqliteRuntimeStore
    queue: SqliteStepQueue
    engine: OrchestratorEngine
    service: LocalRuntimeService
    authority: LocalAuthorityProvider
    approvals: SqliteApprovalRegistry
    identity: LocalIdentityProvider
    policy: LocalPolicyEngine


def _default_clock() -> Callable[[], str]:
    from datetime import datetime, timezone

    return lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _default_policy_set() -> PolicySet:
    """Minimal standalone policy: workers may discover/persist, sandbox
    execution requires approval, everything else fails closed."""
    from qcae.governance.standalone.policy import PolicyEffect, PolicyRule

    return PolicySet(
        policy_id="pol-standalone-default",
        policy_version="1.0.0",
        rules=(
            PolicyRule(
                rule_id="allow-discover",
                effect=PolicyEffect.ALLOW,
                action="may_discover",
                principal_match="id-worker-*",
                reason="standalone discovery permitted",
            ),
            PolicyRule(
                rule_id="allow-persist-metadata",
                effect=PolicyEffect.ALLOW_WITH_CONSTRAINTS,
                action="may_persist_registry_record",
                principal_match="id-worker-*",
                constraints=("scope:candidate-metadata-only",),
                reason="registry metadata persistence permitted",
            ),
            PolicyRule(
                rule_id="approval-sandbox",
                effect=PolicyEffect.REQUIRE_APPROVAL,
                action="may_execute_in_sandbox",
                principal_match="id-worker-*",
                reason="sandbox execution requires operator approval",
            ),
            PolicyRule(
                rule_id="deny-credentials",
                effect=PolicyEffect.DENY,
                action="may_access_production_credentials",
                reason="outside standalone authority",
            ),
        ),
    )


def build_local_runtime(
    db_path: Union[str, Path],
    *,
    workers: Optional[Dict[str, Worker]] = None,
    policy_set: Optional[PolicySet] = None,
    clock: Optional[Callable[[], str]] = None,
    lease_ttl_seconds: int = 300,
) -> LocalRuntime:
    clock = clock or _default_clock()
    conn = open_metadata_db(db_path)
    for ddl in (RUNTIME_DDL, QUEUE_INTEGRITY_DDL, BUDGET_DDL, GOVERNANCE_DDL, APPROVAL_DDL):
        conn.executescript(ddl)

    store = SqliteRuntimeStore(conn)
    queue = SqliteStepQueue(conn, store, now_fn=clock, lease_ttl_seconds=lease_ttl_seconds)
    engine = OrchestratorEngine(store, queue, clock=clock, workers=dict(workers or {}))
    identity = LocalIdentityProvider()
    policy = LocalPolicyEngine(policy_set or _default_policy_set())
    policy_log = SqlitePolicyDecisionLog(conn)
    authority = LocalAuthorityProvider(policy, policy_log, clock=clock)
    approvals = SqliteApprovalRegistry(conn)

    # Identity snapshot for schema/policy versions comes from the policy set.
    service = LocalRuntimeService(
        runtime_store=store,
        queue=queue,
        engine=engine,
        identity_provider=identity,
        policy_provider=authority,
        approval_registry=approvals,
        clock=clock,
        schema_version=4,
        policy_version=policy.policy.policy_version,
        storage_location=str(db_path),
    )
    return LocalRuntime(
        conn=conn, store=store, queue=queue, engine=engine, service=service,
        authority=authority, approvals=approvals, identity=identity, policy=policy,
    )


class QcaeApp:
    """Stable application-service boundary (Book V 13.7 CLI/API)."""

    def __init__(self, runtime: LocalRuntime) -> None:
        self._rt = runtime

    # -- jobs ----------------------------------------------------------------

    def submit_job(self, job, steps, *, submitted_by=None, not_before=""):
        return self._rt.service.submit(job, steps, submitted_by=submitted_by, not_before=not_before)

    def job_status(self, job_id: str):
        return self._rt.service.inspect(job_id)

    def job_list(self, status=None):
        return self._rt.service.list_jobs(status=status)

    def job_run_step(self, job_id: str, worker_id: str):
        # Derive readiness first (engine-owned graph logic), then claim.
        self._rt.service.ready_steps(job_id)
        lease = self._rt.service.lease_next(job_id, worker_id)
        if lease is None:
            return None
        return self._rt.service.execute_step(lease)

    def job_resume(self, job_id: str):
        self._rt.service._engine.mark_running(job_id)
        return self._rt.service.resume(job_id)

    def job_cancel(self, job_id: str, *, reason: str = ""):
        return self._rt.service.cancel(job_id, reason=reason)

    def job_events(self, job_id: str):
        return self._rt.service.job_events(job_id)

    def recover(self, job_id: str | None = None):
        """Recover expired leases (all jobs) or resume one job."""
        if job_id is not None:
            return self._rt.service.resume(job_id)
        return self._rt.service.recover_expired_leases()

    # -- approvals -----------------------------------------------------------

    def approval_list(self):
        return self._rt.service.pending_approvals()

    def approval_record(self, decision):
        self._rt.service.record_approval(decision)

    def approval_decide(
        self, *, request_id: str, decision: str, decided_by: str,
        job_id: str = "", reason: str = "",
    ):
        return self._rt.service.decide_approval(
            request_id=request_id, decision=decision, decided_by=decided_by,
            job_id=job_id, reason=reason,
        )

    # -- governance ----------------------------------------------------------

    def authority_decision(self, request):
        return self._rt.authority.decide(request)

    def runtime_identity(self):
        return self._rt.service.identity()
