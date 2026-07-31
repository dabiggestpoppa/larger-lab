"""
V3 Phase 4 — Executive Router

Replaces static orchestration. Dynamically selects agents, models, tools, 
topology structures, compute allocation, execution pathways based on entropy 
pressure, resonance fit, cost, continuity stability, task topology.
"""

from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RoutingDecision:
    """A routing decision made by the executive router."""
    decision_id: str
    timestamp: float
    selected_agent: str
    selected_model: str
    selected_tool: str
    confidence: float
    entropy_pressure: float
    resonance_fit: float
    cost_estimate: float
    continuity_stability: float
    task_topology: str

    def to_dict(self) -> dict:
        return {
            "decision_id": self.decision_id,
            "timestamp": self.timestamp,
            "selected_agent": self.selected_agent,
            "selected_model": self.selected_model,
            "selected_tool": self.selected_tool,
            "confidence": self.confidence,
            "entropy_pressure": self.entropy_pressure,
            "resonance_fit": self.resonance_fit,
            "cost_estimate": self.cost_estimate,
            "continuity_stability": self.continuity_stability,
            "task_topology": self.task_topology,
        }


class ExecutiveRouter:
    """
    Executive Router — Dynamic agent/model/tool routing.
    
    Selects optimal execution pathways based on entropy pressure, resonance fit,
    cost, continuity stability, and task topology.
    """

    def __init__(self):
        self._decision_history: list[RoutingDecision] = []
        self._available_agents = ["claude", "gpt", "gemini", "llama"]
        self._available_models = ["opus", "sonnet", "haiku", "gpt-4", "gpt-3.5"]
        self._available_tools = ["terminal", "browser", "desktop", "memory"]

    def route(
        self,
        entropy_pressure: float,
        resonance_fit: float,
        cost_budget: float,
        continuity_stability: float,
        task_topology: str,
    ) -> RoutingDecision:
        """
        Make a routing decision based on current conditions.
        
        Args:
            entropy_pressure: Current entropy pressure (0-1)
            resonance_fit: Resonance fit score (0-1)
            cost_budget: Available cost budget
            continuity_stability: Continuity stability score (0-1)
            task_topology: Type of task topology
            
        Returns:
            RoutingDecision with selected agent, model, and tool
        """
        # Calculate confidence based on inputs
        confidence = self._calculate_confidence(
            entropy_pressure, resonance_fit, continuity_stability
        )

        # Select agent based on entropy pressure
        agent = self._select_agent(entropy_pressure, task_topology)

        # Select model based on resonance fit and cost
        model = self._select_model(resonance_fit, cost_budget)

        # Select tool based on task topology
        tool = self._select_tool(task_topology)

        decision = RoutingDecision(
            decision_id=f"route-{uuid.uuid4().hex[:8]}",
            timestamp=time.time(),
            selected_agent=agent,
            selected_model=model,
            selected_tool=tool,
            confidence=confidence,
            entropy_pressure=entropy_pressure,
            resonance_fit=resonance_fit,
            cost_estimate=self._estimate_cost(model, tool),
            continuity_stability=continuity_stability,
            task_topology=task_topology,
        )

        self._decision_history.append(decision)
        return decision

    def _calculate_confidence(
        self, entropy_pressure: float, resonance_fit: float, continuity_stability: float
    ) -> float:
        """Calculate routing confidence score."""
        return (resonance_fit * 0.4 + continuity_stability * 0.4 + (1 - entropy_pressure) * 0.2)

    def _select_agent(self, entropy_pressure: float, task_topology: str) -> str:
        """Select agent based on entropy pressure and task type."""
        if entropy_pressure > 0.7:
            return "claude"  # Better for high entropy
        elif task_topology == "research":
            return "gemini"
        elif task_topology == "coding":
            return "claude"
        else:
            return "claude"

    def _select_model(self, resonance_fit: float, cost_budget: float) -> str:
        """Select model based on resonance fit and cost budget."""
        if cost_budget < 0.1:
            return "haiku"
        elif resonance_fit > 0.8:
            return "opus"
        elif resonance_fit > 0.5:
            return "sonnet"
        else:
            return "haiku"

    def _select_tool(self, task_topology: str) -> str:
        """Select tool based on task topology."""
        tool_map = {
            "research": "browser",
            "coding": "terminal",
            "analysis": "memory",
            "execution": "desktop",
        }
        return tool_map.get(task_topology, "terminal")

    def _estimate_cost(self, model: str, tool: str) -> float:
        """Estimate cost for model and tool combination."""
        model_costs = {"opus": 0.03, "sonnet": 0.015, "haiku": 0.005, "gpt-4": 0.03, "gpt-3.5": 0.002}
        tool_costs = {"terminal": 0.001, "browser": 0.002, "desktop": 0.003, "memory": 0.0005}
        return model_costs.get(model, 0.01) + tool_costs.get(tool, 0.001)

    def get_stats(self) -> dict:
        """Get router statistics."""
        return {
            "total_decisions": len(self._decision_history),
            "available_agents": len(self._available_agents),
            "available_models": len(self._available_models),
            "available_tools": len(self._available_tools),
        }