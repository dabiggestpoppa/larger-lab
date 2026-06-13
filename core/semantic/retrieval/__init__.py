"""
Phase 1.4 — Retrieval + Semantic Memory Layer

Unified retrieval router providing contextual recall, semantic querying,
and live retrieval over the cognition substrate's vector memory.

Components:
- rtrvr: Live Retrieval Engine — real-time semantic search
- shiji: Semantic Recall Engine — associative memory + multi-hop retrieval
- context: Context Assembler — merge, deduplicate, budget, attribute

Usage:
    from core.semantic.retrieval import RetrievalRouter

    router = RetrievalRouter(embedding_engine, vector_store)
    results = router.retrieve("query", mode="both", limit=5)
"""

from .rtrvr import RTRVR, RetrievalResult
from .shiji import SHIJI, RecallResult, MemoryLink
from .context import ContextAssembler, AssembledContext

__all__ = [
    "RTRVR",
    "RetrievalResult",
    "SHIJI",
    "RecallResult",
    "MemoryLink",
    "ContextAssembler",
    "AssembledContext",
]


class RetrievalRouter:
    """
    Unified entry point for all retrieval operations.

    Routes queries to RTRVR (live search), SHIJI (associative recall),
    or both, with query-level caching for frequent lookups.
    """

    def __init__(self, embedding_engine, vector_store, cache_size: int = 256):
        self.rtrvr = RTRVR(embedding_engine, vector_store)
        self.shiji = SHIJI(embedding_engine, vector_store)
        self.context_assembler = ContextAssembler()
        self._cache: dict[str, dict] = {}
        self._cache_size = cache_size
        self._cache_order: list[str] = []

    def retrieve(
        self,
        query: str,
        mode: str = "both",
        limit: int = 10,
        threshold: float = 0.0,
        filters: dict | None = None,
        max_hops: int = 3,
        token_budget: int = 4096,
    ) -> dict:
        """
        Unified retrieval entry point.

        Args:
            query: Search query string.
            mode: "rtrvr" | "shiji" | "both"
            limit: Max results per engine.
            threshold: Minimum relevance score.
            filters: Optional metadata filters for RTRVR.
            max_hops: Max hops for SHIJI multi-hop retrieval.
            token_budget: Max tokens for assembled context.

        Returns:
            Dict with keys: "rtrvr_results", "shiji_results", "context"
        """
        # Check cache
        cache_key = f"{query}:{mode}:{limit}:{threshold}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        result: dict = {"rtrvr_results": [], "shiji_results": [], "context": None}

        if mode in ("rtrvr", "both"):
            result["rtrvr_results"] = self.rtrvr.search(
                query, limit=limit, threshold=threshold, filters=filters
            )

        if mode in ("shiji", "both"):
            result["shiji_results"] = self.shiji.recall(
                query, limit=limit, max_hops=max_hops
            )

        # Assemble context from all results
        all_results = result["rtrvr_results"] + result["shiji_results"]
        if all_results:
            result["context"] = self.context_assembler.assemble(
                all_results, token_budget=token_budget
            )

        # Update cache (LRU eviction)
        self._cache[cache_key] = result
        self._cache_order.append(cache_key)
        if len(self._cache_order) > self._cache_size:
            evicted = self._cache_order.pop(0)
            self._cache.pop(evicted, None)

        return result

    def clear_cache(self) -> None:
        """Clear the query cache."""
        self._cache.clear()
        self._cache_order.clear()
