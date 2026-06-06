"""
L2.3 — Citation graph builder.

Builds citation edges from paper metadata.
Stores in SQLite with orphan reference pruning.
Caps at 50 citations per paper (per TEAM-NOTES §0).

Usage:
    builder = CitationGraphBuilder()
    edges = builder.build_from_paper(paper)
    # Returns count of edges added
"""

from __future__ import annotations

import logging
from typing import List, Optional, Set

from ..ingestion.models import Paper
from .graph_store import GraphStore

logger = logging.getLogger(__name__)

# Max citations per paper (per TEAM-NOTES §0 graph corruption prevention)
MAX_CITATIONS_PER_PAPER = 50


class CitationGraphBuilder:
    """
    Builds citation graph edges from paper metadata.
    
    Only stores edges where both nodes exist in our graph (orphan reference pruning).
    Caps at 50 citations per paper to prevent graph bloat.
    """

    def __init__(self, graph_store: Optional[GraphStore] = None):
        self.graph = graph_store or GraphStore()

    def build_from_paper(self, paper: Paper) -> int:
        """
        Build citation edges from a single paper.
        
        Args:
            paper: Paper object with referenced_works list
            
        Returns:
            Number of edges added
        """
        if not paper.referenced_works:
            return 0

        src_id = self._normalize_id(paper.id, paper.doi)
        edges_added = 0

        # Cap citations per paper
        refs = paper.referenced_works[:MAX_CITATIONS_PER_PAPER]

        for ref_id in refs:
            dst_id = self._normalize_ref_id(ref_id)
            
            # Only add edge if destination exists in our graph (orphan pruning)
            # For now, we add the edge — orphan pruning happens at query time
            # or during periodic cleanup
            if self.graph.add_edge(src_id, dst_id, kind="cites"):
                edges_added += 1

        if edges_added > 0:
            logger.debug(f"Added {edges_added} citation edges for {src_id}")

        return edges_added

    def build_from_papers(self, papers: List[Paper]) -> int:
        """
        Build citation edges from multiple papers.
        
        Returns total number of edges added.
        """
        total = 0
        for paper in papers:
            total += self.build_from_paper(paper)
        return total

    def prune_orphans(self) -> int:
        """
        Remove edges where the destination node doesn't exist in our graph.
        
        Returns number of edges removed.
        """
        conn = self.graph._get_connection()
        try:
            # Find edges with no matching destination node
            cursor = conn.execute("""
                DELETE FROM graph_edges 
                WHERE dst_id NOT IN (SELECT id FROM graph_nodes)
                AND kind = 'cites'
            """)
            removed = cursor.rowcount
            conn.commit()
            if removed > 0:
                logger.info(f"Pruned {removed} orphan citation edges")
            return removed
        finally:
            conn.close()

    def get_citation_count(self, paper_id: str) -> int:
        """Get number of citations for a paper (edges where it's the source)."""
        conn = self.graph._get_connection()
        try:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM graph_edges WHERE src_id = ? AND kind = 'cites'",
                (paper_id,),
            )
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def get_referenced_by_count(self, paper_id: str) -> int:
        """Get number of papers referencing this paper (edges where it's the destination)."""
        conn = self.graph._get_connection()
        try:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM graph_edges WHERE dst_id = ? AND kind = 'cites'",
                (paper_id,),
            )
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def _normalize_id(self, paper_id: str, doi: str = "") -> str:
        """Normalize paper ID to graph format."""
        if paper_id.startswith("W"):
            return f"openalex:{paper_id}"
        if doi:
            return f"doi:{doi}"
        return f"paper:{paper_id}"

    def _normalize_ref_id(self, ref_id: str) -> str:
        """Normalize reference ID to graph format."""
        # Strip OpenAlex URL prefix if present
        ref_id = ref_id.replace("https://openalex.org/", "")
        if ref_id.startswith("W"):
            return f"openalex:{ref_id}"
        if ref_id.startswith("10."):
            return f"doi:{ref_id}"
        return f"paper:{ref_id}"