"""
Phase 1.4.2 — SHIJI (Semantic Recall Engine)

Associative memory recall with multi-hop retrieval.
Finds related concepts, assembles context from multiple sources,
ranks by confidence, and links related memories.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from core.semantic.embeddings.embedding_engine import EmbeddingEngine


@dataclass
class MemoryLink:
    """A link between two related memories."""
    source_id: str
    target_id: str
    relation_type: str  # "semantic", "temporal", "causal", "associative"
    strength: float  # 0.0 to 1.0
    metadata: dict = field(default_factory=dict)


@dataclass
class RecallResult:
    """A single recall result from associative memory."""
    result_id: str
    chunk_id: str
    text: str
    confidence: float  # combined relevance + hop decay
    source: str = ""
    metadata: dict = field(default_factory=dict)
    hop_distance: int = 0  # number of hops from original query
    reasoning_chain: list[str] = field(default_factory=list)  # chain of chunk_ids
    linked_memories: list[MemoryLink] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    @property
    def token_count(self) -> int:
        """Approximate token count."""
        return len(self.text) // 4


class SHIJI:
    """
    Semantic Recall Engine.

    Provides associative memory capabilities:
    - Find related concepts via embedding similarity
    - Multi-hop retrieval: A → B → C reasoning chains
    - Context assembly from multiple sources
    - Relevance ranking with confidence scores
    - Memory linking between related memories
    """

    def __init__(
        self,
        embedding_engine: EmbeddingEngine,
        vector_store: Any,
        hop_decay: float = 0.85,
        min_link_strength: float = 0.5,
    ):
        self.embedding_engine = embedding_engine
        self.vector_store = vector_store
        self.hop_decay = hop_decay
        self.min_link_strength = min_link_strength
        self._memory_links: list[MemoryLink] = []

    def recall(
        self,
        query: str,
        limit: int = 10,
        max_hops: int = 3,
        include_links: bool = True,
    ) -> list[RecallResult]:
        """
        Associative memory recall with optional multi-hop retrieval.

        Args:
            query: The concept or text to recall.
            limit: Max results per hop.
            max_hops: Maximum number of reasoning hops.
            include_links: Whether to compute memory links.

        Returns:
            Ranked list of RecallResult objects.
        """
        if not query.strip():
            return []

        all_results: list[RecallResult] = []
        visited_ids: set[str] = set()

        # Hop 0: direct retrieval
        current_query = query
        reasoning_chain: list[str] = []

        for hop in range(max_hops + 1):
            hop_results = self._retrieve_hop(
                current_query, limit, hop, reasoning_chain, visited_ids
            )

            if not hop_results:
                break

            # Mark visited
            for r in hop_results:
                visited_ids.add(r.chunk_id)

            all_results.extend(hop_results)

            # Prepare next hop: use top result's text as new query
            if hop < max_hops and hop_results:
                top = hop_results[0]
                current_query = top.text[:512]  # truncate to avoid query bloat
                reasoning_chain = reasoning_chain + [top.chunk_id]

        # Compute memory links if requested
        if include_links:
            self._compute_links(all_results)

        # Deduplicate by chunk_id, keep highest confidence
        deduped = self._deduplicate(all_results)

        # Sort by confidence descending
        deduped.sort(key=lambda r: r.confidence, reverse=True)
        return deduped

    def find_related(
        self,
        chunk_id: str,
        limit: int = 5,
    ) -> list[RecallResult]:
        """
        Find memories related to a specific chunk.

        Args:
            chunk_id: The chunk to find related memories for.
            limit: Max results.

        Returns:
            List of related RecallResult objects.
        """
        # Find the chunk's text
        chunk_text = self._get_chunk_text(chunk_id)
        if chunk_text is None:
            return []

        return self._retrieve_hop(chunk_text, limit, hop=0, reasoning_chain=[], visited_ids={})

    def get_memory_links(self, chunk_id: str | None = None) -> list[MemoryLink]:
        """
        Get memory links, optionally filtered by chunk_id.

        Args:
            chunk_id: If provided, return only links involving this chunk.

        Returns:
            List of MemoryLink objects.
        """
        if chunk_id is None:
            return list(self._memory_links)
        return [
            link for link in self._memory_links
            if link.source_id == chunk_id or link.target_id == chunk_id
        ]

    def _retrieve_hop(
        self,
        query: str,
        limit: int,
        hop: int,
        reasoning_chain: list[str],
        visited_ids: set[str],
    ) -> list[RecallResult]:
        """Execute a single hop of retrieval."""
        try:
            query_embedding = self.embedding_engine.embed(query)
        except Exception:
            return []

        if query_embedding is None:
            return []

        # Search vector store
        raw_results = self._search_store(query_embedding, limit * 2)  # over-fetch for filtering

        results: list[RecallResult] = []
        for hit in raw_results:
            chunk_id = self._extract_chunk_id(hit)
            if chunk_id in visited_ids:
                continue

            text = self._extract_text(hit)
            if not text.strip():
                continue

            base_score = self._extract_score(hit)
            # Apply hop decay
            confidence = base_score * (self.hop_decay ** hop)

            result = RecallResult(
                result_id=str(uuid.uuid4()),
                chunk_id=chunk_id,
                text=text,
                confidence=confidence,
                source=self._extract_source(hit),
                metadata=self._extract_metadata(hit),
                hop_distance=hop,
                reasoning_chain=list(reasoning_chain),
            )
            results.append(result)

            if len(results) >= limit:
                break

        return results

    def _search_store(
        self,
        query_embedding: list[float],
        limit: int,
    ) -> list[dict]:
        """Search the vector store, trying multiple interfaces."""
        store = self.vector_store

        if hasattr(store, "search"):
            try:
                raw = store.search(query_embedding=query_embedding, limit=limit)
                return _normalize_results(raw)
            except TypeError:
                try:
                    raw = store.search(query_embedding, limit)
                    return _normalize_results(raw)
                except Exception:
                    pass

        if hasattr(store, "query"):
            try:
                raw = store.query(query_embedding, top_k=limit)
                return _normalize_results(raw)
            except Exception:
                pass

        if hasattr(store, "get_all"):
            try:
                all_items = store.get_all()
                return self._brute_force(query_embedding, all_items, limit)
            except Exception:
                pass

        return []

    def _brute_force(
        self,
        query_embedding: list[float],
        items: list[dict],
        limit: int,
    ) -> list[dict]:
        """Brute-force cosine similarity."""
        scored: list[tuple[float, dict]] = []
        for item in items:
            emb = item.get("embedding") or item.get("vector")
            if emb is None:
                continue
            score = _cosine_sim(query_embedding, emb)
            item_copy = dict(item)
            item_copy["_score"] = score
            scored.append((score, item_copy))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:limit]]

    def _compute_links(self, results: list[RecallResult]) -> None:
        """Compute memory links between results based on semantic similarity."""
        for i, r1 in enumerate(results):
            for r2 in results[i + 1:]:
                # Use hop distance and confidence to determine link strength
                strength = min(r1.confidence, r2.confidence)
                if strength < self.min_link_strength:
                    continue

                # Determine relation type
                if r1.source and r1.source == r2.source:
                    relation = "semantic"
                elif abs(r1.hop_distance - r2.hop_distance) <= 1:
                    relation = "associative"
                else:
                    relation = "temporal"

                link = MemoryLink(
                    source_id=r1.chunk_id,
                    target_id=r2.chunk_id,
                    relation_type=relation,
                    strength=strength,
                )
                self._memory_links.append(link)
                r1.linked_memories.append(link)
                r2.linked_memories.append(link)

    def _deduplicate(self, results: list[RecallResult]) -> list[RecallResult]:
        """Deduplicate by chunk_id, keeping highest confidence."""
        best: dict[str, RecallResult] = {}
        for r in results:
            if r.chunk_id not in best or r.confidence > best[r.chunk_id].confidence:
                best[r.chunk_id] = r
        return list(best.values())

    def _get_chunk_text(self, chunk_id: str) -> str | None:
        """Look up a chunk's text by ID."""
        store = self.vector_store
        if hasattr(store, "get"):
            try:
                item = store.get(chunk_id)
                if isinstance(item, dict):
                    return item.get("text") or item.get("content")
            except Exception:
                pass

        if hasattr(store, "get_all"):
            try:
                for item in store.get_all():
                    cid = item.get("chunk_id") or item.get("id")
                    if cid == chunk_id:
                        return item.get("text") or item.get("content")
            except Exception:
                pass

        return None

    @staticmethod
    def _extract_chunk_id(hit: dict) -> str:
        for key in ("chunk_id", "id", "node_id", "result_id"):
            if key in hit:
                return str(hit[key])
        return str(uuid.uuid4())

    @staticmethod
    def _extract_text(hit: dict) -> str:
        for key in ("text", "content", "document", "body"):
            if key in hit:
                return str(hit[key])
        return ""

    @staticmethod
    def _extract_score(hit: dict) -> float:
        for key in ("score", "_score", "relevance", "similarity", "distance"):
            if key in hit:
                val = hit[key]
                if key == "distance":
                    return 1.0 - float(val)
                return float(val)
        return 0.0

    @staticmethod
    def _extract_source(hit: dict) -> str:
        for key in ("source", "source_object_id", "file_path", "origin"):
            if key in hit:
                return str(hit[key])
        return ""

    @staticmethod
    def _extract_metadata(hit: dict) -> dict:
        meta = hit.get("metadata")
        if isinstance(meta, dict):
            return meta
        return {}


def _normalize_results(raw: Any) -> list[dict]:
    """Normalize various result formats into list[dict]."""
    if raw is None:
        return []
    if isinstance(raw, list):
        return [_to_dict(item) for item in raw]
    return [_to_dict(raw)]


def _to_dict(item: Any) -> dict:
    if isinstance(item, dict):
        return item
    if hasattr(item, "__dict__"):
        return dict(item.__dict__)
    if hasattr(item, "to_dict"):
        return item.to_dict()
    return {"text": str(item), "_raw": item}


def _cosine_sim(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
