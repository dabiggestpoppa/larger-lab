"""P2 job graph qualification (directive §7)."""

from __future__ import annotations

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.orchestration.jobs.graph import StepGraph, runnable_steps
from qcae.orchestration.jobs.runtime import RuntimeStep, RuntimeStepStatus

JOB = "job-12345678"


def _step(sid, deps=(), status=RuntimeStepStatus.PENDING, **over):
    base = dict(
        step_id=sid,
        job_id=JOB,
        step_type="GENERIC",
        dependencies=tuple(deps),
        status=status,
        created_at="2026-09-13T00:00:00Z",
    )
    base.update(over)
    return RuntimeStep(**base)


class TestGraphStructure:
    def test_linear_chain(self):
        graph = StepGraph(
            [_step("A"), _step("B", deps=("A",)), _step("C", deps=("B",))]
        )
        assert graph.dependencies_of("C") == frozenset({"B"})
        assert graph.dependents_of("A") == ["B"]

    def test_fan_out_fan_in(self):
        # A -> B -> D; A -> C -> D
        steps = [
            _step("A"),
            _step("B", deps=("A",)),
            _step("C", deps=("A",)),
            _step("D", deps=("B", "C")),
        ]
        graph = StepGraph(steps)
        assert graph.dependencies_of("D") == frozenset({"B", "C"})
        assert graph.dependents_of("A") == ["B", "C"]

    def test_cycle_rejected(self):
        with pytest.raises(QcaeValidationError, match="cycle"):
            StepGraph(
                [_step("A", deps=("B",)), _step("B", deps=("A",))]
            )

    def test_three_node_cycle_rejected(self):
        with pytest.raises(QcaeValidationError, match="cycle"):
            StepGraph(
                [
                    _step("A", deps=("C",)),
                    _step("B", deps=("A",)),
                    _step("C", deps=("B",)),
                ]
            )

    def test_self_dependency_rejected(self):
        with pytest.raises(QcaeValidationError, match="itself"):
            StepGraph([_step("A", deps=("A",))])

    def test_missing_dependency_rejected(self):
        with pytest.raises(QcaeValidationError, match="missing"):
            StepGraph([_step("A", deps=("GHOST",))])

    def test_duplicate_step_rejected(self):
        with pytest.raises(QcaeValidationError, match="duplicate"):
            StepGraph([_step("A"), _step("A")])


class TestReadiness:
    def test_only_roots_runnable_initially(self):
        steps = [
            _step("A"),
            _step("B", deps=("A",)),
            _step("C", deps=("A",)),
            _step("D", deps=("B", "C")),
        ]
        runnable = [s.step_id for s in runnable_steps(steps)]
        assert runnable == ["A"]

    def test_ready_after_predecessor_succeeds(self):
        steps = [
            _step("A", status=RuntimeStepStatus.SUCCEEDED),
            _step("B", deps=("A",)),
            _step("C", deps=("A",)),
            _step("D", deps=("B", "C")),
        ]
        runnable = sorted(s.step_id for s in runnable_steps(steps))
        assert runnable == ["B", "C"]

    def test_join_waits_for_all_predecessors(self):
        steps = [
            _step("A", status=RuntimeStepStatus.SUCCEEDED),
            _step("B", status=RuntimeStepStatus.SUCCEEDED),
            _step("C", status=RuntimeStepStatus.RUNNING),
            _step("D", deps=("B", "C")),
        ]
        runnable = [s.step_id for s in runnable_steps(steps)]
        assert runnable == []

    def test_join_opens_when_both_succeed(self):
        steps = [
            _step("B", status=RuntimeStepStatus.SUCCEEDED),
            _step("C", status=RuntimeStepStatus.SUCCEEDED),
            _step("D", deps=("B", "C")),
        ]
        runnable = [s.step_id for s in runnable_steps(steps)]
        assert runnable == ["D"]

    def test_failed_predecessor_does_not_satisfy_gate(self):
        steps = [
            _step("A", status=RuntimeStepStatus.FAILED),
            _step("B", deps=("A",)),
        ]
        assert runnable_steps(steps) == []

    def test_cancelled_step_excludes_its_dependents(self):
        steps = [
            _step("A", status=RuntimeStepStatus.CANCELLED),
            _step("B", deps=("A",), status=RuntimeStepStatus.CANCELLED),
            _step("C"),
        ]
        runnable = [s.step_id for s in runnable_steps(steps)]
        assert runnable == ["C"]

    def test_custom_completion_condition_allows_partial_join(self):
        steps = [
            _step("A", status=RuntimeStepStatus.PARTIAL),
            _step("B", deps=("A",)),
        ]
        runnable = runnable_steps(
            steps,
            completion_condition=lambda s: s.status in (
                RuntimeStepStatus.SUCCEEDED,
                RuntimeStepStatus.PARTIAL,
            ),
        )
        assert [s.step_id for s in runnable] == ["B"]
