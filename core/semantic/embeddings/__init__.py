"""
Phase 1.3.2 — Embedding Engine

Converts semantic chunks into high-dimensional meaning vectors.
Supports multiple embedding models (OpenAI, local, etc.).
"""

from .embedding_engine import EmbeddingEngine

__all__ = ["EmbeddingEngine"]
