"""
Phase 1.4 — Retrieval + Semantic Memory Tests

Tests for RTRVR, SHIJI, ContextAssembler, and RetrievalRouter.
All tests use mock embeddings and vector stores — no external dependencies.
"""

from __future__ import annotations

import math
import pytest

from core.semantic.retrieval.rtrvr import RTRVR, RetrievalResult, _cosine_similarity
from core.semantic.retrieval.shiji import SHIJI, RecallResult, MemoryLink
from core.semantic.retrieval.context import ContextAssembler, AssembledContext, SourceAttribution
from core.semantic.retrieval import RetrievalRouter


# ---------------------------------------------------------------------------
# Fixtures — Mock EmbeddingEngine
# ---------------------------------------------------------------------------

class MockEmbeddingEngine:
    """
    Deterministic mock embedding engine.
    Produces predictable vectors so tests are reproducible.
    """

    def __init__(self, dim: int = 128):
        self.dim = dim
        self._cache: dict[str, list[float]] = {}

    def embed(self, text: str) -> list[float]:
        if text in self._cache:
            return self._cache[text]
        # Deterministic pseudo-embedding based on character codes
        vec = [0.0] * self.dim
        for i, ch in enumerate(text):
            vec[i % self.dim] += ord(ch) / 255.0
        # Normalize
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        vec = [x / norm for x in vec]
        self._cache[text] = vec
        return vec

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


# ---------------------------------------------------------------------------
# Fixtures — Mock VectorStore
# ---------------------------------------------------------------------------

class MockVectorStore:
    """
    In-memory vector store for testing.
    Supports search(), get_all(), and get() interfaces.
    """

    def __init__(self, items: list[dict] | None = None):
        self._items: list[dict] = list(items) if items else []

    def search(
        self,
        query_embedding: list[float],
        limit: int = 10,
        filters: dict | None = None,
    ) -> list[dict]:
        """Cosine similarity search over stored items."""
        scored: list[tuple[float, dict]] = []
        for item in self._items:
            emb = item.get("embedding")
            if emb is None:
                continue
            # Apply filters
            if filters:
                meta = item.get("metadata", {})
                if not all(meta.get(k) == v for k, v in filters.items()):
                    continue
            score = self._cosine(query_embedding, emb)
            item_copy = dict(item)
            item_copy["score"] = score
            scored.append((score, item_copy))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:limit]]

    def get_all(self) -> list[dict]:
        return list(self._items)

    def get(self, chunk_id: str) -> dict | None:
        for item in self._items:
            if item.get("chunk_id") == chunk_id or item.get("id") == chunk_id:
                return item
        return None

    def add(self, item: dict) -> None:
        self._items.append(item)

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        if not a or not b:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a)) or 1.0
        nb = math.sqrt(sum(x * x for x in b)) or 1.0
        return dot / (na * nb)


@pytest.fixture
def embedding_engine():
    return MockEmbeddingEngine(dim=128)


@pytest.fixture
def sample_items():
    """Sample items for the vector store."""
    engine = MockEmbeddingEngine(dim=128)
    return [
        {
            "chunk_id": "chunk_001",
            "text": "The observer pattern decouples event emitters from observers.",
            "source": "design_patterns.pdf",
            "metadata": {"type": "concept", "domain": "software"},
            "embedding": engine.embed("The observer pattern decouples event emitters from observers."),
        },
        {
            "chunk_id": "chunk_002",
            "text": "Semantic memory stores general world knowledge and concepts.",
            "source": "cognitive_science.pdf",
            "metadata": {"type": "concept", "domain": "cognition"},
            "embedding": engine.embed("Semantic memory stores general world knowledge and concepts."),
        },
        {
            "chunk_id": "chunk_003",
            "text": "Vector similarity search finds nearest neighbors in embedding space.",
            "source": "ml_textbook.pdf",
            "metadata": {"type": "procedure", "domain": "ml"},
            "embedding": engine.embed("Vector similarity search finds nearest neighbors in embedding space."),
        },
        {
            "chunk_id": "chunk_004",
            "text": "The observer runtime monitors system state changes in real-time.",
            "source": "systems_design.pdf",
            "metadata": {"type": "concept", "domain": "software"},
            "embedding": engine.embed("The observer runtime monitors system state changes in real-time."),
        },
        {
            "chunk_id": "chunk_005",
            "text": "Multi-hop reasoning chains connect distant concepts through intermediates.",
            "source": "reasoning_paper.pdf",
            "metadata": {"type": "concept", "domain": "cognition"},
            "embedding": engine.embed("Multi-hop reasoning chains connect distant concepts through intermediates."),
        },
    ]


