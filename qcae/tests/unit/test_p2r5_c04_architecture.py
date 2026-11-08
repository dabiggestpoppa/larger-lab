"""P2-R5-C04 — resolver dedup + architecture guard.

- One ``ApprovalRequestResolver.latest_for_step`` is used by both execution-time
  admission (engine) and grant-release verification (runtime service); no
  duplicated request lookup.
- The orchestrator does not import ``qcae.governance.standalone.*``; it
  depends on the provider-neutral ``ApprovalAdmissionProvider`` port.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

import pytest

from qcae.orchestration.authority_gate import (
    ApprovalAdmissionProvider,
    ApprovalRequestResolver,
)
from qcae.infrastructure.persistence.sqlite_approval_registry import (
    SqliteApprovalRegistry,
)
from qcae.orchestration.jobs.runtime import JobEventType


class TestNoGovernanceStandaloneImportInOrchestrator:
    """Architecture guard: engine must not import governance standalone."""

    def test_engine_source_has_no_governance_standalone_import(self) -> None:
        engine_path = (
            Path(__file__).resolve().parents[2]
            / "orchestration"
            / "orchestrator"
            / "engine.py"
        )
        tree = ast.parse(engine_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert not module.startswith("qcae.governance.standalone"), (
                    f"engine.py imports '{module}' from governance standalone"
                )


class TestResolverSingleSourceOfTruth:
    def test_latest_for_step_reads_latest_approval_requested(self) -> None:
        # Resolver unpacks (seq, event, payload) tuples from events_for_job.
        events = [
            (1, _ev("APPROVAL_REQUESTED", "s-1"), '{"authority_request_id": "req-1"}'),
            (2, _ev("APPROVAL_REQUESTED", "s-1"), '{"authority_request_id": "req-2"}'),
            (3, _ev("STEP_SUCCEEDED", "s-1"), '{"reason": "done"}'),
        ]
        resolver = ApprovalRequestResolver(lambda job_id: events)
        assert resolver.latest_for_step("job-1", "s-1") == "req-2"

    def test_latest_for_step_none_when_no_request(self) -> None:
        resolver = ApprovalRequestResolver(lambda job_id: [])
        assert resolver.latest_for_step("job-1", "s-1") is None


class TestRegistryImplementsPort:
    def test_registry_exposes_port_methods(self) -> None:
        for name in ("get_request", "effective_grant", "consume_grant"):
            assert hasattr(SqliteApprovalRegistry, name), name


@dataclass
class _Ev:
    event_type: object
    event_id: str
    step_id: str


def _ev(event_type_name: str, step_id: str) -> _Ev:
    return _Ev(
        event_type=JobEventType[event_type_name],
        event_id="ev",
        step_id=step_id,
    )
