"""
L2.1 — Rule-based paper distiller.

Converts raw paper metadata into CAUSE/METHOD/RESULT/LIMITATIONS/APPLICATION/LINKS format.
Primary distiller — LLM is opt-in (L2.6). No API calls here.

Usage:
    distiller = Distiller()
    note = distiller.distill(paper)
    # Returns markdown string ready for vault write
"""

from __future__ import annotations

import re
from typing import List, Optional

from ..ingestion.models import Paper


class Distiller:
    """
    Rule-based distillation engine.
    
    Extracts operational signal from paper metadata using heuristics.
    No LLM calls — pure pattern matching on abstract/title.
    """

    # Keywords that indicate CAUSE (problem being addressed)
    CAUSE_PATTERNS = [
        r"problem.*(?:of|is)",
        r"challenge.*(?:of|is)",
        r"limitation.*(?:of|is)",
        r"gap.*(?:in|exists)",
        r"difficult.*(?:to|for)",
        r"hard.*(?:to|for)",
        r"lack.*(?:of|in)",
        r"missing.*(?:in|from)",
    ]

    # Keywords that indicate METHOD
    METHOD_PATTERNS = [
        r"we propose",
        r"we present",
        r"we introduce",
        r"we develop",
        r"we design",
        r"our approach",
        r"our method",
        r"algorithm",
        r"framework",
        r"model",
    ]

    # Keywords that indicate RESULT (numbers/metrics)
    RESULT_PATTERNS = [
        r"\d+\.?\d*\s*%.*improvement",
        r"accuracy.*(?:of|at)\s*\d+\.?\d*",
        r"precision.*(?:of|at)\s*\d+\.?\d*",
        r"recall.*(?:of|at)\s*\d+\.?\d*",
        r"increased?.*(?:by|\d+\.?\d*)",
        r"decreased?.*(?:by|\d+\.?\d*)",
        r"outperform(?:s|ed)",
        r"state.?of.?the.?art",
    ]

    def __init__(self):
        self._compiled_cause = [re.compile(p, re.I) for p in self.CAUSE_PATTERNS]
        self._compiled_method = [re.compile(p, re.I) for p in self.METHOD_PATTERNS]
        self._compiled_result = [re.compile(p, re.I) for p in self.RESULT_PATTERNS]

    def distill(self, paper: Paper) -> str:
        """
        Distill a paper into the standard CAUSE/METHOD/RESULT/LIMITATIONS/APPLICATION/LINKS format.
        
        Args:
            paper: Paper object with title, abstract, authors, concepts, etc.
            
        Returns:
            Markdown string ready for vault write
        """
        abstract = paper.abstract or ""
        
        cause = self._extract_cause(abstract, paper.title)
        method = self._extract_method(abstract, paper.title)
        result = self._extract_result(abstract, paper.title)
        limitations = self._extract_limitations(abstract)
        application = self._extract_application(abstract, paper.concepts)
        links = self._extract_links(paper)

        return self._format_note(paper, cause, method, result, limitations, application, links)

    def _extract_cause(self, abstract: str, title: str) -> str:
        """Extract what problem the paper addresses."""
        text = f"{title} {abstract}"
        for pattern in self._compiled_cause:
            match = pattern.search(text)
            if match:
                # Get surrounding context
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 100)
                return text[start:end].strip()
        # Fallback: first sentence often states the problem
        sentences = abstract.split(". ")
        if sentences:
            return sentences[0].strip()
        return "Problem not explicitly stated"

    def _extract_method(self, abstract: str, title: str) -> str:
        """Extract how the paper solves the problem."""
        text = f"{title} {abstract}"
        for pattern in self._compiled_method:
            match = pattern.search(text)
            if match:
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 150)
                return text[start:end].strip()
        # Fallback: look for methodology section
        if "method" in abstract.lower():
            idx = abstract.lower().find("method")
            return abstract[idx:idx+200].strip()
        return "Method not explicitly described"

    def _extract_result(self, abstract: str, title: str) -> str:
        """Extract quantitative results."""
        text = f"{title} {abstract}"
        for pattern in self._compiled_result:
            match = pattern.search(text)
            if match:
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 80)
                return text[start:end].strip()
        # Fallback: look for results section
        if "result" in abstract.lower():
            idx = abstract.lower().find("result")
            return abstract[idx:idx+200].strip()
        return "Results not quantified in abstract"

    def _extract_limitations(self, abstract: str) -> str:
        """Extract limitations or assumptions."""
        if "limitation" in abstract.lower():
            idx = abstract.lower().find("limitation")
            return abstract[idx:idx+150].strip()
        if "assumption" in abstract.lower():
            idx = abstract.lower().find("assumption")
            return abstract[idx:idx+150].strip()
        return "Limitations not explicitly stated"

    def _extract_application(self, abstract: str, concepts: List) -> str:
        """Extract potential applications for OCE/PO."""
        if concepts:
            concept_names = [c.name for c in concepts[:3]]
            return f"Relevant to: {', '.join(concept_names)}. Potential use in agent orchestration, memory systems, or knowledge graph enhancement."
        return "Application context derived from domain classification"

    def _extract_links(self, paper: Paper) -> str:
        """Extract link references for the note."""
        links = []
        for concept in paper.concepts[:5]:
            links.append(f"- [[{concept.name}]]")
        for ref_id in paper.referenced_works[:3]:
            links.append(f"- cites:[[{ref_id}]]")
        if paper.url:
            links.append(f"- URL: {paper.url}")
        return "\n".join(links) if links else "- No links"

    def _format_note(self, paper: Paper, cause: str, method: str, result: str,
                     limitations: str, application: str, links: str) -> str:
        """Format the distilled note in standard markdown format."""
        return f"""# {paper.title}

CAUSE: {cause}
METHOD: {method}
RESULT: {result}
LIMITATIONS: {limitations}
APPLICATION: {application}
LINKS:
{links}

#paper #domain/{paper.concepts[0].name if paper.concepts else 'unclassified'} #year/{paper.year} #operational_relevance/{paper.operational_relevance}
"""