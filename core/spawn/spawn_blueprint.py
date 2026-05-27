"""
O3-B2: SpawnBlueprint
======================
Formal orchestration schema.

Defines the structure of a spawn plan: what to spawn, how to configure
it, what context to inject, and what boundaries to enforce.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SpawnPlan:
    """Complete blueprint for spawning an agent."""
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    task_type: str = ""
    complexity: str = "low"
    target_model: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    tools: list[str] = field(default_factory=list)
    execution_boundary: dict[str, Any] = field(default_factory=dict)
    max_turns: int = 50
    timeout_seconds: int = 300
    priority: str = "normal"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "task_type": self.task_type,
            "complexity": self.complexity,
            "target_model": self.target_model,
            "context_keys": list(self.context.keys()),
            "tools": self.tools,
            "max_turns": self.max_turns,
            "timeout_seconds": self.timeout_seconds,
            "priority": self.priority,
        }


class SpawnBlueprint:
    """
    Generates and validates spawn plans from consensus results.
    
    Takes a ConsensusResult from O-2 and produces a SpawnPlan
    that the AgentSpawner can execute.
    """

    # Default model mapping by task type
    DEFAULT_MODELS: dict[str, str] = {
        "coding": "qwen/qwen-2.5-coder-32b-instruct",
        "research": "deepseek/deepseek-chat",
        "architecture": "deepseek/deepseek-reasoner",
        "repair": "qwen/qwen-2.5-coder-32b-instruct",
        "debugging": "qwen/qwen-2.5-coder-32b-instruct",
        "orchestration": "deepseek/deepseek-chat",
        "visualization": "qwen/qwen-2.5-coder-32b-instruct",
        "automation": "qwen/qwen-2.5-coder-32b-instruct",
        "system_analysis": "deepseek/deepseek-reasoner",
        "general": "deepseek/deepseek-chat",
    }

    # Default tool sets by task type
    DEFAULT_TOOLS: dict[str, list[str]] = {
        "coding": ["read_file", "write_file", "run_terminal", "search_code"],
        "research": ["web_search", "read_file", "summarize"],
        "architecture": ["read_file", "write_file", "diagram"],
        "repair": ["read_file", "run_terminal", "search_code", "test"],
        "debugging": ["read_file", "run_terminal", "search_code", "inspect"],
        "orchestration": ["spawn_agent", "delegate", "monitor"],
        "visualization": ["read_file", "write_file", "render"],
        "automation": ["run_terminal", "write_file", "schedule"],
        "system_analysis": ["read_file", "run_terminal", "inspect", "diagram"],
        "general": ["read_file", "write_file", "run_terminal"],
    }

    def create_plan(
        self,
        task_type: str | None = None,
        complexity: str | None = None,
        context: dict[str, Any] | None = None,
        capabilities: list[str] | None = None,
        recommended_model: str = "",
        spawn_required: bool = True,
        consensus_result: Any = None,
        user_input: str = "",
    ) -> SpawnPlan:
        """Create a spawn plan from consensus output or direct parameters.
        
        Supports two calling conventions:
        1. Direct: create_plan(task_type='coding', complexity='medium', ...)
        2. From consensus: create_plan(consensus_result=result, user_input='...')
        """
        # Extract from consensus_result if provided
        if consensus_result is not None:
            task_type = getattr(consensus_result, 'task_type', task_type)
            if hasattr(task_type, 'value'):
                task_type = task_type.value
            complexity = getattr(consensus_result, 'complexity', complexity)
            recommended_model = getattr(consensus_result, 'recommended_model', recommended_model)
            caps = getattr(consensus_result, 'required_capabilities', None)
            if caps:
                capabilities = caps
            if context is None:
                context = {}
            context['user_input'] = user_input
            context['routing_path'] = getattr(consensus_result, 'routing_path', [])
            context['confidence'] = getattr(consensus_result, 'confidence', 0.0)
        model = recommended_model or self.DEFAULT_MODELS.get(task_type, "deepseek/deepseek-chat")
        tools = self.DEFAULT_TOOLS.get(task_type, ["read_file", "write_file"])

        # Add capability-specific tools
        if capabilities:
            for cap in capabilities:
                if cap == "TERMINAL" and "run_terminal" not in tools:
                    tools.append("run_terminal")
                elif cap == "WEB_SEARCH" and "web_search" not in tools:
                    tools.append("web_search")
                elif cap == "REPO_ACCESS" and "search_code" not in tools:
                    tools.append("search_code")

        # Adjust limits by complexity
        max_turns = {"low": 20, "medium": 50, "high": 100, "critical": 200}.get(complexity, 50)
        timeout = {"low": 120, "medium": 300, "high": 600, "critical": 1200}.get(complexity, 300)

        return SpawnPlan(
            task_type=task_type,
            complexity=complexity,
            target_model=model,
            context=context,
            tools=tools,
            max_turns=max_turns,
            timeout_seconds=timeout,
            execution_boundary=self._build_boundary(complexity, tools),
        )

    def _build_boundary(self, complexity: str, tools: list[str]) -> dict[str, Any]:
        """Build execution boundary configuration."""
        return {
            "max_file_writes": {"low": 5, "medium": 20, "high": 50, "critical": 100}.get(complexity, 20),
            "max_terminal_commands": {"low": 10, "medium": 30, "high": 100, "critical": 200}.get(complexity, 30),
            "allowed_tools": tools,
            "allow_network": True,
            "allow_file_system": True,
            "sandbox_enabled": complexity in ("high", "critical"),
        }

    def validate_plan(self, plan: SpawnPlan) -> tuple[bool, list[str]]:
        """Validate a spawn plan. Returns (valid, list_of_issues)."""
        issues = []
        if not plan.task_type:
            issues.append("Missing task_type")
        if not plan.target_model:
            issues.append("Missing target_model")
        if plan.max_turns < 1:
            issues.append("max_turns must be >= 1")
        if plan.timeout_seconds < 10:
            issues.append("timeout_seconds must be >= 10")
        if not plan.tools:
            issues.append("No tools specified")
        return (len(issues) == 0, issues)
