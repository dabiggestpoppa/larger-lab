"""
8_coevolution.suggestion_engine
=================================
Intelligent suggestion engine for field operations.

Generates contextual suggestions for operators based on:
- Current field state and active modules
- Operator profiles and expertise areas
- Historical feedback patterns
- Coevolution tracking data

Suggestion types:
- optimization: performance/efficiency improvements
- safety: risk mitigation recommendations
- exploration: new capabilities to try
- workflow: process improvements
"""

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.coevolution.suggestion_engine")


class Suggestion(BaseModel):
    """A single suggestion."""
    suggestion_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    suggestion_type: str  # optimization, safety, exploration, workflow
    title: str
    description: str
    priority: float = 0.5  # 0.0 to 1.0
    confidence: float = 0.5  # how confident the engine is
    source: str = ""  # what triggered this suggestion
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    accepted: Optional[bool] = None
    helpful_rating: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SuggestionEngineConfig(BaseModel):
    """Configuration for suggestion_engine."""
    enabled: bool = True
    max_suggestions: int = 5000
    min_confidence: float = 0.3
    max_active_suggestions: int = 50
    cooldown_seconds: int = 60  # min time between similar suggestions
    priority_threshold: float = 0.4


class SuggestionEngineModule:
    """Generates contextual suggestions for field operations."""

    def __init__(self):
        self.config = SuggestionEngineConfig()
        self.running = False
        self._lock = Lock()
        self._suggestions: List[Suggestion] = []
        self._active: Dict[str, Suggestion] = {}  # suggestion_id -> suggestion
        self._by_type: Dict[str, List[str]] = defaultdict(list)
        self._suppressed: Dict[str, str] = {}  # source_key -> last_suggestion_time
        self._stats: Dict[str, int] = defaultdict(int)

    def start(self) -> None:
        self.running = True
        logger.info("SuggestionEngine started")

    def stop(self) -> None:
        self.running = False
        logger.info("SuggestionEngine stopped with %d total suggestions", len(self._suggestions))

    def generate_suggestion(self, suggestion_type: str, title: str,
                            description: str, priority: float = 0.5,
                            confidence: float = 0.5, source: str = "",
                            metadata: Optional[Dict[str, Any]] = None) -> Optional[Suggestion]:
        """
        Generate a new suggestion.

        Args:
            suggestion_type: Type of suggestion (optimization, safety, exploration, workflow).
            title: Short suggestion title.
            description: Detailed description.
            priority: Priority 0.0-1.0.
            confidence: Confidence 0.0-1.0.
            source: What triggered this suggestion.
            metadata: Additional data.

        Returns:
            The created Suggestion, or None if suppressed by cooldown/filter.
        """
        if not self.running:
            return None

        confidence = max(0.0, min(1.0, confidence))
        priority = max(0.0, min(1.0, priority))

        # Filter low confidence
        if confidence < self.config.min_confidence:
            logger.debug("Suggestion filtered (low confidence %.2f < %.2f): %s",
                         confidence, self.config.min_confidence, title)
            return None

        # Cooldown check
        now = datetime.now(timezone.utc)
        source_key = f"{suggestion_type}:{source}"
        with self._lock:
            if source_key in self._suppressed:
                last_time = datetime.fromisoformat(self._suppressed[source_key])
                elapsed = (now - last_time).total_seconds()
                if elapsed < self.config.cooldown_seconds:
                    logger.debug("Suggestion cooldown active for %s (%.0fs remaining)",
                                 source_key, self.config.cooldown_seconds - elapsed)
                    return None

            # Check active limit
            if len(self._active) >= self.config.max_active_suggestions:
                # Remove lowest priority active suggestion
                lowest_id = min(self._active, key=lambda sid: self._active[sid].priority)
                removed = self._active.pop(lowest_id)
                logger.debug("Evicted low-priority suggestion: %s", removed.title)

            suggestion = Suggestion(
                suggestion_type=suggestion_type,
                title=title,
                description=description,
                priority=round(priority, 4),
                confidence=round(confidence, 4),
                source=source,
                metadata=metadata or {},
            )

            self._suggestions.append(suggestion)
            self._active[suggestion.suggestion_id] = suggestion
            self._by_type[suggestion_type].append(suggestion.suggestion_id)
            self._suppressed[source_key] = now.isoformat()
            self._stats["generated"] += 1
            self._stats[f"type_{suggestion_type}"] += 1

            # Trim total
            if len(self._suggestions) > self.config.max_suggestions:
                self._suggestions = self._suggestions[-self.config.max_suggestions:]

        logger.info("Suggestion generated: [%s] %s (priority=%.2f, confidence=%.2f)",
                     suggestion_type, title, priority, confidence)
        return suggestion

    def accept_suggestion(self, suggestion_id: str) -> bool:
        """Mark a suggestion as accepted."""
        with self._lock:
            s = self._active.get(suggestion_id)
            if s:
                s.accepted = True
                self._stats["accepted"] += 1
                logger.info("Suggestion accepted: %s", s.title)
                return True
            # Check historical
            for s in self._suggestions:
                if s.suggestion_id == suggestion_id:
                    s.accepted = True
                    self._stats["accepted"] += 1
                    return True
        return False

    def reject_suggestion(self, suggestion_id: str) -> bool:
        """Mark a suggestion as rejected."""
        with self._lock:
            s = self._active.get(suggestion_id)
            if s:
                s.accepted = False
                self._active.pop(suggestion_id, None)
                self._stats["rejected"] += 1
                logger.info("Suggestion rejected: %s", s.title)
                return True
        return False

    def rate_suggestion(self, suggestion_id: str, helpful: float) -> bool:
        """Rate how helpful a suggestion was (0.0-1.0)."""
        with self._lock:
            for s in self._suggestions:
                if s.suggestion_id == suggestion_id:
                    s.helpful_rating = max(0.0, min(1.0, helpful))
                    self._stats["rated"] += 1
                    return True
        return False

    def get_active(self, suggestion_type: Optional[str] = None,
                   min_priority: Optional[float] = None) -> List[Dict]:
        """Get active (pending) suggestions."""
        with self._lock:
            results = list(self._active.values())
            if suggestion_type:
                results = [s for s in results if s.suggestion_type == suggestion_type]
            if min_priority is not None:
                results = [s for s in results if s.priority >= min_priority]
            results.sort(key=lambda s: s.priority, reverse=True)
            return [s.model_dump() for s in results]

    def get_history(self, suggestion_type: Optional[str] = None,
                    limit: int = 100) -> List[Dict]:
        """Get suggestion history."""
        with self._lock:
            results = list(reversed(self._suggestions))
            if suggestion_type:
                results = [s for s in results if s.suggestion_type == suggestion_type]
            return [s.model_dump() for s in results[:limit]]

    def get_stats(self) -> Dict[str, Any]:
        """Get suggestion engine statistics."""
        with self._lock:
            rated = [s for s in self._suggestions if s.helpful_rating is not None]
            avg_helpful = (
                round(sum(s.helpful_rating for s in rated) / len(rated), 3)
                if rated else 0.0
            )
            return {
                "total_generated": self._stats["generated"],
                "total_accepted": self._stats.get("accepted", 0),
                "total_rejected": self._stats.get("rejected", 0),
                "total_rated": self._stats.get("rated", 0),
                "active_count": len(self._active),
                "average_helpfulness": avg_helpful,
                "acceptance_rate": (
                    round(self._stats.get("accepted", 0) / self._stats["generated"], 3)
                    if self._stats["generated"] > 0 else 0.0
                ),
                "by_type": {
                    t: len(ids) for t, ids in self._by_type.items()
                },
            }
