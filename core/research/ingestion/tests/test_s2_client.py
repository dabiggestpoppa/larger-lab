"""
Tests for L1.3 Semantic Scholar client.

6 tests covering:
1. Client initialization
2. Search returns papers
3. Paper parsing (title, abstract, authors)
4. DOI lookup
5. Paper ID lookup
6. Domain search
"""

from unittest.mock import MagicMock, patch

import pytest

from ..s2_client import S2Client
from ..models import Paper


@pytest.fixture
def mock_response():
    """Create a mock HTTP response."""
    def _make_response(data, status_code=200):
        response = MagicMock()
        response.status_code = status_code
        response.json.return_value = data
        response.raise_for_status = MagicMock()
        return response
    return _make_response


@pytest.fixture
def sample_paper():
    """Sample Semantic Scholar paper response."""
    return {
        "paperId": "abc123def456",
        "doi": "10.1234/test-paper",
        "title": "Test Paper on Memory Systems",
        "abstract": "This is a test abstract for memory systems.",
        "year": 2024,
        "publicationDate": "2024-01-15",
        "citationCount": 42,
        "url": "https://example.com/paper",
        "authors": [
            {"authorId": "A123", "name": "Jane Doe"},
            {"authorId": "A456", "name": "John Smith"},
        ],
        "references": [
            {"paperId": "ref1"},
            {"paperId": "ref2"},
        ],
    }


class TestS2ClientInit:
    """Test 1: Client initialization."""

    def test_client_initialization(self):
        """Client initializes with correct defaults."""
        client = S2Client()
        assert client.timeout == 30.0
        assert client.api_key is None

    def test_client_with_api_key(self):
        """Client accepts optional API key."""
        client = S2Client(api_key="test-key-123")
        assert client.api_key == "test-key-123"


class TestS2ClientSearch:
    """Test 2: Search returns papers."""

    @pytest.mark.asyncio
    async def test_search_returns_papers(self, mock_response, sample_paper):
        """Search returns Paper objects."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = mock_response({
                "data": [sample_paper]
            })
            
            async with S2Client() as client:
                papers = await client.search_by_query("memory systems", limit=10)
                
                assert len(papers) == 1
                assert isinstance(papers[0], Paper)


class TestS2ClientParsing:
    """Test 3: Paper parsing."""

    @pytest.mark.asyncio
    async def test_paper_parsing_title(self, mock_response, sample_paper):
        """Paper title is parsed correctly."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = mock_response({"data": [sample_paper]})
            
            async with S2Client() as client:
                papers = await client.search_by_query("test", limit=1)
                
                assert papers[0].title == "Test Paper on Memory Systems"

    @pytest.mark.asyncio
    async def test_paper_parsing_abstract(self, mock_response, sample_paper):
        """Paper abstract is parsed correctly."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = mock_response({"data": [sample_paper]})
            
            async with S2Client() as client:
                papers = await client.search_by_query("test", limit=1)
                
                assert "memory systems" in papers[0].abstract.lower()

    @pytest.mark.asyncio
    async def test_paper_parsing_authors(self, mock_response, sample_paper):
        """Paper authors are parsed correctly."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = mock_response({"data": [sample_paper]})
            
            async with S2Client() as client:
                papers = await client.search_by_query("test", limit=1)
                
                assert len(papers[0].authors) == 2
                assert papers[0].authors[0].name == "Jane Doe"


class TestS2ClientDoiLookup:
    """Test 4: DOI lookup."""

    @pytest.mark.asyncio
    async def test_get_paper_by_doi(self, mock_response, sample_paper):
        """get_paper_by_doi returns Paper object."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = mock_response(sample_paper)
            
            async with S2Client() as client:
                paper = await client.get_paper_by_doi("10.1234/test-paper")
                
                assert paper is not None
                assert paper.doi == "10.1234/test-paper"

    @pytest.mark.asyncio
    async def test_get_paper_by_doi_returns_none(self, mock_response):
        """get_paper_by_doi returns None for missing DOI."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = mock_response({})
            
            async with S2Client() as client:
                paper = await client.get_paper_by_doi("10.9999/missing")
                
                assert paper is None


class TestS2ClientPaperIdLookup:
    """Test 5: Paper ID lookup."""

    @pytest.mark.asyncio
    async def test_get_paper_by_id(self, mock_response, sample_paper):
        """get_paper returns Paper by ID."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = mock_response(sample_paper)
            
            async with S2Client() as client:
                paper = await client.get_paper("abc123def456")
                
                assert paper is not None
                assert paper.id == "abc123def456"


class TestS2ClientDomainSearch:
    """Test 6: Domain search."""

    @pytest.mark.asyncio
    async def test_fetch_by_domain(self, mock_response, sample_paper):
        """fetch_by_domain searches with domain query."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = mock_response({"data": [sample_paper]})
            
            async with S2Client() as client:
                papers = await client.fetch_by_domain("agent orchestration", limit=50)
                
                assert len(papers) == 1
                
                # Verify query was passed
                call_args = mock_get.call_args
                assert "query" in call_args[1]["params"]
                assert "agent orchestration" in call_args[1]["params"]["query"].lower()