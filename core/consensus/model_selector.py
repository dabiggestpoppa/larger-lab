"""
O2-B6: ModelSelector
=====================
Choose best cognition provider for a task.

Selects appropriate model based on task type, complexity,
and available providers.
"""

from __future__ import annotations

from typing import Any


# Model capabilities and costs
MODEL_REGISTRY: dict[str, dict[str, Any]] = {
    "claude-sonnet-4": {
        "strengths": ["coding", "architecture", "complex_reasoning"],
        "max_context": 200000,
        "cost_per_1k": 0.003,
        "speed": "medium",
        "available": True,
    },
    "claude-haiku-4": {
        "strengths": ["quick_tasks", "simple_queries", "classification"],
        "max_context": 200000,
        "cost_per_1k": 0.001,
        "speed": "fast",
        "available": True,
    },
    "gpt-4o": {
        "strengths": ["coding", "reasoning", "multimodal"],
        "max_context": 128000,
        "cost_per_1k": 0.005,
        "speed": "medium",
        "available": False,  # Not configured by default
    },
    "gpt-4o-mini": {
        "strengths": ["quick_tasks", "simple_queries"],
        "max_context": 128000,
        "cost_per_1k": 0.0003,
        "speed": "fast",
        "available": False,
    },
}

# Task type -> preferred model mapping
TASK_MODEL_PREFERENCE: dict[str, list[str]] = {
    "coding": ["claude-sonnet-4", "gpt-4o", "claude-haiku-4"],
    "research": ["claude-sonnet-4", "claude-haiku-4"],
    "architecture": ["claude-sonnet-4", "gpt-4o"],
    "repair": ["claude-sonnet-4", "claude-haiku-4"],
    "debugging": ["claude-sonnet-4", "gpt-4o"],
    "orchestration": ["claude-sonnet-4", "gpt-4o"],
    "visualization": ["claude-haiku-4", "claude-sonnet-4"],
    "automation": ["claude-haiku-4", "claude-sonnet-4"],
    "system_analysis": ["claude-haiku-4", "claude-sonnet-4"],
    "general": ["claude-haiku-4", "claude-sonnet-4"],
}


class ModelSelector:
    """
    Selects the best model for a given task.

    Considers task type, complexity, cost, and availability.
    """

    def select(
        self,
        task_type: str,
        complexity: str,
        required_capabilities: list[str] | None = None,
        prefer_speed: bool = False,
    ) -> dict[str, Any]:
        """
        Select the best model for a task.

        Returns:
            {
                "model": str,
                "reason": str,
                "fallbacks": list[str],
                "estimated_cost": float,
            }
        """
        preferences = TASK_MODEL_PREFERENCE.get(task_type, ["claude-haiku-4"])

        # Filter by availability
        available = [m for m in preferences if MODEL_REGISTRY.get(m, {}).get("available", False)]

        if not available:
            return {
                "model": "claude-haiku-4",
                "reason": "default_fallback",
                "fallbacks": [],
                "estimated_cost": 0.001,
            }

        # For critical/high complexity, prefer stronger models
        if complexity in ("critical", "high") and not prefer_speed:
            for model in available:
                info = MODEL_REGISTRY.get(model, {})
                if "complex_reasoning" in info.get("strengths", []):
                    return {
                        "model": model,
                        "reason": f"complexity_{complexity}",
                        "fallbacks": available,
                        "estimated_cost": info.get("cost_per_1k", 0.003),
                    }

        # Default: first available
        selected = available[0]
        info = MODEL_REGISTRY.get(selected, {})

        return {
            "model": selected,
            "reason": "default_available",
            "fallbacks": available[1:],
            "estimated_cost": info.get("cost_per_1k", 0.001),
        }

    def get_available_models(self) -> list[dict[str, Any]]:
        """Get list of available models."""
        return [
            {"name": name, **info}
            for name, info in MODEL_REGISTRY.items()
            if info.get("available", False)
        ]
