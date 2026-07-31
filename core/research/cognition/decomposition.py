"""
R1 — Knowledge Decomposition Engine

Destroys summarization. Every paper becomes a structured knowledge object.
Extracts: claims, mechanisms, assumptions, equations, limitations, novelty.

Uses rule-based extraction with optional LLM enhancement.
No summaries allowed — only decomposition.
"""

from __future__ import annotations

import logging
import re
import uuid
from typing import Any, Dict, List, Optional

from .schema import (
    Assumption,
    Claim,
    Equation,
    KnowledgeObject,
    Limitation,
    Mechanism,
    NovelContribution,
)

logger = logging.getLogger("oce.rce.decomposition")


# ─── R1.1 Claim Extraction Patterns ───

CLAIM_INDICATORS = [
    r"(?:we (?:show|demonstrate|prove|establish|find|observe))",
    r"(?:results? (?:show|indicate|suggest|demonstrate|reveal))",
    r"(?:evidence (?:suggests|indicates|shows|supports))",
    r"(?:this (?:study|paper|work) (?:shows|demonstrates|proves|establishes))",
    r"(?:our (?:findings?|results?|analysis) (?:show|indicate|suggest))",
    r"(?:it (?:is|was) (?:found|shown|demonstrated|observed))",
    r"(?:the (?:data|evidence|results?) (?:show|indicate|suggest))",
]

CLAIM_PATTERNS = [
    r"(?:we (?:show|demonstrate|prove|establish|find|observe))\s+(?:that\s+)?(.{20,200})",
    r"(?:results? (?:show|indicate|suggest|demonstrate|reveal))\s+(?:that\s+)?(.{20,200})",
    r"(?:this (?:study|paper|work))\s+(?:shows|demonstrates|proves|establishes)\s+(?:that\s+)?(.{20,200})",
    r"(?:our (?:findings?|results?|analysis))\s+(?:show|indicate|suggest)\s+(?:that\s+)?(.{20,200})",
]


# ─── R1.2 Mechanism Extraction Patterns ───

MECHANISM_PATTERNS = [
    # cause → effect
    r"(.{10,80})\s+(?:causes?|leads? to|results? in|produces?|generates?|drives?|induces?)\s+(.{10,80})",
    # via / through mechanism
    r"(.{10,80})\s+(?:via|through|by means of|by|through the mechanism of)\s+(.{10,80})",
    # mediates / amplifies / suppresses
    r"(.{10,80})\s+(?:mediates?|amplifies?|suppresses?|modulates?|attenuates?)\s+(.{10,80})",
]

CAUSAL_CONNECTORS = [
    "because", "due to", "owing to", "as a result of", "consequently",
    "therefore", "thus", "hence", "accordingly", "as a consequence",
]


# ─── R1.3 Assumption Extraction Patterns ───

ASSUMPTION_PATTERNS = [
    r"(?:we assume|assuming|assumption|it is assumed|presupposes?)\s+(?:that\s+)?(.{10,200})",
    r"(?:this (?:requires|depends on|presupposes?))\s+(.{10,200})",
    r"(?:under the assumption|given that|provided that)\s+(.{10,200})",
    r"(?:if we assume|let us assume|suppose that)\s+(.{10,200})",
]

IMPLICIT_ASSUMPTION_INDICATORS = [
    "clearly", "obviously", "naturally", "of course", "undoubtedly",
    "it is well known", "it is widely accepted", "standard",
    "conventional", "established", "well-established",
]


# ─── R1.4 Equation / Math Extraction ───

EQUATION_PATTERNS = [
    # LaTeX-style equations
    r"(\\[a-zA-Z]+\{[^}]*\}(?:\s*\\[a-zA-Z]+\{[^}]*\})*)",
    # Inline math with = sign and variables
    r"([A-Z]\s*=\s*[A-Za-z0-9\s\+\-\*\/\^\(\)\{\}\.,]+)",
    # Greek letter equations
    r"([α-ωΑ-Ω][\s\w]*\s*=\s*[^\.\n]{5,100})",
]

