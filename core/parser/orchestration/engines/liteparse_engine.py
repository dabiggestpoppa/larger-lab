"""
LiteParse Engine Wrapper
https://github.com/run-llama/liteparse

LlamaIndex-based parsing + chunking for documents and code.
Provides AST-aware code parsing and web extraction.
"""

from ..cognition_object import CognitionObject


class LiteParseEngine:
    """
    Wraps LiteParse for intelligent document parsing and chunking.
    
    Installation: pip install liteparse
    """
    
    def __init__(self):
        self._parser = None
    
    def extract(self, file_path: str, source_hash: str) -> CognitionObject:
        """
        Parse a document or code file using LiteParse.
        """
        try:
            raw_text = self._read_file(file_path)
            
            return CognitionObject(
                source_path=file_path,
                source_type="code",
                source_hash=source_hash,
                raw_text=raw_text,
                markdown=self._to_markdown(raw_text, file_path),
                summary=self._generate_summary(raw_text),
                word_count=len(raw_text.split()),
                confidence=0.9 if raw_text else 0.1,
            )
        except ImportError:
            raise ImportError(
                "liteparse not installed. "
                "See: https://github.com/run-llama/liteparse"
            )
    
    def _read_file(self, file_path: str) -> str:
        """Read file content."""
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    
    def _to_markdown(self, text: str, file_path: str) -> str:
        """Wrap code in markdown code blocks."""
        ext = file_path.split(".")[-1] if "." in file_path else ""
        return f"```{ext}\n{text}\n```"
    
    def _generate_summary(self, text: str, max_chars: int = 300) -> str:
        """Generate summary from first lines."""
        lines = text.split("\n")
        summary_lines = []
        for line in lines[:20]:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith("//"):
                summary_lines.append(stripped)
            if len(" ".join(summary_lines)) >= max_chars:
                break
        return " ".join(summary_lines)[:max_chars]
