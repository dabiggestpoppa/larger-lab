"""5_continuity.pattern_librarian

Pattern Librarian — Pattern storage and matching.

Stores and matches patterns observed in field behavior.
Uses Jaccard similarity for set-based patterns and cosine-like
similarity for vector-based patterns.

Status: IMPLEMENTED
"""
import logging
import math
import time
from collections import defaultdict
from threading import Lock
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field

logger = logging.getLogger("field.pattern_librarian")


class PatternMatch(BaseModel):
    pattern_id: str
    similarity: float
    context: Dict[str, Any] = Field(default_factory=dict)
    matched_at: str = ""


class Pattern(BaseModel):
    pattern_id: str
    pattern_data: Any
    context: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = 0.0
    last_matched: float = 0.0
    match_count: int = 0


class PatternLibrarianConfig(BaseModel):
    """Configuration for pattern_librarian."""
    enabled: bool = True
    max_patterns: int = 10000
    match_threshold: float = 0.7
    pattern_ttl_sec: float = 86400.0  # 24 hours


class PatternLibrarianModule:
    """Pattern storage and matching field module."""

    def __init__(self):
        self.config = PatternLibrarianConfig()
        self.running = False
        self._lock = Lock()
        self._patterns: Dict[str, Pattern] = {}
        self._total_matches = 0
        self._total_attempts = 0
        self._hit_rate = 0.0
        self._type_index: Dict[str, Set[str]] = defaultdict(set)

    def start(self) -> None:
        """Start the module."""
        self.running = True
        logger.info("PatternLibrarian started (max_patterns=%d, threshold=%.2f)",
                     self.config.max_patterns, self.config.match_threshold)

    def stop(self) -> None:
        """Stop the module."""
        self.running = False
        logger.info("PatternLibrarian stopped (stored=%d, matches=%d)",
                     len(self._patterns), self._total_matches)

    def record_pattern(self, pattern_id: str, pattern_data: Any,
                       context: Optional[Dict[str, Any]] = None) -> str:
        """Store a new pattern.

        Args:
            pattern_id: Unique pattern identifier.
            pattern_data: The pattern data (set, list, dict, or numeric vector).
            context: Optional context metadata.

        Returns:
            The pattern_id.
        """
        with self._lock:
            now = time.time()
            p = Pattern(
                pattern_id=pattern_id,
                pattern_data=pattern_data,
                context=context or {},
                created_at=now,
            )
            self._patterns[pattern_id] = p

            # Index by type
            type_key = type(pattern_data).__name__
            self._type_index[type_key].add(pattern_id)

            # Evict oldest if over capacity
            if len(self._patterns) > self.config.max_patterns:
                oldest_id = min(self._patterns, key=lambda k: self._patterns[k].created_at)
                self._remove_pattern(oldest_id)
                logger.debug("Evicted oldest pattern: %s", oldest_id)

            logger.debug("Recorded pattern: %s (total=%d)", pattern_id, len(self._patterns))
            return pattern_id

    def _remove_pattern(self, pattern_id: str):
        if pattern_id in self._patterns:
            p = self._patterns.pop(pattern_id)
            type_key = type(p.pattern_data).__name__
            self._type_index[type_key].discard(pattern_id)

    def match_pattern(self, data: Any, threshold: Optional[float] = None) -> List[PatternMatch]:
        """Find patterns matching the given data.

        Args:
            data: Data to match against stored patterns.
            threshold: Minimum similarity (default from config).

        Returns:
            List of PatternMatch results sorted by similarity descending.
        """
        threshold = threshold or self.config.match_threshold
        matches = []
        now = time.time()

        with self._lock:
            # Expire old patterns
            expired = [pid for pid, p in self._patterns.items()
                       if now - p.created_at > self.config.pattern_ttl_sec]
            for pid in expired:
                self._remove_pattern(pid)
            if expired:
                logger.debug("Expired %d patterns", len(expired))

            self._total_attempts += 1

            for pid, pattern in self._patterns.items():
                sim = self._compute_similarity(data, pattern.pattern_data)
                if sim >= threshold:
                    match = PatternMatch(
                        pattern_id=pid,
                        similarity=round(sim, 4),
                        context=pattern.context,
                        matched_at=now,
                    )
                    matches.append(match)
                    pattern.last_matched = now
                    pattern.match_count += 1
                    self._total_matches += 1

            # Update hit rate
            if self._total_attempts > 0:
                self._hit_rate = self._total_matches / self._total_attempts

        matches.sort(key=lambda m: m.similarity, reverse=True)
        logger.debug("Pattern match: %d matches above %.2f", len(matches), threshold)
        return matches

    def _compute_similarity(self, a: Any, b: Any) -> float:
        """Compute similarity between two data items.

        Supports: sets (Jaccard), lists/tuples of numbers (cosine-like),
        dicts (key overlap), scalars (normalized diff).
        """
        if type(a) != type(b):
            return 0.0

        if isinstance(a, set):
            return self._jaccard_similarity(a, b)
        elif isinstance(a, (list, tuple)) and len(a) > 0 and isinstance(a[0], (int, float)):
            return self._cosine_similarity(a, b)
        elif isinstance(a, dict):
            return self._dict_overlap(a, b)
        elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return self._scalar_similarity(a, b)
        else:
            return 1.0 if a == b else 0.0

    @staticmethod
    def _jaccard_similarity(a: set, b: set) -> float:
        if not a and not b:
            return 1.0
        intersection = len(a & b)
        union = len(a | b)
        return intersection / union if union > 0 else 0.0

    @staticmethod
    def _cosine_similarity(a, b) -> float:
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x * x for x in a))
        mag_b = math.sqrt(sum(x * x for x in b))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)

    @staticmethod
    def _dict_overlap(a: dict, b: dict) -> float:
        if not a and not b:
            return 1.0
        keys_a = set(a.keys())
        keys_b = set(b.keys())
        common = len(keys_a & keys_b)
        total = len(keys_a | keys_b)
        if total == 0:
            return 1.0
        # Also check value agreement for common keys
        value_agreement = sum(1 for k in keys_a & keys_b if a[k] == b[k]) / common if common else 0
        return (common / total) * 0.5 + value_agreement * 0.5

    @staticmethod
    def _scalar_similarity(a: float, b: float) -> float:
        if a == b:
            return 1.0
        max_val = max(abs(a), abs(b), 1e-10)
        return 1.0 - abs(a - b) / max_val

    def get_pattern(self, pattern_id: str) -> Optional[Pattern]:
        """Get a specific pattern by ID."""
        with self._lock:
            return self._patterns.get(pattern_id)

    def get_all_patterns(self) -> List[Pattern]:
        """Get all stored patterns."""
        with self._lock:
            return list(self._patterns.values())

    def get_pattern_stats(self) -> Dict[str, Any]:
        """Get pattern library statistics."""
        with self._lock:
            now = time.time()
            expired_count = sum(1 for p in self._patterns.values()
                                if now - p.created_at > self.config.pattern_ttl_sec)
            type_counts = {k: len(v) for k, v in self._type_index.items()}
            return {
                "total_patterns": len(self._patterns),
                "expired_patterns": expired_count,
                "total_matches": self._total_matches,
                "total_attempts": self._total_attempts,
                "hit_rate": round(self._hit_rate, 4),
                "by_type": type_counts,
                "avg_match_count": (
                    sum(p.match_count for p in self._patterns.values()) / len(self._patterns)
                    if self._patterns else 0.0
                ),
            }
