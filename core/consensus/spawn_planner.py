"""
O2-B5: SpawnPlanner
====================
Generate task orchestration blueprint.

Creates structured spawn plans for agent execution with full
context injection from vault, shared memory, and session state.
"""

from __future__ import annotations

import uuid
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from pathlib import Path

from core.consensus.shared_memory_bridge import SharedMemoryBridge


@dataclass
class SpawnBlueprint:
    """Formal orchestration schema for spawning agents."""
    blueprint_id: str
    task_type: str
    complexity: str
    timestamp: str
    steps: list[dict[str, Any]] = field(default_factory=list)
    context_injection: dict[str, Any] = field(default_factory=dict)
    execution_boundaries: list[str] = field(default_factory=list)
    fallback_strategy: str = "retry"
    max_retries: int = 3
    timeout_seconds: int = 300

    def to_dict(self) -> dict[str, Any]:
        return {
            "blueprint_id": self.blueprint_id,
            "task_type": self.task_type,
            "complexity": self.complexity,
            "timestamp": self.timestamp,
            "steps": self.steps,
            "context_injection": self.context_injection,
            "execution_boundaries": self.execution_boundaries,
            "fallback_strategy": self.fallback_strategy,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
        }


class SpawnPlanner:
    """
    Generates task orchestration blueprints.

    Creates structured plans for agent spawning with context injection,
    execution boundaries, and fallback strategies.

    Context sources (in priority order):
    1. Vault knowledge (via API query)
    2. Shared memory bridge (recent cross-agent observations)
    3. Session context (active goals, domain, complexity)
    """

    def __init__(self, vault_url: str = "http://127.0.0.1:8000"):
        self.vault_url = vault_url.rstrip("/")
        self.bridge = SharedMemoryBridge()

    def create_blueprint(
        self,
        task_type: str,
        complexity: str,
        user_input: str,
        routing_path: list[str],
        capabilities: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> SpawnBlueprint:
        """
        Create a spawn blueprint for a task.

        Args:
            task_type: Classified task type
            complexity: Estimated complexity
            user_input: Original user input
            routing_path: Observer routing path
            capabilities: Capability matching result
            context: Session context

        Returns:
            SpawnBlueprint with execution plan and full context injection
        """
        blueprint_id = f"bp_{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now(timezone.utc).isoformat()

        # Build execution steps
        steps = self._build_steps(task_type, complexity, routing_path, capabilities)

        # Build context injection from ALL three sources
        context_injection = self._build_context(
            task_type=task_type,
            complexity=complexity,
            user_input=user_input,
            routing_path=routing_path,
            session_context=context,
        )

        # Build execution boundaries
        boundaries = self._build_boundaries(task_type, complexity)

        # Determine fallback strategy
        fallback = self._determine_fallback(complexity)

        return SpawnBlueprint(
            blueprint_id=blueprint_id,
            task_type=task_type,
            complexity=complexity,
            timestamp=timestamp,
            steps=steps,
            context_injection=context_injection,
            execution_boundaries=boundaries,
            fallback_strategy=fallback,
        )

    # ── Context Injection (THE FIX) ────────────────────────────────────

    def _build_context(
        self,
        task_type: str,
        complexity: str,
        user_input: str,
        routing_path: list[str],
        session_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Build full context injection from all sources.

        Sources:
        1. Vault API — relevant patterns, skills, past errors
        2. Shared memory — recent cross-agent observations
        3. Session context — active goals, domain state
        """
        ctx: dict[str, Any] = {
            "task_type": task_type,
            "complexity": complexity,
            "user_input": user_input,
            "routing_path": routing_path,
            "injected_at": datetime.now(timezone.utc).isoformat(),
        }

        # ── Source 1: Vault context ──
        vault_ctx = self._pull_vault_context(task_type)
        if vault_ctx:
            ctx["vault"] = vault_ctx

        # ── Source 2: Shared memory ──
        shared_ctx = self._pull_shared_memory(task_type)
        if shared_ctx:
            ctx["shared_memory"] = shared_ctx

        # ── Source 3: Session context ──
        if session_context:
            ctx["session"] = {
                k: v for k, v in session_context.items()
                if k in ("last_domain", "last_complexity", "active_goals", "recent_tasks")
            }

        return ctx

    def _pull_vault_context(self, task: str) -> dict[str, Any] | None:
        """Pull relevant context from vault via API."""
        try:
            import httpx
            params = {"task": task, "max_skills": 3, "max_patterns": 5}
            resp = httpx.get(
                f"{self.vault_url}/api/vault/context",
                params=params,
                timeout=5.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("context", {})
        except Exception:
            pass  # Vault unavailable — skip gracefully
        return None

    def _pull_shared_memory(self, task: str) -> dict[str, Any] | None:
        """Pull recent observations from shared memory bridge."""
        try:
            recent = self.bridge.read_latest(limit=20)
            consensus = self.bridge.get_all_consensus()
            return {
                "recent_observations": recent,
                "consensus_state": consensus,
            }
        except Exception:
            pass
        return None

    # ── Steps ───────────────────────────────────────────────────────────

    def _build_steps(
        self,
        task_type: str,
        complexity: str,
        routing_path: list[str],
        capabilities: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Build the ordered execution steps."""
        steps = [
            {"step": 1, "action": "validate_input", "params": {"task_type": task_type}},
            {"step": 2, "action": "acquire_context", "params": {"from": ["vault", "shared_memory", "session"]}},
        ]

        if complexity in ("critical", "high"):
            steps.append(
                {"step": 3, "action": "safety_check", "params": {"level": complexity}}
            )

        steps.extend([
            {"step": len(steps) + 1, "action": "execute_task", "params": {"routing": routing_path}},
            {"step": len(steps) + 2, "action": "record_outcome", "params": {"store": ["consensus_memory", "shared_memory"]}},
        ])

        return steps

    # ── Boundaries ──────────────────────────────────────────────────────

    def _build_boundaries(self, task_type: str, complexity: str) -> list[str]:
        """Build execution boundaries."""
        boundaries = ["no_file_deletion", "no_external_api_without_approval"]
        if complexity in ("critical", "high"):
            boundaries.extend([
                "no_database_writes_without_backup",
                "no_production_deployment_without_approval",
            ])
        return boundaries

    def _determine_fallback(self, complexity: str) -> str:
        """Determine fallback strategy."""
        if complexity == "critical":
            return "escalate"
        if complexity == "high":
            return "retry_with_simplification"
        return "retry"