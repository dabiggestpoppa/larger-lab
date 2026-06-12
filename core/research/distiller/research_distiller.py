"""
Phase 2 — Research Distiller

Converts raw research papers into structured operational insights.
Output format (machine-readable, graph-linkable):

    CAUSE: What problem exists?
    METHOD: How did they solve it?
    RESULT: What changed?
    LIMITATIONS: Where does it fail?
    APPLICATION: How can OCE/PO use this?
    LINKS: [[Related Concepts]]
"""

from dataclasses import dataclass, field
from typing import Optional
import uuid


@dataclass
class DistilledInsight:
    """A distilled research insight."""
    insight_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    # Source
    source_paper: str = ""
    source_authors: list[str] = field(default_factory=list)
    source_year: str = ""
    
    # Distillation
    cause: str = ""       # What problem exists?
    method: str = ""      # How did they solve it?
    result: str = ""      # What changed?
    limitations: str = "" # Where does it fail?
    application: str = "" # How can OCE/PO use this?
    
    # Linking
    links: list[str] = field(default_factory=list)  # [[wiki-links]]
    concepts: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    
    # Scoring
    operational_relevance: float = 0.0  # 0-1
    novelty: float = 0.0               # 0-1
    reliability: float = 0.0           # 0-1
    
    def to_obsidian_markdown(self) -> str:
        """Convert to Obsidian-compatible markdown."""
        lines = [
            "---",
            f"insight_id: {self.insight_id}",
            f"source: {self.source_paper}",
            f"year: {self.source_year}",
            f"tags: [{', '.join(self.tags)}]",
            f"relevance: {self.operational_relevance}",
            "---",
            "",
            f"# {self.source_paper}",
            "",
            f"**Authors:** {', '.join(self.source_authors)}",
            "",
            f"## CAUSE\n{self.cause}",
            "",
            f"## METHOD\n{self.method}",
            "",
            f"## RESULT\n{self.result}",
            "",
            f"## LIMITATIONS\n{self.limitations}",
            "",
            f"## APPLICATION\n{self.application}",
            "",
        ]
        
        if self.links:
            lines.append("## LINKS")
            for link in self.links:
                lines.append(f"- [[{link}]]")
            lines.append("")
        
        return "\n".join(lines)


class ResearchDistiller:
    """
    Distills research papers into operational insights.
    
    Uses LLM for extraction when available, falls back to
    rule-based extraction from structured content.
    """
    
    # Distillation prompt template
    DISTILL_PROMPT = """Analyze this research paper and extract the following:

CAUSE: What problem or gap does this paper address? (1-2 sentences)
METHOD: What approach, algorithm, or methodology did they use? (2-3 sentences)
RESULT: What were the key findings or improvements? (2-3 sentences)
LIMITATIONS: What are the weaknesses or failure modes? (1-2 sentences)
APPLICATION: How could this be applied to OCE/SRRA/cognitive systems? (1-2 sentences)
CONCEPTS: List 3-5 key concepts as comma-separated values
LINKS: List 3-5 related concepts as comma-separated values (for wiki-linking)

Paper content:
{content}
"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
    
    def distill(self, text: str, title: str = "", authors: list[str] = None,
                year: str = "") -> DistilledInsight:
        """
        Distill a research paper into structured insights.
        """
        if self.llm_client:
            return self._distill_with_llm(text, title, authors, year)
        else:
            return self._distill_rule_based(text, title, authors, year)
    
    def _distill_with_llm(self, text: str, title: str, authors: list[str],
                          year: str) -> DistilledInsight:
        """Distill using LLM extraction."""
        prompt = self.DISTILL_PROMPT.format(content=text[:8000])
        
        try:
            response = self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a research analyst. Extract structured insights from research papers."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )
            
            content = response.choices[0].message.content
            return self._parse_distillation(content, title, authors, year)
            
        except Exception:
            return self._distill_rule_based(text, title, authors, year)
    
    def _distill_rule_based(self, text: str, title: str, authors: list[str],
                            year: str) -> DistilledInsight:
        """Fallback rule-based distillation."""
        # Extract abstract (first paragraph after "Abstract")
        abstract = self._extract_abstract(text)
        
        return DistilledInsight(
            source_paper=title,
            source_authors=authors or [],
            source_year=year,
            cause="",
            method="",
            result=abstract[:500] if abstract else text[:500],
            limitations="",
            application="",
            concepts=self._extract_concepts_simple(text),
            tags=["paper", "auto-distilled"],
            operational_relevance=0.5,
            novelty=0.5,
            reliability=0.5,
        )
    
    def _parse_distillation(self, content: str, title: str, authors: list[str],
                            year: str) -> DistilledInsight:
        """Parse LLM distillation output."""
        fields = {}
        current_field = None
        current_value = []
        
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("CAUSE:"):
                if current_field:
                    fields[current_field] = " ".join(current_value).strip()
                current_field = "cause"
                current_value = [line[6:].strip()]
            elif line.startswith("METHOD:"):
                if current_field:
                    fields[current_field] = " ".join(current_value).strip()
                current_field = "method"
                current_value = [line[7:].strip()]
            elif line.startswith("RESULT:"):
                if current_field:
                    fields[current_field] = " ".join(current_value).strip()
                current_field = "result"
                current_value = [line[7:].strip()]
            elif line.startswith("LIMITATIONS:"):
                if current_field:
                    fields[current_field] = " ".join(current_value).strip()
                current_field = "limitations"
                current_value = [line[12:].strip()]
            elif line.startswith("APPLICATION:"):
                if current_field:
                    fields[current_field] = " ".join(current_value).strip()
                current_field = "application"
                current_value = [line[12:].strip()]
            elif line.startswith("CONCEPTS:"):
                if current_field:
                    fields[current_field] = " ".join(current_value).strip()
                current_field = "concepts"
                current_value = [line[9:].strip()]
            elif line.startswith("LINKS:"):
                if current_field:
                    fields[current_field] = " ".join(current_value).strip()
                current_field = "links"
                current_value = [line[6:].strip()]
            elif line and current_field:
                current_value.append(line)
        
        if current_field:
            fields[current_field] = " ".join(current_value).strip()
        
        # Parse concepts and links
        concepts = [c.strip() for c in fields.get("concepts", "").split(",") if c.strip()]
        links = [l.strip() for l in fields.get("links", "").split(",") if l.strip()]
        
        return DistilledInsight(
            source_paper=title,
            source_authors=authors or [],
            source_year=year,
            cause=fields.get("cause", ""),
            method=fields.get("method", ""),
            result=fields.get("result", ""),
            limitations=fields.get("limitations", ""),
            application=fields.get("application", ""),
            concepts=concepts,
            links=links,
            tags=["paper", "llm-distilled"],
            operational_relevance=0.7,
            novelty=0.6,
            reliability=0.7,
        )
    
    def _extract_abstract(self, text: str) -> str:
        """Extract abstract from paper text."""
        import re
        match = re.search(r'(?i)abstract[:\s]*\n?(.*?)(?:\n\n|\n(?:1\.|I\.|introduction))', text, re.DOTALL)
        if match:
            return match.group(1).strip()[:1000]
        return ""
    
    def _extract_concepts_simple(self, text: str) -> list[str]:
        """Simple concept extraction: capitalized phrases."""
        import re
        # Find capitalized multi-word phrases
        phrases = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        # Deduplicate and filter
        seen = set()
        concepts = []
        for p in phrases:
            if p not in seen and len(p) > 3 and p not in ("The", "This", "That", "These", "Those"):
                concepts.append(p)
                seen.add(p)
            if len(concepts) >= 5:
                break
        return concepts
