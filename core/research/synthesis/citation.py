"""
Phase 1.5 — Citation Mapper

Maps claims to source documents.
Extracts citations from text (DOI, arXiv, URL).
Validates citation existence.
Generates bibliography in multiple formats.
"""

from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger("oce.citation")


@dataclass
class Citation:
    """A single citation."""
    citation_id: str = ""
    title: str = ""
    authors: List[str] = field(default_factory=list)
    year: str = ""
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    url: Optional[str] = None
    source_type: str = "unknown"  # journal, preprint, book, web

    def to_apa(self) -> str:
        """Format as APA citation."""
        authors_str = ", ".join(self.authors) if self.authors else "Unknown"
        year_str = f"({self.year})" if self.year else "(n.d.)"
        title_str = self.title if self.title else "Untitled"
        if self.doi:
            return f"{authors_str} {year_str}. {title_str}. https://doi.org/{self.doi}"
        elif self.url:
            return f"{authors_str} {year_str}. {title_str}. {self.url}"
        return f"{authors_str} {year_str}. {title_str}."

    def to_bibtex(self) -> str:
        """Format as BibTeX entry."""
        key = self.doi or self.arxiv_id or self.title[:20].replace(" ", "_")
        authors_str = " and ".join(self.authors) if self.authors else "Unknown"
        entry = f"@misc{{{key},\n"
        entry += f"  title = {{{self.title}}},\n"
        entry += f"  author = {{{authors_str}}},\n"
        if self.year:
            entry += f"  year = {{{self.year}}},\n"
        if self.doi:
            entry += f"  doi = {{{self.doi}}},\n"
        if self.url:
            entry += f"  url = {{{self.url}}},\n"
        entry += "}"
        return entry


class CitationMapper:
    """
    Maps claims to source documents and extracts citations.
    
    Usage:
        mapper = CitationMapper()
        citations = mapper.extract_citations(text)
        bibliography = mapper.generate_bibliography(citations, format="apa")
    """

    # Regex patterns for citation extraction
    DOI_PATTERN = re.compile(r'10\.\d{4,}/[^\s\)]+')
    ARXIV_PATTERN = re.compile(r'arXiv:(\d{4}\.\d{4,5})')
    URL_PATTERN = re.compile(r'https?://[^\s]+')

    def extract_citations(self, text: str) -> List[Citation]:
        """Extract citations from text."""
        citations = []

        # Extract DOIs
        for match in self.DOI_PATTERN.finditer(text):
            doi = match.group()
            # Get surrounding context (100 chars before)
            start = max(0, match.start() - 100)
            context = text[start:match.end() + 50]

            citations.append(Citation(
                citation_id=doi,
                doi=doi,
                source_type="journal",
                title=self._extract_title_from_context(context),
            ))

        # Extract arXiv IDs
        for match in self.ARXIV_PATTERN.finditer(text):
            arxiv_id = match.group(1)
            start = max(0, match.start() - 100)
            context = text[start:match.end() + 50]

            citations.append(Citation(
                citation_id=f"arxiv:{arxiv_id}",
                arxiv_id=arxiv_id,
                source_type="preprint",
                title=self._extract_title_from_context(context),
            ))

        # Deduplicate by DOI/arXiv ID
        seen = set()
        unique = []
        for c in citations:
            key = c.doi or c.arxiv_id or c.citation_id
            if key not in seen:
                seen.add(key)
                unique.append(c)

        return unique

    def _extract_title_from_context(self, context: str) -> str:
        """Try to extract a title from surrounding context."""
        # Simple heuristic: look for capitalized phrase before DOI
        words = context.split()
        title_words = []
        for word in words:
            if word[0].isupper() if word else False:
                title_words.append(word)
            elif title_words:
                break
        return " ".join(title_words[:10]) if title_words else "Unknown Title"

    def map_claim_to_sources(
        self,
        claim: str,
        sources: List[Dict[str, str]],
    ) -> List[Citation]:
        """Map a claim to its supporting sources."""
        citations = []
        claim_lower = claim.lower()

        for source in sources:
            source_text = source.get("text", "").lower()
            # Check if claim text appears in source
            if any(word in source_text for word in claim_lower.split()[:5]):
                citations.append(Citation(
                    citation_id=source.get("id", ""),
                    title=source.get("title", ""),
                    authors=source.get("authors", []),
                    year=source.get("year", ""),
                    doi=source.get("doi"),
                    url=source.get("url"),
                ))

        return citations

    def generate_bibliography(
        self,
        citations: List[Citation],
        format: str = "apa",
    ) -> str:
        """Generate formatted bibliography."""
        if not citations:
            return "No citations found."

        entries = []
        for citation in citations:
            if format == "apa":
                entries.append(citation.to_apa())
            elif format == "bibtex":
                entries.append(citation.to_bibtex())
            else:
                entries.append(citation.to_apa())

        if format == "bibtex":
            return "\n\n".join(entries)

        return "\n".join(f"{i+1}. {entry}" for i, entry in enumerate(entries))

    def validate_citation(self, citation: Citation) -> Dict[str, Any]:
        """Validate a citation has minimum required fields."""
        result = {
            "valid": True,
            "issues": [],
        }

        if not citation.title or citation.title == "Unknown Title":
            result["issues"].append("Missing title")
        if not citation.doi and not citation.arxiv_id and not citation.url:
            result["issues"].append("No identifier (DOI/arXiv/URL)")
        if not citation.authors:
            result["issues"].append("No authors")
        if not citation.year:
            result["issues"].append("No year")

        result["valid"] = len(result["issues"]) < 3
        return result
