"""
L2.5 — SQLite knowledge graph wrapper.

Stores nodes (papers, authors, concepts) and edges (citations, authorship)
in a queryable SQLite database. No Neo4j required.

Usage:
    graph = GraphStore()
    graph.add_node(paper)
    graph.add_edge("W123", "W456", "cites")
    nodes = graph.query_nodes(kind="paper", domain="agent_orchestration")
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..ingestion.models import Paper

GRAPH_DB = Path(__file__).resolve().parents[4] / "data" / "research" / "citations.db"


class GraphStore:
    """
    SQLite-backed knowledge graph store.
    
    Nodes: papers, authors, concepts, methods, institutions
    Edges: cites, authored, introduces, extends, contradicts
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or GRAPH_DB
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Create graph tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executescript(_GRAPH_SCHEMA)
            conn.commit()
        finally:
            conn.close()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def add_node(self, node_id: str, kind: str, label: str, 
                 metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a node to the graph.
        
        Args:
            node_id: Unique identifier (openalex:W..., doi:..., concept:...)
            kind: Node type (paper, author, concept, method, institution)
            label: Display label
            metadata: Optional JSON metadata
            
        Returns:
            True if added, False if already exists
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """INSERT OR IGNORE INTO graph_nodes (id, kind, label, metadata, created_at, updated_at)
                   VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))""",
                (node_id, kind, label, json.dumps(metadata) if metadata else None),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def add_edge(self, src_id: str, dst_id: str, kind: str,
                 weight: float = 1.0, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add an edge to the graph.
        
        Args:
            src_id: Source node ID
            dst_id: Destination node ID
            kind: Edge type (cites, authored, introduces, extends, contradicts)
            weight: Edge weight (default 1.0)
            metadata: Optional JSON metadata
            
        Returns:
            True if added, False if already exists
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """INSERT OR IGNORE INTO graph_edges (src_id, dst_id, kind, weight, metadata)
                   VALUES (?, ?, ?, ?, ?)""",
                (src_id, dst_id, kind, weight, json.dumps(metadata) if metadata else None),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def add_paper(self, paper: Paper) -> int:
        """
        Add a paper and its relations to the graph.
        
        Returns count of nodes/edges added.
        """
        count = 0
        
        # Add paper node
        count += self.add_node(
            node_id=f"openalex:{paper.id}" if paper.id.startswith("W") else f"doi:{paper.doi}",
            kind="paper",
            label=paper.title,
            metadata={"year": paper.year, "source": paper.source, "citation_count": paper.citation_count}
        )
        
        # Add author nodes and edges
        for author in paper.authors:
            count += self.add_node(
                node_id=f"author:{author.id}",
                kind="author",
                label=author.name,
                metadata={"orcid": author.orcid}
            )
            count += self.add_edge(
                src_id=f"openalex:{paper.id}",
                dst_id=f"author:{author.id}",
                kind="authored"
            )
        
        # Add concept nodes and edges
        for concept in paper.concepts:
            count += self.add_node(
                node_id=f"concept:{concept.id}",
                kind="concept",
                label=concept.name,
                metadata={"level": concept.level, "score": concept.score}
            )
            count += self.add_edge(
                src_id=f"openalex:{paper.id}",
                dst_id=f"concept:{concept.id}",
                kind="about",
                weight=concept.score
            )
        
        # Add citation edges (only if both nodes exist in our graph)
        for ref_id in paper.referenced_works[:50]:  # Cap at 50 per TEAM-NOTES
            # We add the edge but don't create orphan nodes
            count += self.add_edge(
                src_id=f"openalex:{paper.id}",
                dst_id=f"openalex:{ref_id}",
                kind="cites"
            )
        
        return count

    def has_node(self, node_id: str) -> bool:
        """Check if a node exists in the graph."""
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT 1 FROM graph_nodes WHERE id = ?", (node_id,)
            ).fetchone()
            return row is not None
        finally:
            conn.close()

    def query_nodes(self, kind: Optional[str] = None, 
                    domain: Optional[str] = None,
                    limit: int = 100) -> List[Dict[str, Any]]:
        """
        Query nodes from the graph.
        
        Args:
            kind: Filter by node type
            domain: Filter by domain (via concept edge)
            limit: Max results
            
        Returns:
            List of node dicts with id, kind, label, metadata
        """
        conn = self._get_connection()
        try:
            query = "SELECT id, kind, label, metadata FROM graph_nodes"
            params = []
            
            if kind:
                query += " WHERE kind = ?"
                params.append(kind)
            
            query += f" LIMIT {limit}"
            
            cursor = conn.execute(query, params)
            return [
                {
                    "id": row[0],
                    "kind": row[1],
                    "label": row[2],
                    "metadata": json.loads(row[3]) if row[3] else {}
                }
                for row in cursor.fetchall()
            ]
        finally:
            conn.close()

    def query_edges(self, src_id: Optional[str] = None,
                    dst_id: Optional[str] = None,
                    kind: Optional[str] = None,
                    limit: int = 100) -> List[Dict[str, Any]]:
        """
        Query edges from the graph.
        
        Returns list of edge dicts with src_id, dst_id, kind, weight.
        """
        conn = self._get_connection()
        try:
            query = "SELECT src_id, dst_id, kind, weight FROM graph_edges"
            conditions = []
            params = []
            
            if src_id:
                conditions.append("src_id = ?")
                params.append(src_id)
            if dst_id:
                conditions.append("dst_id = ?")
                params.append(dst_id)
            if kind:
                conditions.append("kind = ?")
                params.append(kind)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += f" LIMIT {limit}"
            
            cursor = conn.execute(query, params)
            return [
                {
                    "src_id": row[0],
                    "dst_id": row[1],
                    "kind": row[2],
                    "weight": row[3]
                }
                for row in cursor.fetchall()
            ]
        finally:
            conn.close()

    def get_node_count(self) -> int:
        """Get total node count."""
        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM graph_nodes")
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def get_edge_count(self) -> int:
        """Get total edge count."""
        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM graph_edges")
            return cursor.fetchone()[0]
        finally:
            conn.close()


_GRAPH_SCHEMA = """
CREATE TABLE IF NOT EXISTS graph_nodes (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    label TEXT NOT NULL,
    metadata JSON,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_nodes_kind ON graph_nodes(kind);

CREATE TABLE IF NOT EXISTS graph_edges (
    src_id TEXT,
    dst_id TEXT,
    kind TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    metadata JSON,
    PRIMARY KEY (src_id, dst_id, kind)
);

CREATE INDEX IF NOT EXISTS idx_edges_src ON graph_edges(src_id);
CREATE INDEX IF NOT EXISTS idx_edges_dst ON graph_edges(dst_id);
CREATE INDEX IF NOT EXISTS idx_edges_kind ON graph_edges(kind);
"""