"""
Phase 1.4.1 — RTRVR (Live Retrieval Engine)

Real-time semantic search over vector memory.
Embeds queries, searches the vector store, and returns ranked results
with context windows and metadata filtering.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from core.semantic.embeddings.embedding_engine import EmbeddingEngine


@dataclass
class RetrievalResult:
    """A single retrieval hit with context window and metadata."""
    result_id: str
    chunk_id: str
    text: str
    score: float
    source: str = ""
    metadata: dict = field(default_factory=dict)
    context_before: str = ""  # preceding text for context window
    context_after: str = ""   # following text for context window
    timestamp: float = field(default_factory=time.time)

    @property
    def context_window(self) -> str:
        """Full context window: before + text + after."""
        parts = []
        if self.context_before:
            parts.append(self.context_before)
        parts.append(self.text)
        if self.context_after:
            parts.append(self.context_after)
        return "\n".join(parts)

    @property
    def token_count(self) -> int:
        """Approximate token count of the main text."""
        return len(self.text) // 4


class RTRVR:
    """
    Live Retrieval Engine.

    Performs real-time semantic search:
    1. Embeds the query using EmbeddingEngine
    2. Searches the vector store for nearest neighbors
    3. Filters by metadata and relevance threshold
    4. Assembles context windows around hits
    5. Returns ranked RetrievalResult list
    """

    def __init__(
        self,
        embedding_engine: EmbeddingEngine,
        vector_store: Any,
        default_threshold: float = 0.0,
        default_limit: int = 10,
    ):
        self.embedding_engine = embedding_engine
        self.vector_store = vector_store
        self.default_threshold = default_threshold
        self.default_limit = default_limit

    def search(
        self,
        query: str,
        limit: int | None = None,
        threshold: float | None = None,
        filters: dict | None = None,
        include_context: bool = True,
    ) -> list[RetrievalResult]:
        """
        Execute a semantic search query.

        Args:
            query: Natural language search query.
            limit: Max results to return (default: self.default_limit).
            threshold: Minimum relevance score (default: self.default_threshold).
            filters: Metadata filters, e.g. {"source": "doc_123", "type": "procedure"}.
            include_context: Whether to include surrounding context windows.

        Returns:
            Ranked list of RetrievalResult objects, highest score first.
        """
        if not query.strip():
            return []

        limit = limit or self.default_limit
        threshold = threshold if threshold is not None else self.default_threshold

        # Step 1: Embed the query
        query_embedding = self._embed_query(query)
        if query_embedding is None:
            return []

        # Step 2: Search vector store
        raw_results = self._vector_search(query_embedding, limit, filters)

        # Step 3: Filter by threshold and build RetrievalResult objects
        results: list[RetrievalResult] = []
        for hit in raw_results:
            score = self._extract_score(hit)
            if score < threshold:
                continue

            result = self._build_result(hit, score, include_context)
            results.append(result)

        # Step 4: Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)
        return results

    def _embed_query(self, query: str) -> list[float] | None:
        """Embed the query string. Returns None on failure."""
        try:
            return self.embedding_engine.embed(query)
        except Exception:
            return None

    def _vector_search(
        self,
        query_embedding: list[float],
        limit: int,
        filters: dict | None,
    ) -> list[dict]:
        """
        Search the vector store.

        Supports multiple vector store backends:
        - Objects with a `search(query_embedding, limit, filters)` method
        - Objects with a `query(query_embedding, top_k)` method
        - Fallback: brute-force cosine similarity over `get_all()` items
        """
        store = self.vector_store

        # Try standard search interface
        if hasattr(store, "search"):
            try:
                raw = store.search(
                    query_embedding=query_embedding,
                    limit=limit,
                    filters=filters,
                )
                return self._normalize_raw_results(raw)
            except TypeError:
                # Some stores have different signatures; try without kwargs
                try:
                    raw = store.search(query_embedding, limit)
                    return self._normalize_raw_results(raw)
                except Exception:
                    pass

        # Try query interface (e.g., LlamaIndex-style)
        if hasattr(store, "query"):
            try:
                raw = store.query(query_embedding, top_k=limit)
                return self._normalize_raw_results(raw)
            except Exception:
                pass

        # Fallback: brute-force over all stored items
        if hasattr(store, "get_all"):
            try:
                all_items = store.get_all()
                return self._brute_force_search(query_embedding, all_items, limit)
            except Exception:
                pass

        return []

    def _normalize_raw_results(self, raw: Any) -> list[dict]:
        """Normalize various result formats into list[dict]."""
        if raw is None:
            return []

        # Already a list
        if isinstance(raw, list):
            return [_to_dict(item) for item in raw]

        # Single item
        return [_to_dict(raw)]

    def _brute_force_search(
        self,
        query_embedding: list[float],
        items: list[dict],
        limit: int,
    ) -> list[dict]:
        """Brute-force cosine similarity search over items with embeddings."""
        scored: list[tuple[float, dict]] = []
        for item in items:
            item_emb = item.get("embedding") or item.get("vector")
            if item_emb is None:
                continue
            score = _cosine_similarity(query_embedding, item_emb)
            scored.append((score, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, item in scored[:limit]:
            item_copy = dict(item)
            item_copy["_score"] = score
            results.append(item_copy)
        return results

    def _extract_score(self, hit: dict) -> float:
        """Extract relevance score from a hit dict."""
        for key in ("score", "_score", "relevance", "similarity", "distance"):
            if key in hit:
                val = hit[key]
                # Convert distance to similarity if needed
                if key == "distance":
                    return 1.0 - float(val)
                return float(val)
        return 0.0

    def _build_result(self, hit: dict, score: float, include_context: bool) -> RetrievalResult:
        """Build a RetrievalResult from a raw hit dict."""
        text = hit.get("text") or hit.get("content") or hit.get("document") or ""
        chunk_id = hit.get("chunk_id") or hit.get("id") or hit.get("node_id") or str(uuid.uuid4())
        source = hit.get("source") or hit.get("source_object_id") or hit.get("file_path", "")
        metadata = hit.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = {}

        context_before = hit.get("context_before") or hit.get("overlap_prev", "")
        context_after = hit.get("context_after") or hit.get("overlap_next", "")

        if include_context and not (context_before or context_after):
            # Try to extract from surrounding chunks if available
            context_before = hit.get("preceding_text", "")
            context_after = hit.get("following_text", "")

        return RetrievalResult(
            result_id=str(uuid.uuid4()),
            chunk_id=str(chunk_id),
            text=text,
            score=score,
            source=str(source),
            metadata=metadata,
            context_before=str(context_before),
            context_after=str(context_after),
        )


def _to_dict(item: Any) -> dict:
    """Convert an item to a dict, handling various types."""
    if isinstance(item, dict):
        return item
    if hasattr(item, "__dict__"):
        return dict(item.__dict__)
    if hasattr(item, "to_dict"):
        return item.to_dict()
    return {"text": str(item), "_raw": item}


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
