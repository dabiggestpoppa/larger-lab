"""
Bidirectional Coherence Reinforcement
=======================================
Phase 8: System learns from operator, operator learns from system.

Feedback loops: system suggestions → operator decisions → system model updates.
Coherence metric: alignment between system recommendations and operator actions.

No global state — self-stabilizing coherence engine.
"""

import json
import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict


class FeedbackEvent:
    """A single feedback loop event."""

    def __init__(self, suggestion: str, operator_action: str,
                 aligned: bool, context: Optional[Dict[str, Any]] = None):
        self.suggestion = suggestion
        self.operator_action = operator_action
        self.aligned = aligned
        self.context = context or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "suggestion": self.suggestion,
            "operator_action": self.operator_action,
            "aligned": self.aligned,
            "context": self.context,
            "timestamp": self.timestamp,
        }


class BidirectionalCoherenceEngine:
    """
    Manages bidirectional learning between system and operator.

    Feedback loop:
    1. System makes suggestion
    2. Operator acts (may follow or override)
    3. System records alignment/misalignment
    4. Coherence metric updated
    5. System adapts future suggestions based on coherence history

    Coherence score: 0.0 (system and operator always disagree) to
    1.0 (perfect alignment). Healthy range: 0.4-0.8.
    Too high = system just echoes operator (no value).
    Too low = system is ignored (no trust).
    """

    # Window size for rolling coherence calculation
    WINDOW_SIZE = 20
    # Healthy coherence range
    HEALTHY_MIN = 0.4
    HEALTHY_MAX = 0.8

    def __init__(self, operator_id: str):
        self.operator_id = operator_id
        self._feedback_history: List[FeedbackEvent] = []
        self._suggestion_count = 0
        self._alignment_count = 0
        self._coherence_score: float = 0.5  # Start neutral
        self._system_learning_rate: float = 0.1
        self._operator_trust_score: float = 0.5  # How much operator trusts system

    def record_feedback(self, suggestion: str, operator_action: str,
                        context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Record a feedback event: system suggested X, operator did Y.

        Returns True if aligned, False if not.
        """
        aligned = self._evaluate_alignment(suggestion, operator_action)
        event = FeedbackEvent(
            suggestion=suggestion,
            operator_action=operator_action,
            aligned=aligned,
            context=context,
        )
        self._feedback_history.append(event)
        self._suggestion_count += 1
        if aligned:
            self._alignment_count += 1

        self._update_coherence()
        return aligned

    def _evaluate_alignment(self, suggestion: str, action: str) -> bool:
        """
        Evaluate whether operator action aligns with system suggestion.

        Matching strategy:
        1. Exact match -> aligned
        2. Key term overlap (with simple stemming) -> aligned if >= 50% match
        3. Otherwise -> not aligned
        """
        suggestion_lower = suggestion.lower().strip()
        action_lower = action.lower().strip()

        if suggestion_lower == action_lower:
            return True

        stop_words = {"the", "a", "an", "to", "is", "of", "in", "at", "on", "for"}

        def stem(word: str) -> str:
            for suffix in ("ing", "ed", "es", "s", "ly", "er", "est"):
                if word.endswith(suffix) and len(word) > len(suffix) + 2:
                    return word[:-len(suffix)]
            return word

        suggestion_terms = [stem(w) for w in suggestion_lower.split() if w not in stop_words]
        action_terms = [stem(w) for w in action_lower.split() if w not in stop_words]

        if not suggestion_terms:
            return False

        matches = 0
        for s_term in suggestion_terms:
            for a_term in action_terms:
                if s_term in a_term or a_term in s_term:
                    matches += 1
                    break

        return matches >= len(suggestion_terms) * 0.5

    def _update_coherence(self):
        """Update coherence score using rolling window."""
        recent = self._feedback_history[-self.WINDOW_SIZE:]
        if not recent:
            self._coherence_score = 0.5
            return

        aligned_count = sum(1 for e in recent if e.aligned)
        self._coherence_score = round(aligned_count / len(recent), 3)

        # Update operator trust: if coherence is high, trust increases
        if self._coherence_score > 0.6:
            self._operator_trust_score = min(1.0, self._operator_trust_score + 0.02)
        elif self._coherence_score < 0.3:
            self._operator_trust_score = max(0.0, self._operator_trust_score - 0.05)

    def get_coherence_score(self) -> float:
        """Get current coherence score."""
        return self._coherence_score

    def get_coherence_health(self) -> Dict[str, Any]:
        """
        Assess coherence health.

        Healthy: 0.4-0.8 (system provides value, operator has agency)
        Too low: < 0.4 (system ignored or wrong)
        Too high: > 0.8 (system just echoes, no added value)
        """
        score = self._coherence_score
        if score < self.HEALTHY_MIN:
            status = "too_low"
            diagnosis = "System suggestions are frequently ignored or misaligned. Review suggestion quality."
        elif score > self.HEALTHY_MAX:
            status = "too_high"
            diagnosis = "System may be echoing operator too much. Consider providing more independent analysis."
        else:
            status = "healthy"
            diagnosis = "Good balance between system guidance and operator agency."

        return {
            "score": score,
            "status": status,
            "diagnosis": diagnosis,
            "operator_trust": round(self._operator_trust_score, 3),
            "total_suggestions": self._suggestion_count,
            "total_aligned": self._alignment_count,
        }

    def get_adaptation_recommendation(self) -> Dict[str, Any]:
        """
        Recommend how the system should adapt based on coherence history.

        If coherence is low: system should be more conservative, provide more evidence.
        If coherence is high: system can be more assertive.
        """
        health = self.get_coherence_health()

        if health["status"] == "too_low":
            return {
                "recommendation": "increase_evidence",
                "detail": "Provide more supporting evidence with suggestions. "
                          "Operator is overriding frequently — understand why.",
                "assertiveness": 0.3,
            }
        elif health["status"] == "too_high":
            return {
                "recommendation": "increase_independence",
                "detail": "System may be too agreeable. Introduce more diverse perspectives "
                          "and independent analysis.",
                "assertiveness": 0.7,
            }
        else:
            return {
                "recommendation": "maintain",
                "detail": "Coherence is in healthy range. Continue current approach.",
                "assertiveness": 0.5,
            }

    def get_feedback_summary(self, last_n: int = 10) -> Dict[str, Any]:
        """Get summary of recent feedback events."""
        recent = self._feedback_history[-last_n:]
        return {
            "operator_id": self.operator_id,
            "coherence_score": self._coherence_score,
            "coherence_health": self.get_coherence_health(),
            "adaptation": self.get_adaptation_recommendation(),
            "recent_events": [e.to_dict() for e in recent],
            "total_events": len(self._feedback_history),
        }

    def to_dict(self) -> dict:
        return self.get_feedback_summary()