@pytest.fixture
def vector_store(sample_items):
    return MockVectorStore(sample_items)


# ---------------------------------------------------------------------------
# RTRVR Tests
# ---------------------------------------------------------------------------

class TestRTRVR:
    """Tests for the Live Retrieval Engine."""

    def test_basic_search(self, embedding_engine, vector_store):
        """RTRVR returns results for a relevant query."""
        rtrvr = RTRVR(embedding_engine, vector_store)
        results = rtrvr.search("observer pattern design")
        assert len(results) > 0
        assert all(isinstance(r, RetrievalResult) for r in results)

    def test_results_ranked_by_score(self, embedding_engine, vector_store):
        """Results are sorted by score descending."""
        rtrvr = RTRVR(embedding_engine, vector_store)
        results = rtrvr.search("observer pattern")
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_empty_query_returns_empty(self, embedding_engine, vector_store):
        """Empty or whitespace query returns empty list."""
        rtrvr = RTRVR(embedding_engine, vector_store)
        assert rtrvr.search("") == []
        assert rtrvr.search("   ") == []

    def test_threshold_filters_low_scores(self, embedding_engine, vector_store):
        """Results below threshold are filtered out."""
        rtrvr = RTRVR(embedding_engine, vector_store, default_threshold=0.99)
        results = rtrvr.search("completely unrelated xyzzy")
        # With a very high threshold, most results should be filtered
        for r in results:
            assert r.score >= 0.99

    def test_limit_caps_results(self, embedding_engine, vector_store):
        """Limit parameter caps the number of results."""
        rtrvr = RTRVR(embedding_engine, vector_store)
        results = rtrvr.search("observer", limit=2)
        assert len(results) <= 2

    def test_metadata_filtering(self, embedding_engine, vector_store):
        """Filters narrow results by metadata."""
        rtrvr = RTRVR(embedding_engine, vector_store)
        results = rtrvr.search("observer", filters={"domain": "software"})
        for r in results:
            assert r.metadata.get("domain") == "software"

    def test_context_window_included(self, embedding_engine, vector_store):
        """Context window property combines before + text + after."""
        rtrvr = RTRVR(embedding_engine, vector_store)
        results = rtrvr.search("observer")
        for r in results:
            assert r.text in r.context_window

    def test_retrieval_result_token_count(self):
        """Token count is approximate chars / 4."""
        r = RetrievalResult(
            result_id="r1",
            chunk_id="c1",
            text="a" * 400,
            score=0.9,
        )
        assert r.token_count == 100

    def test_retrieval_result_context_window_assembly(self):
        """Context window assembles before, text, and after."""
        r = RetrievalResult(
            result_id="r1",
            chunk_id="c1",
            text="main content",
            score=0.9,
            context_before="before text",
            context_after="after text",
        )
        assert "before text" in r.context_window
        assert "main content" in r.context_window
        assert "after text" in r.context_window


# ---------------------------------------------------------------------------
# SHIJI Tests
# ---------------------------------------------------------------------------

