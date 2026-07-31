"""
REV-1: Structural Decomposition Hardening Engine
Part 2: Mechanism Decomposition + Limitation Extraction + Scientific Object
"""

from __future__ import annotations
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ─── REV-1.4 Mechanism Decomposition Engine ───

MECHANISM_PATTERNS = [
    r"(.{10,80})\s+(?:causes?|leads? to|results? in|produces?|generates?|drives?|induces?|triggers?|amplifies?|mediates?)\s+(.{10,80})",
    r"(.{10,80})\s+(?:via|through|by means of|by|through the mechanism of)\s+(.{10,80})",
    r"(?:when|if|under)\s+(.{10,60}),\s+(.{10,80})\s+(?:causes?|leads? to|results? in|produces?)\s+(.{10,80})",
]


def decompose_mechanisms(text: str, claims: List[Dict], paper_id: str = "") -> List[Dict[str, Any]]:
    """REV-1.4: Extract causal mechanisms. Break into intermediate steps."""
    mechanisms, seen = [], set()
    for pattern in MECHANISM_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            groups = [g for g in match.groups() if g]
            if len(groups) >= 2:
                chain = [g.strip()[:80] for g in groups]
                chain_key = "→".join(c.lower()[:30] for c in chain)
                if chain_key not in seen:
                    seen.add(chain_key)
                    mechanisms.append({
                        "mechanism_id": f"mech_{paper_id}_{len(mechanisms):03d}",
                        "cause": chain[0], "effect": chain[-1],
                        "mechanism": " → ".join(chain), "chain_length": len(chain),
                        "intermediates": chain[1:-1],
                        "confidence": min(0.6 + 0.1 * len(chain[1:-1]), 1.0),
                        "source_paper": paper_id,
                    })
    for claim in claims:
        if claim.get("claim_type") == "causal":
            parts = re.split(r"\s+(?:because|since|due to|through|via|by)\s+", claim.get("claim", ""), flags=re.IGNORECASE)
            if len(parts) >= 2:
                chain = [p.strip()[:60] for p in parts if len(p.strip()) > 5]
                if len(chain) >= 2:
                    chain_key = "→".join(c.lower()[:30] for c in chain)
                    if chain_key not in seen:
                        seen.add(chain_key)
                        mechanisms.append({
                            "mechanism_id": f"mech_{paper_id}_{len(mechanisms):03d}",
                            "cause": chain[0], "effect": chain[-1],
                            "mechanism": " → ".join(chain), "chain_length": len(chain),
                            "intermediates": chain[1:-1], "confidence": 0.7,
                            "source_paper": paper_id,
                            "derived_from_claim": claim.get("claim_id", ""),
                        })
    return mechanisms[:10]


# ─── REV-1.5 Limitation + Weakness Extraction ───

LIMITATION_PATTERNS = [
    r"(?:limitation|limited|weakness|drawback|shortcoming|constraint|caveat)[:\s]+(.{10,200})",
    r"(?:however|nevertheless|nonetheless|on the other hand)[,\s]+(.{10,200})",
    r"(?:future work|further research|remains? (?:to be|an))[:\s]+(.{10,200})",
    r"(?:out of scope|beyond the scope|not addressed)[:\s]+(.{10,200})",
    r"(?:small sample|limited data|restricted to|only applies? to)[:\s]+(.{10,200})",
]

HIDDEN_WEAKNESS_TRIGGERS = {
    "small_sample": ([r"\d{1,3}\s+(?:participants?|subjects?|firms?|companies?|observations?)"], "small sample size may limit statistical power and generalizability"),
    "single_country": ([r"(?:in|from|based on) (?:the )?(?:US|USA|United States|UK|China|India|Germany)"], "single-country study limits cross-cultural generalizability"),
    "single_sector": ([r"(?:financial sector|banking|technology|manufacturing|healthcare)"], "single-sector focus limits cross-sector generalizability"),
    "cross_sectional": ([r"cross-sectional", r"single time point"], "cross-sectional design cannot establish causal direction"),
    "self_report": ([r"self-reported", r"questionnaire", r"survey data"], "self-reported data subject to social desirability and recall bias"),
    "endogeneity": ([r"correlation", r"associated with", r"linked to"], "correlational evidence cannot rule out endogeneity or reverse causality"),
}


def extract_limitations_and_weaknesses(text: str, paper_id: str = "") -> List[Dict[str, Any]]:
    """REV-1.5: Force adversarial reading. Detect stated and hidden weaknesses."""
    limitations, seen = [], set()
    for pattern in LIMITATION_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            t = re.sub(r'\s+', ' ', match.group(1).strip()).rstrip('.')
            n = t.lower().strip()[:60]
            if n not in seen and len(t) >= 10:
                seen.add(n)
                severity = "high" if any(w in t.lower() for w in ["major", "significant", "severe", "critical"]) else ("low" if any(w in t.lower() for w in ["minor", "small", "slight"]) else "medium")
                limitations.append({"limitation_id": f"limit_{paper_id}_{len(limitations):03d}", "limitation": t[:200], "severity": severity, "is_stated": True, "source_paper": paper_id})
    for wtype, (patterns, weakness) in HIDDEN_WEAKNESS_TRIGGERS.items():
        if any(re.search(p, text, re.IGNORECASE) for p in patterns):
            n = weakness.lower()[:60]
            if n not in seen:
                seen.add(n)
                limitations.append({"limitation_id": f"limit_{paper_id}_{len(limitations):03d}", "limitation": weakness, "severity": "medium", "is_stated": False, "weakness_type": wtype, "source_paper": paper_id})
    return limitations[:12]


# ─── REV-1.6 Forced Scientific Object Schema ───

