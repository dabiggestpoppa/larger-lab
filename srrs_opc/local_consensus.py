"""
Local Consensus Engines
========================
Phase 3 (Updated): Consensus is separate from synchronization.

Synchronization transfers information.
Consensus produces stable overlap closure.

Consensus only occurs where overlap exists.
Probabilistic closure, not universal truth.
"""

import json
import math
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from collections import defaultdict


class LocalConsensusEngine:
    """
    Produces stable overlap closure through probabilistic consensus.

    Key distinction: consensus != synchronization.
    - Sync: transfers information between observers
    - Consensus: produces stable closure in overlap regions
    """

    def __init__(self, engine_id: str, observers: List[str]):
        self.engine_id = engine_id
        self.observers = observers
        self.topics: Dict[str, Dict[str, Any]] = {}
        self.consensus_history: List[dict] = []
        self.convergence_threshold = 0.8

    def propose(self, observer_id: str, topic: str, value: Any, confidence: float = 0.5):
        """An observer proposes a value for a topic."""
        if topic not in self.topics:
            self.topics[topic] = {
                "proposals": {},
                "consensus_value": None,
                "consensus_confidence": 0.0,
                "converged": False,
                "rounds": 0
            }

        self.topics[topic]["proposals"][observer_id] = {
            "value": value,
            "confidence": max(0.0, min(1.0, confidence)),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def evaluate_consensus(self, topic: str) -> dict:
        """Evaluate whether consensus has been reached for a topic."""
        if topic not in self.topics:
            return {"converged": False, "reason": "topic_not_found"}

        topic_data = self.topics[topic]
        proposals = topic_data["proposals"]

        if len(proposals) < 2:
            return {"converged": False, "reason": "insufficient_proposals"}

        # Group proposals by value
        value_groups: Dict[str, List[dict]] = defaultdict(list)
        for observer_id, proposal in proposals.items():
            value_key = str(proposal["value"])
            value_groups[value_key].append(proposal)

        # Find the value with highest aggregate confidence
        best_value = None
        best_confidence = 0.0
        total_confidence = 0.0

        for value_key, group in value_groups.items():
            group_confidence = sum(p["confidence"] for p in group) / len(group)
            total_confidence += group_confidence
            if group_confidence > best_confidence:
                best_confidence = group_confidence
                best_value = group[0]["value"]

        # Consensus reached if best value has sufficient confidence
        converged = best_confidence >= self.convergence_threshold

        topic_data["consensus_value"] = best_value
        topic_data["consensus_confidence"] = round(best_confidence, 3)
        topic_data["converged"] = converged
        topic_data["rounds"] += 1

        result = {
            "topic": topic,
            "converged": converged,
            "consensus_value": best_value,
            "consensus_confidence": round(best_confidence, 3),
            "participating_observers": len(proposals),
            "rounds": topic_data["rounds"],
        }

        self.consensus_history.append(result)
        return result

    def get_local_closure(self, topic: str) -> Optional[dict]:
        """Get the current local consensus closure for a topic."""
        if topic in self.topics:
            t = self.topics[topic]
            return {
                "topic": topic,
                "value": t["consensus_value"],
                "confidence": t["consensus_confidence"],
                "converged": t["converged"],
            }
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "engine_id": self.engine_id,
            "observers": self.observers,
            "topics": {
                t: {
                    "converged": d["converged"],
                    "consensus_value": d["consensus_value"],
                    "consensus_confidence": d["consensus_confidence"],
                    "rounds": d["rounds"],
                }
                for t, d in self.topics.items()
            },
            "total_rounds": sum(d["rounds"] for d in self.topics.values()),
        }
