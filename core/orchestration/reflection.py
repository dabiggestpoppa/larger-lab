"""
Phase 1.6.6 — Reflection Engine

Self-correction loops: verify outputs, detect errors, replan.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.reflection")


@dataclass
class ReflectionResult:
    """Result of a reflection/review pass."""
    passed: bool = True
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    confidence: float = 1.0
    needs_retry: bool = False


class ReflectionEngine:
    """
    Self-correction through reflection loops.
    
    After an agent produces output, this engine:
    1. Verifies claims against sources
    2. Detects unsupported assertions
    3. Checks logical consistency
    4. Suggests improvements
    5. Triggers retry if needed
    """

    def __init__(self):
        self._reflection_count = 0
        self._max_reflections = 3

    def reflect(
        self,
        output: str,
        sources: Optional[List[str]] = None,
        query: str = "",
    ) -> ReflectionResult:
        """
        Perform reflection on an agent output.
        
        Args:
            output: The agent's output to review
            sources: Original source materials
            query: The original query/task
            
        Returns:
            ReflectionResult with issues and suggestions
        """
        result = ReflectionResult()
        self._reflection_count += 1

        # Check 1: Empty or too short output
        if not output or len(output.strip()) < 50:
            result.issues.append("Output is empty or too short")
            result.needs_retry = True

        # Check 2: Unsupported claims (heuristic)
        if output and self._has_unsupported_claims(output, sources or []):
            result.issues.append("Potential unsupported claims detected")
            result.suggestions.append("Add citations to key claims")

        # Check 3: Logical consistency
        if output and self._has_contradictions(output):
            result.issues.append("Internal contradictions detected")
            result.suggestions.append("Review and resolve conflicting statements")

        # Check 4: Relevance to query
        if query and output and not self._is_relevant(output, query):
            result.issues.append("Output may not be relevant to the query")
            result.suggestions.append("Refocus on the original research question")

        # Check 5: Confidence calibration
        if result.issues:
            result.confidence = max(0.1, 1.0 - (len(result.issues) * 0.2))
            if self._reflection_count < self._max_reflections:
                result.needs_retry = True
            # Fail if any critical issues (empty output, contradictions)
            critical = ["empty or too short", "contradictions detected"]
            has_critical = any(c in i for c in critical for i in result.issues)
            result.passed = not has_critical and len(result.issues) <= 1
        else:
            result.confidence = 0.9

        logger.info(
            f"Reflection #{self._reflection_count}: "
            f"{'PASS' if result.passed else 'FAIL'} "
            f"({len(result.issues)} issues, confidence={result.confidence:.2f})"
        )

        return result

    def _has_unsupported_claims(self, output: str, sources: List[str]) -> bool:
        """Heuristic: detect claims that lack source support."""
        # Look for strong assertion words without nearby citations
        import re
        claim_patterns = [
            r'\b(proves?|demonstrates?|shows?|confirms?|establishes?)\b',
            r'\b(significantly|substantially|clearly|definitely)\b',
        ]
        citation_pattern = r'\[.*?\]|\(.*?\d{4}.*?\)'

        has_claims = any(re.search(p, output, re.IGNORECASE) for p in claim_patterns)
        has_citations = bool(re.search(citation_pattern, output))

        # If strong claims but few citations, flag it
        if has_claims and not has_citations:
            return True
        return False

    def _has_contradictions(self, output: str) -> bool:
        """Heuristic: detect internal contradictions."""
        import re
        # Look for contradictory statement pairs
        negation_pairs = [
            (r'\b(is|are|was|were)\b', r'\b(is not|are not|was not|were not)\b'),
            (r'\b(increases?|rises?|grows?)\b', r'\b(decreases?|falls?|declines?)\b'),
        ]
        for pos_pattern, neg_pattern in negation_pairs:
            pos_matches = re.findall(pos_pattern, output, re.IGNORECASE)
            neg_matches = re.findall(neg_pattern, output, re.IGNORECASE)
            if pos_matches and neg_matches:
                # Check if they're about the same topic (simplified)
                return True
        return False

    def _is_relevant(self, output: str, query: str) -> bool:
        """Heuristic: check if output is relevant to query."""
        # Extract key words from query
        import re
        query_words = set(re.findall(r'\b\w{4,}\b', query.lower()))
        output_words = set(re.findall(r'\b\w{4,}\b', output.lower()))

        if not query_words:
            return True

        overlap = query_words & output_words
        relevance = len(overlap) / len(query_words)
        return relevance > 0.2  # At least 20% word overlap

    def reset(self):
        """Reset reflection counter."""
        self._reflection_count = 0
