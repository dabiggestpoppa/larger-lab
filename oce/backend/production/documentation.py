"""
V3 Phase 9 — Documentation
System documentation management for all V3 phases.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DocPage:
    """A single documentation page."""
    page_id: str
    title: str
    content: str = ""
    section: str = ""
    version: str = "1.0"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    @property
    def word_count(self) -> int:
        return len(self.content.split())

    def update(self, content: str) -> None:
        self.content = content
        self.updated_at = time.time()


@dataclass
class DocSection:
    """A documentation section containing pages."""
    section_id: str
    title: str
    description: str = ""
    pages: list = field(default_factory=list)
    order: int = 0


class Documentation:
    """
    System documentation management.
    
    Organizes documentation into sections and pages.
    Tracks completeness across all V3 phases.
    """

    def __init__(self):
        self._sections: dict[str, DocSection] = {}
        self._pages: dict[str, DocPage] = {}

    def add_section(self, title: str, description: str = "", order: int = 0) -> DocSection:
        """Add a documentation section."""
        section_id = f"sec_{len(self._sections)}"
        section = DocSection(
            section_id=section_id, title=title,
            description=description, order=order,
        )
        self._sections[section_id] = section
        return section

    def add_page(self, title: str, content: str = "", section_id: str = "") -> DocPage:
        """Add a documentation page."""
        page_id = f"page_{len(self._pages)}"
        page = DocPage(
            page_id=page_id, title=title,
            content=content, section=section_id,
        )
        self._pages[page_id] = page

        if section_id in self._sections:
            self._sections[section_id].pages.append(page_id)

        return page

    def get_page(self, page_id: str) -> Optional[DocPage]:
        """Get a page by ID."""
        return self._pages.get(page_id)

    def get_section_pages(self, section_id: str) -> list[DocPage]:
        """Get all pages in a section."""
        section = self._sections.get(section_id)
        if section is None:
            return []
        return [self._pages[pid] for pid in section.pages if pid in self._pages]

    def search(self, query: str) -> list[DocPage]:
        """Search pages by title or content."""
        query_lower = query.lower()
        return [
            p for p in self._pages.values()
            if query_lower in p.title.lower() or query_lower in p.content.lower()
        ]

    def get_completeness(self) -> dict:
        """Check documentation completeness."""
        total_sections = len(self._sections)
        total_pages = len(self._pages)
        pages_with_content = sum(1 for p in self._pages.values() if p.word_count > 0)
        sections_with_pages = sum(
            1 for s in self._sections.values() if len(s.pages) > 0
        )

        return {
            "total_sections": total_sections,
            "sections_with_pages": sections_with_pages,
            "total_pages": total_pages,
            "pages_with_content": pages_with_content,
            "completeness_pct": round(
                pages_with_content / max(total_pages, 1), 4
            ),
        }

    @property
    def stats(self) -> dict:
        completeness = self.get_completeness()
        total_words = sum(p.word_count for p in self._pages.values())
        return {
            **completeness,
            "total_words": total_words,
        }
