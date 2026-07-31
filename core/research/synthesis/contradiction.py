"""
Phase 1.5 — Contradiction Detector

Detects conflicting claims across sources.
Scores contradiction severity.
Suggests resolution strategies.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.contradiction")


@dataclass
class Contradiction:
    """A detected contradiction between sources."""
    contradiction_id: str = ""
    claim_a: str = ""
    claim_b: str = ""
    source_a: str = ""
    source_b: str = ""
    severity: str = "low"  # low, medium, high
    similarity: float = 0.0
    resolution_hint: str = ""

    def to_dict(self) -> dict:
        return {
            "claim_a": self.claim_a[:200],
            "claim_b": self.claim_b[:200],
            "source_a": self.source_a,
            "source_b": self.source_b,
            "severity": self.severity,
            "similarity": self.similarity,
            "resolution_hint": self.resolution_hint,
        }


class ContradictionDetector:
    """
    Detects conflicting claims across sources.
    
    Usage:
        detector = ContradictionDetector(embedding_engine=embedder)
        contradictions = detector.detect(claims_list)
    """

    NEGATION_WORDS = {
        "not", "no", "never", "cannot", "doesn't", "don't", "won't",
        "isn't", "aren't", "wasn't", "weren't", "neither", "nor",
        "contrary", "opposite", "refute", "reject", "deny", "disprove",
    }

    CONTRAST_MARKERS = {
        "however", "but", "although", "despite", "nevertheless",
        "on the other hand", "in contrast", "conversely", "whereas",
    }

    def __init__(self, embedding_engine=None):
        self.embedding_engine = embedding_engine

    def detect(self, claims: List[Dict[str, Any]]) -> List[Contradiction]:
        """
        Detect contradictions in a list of claims.
        
        Each claim dict should have:
        - text: the claim text
        - source: source document ID
        """
        contradictions = []

        for i, claim_a in enumerate(claims):
            for j, claim_b in enumerate(claims):
                if i >= j:
                    continue

                text_a = claim_a.get("text", "").lower()
                text_b = claim_b.get("text", "").lower()

                # Check for negation-based contradictions
                has_neg_a = any(w in text_a for w in self.NEGATION_WORDS)
                has_neg_b = any(w in text_b for w in self.NEGATION_WORDS)

                if has_neg_a != has_neg_b:
                    # One has negation, the other doesn't
                    similarity = self._compute_similarity(text_a, text_b)
                    if similarity > 0.1:
                        severity = self._score_severity(similarity, text_a, text_b)
                        contradictions.append(Contradiction(
                            contradiction_id=f"ctr-{len(contradictions)+1}",
                            claim_a=claim_a.get("text", "")[:200],
                            claim_b=claim_b.get("text", "")[:200],
                            source_a=claim_a.get("source", ""),
                            source_b=claim_b.get("source", ""),
                            severity=severity,
                            similarity=similarity,
                            resolution_hint=self._suggest_resolution(text_a, text_b),
                        ))

        logger.info(f"Detected {len(contradictions)} contradictions")
        return contradictions

    def _compute_similarity(self, text_a: str, text_b: str) -> float:
        """Compute similarity between two texts."""
        if self.embedding_engine:
            try:
                emb_a = self.embedding_engine.embed(text_a)
                emb_b = self.embedding_engine.embed(text_b)
                return self._cosine_similarity(emb_a, emb_b)
            except Exception:
                pass

        # Fallback: Jaccard similarity
        words_a = set(text_a.split())
        words_b = set(text_b.split())
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        union = words_a | words_b
        return len(intersection) / len(union)

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _score_severity(self, similarity: float, text_a: str, text_b: str) -> str:
        """Score contradiction severity."""
        # High similarity + negation = high severity
        if similarity > 0.7:
            return "high"
        elif similarity > 0.5:
            return "medium"
        return "low"

    def _suggest_resolution(self, text_a: str, text_b: str) -> str:
        """Suggest resolution strategy."""
        # Check for temporal differences
        has_dates = any(char.isdigit() for char in text_a + text_b)
        if has_dates:
            return "Check if claims refer to different time periods"

        # Check for scope differences
        scope_words = ["all", "some", "most", "few", "many", "always", "sometimes"]
        has_scope = any(w in text_a + text_b for w in scope_words)
        if has_scope:
            return "Check if claims differ in scope/quantification"

        return "Review source methodology and evidence quality"
