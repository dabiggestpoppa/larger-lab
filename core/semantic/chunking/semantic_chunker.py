"""
Phase 1.3.1 — Semantic Chunker

Splits documents into semantically meaningful chunks with overlap.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Chunk:
    """A semantic chunk of text."""
    chunk_id: str
    text: str
    source_object_id: str
    start_pos: int = 0
    end_pos: int = 0
    overlap_prev: str = ""  # text from previous chunk for context
    overlap_next: str = ""  # text from next chunk for context
    metadata: dict = field(default_factory=dict)
    embedding: Optional[list[float]] = None
    
    @property
    def token_count(self) -> int:
        """Approximate token count (4 chars ≈ 1 token)."""
        return len(self.text) // 4


class SemanticChunker:
    """
    Semantic chunking engine.
    
    Strategy:
    1. Split on document structure (headings, paragraphs)
    2. Respect max chunk size (default 512 tokens)
    3. Add overlap windows (default 64 tokens)
    4. Preserve semantic boundaries (don't split mid-sentence)
    """
    
    def __init__(
        self,
        max_chunk_tokens: int = 512,
        overlap_tokens: int = 64,
        min_chunk_tokens: int = 64,
    ):
        self.max_chunk_tokens = max_chunk_tokens
        self.overlap_tokens = overlap_tokens
        self.min_chunk_tokens = min_chunk_tokens
    
    def chunk(self, text: str, source_object_id: str = "") -> list[Chunk]:
        """
        Split text into semantic chunks.
        
        Strategy:
        1. Split on markdown headings (##, ###)
        2. Split on double newlines (paragraphs)
        3. Respect max_chunk_tokens
        4. Add overlap windows
        """
        if not text.strip():
            return []
        
        # Split on headings first
        sections = self._split_on_headings(text)
        
        chunks = []
        for section in sections:
            section_chunks = self._chunk_section(section, source_object_id)
            chunks.extend(section_chunks)
        
        # Add overlap windows
        chunks = self._add_overlaps(chunks)
        
        return chunks
    
    def _split_on_headings(self, text: str) -> list[str]:
        """Split text on markdown headings."""
        import re
        # Split on ## or ### headings
        sections = re.split(r'\n(?=#{1,3}\s)', text)
        return [s.strip() for s in sections if s.strip()]
    
    def _chunk_section(self, text: str, source_object_id: str) -> list[Chunk]:
        """Chunk a single section respecting max size."""
        approx_tokens = len(text) // 4
        
        if approx_tokens <= self.max_chunk_tokens:
            # Small enough — single chunk
            return [Chunk(
                chunk_id=f"chunk_{hash(text) % 100000:05d}",
                text=text,
                source_object_id=source_object_id,
                start_pos=0,
                end_pos=len(text),
            )]
        
        # Split on paragraphs
        paragraphs = text.split("\n\n")
        chunks = []
        current_text = ""
        current_start = 0
        
        for para in paragraphs:
            para_tokens = len(para) // 4
            current_tokens = len(current_text) // 4
            
            if current_tokens + para_tokens > self.max_chunk_tokens and current_text:
                # Save current chunk
                chunks.append(Chunk(
                    chunk_id=f"chunk_{hash(current_text) % 100000:05d}",
                    text=current_text.strip(),
                    source_object_id=source_object_id,
                    start_pos=current_start,
                    end_pos=current_start + len(current_text),
                ))
                current_text = para
                current_start += len(current_text) + 2  # +2 for \n\n
            else:
                if current_text:
                    current_text += "\n\n" + para
                else:
                    current_text = para
                    current_start = text.find(para)
        
        # Don't forget the last chunk
        if current_text.strip():
            chunks.append(Chunk(
                chunk_id=f"chunk_{hash(current_text) % 100000:05d}",
                text=current_text.strip(),
                source_object_id=source_object_id,
                start_pos=current_start,
                end_pos=current_start + len(current_text),
            ))
        
        return chunks
    
    def _add_overlaps(self, chunks: list[Chunk]) -> list[Chunk]:
        """Add overlap windows between chunks."""
        overlap_chars = self.overlap_tokens * 4  # approx chars per token
        
        for i in range(len(chunks)):
            if i > 0:
                # Overlap from previous chunk
                prev_text = chunks[i - 1].text
                chunks[i].overlap_prev = prev_text[-overlap_chars:] if len(prev_text) > overlap_chars else prev_text
            
            if i < len(chunks) - 1:
                # Overlap from next chunk
                next_text = chunks[i + 1].text
                chunks[i].overlap_next = next_text[:overlap_chars] if len(next_text) > overlap_chars else next_text
        
        return chunks
