"""
O-4-B8: PatternMemory
======================
Stores stable knowledge extracted from operational patterns.

Maintains a persistent memory of:
- Stable workflow patterns
- Effective routing decisions
- Context templates per task domain
- Failure patterns to avoid
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("core.learning.pattern_memory")


@dataclass
class StoredPattern:
    """A stable pattern stored in memory."""
    pattern_id: str
    name: str
    category: str  # "workflow", "routing", "context", "failure"
    content: dict[str, Any]
    confidence: float  # 0.0 to 1.0
    usage_count: int
    created_at: str
    updated_at: str
    source_traces: int = 0


class PatternMemory:
    """Persistent memory for stable operational patterns."""

    def __init__(self, storage_path: str | None = None):
        self._patterns: dict[str, StoredPattern] = {}
        self._storage_path = Path(storage_path) if storage_path else None

    @property
    def patterns(self) -> list[StoredPattern]:
        return list(self._patterns.values())

    def store(self, pattern: StoredPattern) -> None:
        """Store or update a pattern."""
        existing = self._patterns.get(pattern.pattern_id)
        if existing:
            # Update existing pattern
            existing.content = pattern.content
            existing.confidence = max(existing.confidence, pattern.confidence)
            existing.usage_count += 1
            existing.updated_at = datetime.now(timezone.utc).isoformat()
            existing.source_traces = pattern.source_traces
        else:
            self._patterns[pattern.pattern_id] = pattern
        logger.debug(f"Stored pattern: {pattern.pattern_id} ({pattern.category})")

    def recall(self, pattern_id: str) -> StoredPattern | None:
        """Recall a pattern by ID."""
        return self._patterns.get(pattern_id)

    def search(self, category: str | None = None, min_confidence: float = 0.0) -> list[StoredPattern]:
        """Search patterns by category and confidence."""
        results = []
        for p in self._patterns.values():
            if category and p.category != category:
                continue
            if p.confidence < min_confidence:
                continue
            results.append(p)
        return sorted(results, key=lambda p: p.confidence * p.usage_count, reverse=True)

    def get_routing_knowledge(self, task_domain: str) -> dict[str, Any]:
        """Get accumulated routing knowledge for a task domain."""
        routing_patterns = self.search(category="routing")
        relevant = [p for p in routing_patterns if task_domain in p.name]
        if not relevant:
            return {}
        # Return the highest-confidence routing knowledge
        best = max(relevant, key=lambda p: p.confidence)
        return best.content

    def get_context_template(self, task_domain: str) -> dict[str, Any]:
        """Get the best context template for a task domain."""
        context_patterns = self.search(category="context")
        relevant = [p for p in context_patterns if task_domain in p.name]
        if not relevant:
            return {}
        best = max(relevant, key=lambda p: p.confidence)
        return best.content

    def get_failure_patterns(self, task_domain: str | None = None) -> list[StoredPattern]:
        """Get known failure patterns to avoid."""
        failures = self.search(category="failure")
        if task_domain:
            failures = [f for f in failures if task_domain in f.name]
        return failures

    def consolidate(self) -> int:
        """Consolidate patterns — merge similar, prune weak. Returns count pruned."""
        to_remove = []
        for pid, pattern in self._patterns.items():
            # Prune patterns with very low confidence and low usage
            if pattern.confidence < 0.2 and pattern.usage_count < 2:
                to_remove.append(pid)
            # Decay confidence for unused patterns
            elif pattern.usage_count == 0:
                pattern.confidence *= 0.9

        for pid in to_remove:
            del self._patterns[pid]

        if to_remove:
            logger.info(f"Consolidated: pruned {len(to_remove)} weak patterns")
        return len(to_remove)

    def get_stats(self) -> dict[str, Any]:
        """Get memory statistics."""
        categories = {}
        for p in self._patterns.values():
            categories[p.category] = categories.get(p.category, 0) + 1
        return {
            "total_patterns": len(self._patterns),
            "categories": categories,
            "avg_confidence": (
                sum(p.confidence for p in self._patterns.values()) / len(self._patterns)
                if self._patterns else 0
            ),
            "total_usage": sum(p.usage_count for p in self._patterns.values()),
        }

    def save(self) -> None:
        """Persist memory to disk."""
        if not self._storage_path:
            return
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "patterns": {
                pid: {
                    "pattern_id": p.pattern_id,
                    "name": p.name,
                    "category": p.category,
                    "content": p.content,
                    "confidence": p.confidence,
                    "usage_count": p.usage_count,
                    "created_at": p.created_at,
                    "updated_at": p.updated_at,
                    "source_traces": p.source_traces,
                }
                for pid, p in self._patterns.items()
            },
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
        self._storage_path.write_text(json.dumps(data, indent=2))
        logger.info(f"Saved {len(self._patterns)} patterns to {self._storage_path}")

    def load(self) -> bool:
        """Load memory from disk."""
        if not self._storage_path or not self._storage_path.exists():
            return False
        try:
            data = json.loads(self._storage_path.read_text())
            for pid, pdata in data.get("patterns", {}).items():
                self._patterns[pid] = StoredPattern(**pdata)
            logger.info(f"Loaded {len(self._patterns)} patterns from {self._storage_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load patterns: {e}")
            return False
