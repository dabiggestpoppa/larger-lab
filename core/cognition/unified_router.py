"""
Phase 1.7 — Unified Cognition Router

Unifies all Phase 1 components into one cognition field:
- Ingestion (OpenAlex, parsers)
- Memory (semantic, vector, graph)
- Retrieval (RTRVR, SHIJI)
- Synthesis (Sisyphus)
- Procedural cognition (skills, workflows)

This is the single entry point for all cognition operations.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.cognition_router")


class CognitionRouter:
    """
    Unified cognition routing hub.
    
    Routes operations to the appropriate subsystem:
    - ingest: Store new knowledge
    - recall: Retrieve existing knowledge
    - synthesize: Multi-source reasoning
    - execute: Procedural cognition
    
    Usage:
        router = CognitionRouter(
            embedding_engine=embedder,
            vector_store=vector_store,
            graph_store=graph_store,
        )
        
        # Ingest a research paper
        result = await router.ingest(query="semantic memory agents", source="openalex")
        
        # Retrieve relevant knowledge
        results = router.recall("How does semantic memory work?", limit=5)
        
        # Synthesize across sources
        synthesis = router.synthesize(
            query="Compare semantic memory approaches",
            sources=["doc1", "doc2", "doc3"],
        )
    """

    def __init__(
        self,
        embedding_engine=None,
        vector_store=None,
        graph_store=None,
        chunker=None,
        openalex_client=None,
        sisyphus_engine=None,
    ):
        self.embedding_engine = embedding_engine
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.chunker = chunker
        self.openalex_client = openalex_client
        self.sisyphus_engine = sisyphus_engine

        # Initialize sub-engines if not provided
        self._init_sub_engines()

    def _init_sub_engines(self):
        """Lazily initialize sub-engines from available components."""
        # RTRVR (Live Retrieval)
        if self.embedding_engine and self.vector_store:
            try:
                from core.semantic.retrieval.rtrvr import RTRVR
                self.rtrvr = RTRVR(
                    embedding_engine=self.embedding_engine,
                    vector_store=self.vector_store,
                )
            except ImportError:
                self.rtrvr = None
        else:
            self.rtrvr = None

        # SHIJI (Semantic Recall)
        if self.embedding_engine and self.vector_store:
            try:
                from core.semantic.retrieval.shiji import SHIJI
                self.shiji = SHIJI(
                    embedding_engine=self.embedding_engine,
                    vector_store=self.vector_store,
                    graph_store=self.graph_store,
                )
            except ImportError:
                self.shiji = None
        else:
            self.shiji = None

        # Sisyphus (Synthesis)
        if self.embedding_engine:
            try:
                from core.research.synthesis.sisyphus import SisyphusEngine
                self.sisyphus = SisyphusEngine(
                    embedding_engine=self.embedding_engine,
                    chunker=self.chunker,
                )
            except ImportError:
                self.sisyphus = None
        else:
            self.sisyphus = None

        # OpenAlex Ingester
        if self.openalex_client:
            try:
                from core.research.ingestion.openalex import OpenAlexIngester
                self.openalex_ingester = OpenAlexIngester(
                    client=self.openalex_client,
                    chunker=self.chunker,
                    embedder=self.embedding_engine,
                    graph_store=self.graph_store,
                    vector_store=self.vector_store,
                )
            except ImportError:
                self.openalex_ingester = None
        else:
            self.openalex_ingester = None

    # ─── Public API ───────────────────────────────────────────────────────

    def recall(
        self,
        query: str,
        limit: int = 10,
        mode: str = "both",  # "rtrvr", "shiji", "both"
    ) -> Dict[str, Any]:
        """
        Retrieve knowledge by meaning.
        
        Args:
            query: Natural language query
            limit: Max results per mode
            mode: Which retrieval engine to use
            
        Returns:
            Dict with "rtrvr_results", "shiji_results", "merged"
        """
        results = {"query": query, "rtrvr_results": [], "shiji_results": [], "merged": []}

        if mode in ("rtrvr", "both") and self.rtrvr:
            try:
                results["rtrvr_results"] = self.rtrvr.retrieve(query, limit=limit)
            except Exception as e:
                logger.error(f"RTRVR recall failed: {e}")

        if mode in ("shiji", "both") and self.shiji:
            try:
                results["shiji_results"] = self.shiji.recall(query, limit=limit)
            except Exception as e:
                logger.error(f"SHIJI recall failed: {e}")

        # Merge and deduplicate
        all_results = results["rtrvr_results"] + results["shiji_results"]
        seen_texts = set()
        merged = []
        for r in all_results:
            text_key = r.text[:100] if hasattr(r, 'text') else str(r)[:100]
            if text_key not in seen_texts:
                seen_texts.add(text_key)
                merged.append(r)
        results["merged"] = merged[:limit]

        return results

    def synthesize(
        self,
        query: str,
        sources: Optional[List[Any]] = None,
    ) -> Any:
        """
        Multi-source research synthesis.
        
        If no sources provided, recalls from memory first.
        """
        if not self.sisyphus:
            logger.warning("Sisyphus engine not available")
            return None

        # If no sources, recall from memory
        if not sources:
            recall_results = self.recall(query, limit=10)
            sources = recall_results.get("merged", [])

        if not sources:
            logger.warning("No sources available for synthesis")
            return None

        return self.sisyphus.synthesize(query=query, sources=sources)

    async def ingest_openalex(
        self,
        query: str,
        limit: int = 25,
    ) -> List[Any]:
        """Ingest research from OpenAlex."""
        if not self.openalex_ingester:
            logger.warning("OpenAlex ingester not available")
            return []
        return await self.openalex_ingester.ingest_query(query, limit=limit)

    def get_status(self) -> Dict[str, Any]:
        """Get status of all cognition subsystems."""
        return {
            "embedding_engine": self.embedding_engine is not None,
            "vector_store": self.vector_store is not None,
            "graph_store": self.graph_store is not None,
            "chunker": self.chunker is not None,
            "rtrvr": self.rtrvr is not None,
            "shiji": self.shiji is not None,
            "sisyphus": self.sisyphus is not None,
            "openalex": self.openalex_ingester is not None,
        }