def _detect_domain(text: str) -> str:
    text_lower = text.lower()
    domain_keywords = {
        "finance": ["market", "trading", "price", "volatility", "risk", "portfolio", "asset", "return"],
        "physics": ["quantum", "particle", "field", "energy", "force", "wave", "entropy"],
        "biology": ["cell", "gene", "protein", "organism", "evolution", "species", "dna"],
        "computer science": ["algorithm", "computation", "software", "data", "neural", "machine learning"],
        "economics": ["gdp", "inflation", "monetary", "fiscal", "trade", "supply", "demand"],
        "medicine": ["patient", "treatment", "disease", "clinical", "therapy", "diagnosis"],
        "political science": ["political", "government", "policy", "election", "democracy", "regime"],
        "sociology": ["social", "society", "culture", "institution", "norm", "identity"],
        "psychology": ["cognitive", "behavior", "perception", "memory", "attention", "emotion"],
    }
    scores = {d: sum(1 for kw in kws if kw in text_lower) for d, kws in domain_keywords.items()}
    scores = {k: v for k, v in scores.items() if v > 0}
    return max(scores, key=scores.get) if scores else "general"


@dataclass
class ScientificKnowledgeObject:
    """REV-1.6: Forced Scientific Object Schema. No prose until decomposition complete."""
    paper_title: str = ""
    paper_id: str = ""
    domain: str = ""
    confidence_score: float = 0.0
    claims: List[Dict[str, Any]] = field(default_factory=list)
    explicit_assumptions: List[Dict[str, Any]] = field(default_factory=list)
    implicit_assumptions: List[Dict[str, Any]] = field(default_factory=list)
    mechanisms: List[Dict[str, Any]] = field(default_factory=list)
    limitations: List[Dict[str, Any]] = field(default_factory=list)
    causal_relationships: List[Dict[str, str]] = field(default_factory=list)
    methodology: str = ""
    novel_contribution: str = ""
    authors: List[str] = field(default_factory=list)
    year: str = ""
    doi: str = ""
    source: str = ""
    error: str = ""
    
    @property
    def is_complete(self) -> bool:
        return len(self.claims) >= 1 and len(self.explicit_assumptions) >= 1 and len(self.mechanisms) >= 1
    
    @property
    def decomposition_quality(self) -> float:
        scores = [
            min(len(self.claims) / 3, 1.0),
            min(len(self.explicit_assumptions) / 2, 1.0),
            min(len(self.implicit_assumptions) / 2, 1.0),
            min(len(self.mechanisms) / 2, 1.0),
            min(len(self.limitations) / 2, 1.0),
        ]
        return sum(scores) / len(scores)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "paper_title": self.paper_title, "paper_id": self.paper_id,
            "domain": self.domain, "confidence_score": self.confidence_score,
            "claims": self.claims, "explicit_assumptions": self.explicit_assumptions,
            "implicit_assumptions": self.implicit_assumptions, "mechanisms": self.mechanisms,
            "limitations": self.limitations, "decomposition_quality": self.decomposition_quality,
            "is_complete": self.is_complete,
        }


def decompose_paper(text: str, title: str = "", paper_id: str = "",
                    authors: Optional[List[str]] = None, year: str = "",
                    doi: str = "", source: str = "",
                    claims: Optional[List[Dict]] = None) -> ScientificKnowledgeObject:
    """REV-1 Master: Full structural decomposition of a paper."""
    if not paper_id:
        paper_id = str(uuid.uuid4())[:12]
    
    if claims is None:
        from .rev1_decomposition import extract_claims, extract_explicit_assumptions, infer_implicit_assumptions
        claims = extract_claims(text, paper_id)
        explicit_assumptions = extract_explicit_assumptions(text, paper_id)
        implicit_assumptions = infer_implicit_assumptions(text, claims, paper_id)
    else:
        from .rev1_decomposition import extract_explicit_assumptions, infer_implicit_assumptions
        explicit_assumptions = extract_explicit_assumptions(text, paper_id)
        implicit_assumptions = infer_implicit_assumptions(text, claims, paper_id)
    
    mechanisms = decompose_mechanisms(text, claims, paper_id)
    limitations = extract_limitations_and_weaknesses(text, paper_id)
    domain = _detect_domain(text)
    
    all_confidences = (
        [c.get("confidence", 0.5) for c in claims]
        + [a.get("confidence", 0.5) for a in explicit_assumptions]
        + [m.get("confidence", 0.5) for m in mechanisms]
    )
    avg_confidence = sum(all_confidences) / max(len(all_confidences), 1)
    
    return ScientificKnowledgeObject(
        paper_title=title, paper_id=paper_id, domain=domain,
        confidence_score=avg_confidence, claims=claims,
        explicit_assumptions=explicit_assumptions,
        implicit_assumptions=implicit_assumptions,
        mechanisms=mechanisms, limitations=limitations,
        authors=authors or [], year=year, doi=doi, source=source,
    )


def decompose_papers(texts: List[Dict[str, str]]) -> List[ScientificKnowledgeObject]:
    """REV-1 Batch: Decompose multiple papers."""
    from .rev1_decomposition import extract_claims
    results = []
    for paper in texts:
        try:
            claims = extract_claims(paper.get("text", ""), paper.get("id", ""))
            obj = decompose_paper(
                text=paper.get("text", ""), title=paper.get("title", ""),
                paper_id=paper.get("id", ""), authors=paper.get("authors"),
                year=paper.get("year", ""), doi=paper.get("doi", ""),
                source=paper.get("source", ""), claims=claims,
            )
            results.append(obj)
        except Exception as e:
            results.append(ScientificKnowledgeObject(
                paper_title=paper.get("title", ""),
                paper_id=paper.get("id", ""), error=str(e),
            ))
    return results
