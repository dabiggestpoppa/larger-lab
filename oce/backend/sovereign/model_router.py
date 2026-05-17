"""
V3 Phase 4 — Model Router

OpenRouter abstraction for dynamic model routing. Routes to optimal
model based on task requirements, cost, and performance.
"""

from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelRoute:
    """A model routing decision."""
    route_id: str
    timestamp: float
    model_name: str
    provider: str
    cost: float
    latency: float
    capability_match: float

    def to_dict(self) -> dict:
        return {
            "route_id": self.route_id,
            "timestamp": self.timestamp,
            "model_name": self.model_name,
            "provider": self.provider,
            "cost": self.cost,
            "latency": self.latency,
            "capability_match": self.capability_match,
        }


class ModelRouter:
    """
    Model Router — OpenRouter abstraction for dynamic model routing.
    
    Routes to optimal model based on task requirements, cost, and performance.
    """

    def __init__(self):
        self._route_history: list[ModelRoute] = []
        self._models = {
            "opus": {"provider": "anthropic", "cost": 0.03, "latency": 0.5},
            "sonnet": {"provider": "anthropic", "cost": 0.015, "latency": 0.3},
            "haiku": {"provider": "anthropic", "cost": 0.005, "latency": 0.1},
            "gpt-4": {"provider": "openai", "cost": 0.03, "latency": 0.4},
            "gpt-3.5": {"provider": "openai", "cost": 0.002, "latency": 0.2},
        }

    def route(
        self,
        task_complexity: float,
        cost_budget: float,
        latency_requirement: float,
    ) -> ModelRoute:
        """
        Route to optimal model based on requirements.
        
        Args:
            task_complexity: Complexity of task (0-1)
            cost_budget: Available cost budget
            latency_requirement: Maximum acceptable latency
            
        Returns:
            ModelRoute with selected model
        """
        best_model = None
        best_score = -1

        for model_name, model_info in self._models.items():
            if model_info["cost"] > cost_budget:
                continue
            if model_info["latency"] > latency_requirement:
                continue

            # Score based on capability match
            capability_match = self._calculate_capability_match(model_name, task_complexity)
            score = capability_match - (model_info["cost"] * 10)

            if score > best_score:
                best_score = score
                best_model = model_name

        if best_model is None:
            best_model = "haiku"  # Default fallback

        model_info = self._models[best_model]
        route = ModelRoute(
            route_id=f"route-{uuid.uuid4().hex[:8]}",
            timestamp=time.time(),
            model_name=best_model,
            provider=model_info["provider"],
            cost=model_info["cost"],
            latency=model_info["latency"],
            capability_match=self._calculate_capability_match(best_model, task_complexity),
        )

        self._route_history.append(route)
        return route

    def _calculate_capability_match(self, model_name: str, task_complexity: float) -> float:
        """Calculate capability match for model and task."""
        model_capabilities = {
            "opus": 1.0,
            "sonnet": 0.8,
            "haiku": 0.5,
            "gpt-4": 0.9,
            "gpt-3.5": 0.6,
        }
        capability = model_capabilities.get(model_name, 0.5)
        return 1.0 - abs(capability - task_complexity)

    def get_stats(self) -> dict:
        """Get router statistics."""
        return {
            "total_routes": len(self._route_history),
            "available_models": list(self._models.keys()),
        }