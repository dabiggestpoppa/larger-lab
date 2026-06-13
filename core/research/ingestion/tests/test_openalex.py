"""
Tests for Phase 1.1 — OpenAlex Stabilization
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from core.research.ingestion.openalex import (
    OpenAlexClient,
    OpenAlexConcept,
    OpenAlexIngester,
    OpenAlexNormalizer,
    OpenAlexWork,
    RateLimiter,
)


class TestRateLimiter:
    """Test rate limiter."""

    @pytest.mark.asyncio
    async def test_rate_limiter_delays(self):
        limiter = RateLimiter(max_per_second=10)
        import asyncio
        start = asyncio.get_event_loop().time()
        await limiter.acquire()
        await limiter.acquire()
        elapsed = asyncio.get_event_loop().time() - start
        # Two calls at 10/s should take at least 0.1s
        assert elapsed >= 0.05  # allow some tolerance


class TestOpenAlexNormalizer:
    """Test OpenAlex response normalization."""

    def test_normalize_complete_work(self):
        raw = {
            "id": "https://openalex.org/W123456789",
            "doi": "https://doi.org/10.1038/s41586-021-03819-2",
            "title": "Test Paper Title",
            "abstract_inverted_index": {"Test": [0], "abstract": [1]},
            "authorships": [
                {
                    "author": {
                        "id": "https://openalex.org/A123",
                        "display_name": "John Doe",
                        "orcid": "0000-0000-0000-0001",
                    },
                    "institutions": [{"display_name": "MIT"}],
                }
            ],
            "concepts": [
                {"id": "https://openalex.org/C1", "display_name": "Machine Learning", "level": 0, "score": 0.95, "wikidata": "http://www.wikidata.org/entity/Q2539"},
            ],
            "publication_date": "2024-01-15",
            "cited_by_count": 42,
            "referenced_works": ["https://openalex.org/W987654321"],
            "open_access": {"oa_url": "https://arxiv.org/pdf/2401.00001"},
        }

        work = OpenAlexNormalizer.normalize_work(raw)

        assert work.work_id == "W123456789"
        assert work.doi == "10.1038/s41586-021-03819-2"
        assert work.title == "Test Paper Title"
        assert len(work.authors) == 1
        assert work.authors[0].display_name == "John Doe"
        assert work.authors[0].orcid == "0000-0000-0000-0001"
        assert len(work.concepts) == 1
        assert work.concepts[0].display_name == "Machine Learning"
        assert work.concepts[0].score == 0.95
        assert work.cited_by_count == 42
        assert work.open_access_url == "https://arxiv.org/pdf/2401.00001"

    def test_normalize_minimal_work(self):
        """Test normalization with minimal data."""
        raw = {
            "id": "https://openalex.org/W999",
            "title": "Minimal Paper",
        }

        work = OpenAlexNormalizer.normalize_work(raw)

        assert work.work_id == "W999"
        assert work.title == "Minimal Paper"
        assert work.doi is None
        assert work.authors == []
        assert work.concepts == []

    def test_semantic_tags(self):
        """Test semantic tag generation."""
        work = OpenAlexWork(
            work_id="W1",
            title="Test",
            concepts=[
                OpenAlexConcept(concept_id="C1", display_name="AI", score=0.9),
                OpenAlexConcept(concept_id="C2", display_name="ML", score=0.2),
            ],
        )

        tags = work.semantic_tags
        assert "AI" in tags
        assert "ML" not in tags  # score < 0.3

    def test_canonical_id(self):
        """Test canonical ID prefers DOI."""
        work_with_doi = OpenAlexWork(work_id="W1", doi="10.1000/test")
        assert work_with_doi.canonical_id == "10.1000/test"

        work_without_doi = OpenAlexWork(work_id="W2")
        assert work_without_doi.canonical_id == "W2"

    def test_reconstruct_abstract(self):
        """Test abstract reconstruction from inverted index."""
        inverted = {"This": [0], "is": [1], "a": [2], "test": [3]}
        abstract = OpenAlexNormalizer._reconstruct_abstract(inverted)
        assert "This" in abstract
        assert "test" in abstract

    def test_reconstruct_abstract_empty(self):
        """Test abstract reconstruction with empty input."""
        assert OpenAlexNormalizer._reconstruct_abstract(None) == ""
        assert OpenAlexNormalizer._reconstruct_abstract({}) == ""


class TestOpenAlexClient:
    """Test OpenAlex API client."""

    @pytest.mark.asyncio
    async def test_search_works(self):
        mock_response = {
            "results": [
                {"id": "W1", "title": "Paper 1"},
                {"id": "W2", "title": "Paper 2"},
            ]
        }

        client = OpenAlexClient()
        with patch.object(client, "_request", new_callable=AsyncMock, return_value=mock_response):
            results = await client.search_works("test query", limit=10)
            assert len(results) == 2
            assert results[0]["title"] == "Paper 1"

    @pytest.mark.asyncio
    async def test_get_work_by_doi(self):
        mock_response = {"id": "W1", "title": "Test Paper"}

        client = OpenAlexClient()
        with patch.object(client, "_request", new_callable=AsyncMock, return_value=mock_response):
            result = await client.get_work_by_doi("10.1000/test")
            assert result["title"] == "Test Paper"

    @pytest.mark.asyncio
    async def test_get_work_by_doi_failure(self):
        client = OpenAlexClient()
        with patch.object(client, "_request", new_callable=AsyncMock, side_effect=Exception("Not found")):
            result = await client.get_work_by_doi("10.1000/nonexistent")
            assert result is None


class TestOpenAlexIngester:
    """Test OpenAlex ingestion pipeline."""

    @pytest.mark.asyncio
    async def test_ingest_query(self):
        mock_raw = [
            {"id": "W1", "title": "Paper 1"},
            {"id": "W2", "title": "Paper 2"},
        ]

        client = OpenAlexClient()
        with patch.object(client, "search_works", new_callable=AsyncMock, return_value=mock_raw):
            ingester = OpenAlexIngester(client=client)
            works = await ingester.ingest_query("test", limit=10)
            assert len(works) == 2

    @pytest.mark.asyncio
    async def test_deduplication(self):
        mock_raw = [
            {"id": "W1", "doi": "10.1000/same", "title": "Paper 1"},
            {"id": "W2", "doi": "10.1000/same", "title": "Paper 1 Duplicate"},
        ]

        client = OpenAlexClient()
        with patch.object(client, "search_works", new_callable=AsyncMock, return_value=mock_raw):
            ingester = OpenAlexIngester(client=client)
            works = await ingester.ingest_query("test", limit=10)
            assert len(works) == 1  # duplicate removed
