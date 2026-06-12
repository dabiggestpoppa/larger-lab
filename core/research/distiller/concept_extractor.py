"""
Phase 2 — Concept Extractor

Extracts entities, mechanisms, equations, and methodologies from research.
"""

from dataclasses import dataclass, field
from typing import Optional
import re


@dataclass
class Concept:
    """An extracted concept from research."""
    name: str
    concept_type: str  # entity, mechanism, equation, methodology, dataset, domain
    description: str = ""
    source_refs: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)


class ConceptExtractor:
    """
    Extracts key concepts from research text.
    
    Types:
    - entity: named thing (model, system, framework)
    - mechanism: how something works
    - equation: mathematical formula
    - methodology: research method
    - dataset: named dataset
    - domain: research domain
    """
    
    # Known concept patterns
    EQUATION_PATTERN = r'\$[^$]+\$|\b[A-Z]\s*=\s*[^.]+'
    CITATION_PATTERN = r'\[[\d,\s–-]+\]|\([A-Z][a-z]+(?:\s+(?:et\s+al\.?|and\s+[A-Z][a-z]+))?,?\s*\d{4}\)'
    METHOD_KEYWORDS = [
        "algorithm", "method", "approach", "technique", "framework",
        "model", "architecture", "pipeline", "system", "protocol",
    ]
    
    def extract(self, text: str, source_ref: str = "") -> list[Concept]:
        """Extract all concepts from text."""
        concepts = []
        
        # Extract equations
        equations = re.findall(self.EQUATION_PATTERN, text)
        for eq in equations:
            concepts.append(Concept(
                name=eq[:50],
                concept_type="equation",
                source_refs=[source_ref] if source_ref else [],
            ))
        
        # Extract method mentions
        for keyword in self.METHOD_KEYWORDS:
            pattern = rf'\b{keyword}\s+(?:of\s+)?["\']?([A-Z][A-Za-z\s]+)["\']?'
            matches = re.findall(pattern, text)
            for match in matches:
                concepts.append(Concept(
                    name=match.strip()[:50],
                    concept_type="methodology",
                    source_refs=[source_ref] if source_ref else [],
                ))
        
        # Extract capitalized multi-word phrases (potential entities)
        phrases = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b', text)
        seen = set()
        for phrase in phrases:
            if phrase not in seen and len(phrase) > 5:
                concepts.append(Concept(
                    name=phrase,
                    concept_type="entity",
                    source_refs=[source_ref] if source_ref else [],
                ))
                seen.add(phrase)
        
        return concepts[:20]  # Limit to top 20
