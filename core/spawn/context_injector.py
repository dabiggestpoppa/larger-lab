"""
O3-B3: ContextInjector
=======================
Inject field continuity into spawned agents.

Compresses relevant field state (topology, active tasks, prior workflows,
entropy state, user objective) into a structured context that spawned
agents receive — NOT massive prompt dumping.
"""

from __future__ import annotations

import json
from typing import Any

from core.observer.context_distiller import ContextDistiller


class ContextInjector:
    """
    Builds structured context packages for spawned agents.
    
    Uses O-1 ContextDistiller as the base, then adds spawn-specific
    context: execution boundaries, tool scope, coordination info.
    """

    MAX_CONTEXT_TOKENS = 2000  # Hard limit to prevent prompt bloat

    def __init__(self):
        self.distiller = ContextDistiller()

    def inject(
        self,
        blueprint: Any,
        session_context: dict[str, Any],
        consensus: Any,
    ) -> dict[str, Any]:
        """Legacy-compatible inject method. Delegates to build_context."""
        task_type = getattr(consensus, 'task_type', '')
        if hasattr(task_type, 'value'):
            task_type = task_type.value
        complexity = getattr(consensus, 'complexity', 'low')
        
        field_state = {}
        if session_context:
            field_state = session_context.get('field_state', {})
        field_state['user_input'] = session_context.get('user_input', '')
        field_state['routing_path'] = getattr(consensus, 'routing_path', [])
        
        plan_dict = {}
        if hasattr(blueprint, 'to_dict'):
            plan_dict = blueprint.to_dict()
        elif isinstance(blueprint, dict):
            plan_dict = blueprint
        
        return self.build_context(
            task_type=str(task_type),
            complexity=str(complexity),
            field_state=field_state,
            spawn_plan=plan_dict,
        )

    def build_context(
        self,
        task_type: str,
        complexity: str,
        field_state: dict[str, Any],
        spawn_plan: dict[str, Any],
        prior_results: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Build a structured context package for a spawned agent.
        
        Args:
            task_type: Type of task (coding, research, etc.)
            complexity: low, medium, high, critical
            field_state: Current runtime field state
            spawn_plan: The SpawnPlan for this agent
            prior_results: Results from previous related spawns
            
        Returns:
            Structured context dict with sections:
            - objective: What the agent needs to do
            - constraints: Boundaries and limits
            - environment: Relevant field state
            - coordination: Multi-agent context if applicable
            - history: Prior related results
        """
        context: dict[str, Any] = {}

        # 1. Objective — distilled from spawn plan
        context["objective"] = {
            "task_type": task_type,
            "complexity": complexity,
            "description": spawn_plan.get("description", ""),
            "success_criteria": spawn_plan.get("success_criteria", []),
        }

        # 2. Constraints — from execution boundary
        boundary = spawn_plan.get("execution_boundary", {})
        context["constraints"] = {
            "max_turns": spawn_plan.get("max_turns", 50),
            "timeout_seconds": spawn_plan.get("timeout_seconds", 300),
            "allowed_tools": spawn_plan.get("tools", []),
            "max_file_writes": boundary.get("max_file_writes", 20),
            "max_terminal_commands": boundary.get("max_terminal_commands", 30),
            "sandbox_enabled": boundary.get("sandbox_enabled", False),
        }

        # 3. Environment — compressed field state
        context["environment"] = self._compress_field_state(field_state, task_type)

        # 4. Coordination — if multi-agent
        if field_state.get("active_agents"):
            context["coordination"] = {
                "active_agent_count": len(field_state["active_agents"]),
                "my_role": spawn_plan.get("role", "worker"),
                "coordination_channel": spawn_plan.get("coord_channel", "default"),
            }

        # 5. History — prior results (truncated)
        if prior_results:
            context["history"] = self._summarize_prior_results(prior_results)

        # Enforce token budget
        context = self._enforce_token_budget(context)

        return context

    def _compress_field_state(
        self, field_state: dict[str, Any], task_type: str
    ) -> dict[str, Any]:
        """Extract only the field state relevant to this task type."""
        compressed: dict[str, Any] = {}

        # Always include topology summary
        if "topology" in field_state:
            topo = field_state["topology"]
            compressed["topology"] = {
                "node_count": topo.get("node_count", 0),
                "active_observers": topo.get("active_observers", 0),
                "health": topo.get("health", "unknown"),
            }

        # Include entropy state for repair/debugging tasks
        if task_type in ("repair", "debugging") and "entropy" in field_state:
            compressed["entropy"] = {
                "level": field_state["entropy"].get("level", "normal"),
                "hotspots": field_state["entropy"].get("hotspots", [])[:5],
            }

        # Include active tasks for orchestration
        if task_type == "orchestration" and "active_tasks" in field_state:
            compressed["active_tasks"] = [
                {"id": t.get("id"), "status": t.get("status"), "type": t.get("type")}
                for t in field_state["active_tasks"][:10]
            ]

        # Include user objective
        if "user_objective" in field_state:
            obj = field_state["user_objective"]
            if isinstance(obj, str):
                compressed["user_objective"] = obj[:500]
            elif isinstance(obj, dict):
                compressed["user_objective"] = {k: str(v)[:200] for k, v in obj.items()}

        return compressed

    def _summarize_prior_results(
        self, results: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Summarize prior spawn results for context inheritance."""
        summarized = []
        for r in results[-5:]:  # Last 5 results max
            summarized.append({
                "task_type": r.get("task_type", ""),
                "status": r.get("status", ""),
                "key_findings": r.get("key_findings", [])[:3],
                "output_path": r.get("output_path", ""),
            })
        return summarized

    def _enforce_token_budget(self, context: dict[str, Any]) -> dict[str, Any]:
        """Truncate context to stay within token budget."""
        # Rough estimate: 1 token ≈ 4 chars
        max_chars = self.MAX_CONTEXT_TOKENS * 4
        serialized = json.dumps(context, default=str)
        
        if len(serialized) <= max_chars:
            return context

        # Truncate environment first (least critical for task execution)
        if "environment" in context:
            env = context["environment"]
            for key in list(env.keys()):
                if isinstance(env[key], str) and len(env[key]) > 200:
                    env[key] = env[key][:200] + "..."

        # Truncate history if still over budget
        serialized = json.dumps(context, default=str)
        if len(serialized) > max_chars and "history" in context:
            context["history"] = context["history"][:2]

        return context
