"""
Local cache + dedup layer for the research mesh.

All paper writes go through this layer. Dedup is a write-time gate.
Primary key: DOI (universal). Fallback: fuzzy match on title+author+year.
Daily write cap enforced to prevent vault pollution.
"""

from __future__ import annotations

import difflib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from .models import Paper, PaperStatus

# Daily write cap (hard limit per TEAM-NOTES §0)
DAILY_WRITE_CAP = 200

# Fuzzy match threshold for dedup fallback (higher = stricter)
FUZZY_MATCH_THRESHOLD = 0.98

# Database paths
PAPERS_DB = Path(__file__).parent.parent.parent.parent / "data" / "research" / "papers.db"


class CacheError(Exception):
    """Raised when cache operations fail."""
    pass


class DailyCapExceeded(CacheError):
    """Raised when daily write cap is exceeded."""
    pass


class Cache:
    """
    SQLite-backed cache with dedup and daily write cap enforcement.
    
    All source clients write through this layer. Dedup happens at write time.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or PAPERS_DB
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Create tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript(_SCHEMA)
            conn.commit()
        finally:
            conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _count_today_writes(self) -> int:
        """Count papers written today (UTC)."""
        conn = self._get_connection()
        try:
            # SQLite date() extracts date portion from ISO timestamp
            cursor = conn.execute(
                "SELECT COUNT(*) FROM papers WHERE date(created_at) = date('now')"
            )
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def _fuzzy_match_exists(self, paper: Paper) -> bool:
        """Check if paper exists via fuzzy title+author+year match."""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT title, year FROM papers"
            )
            for row in cursor.fetchall():
                existing_title, existing_year = row
                ratio = difflib.SequenceMatcher(
                    None, paper.title.lower(), existing_title.lower()
                ).ratio()
                if ratio >= FUZZY_MATCH_THRESHOLD and paper.year == existing_year:
                    return True
            return False
        finally:
            conn.close()

    def exists(self, paper: Paper) -> bool:
        """
        Check if paper already exists in cache.
        
        Primary: DOI match (universal).
        Fallback: fuzzy title+author+year match.
        """
        conn = self._get_connection()
        try:
            # DOI check (primary)
            if paper.doi:
                cursor = conn.execute(
                    "SELECT 1 FROM papers WHERE doi = ?",
                    (paper.doi,)
                )
                if cursor.fetchone():
                    return True

            # OpenAlex ID check
            if paper.id.startswith("W"):
                cursor = conn.execute(
                    "SELECT 1 FROM papers WHERE id = ?",
                    (paper.id,)
                )
                if cursor.fetchone():
                    return True

            # Fuzzy match (fallback)
            return self._fuzzy_match_exists(paper)
        finally:
            conn.close()

    def write(self, paper: Paper) -> Tuple[bool, str]:
        """
        Write paper to cache with dedup and daily cap enforcement.
        
        Returns: (success, message)
        - success=True means paper was written (new)
        - success=False means paper was skipped (duplicate or cap exceeded)
        """
        # Check daily cap first
        today_count = self._count_today_writes()
        if today_count >= DAILY_WRITE_CAP:
            raise DailyCapExceeded(
                f"Daily write cap ({DAILY_WRITE_CAP}) exceeded. "
                f"Today's count: {today_count}"
            )

        # Check dedup
        if self.exists(paper):
            return False, f"Paper already exists: {paper.title[:50]}..."

        # Write paper
        conn = self._get_connection()
        try:
            data = paper.to_sqlite_dict()
            conn.execute(
                """INSERT INTO papers 
                   (id, doi, title, abstract, year, published_date, source, 
                    source_id, url, pdf_url, language, citation_count, 
                    referenced_count, is_open_access, operational_relevance, 
                    status, distilled_at, vault_path, raw_json, created_at, updated_at)
                   VALUES 
                   (:id, :doi, :title, :abstract, :year, :published_date, :source,
                    :source_id, :url, :pdf_url, :language, :citation_count,
                    :referenced_count, :is_open_access, :operational_relevance,
                    :status, :distilled_at, :vault_path, :raw_json, :created_at, :updated_at)""",
                data
            )
            conn.commit()
            return True, f"Written: {paper.title[:50]}..."
        except sqlite3.Error as e:
            return False, f"Write error: {e}"
        finally:
            conn.close()

    def write_batch(self, papers: List[Paper]) -> Tuple[int, int, List[str]]:
        """
        Write batch of papers with dedup and daily cap enforcement.
        
        Returns: (written_count, skipped_count, messages)
        """
        written = 0
        skipped = 0
        messages = []

        for paper in papers:
            try:
                success, msg = self.write(paper)
                if success:
                    written += 1
                else:
                    skipped += 1
                messages.append(msg)
            except DailyCapExceeded as e:
                messages.append(str(e))
                # Stop processing - cap exceeded
                break

        return written, skipped, messages

    def get_paper(self, paper_id: str) -> Optional[Paper]:
        """Retrieve a paper by ID."""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM papers WHERE id = ?",
                (paper_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None

            # Map row to Paper object
            columns = [desc[0] for desc in cursor.description]
            data = dict(zip(columns, row))
            return Paper(
                id=data["id"],
                doi=data["doi"],
                title=data["title"],
                abstract=data["abstract"],
                year=data["year"],
                published_date=data["published_date"],
                source=data["source"],
                source_id=data["source_id"],
                url=data["url"],
                pdf_url=data["pdf_url"],
                language=data["language"],
                citation_count=data["citation_count"],
                referenced_count=data["referenced_count"],
                is_open_access=bool(data["is_open_access"]),
                operational_relevance=data["operational_relevance"],
                status=PaperStatus(data["status"]),
                distilled_at=data["distilled_at"],
                vault_path=data["vault_path"],
                raw_json=data["raw_json"],
                created_at=data["created_at"],
                updated_at=data["updated_at"],
            )
        finally:
            conn.close()

    def list_papers(
        self, 
        source: Optional[str] = None, 
        limit: int = 100
    ) -> List[Paper]:
        """List papers, optionally filtered by source."""
        conn = self._get_connection()
        try:
            if source:
                cursor = conn.execute(
                    "SELECT * FROM papers WHERE source = ? ORDER BY created_at DESC LIMIT ?",
                    (source, limit)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM papers ORDER BY created_at DESC LIMIT ?",
                    (limit,)
                )
            return [self._row_to_paper(row, cursor) for row in cursor.fetchall()]
        finally:
            conn.close()

    def _row_to_paper(self, row: tuple, cursor: sqlite3.Cursor) -> Paper:
        """Convert a database row to a Paper object."""
        columns = [desc[0] for desc in cursor.description]
        data = dict(zip(columns, row))
        return Paper(
            id=data["id"],
            doi=data["doi"],
            title=data["title"],
            abstract=data["abstract"],
            year=data["year"],
            published_date=data["published_date"],
            source=data["source"],
            source_id=data["source_id"],
            url=data["url"],
            pdf_url=data["pdf_url"],
            language=data["language"],
            citation_count=data["citation_count"],
            referenced_count=data["referenced_count"],
            is_open_access=bool(data["is_open_access"]),
            operational_relevance=data["operational_relevance"],
            status=PaperStatus(data["status"]),
            distilled_at=data["distilled_at"],
            vault_path=data["vault_path"],
            raw_json=data["raw_json"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )

    def log_ingestion(
        self, 
        source: str, 
        query: str, 
        papers_found: int, 
        papers_new: int, 
        papers_dup: int, 
        errors: int, 
        duration_seconds: float
    ) -> None:
        """Log ingestion run to ingestion_log table."""
        conn = self._get_connection()
        try:
            conn.execute(
                """INSERT INTO ingestion_log 
                   (source, query, papers_found, papers_new, papers_dup, errors, duration_seconds)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (source, query, papers_found, papers_new, papers_dup, errors, duration_seconds)
            )
            conn.commit()
        finally:
            conn.close()


