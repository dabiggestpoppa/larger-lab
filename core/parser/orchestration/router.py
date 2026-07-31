"""
Phase 1.2 — Parser Router

Routes files to the correct extraction engine based on media type.
Integrates: markitdown, odl-pdf, liteparse, chandra

Architecture:
    Input File → Media Detection → Parser Router → Extraction Engine → Cognition Object
"""

import os
import hashlib
from pathlib import Path
from typing import Optional

from .cognition_object import CognitionObject


# Media type detection
MEDIA_TYPES = {
    # Documents
    ".pdf": "pdf",
    ".docx": "docx",
    ".doc": "docx",
    ".pptx": "pptx",
    ".ppt": "pptx",
    ".xlsx": "xlsx",
    ".xls": "xlsx",
    ".txt": "text",
    ".md": "markdown",
    ".rst": "rst",
    ".html": "html",
    ".htm": "html",
    ".epub": "epub",
    ".rtf": "rtf",
    
    # Images
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".gif": "image",
    ".webp": "image",
    ".svg": "image",
    ".bmp": "image",
    ".tiff": "image",
    
    # Audio/Video
    ".mp3": "audio",
    ".wav": "audio",
    ".mp4": "video",
    ".avi": "video",
    ".mov": "video",
    ".mkv": "video",
    
    # Code
    ".py": "code",
    ".js": "code",
    ".ts": "code",
    ".tsx": "code",
    ".jsx": "code",
    ".java": "code",
    ".go": "code",
    ".rs": "code",
    ".cpp": "code",
    ".c": "code",
    ".h": "code",
    ".cs": "code",
    ".rb": "code",
    ".php": "code",
    ".swift": "code",
    ".kt": "code",
    ".scala": "code",
    ".sh": "code",
    ".sql": "code",
    ".yaml": "code",
    ".yml": "code",
    ".json": "code",
    ".xml": "code",
    ".css": "code",
    ".vue": "code",
    ".svelte": "code",
}


class ParserRouter:
    """
    Routes files to the appropriate extraction engine.
    
    Engine selection:
    - PDF research papers → odl-pdf (layout, tables, citations)
    - All other documents → markitdown (universal normalization)
    - Images/screenshots → chandra (OCR)
    - Code files → liteparse (AST-aware parsing)
    - Web URLs → liteparse (web extraction)
    """
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self._engines = {}
    
    def detect_media_type(self, file_path: str) -> str:
        """Detect media type from file extension."""
        ext = Path(file_path).suffix.lower()
        return MEDIA_TYPES.get(ext, "unknown")
    
    def compute_hash(self, file_path: str) -> str:
        """Compute SHA-256 hash of file for deduplication."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def route(self, file_path: str) -> CognitionObject:
        """
        Route a file to the appropriate parser engine.
        Returns a CognitionObject.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        media_type = self.detect_media_type(file_path)
        source_hash = self.compute_hash(file_path)
        
        # Route to engine
        if media_type == "pdf":
            return self._parse_pdf(file_path, source_hash)
        elif media_type == "image":
            return self._parse_image(file_path, source_hash)
        elif media_type == "code":
            return self._parse_code(file_path, source_hash)
        elif media_type in ("docx", "pptx", "xlsx", "html", "epub", "rtf"):
            return self._parse_document(file_path, source_hash, media_type)
        elif media_type in ("text", "markdown", "rst"):
            return self._parse_text(file_path, source_hash)
        elif media_type in ("audio", "video"):
            return self._parse_media(file_path, source_hash, media_type)
        else:
            # Fallback: try markitdown universal
            return self._parse_universal(file_path, source_hash)
    
    def _parse_pdf(self, file_path: str, source_hash: str) -> CognitionObject:
        """
        Parse PDF using ODL-PDF for research papers.
        Falls back to markitdown for non-research PDFs.
        """
        try:
            # Try ODL-PDF first (research PDF extraction)
            from .engines.odl_engine import ODLPDFEngine
            engine = ODLPDFEngine()
            return engine.extract(file_path, source_hash)
        except ImportError:
            # Fallback to markitdown
            return self._parse_universal(file_path, source_hash)
    
    def _parse_image(self, file_path: str, source_hash: str) -> CognitionObject:
        """Parse image/screenshot using Chandra OCR."""
        try:
            from .engines.chandra_engine import ChandraOCREngine
            engine = ChandraOCREngine()
            return engine.extract(file_path, source_hash)
        except ImportError:
            return self._create_error_object(file_path, source_hash, "image", 
                                             "Chandra OCR engine not available")
    
    def _parse_code(self, file_path: str, source_hash: str) -> CognitionObject:
        """Parse code file using LiteParse AST-aware extraction."""
        try:
            from .engines.liteparse_engine import LiteParseEngine
            engine = LiteParseEngine()
            return engine.extract(file_path, source_hash)
        except ImportError:
            return self._parse_text(file_path, source_hash)
    
    def _parse_document(self, file_path: str, source_hash: str, 
                        media_type: str) -> CognitionObject:
        """Parse document using MarkItDown universal converter."""
        try:
            from .engines.markitdown_engine import MarkItDownEngine
            engine = MarkItDownEngine()
            return engine.extract(file_path, source_hash, media_type)
        except ImportError:
            return self._create_error_object(file_path, source_hash, media_type,
                                             "MarkItDown engine not available")
    
    def _parse_text(self, file_path: str, source_hash: str) -> CognitionObject:
        """Parse plain text/markdown files directly."""
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        
        return CognitionObject(
            source_path=file_path,
            source_type="text",
            source_hash=source_hash,
            raw_text=text,
            markdown=text,
            word_count=len(text.split()),
        )
    
    def _parse_media(self, file_path: str, source_hash: str,
                     media_type: str) -> CognitionObject:
        """Parse audio/video using transcription."""
        return CognitionObject(
            source_path=file_path,
            source_type=media_type,
            source_hash=source_hash,
            summary=f"[{media_type.upper()}] Transcription pending",
        )
    
    def _parse_universal(self, file_path: str, source_hash: str) -> CognitionObject:
        """Universal fallback using MarkItDown."""
        return self._parse_document(file_path, source_hash, "unknown")
    
    def _create_error_object(self, file_path: str, source_hash: str,
                             media_type: str, error_msg: str) -> CognitionObject:
        """Create an error CognitionObject when engine is unavailable."""
        return CognitionObject(
            source_path=file_path,
            source_type=media_type,
            source_hash=source_hash,
            summary=f"[ERROR] {error_msg}",
            confidence=0.0,
        )
