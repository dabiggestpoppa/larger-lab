"""
DSPy Event Classification Pipeline — OCE Phase 2
=================================================
Auto-classifies incoming events by type and priority.

Uses DSPy to learn from operator feedback and event patterns.
Falls back to rule-based classification when DSPy is not installed.

Task: OCE-2.24
"""

import logging
from typing import Any, Dict, List, Optional

from event_fabric import classify_event, EVENT_TYPES

logger = logging.getLogger("oce.dspy.event_classifier")

try:
    import dspy
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False
    dspy = None


# ─── Heuristic Classifier ─────────────────────────────────────────────────────

class EventClassifierHeuristic:
    """Rule-based event classification (no DSPy required)."""

    # Keyword-based classification for unknown event types
    KEYWORD_RULES = {
        "observer.": ["observer", "patch", "collar", "state"],
        "attractor.": ["attractor", "goal", "convergence", "divergence"],
        "entropy.": ["entropy", "budget", "cost", "consumption"],
        "repair.": ["repair", "fix", "recover", "heal"],
        "chat.": ["chat", "message", "user", "assistant"],
        "system.": ["system", "startup", "shutdown", "error"],
        "operator.": ["operator", "command", "process", "file"],
    }

    PRIORITY_RULES = {
        3: ["critical", "exhausted", "failed", "divergence", "error"],
        2: ["warning", "threshold", "triggered", "update", "created", "destroyed"],
        1: ["change", "completed", "signal", "executed"],
        0: ["received", "responded", "modified", "heartbeat"],
    }

    @classmethod
    def classify(cls, event_type: str, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        """Classify an event type using keyword matching."""
        # First check the known event types registry
        known = classify_event(event_type)
        if event_type in EVENT_TYPES:
            return {
                "event_type": event_type,
                "priority": known["priority"],
                "category": event_type.split(".")[0],
                "confidence": 1.0,
                "method": "registry",
            }

        # Try keyword matching for unknown types
        event_lower = event_type.lower()
        payload_str = str(payload).lower() if payload else ""

        best_category = "unknown"
        best_score = 0
        for category, keywords in cls.KEYWORD_RULES.items():
            score = sum(1 for kw in keywords if kw in event_lower or kw in payload_str)
            if score > best_score:
                best_score = score
                best_category = category.rstrip(".")

        # Determine priority from keywords
        priority = 1  # Default NORMAL
        for p, keywords in cls.PRIORITY_RULES.items():
            if any(kw in event_lower or kw in payload_str for kw in keywords):
                priority = p
                break

        return {
            "event_type": event_type,
            "priority": priority,
            "category": best_category,
            "confidence": min(1.0, best_score * 0.3),
            "method": "heuristic",
        }


# ─── DSPy Classifier ──────────────────────────────────────────────────────────

if DSPY_AVAILABLE:
    class EventClassificationSignature(dspy.Signature):
        """Classify an event by type and priority from its content."""
        event_type = dspy.InputField(desc="Event type string (e.g., 'observer.state_change')")
        payload_summary = dspy.InputField(desc="Event payload summary")
        source = dspy.InputField(desc="Event source subsystem")

        category = dspy.OutputField(desc="Event category: observer/attractor/entropy/repair/chat/system/operator")
        priority = dspy.OutputField(desc="Priority level: 0=low, 1=normal, 2=high, 3=critical")
        confidence = dspy.OutputField(desc="Classification confidence (0.0-1.0)")


    class DSPyEventClassifier(dspy.Module):
        """DSPy module for event classification."""

        def __init__(self):
            self.classify = dspy.ChainOfThought(EventClassificationSignature)

        def forward(self, event_type: str, payload: Dict[str, Any], source: str) -> Dict[str, Any]:
            result = self.classify(
                event_type=event_type,
                payload_summary=str(payload)[:200],
                source=source,
            )
            return {
                "event_type": event_type,
                "category": result.category,
                "priority": int(result.priority),
                "confidence": float(result.confidence),
                "method": "dspy",
            }


# ─── Pipeline ─────────────────────────────────────────────────────────────────

class EventClassificationPipeline:
    """
    Event classification pipeline.
    Uses DSPy when available, falls back to heuristics.
    """

    def __init__(self, lm: Optional[Any] = None):
        self._dspy_available = DSPY_AVAILABLE
        self._heuristic = EventClassifierHeuristic()
        self._classifier = None
        if self._dspy_available:
            try:
                self._classifier = DSPyEventClassifier()
                if lm:
                    dspy.configure(lm=lm)
            except Exception as e:
                logger.warning(f"DSPy classifier init failed: {e}")
                self._dspy_available = False

    def classify(self, event_type: str, payload: Dict[str, Any] = None, source: str = "unknown") -> Dict[str, Any]:
        """Classify an event."""
        if self._dspy_available and self._classifier:
            try:
                return self._classifier(event_type, payload or {}, source)
            except Exception as e:
                logger.warning(f"DSPy classification failed: {e}")
        return self._heuristic.classify(event_type, payload)

    def get_status(self) -> Dict[str, Any]:
        return {
            "dspy_available": self._dspy_available,
            "method": "dspy" if self._dspy_available else "heuristic",
            "registered_types": len(EVENT_TYPES),
        }
