"""P2-R5R-R1-C04 — REQUIRE_APPROVAL constraint preservation guard.

The durable ApprovalRequest schema cannot preserve per-request
constraints, so a REQUIRE_APPROVAL verdict carrying non-empty constraints
MUST fail closed in ``record_authority_request`` rather than be silently
narrowed into an unconstrained request. The policy gate currently emits
REQUIRE_APPROVAL with constraints == (); these tests pin that invariant.
"""

from __future__ import annotations

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.governance.standalone.approvals import ApprovalRequest
from qcae.governance.standalone.step_gate import ApprovalRegistrySink
from qcae.infrastructure.persistence.sqlite_approval_registry import (
    SqliteApprovalRegistry,
)
from qcae.infrastructure.persistence.store_factory import open_metadata_db
from qcae.orchestration.authority_gate import (
    StepAuthorityDecision,
    StepAuthorityVerdict,
)


def _verdict(*, constraints=()) -> StepAuthorityVerdict:
    return StepAuthorityVerdict(
        step_id="step-1",
        job_id="job-1",
        principal="worker-1",
        action="execute.GENERIC",
        resource="subject-1",
        scope="job:job-1",
        decision=StepAuthorityDecision.REQUIRE_APPROVAL,
        decision_ref="dec-1",
        policy_version="static-1",
        requirement="may_execute_in_sandbox",
        budget_ref="job:job-1",
        evaluated_at="2026-01-01T00:00:00Z",
        reason="step requires approval",
        constraints=tuple(constraints),
    )


def _sink(conn) -> ApprovalRegistrySink:
    return ApprovalRegistrySink(
        SqliteApprovalRegistry(conn), clock=lambda: "2026-01-01T00:00:00Z"
    )


class TestConstraintPreservation:
    def test_constrained_require_approval_refuses_to_record(
        self, tmp_path
    ) -> None:
        conn = open_metadata_db(tmp_path / "c.sqlite3")
        try:
            with pytest.raises(QcaeValidationError, match="cannot preserve"):
                _sink(conn).record_authority_request(
                    _verdict(constraints=("max_budget_100",))
                )
            # Nothing durable was recorded for the refused verdict.
            assert conn.execute(
                "SELECT COUNT(*) FROM governance_approval_request"
            ).fetchone()[0] == 0
        finally:
            conn.close()

    def test_unconstrained_require_approval_still_records(
        self, tmp_path
    ) -> None:
        conn = open_metadata_db(tmp_path / "u.sqlite3")
        try:
            request_id = _sink(conn).record_authority_request(_verdict())
            row = conn.execute(
                "SELECT request_id FROM governance_approval_request"
            ).fetchone()
            assert row[0] == request_id
            stored = SqliteApprovalRegistry(conn).get_request(request_id)
            assert isinstance(stored, ApprovalRequest)
            assert stored.principal == "worker-1"
        finally:
            conn.close()
