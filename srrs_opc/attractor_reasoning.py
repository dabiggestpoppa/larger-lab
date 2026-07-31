"""
Attractor Reasoning Engine
============================
Phase 7: Reasoning converges toward stable cyclic attractors.
"""

import json
import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from enum import Enum


class AttractorState:
    """A stable cyclic attractor in reasoning space."""

    def __init__(self, attractor_id: str, dimension: int = 3):
        self.attractor_id = attractor_id
        self.dimension = dimension
        self.position = [0.0] * dimension
        self.velocity = [0.0] * dimension
        self.stability = 0.0
        self.convergence_count = 0
        self.last_updated = datetime.now(timezone.utc).isoformat()
        self.trajectory: List[List[float]] = []

    def update(self, new_position: List[float], learning_rate: float = 0.1):
        if len(new_position) != self.dimension:
            new_position = new_position[:self.dimension] + [0.0] * (self.dimension - len(new_position))
        for i in range(self.dimension):
            self.velocity[i] = self.velocity[i] * 0.9 + (new_position[i] - self.position[i]) * learning_rate
            self.position[i] += self.velocity[i]
        velocity_magnitude = math.sqrt(sum(v ** 2 for v in self.velocity))
        self.stability = min(1.0, self.stability + (1.0 - velocity_magnitude) * 0.05)
        self.convergence_count += 1
        self.trajectory.append(list(self.position))
        if len(self.trajectory) > 100:
            self.trajectory = self.trajectory[-50:]
        self.last_updated = datetime.now(timezone.utc).isoformat()

    def is_stable(self, threshold: float = 0.7) -> bool:
        return self.stability >= threshold

    def distance_to(self, point: List[float]) -> float:
        if len(point) != self.dimension:
            point = point[:self.dimension] + [0.0] * (self.dimension - len(point))
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(self.position, point)))

    def to_dict(self) -> dict:
        return {
            "attractor_id": self.attractor_id,
            "stability": round(self.stability, 3),
            "convergence_count": self.convergence_count,
            "is_stable": self.is_stable(),
            "position": [round(p, 3) for p in self.position],
        }


class AttractorReasoningEngine:
    """Reasoning engine that converges toward stable cyclic attractors."""

    def __init__(self, dimension: int = 3, convergence_threshold: float = 0.7):
        self.dimension = dimension
        self.convergence_threshold = convergence_threshold
        self._attractors: Dict[str, AttractorState] = {}
        self._reasoning_log: List[dict] = []

    def create_attractor(self, attractor_id: str) -> AttractorState:
        if attractor_id not in self._attractors:
            self._attractors[attractor_id] = AttractorState(attractor_id, self.dimension)
        return self._attractors[attractor_id]

    def reason(self, problem_state: List[float], attractor_id: str,
               max_iterations: int = 20) -> dict:
        attractor = self.create_attractor(attractor_id)
        for iteration in range(max_iterations):
            current_distance = attractor.distance_to(problem_state)
            new_position = [
                problem_state[i] * (1 - attractor.stability) + attractor.position[i] * attractor.stability
                for i in range(self.dimension)
            ]
            attractor.update(new_position)
            self._reasoning_log.append({
                "iteration": iteration,
                "attractor_id": attractor_id,
                "distance": round(current_distance, 3),
                "stability": round(attractor.stability, 3),
            })
            if attractor.is_stable(self.convergence_threshold):
                return {
                    "status": "converged",
                    "attractor_id": attractor_id,
                    "iterations": iteration + 1,
                    "stability": round(attractor.stability, 3),
                    "compressed_insight": [round(p, 3) for p in attractor.position],
                }
        return {
            "status": "partial_convergence",
            "attractor_id": attractor_id,
            "iterations": max_iterations,
            "stability": round(attractor.stability, 3),
            "compressed_insight": [round(p, 3) for p in attractor.position],
        }

    def get_stable_attractors(self) -> List[dict]:
        return [a.to_dict() for a in self._attractors.values() if a.is_stable()]

    def get_stats(self) -> dict:
        if not self._attractors:
            return {"status": "no_attractors"}
        stabilities = [a.stability for a in self._attractors.values()]
        return {
            "total_attractors": len(self._attractors),
            "stable_attractors": sum(1 for a in self._attractors.values() if a.is_stable()),
            "avg_stability": round(sum(stabilities) / len(stabilities), 3),
            "total_reasoning_steps": len(self._reasoning_log),
        }


if __name__ == "__main__":
    engine = AttractorReasoningEngine(dimension=3)
    result = engine.reason(problem_state=[0.8, 0.2, 0.5], attractor_id="problem_alpha")
    print(f"Result: {json.dumps(result, indent=2)}")
    print(f"Stats: {json.dumps(engine.get_stats(), indent=2)}")
