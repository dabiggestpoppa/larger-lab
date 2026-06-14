"""
REV-2: Adversarial Scientific Reasoning Engine

Teaches machine skepticism. Forces contradiction pressure, alternative
explanations, scientific attack, and boundary detection.

6 engines:
- REV-2.1: Contradiction Detection Engine
- REV-2.2: Contradiction Pressure Engine
- REV-2.3: Alternative Explanation Generator
- REV-2.4: Scientific Skeptic Engine
- REV-2.5: Boundary Condition Detector
- REV-2.6: Conflict Memory Layer

Anchor principle: No reconciliation before attack. Assume papers are wrong.
"""

from __future__ import annotations
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("oce.rce.rev2")


# ─── REV-2.1 Contradiction Detection Engine ───

def detect_contradictions(objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    REV-2.1: Identify claim conflicts between papers.
    Not semantic similarity — logical conflict.
    """
    contradictions = []
    
    for i, obj_a in enumerate(objects):
        for j, obj_b in enumerate(objects):
            if j <= i:
                continue
            
            claims_a = obj_a.get("claims", [])
            claims_b = obj_b.get("claims", [])
            
            for claim_a in claims_a:
                for claim_b in claims_b:
                    conflict = _check_claim_conflict(claim_a, claim_b)
                    if conflict:
                        contradictions.append({
                            "type": "claim_contradiction",
                            "paper_a": obj_a.get("paper_title", obj_a.get("paper_id", "?")),
                            "paper_b": obj_b.get("paper_title", obj_b.get("paper_id", "?")),
                            "claim_a": claim_a.get("claim", ""),
                            "claim_b": claim_b.get("claim", ""),
                            "severity": conflict["severity"],
                            "explanation": conflict["explanation"],
                        })
            
            # Check assumption conflicts
            assumptions_a = obj_a.get("explicit_assumptions", []) + obj_a.get("implicit_assumptions", [])
            assumptions_b = obj_b.get("explicit_assumptions", []) + obj_b.get("implicit_assumptions", [])
            
            for assump_a in assumptions_a:
                for assump_b in assumptions_b:
                    conflict = _check_assumption_conflict(assump_a, assump_b)
                    if conflict:
                        contradictions.append({
                            "type": "assumption_conflict",
                            "paper_a": obj_a.get("paper_title", "?"),
                            "paper_b": obj_b.get("paper_title", "?"),
                            "assumption_a": assump_a.get("assumption", ""),
                            "assumption_b": assump_b.get("assumption", ""),
                            "conflict_type": conflict["conflict_type"],
                            "severity": conflict["severity"],
                        })
    
    return contradictions


def _check_claim_conflict(claim_a: Dict, claim_b: Dict) -> Optional[Dict[str, Any]]:
    """Check if two claims logically conflict."""
    text_a = claim_a.get("claim", "").lower()
    text_b = claim_b.get("claim", "").lower()
    
    # Negation patterns
    negation_pairs = [
        (r"(?:increase|higher|more|positive|improve|amplify)", r"(?:decrease|lower|negative|worsen|decline|reduce)"),
        (r"(?:positive|direct|significant|strong)", r"(?:negative|inverse|weak|not significant|no effect)"),
        (r"(?:causes?|leads? to|results? in|produces?)", r"(?:prevents?|inhibits?|blocks?|no effect|no relationship)"),
        (r"(?:predict|predictive|explains?)", r"(?:no predictive|does not predict|fails to explain|no relationship)"),
    ]
    
    for pos_pattern, neg_pattern in negation_pairs:
        a_has_pos = bool(re.search(pos_pattern, text_a))
        b_has_neg = bool(re.search(neg_pattern, text_b))
        
        if a_has_pos and b_has_neg:
            # Check if they're talking about the same thing
            from difflib import SequenceMatcher
            similarity = SequenceMatcher(None, text_a, text_b).ratio()
            if similarity >= 0.2:
                return {
                    "severity": min(0.5 + similarity, 1.0),
                    "explanation": f"Claim A asserts positive relationship, Claim B asserts negative relationship on similar topic (similarity={similarity:.2f})",
                }
    
    return None


def _check_assumption_conflict(assump_a: Dict, assump_b: Dict) -> Optional[Dict[str, Any]]:
    """Check if two assumptions conflict."""
    text_a = assump_a.get("assumption", "").lower()
    text_b = assump_b.get("assumption", "").lower()
    
    negation_pairs = [
        ("efficient", "inefficient"), ("stable", "unstable"), ("linear", "nonlinear"),
        ("symmetric", "asymmetric"), ("homogeneous", "heterogeneous"),
        ("stationary", "non-stationary"), ("rational", "irrational"),
        ("optimal", "suboptimal"), ("normal", "abnormal"),
    ]
    
    for term_a, term_b in negation_pairs:
        if (term_a in text_a and term_b in text_b) or (term_b in text_a and term_a in text_b):
            return {
                "conflict_type": f"{term_a} vs {term_b}",
                "severity": 0.7,
            }
    
    return None


# ─── REV-2.2 Contradiction Pressure Engine ───

def pressure_test_contradiction(contradiction: Dict[str, Any]) -> List[str]:
    """
    REV-2.2: Never reconcile contradiction immediately.
    Force machine to generate multiple explanations for conflict.
    """
    claim_a = contradiction.get("claim_a", "")
    claim_b = contradiction.get("claim_b", "")
    
    explanations = [
        f"Methodological difference: papers may use different measures or samples",
        f"Contextual difference: findings may apply to different populations or time periods",
        f"Assumption difference: underlying assumptions may differ between studies",
        f"Measurement difference: constructs may be operationalized differently",
        f"Publication bias: one or both results may be affected by selective reporting",
    ]
    
    # Add specific explanations based on the claims
    if "sample" in claim_a.lower() or "sample" in claim_b.lower():
        explanations.append("Sample composition difference: different populations studied")
    
    if "time" in claim_a.lower() or "period" in claim_a.lower() or "time" in claim_b.lower():
        explanations.append("Temporal difference: findings may vary across time periods")
    
    if "sector" in claim_a.lower() or "industry" in claim_a.lower() or "sector" in claim_b.lower():
        explanations.append("Sector heterogeneity: effects may differ across industries")
    
    return explanations


# ─── REV-2.3 Alternative Explanation Generator ───

def generate_alternative_explanations(claim: Dict[str, Any]) -> List[str]:
    """
    REV-2.3: Generate competing explanations beyond paper conclusions.
    Scientists always consider alternatives.
    """
    claim_text = claim.get("claim", "")
    alternatives = [
        f"Reverse causality: the observed effect may run in the opposite direction",
        f"Omitted variable: an unmeasured factor may drive both observed variables",
        f"Selection bias: the sample may not be representative of the broader population",
        f"Measurement error: the key constructs may not be accurately captured",
        f"Context dependency: the finding may only hold under specific conditions",
    ]
    
    # Add claim-specific alternatives
    if "risk" in claim_text.lower():
        alternatives.append("Risk perception vs actual risk: perceived risk may differ from objective risk")
    if "investment" in claim_text.lower() or "capital" in claim_text.lower():
        alternatives.append("Liquidity constraints: investment changes may reflect liquidity rather than risk perception")
    if "political" in claim_text.lower() or "geopolitical" in claim_text.lower():
        alternatives.append("Proxy mismatch: political risk measures may capture different underlying phenomena")
    
    return alternatives


# ─── REV-2.4 Scientific Skeptic Engine ───

def scientific_attack(claim: Dict[str, Any], paper_object: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    REV-2.4: Machine attacks conclusions aggressively.
    No trusting authors. Assume conclusion is wrong, find weaknesses.
    """
    claim_text = claim.get("claim", "")
    limitations = paper_object.get("limitations", [])
    
    attacks = []
    
    # Attack based on limitations
    for lim in limitations:
        attacks.append({
            "attack_type": "limitation_based",
            "weakness": f"Limitation undermines claim: {lim.get('limitation', '')}",
            "severity": lim.get("severity", "medium"),
        })
    
    # Attack based on assumptions
    implicit_assumptions = paper_object.get("implicit_assumptions", [])
    for assump in implicit_assumptions:
        attacks.append({
            "attack_type": "assumption_based",
            "weakness": f"Claim depends on unstated assumption: {assump.get('assumption', '')}",
            "severity": "medium",
        })
    
    # Generic scientific attacks
    generic_attacks = [
        {"attack_type": "causality", "weakness": "Claim asserts causality but evidence may be correlational", "severity": "high"},
        {"attack_type": "generalizability", "weakness": "Finding may not generalize beyond studied population", "severity": "medium"},
        {"attack_type": "replication", "weakness": "Result may not replicate in different samples or contexts", "severity": "low"},
    ]
    
    # Only add generic attacks if no specific ones found
    if len(attacks) < 2:
        attacks.extend(generic_attacks[:2])
    
    return attacks[:5]


# ─── REV-2.5 Boundary Condition Detector ───

def detect_boundary_conditions(claim: Dict[str, Any], paper_object: Dict[str, Any]) -> List[str]:
    """
    REV-2.5: Identify conditions where theory stops working.
    Most papers overgeneralize. Need failure boundaries.
    """
    claim_text = claim.get("claim", "")
    domain = paper_object.get("domain", "general")
    limitations = paper_object.get("limitations", [])
    
    boundaries = []
    
    # Domain-specific boundaries
    domain_boundaries = {
        "finance": [
            "Theory may fail during market crises or liquidity freezes",
            "Theory assumes functioning markets — may not apply in emerging markets",
            "Theory may not hold during periods of extreme volatility",
        ],
        "economics": [
            "Theory assumes rational actors — may fail under behavioral biases",
            "Theory may not apply during economic crises or structural breaks",
            "Theory assumes stable institutional environment",
        ],
        "political science": [
            "Theory may fail in authoritarian or hybrid regimes",
            "Theory assumes stable political institutions",
            "Theory may not apply during periods of rapid political change",
        ],
    }
    
    if domain in domain_boundaries:
        boundaries.extend(domain_boundaries[domain])
    
    # Limitation-based boundaries
    for lim in limitations:
        lim_text = lim.get("limitation", "").lower()
        if "sample" in lim_text:
            boundaries.append(f"Theory may fail outside the studied sample: {lim.get('limitation', '')}")
        if "country" in lim_text or "region" in lim_text:
            boundaries.append(f"Theory may not generalize to other geographic contexts")
        if "time" in lim_text or "period" in lim_text:
            boundaries.append(f"Theory may not hold in different time periods")
        if "sector" in lim_text or "industry" in lim_text:
            boundaries.append(f"Theory may not apply to other sectors")
    
    # Generic boundaries
    boundaries.extend([
        "Theory may fail when key moderating variables are absent",
        "Theory may not hold at extreme values of key variables",
        "Theory assumes stable relationships — may fail during structural breaks",
    ])
    
    return boundaries[:8]


# ─── REV-2.6 Conflict Memory Layer ───

class ConflictMemory:
    """
    REV-2.6: Store historical contradictions permanently.
    Machine learns recurring scientific conflicts.
    """
    
    def __init__(self):
        self.conflicts: List[Dict[str, Any]] = []
        self.explanations: Dict[str, List[str]] = {}
        self.boundaries: Dict[str, List[str]] = {}
    
    def record_contradiction(self, contradiction: Dict, explanations: List[str]):
        self.conflicts.append(contradiction)
        key = f"{contradiction.get('paper_a', '')} vs {contradiction.get('paper_b', '')}"
        self.explanations[key] = explanations
    
    def record_boundary(self, claim_id: str, boundaries: List[str]):
        self.boundaries[claim_id] = boundaries
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_conflicts": len(self.conflicts),
            "high_severity": sum(1 for c in self.conflicts if c.get("severity", 0) > 0.7),
            "assumption_conflicts": sum(1 for c in self.conflicts if c.get("type") == "assumption_conflict"),
            "claim_conflicts": sum(1 for c in self.conflicts if c.get("type") == "claim_contradiction"),
        }


