"""
OpenAlex API client for the research mesh.

Endpoint: https://api.openalex.org/works
Filters: domain (from INITIAL_DOMAINS), year range, open access
Pagination: cursor-based, batch of 200
Rate limit: polite pool with mailto parameter
"""

from __future__ import annotations

import asyncio
import json
from typing import List, Optional

import httpx

from .models import Author, Concept, Paper
from .sources import get_registry


class OpenAlexClient:
    """
    Client for OpenAlex API.
    
    Returns Paper objects in the canonical schema.
    All requests include mailto parameter for polite pool rate limits.
    """

    BASE_URL = "https://api.openalex.org"
    DEFAULT_MAILTO = "ops@larger-lab.local"
    DEFAULT_PER_PAGE = 200
    DEFAULT_TIMEOUT = 30.0

    def __init__(self, mailto: Optional[str] = None, timeout: float = DEFAULT_TIMEOUT):
        self.mailto = mailto or self.DEFAULT_MAILTO
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.aclose()

    async def _get(self, url: str, params: Optional[dict] = None) -> dict:
        """Make GET request with mailto parameter."""
        if params is None:
            params = {}
        params["mailto"] = self.mailto
        
        response = await self._client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def _parse_paper(self, work: dict) -> Paper:
        """Parse OpenAlex work into Paper object."""
        # Extract authors
        authors = []
        for authorship in work.get("authorships", []):
            author = authorship.get("author") or {}
            authors.append(Author(
                id=(author.get("id") or "").replace("https://openalex.org/", ""),
                name=author.get("display_name", ""),
                orcid=author.get("orcid", ""),
            ))

        # Extract concepts
        concepts = []
        for concept in work.get("concepts", []):
            concepts.append(Concept(
                id=(concept.get("id") or "").replace("https://openalex.org/", ""),
                name=concept.get("display_name", ""),
                score=concept.get("score", 0.0),
                level=concept.get("level", 0),
            ))

        # Extract referenced works (citations)
        referenced_works = [
            (ref or "").replace("https://openalex.org/", "")
            for ref in work.get("referenced_works", [])
            if ref
        ]

        # Get publication year
        publication_year = work.get("publication_year", 0) or 0

        # Get publication date
        published_date = work.get("publication_date", "") or ""

        # Get best available abstract
        abstract = ""
        if work.get("abstract_inverted_index"):
            abstract = self._reconstruct_abstract(work["abstract_inverted_index"])

        # Get PDF URL
        pdf_url = ""
        best_oa = work.get("best_oa_location") or {}
        if best_oa:
            pdf_url = best_oa.get("url", "") or ""

        # Get open access status
        is_oa = (work.get("open_access") or {}).get("is_oa", False)

        # Get citation count
        citation_count = work.get("cited_by_count", 0)

        # Get primary location URL
        url = ""
        primary_location = work.get("primary_location", {})
        if primary_location:
            url = primary_location.get("landing_page_url", "")

        return Paper(
            id=work.get("id", "").replace("https://openalex.org/", ""),
            doi=(work.get("doi") or "").replace("https://doi.org/", ""),
            title=work.get("display_name", ""),
            abstract=abstract,
            year=publication_year,
            published_date=published_date,
            source="openalex",
            source_id=work.get("id", "").replace("https://openalex.org/", ""),
            url=url,
            pdf_url=pdf_url,
            language=work.get("language", "en"),
            citation_count=citation_count,
            referenced_count=work.get("referenced_works_count", 0),
            is_open_access=is_oa,
            authors=authors,
            concepts=concepts,
            referenced_works=referenced_works,
            raw_json=json.dumps(work),
        )

    def _reconstruct_abstract(self, inverted_index: dict) -> str:
        """Reconstruct abstract from inverted index format."""
        if not inverted_index:
            return ""
        
        # Find max position
        max_pos = 0
        for word, positions in inverted_index.items():
            for pos in positions:
                max_pos = max(max_pos, pos)
        
        # Build word list
        words = [""] * (max_pos + 1)
        for word, positions in inverted_index.items():
            for pos in positions:
                words[pos] = word
        
        return " ".join(words)

    async def search(
        self,
        query: str,
        per_page: int = DEFAULT_PER_PAGE,
        cursor: Optional[str] = None
    ) -> List[Paper]:
        """
        General search by query string.
        
        Returns: List of Paper objects
        """
        params = {
            "search": query,
            "per_page": per_page,
            "sort": "cited_by_count:desc",
        }
        if cursor:
            params["cursor"] = cursor
        data = await self._get(f"{self.BASE_URL}/works", params=params)
        papers = [self._parse_paper(work) for work in data.get("results", [])]
        return papers

    async def search_by_domain(
        self, 
        domain: str, 
        per_page: int = DEFAULT_PER_PAGE,
        cursor: Optional[str] = None
    ) -> tuple[List[Paper], Optional[str]]:
        """
        Search works by domain query.
        
        Returns: (papers, next_cursor)
        """
        registry = get_registry()
        query = registry.openalex_query_for_domain(domain)
        
        params = {
            "search": query,
            "per_page": per_page,
            "sort": "cited_by_count:desc",
        }
        
        if cursor:
            params["cursor"] = cursor

        data = await self._get(f"{self.BASE_URL}/works", params=params)
        
        papers = [self._parse_paper(work) for work in data.get("results", [])]
        
        # Get next cursor
        meta = data.get("meta", {})
        next_cursor = meta.get("next_cursor")
        
        return papers, next_cursor

    async def search_by_doi(self, doi: str) -> Optional[Paper]:
        """Get a specific work by DOI."""
        data = await self._get(f"{self.BASE_URL}/works/{doi}")
        if "id" not in data:
            return None
        return self._parse_paper(data)

    async def fetch_batch(
        self, 
        domain: str, 
        batch_size: int = DEFAULT_PER_PAGE
    ) -> List[Paper]:
        """
        Fetch a batch of papers for a domain.
        
        Convenience method that handles pagination internally.
        """
        papers = []
        cursor = None
        
        while len(papers) < batch_size:
            batch, cursor = await self.search_by_domain(domain, per_page=batch_size)
            papers.extend(batch)
            
            if not cursor:
                break
        
        return papers[:batch_size]

    async def fetch_multiple_domains(
        self, 
        domains: List[str], 
        per_domain: int = 50
    ) -> List[Paper]:
        """Fetch papers from multiple domains."""
        all_papers = []
        
        for domain in domains:
            papers = await self.fetch_batch(domain, batch_size=per_domain)
            all_papers.extend(papers)
        
        return all_papers


async def quick_test():
    """Quick smoke test to verify API works."""
    async with OpenAlexClient() as client:
        papers, cursor = await client.search_by_domain("agent_orchestration", per_page=10)
        print(f"Fetched {len(papers)} papers")
        for p in papers[:3]:
            print(f"  - {p.title[:60]}... (citations: {p.citation_count})")
        return papers


if __name__ == "__main__":
    asyncio.run(quick_test())