MATH_FRAMEWORKS = {
    "information theory": ["entropy", "shannon", "mutual information", "transfer entropy", "kullback-leibler"],
    "statistics": ["regression", "correlation", "variance", "covariance", "p-value", "hypothesis"],
    "optimization": ["gradient", "convex", "lagrangian", "objective function", "constraint"],
    "dynamical systems": ["differential equation", "phase space", "attractor", "bifurcation", "chaos"],
    "network theory": ["graph", "topology", "node", "edge", "centrality", "degree distribution"],
    "machine learning": ["neural network", "deep learning", "classification", "regression", "training"],
    "economics": ["equilibrium", "utility", "marginal", "supply", "demand", "elasticity"],
    "physics": ["hamiltonian", "lagrangian", "quantum", "thermodynamic", "statistical mechanics"],
}


# ─── R1.5 Limitation Extraction ───

LIMITATION_PATTERNS = [
    r"(?:limitation|limited|weakness|drawback|shortcoming|constraint)[:\s]+(.{10,200})",
    r"(?:however|nevertheless|nonetheless|on the other hand)[,\s]+(.{10,200})",
    r"(?:future work|further research|remains? (?:to be|an))[:\s]+(.{10,200})",
    r"(?:out of scope|beyond the scope|not addressed)[:\s]+(.{10,200})",
    r"(?:small sample|limited data|restricted to|only applies? to)[:\s]+(.{10,200})",
]


# ─── R1.6 Novelty Detection ───

NOVELTY_INDICATORS = [
    r"(?:novel|new|first|original|unprecedented|unique|innovative)\s+(.{10,100})",
    r"(?:we (?:introduce|propose|present|develop|design))\s+(.{10,100})",
    r"(?:no previous|prior work has|existing (?:work|studies|approaches) (?:have not|fail to))\s+(.{10,100})",
    r"(?:unlike previous|in contrast to prior|compared to existing)\s+(.{10,100})",
    r"(?:this is the first|to the best of our knowledge)\s+(.{10,100})",
]


