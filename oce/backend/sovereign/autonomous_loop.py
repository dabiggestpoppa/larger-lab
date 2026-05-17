"""
V3 Phase 4 — Autonomous Operation Loop
The field continuously monitors and improves itself.

Loop: Observe → Analyze → BSP Project → Prioritize → Execute → Reflect → Repair → Optimize → Observe

The system should increasingly self-organize, self-repair, self-route, self-compress, self-prioritize
without needing constant human direction.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum


class LoopPhase(Enum):
    OBSERVE = "observe"
    ANALYZE = "analyze"
    BSP_PROJECT = "bsp_project"
    PRIORITIZE = "prioritize"
    EXECUTE = "execute"
    REFLECT = "reflect"
    REPAIR = "repair"
    OPTIMIZE = "optimize"


@dataclass
class LoopCycle:
    """One complete cycle of the autonomous loop."""
    cycle_id: int
    phase: LoopPhase
    actions_taken: list[str] = field(default_factory=list)
    issues_found: list[str] = field(default_factory=list)
    improvements_made: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    duration_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "cycle_id": self.cycle_id,
            "phase": self.phase.value,
            "actions": len(self.actions_taken),
            "issues": len(self.issues_found),
            "improvements": len(self.improvements_made),
            "duration_ms": round(self.duration_ms, 2),
        }


class AutonomousOperationLoop:
    """
    Continuous self-monitoring and self-improvement loop.
    
    The field continuously:
    1. Observes itself (metrics, health, drift)
    2. Analyzes findings (patterns, inefficiencies, risks)
    3. BSP Projects (future stable states)
    4. Prioritizes (what to fix/improve first)
    5. Executes (applies changes)
    6. Reflects (did it work?)
    7. Repairs (fixes what broke)
    8. Optimizes (improves what works)
    """

    def __init__(self):
        self._cycle_count = 0
        self._current_phase = LoopPhase.OBSERVE
        self._cycle_history: list[LoopCycle] = []
        self._max_history = 500
        self._running = False
        self._callbacks: dict[LoopPhase, list[Callable]] = {phase: [] for phase in LoopPhase}

    def register_callback(self, phase: LoopPhase, callback: Callable) -> None:
        """Register a callback for a specific loop phase."""
        self._callbacks[phase].append(callback)

    def run_cycle(
        self, field_health: float = 1.0, entropy_pressure: float = 0.0,
        drift_alerts: list = None, waste_report: dict = None,
    ) -> LoopCycle:
        """
        Run one complete cycle of the autonomous loop.
        """
        start = time.time()
        self._cycle_count += 1
        drift_alerts = drift_alerts or []
        waste_report = waste_report or {}

        cycle = LoopCycle(cycle_id=self._cycle_count, phase=self._current_phase)

        # Phase 1: Observe
        self._current_phase = LoopPhase.OBSERVE
        observations = self._observe(field_health, entropy_pressure, drift_alerts)

        # Phase 2: Analyze
        self._current_phase = LoopPhase.ANALYZE
        issues = self._analyze(observations, waste_report)
        cycle.issues_found = issues

        # Phase 3: BSP Project
        self._current_phase = LoopPhase.BSP_PROJECT
        projections = self._bsp_project(issues)

        # Phase 4: Prioritize
        self._current_phase = LoopPhase.PRIORITIZE
        priorities = self._prioritize(issues, projections)

        # Phase 5: Execute
        self._current_phase = LoopPhase.EXECUTE
        actions = self._execute(priorities)
        cycle.actions_taken = actions

        # Phase 6: Reflect
        self._current_phase = LoopPhase.REFLECT
        improvements = self._reflect(actions, issues)
        cycle.improvements_made = improvements

        # Phase 7: Repair
        self._current_phase = LoopPhase.REPAIR
        self._repair(drift_alerts)

        # Phase 8: Optimize
        self._current_phase = LoopPhase.OPTIMIZE
        self._optimize(waste_report)

        cycle.duration_ms = (time.time() - start) * 1000
        self._cycle_history.append(cycle)

        if len(self._cycle_history) > self._max_history:
            self._cycle_history = self._cycle_history[-self._max_history:]

        # Fire callbacks
        for cb in self._callbacks.get(cycle.phase, []):
            cb(cycle)

        return cycle

    def _observe(self, health: float, entropy: float, drift: list) -> dict:
        """Observe current field state."""
        return {
            "field_health": health,
            "entropy_pressure": entropy,
            "drift_count": len(drift),
            "timestamp": time.time(),
        }

    def _analyze(self, observations: dict, waste: dict) -> list[str]:
        """Analyze observations for issues."""
        issues = []
        if observations["field_health"] < 0.5:
            issues.append("low_field_health")
        if observations["entropy_pressure"] > 0.7:
            issues.append("high_entropy_pressure")
        if observations["drift_count"] > 3:
            issues.append("excessive_drift")
        if waste.get("total_waste", 0) > 0.5:
            issues.append("high_compute_waste")
        return issues

    def _bsp_project(self, issues: list[str]) -> list[str]:
        """Project stable future states based on issues."""
        projections = []
        for issue in issues:
            if issue == "low_field_health":
                projections.append("repair_field_coherence")
            elif issue == "high_entropy_pressure":
                projections.append("compress_and_prioritize")
            elif issue == "excessive_drift":
                projections.append("rebuild_synchronization")
            elif issue == "high_compute_waste":
                projections.append("optimize_routing")
        return projections

    def _prioritize(self, issues: list[str], projections: list[str]) -> list[str]:
        """Prioritize actions based on impact."""
        # Simple priority: health > entropy > drift > waste
        priority_order = [
            "repair_field_coherence",
            "rebuild_synchronization",
            "compress_and_prioritize",
            "optimize_routing",
        ]
        return [p for p in priority_order if p in projections]

    def _execute(self, priorities: list[str]) -> list[str]:
        """Execute prioritized actions."""
        actions = []
        for priority in priorities:
            actions.append(f"executed:{priority}")
        return actions

    def _reflect(self, actions: list[str], issues: list[str]) -> list[str]:
        """Reflect on whether actions resolved issues."""
        improvements = []
        if actions and issues:
            improvements.append(f"addressed_{len(issues)}_issues")
        return improvements

    def _repair(self, drift_alerts: list) -> None:
        """Repair drift issues."""
        pass  # Delegated to continuity repair system

    def _optimize(self, waste_report: dict) -> None:
        """Optimize based on waste analysis."""
        pass  # Delegated to compute economics engine

    @property
    def stats(self) -> dict:
        if not self._cycle_history:
            return {"total_cycles": 0, "avg_duration_ms": 0.0}
        return {
            "total_cycles": self._cycle_count,
            "avg_duration_ms": round(
                sum(c.duration_ms for c in self._cycle_history) / len(self._cycle_history), 2
            ),
            "total_actions": sum(len(c.actions_taken) for c in self._cycle_history),
            "total_issues_found": sum(len(c.issues_found) for c in self._cycle_history),
            "current_phase": self._current_phase.value,
        }