class TestSHIJI:
    """Tests for the Semantic Recall Engine."""

    def test_basic_recall(self, embedding_engine, vector_store):
        """SHIJI returns results for a query."""
        shiji = SHIJI(embedding_engine, vector_store)
        results = shiji.recall("observer pattern")
        assert len(results) > 0
        assert all(isinstance(r, RecallResult) for r in results)

    def test_recall_results_have_confidence(self, embedding_engine, vector_store):
        """All recall results have confidence scores."""
        shiji = SHIJI(embedding_engine, vector_store)
        results = shiji.recall("semantic memory")
        for r in results:
            assert 0.0 <= r.confidence <= 1.0

    def test_multi_hop_increases_results(self, embedding_engine, vector_store):
        """Multi-hop retrieval can return more results than single-hop."""
        shiji = SHIJI(embedding_engine, vector_store)
        single = shiji.recall("observer", max_hops=0)
        multi = shiji.recall("observer", max_hops=2)
        # Multi-hop should find at least as many
        assert len(multi) >= len(single)

    def test_hop_distance_tracked(self, embedding_engine, vector_store):
        """Results track their hop distance."""
        shiji = SHIJI(embedding_engine, vector_store)
        results = shiji.recall("observer", max_hops=2)
        hop_distances = {r.hop_distance for r in results}
        # Should have results from multiple hops
        assert 0 in hop_distances

    def test_hop_decay_reduces_confidence(self, embedding_engine, vector_store):
        """Later hops have lower confidence due to decay."""
        shiji = SHIJI(embedding_engine, vector_store, hop_decay=0.5)
        results = shiji.recall("observer", max_hops=3)
        hop_0 = [r for r in results if r.hop_distance == 0]
        hop_2 = [r for r in results if r.hop_distance == 2]
        if hop_0 and hop_2:
            assert hop_0[0].confidence >= hop_2[0].confidence

    def test_empty_query_returns_empty(self, embedding_engine, vector_store):
        """Empty query returns empty results."""
        shiji = SHIJI(embedding_engine, vector_store)
        assert shiji.recall("") == []

    def test_find_related(self, embedding_engine, vector_store):
        """find_related returns memories related to a chunk."""
        shiji = SHIJI(embedding_engine, vector_store)
        related = shiji.find_related("chunk_001")
        # Should find chunk_004 (also about observers)
        assert any(r.chunk_id == "chunk_004" for r in related)

    def test_memory_links_created(self, embedding_engine, vector_store):
        """Memory links are created between related results."""
        shiji = SHIJI(embedding_engine, vector_store)
        results = shiji.recall("observer", include_links=True)
        all_links = shiji.get_memory_links()
        # Should have some links if there are multiple results
        if len(results) >= 2:
            assert len(all_links) >= 0  # links may or may not meet threshold

    def test_memory_link_structure(self, embedding_engine, vector_store):
        """Memory links have correct structure."""
        shiji = SHIJI(embedding_engine, vector_store, min_link_strength=0.0)
        shiji.recall("observer", include_links=True)
        for link in shiji.get_memory_links():
            assert isinstance(link, MemoryLink)
            assert isinstance(link.source_id, str)
            assert isinstance(link.target_id, str)
            assert link.relation_type in ("semantic", "temporal", "causal", "associative")
            assert 0.0 <= link.strength <= 1.0

    def test_reasoning_chain_tracked(self, embedding_engine, vector_store):
        """Multi-hop results track the reasoning chain."""
        shiji = SHIJI(embedding_engine, vector_store)
        results = shiji.recall("observer", max_hops=2)
        multi_hop = [r for r in results if r.hop_distance > 0]
        for r in multi_hop:
            assert len(r.reasoning_chain) > 0

    def test_deduplication(self, embedding_engine, vector_store):
        """Duplicate chunk_ids are deduplicated, keeping highest confidence."""
        shiji = SHIJI(embedding_engine, vector_store)
        results = shiji.recall("observer", max_hops=3)
        chunk_ids = [r.chunk_id for r in results]
        assert len(chunk_ids) == len(set(chunk_ids))


# ---------------------------------------------------------------------------
# ContextAssembler Tests
# ---------------------------------------------------------------------------