class KnowledgeDecomposer:
    """
    R1 — Main decomposition engine.
    
    Transforms raw paper text into structured KnowledgeObjects.
    Rule-based extraction with confidence scoring.
    
    Usage:
        decomposer = KnowledgeDecomposer()
        knowledge_obj = decomposer.decompose(paper_text, title="...")
    """
    
    def __init__(self, min_claim_confidence: float = 0.3):
        self.min_claim_confidence = min_claim_confidence
    
    def decompose(
        self,
        text: str,
        title: str = "",
        authors: Optional[List[str]] = None,
        year: str = "",
        doi: str = "",
        source_url: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeObject:
        """
        Decompose a paper into a structured knowledge object.
        
        Args:
            text: Full paper text (abstract + body if available)
            title: Paper title
            authors: List of author names
            year: Publication year
            doi: DOI if available
            source_url: URL to source
            metadata: Additional metadata dict
            
        Returns:
            KnowledgeObject with all extracted components
        """
        paper_id = str(uuid.uuid4())[:12]
        
        # Run all extractors
        claims = self._extract_claims(text, paper_id)
        mechanisms = self._extract_mechanisms(text, paper_id)
        assumptions = self._extract_assumptions(text, paper_id)
        equations = self._extract_equations(text, paper_id)
        limitations = self._extract_limitations(text, paper_id)
        novelty = self._extract_novelty(text, paper_id)
        causal_rels = self._extract_causal_relationships(text)
        implicit_theory = self._infer_implicit_theory(text, claims, mechanisms)
        methodology = self._extract_methodology(text)
        domain = self._detect_domain(text)
        
        # Overall confidence
        confidences = [c.confidence for c in claims] + [m.confidence for m in assumptions]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return KnowledgeObject(
            paper_title=title,
            paper_id=paper_id,
            domain=domain,
            confidence_score=avg_confidence,
            main_claims=claims,
            mechanisms=mechanisms,
            assumptions=assumptions,
            equations=equations,
            limitations=limitations,
            novel_contribution=novelty,
            causal_relationships=causal_rels,
            implicit_theory=implicit_theory,
            methodology=methodology,
            authors=authors or [],
            year=year,
            doi=doi,
            source_url=source_url,
        )
    
    def decompose_batch(
        self,
        papers: List[Dict[str, Any]],
    ) -> List[KnowledgeObject]:
        """
        Decompose multiple papers.
        
        Args:
            papers: List of dicts with keys: text, title, authors, year, doi, source_url
            
        Returns:
            List of KnowledgeObjects
        """
        results = []
        for paper in papers:
            try:
                obj = self.decompose(
                    text=paper.get("text", ""),
                    title=paper.get("title", ""),
                    authors=paper.get("authors"),
                    year=paper.get("year", ""),
                    doi=paper.get("doi", ""),
                    source_url=paper.get("source_url", ""),
                    metadata=paper.get("metadata"),
                )
                results.append(obj)
            except Exception as e:
                logger.warning(f"Failed to decompose paper '{paper.get('title', '?')}': {e}")
        return results
    
    # ─── R1.1 Claim Extraction ───
    
    def _extract_claims(self, text: str, paper_id: str) -> List[Claim]:
        """Extract claims from paper text."""
        claims = []
        seen_claims = set()
        
        for pattern in CLAIM_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                claim_text = match.group(1).strip()
                # Deduplicate
                normalized = claim_text.lower().strip()[:60]
                if normalized in seen_claims:
                    continue
                seen_claims.add(normalized)
                
                # Score confidence based on specificity
                confidence = self._score_claim_confidence(claim_text)
                if confidence >= self.min_claim_confidence:
                    claims.append(Claim(
                        claim_id=f"claim_{paper_id}_{len(claims):03d}",
                        claim=claim_text,
                        confidence=confidence,
                        source_paper=paper_id,
                        claim_type="primary" if len(claims) < 3 else "secondary",
                    ))
        
        return claims[:10]  # Cap at 10 claims per paper
    
    def _score_claim_confidence(self, claim_text: str) -> float:
        """Score how likely this is a real claim vs noise."""
        score = 0.5
        # Longer claims with specific content score higher
        if len(claim_text) > 50:
            score += 0.1
        if len(claim_text) > 100:
            score += 0.1
        # Contains specific terms
        if any(w in claim_text.lower() for w in ["significant", "correlation", "predict", "cause", "effect", "increase", "decrease"]):
            score += 0.15
        # Contains numbers/metrics
        if re.search(r"\d+\.?\d*", claim_text):
            score += 0.1
        # Penalize vague claims
        if any(w in claim_text.lower() for w in ["interesting", "important", "relevant", "notable"]):
            score -= 0.15
        return min(max(score, 0.0), 1.0)
    
    # ─── R1.2 Mechanism Extraction ───
    
    def _extract_mechanisms(self, text: str, paper_id: str) -> List[Mechanism]:
        """Extract causal mechanisms."""
        mechanisms = []
        seen = set()
        
        for pattern in MECHANISM_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                cause = match.group(1).strip()[:80]
                effect = match.group(2).strip()[:80]
                
                key = f"{cause.lower()[:40]}->{effect.lower()[:40]}"
                if key in seen:
                    continue
                seen.add(key)
                
                # Identify the mechanism description
                mechanism_desc = self._find_mechanism_description(text, match.end())
                
                confidence = 0.6 if len(cause) > 15 and len(effect) > 15 else 0.4
                
                mechanisms.append(Mechanism(
                    cause=cause,
                    mechanism=mechanism_desc or f"{cause} → {effect}",
                    effect=effect,
                    confidence=confidence,
                    source_paper=paper_id,
                ))
        
        return mechanisms[:8]
    
    def _find_mechanism_description(self, text: str, position: int) -> str:
        """Look for mechanism description near the match."""
        window = text[position:position + 200]
        # Look for explanatory phrases
        for connector in ["by", "via", "through", "because"]:
            idx = window.lower().find(f" {connector} ")
            if 0 < idx < 100:
                return window[idx:idx + 80].strip().rstrip(".,;")
        return ""
    
    # ─── R1.3 Assumption Extraction ───
    
    def _extract_assumptions(self, text: str, paper_id: str) -> List[Assumption]:
        """Extract explicit and implicit assumptions."""
        assumptions = []
        seen = set()
        
        # Explicit assumptions
        for pattern in ASSUMPTION_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                assumption_text = match.group(1).strip()[:150]
                normalized = assumption_text.lower().strip()[:50]
                if normalized in seen:
                    continue
                seen.add(normalized)
                
                assumptions.append(Assumption(
                    assumption=assumption_text,
                    explicit=True,
                    confidence=0.7,
                    source_paper=paper_id,
                ))
        
        # Implicit assumptions — look for "clearly", "obviously", etc.
        for indicator in IMPLICIT_ASSUMPTION_INDICATORS:
            pattern = rf"{indicator}[,\s]+(.{{10,150}})"
            for match in re.finditer(pattern, text, re.IGNORECASE):
                assumption_text = match.group(1).strip()[:150]
                normalized = assumption_text.lower().strip()[:50]
                if normalized in seen:
                    continue
                seen.add(normalized)
                
                assumptions.append(Assumption(
                    assumption=assumption_text,
                    explicit=False,
                    confidence=0.4,
                    source_paper=paper_id,
                ))
        
        return assumptions[:8]
    
    # ─── R1.4 Equation Extraction ───
    
    def _extract_equations(self, text: str, paper_id: str) -> List[Equation]:
        """Extract mathematical frameworks and equations."""
        equations = []
        seen = set()
        
        for pattern in EQUATION_PATTERNS:
            for match in re.finditer(pattern, text):
                eq_text = match.group(1).strip()[:200]
                normalized = eq_text.lower().strip()[:40]
                if normalized in seen or len(eq_text) < 5:
                    continue
                seen.add(normalized)
                
                # Classify the mathematical framework
                framework = self._classify_math_framework(eq_text)
                variables = self._extract_variables(eq_text)
                
                equations.append(Equation(
                    equation_type=framework,
                    variables=variables,
                    mathematical_framework=framework,
                    raw_text=eq_text,
                    source_paper=paper_id,
                ))
        
        return equations[:5]
    
    def _classify_math_framework(self, eq_text: str) -> str:
        """Classify which mathematical framework this belongs to."""
        eq_lower = eq_text.lower()
        for framework, keywords in MATH_FRAMEWORKS.items():
            if any(kw in eq_lower for kw in keywords):
                return framework
        return "general"
    
    def _extract_variables(self, eq_text: str) -> List[str]:
        """Extract variable names from equation text."""
        # Single capital letters used as variables
        variables = re.findall(r'\b([A-Z])\b', eq_text)
        # Greek letters
        greek = re.findall(r'[α-ωΑ-Ω]', eq_text)
        return list(set(variables + greek))[:10]
    
    # ─── R1.5 Limitation Extraction ───
    
    def _extract_limitations(self, text: str, paper_id: str) -> List[Limitation]:
        """Extract stated and hidden limitations."""
        limitations = []
        seen = set()
        
        for pattern in LIMITATION_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                limitation_text = match.group(1).strip()[:150]
                normalized = limitation_text.lower().strip()[:50]
                if normalized in seen:
                    continue
                seen.add(normalized)
                
                severity = self._assess_limitation_severity(limitation_text)
                
                limitations.append(Limitation(
                    limitation=limitation_text,
                    severity=severity,
                    is_stated=True,
                    source_paper=paper_id,
                ))
        
        return limitations[:5]
    
    def _assess_limitation_severity(self, text: str) -> str:
        """Assess how severe a limitation is."""
        text_lower = text.lower()
        high_severity = ["fundamental", "critical", "severe", "major", "significant weakness"]
        low_severity = ["minor", "small", "slight", "marginal", "negligible"]
        
        if any(w in text_lower for w in high_severity):
            return "high"
        if any(w in text_lower for w in low_severity):
            return "low"
        return "medium"
    
    # ─── R1.6 Novelty Detection ───
    
    def _extract_novelty(self, text: str, paper_id: str) -> Optional[NovelContribution]:
        """Detect what's novel about this paper."""
        for pattern in NOVELTY_INDICATORS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                contribution = match.group(1).strip()[:200]
                novelty_score = self._score_novelty(contribution)
                return NovelContribution(
                    contribution=contribution,
                    novelty_score=novelty_score,
                    prior_literature_gap=self._find_prior_gap(text),
                    source_paper=paper_id,
                )
        return None
    
    def _score_novelty(self, text: str) -> float:
        """Score how novel a contribution is."""
        score = 0.5
        text_lower = text.lower()
        if any(w in text_lower for w in ["first", "novel", "new", "original", "unprecedented"]):
            score += 0.3
        if any(w in text_lower for w in ["improve", "outperform", "better", "superior"]):
            score += 0.15
        if any(w in text_lower for w in ["similar", "comparable", "consistent with"]):
            score -= 0.2
        return min(max(score, 0.0), 1.0)
    
    def _find_prior_gap(self, text: str) -> str:
        """Find what gap in prior literature this paper fills."""
        gap_patterns = [
            r"(?:no previous|prior work has not|existing (?:work|studies) (?:have not|fail to))\s+(.{10,150})",
            r"(?:gap in|lack of|absence of)\s+(.{10,150})",
            r"(?:remains? (?:unclear|unknown|an open question))\s+(.{10,150})",
        ]
        for pattern in gap_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:150]
        return ""
    
    # ─── Helper Methods ───
    
    def _extract_causal_relationships(self, text: str) -> List[Dict[str, str]]:
        """Extract causal relationship triples."""
        relationships = []
        for pattern in MECHANISM_PATTERNS[:2]:  # Only direct causal patterns
            for match in re.finditer(pattern, text, re.IGNORECASE):
                relationships.append({
                    "cause": match.group(1).strip()[:60],
                    "relationship": "causes",
                    "effect": match.group(2).strip()[:60],
                })
        return relationships[:5]
    
    def _infer_implicit_theory(
        self, text: str, claims: List[Claim], mechanisms: List[Mechanism]
    ) -> str:
        """Infer the implicit theory connecting claims and mechanisms."""
        if not claims or not mechanisms:
            return ""
        
        # Build a simple theory statement from the top claim + top mechanism
        top_claim = claims[0].claim if claims else ""
        top_mechanism = mechanisms[0].mechanism if mechanisms else ""
        
        if top_claim and top_mechanism:
            return f"Implicit theory: {top_claim} operates through {top_mechanism}"
        return ""
    
    def _extract_methodology(self, text: str) -> str:
        """Extract methodology description."""
        method_patterns = [
            r"(?:we (?:use|employ|apply|adopt|utilize))\s+(.{10,150})",
            r"(?:method(?:ology)?|approach|technique)[:\s]+(.{10,150})",
            r"(?:experiment(?:al)? setup|study design)[:\s]+(.{10,150})",
        ]
        for pattern in method_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:150]
        return ""
    
    def _detect_domain(self, text: str) -> str:
        """Detect the scientific domain of the paper."""
        text_lower = text.lower()
        domain_keywords = {
            "finance": ["market", "trading", "price", "volatility", "risk", "portfolio", "asset"],
            "physics": ["quantum", "particle", "field", "energy", "force", "wave", "entropy"],
            "biology": ["cell", "gene", "protein", "organism", "evolution", "species", "dna"],
            "computer science": ["algorithm", "computation", "software", "hardware", "data", "neural"],
            "economics": ["supply", "demand", "gdp", "inflation", "monetary", "fiscal", "trade"],
            "medicine": ["patient", "treatment", "disease", "clinical", "therapy", "diagnosis"],
            "mathematics": ["theorem", "proof", "conjecture", "lemma", "corollary", "axiom"],
        }
        
        scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[domain] = score
        
        if scores:
            return max(scores, key=scores.get)
        return "general"
