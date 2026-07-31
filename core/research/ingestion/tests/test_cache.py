"""
Tests for L1.7 Cache + dedup layer.

6 tests covering:
1. Basic write and retrieval
2. DOI-based dedup
3. Fuzzy title+author+year dedup
4. Daily write cap enforcement
5. Batch write with dedup
6. Ingestion log recording
"""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from ..cache import Cache, DailyCapExceeded, get_cache
from ..models import Paper, PaperStatus


@pytest.fixture
def temp_cache():
    """Create a cache with a temporary database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_papers.db"
        cache = Cache(db_path)
        yield cache


class TestCacheBasicWrite:
    """Test 1: Basic write and retrieval."""

    def test_write_and_retrieve_paper(self, temp_cache):
        paper = Paper(
            id="W123456789",
            doi="10.1234/test-paper",
            title="Test Paper for Cache",
            abstract="This is a test abstract.",
            year=2024,
            source="openalex",
            source_id="W123456789",
            url="https://example.com/paper",
            citation_count=42,
        )

        success, msg = temp_cache.write(paper)
        assert success is True
        assert "Written" in msg

        retrieved = temp_cache.get_paper("W123456789")
        assert retrieved is not None
        assert retrieved.title == "Test Paper for Cache"
        assert retrieved.doi == "10.1234/test-paper"
        assert retrieved.year == 2024


class TestCacheDoiDedup:
    """Test 2: DOI-based dedup prevents duplicates."""

    def test_doi_prevents_duplicate(self, temp_cache):
        paper1 = Paper(
            id="W111",
            doi="10.1234/same-paper",
            title="Original Title",
            year=2024,
            source="openalex",
        )
        paper2 = Paper(
            id="W222",
            doi="10.1234/same-paper",  # Same DOI
            title="Different Title",
            year=2024,
            source="s2",
        )

        success1, _ = temp_cache.write(paper1)
        assert success1 is True

        success2, msg2 = temp_cache.write(paper2)
        assert success2 is False
        assert "already exists" in msg2


class TestCacheFuzzyDedup:
    """Test 3: Fuzzy title+author+year dedup fallback."""

    def test_fuzzy_match_prevents_duplicate(self, temp_cache):
        from ..models import Author
        
        paper1 = Paper(
            id="W111",
            title="Deep Learning for Memory Systems",
            year=2023,
            source="openalex",
            authors=[Author(name="Smith, John")],
        )
        paper2 = Paper(
            id="W222",
            title="Deep Learning for Memory Systems",  # Identical title
            year=2023,  # Same year
            source="arxiv",  # Different source
            authors=[Author(name="Smith, John")],
        )

        success1, _ = temp_cache.write(paper1)
        assert success1 is True

        success2, msg2 = temp_cache.write(paper2)
        assert success2 is False
        assert "already exists" in msg2


class TestCacheDailyCap:
    """Test 4: Daily write cap enforcement."""

    def test_daily_cap_enforced(self, temp_cache):
        # Write 200 papers (the cap)
        for i in range(200):
            paper = Paper(
                id=f"W{i:04d}",
                title=f"Paper {i}",
                year=2024,
                source="openalex",
            )
            temp_cache.write(paper)

        # 201st should fail
        paper_201 = Paper(
            id="W201",
            title="Paper 201",
            year=2024,
            source="openalex",
        )

        with pytest.raises(DailyCapExceeded):
            temp_cache.write(paper_201)


class TestCacheBatchWrite:
    """Test 5: Batch write with dedup."""

    def test_batch_write_with_mixed_results(self, temp_cache):
        papers = [
            Paper(id="W1", title="Paper 1", year=2024, source="openalex"),
            Paper(id="W2", title="Paper 2", year=2024, source="openalex"),
            Paper(id="W1", title="Paper 1", year=2024, source="openalex"),  # Duplicate
            Paper(id="W3", title="Paper 3", year=2024, source="openalex"),
        ]

        written, skipped, messages = temp_cache.write_batch(papers)
        assert written == 3
        assert skipped == 1
        assert any("already exists" in m for m in messages)


class TestCacheIngestionLog:
    """Test 6: Ingestion log recording."""

    def test_ingestion_log_recorded(self, temp_cache):
        temp_cache.log_ingestion(
            source="openalex",
            query="agent orchestration",
            papers_found=50,
            papers_new=45,
            papers_dup=5,
            errors=0,
            duration_seconds=12.5,
        )

        conn = temp_cache._get_connection()
        cursor = conn.execute(
            "SELECT source, papers_found, papers_new, papers_dup, errors FROM ingestion_log"
        )
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[0] == "openalex"
        assert row[1] == 50
        assert row[2] == 45
        assert row[3] == 5
        assert row[4] == 0