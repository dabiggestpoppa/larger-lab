"""
R1.7 — Structured Knowledge Object Schema

Every paper becomes a machine-readable cognition object.
Replaces summaries permanently.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Claim:
    """R1.1 — Extracted claim from a paper."""
    claim_id: str
    claim: str
    confidence: float = 0.0
    source_paper: str = ""
    claim_type: str = "primary"  # primary | secondary | implicit


@dataclass
class Mechanism:
    """R1.2 — Extracted causal mechanism."""
    cause: str
    mechanism: str
    effect: str
    confidence: float = 0.0
    source_paper: str = ""


@dataclass
class Assumption:
    """R1.3 — Extracted assumption (explicit or implicit)."""
    assumption: str
    explicit: bool = True
    confidence: float = 0.0
    source_paper: str = ""


@dataclass
class Equation:
    """R1.4 — Mathematical framework extraction."""
    equation_type: str
    variables: List[str] = field(default_factory=list)
    mathematical_framework: str = ""
    raw_text: str = ""
    source_paper: str = ""


@dataclass
class Limitation:
    """R1.5 — Extracted limitation or weakness."""
    limitation: str
    severity: str = "medium"  # low | medium | high
    is_stated: bool = True  # stated by authors vs detected by system
    source_paper: str = ""


@dataclass
class NovelContribution:
    """R1.6 — What this paper contributes that prior literature did not."""
    contribution: str
    novelty_score: float = 0.0
    prior_literature_gap: str = ""
    source_paper: str = ""


@dataclass
class KnowledgeObject:
    """
    R1.7 — Complete structured knowledge object.
    
    Every paper is decomposed into this schema.
    No summaries. Only structured scientific cognition.
    """
    paper_title: str = ""
    paper_id: str = ""
    domain: str = ""
    confidence_score: float = 0.0
    
    # R1.1 — Claims
    main_claims: List[Claim] = field(default_factory=list)
    
    # R1.2 — Mechanisms
    mechanisms: List[Mechanism] = field(default_factory=list)
    
    # R1.3 — Assumptions
    assumptions: List[Assumption] = field(default_factory=list)
    
    # R1.4 — Equations / Math
    equations: List[Equation] = field(default_factory=list)
    
    # R1.5 — Limitations
    limitations: List[Limitation] = field(default_factory=list)
    
    # R1.6 — Novelty
    novel_contribution: Optional[NovelContribution] = None
    
    # Metadata
    causal_relationships: List[Dict[str, str]] = field(default_factory=list)
    implicit_theory: str = ""
    methodology: str = ""
    authors: List[str] = field(default_factory=list)
    year: str = ""
    doi: str = ""
    source_url: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for storage."""
        import dataclasses
        return dataclasses.asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> KnowledgeObject:
        """Deserialize from dict."""
        claims = [Claim(**c) for c in data.get("main_claims", [])]
        mechanisms = [Mechanism(**m) for m in data.get("mechanisms", [])]
        assumptions = [Assumption(**a) for a in data.get("assumptions", [])]
        equations = [Equation(**e) for e in data.get("equations", [])]
        limitations = [Limitation(**l) for l in data.get("limitations", [])]
        nc_data = data.get("novel_contribution")
        novel = NovelContribution(**nc_data) if nc_data else None
        
        return cls(
            paper_title=data.get("paper_title", ""),
            paper_id=data.get("paper_id", ""),
            domain=data.get("domain", ""),
            confidence_score=data.get("confidence_score", 0.0),
            main_claims=claims,
            mechanisms=mechanisms,
            assumptions=assumptions,
            equations=equations,
            limitations=limitations,
            novel_contribution=novel,
            causal_relationships=data.get("causal_relationships", []),
            implicit_theory=data.get("implicit_theory", ""),
            methodology=data.get("methodology", ""),
            authors=data.get("authors", []),
            year=data.get("year", ""),
            doi=data.get("doi", ""),
            source_url=data.get("source_url", ""),
        )
    
    @property
    def extraction_completeness(self) -> float:
        """Score 0-1 of how complete the decomposition is."""
        scores = [
            min(len(self.main_claims) / 3, 1.0),
            min(len(self.mechanisms) / 2, 1.0),
            min(len(self.assumptions) / 2, 1.0),
            1.0 if self.equations else 0.0,
            min(len(self.limitations) / 2, 1.0),
            1.0 if self.novel_contribution else 0.0,
        ]
        return sum(scores) / len(scores)
    
    @property
    def is_well_decomposed(self) -> bool:
        """Minimum threshold for a usable knowledge object."""
        return self.extraction_completeness >= 0.5 and len(self.main_claims) >= 1
