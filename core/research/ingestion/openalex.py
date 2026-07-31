"""
Phase 1.1 — OpenAlex Stabilization

Stabilizes OpenAlex research paper ingestion:
- API client with rate limiting
- Response normalization
- Semantic tagging
- Embedding compatibility
- Deduplication

OpenAlex API: https://api.openalex.org
Docs: https://docs.openalex.org
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.openalex")

# ─── Configuration ───────────────────────────────────────────────────────────

OPENALEX_BASE_URL = "https://api.openalex.org"
OPENALEX_RATE_LIMIT = 10  # requests per second (free tier)
OPENALEX_PAGE_SIZE = 200  # max results per page

# ─── Data Models ─────────────────────────────────────────────────────────────

@dataclass
class OpenAlexAuthor:
    """An author from OpenAlex."""
    author_id: str  # OpenAlex ID (e.g., "A123456789")
    display_name: str
    orcid: Optional[str] = None
    affiliations: List[str] = field(default_factory=list)
    cited_by_count: int = 0
    works_count: int = 0

    def to_dict(self) -> dict:
        return {
            "author_id": self.author_id,
            "display_name": self.display_name,
            "orcid": self.orcid,
            "affiliations": self.affiliations,
            "cited_by_count": self.cited_by_count,
            "works_count": self.works_count,
        }


@dataclass
class OpenAlexConcept:
    """A concept/topic from OpenAlex."""
    concept_id: str  # OpenAlex ID
    display_name: str
    level: int = 0  # 0 = most specific, higher = broader
    score: float = 0.0  # relevance score
    wikidata: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "concept_id": self.concept_id,
            "display_name": self.display_name,
            "level": self.level,
            "score": self.score,
            "wikidata": self.wikidata,
        }


@dataclass
class OpenAlexWork:
    """A research work (paper) from OpenAlex."""
    work_id: str  # OpenAlex ID (e.g., "W123456789")
    doi: Optional[str] = None
    title: str = ""
    abstract: str = ""
    authors: List[OpenAlexAuthor] = field(default_factory=list)
    concepts: List[OpenAlexConcept] = field(default_factory=list)
    publication_date: Optional[str] = None
    cited_by_count: int = 0
    referenced_works: List[str] = field(default_factory=list)
    open_access_url: Optional[str] = None
    source: str = "openalex"
    ingested_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def canonical_id(self) -> str:
        """Canonical identifier — DOI preferred, fallback to OpenAlex ID."""
        return self.doi or self.work_id

    @property
    def semantic_tags(self) -> List[str]:
        """Generate semantic tags from concepts."""
        return [c.display_name for c in self.concepts if c.score > 0.3]

    def to_dict(self) -> dict:
        return {
            "work_id": self.work_id,
            "doi": self.doi,
            "title": self.title,
            "abstract": self.abstract,
            "authors": [a.to_dict() for a in self.authors],
            "concepts": [c.to_dict() for c in self.concepts],
            "publication_date": self.publication_date,
            "cited_by_count": self.cited_by_count,
            "referenced_works": self.referenced_works,
            "open_access_url": self.open_access_url,
            "source": self.source,
            "ingested_at": self.ingested_at,
        }


# ─── Rate Limiter ────────────────────────────────────────────────────────────

class RateLimiter:
    """Simple async rate limiter."""

    def __init__(self, max_per_second: int = OPENALEX_RATE_LIMIT):
        self._min_interval = 1.0 / max_per_second
        self._last_call = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_call
            if elapsed < self._min_interval:
                await asyncio.sleep(self._min_interval - elapsed)
            self._last_call = time.monotonic()


# ─── OpenAlex API Client ────────────────────────────────────────────────────

class OpenAlexClient:
    """
    Async API client for OpenAlex.
    
    Usage:
        client = OpenAlexClient()
        works = await client.search_works("semantic memory", limit=10)
        work = await client.get_work_by_doi("10.1038/s41586-021-03819-2")
    """

    def __init__(
        self,
        base_url: str = OPENALEX_BASE_URL,
        api_key: Optional[str] = None,
        rate_limit: int = OPENALEX_RATE_LIMIT,
        timeout: float = 30.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.environ.get("OPENALEX_API_KEY", "")
        self.rate_limiter = RateLimiter(rate_limit)
        self.timeout = timeout
        self._session = None

    async def _get_session(self):
        """Lazy-create aiohttp session."""
        if self._session is None:
            import aiohttp
            headers = {"User-Agent": "OCE-Phase1/1.0"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self._session = aiohttp.ClientSession(
                base_url=self.base_url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            )
        return self._session

    async def close(self):
        if self._session:
            await self._session.close()
            self._session = None

    async def _request(self, path: str, params: Optional[dict] = None) -> dict:
        """Make a rate-limited API request."""
        await self.rate_limiter.acquire()
        session = await self._get_session()
        async with session.get(path, params=params) as resp:
            if resp.status == 429:
                retry_after = int(resp.headers.get("Retry-After", 5))
                logger.warning(f"Rate limited, waiting {retry_after}s")
                await asyncio.sleep(retry_after)
                return await self._request(path, params)
            resp.raise_for_status()
            return await resp.json()

    async def search_works(
        self,
        query: str,
        limit: int = 25,
        offset: int = 0,
        page: int = 0,
        filters: Optional[dict] = None,
    ) -> List[dict]:
        """Search for works by query string."""
        if page > 0:
            page_num = page
        else:
            page_num = (offset // OPENALEX_PAGE_SIZE) + 1
        params = {
            "search": query,
            "per-page": min(limit, OPENALEX_PAGE_SIZE),
            "page": page_num,
        }
        if filters:
            filter_str = ",".join(f"{k}:{v}" for k, v in filters.items())
            params["filter"] = filter_str

        data = await self._request("/works", params)
        return data.get("results", [])

    async def get_work_by_doi(self, doi: str) -> Optional[dict]:
        """Fetch a single work by DOI."""
        # Normalize DOI
        doi = doi.strip().lower()
        if doi.startswith("https://doi.org/"):
            doi = doi[18:]
        try:
            data = await self._request(f"/works/doi:{doi}")
            return data
        except Exception as e:
            logger.warning(f"Failed to fetch DOI {doi}: {e}")
            return None

    async def get_work_by_id(self, work_id: str) -> Optional[dict]:
        """Fetch a single work by OpenAlex ID."""
        try:
            return await self._request(f"/works/{work_id}")
        except Exception as e:
            logger.warning(f"Failed to fetch work {work_id}: {e}")
            return None

    async def get_author(self, author_id: str) -> Optional[dict]:
        """Fetch author details."""
        try:
            return await self._request(f"/authors/{author_id}")
        except Exception as e:
            logger.warning(f"Failed to fetch author {author_id}: {e}")
            return None

    async def search_authors(self, query: str, limit: int = 10) -> List[dict]:
        """Search for authors."""
        params = {"search": query, "per-page": min(limit, OPENALEX_PAGE_SIZE)}
        data = await self._request("/authors", params)
        return data.get("results", [])


# ─── Normalizer ──────────────────────────────────────────────────────────────

class OpenAlexNormalizer:
    """
    Normalizes OpenAlex API responses into structured OpenAlexWork objects.
    Handles missing fields, aliases, and naming drift.
    """

    @staticmethod
    def normalize_work(raw: dict) -> OpenAlexWork:
        """Normalize a raw OpenAlex work response."""
        # Extract authors
        authors = []
        for authorship in raw.get("authorships", []):
            author_data = authorship.get("author", {})
            authors.append(OpenAlexAuthor(
                author_id=author_data.get("id", "").split("/")[-1],
                display_name=author_data.get("display_name", "Unknown"),
                orcid=author_data.get("orcid"),
                affiliations=[
                    inst.get("display_name", "")
                    for inst in authorship.get("institutions", [])
                ],
            ))

        # Extract concepts
        concepts = []
        for concept_data in raw.get("concepts", []):
            concepts.append(OpenAlexConcept(
                concept_id=concept_data.get("id", "").split("/")[-1],
                display_name=concept_data.get("display_name", ""),
                level=concept_data.get("level", 0),
                score=concept_data.get("score", 0.0),
                wikidata=concept_data.get("wikidata"),
            ))

        # Sort concepts by score (highest first)
        concepts.sort(key=lambda c: c.score, reverse=True)

        # Extract DOI
        doi = raw.get("doi")
        if doi:
            doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "").strip()

        # Extract open access URL
        oa_info = raw.get("open_access", {})
        oa_url = oa_info.get("oa_url")

        # Extract work ID
        work_id = raw.get("id", "").split("/")[-1]

        # Reconstruct abstract (OpenAlex stores it as inverted index)
        abstract = OpenAlexNormalizer._reconstruct_abstract(
            raw.get("abstract_inverted_index")
        )

        return OpenAlexWork(
            work_id=work_id,
            doi=doi,
            title=raw.get("title", ""),
            abstract=abstract,
            authors=authors,
            concepts=concepts,
            publication_date=raw.get("publication_date"),
            cited_by_count=raw.get("cited_by_count", 0),
            referenced_works=[
                w.split("/")[-1] for w in raw.get("referenced_works", [])
            ],
            open_access_url=oa_url,
        )

    @staticmethod
    def _reconstruct_abstract(inverted_index: Optional[Optional[dict]]) -> str:
        """Reconstruct abstract text from OpenAlex inverted index format."""
        if not inverted_index:
            return ""
        try:
            # inverted_index: {"word": [pos1, pos2, ...], ...}
            positions = []
            for word, pos_list in inverted_index.items():
                for pos in pos_list:
                    positions.append((pos, word))
            positions.sort(key=lambda x: x[0])
            return " ".join(word for _, word in positions)
        except Exception:
            return ""


# ─── Ingester ────────────────────────────────────────────────────────────────

class OpenAlexIngester:
    """
    Full ingestion pipeline: Fetch → Normalize → Chunk → Embed → Store.
    
    Integrates with existing:
    - SemanticChunker (core/semantic/chunking/)
    - EmbeddingEngine (core/semantic/embeddings/)
    - GraphStore (core/knowledge/graph/)
    """

    def __init__(
        self,
        client: Optional[OpenAlexClient] = None,
        chunker=None,
        embedder=None,
        graph_store=None,
        vector_store=None,
    ):
        self.client = client or OpenAlexClient()
        self.normalizer = OpenAlexNormalizer()
        self.chunker = chunker
        self.embedder = embedder
        self.graph_store = graph_store
        self.vector_store = vector_store
        self._seen_dois: set[str] = set()

    async def ingest_query(
        self,
        query: str,
        limit: int = 25,
        filters: Optional[dict] = None,
    ) -> List[OpenAlexWork]:
        """
        Full ingestion pipeline for a search query.
        
        Returns list of ingested OpenAlexWork objects.
        """
        logger.info(f"OpenAlex ingest: query='{query}', limit={limit}")

        # 1. Fetch
        raw_results = await self.client.search_works(query, limit=limit, filters=filters)
        logger.info(f"Fetched {len(raw_results)} raw results")

        # 2. Normalize
        works = []
        for raw in raw_results:
            try:
                work = self.normalizer.normalize_work(raw)
                # 3. Deduplicate
                if work.canonical_id not in self._seen_dois:
                    works.append(work)
                    self._seen_dois.add(work.canonical_id)
                else:
                    logger.debug(f"Skipping duplicate: {work.canonical_id}")
            except Exception as e:
                logger.warning(f"Normalization failed: {e}")
                continue

        logger.info(f"Normalized {len(works)} unique works")

        # 4. Chunk + Embed + Store (if components available)
        if self.chunker and self.embedder:
            await self._process_works(works)

        return works

    async def ingest_doi(self, doi: str) -> Optional[OpenAlexWork]:
        """Ingest a single work by DOI."""
        raw = await self.client.get_work_by_doi(doi)
        if not raw:
            return None
        work = self.normalizer.normalize_work(raw)
        if work.canonical_id not in self._seen_dois:
            self._seen_dois.add(work.canonical_id)
            if self.chunker and self.embedder:
                await self._process_work(work)
            return work
        return None

    async def _process_works(self, works: List[OpenAlexWork]):
        """Chunk, embed, and store a list of works."""
        for work in works:
            try:
                await self._process_work(work)
            except Exception as e:
                logger.error(f"Processing failed for {work.canonical_id}: {e}")

    async def _process_work(self, work: OpenAlexWork):
        """Chunk, embed, and store a single work."""
        # Prepare text for chunking
        text = f"{work.title}\n\n{work.full_text}"

        # Chunk
        if self.chunker:
            chunks = self.chunker.chunk(text, source_id=work.canonical_id)
        else:
            chunks = []

        # Embed
        if self.embedder and chunks:
            for chunk in chunks:
                chunk.embedding = self.embedder.embed(chunk.text)

        # Store in vector store
        if self.vector_store and chunks:
            for chunk in chunks:
                if chunk.embedding:
                    self.vector_store.upsert(
                        id=chunk.chunk_id,
                        vector=chunk.embedding,
                        metadata={
                            "source": "openalex",
                            "canonical_id": work.canonical_id,
                            "title": work.title,
                            "tags": work.semantic_tags,
                        },
                    )

        # Store in knowledge graph
        if self.graph_store:
            self.graph_store.add_entity(
                entity_id=work.canonical_id,
                entity_type="research_work",
                name=work.title,
                description=work.abstract[:500] if work.abstract else "",
                metadata=work.to_dict(),
            )
            # Add author entities and relationships
            for author in work.authors:
                self.graph_store.add_entity(
                    entity_id=author.author_id,
                    entity_type="author",
                    name=author.display_name,
                )
                self.graph_store.add_edge(
                    source=author.author_id,
                    target=work.canonical_id,
                    relation="authored",
                    confidence=1.0,
                )

    async def close(self):
        await self.client.close()


# ─── Convenience Functions ───────────────────────────────────────────────────

async def search_and_ingest(
    query: str,
    limit: int = 25,
    filters: Optional[dict] = None,
) -> List[OpenAlexWork]:
    """One-shot search and ingest."""
    ingester = OpenAlexIngester()
    try:
        return await ingester.ingest_query(query, limit=limit, filters=filters)
    finally:
        await ingester.close()


async def ingest_doi(doi: str) -> Optional[OpenAlexWork]:
    """One-shot DOI ingest."""
    ingester = OpenAlexIngester()
    try:
        return await ingester.ingest_doi(doi)
    finally:
        await ingester.close()
