"""
OCE Structural Memory Engine — Phase 4
=======================================
Three-layer memory system (WORK / LEARNED / KNOWLEDGE) with SQLite + FTS5
for full-text search, timeline queries, compression, and wiki export.
"""

import sqlite3
import json
import uuid
import logging
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field

logger = logging.getLogger("oce.structural_memory")

# ─── Constants ────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "structural_memory.db"

# ─── Models ───────────────────────────────────────────────────────────────────


class MemoryLayer(str, Enum):
    WORK = "WORK"
    LEARNED = "LEARNED"
    KNOWLEDGE = "KNOWLEDGE"


class MemoryEntry(BaseModel):
    entry_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    layer: MemoryLayer
    content: Dict[str, Any]
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ttl_seconds: Optional[int] = None
    source: str = "unknown"


class MemoryStats(BaseModel):
    total_entries: int
    work_count: int
    learned_count: int
    knowledge_count: int
    oldest_entry: Optional[str] = None
    newest_entry: Optional[str] = None
    db_size_bytes: int


# ─── Engine ───────────────────────────────────────────────────────────────────


class StructuralMemory:
    """Three-layer structural memory engine backed by SQLite + FTS5."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ── internal ───────────────────────────────────────────────────────────

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_entries (
                    entry_id    TEXT PRIMARY KEY,
                    layer       TEXT NOT NULL CHECK(layer IN ('WORK','LEARNED','KNOWLEDGE')),
                    content     TEXT NOT NULL,
                    tags        TEXT NOT NULL DEFAULT '[]',
                    created_at  TEXT NOT NULL,
                    updated_at  TEXT NOT NULL,
                    ttl_seconds INTEGER,
                    source      TEXT NOT NULL DEFAULT 'unknown'
                )
            """)
            # Indexes for common query patterns
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_layer ON memory_entries(layer)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_source ON memory_entries(source)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_created ON memory_entries(created_at)")
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
                    entry_id,
                    content,
                    tags,
                    layer,
                    content='memory_entries',
                    content_rowid='rowid'
                )
            """)
            # Triggers to keep FTS index in sync
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memory_ai AFTER INSERT ON memory_entries BEGIN
                    INSERT INTO memory_fts(rowid, entry_id, content, tags, layer)
                    VALUES (new.rowid, new.entry_id, new.content, new.tags, new.layer);
                END
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memory_ad AFTER DELETE ON memory_entries BEGIN
                    INSERT INTO memory_fts(memory_fts, rowid, entry_id, content, tags, layer)
                    VALUES ('delete', old.rowid, old.entry_id, old.content, old.tags, old.layer);
                END
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memory_au AFTER UPDATE ON memory_entries BEGIN
                    INSERT INTO memory_fts(memory_fts, rowid, entry_id, content, tags, layer)
                    VALUES ('delete', old.rowid, old.entry_id, old.content, old.tags, old.layer);
                    INSERT INTO memory_fts(rowid, entry_id, content, tags, layer)
                    VALUES (new.rowid, new.entry_id, new.content, new.tags, new.layer);
                END
            """)

    def _row_to_entry(self, row: sqlite3.Row) -> MemoryEntry:
        return MemoryEntry(
            entry_id=row["entry_id"],
            layer=MemoryLayer(row["layer"]),
            content=json.loads(row["content"]),
            tags=json.loads(row["tags"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            ttl_seconds=row["ttl_seconds"],
            source=row["source"],
        )

    # ── public API ─────────────────────────────────────────────────────────

    def store(self, entry: MemoryEntry) -> str:
        """Store a memory entry. Returns entry_id."""
        now = datetime.now(timezone.utc)
        entry.updated_at = now
        if entry.created_at is None:
            entry.created_at = now
        with self._conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO memory_entries
                   (entry_id, layer, content, tags, created_at, updated_at, ttl_seconds, source)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (
                    entry.entry_id,
                    entry.layer.value,
                    json.dumps(entry.content, default=str),
                    json.dumps(entry.tags),
                    entry.created_at.isoformat(),
                    entry.updated_at.isoformat(),
                    entry.ttl_seconds,
                    entry.source,
                ),
            )
        logger.info(f"Stored {entry.layer.value} entry {entry.entry_id[:8]}… from {entry.source}")
        return entry.entry_id

    def _validate_fts5_query(self, query: str) -> str:
        """Sanitize FTS5 query to prevent crashes from malformed syntax."""
        if not query.strip():
            return ""
        # Remove leading/trailing operators that cause syntax errors
        query = query.strip()
        for op in ["AND", "OR", "NOT"]:
            if query.upper().endswith(op):
                query = query[: -len(op)].strip()
        # Balance parentheses
        open_count = query.count("(")
        close_count = query.count(")")
        if open_count > close_count:
            query += ")" * (open_count - close_count)
        elif close_count > open_count:
            query = query[: -(close_count - open_count)]
        return query

    def expire(self, layer: Optional[MemoryLayer] = None) -> int:
        """Remove expired entries (where created_at + ttl_seconds < now). Returns count removed."""
        now = datetime.now(timezone.utc).isoformat()
        with self._conn() as conn:
            if layer:
                result = conn.execute(
                    """DELETE FROM memory_entries
                       WHERE layer = ? AND ttl_seconds IS NOT NULL
                       AND datetime(created_at, '+' || ttl_seconds || ' seconds') < ?""",
                    (layer.value, now),
                )
            else:
                result = conn.execute(
                    """DELETE FROM memory_entries
                       WHERE ttl_seconds IS NOT NULL
                       AND datetime(created_at, '+' || ttl_seconds || ' seconds') < ?""",
                    (now,),
                )
            deleted = result.rowcount
        if deleted:
            logger.info(f"Expired {deleted} entries" + (f" from {layer.value}" if layer else ""))
        return deleted

    def search(
        self,
        query: str = "",
        layer: Optional[MemoryLayer] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[MemoryEntry]:
        """Search memories by full-text query, layer filter, and/or tags."""
        # Expire stale entries first
        self.expire(layer)

        with self._conn() as conn:
            if query:
                # Sanitize FTS5 query
                safe_query = self._validate_fts5_query(query)
                if not safe_query:
                    return []
                sql = """
                    SELECT e.* FROM memory_entries e
                    JOIN memory_fts f ON e.rowid = f.rowid
                    WHERE memory_fts MATCH ?
                """
                params: List[Any] = [safe_query]
                if layer:
                    sql += " AND e.layer = ?"
                    params.append(layer.value)
            else:
                sql = "SELECT * FROM memory_entries WHERE 1=1"
                params = []
                if layer:
                    sql += " AND layer = ?"
                    params.append(layer.value)

            sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            try:
                rows = conn.execute(sql, params).fetchall()
            except sqlite3.OperationalError:
                logger.warning(f"FTS5 query failed, returning empty: {query}")
                return []

        entries = [self._row_to_entry(r) for r in rows]

        # Post-filter by tags if provided (SQLite FTS can't do array intersection)
        if tags:
            tag_set = set(tags)
            entries = [e for e in entries if tag_set & set(e.tags)]

        return entries

    def get_timeline(
        self,
        observer_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[MemoryEntry]:
        """Get chronological memory entries for an observer (source == observer_id)."""
        sql = "SELECT * FROM memory_entries WHERE source = ?"
        params: List[Any] = [observer_id]

        if start_time:
            sql += " AND created_at >= ?"
            params.append(start_time.isoformat())
        if end_time:
            sql += " AND created_at <= ?"
            params.append(end_time.isoformat())

        sql += " ORDER BY created_at ASC LIMIT ?"
        params.append(limit)

        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()

        return [self._row_to_entry(r) for r in rows]

    def compress(self, layer: MemoryLayer, max_entries: int = 1000) -> int:
        """
        Compress a layer by removing oldest entries beyond max_entries.
        Returns the number of entries removed.
        """
        with self._conn() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM memory_entries WHERE layer = ?",
                (layer.value,),
            ).fetchone()[0]

            if count <= max_entries:
                return 0

            to_remove = count - max_entries
            conn.execute(
                """DELETE FROM memory_entries WHERE entry_id IN (
                    SELECT entry_id FROM memory_entries
                    WHERE layer = ?
                    ORDER BY created_at ASC
                    LIMIT ?
                )""",
                (layer.value, to_remove),
            )
            logger.info(f"Compressed {layer.value}: removed {to_remove} entries")
            return to_remove

    def export_wiki(self, path: Optional[Path] = None) -> str:
        """Export KNOWLEDGE layer as markdown wiki. Returns markdown string."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM memory_entries WHERE layer = ? ORDER BY created_at ASC",
                (MemoryLayer.KNOWLEDGE.value,),
            ).fetchall()

        entries = [self._row_to_entry(r) for r in rows]

        lines = [
            "# OCE Knowledge Wiki",
            f"\n*Auto-generated {datetime.now(timezone.utc).isoformat()}*",
            f"\n**{len(entries)} entries**\n",
            "---\n",
        ]

        for entry in entries:
            title = entry.content.get("title", entry.entry_id[:8])
            lines.append(f"## {title}\n")
            if entry.tags:
                lines.append(f"**Tags:** {', '.join(entry.tags)}\n")
            body = entry.content.get("body", json.dumps(entry.content, indent=2, default=str))
            lines.append(f"{body}\n")
            lines.append(f"*Source: {entry.source} | Created: {entry.created_at.isoformat()}*\n")
            lines.append("---\n")

        markdown = "\n".join(lines)

        if path:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(markdown, encoding="utf-8")
            logger.info(f"Wiki exported to {path}")

        return markdown

    def get_stats(self) -> MemoryStats:
        """Return memory statistics."""
        with self._conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM memory_entries").fetchone()[0]
            work = conn.execute(
                "SELECT COUNT(*) FROM memory_entries WHERE layer = 'WORK'"
            ).fetchone()[0]
            learned = conn.execute(
                "SELECT COUNT(*) FROM memory_entries WHERE layer = 'LEARNED'"
            ).fetchone()[0]
            knowledge = conn.execute(
                "SELECT COUNT(*) FROM memory_entries WHERE layer = 'KNOWLEDGE'"
            ).fetchone()[0]
            oldest = conn.execute(
                "SELECT created_at FROM memory_entries ORDER BY created_at ASC LIMIT 1"
            ).fetchone()
            newest = conn.execute(
                "SELECT created_at FROM memory_entries ORDER BY created_at DESC LIMIT 1"
            ).fetchone()

        db_size = self.db_path.stat().st_size if self.db_path.exists() else 0

        return MemoryStats(
            total_entries=total,
            work_count=work,
            learned_count=learned,
            knowledge_count=knowledge,
            oldest_entry=oldest["created_at"] if oldest else None,
            newest_entry=newest["created_at"] if newest else None,
            db_size_bytes=db_size,
        )


# ─── Singleton Access ───────────────────────────────────────────────────────

_structural_memory_instance: Optional[StructuralMemory] = None


def get_structural_memory() -> StructuralMemory:
    """Get the singleton StructuralMemory instance."""
    global _structural_memory_instance
    if _structural_memory_instance is None:
        _structural_memory_instance = StructuralMemory()
    return _structural_memory_instance