# ─── REV-2 Master: Full Adversarial Pipeline ───

def run_adversarial_reasoning(objects: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    REV-2 Master: Run full adversarial reasoning pipeline.
    
    Pipeline: detect contradictions → pressure test → generate alternatives →
              scientific attack → boundary detection → conflict memory
    """
    memory = ConflictMemory()
    
    # Step 1: Detect contradictions
    contradictions = detect_contradictions(objects)
    
    # Step 2: Pressure test each contradiction
    pressured = []
    for c in contradictions:
        explanations = pressure_test_contradiction(c)
        memory.record_contradiction(c, explanations)
        pressured.append({**c, "possible_explanations": explanations})
    
    # Step 3-4: For each paper, generate alternatives and attack
    paper_analyses = {}
    for obj in objects:
        paper_id = obj.get("paper_id", "")
        claims = obj.get("claims", [])
        
        claim_analyses = []
        for claim in claims:
            alternatives = generate_alternative_explanations(claim)
            attacks = scientific_attack(claim, obj)
            boundaries = detect_boundary_conditions(claim, obj)
            
            claim_analyses.append({
                "claim_id": claim.get("claim_id", ""),
                "claim": claim.get("claim", ""),
                "alternatives": alternatives,
                "attacks": attacks,
                "boundaries": boundaries,
            })
            
            memory.record_boundary(claim.get("claim_id", ""), boundaries)
        
        paper_analyses[paper_id] = {
            "paper_title": obj.get("paper_title", ""),
            "claim_analyses": claim_analyses,
        }
    
    return {
        "contradictions": pressured,
        "paper_analyses": paper_analyses,
        "conflict_memory": memory.get_stats(),
        "summary": {
            "num_contradictions": len(contradictions),
            "num_papers_analyzed": len(objects),
            "total_claims_analyzed": sum(len(obj.get("claims", [])) for obj in objects),
            "total_attacks_generated": sum(
                len(ca.get("attacks", []))
                for pa in paper_analyses.values()
                for ca in pa.get("claim_analyses", [])
            ),
        },
    }
