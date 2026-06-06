"""
Tests for L1.1 OpenAlex client.

8 tests covering:
1. Basic API connectivity
2. Domain search returns papers
3. Paper parsing (title, abstract, authors, concepts)
4. Pagination with cursor
5. DOI lookup
6. Batch fetch
7. Multiple domains fetch
8. Rate limit handling (mailto param)
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ..openalex_client import OpenAlexClient
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
def sample_work():
    """Sample OpenAlex work response."""
    return {
        "id": "https://openalex.org/W123456789",
        "doi": "https://doi.org/10.1234/test",
        "display_name": "Test Paper on Agent Orchestration",
        "publication_year": 2024,
        "publication_date": "2024-01-15",
        "cited_by_count": 42,
        "referenced_works_count": 15,
        "language": "en",
        "abstract_inverted_index": {
            "This": [0],
            "is": [1],
            "a": [2],
            "test": [3],
            "abstract": [4],
        },
        "authorships": [
            {
                "author": {
                    "id": "https://openalex.org/A12345",
                    "display_name": "John Smith",
                    "orcid": "https://orcid.org/0000-0001-2345-6789",
                }
            }
        ],
        "concepts": [
            {
                "id": "https://openalex.org/C12345",
                "display_name": "Agent Orchestration",
                "score": 0.87,
                "level": 2,
            }
        ],
        "referenced_works": ["https://openalex.org/W111", "https://openalex.org/W222"],
        "open_access": {"is_oa": True},
        "best_oa_location": {"url": "https://example.com/paper.pdf"},
        "primary_location": {"landing_page_url": "https://example.com/paper"},
    }


class TestOpenAlexClientConnectivity:
    """Test 1: Basic API connectivity."""

    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Client initializes with correct defaults."""
        async with OpenAlexClient() as client:
            assert client.mailto == "ops@larger-lab.local"
            assert client.timeout == 30.0

    @pytest.mark.asyncio
    async def test_mailto_included_in_request(self, mock_response, sample_work):
        """Mailto parameter is included in all requests."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = mock_response({"results": [sample_work]})
            
            async with OpenAlexClient() as client:
                await client.search_by_domain("agent_orchestration", per_page=1)
                
                # Check that mailto was in params
                call_args = mock_get.call_args
                assert "mailto" in call_args[1]["params"]
                assert call_args[1]["params"]["mailto"] == "ops@larger-lab.local"


class TestOpenAlexClientDomainSearch:
    """Test 2: Domain search returns papers."""

    @pytest.mark.asyncio
    async def test_search_by_domain_returns_papers(self, mock_response, sample_work):
        """Domain search returns Paper objects."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = mock_response({
                "results": [sample_work],
                "meta": {"next_cursor": None}
            })
            
            async with OpenAlexClient() as client:
                papers, cursor = await client.search_by_domain("agent_orchestration", per_page=10)
                
                assert len(papers) == 1
                assert isinstance(papers[0], Paper)
                assert cursor is None

    @pytest.mark.asyncio
    async def test_search_by_domain_uses_registry_query(self, mock_response, sample_work):
        """Domain search uses registry query mapping."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = mock_response({
                "results": [sample_work],
                "meta": {}
            })
            
            async with OpenAlexClient() as client:
                await client.search_by_domain("agent_orchestration", per_page=10)
                
                call_args = mock_get.call_args
                assert "search" in call_args[1]["params"]
                assert "agent orchestration" in call_args[1]["params"]["search"].lower()


class TestOpenAlexClientParsing:
    """Test 3: Paper parsing."""

    @pytest.mark.asyncio
    async def test_paper_parsing_title(self, mock_response, sample_work):
        """Paper title is parsed correctly."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = mock_response({"results": [sample_work]})
            
            async with OpenAlexClient() as client:
                papers, _ = await client.search_by_domain("test", per_page=1)
                
                assert papers[0].title == "Test Paper on Agent Orchestration"

    @pytest.mark.asyncio
    async def test_paper_parsing_abstract(self, mock_response, sample_work):
        """Paper abstract is reconstructed from inverted index."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = mock_response({"results": [sample_work]})
            
            async with OpenAlexClient() as client:
                papers, _ = await client.search_by_domain("test", per_page=1)
                
                assert "test abstract" in papers[0].abstract.lower()

    @pytest.mark.asyncio
    async def test_paper_parsing_authors(self, mock_response, sample_work):
        """Paper authors are parsed correctly."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = mock_response({"results": [sample_work]})
            
            async with OpenAlexClient() as client:
                papers, _ = await client.search_by_domain("test", per_page=1)
                
                assert len(papers[0].authors) == 1
                assert papers[0].authors[0].name == "John Smith"

    @pytest.mark.asyncio
    async def test_paper_parsing_concepts(self, mock_response, sample_work):
        """Paper concepts are parsed with scores."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = mock_response({"results": [sample_work]})
            
            async with OpenAlexClient() as client:
                papers, _ = await client.search_by_domain("test", per_page=1)
                
                assert len(papers[0].concepts) == 1
                assert papers[0].concepts[0].score == 0.87


class TestOpenAlexClientPagination:
    """Test 4: Pagination with cursor."""

    @pytest.mark.asyncio
    async def test_pagination_returns_cursor(self, mock_response, sample_work):
        """Pagination returns next_cursor for continuation."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = mock_response({
                "results": [sample_work],
                "meta": {"next_cursor": "cursor_abc123"}
            })
            
            async with OpenAlexClient() as client:
                papers, cursor = await client.search_by_domain("test", per_page=1)
                
                assert cursor == "cursor_abc123"

    @pytest.mark.asyncio
    async def test_pagination_uses_cursor(self, mock_response, sample_work):
        """Subsequent request uses cursor parameter."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = mock_response({
                "results": [sample_work],
                "meta": {}
            })
            
            async with OpenAlexClient() as client:
                await client.search_by_domain("test", per_page=1, cursor="cursor_xyz")
                
                call_args = mock_get.call_args
                assert call_args[1]["params"]["cursor"] == "cursor_xyz"


class TestOpenAlexClientDoiLookup:
    """Test 5: DOI lookup."""

    @pytest.mark.asyncio
    async def test_doi_lookup_returns_paper(self, mock_response, sample_work):
        """DOI lookup returns Paper object."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = mock_response(sample_work)
            
            async with OpenAlexClient() as client:
                paper = await client.search_by_doi("10.1234/test")
                
                assert paper is not None
                assert paper.doi == "10.1234/test"

    @pytest.mark.asyncio
    async def test_doi_lookup_returns_none_for_missing(self, mock_response):
        """DOI lookup returns None for missing DOI."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = mock_response({})
            
            async with OpenAlexClient() as client:
                paper = await client.search_by_doi("10.9999/missing")
                
                assert paper is None


class TestOpenAlexClientBatchFetch:
    """Test 6: Batch fetch."""

    @pytest.mark.asyncio
    async def test_fetch_batch_returns_correct_count(self, mock_response, sample_work):
        """fetch_batch returns requested number of papers."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = mock_response({
                "results": [sample_work] * 5,
                "meta": {}
            })
            
            async with OpenAlexClient() as client:
                papers = await client.fetch_batch("test", batch_size=5)
                
                assert len(papers) == 5


class TestOpenAlexClientMultipleDomains:
    """Test 7: Multiple domains fetch."""

    @pytest.mark.asyncio
    async def test_fetch_multiple_domains(self, mock_response, sample_work):
        """fetch_multiple_domains fetches from all domains."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.return_value = mock_response({
                "results": [sample_work] * 5,  # Return 5 papers per call
                "meta": {}
            })
            
            async with OpenAlexClient() as client:
                papers = await client.fetch_multiple_domains(
                    ["agent_orchestration", "memory_systems"],
                    per_domain=5
                )
                
                assert len(papers) == 10  # 5 per domain


class TestOpenAlexClientRateLimit:
    """Test 8: Rate limit handling."""

    @pytest.mark.asyncio
    async def test_rate_limit_configurable(self):
        """Rate limit can be configured via SourceRegistry."""
        from ..sources import get_registry
        
        registry = get_registry()
        config = registry.get("openalex")
        
        assert config.rate_limit_per_second == 10.0
        assert config.mailto == "ops@larger-lab.local"