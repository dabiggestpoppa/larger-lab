"""
Semantic Scholar API client for the research mesh.

Endpoint: https://api.semanticscholar.org/graph/v1/paper/
Returns: Paper objects in canonical schema
Rate limit: 1 req/s (free tier)
"""

from __future__ import annotations

import json
from typing import List, Optional

import httpx

from .models import Author, Concept, Paper


class S2Client:
    """
    Client for Semantic Scholar Graph API.
    
    Returns Paper objects in the canonical schema.
    """

    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    DEFAULT_TIMEOUT = 30.0
    DEFAULT_FIELDS = "title,abstract,authors,year,publicationDate,url,citationCount,references,doi"

    def __init__(self, api_key: Optional[str] = None, timeout: float = DEFAULT_TIMEOUT):
        self.api_key = api_key
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._client.aclose()

    def _get_headers(self) -> dict:
        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    async def _get(self, url: str, params: Optional[dict] = None) -> dict:
        """Make GET request with optional API key."""
        if params is None:
            params = {}
        params["fields"] = self.DEFAULT_FIELDS
        
        response = await self._client.get(url, params=params, headers=self._get_headers())
        response.raise_for_status()
        return response.json()

    def _parse_paper(self, data: dict) -> Paper:
        """Parse Semantic Scholar response into Paper object."""
        # Extract authors
        authors = []
        for author in data.get("authors", []):
            authors.append(Author(
                id=author.get("authorId", ""),
                name=author.get("name", ""),
            ))

        # Extract concepts (S2 doesn't have explicit concepts, use keywords)
        concepts = []
        # S2 doesn't return concepts in basic fields, skip for now

        # Extract references
        referenced_works = [
            ref.get("paperId", "")
            for ref in data.get("references", [])
            if ref.get("paperId")
        ]

        # Get publication date
        published_date = data.get("publicationDate", "")

        # Get citation count
        citation_count = data.get("citationCount", 0)

        # Get URL
        url = data.get("url", "")

        return Paper(
            id=data.get("paperId", ""),
            doi=data.get("doi", ""),
            title=data.get("title", ""),
            abstract=data.get("abstract", "") or "",
            year=data.get("year", 0) or 0,
            published_date=published_date,
            source="s2",
            source_id=data.get("paperId", ""),
            url=url,
            pdf_url="",  # S2 doesn't provide PDF URL in basic fields
            language="en",
            citation_count=citation_count,
            referenced_count=len(referenced_works),
            is_open_access=False,  # Would need additional field
            authors=authors,
            concepts=concepts,
            referenced_works=referenced_works,
            raw_json=json.dumps(data),
        )

    async def search_paper(self, query: str) -> Optional[Paper]:
        """
        Search for a paper by query.
        
        Returns first matching paper.
        """
        data = await self._get(
            f"{self.BASE_URL}/paper/search",
            params={"query": query, "limit": 1}
        )
        
        results = data.get("data", [])
        if not results:
            return None
        
        return self._parse_paper(results[0])

    async def get_paper(self, paper_id: str) -> Optional[Paper]:
        """
        Get a specific paper by Semantic Scholar ID.
        """
        data = await self._get(f"{self.BASE_URL}/paper/{paper_id}")
        
        if "paperId" not in data:
            return None
        
        return self._parse_paper(data)

    async def get_paper_by_doi(self, doi: str) -> Optional[Paper]:
        """
        Get a paper by DOI.
        """
        data = await self._get(f"{self.BASE_URL}/paper/{doi}")
        
        if "paperId" not in data:
            return None
        
        return self._parse_paper(data)

    async def search_by_query(
        self, 
        query: str, 
        limit: int = 20
    ) -> List[Paper]:
        """
        Search papers by query string.
        
        Returns up to limit papers.
        """
        data = await self._get(
            f"{self.BASE_URL}/paper/search",
            params={"query": query, "limit": limit}
        )
        
        return [self._parse_paper(p) for p in data.get("data", [])]

    async def fetch_by_domain(
        self, 
        domain_query: str, 
        limit: int = 50
    ) -> List[Paper]:
        """
        Fetch papers for a domain using a search query.
        
        Convenience method that wraps search_by_query.
        """
        return await self.search_by_query(domain_query, limit=limit)


async def quick_test():
    """Quick smoke test to verify API works."""
    async with S2Client() as client:
        papers = await client.search_by_query("agent orchestration", limit=5)
        print(f"Fetched {len(papers)} papers")
        for p in papers[:3]:
            print(f"  - {p.title[:60]}... (citations: {p.citation_count})")
        return papers


if __name__ == "__main__":
    import asyncio
    asyncio.run(quick_test())