"""
Phase 1.3.1 — Chunking Engine

Splits cognition into semantically meaningful units.
NOT arbitrary token cuts — preserves semantic continuity.

Rules:
- Semantic chunking (split on section boundaries, paragraphs)
- Overlap windows (preserve context across chunk boundaries)
- Context preservation (don't split mid-concept)
- Retrieval optimization (chunks sized for embedding models)
"""

from .semantic_chunker import SemanticChunker

__all__ = ["SemanticChunker"]
