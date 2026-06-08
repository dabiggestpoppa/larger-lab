"""5_continuity.long_term_memory

Long-term memory storage and retrieval with importance scoring and decay.
"""

import logging
import time
from collections import OrderedDict
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.ltm")


class MemoryEntry(BaseModel):
    memory_id: str
    content: str
    importance: float = 0.5
    tags: List[str] = Field(default_factory=list)
    created_at: float = 0.0
    last_accessed: float = 0.0
    access_count: int = 0
    current_importance: float = 0.5


class LongTermMemoryConfig(BaseModel):
    enabled: bool = True
    max_memories: int = 100000
    decay_rate: float = 0.001
    importance_threshold: float = 0.1


class LongTermMemoryModule:
    """Long-term memory storage and retrieval with importance decay."""

    def __init__(self):
        self.config = LongTermMemoryConfig()
        self.running = False
        self._memories: OrderedDict[str, MemoryEntry] = OrderedDict()
        self._lock = Lock()
        self._total_stored = 0
        self._total_forgotten = 0
        self._total_recalled = 0

    def start(self) -> None:
        self.running = True
        logger.info("LongTermMemory started (max_memories=%d)", self.config.max_memories)

    def stop(self) -> None:
        self.running = False
        logger.info("LongTermMemory stopped")

    def store(self, memory_id: str, content: str, importance: float = 0.5,
              tags: Optional[List[str]] = None) -> MemoryEntry:
        now = time.time()
        entry = MemoryEntry(
            memory_id=memory_id,
            content=content,
            importance=importance,
            tags=tags or [],
            created_at=now,
            last_accessed=now,
            current_importance=importance,
        )
        with self._lock:
            # Evict lowest importance if at capacity
            if len(self._memories) >= self.config.max_memories and memory_id not in self._memories:
                self._evict_one()
            self._memories[memory_id] = entry
            self._memories.move_to_end(memory_id)
            self._total_stored += 1
        logger.debug("Stored memory %s (importance=%.2f)", memory_id, importance)
        return entry

    def recall(self, query: str = "", n: int = 10,
               min_importance: float = 0.0) -> List[MemoryEntry]:
        now = time.time()
        results = []
        with self._lock:
            for entry in reversed(self._memories.values()):
                # Apply decay
                age_hours = (now - entry.created_at) / 3600
                decayed = entry.importance * (1 - self.config.decay_rate) ** age_hours
                entry.current_importance = max(0.0, decayed)

                if entry.current_importance < min_importance:
                    continue

                # Match: query in content or tags
                if query.lower() in entry.content.lower() or any(query.lower() in t.lower() for t in entry.tags):
                    entry.last_accessed = now
                    entry.access_count += 1
                    results.append(entry)
                    if len(results) >= n:
                        break

            self._total_recalled += 1

        results.sort(key=lambda e: e.current_importance, reverse=True)
        logger.debug("Recall '%s': %d results", query, len(results))
        return results

    def forget(self, memory_id: str) -> bool:
        with self._lock:
            if memory_id in self._memories:
                del self._memories[memory_id]
                self._total_forgotten += 1
                logger.debug("Forgot memory %s", memory_id)
                return True
        return False

    def get_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        with self._lock:
            entry = self._memories.get(memory_id)
            if entry:
                entry.last_accessed = time.time()
                entry.access_count += 1
                self._memories.move_to_end(memory_id)
            return entry

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            if not self._memories:
                return {"total": 0, "total_stored": self._total_stored,
                        "total_forgotten": self._total_forgotten, "total_recalled": self._total_recalled}
            importances = [e.current_importance for e in self._memories.values()]
            return {
                "total": len(self._memories),
                "avg_importance": round(sum(importances) / len(importances), 4),
                "max_importance": round(max(importances), 4),
                "min_importance": round(min(importances), 4),
                "total_stored": self._total_stored,
                "total_forgotten": self._total_forgotten,
                "total_recalled": self._total_recalled,
            }

    def _evict_one(self):
        """Evict the lowest-importance memory."""
        if not self._memories:
            return
        lowest_id = min(self._memories, key=lambda k: self._memories[k].current_importance)
        del self._memories[lowest_id]
        self._total_forgotten += 1
        logger.debug("Evicted memory %s (lowest importance)", lowest_id)
