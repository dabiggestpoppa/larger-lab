"""
L2.2 — Concept extractor.

Extracts top concepts from paper metadata.
Primary: OpenAlex concepts field (with scores).
Fallback: keyword extraction from abstract.

Usage:
    extractor = ConceptExtractor()
    concepts = extractor.extract(paper)
    # Returns List[Concept] sorted by score
"""

from __future__ import annotations

import re
from collections import Counter
from typing import List, Optional

from ..ingestion.models import Concept, Paper

# Common stop words to filter out
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
    "be", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "this", "that",
    "these", "those", "it", "its", "we", "our", "they", "their", "which",
    "what", "who", "whom", "how", "when", "where", "why", "not", "no",
    "nor", "so", "if", "then", "than", "too", "very", "just", "about",
    "also", "more", "most", "some", "any", "each", "every", "all", "both",
    "few", "many", "much", "several", "other", "such", "only", "own",
    "same", "new", "old", "first", "last", "long", "great", "little",
    "right", "big", "high", "different", "small", "large", "next",
    "early", "young", "important", "public", "bad", "good", "make",
    "like", "use", "using", "used", "based", "show", "shown", "study",
    "paper", "propose", "proposed", "method", "methods", "approach",
    "result", "results", "performance", "model", "models", "data",
    "set", "sets", "one", "two", "three", "four", "five", "six",
    "seven", "eight", "nine", "ten", "et", "al", "fig", "figure",
    "table", "eq", "equation", "sec", "section", "ref", "reference",
}


class ConceptExtractor:
    """
    Extracts concepts from paper metadata.
    
    Primary source: OpenAlex concepts field (with confidence scores).
    Fallback: keyword extraction from abstract using TF-like scoring.
    """

    def __init__(self, max_concepts: int = 5):
        self.max_concepts = max_concepts

    def extract(self, paper: Paper) -> List[Concept]:
        """
        Extract top concepts from a paper.
        
        Uses OpenAlex concepts if available, otherwise falls back to
        keyword extraction from abstract.
        
        Args:
            paper: Paper object with concepts and/or abstract
            
        Returns:
            List of Concept objects sorted by score (descending)
        """
        # Primary: use OpenAlex concepts if available
        if paper.concepts:
            return self._from_openalex(paper.concepts)
        
        # Fallback: extract from abstract
        if paper.abstract:
            return self._from_abstract(paper.abstract)
        
        return []

    def _from_openalex(self, concepts: List[Concept]) -> List[Concept]:
        """Sort OpenAlex concepts by score and return top N."""
        sorted_concepts = sorted(concepts, key=lambda c: c.score, reverse=True)
        return sorted_concepts[:self.max_concepts]

    def _from_abstract(self, abstract: str) -> List[Concept]:
        """
        Extract keywords from abstract using simple TF scoring.
        
        This is a fallback when OpenAlex concepts are not available.
        Uses word frequency with stop-word filtering.
        """
        # Normalize text
        text = abstract.lower()
        text = re.sub(r"[^\w\s-]", " ", text)
        
        # Tokenize and filter
        words = text.split()
        filtered = [
            w for w in words
            if len(w) > 3 and w not in STOP_WORDS and not w.isdigit()
        ]
        
        # Score by frequency
        word_counts = Counter(filtered)
        total = sum(word_counts.values()) or 1
        
        # Create concepts from top words
        concepts = []
        for word, count in word_counts.most_common(self.max_concepts * 2):
            score = count / total
            if score > 0.01:  # Minimum threshold
                concepts.append(Concept(
                    id=f"kw_{word}",
                    name=word.replace("-", " ").title(),
                    score=round(score, 3),
                    level=1,
                ))
        
        return concepts[:self.max_concepts]

    def extract_batch(self, papers: List[Paper]) -> dict[str, List[Concept]]:
        """
        Extract concepts from multiple papers.
        
        Returns dict mapping paper_id -> List[Concept].
        """
        return {paper.id: self.extract(paper) for paper in papers}