"""
Research Cognition Engine (RCE) — Phase 1+2 of the RCE revision.

R1: Knowledge Decomposition Engine
R2: Semantic Relationship Construction
R3: Cross-Document Reasoning Engine
R4: Theory Synthesis Engine
R5: Validation + Stress Testing

This package transforms OCE from a retrieval system into a scientific reasoning engine.
"""

from .decomposition import KnowledgeDecomposer
from .relationships import RelationshipBuilder
from .reasoning import CrossDocumentReasoner
from .synthesis import TheorySynthesizer
from .validation import RCEValidator

__all__ = [
    "KnowledgeDecomposer",
    "RelationshipBuilder",
    "CrossDocumentReasoner",
    "TheorySynthesizer",
    "RCEValidator",
]
