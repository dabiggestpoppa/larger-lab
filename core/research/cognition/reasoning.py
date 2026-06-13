"""
R3 — Cross-Document Reasoning Engine

Makes papers reason against each other:
- Cross-paper comparison
- Contradiction detection
- Assumption conflict detection
- Consensus detection
- Explanatory strength evaluation
- Multi-paper reasoning chains
- Unified reasoning layer
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Set, Tuple

from .schema import KnowledgeObject, Claim, Mechanism

logger = logging.getLogger("oce.rce.reasoning")


# Contradiction indicator phrases
CONTRADICTION_PHRASES = [
    "however", "but", "in contrast", "unlike", "contrary to",
    "opposite", "reverse", "inverse", "negatively", "adversely",
    "worse", "lower", "decreased", "reduced", "failed",
    "does not support", "contradicts", "challenges", "refutes",
    "inconsistent with", "opposes", "disagrees with",
]

# Consensus indicator phrases
CONSENSUS_PHRASES = [
    "consistent with", "agrees with", "supports", "confirms",
    "corroborates", "validates", "reinforces", "aligns with",
    "in agreement", "similarly", "likewise", "also found",
    "replicates", "reproduces", "confirms that",
]


class CrossDocumentReasoner:
    """
    R3 — Cross-Document Reasoning Engine.
    
    Takes multiple KnowledgeObjects and performs adversarial reasoning:
    1. Cross-paper comparison
    2. Contradiction detection
    3. Assumption conflict detection
    4. Consensus detection
    5. Explanatory strength evaluation
    6. Multi-paper reasoning chains
    
    Usage:
        reasoner = CrossDocumentReasoner()
        results = reasoner.reason(knowledge_objects)
    """
    
    def __init__(
        self,
        contradiction_threshold: float = 0.6,
        consensus_threshold: float = 0.5,
        similarity_threshold: float = 0.3,
    ):
        self.contradiction_threshold = contradiction_threshold
        self.consensus_threshold = consensus_threshold
        self.similarity_threshold = similarity_threshold
    
    def reason(
        self, knowledge_objects: List[KnowledgeObject]
    ) -> Dict[str, Any]:
        """
        Perform cross-document reasoning over all knowledge objects.
        
        Returns:
            Dict with: contradictions, consensus, assumption_conflicts,
                       explanatory_ranking, reasoning_chains, unified_reasoning
        """
        if len(knowledge_objects) < 2:
            return self._empty_result()
        
        # R3.1 — Cross-paper comparison
        comparisons = self._compare_papers(knowledge_objects)
        
        # R3.2 — Contradiction detection
        contradictions = self._detect_contradictions(knowledge_objects, comparisons)
        
        # R3.3 — Assumption conflict detection
        assumption_conflicts = self._detect_assumption_conflicts(knowledge_objects)
        
        # R3.4 — Consensus detection
        consensus = self._detect_consensus(knowledge_objects, comparisons)
        
        # R3.5 — Explanatory strength evaluation
        explanatory_ranking = self._rank_explanatory_strength(knowledge_objects)
        
        # R3.6 — Multi-paper reasoning chains
        reasoning_chains = self._build_reasoning_chains(knowledge_objects)
        
        # R3.7 — Unified reasoning layer
        unified = self._unified_reasoning(
            contradictions, consensus, assumption_conflicts, explanatory_ranking
        )
        
        return {
            "comparisons": comparisons,
            "contradictions": contradictions,
            "consensus": consensus,
            "assumption_conflicts": assumption_conflicts,
            "explanatory_ranking": explanatory_ranking,
            "reasoning_chains": reasoning_chains,
            "unified_reasoning": unified,
            "stats": {
                "num_papers": len(knowledge_objects),
                "num_contradictions": len(contradictions),
                "num_consensus": len(consensus),
                "num_assumption_conflicts": len(assumption_conflicts),
                "num_reasoning_chains": len(reasoning_chains),
            },
        }
    
    # ─── R3.1 Cross-Paper Comparison ───
    
    def _compare_papers(
        self, knowledge_objects: List[KnowledgeObject]
    ) -> List[Dict[str, Any]]:
        """Compare all pairs of papers."""
        comparisons = []
        
        for i, obj_a in enumerate(knowledge_objects):
            for j, obj_b in enumerate(knowledge_objects):
                if j <= i:
                    continue
                
                comparison = self._compare_pair(obj_a, obj_b)
                if comparison["similarity"] >= self.similarity_threshold:
                    comparisons.append(comparison)
        
        return comparisons
    
    def _compare_pair(
        self, obj_a: KnowledgeObject, obj_b: KnowledgeObject
    ) -> Dict[str, Any]:
        """Compare two knowledge objects."""
        # Claim similarity
        claim_sim = self._text_list_similarity(
            [c.claim for c in obj_a.main_claims],
            [c.claim for c in obj_b.main_claims],
        )
        
        # Mechanism overlap
        mech_sim = self._text_list_similarity(
            [m.mechanism for m in obj_a.mechanisms],
            [m.mechanism for m in obj_b.mechanisms],
        )
        
        # Domain match
        domain_match = 1.0 if obj_a.domain == obj_b.domain and obj_a.domain else 0.0
        
        # Overall similarity
        overall = (claim_sim * 0.4 + mech_sim * 0.3 + domain_match * 0.3)
        
        return {
            "paper_a": obj_a.paper_title or obj_a.paper_id,
            "paper_b": obj_b.paper_title or obj_b.paper_id,
            "claim_similarity": claim_sim,
            "mechanism_similarity": mech_sim,
            "domain_match": domain_match,
            "similarity": overall,
        }
    
    # ─── R3.2 Contradiction Detection ───
    
    def _detect_contradictions(
        self,
        knowledge_objects: List[KnowledgeObject],
        comparisons: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Detect contradictions between papers."""
        contradictions = []
        checked_pairs: Set[Tuple[str, str]] = set()
        
        # First: check pairs from comparisons (similar papers)
        for comp in comparisons:
            obj_a = self._find_by_title(knowledge_objects, comp["paper_a"])
            obj_b = self._find_by_title(knowledge_objects, comp["paper_b"])
            
            if not obj_a or not obj_b:
                continue
            
            pair_key = tuple(sorted([comp["paper_a"], comp["paper_b"]]))
            checked_pairs.add(pair_key)
            
            contradictions.extend(self._check_pair_contradictions(
                obj_a, obj_b, comp["paper_a"], comp["paper_b"]
            ))
        
        # Second: also check same-domain pairs that might have been missed
        # (low surface similarity but same domain = potential hidden contradiction)
        for i, obj_a in enumerate(knowledge_objects):
            for j, obj_b in enumerate(knowledge_objects):
                if j <= i:
                    continue
                pair_key = tuple(sorted([obj_a.paper_title or obj_a.paper_id, obj_b.paper_title or obj_b.paper_id]))
                if pair_key in checked_pairs:
                    continue
                # Only check same-domain pairs
                if obj_a.domain and obj_b.domain and obj_a.domain == obj_b.domain:
                    contradictions.extend(self._check_pair_contradictions(
                        obj_a, obj_b,
                        obj_a.paper_title or obj_a.paper_id,
                        obj_b.paper_title or obj_b.paper_id,
                    ))
                    checked_pairs.add(pair_key)
        
        return contradictions
    
    def _check_pair_contradictions(
        self,
        obj_a: KnowledgeObject,
        obj_b: KnowledgeObject,
        title_a: str,
        title_b: str,
    ) -> List[Dict[str, Any]]:
        """Check a single pair of papers for contradictions."""
        contradictions = []
        
        # Check claim-level contradictions
        for claim_a in obj_a.main_claims:
            for claim_b in obj_b.main_claims:
                contradiction = self._check_claim_contradiction(claim_a, claim_b)
                if contradiction:
                    contradictions.append({
                        "type": "claim_contradiction",
                        "paper_a": title_a,
                        "paper_b": title_b,
                        "claim_a": claim_a.claim,
                        "claim_b": claim_b.claim,
                        "severity": contradiction["severity"],
                        "explanation": contradiction["explanation"],
                    })
        
        # Check mechanism contradictions
        for mech_a in obj_a.mechanisms:
            for mech_b in obj_b.mechanisms:
                contradiction = self._check_mechanism_contradiction(mech_a, mech_b)
                if contradiction:
                    contradictions.append({
                        "type": "mechanism_contradiction",
                        "paper_a": title_a,
                        "paper_b": title_b,
                        "mechanism_a": mech_a.mechanism,
                        "mechanism_b": mech_b.mechanism,
                        "severity": contradiction["severity"],
                        "explanation": contradiction["explanation"],
                    })
        
        return contradictions
    
    def _check_claim_contradiction(
        self, claim_a: Claim, claim_b: Claim
    ) -> Optional[Dict[str, Any]]:
        """Check if two claims contradict each other."""
        text_a = claim_a.claim.lower()
        text_b = claim_b.claim.lower()
        
        # Check for negation patterns
        negation_patterns = [
            (r"(?:increase|higher|more|positive|improve)", r"(?:decrease|lower|negative|worsen|decline)"),
            (r"(?:positive|direct)", r"(?:negative|inverse|reverse)"),
            (r"(?:significant|strong)", r"(?:not significant|no effect|weak)"),
            (r"(?:causes?|leads? to|results? in)", r"(?:prevents?|inhibits?|blocks?)"),
            (r"(?:predicts?|predictive)", r"(?:no (?:significant )?predictive|does not predict|fail to predict|no relationship)"),
            (r"(?:precede|precedes?|before)", r"(?:does not precede|not precede|after|follows?)"),
        ]
        
        for pos_pattern, neg_pattern in negation_patterns:
            a_has_pos = bool(re.search(pos_pattern, text_a))
            b_has_neg = bool(re.search(neg_pattern, text_b))
            
            if a_has_pos and b_has_neg:
                # Check if they're talking about the same thing
                similarity = SequenceMatcher(None, text_a, text_b).ratio()
                if similarity >= 0.2:  # Same topic, opposite conclusion
                    return {
                        "severity": min(0.5 + similarity, 1.0),
                        "explanation": (
                            f"Claim A asserts positive relationship, "
                            f"Claim B asserts negative relationship on similar topic "
                            f"(similarity={similarity:.2f})"
                        ),
                    }
        
        # Also check: same subject, opposite conclusion (broader)
        # Extract key noun phrases and check for opposition
        key_terms_a = set(re.findall(r'\b[a-z]{4,}\b', text_a)) - {"that", "this", "with", "from", "have", "been", "were", "will", "would", "could", "should", "their", "these", "those", "about", "into", "through", "between", "under", "over"}
        key_terms_b = set(re.findall(r'\b[a-z]{4,}\b', text_b)) - {"that", "this", "with", "from", "have", "been", "were", "will", "would", "could", "should", "their", "these", "those", "about", "into", "through", "between", "under", "over"}
        
        overlap = key_terms_a & key_terms_b
        if len(overlap) >= 3:
            # They share key terms — check for negation opposition
            a_positive = bool(re.search(r'(?:predicts?|increases?|causes?|leads? to|positive|significant)', text_a))
            b_negative = bool(re.search(r'(?:no |not |does not |fail to |without |lack of )(?:predict|increase|cause|lead|positive|significant|effect|relationship)', text_b))
            
            if a_positive and b_negative:
                return {
                    "severity": 0.7,
                    "explanation": (
                        f"Claims share key terms ({', '.join(list(overlap)[:3])}) "
                        f"but assert opposite relationships"
                    ),
                }
        
        return None
    
    def _check_mechanism_contradiction(
        self, mech_a: Mechanism, mech_b: Mechanism
    ) -> Optional[Dict[str, Any]]:
        """Check if two mechanisms contradict."""
        # Same cause, opposite effect
        cause_sim = SequenceMatcher(None, mech_a.cause.lower(), mech_b.cause.lower()).ratio()
        effect_sim = SequenceMatcher(None, mech_a.effect.lower(), mech_b.effect.lower()).ratio()
        
        if cause_sim >= 0.5 and effect_sim <= 0.3:
            # Same cause, different effect — potential contradiction
            return {
                "severity": 0.6,
                "explanation": (
                    f"Same cause ({mech_a.cause[:40]}) leads to different effects: "
                    f"'{mech_a.effect[:40]}' vs '{mech_b.effect[:40]}'"
                ),
            }
        
        return None
    
    # ─── R3.3 Assumption Conflict Detection ───
    
    def _detect_assumption_conflicts(
        self, knowledge_objects: List[KnowledgeObject]
    ) -> List[Dict[str, Any]]:
        """Detect when papers have conflicting assumptions."""
        conflicts = []
        
        for i, obj_a in enumerate(knowledge_objects):
            for j, obj_b in enumerate(knowledge_objects):
                if j <= i:
                    continue
                
                for assump_a in obj_a.assumptions:
                    for assump_b in obj_b.assumptions:
                        conflict = self._check_assumption_conflict(
                            assump_a, assump_b, obj_a, obj_b
                        )
                        if conflict:
                            conflicts.append(conflict)
        
        return conflicts
    
    def _check_assumption_conflict(
        self, assump_a: Any, assump_b: Any,
        obj_a: KnowledgeObject, obj_b: KnowledgeObject,
    ) -> Optional[Dict[str, Any]]:
        """Check if two assumptions conflict."""
        text_a = assump_a.assumption.lower()
        text_b = assump_b.assumption.lower()
        
        # Direct negation
        negation_pairs = [
            ("efficient", "inefficient"),
            ("stable", "unstable"),
            ("linear", "nonlinear"),
            ("symmetric", "asymmetric"),
            ("homogeneous", "heterogeneous"),
            ("stationary", "non-stationary"),
            ("normal", "abnormal"),
            ("optimal", "suboptimal"),
            ("rational", "irrational"),
        ]
        
        for term_a, term_b in negation_pairs:
            if (term_a in text_a and term_b in text_b) or (term_b in text_a and term_a in text_b):
                similarity = SequenceMatcher(None, text_a, text_b).ratio()
                if similarity >= 0.3:
                    return {
                        "type": "assumption_conflict",
                        "paper_a": obj_a.paper_title or obj_a.paper_id,
                        "paper_b": obj_b.paper_title or obj_b.paper_id,
                        "assumption_a": assump_a.assumption,
                        "assumption_b": assump_b.assumption,
                        "conflict_type": f"{term_a} vs {term_b}",
                        "severity": 0.7,
                    }
        
        return None
    
    # ─── R3.4 Consensus Detection ───
    
    def _detect_consensus(
        self,
        knowledge_objects: List[KnowledgeObject],
        comparisons: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Find where multiple papers independently agree."""
        consensus_items = []
        
        # Group by domain
        domain_groups: Dict[str, List[KnowledgeObject]] = defaultdict(list)
        for obj in knowledge_objects:
            domain_groups[obj.domain].append(obj)
        
        for domain, objects in domain_groups.items():
            if len(objects) < 2:
                continue
            
            # Find claims that appear in multiple papers
            claim_texts: Dict[str, List[str]] = defaultdict(list)
            for obj in objects:
                for claim in obj.main_claims:
                    # Normalize for comparison
                    normalized = self._normalize_claim(claim.claim)
                    claim_texts[normalized].append(obj.paper_title or obj.paper_id)
            
            # Claims appearing in 2+ papers = consensus
            for normalized_claim, papers in claim_texts.items():
                if len(papers) >= 2:
                    consensus_items.append({
                        "type": "claim_consensus",
                        "domain": domain,
                        "claim": normalized_claim[:200],
                        "supporting_papers": papers,
                        "consensus_strength": len(papers) / len(objects),
                        "num_supporting": len(papers),
                    })
        
        return consensus_items
    
    # ─── R3.5 Explanatory Strength Evaluation ───
    
    def _rank_explanatory_strength(
        self, knowledge_objects: List[KnowledgeObject]
    ) -> List[Dict[str, Any]]:
        """Rank papers by how well they explain their domain."""
        rankings = []
        
        for obj in knowledge_objects:
            score = self._calculate_explanatory_strength(obj)
            rankings.append({
                "paper": obj.paper_title or obj.paper_id,
                "domain": obj.domain,
                "explanatory_score": score,
                "factors": {
                    "claim_count": len(obj.main_claims),
                    "mechanism_count": len(obj.mechanisms),
                    "has_equations": len(obj.equations) > 0,
                    "has_limitations": len(obj.limitations) > 0,
                    "has_novelty": obj.novel_contribution is not None,
                    "extraction_completeness": obj.extraction_completeness,
                },
            })
        
        rankings.sort(key=lambda x: x["explanatory_score"], reverse=True)
        return rankings
    
    def _calculate_explanatory_strength(self, obj: KnowledgeObject) -> float:
        """Calculate how well a paper explains its domain."""
        score = 0.0
        
        # More claims = more comprehensive
        score += min(len(obj.main_claims) / 5, 1.0) * 0.2
        
        # Mechanisms show causal understanding
        score += min(len(obj.mechanisms) / 3, 1.0) * 0.25
        
        # Equations show formal rigor
        score += min(len(obj.equations) / 2, 1.0) * 0.15
        
        # Acknowledging limitations shows maturity
        score += min(len(obj.limitations) / 2, 1.0) * 0.1
        
        # Novel contribution
        if obj.novel_contribution:
            score += obj.novel_contribution.novelty_score * 0.15
        
        # Extraction completeness
        score += obj.extraction_completeness * 0.15
        
        return min(score, 1.0)
    
    # ─── R3.6 Multi-Paper Reasoning Chains ───
    
    def _build_reasoning_chains(
        self, knowledge_objects: List[KnowledgeObject]
    ) -> List[Dict[str, Any]]:
        """Build reasoning chains across multiple papers."""
        chains = []
        
        # Collect all causal edges
        edges: Dict[str, List[Tuple[str, float, str]]] = defaultdict(list)
        
        for obj in knowledge_objects:
            for mech in obj.mechanisms:
                cause = self._normalize_claim(mech.cause)
                effect = self._normalize_claim(mech.effect)
                if cause and effect:
                    edges[cause].append((effect, mech.confidence, obj.paper_id))
        
        # Find cross-paper chains
        for start in edges:
            visited_papers: Set[str] = set()
            chain = [start]
            current = start
            chain_confidence = 1.0
            chain_papers: List[str] = []
            
            for _ in range(6):  # Max chain length
                if current not in edges or not edges[current]:
                    break
                
                # Pick highest confidence next
                next_node, conf, paper_id = max(edges[current], key=lambda x: x[1])
                
                if next_node in chain:  # Avoid cycles
                    break
                
                chain.append(next_node)
                chain_confidence *= conf
                chain_papers.append(paper_id)
                visited_papers.add(paper_id)
                current = next_node
            
            if len(chain) >= 3 and len(visited_papers) >= 2:
                chains.append({
                    "chain": chain,
                    "length": len(chain),
                    "confidence": chain_confidence ** (1 / len(chain)),
                    "papers_involved": list(visited_papers),
                    "type": "cross_paper_reasoning",
                })
        
        return chains
    
    # ─── R3.7 Unified Reasoning Layer ───
    
    def _unified_reasoning(
        self,
        contradictions: List[Dict[str, Any]],
        consensus: List[Dict[str, Any]],
        assumption_conflicts: List[Dict[str, Any]],
        explanatory_ranking: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Produce unified machine judgment."""
        # Determine overall landscape
        num_contradictions = len(contradictions)
        num_consensus = len(consensus)
        num_conflicts = len(assumption_conflicts)
        
        # Scientific maturity assessment
        if num_consensus > num_contradictions:
            landscape = "mature"
            maturity_note = (
                f"Strong consensus ({num_consensus} areas) with limited contradiction "
                f"({num_contradictions} areas). Domain is well-established."
            )
        elif num_contradictions > num_consensus * 2:
            landscape = "contested"
            maturity_note = (
                f"High contradiction ({num_contradictions} areas) relative to consensus "
                f"({num_consensus} areas). Domain is actively debated."
            )
        else:
            landscape = "developing"
            maturity_note = (
                f"Balanced consensus ({num_consensus}) and contradiction ({num_contradictions}). "
                f"Domain is in active development."
            )
        
        # Key tensions
        key_tensions = []
        for c in contradictions[:3]:
            key_tensions.append({
                "between": [c.get("paper_a", "?"), c.get("paper_b", "?")],
                "issue": c.get("explanation", "Unknown conflict"),
                "severity": c.get("severity", 0.5),
            })
        
        # Strongest theories
        top_theories = []
        for r in explanatory_ranking[:3]:
            top_theories.append({
                "paper": r["paper"],
                "score": r["explanatory_score"],
                "domain": r["domain"],
            })
        
        return {
            "landscape": landscape,
            "maturity_note": maturity_note,
            "key_tensions": key_tensions,
            "strongest_theories": top_theories,
            "assumption_conflicts_count": num_conflicts,
            "overall_confidence": self._calculate_overall_confidence(
                contradictions, consensus, assumption_conflicts
            ),
        }
    
    def _calculate_overall_confidence(
        self,
        contradictions: List[Dict[str, Any]],
        consensus: List[Dict[str, Any]],
        assumption_conflicts: List[Dict[str, Any]],
    ) -> float:
        """Calculate overall confidence in the reasoning."""
        # More consensus = higher confidence
        consensus_boost = min(len(consensus) * 0.1, 0.3)
        
        # More contradictions = lower confidence
        contradiction_penalty = min(len(contradictions) * 0.05, 0.2)
        
        # Assumption conflicts reduce confidence
        conflict_penalty = min(len(assumption_conflicts) * 0.03, 0.15)
        
        return min(max(0.5 + consensus_boost - contradiction_penalty - conflict_penalty, 0.0), 1.0)
    
    # ─── Helper Methods ───
    
    def _find_by_title(
        self, knowledge_objects: List[KnowledgeObject], title: str
    ) -> Optional[KnowledgeObject]:
        """Find a knowledge object by title or ID."""
        for obj in knowledge_objects:
            if obj.paper_title == title or obj.paper_id == title:
                return obj
        return None
    
    def _text_list_similarity(
        self, texts_a: List[str], texts_b: List[str]
    ) -> float:
        """Calculate maximum similarity between two lists of texts."""
        if not texts_a or not texts_b:
            return 0.0
        
        max_sim = 0.0
        for a in texts_a:
            for b in texts_b:
                sim = SequenceMatcher(None, a.lower(), b.lower()).ratio()
                max_sim = max(max_sim, sim)
        
        return max_sim
    
    def _normalize_claim(self, text: str) -> str:
        """Normalize a claim for comparison."""
        # Lowercase, remove extra whitespace, strip
        normalized = re.sub(r'\s+', ' ', text.lower().strip())
        # Remove common prefixes
        normalized = re.sub(r'^(we (?:show|demonstrate|find|observe) that)\s+', '', normalized)
        return normalized[:100]
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result when not enough papers."""
        return {
            "comparisons": [],
            "contradictions": [],
            "consensus": [],
            "assumption_conflicts": [],
            "explanatory_ranking": [],
            "reasoning_chains": [],
            "unified_reasoning": {
                "landscape": "insufficient_data",
                "maturity_note": "Need at least 2 papers for cross-document reasoning.",
                "key_tensions": [],
                "strongest_theories": [],
                "overall_confidence": 0.0,
            },
            "stats": {
                "num_papers": 0,
                "num_contradictions": 0,
                "num_consensus": 0,
                "num_assumption_conflicts": 0,
                "num_reasoning_chains": 0,
            },
        }
