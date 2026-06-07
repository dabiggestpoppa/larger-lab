"""
L1.2 — arXiv API client.

Fetches papers from the arXiv search API (Atom XML response).
Normalizes results to the canonical Paper schema.

API: http://export.arxiv.org/api/query
Response: Atom XML (not JSON)

Usage:
    client = ArxivClient()
    papers = await client.search("cat:cs.AI+AND+abs:transformer", max_results=10)
"""

from __future__ import annotations

import asyncio
import logging
import ssl
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Optional

import aiohttp

from .models import Author, Concept, Paper, PaperStatus
from .rate_limit import RateLimit

logger = logging.getLogger(__name__)

# Atom XML namespace
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}
ARXIV_NS = {"arxiv": "http://arxiv.org/schemas/atom"}

# Default categories matching INITIAL_DOMAINS
DEFAULT_CATEGORIES = ["cs.AI", "cs.LG", "cs.CL", "cs.IR", "cs.NE", "cs.MA", "cs.DC"]


class ArxivError(Exception):
    """Base exception for arXiv client errors."""

    def __init__(self, message: str, status: int = 0):
        super().__init__(message)
        self.status = status


class ArxivClient:
    """
    Async arXiv API client with rate limiting + retry.

    Returns List[Paper] in the canonical schema.
    """

    BASE_URL = "http://export.arxiv.org/api/query"

    def __init__(
        self,
        rate_limit: Optional[RateLimit] = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        self.rate_limit = rate_limit or RateLimit(
            per_second=3.0,  # arXiv asks for ≤3 req/s
            max_retries=max_retries,
        )
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            # Disable SSL verification on Windows where cert store may be incomplete
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
            connector = aiohttp.TCPConnector(ssl=ssl_ctx)
            self._session = aiohttp.ClientSession(timeout=self.timeout, connector=connector)
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.close()
        return False

    async def search(
        self,
        query: str,
        max_results: int = 20,
        start: int = 0,
        sort_by: str = "submittedDate",
        sort_order: str = "descending",
    ) -> List[Paper]:
        """
        Search arXiv and return normalized Paper objects.

        Args:
            query: arXiv search query (e.g., "cat:cs.AI+AND+abs:transformer")
            max_results: max papers to return (capped at 200 per request)
            start: offset for pagination
            sort_by: "relevance" | "lastUpdatedDate" | "submittedDate"
            sort_order: "ascending" | "descending"
        """
        max_results = min(max_results, 200)
        params = {
            "search_query": query,
            "start": start,
            "max_results": max_results,
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }
        url = f"{self.BASE_URL}?search_query={urllib.parse.quote(query)}&start={start}&max_results={max_results}&sortBy={sort_by}&sortOrder={sort_order}"

        logger.info("arxiv: fetching %d results for query=%s", max_results, query)

        async def _fetch():
            session = await self._get_session()
            async with session.get(url) as resp:
                if resp.status == 429:
                    raise ArxivError("arXiv rate limit hit", status=429)
                if resp.status >= 500:
                    raise ArxivError(f"arXiv server error {resp.status}", status=resp.status)
                resp.raise_for_status()
                return await resp.text()

        xml_text = await self.rate_limit.execute_with_retry(_fetch)
        papers = self._parse_response(xml_text)
        logger.info("arxiv: parsed %d papers from response", len(papers))
        return papers

    async def search_by_category(
        self,
        category: str,
        max_results: int = 20,
        days_back: int = 7,
    ) -> List[Paper]:
        """Search by arXiv category with a recency filter."""
        query = f"cat:{category}"
        return await self.search(query, max_results=max_results)

    async def fetch_by_id(self, arxiv_id: str) -> Optional[Paper]:
        """Fetch a single paper by arXiv ID (e.g., '2301.07041')."""
        papers = await self.search(f"id:{arxiv_id}", max_results=1)
        return papers[0] if papers else None

    def _parse_response(self, xml_text: str) -> List[Paper]:
        """Parse Atom XML response into List[Paper]."""
        root = ET.fromstring(xml_text)
        papers = []
        for entry in root.findall("atom:entry", ATOM_NS):
            try:
                paper = self._parse_entry(entry)
                if paper:
                    papers.append(paper)
            except Exception as exc:
                logger.warning("arxiv: failed to parse entry: %s", exc)
        return papers

    def _parse_entry(self, entry: ET.Element) -> Optional[Paper]:
        """Parse a single Atom entry into a Paper."""
        title_el = entry.find("atom:title", ATOM_NS)
        if title_el is None or not title_el.text:
            return None
        title = title_el.text.strip().replace("\n", " ")

        # arXiv ID from <id>http://arxiv.org/abs/...</id>
        id_el = entry.find("atom:id", ATOM_NS)
        arxiv_url = id_el.text.strip() if id_el is not None and id_el.text else ""
        arxiv_id = arxiv_url.split("/abs/")[-1] if "/abs/" in arxiv_url else arxiv_url

        # Published date
        published_el = entry.find("atom:published", ATOM_NS)
        published_date = published_el.text.strip() if published_el is not None and published_el.text else ""
        year = 0
        if published_date:
            try:
                year = int(published_date[:4])
            except (ValueError, IndexError):
                pass

        # Summary (abstract)
        summary_el = entry.find("atom:summary", ATOM_NS)
        abstract = summary_el.text.strip().replace("\n", " ") if summary_el is not None and summary_el.text else ""

        # Authors
        authors = []
        for author_el in entry.findall("atom:author", ATOM_NS):
            name_el = author_el.find("atom:name", ATOM_NS)
            if name_el is not None and name_el.text:
                authors.append(Author(name=name_el.text.strip()))

        # Categories → Concepts
        concepts = []
        for cat_el in entry.findall("atom:category", ATOM_NS):
            term = cat_el.get("term", "")
            if term:
                concepts.append(Concept(id=f"arxiv:{term}", name=term, score=1.0, level=1))

        # Primary category (arxiv namespace) — promote to level 0, move to front
        primary_cat = entry.find("arxiv:primary_category", ARXIV_NS)
        if primary_cat is not None:
            term = primary_cat.get("term", "")
            if term:
                # Remove existing entry for this term if present
                concepts = [c for c in concepts if c.name != term]
                concepts.insert(0, Concept(id=f"arxiv:{term}", name=term, score=1.0, level=0))

        # DOI (if available in arxiv namespace)
        doi_el = entry.find("arxiv:doi", ARXIV_NS)
        doi = doi_el.text.strip() if doi_el is not None and doi_el.text else ""

        # Links
        pdf_url = ""
        for link_el in entry.findall("atom:link", ATOM_NS):
            if link_el.get("title") == "pdf":
                pdf_url = link_el.get("href", "")
                break

        paper_id = f"arxiv:{arxiv_id}" if not arxiv_id.startswith("arxiv:") else arxiv_id

        return Paper(
            id=paper_id,
            doi=doi,
            title=title,
            abstract=abstract,
            year=year,
            published_date=published_date,
            source="arxiv",
            source_id=arxiv_id,
            url=arxiv_url,
            pdf_url=pdf_url,
            authors=authors,
            concepts=concepts,
            status=PaperStatus.PENDING,
            raw_json=ET.tostring(entry, encoding="unicode"),
        )
