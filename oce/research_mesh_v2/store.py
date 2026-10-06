from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable, List

from .models import EvidenceRecord


SCHEMA = """
CREATE TABLE IF NOT EXISTS evidence (
    evidence_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    source_id TEXT NOT NULL,
    title TEXT NOT NULL,
    abstract TEXT NOT NULL,
    url TEXT NOT NULL,
    doi TEXT NOT NULL,
    year INTEGER,
    authors_json TEXT NOT NULL,
    citation_count INTEGER,
    acquired_at TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    raw_payload_sha256 TEXT NOT NULL,
    source_revision TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    rights_class TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_evidence_source ON evidence(source);
CREATE INDEX IF NOT EXISTS idx_evidence_doi ON evidence(doi);
CREATE INDEX IF NOT EXISTS idx_evidence_title ON evidence(title);
"""


class EvidenceStore:
    def __init__(self, path: str | Path = "data/research_mesh_v2/evidence.sqlite3"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def put_many(self, records: Iterable[EvidenceRecord]) -> int:
        count = 0
        for r in records:
            self.conn.execute(
                """INSERT OR REPLACE INTO evidence VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    r.evidence_id, r.source, r.source_id, r.title, r.abstract, r.url,
                    r.doi, r.year, json.dumps(list(r.authors)), r.citation_count,
                    r.acquired_at, r.content_sha256, r.raw_payload_sha256,
                    r.source_revision, r.parser_version, r.rights_class, 
                    "",
                )[:-1],
            )
            count += 1
        self.conn.commit()
        return count

    def search(self, query: str, limit: int = 20) -> List[dict]:
        q = f"%{query}%"
        cur = self.conn.execute(
            """SELECT evidence_id,source,source_id,title,abstract,url,doi,year,authors_json,
                      citation_count,acquired_at,content_sha256,raw_payload_sha256,
                      source_revision,parser_version,rights_class
               FROM evidence
               WHERE title LIKE ? OR abstract LIKE ?
               ORDER BY COALESCE(citation_count,0) DESC, year DESC
               LIMIT ?""",
            (q, q, limit),
        )
        cols = [d[0] for d in cur.description]
        rows = []
        for row in cur.fetchall():
            item = dict(zip(cols, row))
            item["authors"] = json.loads(item.pop("authors_json"))
            rows.append(item)
        return rows
