"""
6_resonance.belief_propagation
=================================
Bayesian belief propagation across the agent network.

Propagates and updates beliefs across connected agents using
weighted averaging with damping for convergence.

Status: IMPLEMENTED
"""
import logging
import uuid
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.resonance.belief_propagation")


class BeliefRecord(BaseModel):
    """A single belief held by an agent."""
    belief_id: str
    agent_id: str
    probability: float = 0.5  # 0.0 to 1.0
    confidence: float = 1.0
    iteration: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PropagationResult(BaseModel):
    """Result of a belief propagation run."""
    belief_id: str
    iterations: int
    converged: bool
    residual: float
    final_beliefs: Dict[str, float] = Field(default_factory=dict)


class BeliefPropagationConfig(BaseModel):
    """Configuration for belief_propagation."""
    enabled: bool = True
    convergence_threshold: float = 0.01
    max_iterations: int = 100
    damping_factor: float = 0.5


class BeliefPropagationModule:
    """Bayesian belief propagation across agents."""

    def __init__(self):
        self.config = BeliefPropagationConfig()
        self.running = False
        self._lock = Lock()
        self._beliefs: Dict[str, Dict[str, BeliefRecord]] = {}  # belief_id -> agent_id -> record
        self._propagation_history: List[PropagationResult] = []
        self._agent_connections: Dict[str, List[str]] = {}  # agent_id -> [neighbor_ids]

    def start(self) -> None:
        self.running = True
        logger.info("BeliefPropagationModule started")

    def stop(self) -> None:
        self.running = False
        logger.info("BeliefPropagationModule stopped")

    def connect_agents(self, agent_a: str, agent_b: str) -> None:
        """Create a bidirectional connection between two agents."""
        with self._lock:
            self._agent_connections.setdefault(agent_a, []).append(agent_b)
            self._agent_connections.setdefault(agent_b, []).append(agent_a)

    def set_belief(self, agent_id: str, belief_id: str, probability: float,
                   confidence: float = 1.0, **metadata) -> None:
        """Set an agent's belief on a topic."""
        with self._lock:
            if belief_id not in self._beliefs:
                self._beliefs[belief_id] = {}
            self._beliefs[belief_id][agent_id] = BeliefRecord(
                belief_id=belief_id,
                agent_id=agent_id,
                probability=max(0.0, min(1.0, probability)),
                confidence=confidence,
                metadata=metadata,
            )
            logger.debug("Belief set: %s -> %s = %.3f", agent_id, belief_id, probability)

    def get_belief(self, agent_id: str, belief_id: str) -> Optional[BeliefRecord]:
        """Get an agent's current belief on a topic."""
        with self._lock:
            return self._beliefs.get(belief_id, {}).get(agent_id)

    def get_all_beliefs(self, belief_id: str) -> Dict[str, BeliefRecord]:
        """Get all agent beliefs on a topic."""
        with self._lock:
            return dict(self._beliefs.get(belief_id, {}))

    def propagate(self, belief_id: str) -> PropagationResult:
        """
        Propagate a belief across the agent network.

        Uses iterative weighted averaging with damping until convergence
        or max_iterations reached.
        """
        with self._lock:
            beliefs = self._beliefs.get(belief_id, {})
            if not beliefs:
                return PropagationResult(
                    belief_id=belief_id, iterations=0,
                    converged=True, residual=0.0,
                )

            # Current probabilities
            probs = {aid: rec.probability for aid, rec in beliefs.items()}
            damping = self.config.damping_factor
            threshold = self.config.convergence_threshold

            for iteration in range(1, self.config.max_iterations + 1):
                new_probs = {}
                max_delta = 0.0

                for agent_id in probs:
                    neighbors = self._agent_connections.get(agent_id, [])
                    neighbor_probs = [probs[n] for n in neighbors if n in probs]

                    if neighbor_probs:
                        avg_neighbor = sum(neighbor_probs) / len(neighbor_probs)
                        # Damped update: blend current with neighbor average
                        updated = damping * probs[agent_id] + (1 - damping) * avg_neighbor
                    else:
                        updated = probs[agent_id]

                    new_probs[agent_id] = updated
                    max_delta = max(max_delta, abs(updated - probs[agent_id]))

                probs = new_probs

                if max_delta < threshold:
                    result = PropagationResult(
                        belief_id=belief_id,
                        iterations=iteration,
                        converged=True,
                        residual=max_delta,
                        final_beliefs=dict(probs),
                    )
                    self._propagation_history.append(result)
                    logger.info("Belief %s converged in %d iterations (residual=%.6f)",
                                belief_id, iteration, max_delta)
                    return result

            # Did not converge
            result = PropagationResult(
                belief_id=belief_id,
                iterations=self.config.max_iterations,
                converged=False,
                residual=max_delta,
                final_beliefs=dict(probs),
            )
            self._propagation_history.append(result)
            logger.warning("Belief %s did not converge after %d iterations", belief_id, self.config.max_iterations)
            return result

    def get_belief_network_stats(self) -> Dict[str, Any]:
        """Get statistics about the belief network."""
        with self._lock:
            total_beliefs = sum(len(agents) for agents in self._beliefs.values())
            unique_topics = len(self._beliefs)
            total_connections = sum(len(n) for n in self._agent_connections.values()) // 2
            converged_count = sum(1 for r in self._propagation_history if r.converged)
            return {
                "unique_belief_topics": unique_topics,
                "total_belief_records": total_beliefs,
                "agent_connections": total_connections,
                "propagation_runs": len(self._propagation_history),
                "converged_runs": converged_count,
                "avg_iterations": (
                    sum(r.iterations for r in self._propagation_history) / len(self._propagation_history)
                    if self._propagation_history else 0.0
                ),
            }
