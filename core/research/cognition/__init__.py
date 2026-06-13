"""
Research Cognition Engine (RCE) — Full 5-phase scientific reasoning pipeline.

R1: Knowledge Decomposition Engine
R2: Semantic Relationship Construction
R3: Cross-Document Reasoning Engine
R4: Theory Synthesis Engine
R5: Validation + Stress Testing

Multi-source ingestion: OpenAlex + arXiv + S2 (all 3 sources by default)

This package transforms OCE from a retrieval system into a scientific reasoning engine.
"""

from .decomposition import KnowledgeDecomposer
from .multi_source import MultiSourceFetcher
from .relationships import RelationshipBuilder
from .reasoning import CrossDocumentReasoner
from .synthesis import TheorySynthesizer
from .validation import RCEValidator

__all__ = [
    "KnowledgeDecomposer",
    "MultiSourceFetcher",
    "RelationshipBuilder",
    "CrossDocumentReasoner",
    "TheorySynthesizer",
    "RCEValidator",
]
