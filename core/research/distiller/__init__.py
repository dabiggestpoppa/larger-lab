"""
Phase 2 — Research Distillation Engine

Converts raw research into operational intelligence.
Extracts: CAUSE, METHOD, RESULT, LIMITATIONS, APPLICATION, LINKS

Components:
- research_distiller: compresses papers into operational insights
- concept_extractor: extracts entities/mechanisms/equations
- citation_mapper: builds citation intelligence graph
- doctrine_builder: converts repeated insights into doctrine
- contradiction_engine: detects conflicting research
- knowledge_scorer: scores research usefulness
"""

from .research_distiller import ResearchDistiller
from .concept_extractor import ConceptExtractor
from .doctrine_builder import DoctrineBuilder

__all__ = ["ResearchDistiller", "ConceptExtractor", "DoctrineBuilder"]
