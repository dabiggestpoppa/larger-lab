"""
O-1-B6: ContextDistiller
=========================
Compresses relevant field state for spawned agents.

Inputs: topology, active tasks, runtime state, prior workflows,
entropy state, user objective.

Output: structured orchestration context (NOT massive prompt dumping).
"""

from __future__ import annotations

from typing import Any


class ContextDistiller:
    """
    Distills runtime state into compact, relevant context for agents.
    
    Key principle: LOW NOISE. Only include what the agent needs.
    """

    def distill(
        self,
        task_domain: str,
        complexity: str,
        runtime_state: dict[str, Any] | None = None,
        session_context: dict[str, Any] | None = None,
        topology_state: dict[str, Any] | None = None,
        entropy_state: dict[str, Any] | None = None,
        prior_workflows: list[dict] | None = None,
    ) -> dict[str, Any]:
        """
        Produce a compact context summary for the given task.
        
        Returns structured context with only relevant fields.
        """
        runtime_state = runtime_state or {}
        session_context = session_context or {}
        topology_state = topology_state or {}
        entropy_state = entropy_state or {}
        prior_workflows = prior_workflows or []

        context: dict[str, Any] = {
            "task": {
                "domain": task_domain,
                "complexity": complexity,
            },
            "runtime": self._distill_runtime(runtime_state, task_domain),
            "topology": self._distill_topology(topology_state, task_domain),
            "entropy": self._distill_entropy(entropy_state, task_domain),
            "continuity": self._distill_continuity(session_context, prior_workflows),
        }

        # Estimate token count (rough)
        import json
        context["_meta"] = {
            "estimated_tokens": len(json.dumps(context)) // 4,
            "fields_included": list(context.keys()),
        }

        return context

    def _distill_runtime(self, runtime: dict[str, Any], domain: str) -> dict[str, Any]:
        """Extract only runtime fields relevant to the task domain."""
        if not runtime:
            return {}
        
        # Base: always include active agents
        distilled: dict[str, Any] = {}
        if "active_agents" in runtime:
            distilled["active_agents"] = runtime["active_agents"]
        if "execution_systems" in runtime:
            distilled["execution_systems"] = runtime["execution_systems"]

        # Domain-specific additions
        if domain in ("system_analysis", "orchestration"):
            distilled.update({
                k: v for k, v in runtime.items()
                if k.startswith(("system_", "runtime_", "load_"))
            })

        return distilled

    def _distill_topology(self, topology: dict[str, Any], domain: str) -> dict[str, Any]:
        """Extract topology summary (not full graph)."""
        if not topology:
            return {}
        
        distilled: dict[str, Any] = {}
        if "nodes" in topology:
            distilled["node_count"] = topology["nodes"]
        if "edges" in topology:
            distilled["edge_count"] = topology["edges"]

        if domain in ("system_analysis", "orchestration", "visualization"):
            if "clusters" in topology:
                distilled["cluster_count"] = len(topology["clusters"])
            if "alerts" in topology:
                distilled["alerts"] = topology["alerts"][:5]  # max 5 alerts

        return distilled

    def _distill_entropy(self, entropy: dict[str, Any], domain: str) -> dict[str, Any]:
        """Extract entropy state summary."""
        if not entropy:
            return {}
        
        distilled: dict[str, Any] = {}
        if "level" in entropy:
            distilled["level"] = entropy["level"]
        if "trend" in entropy:
            distilled["trend"] = entropy["trend"]

        if domain in ("system_analysis", "repair"):
            distilled.update({
                k: v for k, v in entropy.items()
                if k.startswith(("zones", "hotspots", "history"))
            })

        return distilled

    def _distill_continuity(
        self,
        session: dict[str, Any],
        prior_workflows: list[dict],
    ) -> dict[str, Any]:
        """Extract continuity-relevant session info."""
        distilled: dict[str, Any] = {}
        
        if "last_domain" in session:
            distilled["previous_domain"] = session["last_domain"]
        if "last_complexity" in session:
            distilled["previous_complexity"] = session["last_complexity"]

        # Include last 3 workflows max
        if prior_workflows:
            distilled["recent_workflows"] = [
                {
                    "domain": w.get("domain", ""),
                    "success": w.get("success", True),
                    "routing_path": w.get("routing_path", ""),
                }
                for w in prior_workflows[-3:]
            ]

        return distilled
