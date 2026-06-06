"""
L3.1 — Knowledge gap detector.

Detects knowledge gaps using heuristics:
- Low citation density in domain
- Missing concept links
- Recent papers with no notes

Usage:
    detector = GapDetector()
    gaps = detector.find_gaps(threshold=0.4)
    # Returns list of gap dicts
"""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ..ingestion.models import Paper
from ..distillation.graph_store import GraphStore

logger = logging.getLogger(__name__)

# Gap detection thresholds
DEFAULT_THRESHOLD = 0.4
MIN_PAPERS_FOR_GAP = 5  # Need at least N papers to detect gaps
CITATION_DENSITY_THRESHOLD = 0.3  # Below this = potential gap


class GapDetector:
    """
    Detects knowledge gaps in the research mesh.
    
    Uses heuristics:
    1. Low citation density in a domain (few papers cite each other)
    2. Missing concept links (concepts with few connected papers)
    3. Recent papers with no distilled notes
    """

    def __init__(
        self,
        graph_store: Optional[GraphStore] = None,
        threshold: float = DEFAULT_THRESHOLD,
    ):
        self.graph = graph_store or GraphStore()
        self.threshold = threshold

    def find_gaps(self, papers: Optional[List[Paper]] = None) -> List[Dict[str, Any]]:
        """
        Find knowledge gaps.
        
        Args:
            papers: Optional list of papers to analyze. If None, queries from graph store.
            
        Returns:
            List of gap dicts with type, domain, confidence, description
        """
        gaps = []
        
        # Gap type 1: Low citation density by domain
        density_gaps = self._find_density_gaps(papers)
        gaps.extend(density_gaps)
        
        # Gap type 2: Missing concept links
        concept_gaps = self._find_concept_gaps(papers)
        gaps.extend(concept_gaps)
        
        # Gap type 3: Recent papers with no notes
        note_gaps = self._find_note_gaps(papers)
        gaps.extend(note_gaps)
        
        # Sort by confidence (descending)
        gaps.sort(key=lambda g: g.get("confidence", 0), reverse=True)
        
        logger.info(f"Gap detection: found {len(gaps)} gaps (threshold={self.threshold})")
        return gaps

    def _find_density_gaps(self, papers: Optional[List[Paper]]) -> List[Dict[str, Any]]:
        """Find domains with low citation density."""
        gaps = []
        
        if not papers:
            return gaps
        
        # Group papers by domain (from concepts)
        domain_papers: Dict[str, List[Paper]] = defaultdict(list)
        for paper in papers:
            for concept in paper.concepts:
                domain_papers[concept.name].append(paper)
        
        for domain, domain_paper_list in domain_papers.items():
            if len(domain_paper_list) < MIN_PAPERS_FOR_GAP:
                continue
            
            # Calculate citation density
            total_possible = len(domain_paper_list) * (len(domain_paper_list) - 1)
            if total_possible == 0:
                continue
            
            actual_citations = 0
            paper_ids = {p.id for p in domain_paper_list}
            for paper in domain_paper_list:
                for ref in paper.referenced_works:
                    if ref in paper_ids:
                        actual_citations += 1
            
            density = actual_citations / total_possible if total_possible > 0 else 0
            
            if density < CITATION_DENSITY_THRESHOLD:
                confidence = min(0.9, 1.0 - density)
                if confidence >= self.threshold:
                    gaps.append({
                        "type": "low_citation_density",
                        "domain": domain,
                        "confidence": round(confidence, 2),
                        "description": f"Low citation density in '{domain}' ({density:.2f} < {CITATION_DENSITY_THRESHOLD})",
                        "paper_count": len(domain_paper_list),
                        "actual_citations": actual_citations,
                        "suggested_query": f"recent advances in {domain.replace('_', ' ')}",
                    })
        
        return gaps

    def _find_concept_gaps(self, papers: Optional[List[Paper]]) -> List[Dict[str, Any]]:
        """Find concepts with few connected papers."""
        gaps = []
        
        if not papers:
            return gaps
        
        # Count papers per concept
        concept_counts: Counter = Counter()
        for paper in papers:
            for concept in paper.concepts:
                concept_counts[concept.name] += 1
        
        # Find concepts with very few papers
        avg_count = sum(concept_counts.values()) / len(concept_counts) if concept_counts else 0
        
        for concept, count in concept_counts.items():
            if count < avg_count * 0.3 and count < 3:
                confidence = min(0.8, 1.0 - (count / max(avg_count, 1)))
                if confidence >= self.threshold:
                    gaps.append({
                        "type": "missing_concept_links",
                        "domain": concept,
                        "confidence": round(confidence, 2),
                        "description": f"Concept '{concept}' has only {count} papers (avg: {avg_count:.1f})",
                        "paper_count": count,
                        "suggested_query": f"{concept.replace('_', ' ')} research",
                    })
        
        return gaps

    def _find_note_gaps(self, papers: Optional[List[Paper]]) -> List[Dict[str, Any]]:
        """Find recent papers with no distilled notes."""
        gaps = []
        
        if not papers:
            return gaps
        
        # Find papers without vault_path (not yet distilled)
        undistilled = [p for p in papers if not p.vault_path and p.status.value == "pending"]
        
        if undistilled:
            # Group by domain
            domain_counts: Counter = Counter()
            for paper in undistilled:
                for concept in paper.concepts:
                    domain_counts[concept.name] += 1
            
            for domain, count in domain_counts.most_common(5):
                confidence = min(0.7, count / 10.0)
                if confidence >= self.threshold:
                    gaps.append({
                        "type": "undistilled_papers",
                        "domain": domain,
                        "confidence": round(confidence, 2),
                        "description": f"{count} undistilled papers in '{domain}'",
                        "paper_count": count,
                        "suggested_query": f"distill recent {domain.replace('_', ' ')} papers",
                    })
        
        return gaps

    def get_gap_summary(self) -> Dict[str, Any]:
        """Get summary of current gap state."""
        gaps = self.find_gaps()
        return {
            "total_gaps": len(gaps),
            "by_type": dict(Counter(g["type"] for g in gaps)),
            "by_domain": dict(Counter(g["domain"] for g in gaps)),
            "top_gaps": gaps[:5],
            "threshold": self.threshold,
        }