# Schema for papers table (subset of full schema.sql)
_SCHEMA = """
CREATE TABLE IF NOT EXISTS papers (
    id TEXT PRIMARY KEY,
    doi TEXT,
    title TEXT NOT NULL,
    abstract TEXT,
    year INTEGER,
    published_date TEXT,
    source TEXT NOT NULL,
    source_id TEXT,
    url TEXT,
    pdf_url TEXT,
    language TEXT DEFAULT 'en',
    citation_count INTEGER DEFAULT 0,
    referenced_count INTEGER DEFAULT 0,
    is_open_access INTEGER DEFAULT 0,
    operational_relevance INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    distilled_at TEXT,
    vault_path TEXT,
    raw_json TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_papers_doi ON papers(doi);
CREATE INDEX IF NOT EXISTS idx_papers_source ON papers(source);
CREATE INDEX IF NOT EXISTS idx_papers_year ON papers(year);
CREATE INDEX IF NOT EXISTS idx_papers_status ON papers(status);
CREATE INDEX IF NOT EXISTS idx_papers_relevance ON papers(operational_relevance);

CREATE TABLE IF NOT EXISTS ingestion_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    query TEXT,
    papers_found INTEGER DEFAULT 0,
    papers_new INTEGER DEFAULT 0,
    papers_dup INTEGER DEFAULT 0,
    errors INTEGER DEFAULT 0,
    duration_seconds REAL,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS daily_caps (
    date TEXT PRIMARY KEY,
    vault_writes INTEGER DEFAULT 0,
    llm_tokens_input INTEGER DEFAULT 0,
    llm_tokens_output INTEGER DEFAULT 0,
    llm_cost_usd REAL DEFAULT 0.0,
    papers_ingested INTEGER DEFAULT 0,
    papers_distilled INTEGER DEFAULT 0,
    agents_spawned INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT
);
"""


# Singleton for convenience
_cache: Optional[Cache] = None


def get_cache() -> Cache:
    """Get or create the singleton cache instance."""
    global _cache
    if _cache is None:
        _cache = Cache()
    return _cache