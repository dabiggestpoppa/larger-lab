"""
MarkItDown Engine Wrapper
https://github.com/microsoft/markitdown

Universal file → Markdown converter.
Handles: PDF, DOCX, PPTX, XLSX, HTML, EPUB, images (with LLM), audio (with transcription)
"""

import os
from typing import Optional
from ..cognition_object import CognitionObject


class MarkItDownEngine:
    """
    Wraps Microsoft's MarkItDown for universal document conversion.
    
    Installation: pip install markitdown
    Optional backends:
      - markitdown[pdf]  → PDF support
      - markitdown[docx] → DOCX support  
      - markitdown[pptx] → PPTX support
      - markitdown[xlsx] → XLSX support
      - markitdown[all]  → All backends
    """
    
    def __init__(self, llm_client=None, llm_model=None):
        """
        Args:
            llm_client: Optional OpenAI client for image/audio understanding
            llm_model: Model name for LLM-enhanced extraction
        """
        self.llm_client = llm_client
        self.llm_model = llm_model
        self._converter = None
    
    def _get_converter(self):
        """Lazy-load MarkItDown converter."""
        if self._converter is None:
            try:
                from markitdown import MarkItDown
                self._converter = MarkItDown(
                    llm_client=self.llm_client,
                    llm_model=self.llm_model,
                )
            except ImportError:
                raise ImportError(
                    "markitdown not installed. Run: pip install markitdown[all]"
                )
        return self._converter
    
    def extract(self, file_path: str, source_hash: str,
                media_type: str = "unknown") -> CognitionObject:
        """
        Convert any supported file to markdown and create a CognitionObject.
        """
        converter = self._get_converter()
        
        # MarkItDown converts file → markdown
        result = converter.convert(file_path)
        
        markdown_text = result.text_content or ""
        
        # Extract title from first heading or filename
        title = self._extract_title(markdown_text) or os.path.basename(file_path)
        
        return CognitionObject(
            source_path=file_path,
            source_type=media_type,
            source_hash=source_hash,
            raw_text=markdown_text,
            markdown=markdown_text,
            title=title,
            summary=self._generate_summary(markdown_text),
            word_count=len(markdown_text.split()),
            confidence=0.9 if markdown_text else 0.1,
        )
    
    def _extract_title(self, markdown: str) -> str:
        """Extract title from first markdown heading."""
        for line in markdown.split("\n"):
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
        return ""
    
    def _generate_summary(self, markdown: str, max_chars: int = 500) -> str:
        """Generate a simple summary from the first paragraph."""
        lines = markdown.split("\n")
        summary_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("---"):
                summary_lines.append(line)
                if len(" ".join(summary_lines)) >= max_chars:
                    break
        return " ".join(summary_lines)[:max_chars]
