"""
L3.4 — Finding evaluator.

Scores research findings on confidence (0-1) from:
- Source quality
- Citation count
- Recency
- LLM self-rating (optional)

Threshold: 0.6 (configurable). Below → discarded.

Usage:
    evaluator = FindingEvaluator()
    score = evaluator.evaluate(finding)
    # Returns confidence score 0-1
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Evaluation thresholds
DEFAULT_CONFIDENCE_THRESHOLD = 0.6
MIN_CITATIONS_FOR_HIGH_CONFIDENCE = 10
MAX_PAPER_AGE_YEARS = 5


class FindingEvaluator:
    """
    Evaluates research findings for confidence scoring.
    
    Multi-factor scoring:
    - Source quality (0-0.3): OpenAlex > arXiv > S2
    - Citation count (0-0.3): More citations = higher confidence
    - Recency (0.2): Newer papers score higher
    - LLM self-rating (0.2): Optional LLM verification
    """

    def __init__(self, threshold: float = DEFAULT_CONFIDENCE_THRESHOLD):
        self.threshold = threshold

    def evaluate(self, finding: Any, context: Optional[Dict[str, Any]] = None) -> float:
        """
        Evaluate a research finding and return confidence score.
        
        Args:
            finding: Finding dict with source, citation_count, year, etc.
                     OR a Paper object (context must be provided)
            context: Optional dict with additional context (summary, etc.)
            
        Returns:
            Confidence score between 0 and 1
        """
        # Handle Paper object passed as finding
        if not isinstance(finding, dict):
            finding = {
                "paper_id": getattr(finding, 'id', 'unknown'),
                "source": getattr(finding, 'source', 'test'),
                "citation_count": getattr(finding, 'citation_count', 0),
                "year": getattr(finding, 'year', 2024),
            }
        scores = []
        
        # Source quality score (0-0.3)
        source_score = self._score_source(finding.get("source", ""))
        scores.append(("source", source_score, 0.3))
        
        # Citation count score (0-0.3)
        citation_score = self._score_citations(finding.get("citation_count", 0))
        scores.append(("citations", citation_score, 0.3))
        
        # Recency score (0-0.2)
        recency_score = self._score_recency(finding.get("year", 0))
        scores.append(("recency", recency_score, 0.2))
        
        # LLM self-rating (0-0.2) — placeholder
        llm_score = finding.get("llm_confidence", 0.5)
        scores.append(("llm", llm_score, 0.2))
        
        # Weighted sum
        total = sum(score * weight for _, score, weight in scores)
        
        logger.debug(
            f"Evaluation: {finding.get('paper_id', 'unknown')} = {total:.2f} "
            f"(threshold: {self.threshold})"
        )
        
        return round(min(1.0, max(0.0, total)), 3)

    def is_acceptable(self, finding: Dict[str, Any]) -> bool:
        """Check if finding meets confidence threshold."""
        return self.evaluate(finding) >= self.threshold

    def _score_source(self, source: str) -> float:
        """Score source quality (0-1)."""
        source_scores = {
            "openalex": 1.0,
            "arxiv": 0.8,
            "s2": 0.7,
        }
        return source_scores.get(source.lower(), 0.5)

    def _score_citations(self, citation_count: int) -> float:
        """Score citation count (0-1)."""
        if citation_count >= MIN_CITATIONS_FOR_HIGH_CONFIDENCE:
            return 1.0
        if citation_count <= 0:
            return 0.3
        return min(1.0, citation_count / MIN_CITATIONS_FOR_HIGH_CONFIDENCE)

    def _score_recency(self, year: int) -> float:
        """Score recency (0-1)."""
        current_year = datetime.now(timezone.utc).year
        age = current_year - year
        
        if age <= 0:
            return 1.0
        if age >= MAX_PAPER_AGE_YEARS:
            return 0.3
        return 1.0 - (age / MAX_PAPER_AGE_YEARS) * 0.7

    def get_evaluation_report(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed evaluation report for a finding."""
        source_score = self._score_source(finding.get("source", ""))
        citation_score = self._score_citations(finding.get("citation_count", 0))
        recency_score = self._score_recency(finding.get("year", 0))
        llm_score = finding.get("llm_confidence", 0.5)
        
        total = source_score * 0.3 + citation_score * 0.3 + recency_score * 0.2 + llm_score * 0.2
        
        return {
            "paper_id": finding.get("paper_id", "unknown"),
            "total_confidence": round(total, 3),
            "threshold": self.threshold,
            "acceptable": total >= self.threshold,
            "breakdown": {
                "source": {"score": source_score, "weight": 0.3, "weighted": round(source_score * 0.3, 3)},
                "citations": {"score": citation_score, "weight": 0.3, "weighted": round(citation_score * 0.3, 3)},
                "recency": {"score": recency_score, "weight": 0.2, "weighted": round(recency_score * 0.2, 3)},
                "llm": {"score": llm_score, "weight": 0.2, "weighted": round(llm_score * 0.2, 3)},
            },
        }