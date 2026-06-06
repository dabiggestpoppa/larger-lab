"""
Tests for L1.2 — arXiv client.

6 tests:
    1. Parse valid Atom XML response → List[Paper]
    2. Paper fields correctly mapped (title, abstract, authors, year, concepts)
    3. Empty response → empty list
    4. Entry with missing title is skipped
    5. Categories mapped to Concepts
    6. fetch_by_id returns single paper or None

Uses mock XML fixtures (no live API calls).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from core.research.ingestion.arxiv_client import ArxivClient
from core.research.ingestion.models import Paper, PaperStatus


# ============================================================
# Fixtures
# ============================================================

SAMPLE_ATOM_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2301.07041v2</id>
    <title>Attention Is All You Need</title>
    <published>2023-01-15T00:00:00Z</published>
    <summary>We propose a new simple network architecture, the Transformer,
    based solely on attention mechanisms.</summary>
    <author><name>Ashish Vaswani</name></author>
    <author><name>Noam Shazeer</name></author>
    <category term="cs.CL" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.LG" scheme="http://arxiv.org/schemas/atom"/>
    <arxiv:primary_category term="cs.CL" scheme="http://arxiv.org/schemas/atom"/>
    <link title="pdf" href="https://arxiv.org/pdf/2301.07041.pdf" type="application/pdf"/>
    <arxiv:doi>10.48550/arXiv.2301.07041</arxiv:doi>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2302.12345v1</id>
    <title>Graph Neural Networks for Multi-Agent Systems</title>
    <published>2023-06-20T00:00:00Z</published>
    <summary>We study GNNs in the context of multi-agent orchestration.</summary>
    <author><name>Jane Doe</name></author>
    <category term="cs.AI" scheme="http://arxiv.org/schemas/atom"/>
    <arxiv:primary_category term="cs.AI" scheme="http://arxiv.org/schemas/atom"/>
  </entry>
</feed>
"""

EMPTY_ATOM_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
</feed>
"""

NO_TITLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/9999.99999</id>
    <published>2023-01-01T00:00:00Z</published>
    <summary>No title here</summary>
  </entry>
</feed>
"""


@pytest.fixture
def client():
    return ArxivClient()


# ============================================================
# Tests
# ============================================================

class TestArxivParseResponse:
    def test_parse_valid_xml_returns_papers(self, client):
        papers = client._parse_response(SAMPLE_ATOM_XML)
        assert len(papers) == 2
        assert all(isinstance(p, Paper) for p in papers)

    def test_paper_fields_mapped_correctly(self, client):
        papers = client._parse_response(SAMPLE_ATOM_XML)
        p = papers[0]
        assert p.title == "Attention Is All You Need"
        assert "Transformer" in p.abstract
        assert p.year == 2023
        assert p.published_date == "2023-01-15T00:00:00Z"
        assert p.source == "arxiv"
        assert p.source_id == "2301.07041v2"
        assert p.id == "arxiv:2301.07041v2"
        assert p.url == "http://arxiv.org/abs/2301.07041v2"
        assert p.pdf_url == "https://arxiv.org/pdf/2301.07041.pdf"
        assert p.doi == "10.48550/arXiv.2301.07041"
        assert p.status == PaperStatus.PENDING

    def test_authors_parsed(self, client):
        papers = client._parse_response(SAMPLE_ATOM_XML)
        p = papers[0]
        assert len(p.authors) == 2
        assert p.authors[0].name == "Ashish Vaswani"
        assert p.authors[1].name == "Noam Shazeer"

    def test_empty_response_returns_empty_list(self, client):
        papers = client._parse_response(EMPTY_ATOM_XML)
        assert papers == []

    def test_entry_missing_title_skipped(self, client):
        papers = client._parse_response(NO_TITLE_XML)
        assert len(papers) == 0

    def test_categories_mapped_to_concepts(self, client):
        papers = client._parse_response(SAMPLE_ATOM_XML)
        p = papers[0]
        assert len(p.concepts) >= 2
        concept_names = [c.name for c in p.concepts]
        assert "cs.CL" in concept_names
        assert "cs.LG" in concept_names
        # Primary category should be first
        assert p.concepts[0].name == "cs.CL"
        assert p.concepts[0].level == 0


class TestArxivClientIntegration:
    """Tests that mock the HTTP layer."""

    @pytest.mark.asyncio
    async def test_search_returns_papers(self, client):
        """search() calls the API and parses the response."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=SAMPLE_ATOM_XML)
        mock_response.raise_for_status = MagicMock()

        # Build a proper async context manager for `async with session.get(url) as resp`
        class MockCM:
            def __init__(self, resp):
                self._resp = resp
            async def __aenter__(self):
                return self._resp
            async def __aexit__(self, *exc):
                return False

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=MockCM(mock_response))
        mock_session.closed = False

        client._session = mock_session
        papers = await client.search("cat:cs.AI", max_results=2)
        assert len(papers) == 2
        assert papers[0].title == "Attention Is All You Need"

    @pytest.mark.asyncio
    async def test_fetch_by_id_returns_single_paper(self, client):
        """fetch_by_id returns the first paper or None."""
        single_xml = SAMPLE_ATOM_XML  # has 2 entries, but we want first
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=single_xml)
        mock_response.raise_for_status = MagicMock()

        class MockCM:
            def __init__(self, resp):
                self._resp = resp
            async def __aenter__(self):
                return self._resp
            async def __aexit__(self, *exc):
                return False

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=MockCM(mock_response))
        mock_session.closed = False

        client._session = mock_session
        paper = await client.fetch_by_id("2301.07041")
        assert paper is not None
        assert paper.title == "Attention Is All You Need"

    @pytest.mark.asyncio
    async def test_fetch_by_id_empty_returns_none(self, client):
        """fetch_by_id returns None when no results."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=EMPTY_ATOM_XML)
        mock_response.raise_for_status = MagicMock()

        class MockCM:
            def __init__(self, resp):
                self._resp = resp
            async def __aenter__(self):
                return self._resp
            async def __aexit__(self, *exc):
                return False

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=MockCM(mock_response))
        mock_session.closed = False

        client._session = mock_session
        paper = await client.fetch_by_id("0000.00000")
        assert paper is None
