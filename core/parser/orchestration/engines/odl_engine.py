"""
OpenDataLoader PDF Engine Wrapper
https://github.com/opendataloader-project/opendataloader-pdf

Research PDF extraction: layout parsing, table extraction, citation parsing,
abstract extraction.

This is the PRIMARY engine for research papers.
"""

from ..cognition_object import CognitionObject


class ODLPDFEngine:
    """
    Wraps OpenDataLoader PDF for research paper extraction.
    
    Installation: pip install opendataloader-pdf
    """
    
    def __init__(self):
        self._pipeline = None
    
    def extract(self, file_path: str, source_hash: str) -> CognitionObject:
        """
        Extract structured content from a research PDF.
        """
        try:
            # ODL-PDF extraction pipeline
            raw_text, metadata = self._run_odl(file_path)
            
            return CognitionObject(
                source_path=file_path,
                source_type="pdf",
                source_hash=source_hash,
                raw_text=raw_text,
                markdown=self._to_markdown(raw_text, metadata),
                title=metadata.get("title", ""),
                authors=metadata.get("authors", []),
                abstract=metadata.get("abstract", ""),
                citations=metadata.get("citations", []),
                tables=metadata.get("tables", []),
                summary=metadata.get("abstract", "") or self._generate_summary(raw_text),
                concepts=self._extract_concepts(raw_text),
                tags=self._generate_tags(metadata),
                word_count=len(raw_text.split()),
                confidence=0.95 if raw_text else 0.1,
            )
        except ImportError:
            raise ImportError(
                "opendataloader-pdf not installed. "
                "See: https://github.com/opendataloader-project/opendataloader-pdf"
            )
    
    def _run_odl(self, file_path: str) -> tuple[str, dict]:
        """
        Run ODL-PDF extraction pipeline.
        Returns (raw_text, metadata_dict)
        """
        # TODO: Integrate actual ODL-PDF pipeline
        # For now, return placeholder — the actual ODL-PDF library
        # provides layout analysis, table extraction, citation parsing
        metadata = {
            "title": "",
            "authors": [],
            "abstract": "",
            "citations": [],
            "tables": [],
        }
        
        # Placeholder: read raw text
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                raw_text = f.read()
        except (UnicodeDecodeError, IsADirectoryError):
            raw_text = ""
        
        return raw_text, metadata
    
    def _to_markdown(self, raw_text: str, metadata: dict) -> str:
        """Convert ODL output to structured markdown."""
        md = ""
        if metadata.get("title"):
            md += f"# {metadata['title']}\n\n"
        if metadata.get("authors"):
            md += f"**Authors:** {', '.join(metadata['authors'])}\n\n"
        if metadata.get("abstract"):
            md += f"## Abstract\n{metadata['abstract']}\n\n"
        md += f"## Content\n{raw_text}\n"
        return md
    
    def _extract_concepts(self, text: str) -> list[str]:
        """Extract key concepts from text. Placeholder for NER/NLP."""
        return []
    
    def _generate_tags(self, metadata: dict) -> list[str]:
        """Generate semantic tags from metadata."""
        tags = ["paper"]
        if metadata.get("abstract"):
            tags.append("has-abstract")
        if metadata.get("citations"):
            tags.append("has-citations")
        return tags
    
    def _generate_summary(self, text: str, max_chars: int = 500) -> str:
        """Generate summary from first portion of text."""
        return text[:max_chars].strip()