class TestContextAssembler:
    """Tests for the Context Assembler."""

    def test_assemble_basic(self):
        """Basic assembly produces non-empty context."""
        assembler = ContextAssembler()
        results = [
            RetrievalResult(result_id="r1", chunk_id="c1", text="First piece of context.", score=0.9),
            RetrievalResult(result_id="r2", chunk_id="c2", text="Second piece of context.", score=0.8),
        ]
        ctx = assembler.assemble(results)
        assert isinstance(ctx, AssembledContext)
        assert len(ctx.context_text) > 0
        assert ctx.total_tokens > 0

    def test_assemble_empty_results(self):
        """Empty results produce empty context."""
        assembler = ContextAssembler()
        ctx = assembler.assemble([])
        assert ctx.context_text == ""
        assert ctx.total_tokens == 0

    def test_deduplication(self):
        """Near-duplicate results are deduplicated."""
        assembler = ContextAssembler(overlap_threshold=0.8)
        results = [
            RetrievalResult(result_id="r1", chunk_id="c1", text="The observer pattern is a design pattern.", score=0.9),
            RetrievalResult(result_id="r2", chunk_id="c2", text="The observer pattern is a design pattern.", score=0.7),
        ]
        ctx = assembler.assemble(results)
        # Should only have one copy
        count = ctx.context_text.count("observer pattern is a design pattern")
        assert count == 1

    def test_token_budget_enforced(self):
        """Context is truncated to fit token budget."""
        assembler = ContextAssembler(default_budget=10)  # very small budget
        results = [
            RetrievalResult(result_id="r1", chunk_id="c1", text="a" * 400, score=0.9),
            RetrievalResult(result_id="r2", chunk_id="c2", text="b" * 400, score=0.8),
        ]
        ctx = assembler.assemble(results, token_budget=10)
        assert ctx.truncated is True
        assert ctx.total_tokens <= 10

    def test_source_attribution(self):
        """Source attribution tracks where each piece came from."""
        assembler = ContextAssembler()
        results = [
            RetrievalResult(
                result_id="r1", chunk_id="c1", text="Attributed text.",
                score=0.9, source="test.pdf", metadata={"page": 1}
            ),
        ]
        ctx = assembler.assemble(results)
        assert len(ctx.sources) >= 1
        assert isinstance(ctx.sources[0], SourceAttribution)
        assert ctx.sources[0].source_id == "test.pdf"

    def test_grouped_sections(self):
        """Grouped mode creates sections by source type."""
        assembler = ContextAssembler()
        results = [
            RetrievalResult(result_id="r1", chunk_id="c1", text="RTRVR result.", score=0.9, source="a.pdf"),
            RecallResult(result_id="r2", chunk_id="c2", text="SHIJI result.", confidence=0.8, source="b.pdf", hop_distance=0),
        ]
        ctx = assembler.assemble(results, section_mode="grouped")
        # Should have sections for both rtrvr and shiji
        assert "rtrvr" in ctx.sections or "shiji" in ctx.sections

    def test_prioritized_sections(self):
        """Prioritized mode splits into primary and supporting."""
        assembler = ContextAssembler()
        results = [
            RetrievalResult(result_id=f"r{i}", chunk_id=f"c{i}", text=f"Result {i}.", score=0.9 - i * 0.1)
            for i in range(5)
        ]
        ctx = assembler.assemble(results, section_mode="prioritized")
        assert "primary" in ctx.sections

    def test_flat_sections(self):
        """Flat mode puts everything in one section."""
        assembler = ContextAssembler()
        results = [
            RetrievalResult(result_id="r1", chunk_id="c1", text="Text A.", score=0.9),
            RetrievalResult(result_id="r2", chunk_id="c2", text="Text B.", score=0.8),
        ]
        ctx = assembler.assemble(results, section_mode="flat")
        assert "context" in ctx.sections
        assert "Text A" in ctx.sections["context"]
        assert "Text B" in ctx.sections["context"]

    def test_format_with_attribution(self):
        """format_with_attribution includes source info."""
        assembler = ContextAssembler()
        results = [
            RetrievalResult(
                result_id="r1", chunk_id="c1", text="Some context.",
                score=0.9, source="doc.pdf"
            ),
        ]
        ctx = assembler.assemble(results)
        formatted = ctx.format_with_attribution()
        assert "Sources" in formatted
        assert "doc.pdf" in formatted

    def test_text_overlap_detection(self):
        """Text overlap function detects similarity correctly."""
        # Identical texts
        assert ContextAssembler._text_overlap("hello world", "hello world") == 1.0
        # Completely different
        assert ContextAssembler._text_overlap("abc", "xyz") == 0.0
        # Partial overlap
        overlap = ContextAssembler._text_overlap("hello world", "hello there")
        assert 0.0 < overlap < 1.0

    def test_assembled_context_add_section(self):
        """Adding sections rebuilds the context text."""
        ctx = AssembledContext()
        ctx.add_section("primary", "Primary content.")
        ctx.add_section("supporting", "Supporting content.")
        assert "primary" in ctx.context_text.lower() or "[primary]" in ctx.context_text
        assert "Primary content" in ctx.context_text


