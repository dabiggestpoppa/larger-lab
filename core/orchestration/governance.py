"""
Phase 1.6.8 — Execution Governance

Safety layer that prevents runaway cognition, recursive collapse,
and hallucinated execution.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger("oce.governance")


@dataclass
class GovernanceConfig:
    """Configuration for execution governance."""
    max_recursion_depth: int = 5
    max_concurrent_tasks: int = 10
    max_task_duration_seconds: int = 3600  # 1 hour max per task
    min_confidence_threshold: float = 0.3
    max_tool_calls_per_task: int = 100
    allowed_tools: Set[str] = field(default_factory=lambda: {
        "read_file", "write_file", "search", "web_fetch",
        "openalex_search", "vector_search", "graph_query",
        "synthesize", "generate_report", "generate_pdf",
    })
    blocked_tools: Set[str] = field(default_factory=lambda: {
        "delete_file", "execute_shell", "modify_config",
    })


@dataclass
class GovernanceCheck:
    """Result of a governance check."""
    passed: bool = True
    violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_violation(self, msg: str):
        self.violations.append(msg)
        self.passed = False

    def add_warning(self, msg: str):
        self.warnings.append(msg)


class GovernanceEngine:
    """
    Execution safety layer.
    
    Checks:
    - Recursion limits
    - Permission boundaries
    - Tool constraints
    - Resource limits
    - Confidence thresholds
    """

    def __init__(self, config: Optional[GovernanceConfig] = None):
        self.config = config or GovernanceConfig()
        self._task_start_times: Dict[str, float] = {}
        self._tool_call_counts: Dict[str, int] = {}

    def check_recursion(self, current_depth: int) -> GovernanceCheck:
        """Check if recursion depth is within limits."""
        check = GovernanceCheck()
        if current_depth > self.config.max_recursion_depth:
            check.add_violation(
                f"Recursion depth {current_depth} exceeds limit {self.config.max_recursion_depth}"
            )
        return check

    def check_concurrent(self, active_count: int) -> GovernanceCheck:
        """Check if concurrent task count is within limits."""
        check = GovernanceCheck()
        if active_count > self.config.max_concurrent_tasks:
            check.add_violation(
                f"Concurrent tasks {active_count} exceeds limit {self.config.max_concurrent_tasks}"
            )
        return check

    def check_tool_permission(self, tool_name: str) -> GovernanceCheck:
        """Check if a tool is allowed to be invoked."""
        check = GovernanceCheck()
        if tool_name in self.config.blocked_tools:
            check.add_violation(f"Tool '{tool_name}' is blocked")
        elif tool_name not in self.config.allowed_tools:
            check.add_warning(f"Tool '{tool_name}' is not in allowed list")
        return check

    def check_task_duration(self, task_id: str) -> GovernanceCheck:
        """Check if a task has exceeded its maximum duration."""
        check = GovernanceCheck()
        start_time = self._task_start_times.get(task_id)
        if start_time:
            elapsed = time.time() - start_time
            if elapsed > self.config.max_task_duration_seconds:
                check.add_violation(
                    f"Task {task_id} exceeded max duration "
                    f"({elapsed:.0f}s > {self.config.max_task_duration_seconds}s)"
                )
        return check

    def check_tool_call_limit(self, task_id: str) -> GovernanceCheck:
        """Check if a task has exceeded its tool call limit."""
        check = GovernanceCheck()
        count = self._tool_call_counts.get(task_id, 0)
        if count > self.config.max_tool_calls_per_task:
            check.add_violation(
                f"Task {task_id} exceeded tool call limit "
                f"({count} > {self.config.max_tool_calls_per_task})"
            )
        return check

    def check_confidence(self, confidence: float) -> GovernanceCheck:
        """Check if confidence meets minimum threshold."""
        check = GovernanceCheck()
        if confidence < self.config.min_confidence_threshold:
            check.add_warning(
                f"Confidence {confidence:.2f} below threshold {self.config.min_confidence_threshold}"
            )
        return check

    def start_task(self, task_id: str):
        """Record task start time."""
        self._task_start_times[task_id] = time.time()
        self._tool_call_counts[task_id] = 0

    def record_tool_call(self, task_id: str):
        """Record a tool call for a task."""
        self._tool_call_counts[task_id] = self._tool_call_counts.get(task_id, 0) + 1

    def end_task(self, task_id: str):
        """Clean up task tracking."""
        self._task_start_times.pop(task_id, None)
        self._tool_call_counts.pop(task_id, None)

    def full_check(
        self,
        task_id: str = "",
        recursion_depth: int = 0,
        active_tasks: int = 0,
        confidence: float = 1.0,
    ) -> GovernanceCheck:
        """Run all governance checks."""
        check = GovernanceCheck()

        r = self.check_recursion(recursion_depth)
        check.violations.extend(r.violations)
        check.warnings.extend(r.warnings)
        if not r.passed:
            check.passed = False

        c = self.check_concurrent(active_tasks)
        check.violations.extend(c.violations)
        check.warnings.extend(c.warnings)
        if not c.passed:
            check.passed = False

        if task_id:
            d = self.check_task_duration(task_id)
            check.violations.extend(d.violations)
            check.warnings.extend(d.warnings)
            if not d.passed:
                check.passed = False

            t = self.check_tool_call_limit(task_id)
            check.violations.extend(t.violations)
            check.warnings.extend(t.warnings)
            if not t.passed:
                check.passed = False

        conf = self.check_confidence(confidence)
        check.violations.extend(conf.violations)
        check.warnings.extend(conf.warnings)
        if not conf.passed:
            check.passed = False

        if not check.passed:
            logger.warning(f"Governance check failed: {check.violations}")

        return check
