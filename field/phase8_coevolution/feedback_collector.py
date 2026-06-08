"""8_coevolution.feedback_collector

Collects feedback from operators about field performance.
Tracks ratings, comments, and categories for continuous improvement.

Feedback categories:
- accuracy: correctness of field outputs
- speed: responsiveness and latency
- relevance: usefulness of information
- usability: ease of interaction
"""

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.coevolution.feedback_collector")

VALID_CATEGORIES = ("accuracy", "speed", "relevance", "usability")


class FeedbackEntry(BaseModel):
    """A single feedback entry."""
    feedback_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    operator_id: str
    category: str
    rating: float  # 1.0 - 5.0
    comment: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    helpful_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FeedbackCollectorConfig(BaseModel):
    """Configuration for feedback_collector."""
    enabled: bool = True
    max_entries: int = 50000
    min_rating: float = 1.0
    max_rating: float = 5.0
    default_category: str = "usability"


class FeedbackCollectorModule:
    """Collects and manages operator feedback."""

    def __init__(self):
        self.config = FeedbackCollectorConfig()
        self.running = False
        self._lock = Lock()
        self._entries: List[FeedbackEntry] = []
        self._by_operator: Dict[str, List[str]] = defaultdict(list)  # operator_id -> [feedback_ids]
        self._by_category: Dict[str, List[str]] = defaultdict(list)  # category -> [feedback_ids]
        self._id_index: Dict[str, FeedbackEntry] = {}  # feedback_id -> entry

    def start(self) -> None:
        self.running = True
        logger.info("FeedbackCollectorModule started")

    def stop(self) -> None:
        self.running = False
        logger.info("FeedbackCollectorModule stopped with %d entries", len(self._entries))

    def submit_feedback(self, operator_id: str, category: str = "usability",
                        rating: float = 3.0, comment: str = "",
                        metadata: Optional[Dict[str, Any]] = None) -> FeedbackEntry:
        """Submit feedback from an operator.

        Args:
            operator_id: Unique operator identifier.
            category: Feedback category (accuracy, speed, relevance, usability).
            rating: Rating from min_rating to max_rating.
            comment: Optional text comment.
            metadata: Optional additional data.

        Returns:
            The created FeedbackEntry.
        """
        if category not in VALID_CATEGORIES:
            category = self.config.default_category

        rating = max(self.config.min_rating, min(self.config.max_rating, rating))

        entry = FeedbackEntry(
            operator_id=operator_id,
            category=category,
            rating=round(rating, 2),
            comment=comment,
            metadata=metadata or {},
        )

        with self._lock:
            self._entries.append(entry)
            self._by_operator[operator_id].append(entry.feedback_id)
            self._by_category[category].append(entry.feedback_id)
            self._id_index[entry.feedback_id] = entry

            # Trim if over limit
            if len(self._entries) > self.config.max_entries:
                removed = self._entries[:len(self._entries) - self.config.max_entries]
                self._entries = self._entries[-self.config.max_entries:]
                for r in removed:
                    self._id_index.pop(r.feedback_id, None)
                    self._by_operator[r.operator_id] = [
                        fid for fid in self._by_operator[r.operator_id] if fid != r.feedback_id
                    ]
                    self._by_category[r.category] = [
                        fid for fid in self._by_category[r.category] if fid != r.feedback_id
                    ]

        logger.info("Feedback submitted: %s rated %.1f in %s", operator_id, rating, category)
        return entry

    def get_feedback(self, category: Optional[str] = None,
                     operator_id: Optional[str] = None,
                     min_rating: float = 0.0, limit: int = 100) -> List[Dict]:
        """Get feedback entries, optionally filtered.

        Args:
            category: Filter by category.
            operator_id: Filter by operator.
            min_rating: Minimum rating threshold.
            limit: Max entries to return.

        Returns:
            List of feedback entry dicts, most recent first.
        """
        with self._lock:
            if operator_id:
                ids = set(self._by_operator.get(operator_id, []))
                entries = [self._id_index[fid] for fid in ids if fid in self._id_index]
            elif category:
                ids = set(self._by_category.get(category, []))
                entries = [self._id_index[fid] for fid in ids if fid in self._id_index]
            else:
                entries = list(self._entries)

            entries = [e for e in entries if e.rating >= min_rating]
            entries.sort(key=lambda e: e.timestamp, reverse=True)
            return [e.model_dump() for e in entries[:limit]]

    def get_average_rating(self, category: Optional[str] = None) -> Dict[str, float]:
        """Get average rating, optionally filtered by category.

        Returns:
            Dict with average, count, min, max per category or overall.
        """
        with self._lock:
            if category:
                ids = self._by_category.get(category, [])
                ratings = [self._id_index[fid].rating for fid in ids if fid in self._id_index]
                if not ratings:
                    return {"average": 0.0, "count": 0, "min": 0.0, "max": 0.0}
                return {
                    "average": round(sum(ratings) / len(ratings), 3),
                    "count": len(ratings),
                    "min": round(min(ratings), 2),
                    "max": round(max(ratings), 2),
                }
            else:
                result = {}
                for cat in VALID_CATEGORIES:
                    result[cat] = self.get_average_rating(cat)
                return result

    def get_feedback_summary(self) -> Dict[str, Any]:
        """Get a summary of all feedback."""
        with self._lock:
            total = len(self._entries)
            by_category = {}
            for cat in VALID_CATEGORIES:
                by_category[cat] = self.get_average_rating(cat)

            all_ratings = [e.rating for e in self._entries]
            overall_avg = round(sum(all_ratings) / len(all_ratings), 3) if all_ratings else 0.0

            return {
                "total_entries": total,
                "overall_average_rating": overall_avg,
                "by_category": by_category,
                "unique_operators": len(self._by_operator),
                "category_distribution": {
                    cat: len(self._by_category.get(cat, [])) for cat in VALID_CATEGORIES
                },
            }

    def mark_helpful(self, feedback_id: str) -> bool:
        """Mark a feedback entry as helpful.

        Args:
            feedback_id: The feedback entry ID.

        Returns:
            True if found and updated, False otherwise.
        """
        with self._lock:
            entry = self._id_index.get(feedback_id)
            if entry:
                entry.helpful_count += 1
                return True
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get module statistics."""
        return self.get_feedback_summary()
