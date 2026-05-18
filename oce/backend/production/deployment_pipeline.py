"""
V3 Phase 9 — Deployment Pipeline
Automated build/test/deploy with stage validation.
"""

from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional


class DeploymentStage(str):
    """Pipeline stage identifiers."""
    BUILD = "build"
    TEST = "test"
    VALIDATE = "validate"
    DEPLOY = "deploy"
    VERIFY = "verify"
    ROLLBACK = "rollback"


@dataclass
class DeploymentResult:
    """Result of a pipeline stage execution."""
    stage: str
    passed: bool
    duration_ms: float = 0.0
    message: str = ""
    details: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class DeploymentPipeline:
    """
    Automated build/test/deploy pipeline.
    
    Stages: build → test → validate → deploy → verify
    If any stage fails, the pipeline halts and can trigger rollback.
    """

    STAGES = [
        DeploymentStage.BUILD,
        DeploymentStage.TEST,
        DeploymentStage.VALIDATE,
        DeploymentStage.DEPLOY,
        DeploymentStage.VERIFY,
    ]

    def __init__(self):
        self._history: list[DeploymentResult] = []
        self._stage_handlers: dict[str, callable] = {}

    def register_stage_handler(self, stage: str, handler: callable) -> None:
        """Register a handler function for a pipeline stage."""
        self._stage_handlers[stage] = handler

    def run_stage(self, stage: str, **kwargs) -> DeploymentResult:
        """Run a single pipeline stage."""
        start = time.time()
        handler = self._stage_handlers.get(stage)

        if handler is None:
            result = DeploymentResult(
                stage=stage, passed=False,
                message=f"No handler registered for stage: {stage}",
                duration_ms=(time.time() - start) * 1000,
            )
            self._history.append(result)
            return result

        try:
            handler(**kwargs)
            duration_ms = (time.time() - start) * 1000
            result = DeploymentResult(
                stage=stage, passed=True,
                message=f"Stage '{stage}' completed successfully",
                duration_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            result = DeploymentResult(
                stage=stage, passed=False,
                message=f"Stage '{stage}' failed: {e}",
                duration_ms=duration_ms,
                details={"error": str(e)},
            )

        self._history.append(result)
        return result

    def run_all(self, **kwargs) -> list[DeploymentResult]:
        """Run all pipeline stages in order. Stops on first failure."""
        results = []
        for stage in self.STAGES:
            result = self.run_stage(stage, **kwargs)
            results.append(result)
            if not result.passed:
                break
        return results

    def deploy(self, **kwargs) -> bool:
        """Run full pipeline. Returns True if all stages pass."""
        results = self.run_all(**kwargs)
        return all(r.passed for r in results)

    def get_last_result(self, stage: str) -> Optional[DeploymentResult]:
        """Get the most recent result for a given stage."""
        for r in reversed(self._history):
            if r.stage == stage:
                return r
        return None

    @property
    def history(self) -> list[DeploymentResult]:
        return list(self._history)

    @property
    def stats(self) -> dict:
        if not self._history:
            return {"total_runs": 0, "success_rate": 0.0}

        passed = sum(1 for r in self._history if r.passed)
        avg_duration = sum(r.duration_ms for r in self._history) / len(self._history)
        return {
            "total_runs": len(self._history),
            "passed": passed,
            "failed": len(self._history) - passed,
            "success_rate": round(passed / len(self._history), 4),
            "avg_duration_ms": round(avg_duration, 2),
        }
