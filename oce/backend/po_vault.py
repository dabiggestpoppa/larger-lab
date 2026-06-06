"""
PO Vault Retriever — retrieves relevant context from the OCE vault and memory.

Queries structural memory, event fabric, and the observidian vault indexer
to surface context relevant to the current conversation or task.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RetrievalHit:
    """A single retrieval hit from the vault."""

    source: str  # e.g., "structural_memory", "event_fabric", "vault_indexer"
    layer: str  # e.g., "WORK", "LEARNED", "KNOWLEDGE"
    content: str
    score: float = 0.0  # relevance score 0-1
    tags: List[str] = field(default_factory=list)
    timestamp: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalResult:
    """Aggregated retrieval result."""

    timestamp: float
    query: str
    hits: List[RetrievalHit] = field(default_factory=list)
    sources_queried: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    duration_ms: float = 0.0

    def summary(self) -> Dict[str, Any]:
        return {
            "query": self.query[:100],
            "hits": len(self.hits),
            "sources": self.sources_queried,
            "top_sources": self._top_sources(),
            "errors": len(self.errors),
            "duration_ms": round(self.duration_ms, 1),
        }

    def _top_sources(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for hit in self.hits:
            counts[hit.source] = counts.get(hit.source, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: -x[1])[:5])

    def top_hits(self, n: int = 5) -> List[RetrievalHit]:
        """Return top n hits by score."""
        return sorted(self.hits, key=lambda h: h.score, reverse=True)[:n]

    def as_context_string(self, max_tokens: int = 2000) -> str:
        """Format hits as a single context string for LLM consumption."""
        chunks = []
        tokens_used = 0
        for hit in self.top_hits(20):
            chunk = f"[{hit.source}/{hit.layer}] {hit.content}"
            chunk_tokens = len(chunk.split())
            if tokens_used + chunk_tokens > max_tokens:
                break
            chunks.append(chunk)
            tokens_used += chunk_tokens
        return "\n\n".join(chunks) if chunks else "(no relevant context found)"


class VaultRetriever:
    """Retrieves relevant context from OCE's memory and vault subsystems."""

    def __init__(
        self,
        max_hits: int = 20,
        min_score: float = 0.1,
        sources: List[str] | None = None,
    ):
        self.max_hits = max_hits
        self.min_score = min_score
        self.sources = sources or ["structural_memory", "event_fabric", "vault_indexer"]

    def retrieve(self, query: str, session_id: str = "") -> RetrievalResult:
        """Retrieve relevant context for a query."""
        start = time.monotonic()
        result = RetrievalResult(
            timestamp=time.time(),
            query=query,
        )

        # Query structural memory
        if "structural_memory" in self.sources:
            try:
                hits = self._query_structural_memory(query)
                result.hits.extend(hits)
                result.sources_queried.append("structural_memory")
            except Exception as e:
                result.errors.append(f"structural_memory: {e}")

        # Query event fabric
        if "event_fabric" in self.sources:
            try:
                hits = self._query_event_fabric(query)
                result.hits.extend(hits)
                result.sources_queried.append("event_fabric")
            except Exception as e:
                result.errors.append(f"event_fabric: {e}")

        # Query vault indexer (Obsidian vault)
        if "vault_indexer" in self.sources:
            try:
                hits = self._query_vault_indexer(query)
                result.hits.extend(hits)
                result.sources_queried.append("vault_indexer")
            except Exception as e:
                result.errors.append(f"vault_indexer: {e}")

        # Deduplicate and score
        result.hits = self._deduplicate_and_score(result.hits, query)
        result.hits = sorted(result.hits, key=lambda h: h.score, reverse=True)[:self.max_hits]

        result.duration_ms = (time.monotonic() - start) * 1000
        return result

    def _query_structural_memory(self, query: str) -> List[RetrievalHit]:
        """Query OCE structural memory."""
        hits: List[RetrievalHit] = []
        try:
            from core.structural_memory import StructuralMemory, MemoryLayer
            sm = StructuralMemory()
            entries = sm.search(query=query, limit=self.max_hits)
            for e in entries:
                hits.append(RetrievalHit(
                    source="structural_memory",
                    layer=e.layer.value,
                    content=str(e.content),
                    score=0.5,  # Base score; refined by dedup
                    tags=e.tags,
                    timestamp=e.created_at.isoformat() if e.created_at else "",
                ))
        except ImportError:
            pass
        return hits

    def _query_event_fabric(self, query: str) -> List[RetrievalHit]:
        """Query OCE event fabric for recent relevant events."""
        hits: List[RetrievalHit] = []
        try:
            from core.event_fabric import get_fabric
            fabric = get_fabric()
            events = fabric.get_history(limit=self.max_hits)
            for e in events:
                payload_str = str(e.payload)
                if query.lower() in payload_str.lower() or any(
                    kw in payload_str.lower() for kw in query.lower().split()
                ):
                    hits.append(RetrievalHit(
                        source="event_fabric",
                        layer="EVENT",
                        content=payload_str[:500],
                        score=0.4,
                        tags=[e.event_type],
                        timestamp=e.timestamp.isoformat() if hasattr(e.timestamp, 'isoformat') else str(e.timestamp),
                    ))
        except ImportError:
            pass
        return hits

    def _query_vault_indexer(self, query: str) -> List[RetrievalHit]:
        """Query the Obsidian vault indexer."""
        hits: List[RetrievalHit] = []
        try:
            from core.vault_indexer import VaultIndexer
            indexer = VaultIndexer()
            results = indexer.search(query, limit=self.max_hits)
            for r in results:
                hits.append(RetrievalHit(
                    source="vault_indexer",
                    layer="VAULT",
                    content=r.get("content", "")[:500],
                    score=r.get("score", 0.3),
                    tags=r.get("tags", []),
                    timestamp=r.get("timestamp", ""),
                    metadata=r.get("metadata", {}),
                ))
        except ImportError:
            pass
        return hits

    def _deduplicate_and_score(self, hits: List[RetrievalHit], query: str) -> List[RetrievalHit]:
        """Deduplicate hits by content similarity and boost relevance scores."""
        seen: Dict[str, RetrievalHit] = {}
        query_words = set(query.lower().split())

        for hit in hits:
            # Content fingerprint for dedup
            content_lower = hit.content.lower().strip()[:200]
            if content_lower in seen:
                # Merge: keep higher score
                if hit.score > seen[content_lower].score:
                    seen[content_lower] = hit
                continue

            # Boost score based on query term overlap
            content_words = set(content_lower.split())
            overlap = query_words & content_words
            if overlap:
                hit.score += 0.1 * min(len(overlap), 3)

            seen[content_lower] = hit

        return [h for h in seen.values() if h.score >= self.min_score]