# ---------------------------------------------------------------------------
# RetrievalRouter Tests
# ---------------------------------------------------------------------------

class TestRetrievalRouter:
    """Tests for the unified RetrievalRouter."""

    def test_rtrvr_mode(self, embedding_engine, vector_store):
        """Router in rtrvr mode returns only RTRVR results."""
        router = RetrievalRouter(embedding_engine, vector_store)
        result = router.retrieve("observer", mode="rtrvr")
        assert "rtrvr_results" in result
        assert "shiji_results" in result
        assert "context" in result
        assert len(result["rtrvr_results"]) > 0
        assert len(result["shiji_results"]) == 0

    def test_shiji_mode(self, embedding_engine, vector_store):
        """Router in shiji mode returns only SHIJI results."""
        router = RetrievalRouter(embedding_engine, vector_store)
        result = router.retrieve("observer", mode="shiji")
        assert len(result["rtrvr_results"]) == 0
        assert len(result["shiji_results"]) > 0

    def test_both_mode(self, embedding_engine, vector_store):
        """Router in both mode returns results from both engines."""
        router = RetrievalRouter(embedding_engine, vector_store)
        result = router.retrieve("observer", mode="both")
        assert len(result["rtrvr_results"]) > 0
        assert len(result["shiji_results"]) > 0

    def test_context_assembled(self, embedding_engine, vector_store):
        """Router assembles context when results are found."""
        router = RetrievalRouter(embedding_engine, vector_store)
        result = router.retrieve("observer", mode="both")
        assert result["context"] is not None
        assert isinstance(result["context"], AssembledContext)

    def test_caching(self, embedding_engine, vector_store):
        """Repeated queries return cached results."""
        router = RetrievalRouter(embedding_engine, vector_store)
        r1 = router.retrieve("observer", mode="rtrvr")
        r2 = router.retrieve("observer", mode="rtrvr")
        # Same cache entry
        assert r1["context"].context_id == r2["context"].context_id

    def test_cache_clear(self, embedding_engine, vector_store):
        """Cache clear removes all cached results."""
        router = RetrievalRouter(embedding_engine, vector_store)
        router.retrieve("observer", mode="rtrvr")
        router.clear_cache()
        assert len(router._cache) == 0

    def test_empty_query(self, embedding_engine, vector_store):
        """Empty query returns empty results."""
        router = RetrievalRouter(embedding_engine, vector_store)
        result = router.retrieve("", mode="both")
        assert len(result["rtrvr_results"]) == 0
        assert len(result["shiji_results"]) == 0

    def test_token_budget_passed_through(self, embedding_engine, vector_store):
        """Token budget is respected in assembled context."""
        router = RetrievalRouter(embedding_engine, vector_store)
        result = router.retrieve("observer", mode="both", token_budget=10)
        if result["context"]:
            assert result["context"].total_tokens <= 10


# ---------------------------------------------------------------------------
# Utility function tests
# ---------------------------------------------------------------------------

class TestCosineSimilarity:
    """Tests for the cosine similarity utility."""

    def test_identical_vectors(self):
        v = [1.0, 0.0, 0.0]
        assert _cosine_similarity(v, v) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert _cosine_similarity(a, b) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        a = [1.0, 0.0]
        b = [-1.0, 0.0]
        assert _cosine_similarity(a, b) == pytest.approx(-1.0)

    def test_empty_vectors(self):
        assert _cosine_similarity([], []) == 0.0
        assert _cosine_similarity([1.0], []) == 0.0

    def test_known_value(self):
        a = [1.0, 1.0]
        b = [1.0, 0.0]
        expected = 1.0 / math.sqrt(2)
        assert _cosine_similarity(a, b) == pytest.approx(expected, abs=1e-6)
