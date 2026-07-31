"""
Distributed Consensus Module
=============================
Phase 3: No master orchestrator — truth stabilizes recursively.

Each patch maintains local confidence and synchronizes probabilistically.
Global coherence emerges statistically from local interactions.

Based on gossip protocols + Bayesian confidence updating.
"""

import json
import random
import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict


class ConsensusState:
    """A patch's local view of a consensus topic."""

    def __init__(self, patch_id: str, topic: str, value: Any, confidence: float = 0.5):
        self.patch_id = patch_id
        self.topic = topic
        self.value = value
        self.confidence = max(0.0, min(1.0, confidence))
        self.version = 1
        self.last_updated = datetime.now(timezone.utc).isoformat()
        self.sources: Dict[str, float] = {}  # patch_id -> confidence received

    def update(self, value: Any, confidence: float, source: str):
        """Update state based on received information."""
        self.sources[source] = confidence

        # Bayesian-inspired confidence update
        if value == self.value:
            # Reinforce: increase confidence
            self.confidence = min(1.0, self.confidence + confidence * 0.1)
        else:
            # Challenge: decrease confidence, consider switching
            self.confidence = max(0.1, self.confidence - confidence * 0.05)

            # Switch if challenger has much higher confidence
            if confidence > self.confidence + 0.3:
                self.value = value
                self.confidence = confidence * 0.8  # Adopt with reduced confidence
                self.version += 1

        self.last_updated = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patch_id": self.patch_id,
            "topic": self.topic,
            "value": self.value,
            "confidence": round(self.confidence, 3),
            "version": self.version,
            "sources": self.sources,
        }


class DistributedConsensus:
    """
    Probabilistic distributed consensus without a central authority.

    Properties:
    - No master orchestrator
    - Each patch maintains local confidence
    - Global coherence emerges from gossip-style synchronization
    - Convergence is statistical, not guaranteed
    """

    def __init__(self, convergence_threshold: float = 0.8,
                 sync_probability: float = 0.3):
        self.convergence_threshold = convergence_threshold
        self.sync_probability = sync_probability
        self._states: Dict[str, Dict[str, ConsensusState]] = {}  # patch_id -> topic -> state
        self._sync_log: List[Dict] = []

    def register_patch(self, patch_id: str):
        """Register a patch for consensus participation."""
        if patch_id not in self._states:
            self._states[patch_id] = {}

    def propose(self, patch_id: str, topic: str, value: Any,
                confidence: float = 0.5) -> ConsensusState:
        """A patch proposes a value for a topic."""
        self.register_patch(patch_id)

        if topic in self._states[patch_id]:
            state = self._states[patch_id][topic]
            state.update(value, confidence, patch_id)
        else:
            state = ConsensusState(patch_id, topic, value, confidence)
            self._states[patch_id][topic] = state

        return state

    def synchronize(self, patch_a: str, patch_b: str, topic: str) -> Dict[str, Any]:
        """
        Synchronize a topic between two patches (gossip-style).
        Only syncs with probability sync_probability (sparse synchronization).
        """
        if random.random() > self.sync_probability:
            return {"synced": False, "reason": "skipped (probabilistic)"}

        state_a = self._states.get(patch_a, {}).get(topic)
        state_b = self._states.get(patch_b, {}).get(topic)

        if not state_a or not state_b:
            return {"synced": False, "reason": "missing state"}

        # Exchange values
        old_a = state_a.value
        old_b = state_b.value

        state_a.update(state_b.value, state_b.confidence, patch_b)
        state_b.update(state_a.value, state_a.confidence, patch_a)

        result = {
            "synced": True,
            "topic": topic,
            "patch_a": {"id": patch_a, "old": old_a, "new": state_a.value, "confidence": state_a.confidence},
            "patch_b": {"id": patch_b, "old": old_b, "new": state_b.value, "confidence": state_b.confidence},
            "converged": state_a.value == state_b.value,
        }

        self._sync_log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **result,
        })

        return result

    def run_gossip_round(self, topic: str) -> List[Dict]:
        """Run one round of gossip synchronization for a topic."""
        patches = [p for p, states in self._states.items() if topic in states]
        results = []

        # Random pairings
        random.shuffle(patches)
        for i in range(0, len(patches) - 1, 2):
            result = self.synchronize(patches[i], patches[i + 1], topic)
            results.append(result)

        return results

    def check_convergence(self, topic: str) -> Dict[str, Any]:
        """Check if consensus has converged for a topic."""
        states = []
        for patch_id, topics in self._states.items():
            if topic in topics:
                states.append(topics[topic])

        if not states:
            return {"converged": False, "reason": "no states"}

        values = [s.value for s in states]
        confidences = [s.confidence for s in states]

        # Check if all values agree
        unique_values = set(str(v) for v in values)
        all_agree = len(unique_values) == 1
        avg_confidence = sum(confidences) / len(confidences)
        min_confidence = min(confidences)

        converged = all_agree and avg_confidence >= self.convergence_threshold

        return {
            "converged": converged,
            "all_agree": all_agree,
            "unique_values": list(unique_values),
            "avg_confidence": round(avg_confidence, 3),
            "min_confidence": round(min_confidence, 3),
            "patch_count": len(states),
        }

    def get_consensus_value(self, topic: str) -> Optional[Dict]:
        """Get the current consensus value for a topic (if converged)."""
        convergence = self.check_convergence(topic)
        if convergence["converged"]:
            # Return the agreed value with highest confidence
            states = [s for p, t in self._states.items() if topic in t for s in [t[topic]]]
            best = max(states, key=lambda s: s.confidence)
            return {
                "value": best.value,
                "confidence": best.confidence,
                "patches_agreed": convergence["patch_count"],
            }
        return None

    def get_all_topics(self) -> List[str]:
        """Get all topics being tracked."""
        topics = set()
        for patch_states in self._states.values():
            topics.update(patch_states.keys())
        return list(topics)

    def get_stats(self) -> Dict[str, Any]:
        """Get consensus statistics."""
        topics = self.get_all_topics()
        converged = sum(1 for t in topics if self.check_convergence(t)["converged"])

        return {
            "total_patches": len(self._states),
            "total_topics": len(topics),
            "converged_topics": converged,
            "total_syncs": len(self._sync_log),
            "convergence_rate": round(converged / max(len(topics), 1), 2),
        }


if __name__ == "__main__":
    consensus = DistributedConsensus(convergence_threshold=0.7, sync_probability=0.8)

    # Patches propose values for "strategy"
    consensus.propose("planner", "strategy", "mean_reversion", 0.8)
    consensus.propose("execution", "strategy", "mean_reversion", 0.6)
    consensus.propose("memory", "strategy", "momentum", 0.5)
    consensus.propose("repair", "strategy", "mean_reversion", 0.7)

    print("Initial state:")
    for patch, topics in consensus._states.items():
        for topic, state in topics.items():
            print(f"  {patch}: {state.value} (conf={state.confidence:.2f})")

    # Run gossip rounds
    for i in range(5):
        results = consensus.run_gossip_round("strategy")
        converged = sum(1 for r in results if r.get("converged"))
        print(f"\nRound {i+1}: {converged}/{len(results)} pairs converged")

    print(f"\nFinal convergence: {json.dumps(consensus.check_convergence('strategy'), indent=2)}")
    print(f"Stats: {json.dumps(consensus.get_stats(), indent=2)}")
