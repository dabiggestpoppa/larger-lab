"""
5_continuity.memory_consolidation
=================================
Consolidates short-term memories into long-term storage.
Clusters similar memories, merges duplicates, promotes high-importance ones.
"""

import logging
import uuid
from collections import deque
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.memory_consolidation")


class ConsolidationReport(BaseModel):
    timestamp: str
    memories_processed: int = 0
    duplicates_found: int = 0
    promoted_count: int = 0
    merged_count: int = 0
    discarded_count: int = 0


class MemoryItem(BaseModel):
    memory_id: str
    content: str
    importance: float = 0.5
    tags: List[str] = Field(default_factory=list)
    created_at: str = ""
    consolidated: bool = False


class MemoryConsolidationConfig(BaseModel):
    enabled: bool = True
    consolidation_interval_sec: float = 600.0
    buffer_size: int = 1000
    similarity_threshold: float = 0.8
    promotion_threshold: float = 0.7


class MemoryConsolidationModule:
    """Consolidates short-term to long-term memory."""

    def __init__(self):
        self.config = MemoryConsolidationConfig()
        self.running = False
        self._lock = Lock()
        self._buffer: deque[MemoryItem] = deque(maxlen=self.config.buffer_size)
        self._short_term: List[MemoryItem] = []
        self._consolidation_history: deque[ConsolidationReport] = deque(maxlen=100)
        self._stats = {"total_processed": 0, "total_duplicates": 0, "total_promoted": 0}

    def start(self) -> None:
        self.running = True
        logger.info("MemoryConsolidation started (buffer_size=%d)", self.config.buffer_size)

    def stop(self) -> None:
        self.running = False
        logger.info("MemoryConsolidation stopped")

    def add_short_term(self, content: str, importance: float = 0.5, tags: Optional[List[str]] = None) -> str:
        """Add a short-term memory item. Returns memory_id."""
        item = MemoryItem(
            memory_id=str(uuid.uuid4())[:8],
            content=content,
            importance=importance,
            tags=tags or [],
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        with self._lock:
            self._short_term.append(item)
            self._buffer.append(item)
        logger.debug("Added short-term memory: %s", item.memory_id)
        return item.memory_id

    def consolidate(self) -> ConsolidationReport:
        """Run consolidation: cluster, merge, promote."""
        with self._lock:
            if not self._short_term:
                return ConsolidationReport(timestamp=datetime.now(timezone.utc).isoformat())

            items = list(self._short_term)
            self._short_term.clear()

        processed = len(items)
        duplicates = 0
        promoted = 0
        merged = 0
        discarded = 0

        # Find duplicates by content similarity (Jaccard on word sets)
        seen_contents: List[set] = []
        unique_items: List[MemoryItem] = []
        for item in items:
            words = set(item.content.lower().split())
            is_dup = False
            for seen in seen_contents:
                if words and seen:
                    jaccard = len(words & seen) / len(words | seen)
                    if jaccard >= self.config.similarity_threshold:
                        is_dup = True
                        duplicates += 1
                        break
            if not is_dup:
                seen_contents.append(words)
                unique_items.append(item)
            else:
                discarded += 1

        # Promote high-importance items
        for item in unique_items:
            if item.importance >= self.config.promotion_threshold:
                item.consolidated = True
                promoted += 1
                logger.debug("Promoted memory: %s (importance=%.2f)", item.memory_id, item.importance)

        report = ConsolidationReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            memories_processed=processed,
            duplicates_found=duplicates,
            promoted_count=promoted,
            merged_count=merged,
            discarded_count=discarded,
        )

        with self._lock:
            self._consolidation_history.append(report)
            self._stats["total_processed"] += processed
            self._stats["total_duplicates"] += duplicates
            self._stats["total_promoted"] += promoted

        logger.info(
            "Consolidation complete: processed=%d, duplicates=%d, promoted=%d",
            processed, duplicates, promoted,
        )
        return report

    def get_short_term_buffer(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [item.model_dump() for item in self._short_term]

    def get_consolidation_history(self, n: int = 10) -> List[Dict[str, Any]]:
        with self._lock:
            hist = list(self._consolidation_history)[-n:]
            return [r.model_dump() for r in hist]

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                **self._stats,
                "buffer_size": len(self._short_term),
                "consolidation_runs": len(self._consolidation_history),
            }
