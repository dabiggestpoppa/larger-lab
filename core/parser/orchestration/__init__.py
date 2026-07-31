"""
Phase 1.2 — Multimodal Parser Orchestration Router

Routes incoming files to the appropriate extraction engine:
- markitdown: universal file → markdown normalization
- odl-pdf: research PDF extraction (layout, tables, citations)
- liteparse: LlamaIndex-based parsing + chunking
- chandra: OCR / image / screenshot text extraction

All outputs are normalized to Cognition Objects for the semantic memory pipeline.
"""

from .router import ParserRouter
from .cognition_object import CognitionObject

__all__ = ["ParserRouter", "CognitionObject"]
