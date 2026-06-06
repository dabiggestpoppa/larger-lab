"""
Normalized paper schema for the research mesh.

All source clients (OpenAlex, arXiv, S2) return Paper objects in this format.
This is the canonical internal representation — source-specific parsing happens
in each client, not here.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional


class PaperStatus(str, Enum):
    PENDING = "pending"
    DISTILLED = "distilled"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class Author:
    id: str = ""                            # OpenAlex author ID or "unknown"
    name: str = ""
    orcid: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"author_{uuid.uuid4().hex[:12]}"


@dataclass
class Concept:
    id: str = ""                            # OpenAlex concept ID or slug
    name: str = ""
    score: float = 0.0                      # Relevance score (0-1)
    level: int = 0                         # Hierarchy level (0 = top)

    def __post_init__(self):
        if not self.id:
            self.id = f"concept_{self.name.lower().replace(' ', '_')}"


@dataclass
class Paper:
    """Canonical paper schema — all source clients return this."""

    # Identity
    id: str = ""                            # OpenAlex ID (W...) or DOI
    doi: str = ""
    title: str = ""
    abstract: str = ""

    # Metadata
    year: int = 0
    published_date: str = ""                # ISO 8601
    source: str = ""                        # 'openalex' | 'arxiv' | 's2'
    source_id: str = ""                     # Original ID from source
    url: str = ""
    pdf_url: str = ""
    language: str = "en"

    # Metrics
    citation_count: int = 0
    referenced_count: int = 0
    is_open_access: bool = False

    # Research mesh state
    operational_relevance: int = 0          # 0-5 (0 = not yet scored)
    status: PaperStatus = PaperStatus.PENDING
    distilled_at: str = ""
    vault_path: str = ""

    # Relations
    authors: List[Author] = field(default_factory=list)
    concepts: List[Concept] = field(default_factory=list)
    referenced_works: List[str] = field(default_factory=list)  # IDs of cited papers

    # Raw
    raw_json: str = ""                      # Full API response JSON

    # Timestamps
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    @property
    def first_author(self) -> str:
        return self.authors[0].name if self.authors else "unknown"

    @property
    def slug(self) -> str:
        """Filesystem-safe slug for vault notes."""
        author = self.first_author.lower().replace(" ", "_")
        title_part = "_".join(self.title.lower().split()[:5])
        return f"{author}_{title_part}"

    @property
    def is_relevant(self) -> bool:
        """Quick check: does this paper meet minimum relevance for distillation?"""
        return self.operational_relevance >= 3

    def to_sqlite_dict(self) -> dict:
        """Serialize for SQLite papers table."""
        return {
            "id": self.id,
            "doi": self.doi,
            "title": self.title,
            "abstract": self.abstract,
            "year": self.year,
            "published_date": self.published_date,
            "source": self.source,
            "source_id": self.source_id,
            "url": self.url,
            "pdf_url": self.pdf_url,
            "language": self.language,
            "citation_count": self.citation_count,
            "referenced_count": self.referenced_count,
            "is_open_access": int(self.is_open_access),
            "operational_relevance": self.operational_relevance,
            "status": self.status.value,
            "distilled_at": self.distilled_at,
            "vault_path": self.vault_path,
            "raw_json": self.raw_json,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
