"""P2 job graph semantics (P2 directive §7; Book V 12.1 job graph).

Minimum durable directed job/step graph: dependencies between steps of one
job, with fan-out/fan-in and readiness derivation. Rejects cycles, missing
dependency targets, and self-dependency. Not a general workflow framework.
"""

from __future__ import annotations

from typing import Dict, FrozenSet, Iterable, List, Sequence

from qcae.core.errors import QcaeValidationError
from qcae.orchestration.jobs.runtime import RuntimeStep, RuntimeStepStatus

__all__ = ["StepGraph", "validate_step_graph", "runnable_steps"]


class StepGraph:
    """Read-only view over one job's steps with derived readiness."""

    def __init__(self, steps: Sequence[RuntimeStep]) -> None:
        self._by_id: Dict[str, RuntimeStep] = {}
        self._deps: Dict[str, FrozenSet[str]] = {}
        for step in steps:
            if step.step_id in self._by_id:
                raise QcaeValidationError(f"duplicate step id {step.step_id!r}")
            self._by_id[step.step_id] = step
        # Validate targets/self-deps before cycle check so error messages
        # name the structural defect precisely.
        for step in steps:
            for dep in step.dependencies:
                if dep == step.step_id:
                    raise QcaeValidationError(
                        f"step {step.step_id!r} depends on itself"
                    )
                if dep not in self._by_id:
                    raise QcaeValidationError(
                        f"step {step.step_id!r} depends on missing step {dep!r}"
                    )
            self._deps[step.step_id] = frozenset(step.dependencies)
        self._assert_acyclic()

    def _assert_acyclic(self) -> None:
        WHITE, GRAY, BLACK = 0, 1, 2
        color: Dict[str, int] = {sid: WHITE for sid in self._by_id}

        def visit(node: str) -> None:
            color[node] = GRAY
            for dep in self._deps[node]:
                if color[dep] == GRAY:
                    raise QcaeValidationError(
                        f"dependency cycle detected through step {dep!r}"
                    )
                if color[dep] == WHITE:
                    visit(dep)
            color[node] = BLACK

        for sid in self._by_id:
            if color[sid] == WHITE:
                visit(sid)

    @property
    def step_ids(self) -> List[str]:
        return list(self._by_id)

    def step(self, step_id: str) -> RuntimeStep:
        return self._by_id[step_id]

    def is_terminal(self, step_id: str) -> bool:
        return not is_open(self._by_id[step_id])

    def dependencies_of(self, step_id: str) -> FrozenSet[str]:
        return self._deps[step_id]

    def dependents_of(self, step_id: str) -> List[str]:
        return [
            sid for sid, deps in self._deps.items() if step_id in deps
        ]

    def runnable(
        self,
        *,
        completion_condition=None,
    ) -> List[RuntimeStep]:
        """Steps whose dependencies satisfy their completion conditions.

        Default completion condition: dependency status is SUCCEEDED
        (PARTIAL counts as incomplete by default; jobs needing lenient
        joins pass an explicit condition — Book V 12.1 "gates join only
        when required evidence exists").
        """
        if completion_condition is None:
            def completion_condition(s: RuntimeStep) -> bool:
                return s.status == RuntimeStepStatus.SUCCEEDED

        runnable: List[RuntimeStep] = []
        for step in self._by_id.values():
            # Only not-yet-started steps become runnable; steps already in
            # flight/waiting/retry keep their own state machine path.
            if step.status is not RuntimeStepStatus.PENDING:
                continue
            if all(
                completion_condition(self._by_id[dep])
                for dep in step.dependencies
            ):
                runnable.append(step)
        return runnable


def is_open(step: RuntimeStep) -> bool:
    """True while the step can still make progress."""
    return step.status not in (
        RuntimeStepStatus.SUCCEEDED,
        RuntimeStepStatus.CANCELLED,
    )


def validate_step_graph(steps: Sequence[RuntimeStep]) -> StepGraph:
    """Build a StepGraph, raising on any structural defect."""
    return StepGraph(steps)


def runnable_steps(
    steps: Sequence[RuntimeStep],
    *,
    completion_condition=None,
) -> List[RuntimeStep]:
    return StepGraph(steps).runnable(completion_condition=completion_condition)
