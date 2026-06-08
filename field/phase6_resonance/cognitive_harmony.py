"""
6_resonance.cognitive_harmony
==============================
Measures and maintains cognitive harmony across agents.

Tracks agreement/disagreement levels between all agent pairs,
computes global harmony scores, and identifies discordant pairs
that may need intervention.

Harmony score: 0.0 (total discord) to 1.0 (perfect harmony).
Uses exponential moving average for temporal smoothing.
"""

import logging
from collections import defaultdict
from threading import Lock
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger("field.resonance.harmony")


class CognitiveHarmonyConfig(BaseModel):
    """Configuration for cognitive_harmony."""
    enabled: bool = True
    harmony_window: int = 100
    discord_threshold: float = 0.3
    harmony_decay: float = 0.99


class HarmonyRecord(BaseModel):
    """A single harmony measurement between two agents."""
    agent_a: str
    agent_b: str
    agreement_score: float = 0.0
    timestamp: str = ""


class CognitiveHarmonyModule:
    """cognitive_harmony field module."""

    def __init__(self):
        self.config = CognitiveHarmonyConfig()
        self.running = False
        self._lock = Lock()
        self._harmony_scores: Dict[Tuple[str, str], float] = {}
        self._history: List[HarmonyRecord] = []
        self._global_harmony: float = 1.0
        self._interaction_counts: Dict[Tuple[str, str], int] = defaultdict(int)

    def start(self) -> None:
        """Start the module."""
        self.running = True
        logger.info("CognitiveHarmonyModule started")

    def stop(self) -> None:
        """Stop the module."""
        self.running = False
        logger.info("CognitiveHarmonyModule stopped")

    def _pair_key(self, agent_a: str, agent_b: str) -> Tuple[str, str]:
        """Canonical ordering for agent pair keys."""
        return (agent_a, agent_b) if agent_a <= agent_b else (agent_b, agent_a)

    def record_interaction(self, agent_a: str, agent_b: str, agreement_score: float) -> None:
        """
        Record an interaction between two agents with an agreement score.

        Args:
            agent_a: First agent ID.
            agent_b: Second agent ID.
            agreement_score: 0.0 (total disagreement) to 1.0 (full agreement).
        """
        from datetime import datetime, timezone
        key = self._pair_key(agent_a, agent_b)
        score = max(0.0, min(1.0, agreement_score))

        with self._lock:
            self._interaction_counts[key] += 1
            # Exponential moving average
            prev = self._harmony_scores.get(key, score)
            decay = self.config.harmony_decay
            self._harmony_scores[key] = decay * prev + (1 - decay) * score

            self._history.append(HarmonyRecord(
                agent_a=agent_a, agent_b=agent_b,
                agreement_score=score,
                timestamp=datetime.now(timezone.utc).isoformat()
            ))

            # Trim history
            if len(self._history) > self.config.harmony_window * 10:
                self._history = self._history[-self.config.harmony_window:]

            # Recompute global harmony
            if self._harmony_scores:
                self._global_harmony = sum(self._harmony_scores.values()) / len(self._harmony_scores)

        logger.debug("Harmony recorded: %s <-> %s = %.3f", agent_a, agent_b, score)

    def get_harmony_score(self, agent_a: str, agent_b: str) -> float:
        """
        Get the current harmony score between two agents.

        Returns:
            Harmony score 0.0-1.0. Defaults to 1.0 if no data.
        """
        key = self._pair_key(agent_a, agent_b)
        with self._lock:
            return self._harmony_scores.get(key, 1.0)

    def get_global_harmony(self) -> float:
        """
        Get the global harmony score across all agent pairs.

        Returns:
            Global harmony 0.0-1.0.
        """
        with self._lock:
            return round(self._global_harmony, 4)

    def get_discordant_pairs(self, threshold: Optional[float] = None) -> List[Dict]:
        """
        Get pairs of agents with harmony below the threshold.

        Args:
            threshold: Discord threshold (default from config).

        Returns:
            List of dicts with agent_a, agent_b, harmony_score.
        """
        thresh = threshold if threshold is not None else self.config.discord_threshold
        with self._lock:
            return [
                {"agent_a": k[0], "agent_b": k[1], "harmony_score": round(v, 4)}
                for k, v in self._harmony_scores.items()
                if v < thresh
            ]

    def get_harmony_trend(self, window: Optional[int] = None) -> List[Dict]:
        """
        Get harmony trend over recent history.

        Args:
            window: Number of recent records to analyze.

        Returns:
            List of {timestamp, avg_harmony} dicts.
        """
        w = window or self.config.harmony_window
        with self._lock:
            recent = self._history[-w:]
            if not recent:
                return []
            # Group by time buckets (simple: just return individual scores)
            return [
                {"timestamp": r.timestamp, "agreement_score": r.agreement_score,
                 "agents": f"{r.agent_a}<->{r.agent_b}"}
                for r in recent
            ]

    def get_stats(self) -> Dict:
        """Get module statistics."""
        with self._lock:
            return {
                "total_pairs": len(self._harmony_scores),
                "total_interactions": sum(self._interaction_counts.values()),
                "global_harmony": round(self._global_harmony, 4),
                "discordant_pairs": len(self.get_discordant_pairs()),
                "history_size": len(self._history),
            }
