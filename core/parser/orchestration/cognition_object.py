"""
Phase 1.2 — Cognition Object Schema

Every parsed document becomes a Cognition Object with:
- summary: semantic summary
- concepts: extracted key concepts
- tags: semantic taxonomy tags
- links: context links to other objects
- source: original file reference
- media_type: PDF/DOCX/PPTX/IMAGE/WEB/CODE/etc
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import uuid


@dataclass
class CognitionObject:
    """Normalized output from any parser engine."""
    
    # Identity
    object_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Source
    source_path: str = ""
    source_type: str = ""  # pdf, docx, pptx, image, web, code, audio, video
    source_hash: str = ""  # SHA-256 of original file
    
    # Content
    raw_text: str = ""
    markdown: str = ""
    summary: str = ""
    
    # Semantics
    concepts: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    links: list[str] = field(default_factory=list)  # wiki-links to other objects
    
    # Research-specific (from ODL-PDF)
    title: str = ""
    authors: list[str] = field(default_factory=list)
    abstract: str = ""
    citations: list[str] = field(default_factory=list)
    tables: list[dict] = field(default_factory=list)
    
    # Embedding (filled by Phase 1.3)
    embedding: Optional[list[float]] = None
    
    # Metadata
    word_count: int = 0
    language: str = "en"
    confidence: float = 1.0  # extraction confidence
    
    def to_dict(self) -> dict:
        return {
            "object_id": self.object_id,
            "created_at": self.created_at,
            "source_path": self.source_path,
            "source_type": self.source_type,
            "summary": self.summary,
            "concepts": self.concepts,
            "tags": self.tags,
            "links": self.links,
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "citations_count": len(self.citations),
            "word_count": self.word_count,
            "language": self.language,
        }
    
    def to_obsidian_markdown(self) -> str:
        """Convert to Obsidian-compatible markdown with frontmatter."""
        frontmatter = f"""---
object_id: {self.object_id}
source_type: {self.source_type}
tags: [{', '.join(self.tags)}]
concepts: [{', '.join(self.concepts)}]
created: {self.created_at}
word_count: {self.word_count}
---

"""
        if self.title:
            frontmatter += f"# {self.title}\n\n"
        if self.authors:
            frontmatter += f"**Authors:** {', '.join(self.authors)}\n\n"
        if self.abstract:
            frontmatter += f"## Abstract\n{self.abstract}\n\n"
        
        frontmatter += f"## Summary\n{self.summary}\n\n"
        
        if self.concepts:
            frontmatter += f"## Key Concepts\n"
            for c in self.concepts:
                frontmatter += f"- [[{c}]]\n"
            frontmatter += "\n"
        
        if self.links:
            frontmatter += f"## Related\n"
            for link in self.links:
                frontmatter += f"- [[{link}]]\n"
        
        return frontmatter
