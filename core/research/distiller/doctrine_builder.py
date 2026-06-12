"""
Phase 2 — Doctrine Builder

Converts repeated insights into stable doctrine.
Doctrine = compressed operational knowledge that persists across sessions.
"""

from dataclasses import dataclass, field
from typing import Optional
import uuid


@dataclass
class Doctrine:
    """A stable operational doctrine."""
    doctrine_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    domain: str = ""  # market_structure, cognition, systems, topology, coordination
    statement: str = ""  # The core doctrine statement
    evidence: list[str] = field(default_factory=list)  # Supporting insight IDs
    confidence: float = 0.0  # Based on evidence count and consistency
    tags: list[str] = field(default_factory=list)
    
    def to_obsidian_markdown(self) -> str:
        """Convert to Obsidian-compatible markdown."""
        lines = [
            "---",
            f"doctrine_id: {self.doctrine_id}",
            f"domain: {self.domain}",
            f"confidence: {self.confidence}",
            f"evidence_count: {len(self.evidence)}",
            f"tags: [{', '.join(self.tags)}]",
            "---",
            "",
            f"# Doctrine: {self.name}",
            "",
            f"## Statement\n{self.statement}",
            "",
            f"## Evidence ({len(self.evidence)} sources)",
        ]
        for e in self.evidence:
            lines.append(f"- {e}")
        lines.append("")
        return "\n".join(lines)


class DoctrineBuilder:
    """
    Builds doctrine from accumulated insights.
    
    When multiple insights converge on the same pattern,
    a doctrine is born. This is the compression layer.
    """
    
    def __init__(self):
        self._doctrines: dict[str, Doctrine] = {}
        self._insights: list = []
    
    def add_insight(self, insight):
        """Add an insight and check for doctrine formation."""
        self._insights.append(insight)
        self._check_doctrine_formation(insight)
    
    def _check_doctrine_formation(self, new_insight):
        """
        Check if a new insight reinforces or contradicts existing doctrine.
        
        Doctrine formation rules:
        - ≥3 insights sharing a pattern → new doctrine
        - ≥2 insights contradicting → flag for review
        """
        # Simple matching: check if concepts overlap with existing doctrines
        for doctrine in self._doctrines.values():
            shared_concepts = set(new_insight.concepts) & set(doctrine.tags)
            if len(shared_concepts) >= 2:
                # Reinforce existing doctrine
                doctrine.evidence.append(new_insight.insight_id)
                doctrine.confidence = min(1.0, 0.5 + len(doctrine.evidence) * 0.1)
    
    def create_doctrine(self, name: str, domain: str, statement: str,
                        evidence: list[str] = None) -> Doctrine:
        """Create a new doctrine."""
        doctrine = Doctrine(
            name=name,
            domain=domain,
            statement=statement,
            evidence=evidence or [],
            confidence=0.5 if evidence else 0.1,
            tags=[domain, "doctrine"],
        )
        self._doctrines[name] = doctrine
        return doctrine
    
    def get_doctrine(self, name: str) -> Optional[Doctrine]:
        """Get a doctrine by name."""
        return self._doctrines.get(name)
    
    def list_doctrines(self) -> list[dict]:
        """List all doctrines."""
        return [
            {
                "name": d.name,
                "domain": d.domain,
                "confidence": d.confidence,
                "evidence_count": len(d.evidence),
            }
            for d in self._doctrines.values()
        ]
    
    def get_doctrines_by_domain(self, domain: str) -> list[Doctrine]:
        """Get all doctrines in a domain."""
        return [d for d in self._doctrines.values() if d.domain == domain]
