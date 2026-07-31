"""
REV-3: Theory Competition + Scientific Judgment Engine

Teaches machine scientific judgment. Ranks competing theories.
Theory synthesis only AFTER ranking complete.

7 engines:
- REV-3.1: Theory Extraction Engine
- REV-3.2: Explanatory Competition Engine
- REV-3.3: Assumption Cost Scoring
- REV-3.4: Generalization Analysis Engine
- REV-3.5: Scientific Ranking Engine
- REV-3.6: Theory Synthesis Engine
- REV-3.7: Judgment Memory Layer

Anchor principle: No synthesis before ranking. Choose winner.
"""

from __future__ import annotations
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.rce.rev3")


# ─── REV-3.1 Theory Extraction Engine ───

def extract_theories(objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    REV-3.1: Extract full theories from papers.
    Not claims — entire explanatory framework.
    """
    theories = []
    
    for obj in objects:
        claims = obj.get("claims", [])
        mechanisms = obj.get("mechanisms", [])
        assumptions = obj.get("explicit_assumptions", []) + obj.get("implicit_assumptions", [])
        
        # Build theory from causal claims + mechanisms
        causal_claims = [c for c in claims if c.get("claim_type") == "causal"]
        
        if causal_claims or mechanisms:
            # Extract core variables from claims
            variables = set()
            for claim in causal_claims:
                text = claim.get("claim", "")
                # Simple variable extraction (nouns/phrases)
                words = text.split()
                for w in words:
                    w_clean = w.lower().strip(".,;:()[]")
                    if len(w_clean) > 3 and w_clean not in {
                        "that", "this", "with", "from", "have", "been", "were", "will",
                        "would", "could", "should", "their", "these", "those", "which",
                        "what", "when", "where", "while", "about", "into", "through",
                    }:
                        variables.add(w_clean)
            
            # Build causal chain from mechanisms
            causal_chains = []
            for mech in mechanisms:
                chain = mech.get("mechanism", "")
                if "→" in chain or "causes" in chain.lower() or "leads" in chain.lower():
                    causal_chains.append(chain)
            
            theory = {
                "theory_id": f"theory_{obj.get('paper_id', '')}",
                "theory_name": f"Theory from {obj.get('paper_title', 'Unknown')[:50]}",
                "source_paper": obj.get("paper_title", ""),
                "domain": obj.get("domain", "general"),
                "core_variables": list(variables)[:10],
                "causal_chains": causal_chains,
                "key_claims": [c.get("claim", "")[:150] for c in causal_claims[:3]],
                "mechanisms": [m.get("mechanism", "")[:150] for m in mechanisms[:3]],
                "assumptions": [a.get("assumption", "")[:100] for a in assumptions[:5]],
                "confidence": obj.get("confidence_score", 0.5),
            }
            theories.append(theory)
    
    return theories


# ─── REV-3.2 Explanatory Competition Engine ───

def compete_theories(theories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    REV-3.2: Determine which theory explains more variance.
    Compare explanatory power across theories.
    """
    if len(theories) < 2:
        return theories
    
    scored = []
    for theory in theories:
        score = 0.0
        
        # More causal chains = higher explanatory power
        score += min(len(theory.get("causal_chains", [])) * 0.15, 0.4)
        
        # More mechanisms = more detailed explanation
        score += min(len(theory.get("mechanisms", [])) * 0.1, 0.3)
        
        # More variables covered = broader explanation
        score += min(len(theory.get("core_variables", [])) * 0.02, 0.2)
        
        # Confidence boost
        score += theory.get("confidence", 0.5) * 0.1
        
        scored.append({**theory, "explanatory_score": round(min(score, 1.0), 3)})
    
    # Sort by score
    scored.sort(key=lambda x: x["explanatory_score"], reverse=True)
    return scored


# ─── REV-3.3 Assumption Cost Scoring ───

def score_assumption_cost(theory: Dict[str, Any]) -> Dict[str, Any]:
    """
    REV-3.3: Theories requiring fewer assumptions are stronger.
    Scientific efficiency principle (Occam's razor).
    """
    assumptions = theory.get("assumptions", [])
    num_assumptions = len(assumptions)
    
    # Fewer assumptions = higher score
    if num_assumptions == 0:
        cost_score = 0.5  # No assumptions stated is suspicious
    elif num_assumptions <= 2:
        cost_score = 0.95
    elif num_assumptions <= 4:
        cost_score = 0.8
    elif num_assumptions <= 6:
        cost_score = 0.6
    else:
        cost_score = 0.4
    
    # Check for high-risk assumptions
    high_risk_keywords = ["assume", "perfect", "rational", "efficient", "complete information", "no friction"]
    high_risk_count = sum(1 for a in assumptions if any(kw in a.lower() for kw in high_risk_keywords))
    
    cost_score -= high_risk_count * 0.05
    
    return {
        **theory,
        "assumption_cost_score": round(max(cost_score, 0.1), 3),
        "num_assumptions": num_assumptions,
        "high_risk_assumptions": high_risk_count,
    }


# ─── REV-3.4 Generalization Analysis Engine ───

def analyze_generalization(theory: Dict[str, Any]) -> Dict[str, Any]:
    """
    REV-3.4: Determine whether theory applies broadly.
    Local theories are weaker.
    """
    source = theory.get("source_paper", "").lower()
    domain = theory.get("domain", "general")
    
    # Geographic scope
    geo_score = 0.5  # Default: moderate
    if any(w in source for w in ["global", "international", "cross-country", "worldwide"]):
        geo_score = 0.9
    elif any(w in source for w in ["multi-country", "comparative"]):
        geo_score = 0.7
    elif any(w in source for w in ["us ", "usa", "united states", "uk ", "china", "india", "germany"]):
        geo_score = 0.3
    
    # Sector scope
    sector_score = 0.5
    if any(w in source for w in ["all sectors", "cross-sector", "economy-wide"]):
        sector_score = 0.9
    elif any(w in source for w in ["multiple sectors", "several industries"]):
        sector_score = 0.7
    elif any(w in source for w in ["banking", "financial sector", "technology sector", "manufacturing"]):
        sector_score = 0.3
    
    # Time scope
    time_score = 0.5
    if any(w in source for w in ["longitudinal", "panel", "time series", "decade"]):
        time_score = 0.8
    elif any(w in source for w in ["cross-sectional", "snapshot"]):
        time_score = 0.3
    
    generalization_score = (geo_score + sector_score + time_score) / 3
    
    return {
        **theory,
        "generalization_score": round(generalization_score, 3),
        "geo_score": round(geo_score, 2),
        "sector_score": round(sector_score, 2),
        "time_score": round(time_score, 2),
    }


# ─── REV-3.5 Scientific Ranking Engine ───

def rank_theories(theories: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    REV-3.5: Rank competing theories objectively.
    Criteria: explanatory power, assumption cost, generalization, falsifiability.
    """
    if len(theories) < 2:
        return {"ranked_theories": theories, "winner": theories[0] if theories else None}
    
    # Score each theory on all dimensions
    scored = []
    for theory in theories:
        # Get assumption cost
        theory = score_assumption_cost(theory)
        # Get generalization
        theory = analyze_generalization(theory)
        
        # Calculate composite score
        explanatory = theory.get("explanatory_score", 0.5)
        assumption_cost = theory.get("assumption_cost_score", 0.5)
        generalization = theory.get("generalization_score", 0.5)
        
        # Falsifiability (based on specificity of claims)
        claims = theory.get("key_claims", [])
        falsifiability = min(len(claims) * 0.2, 1.0)  # More specific claims = more falsifiable
        
        # Robustness (based on number of mechanisms)
        mechanisms = theory.get("mechanisms", [])
        robustness = min(len(mechanisms) * 0.15, 1.0)
        
        composite = (
            explanatory * 0.30 +
            assumption_cost * 0.25 +
            generalization * 0.20 +
            falsifiability * 0.15 +
            robustness * 0.10
        )
        
        scored.append({
            **theory,
            "composite_score": round(composite, 3),
            "falsifiability_score": round(falsifiability, 3),
            "robustness_score": round(robustness, 3),
        })
    
    # Sort by composite score
    scored.sort(key=lambda x: x["composite_score"], reverse=True)
    
    return {
        "ranked_theories": scored,
        "winner": scored[0] if scored else None,
        "ranking_criteria": {
            "explanatory_power": 0.30,
            "assumption_cost": 0.25,
            "generalization": 0.20,
            "falsifiability": 0.15,
            "robustness": 0.10,
        },
    }


# ─── REV-3.6 Theory Synthesis Engine ───

def synthesize_theory(ranking_result: Dict[str, Any], 
                      adversarial_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    REV-3.6: Only AFTER ranking complete, generate superior theory.
    Never before. Extract strongest components from ranked theories.
    """
    ranked = ranking_result.get("ranked_theories", [])
    winner = ranking_result.get("winner")
    
    if not winner:
        return {"error": "No theories to synthesize", "synthesis": None}
    
    # Extract strongest components from top theories
    top_theories = ranked[:3]
    
    all_variables = set()
    all_mechanisms = []
    all_claims = []
    
    for t in top_theories:
        all_variables.update(t.get("core_variables", []))
        all_mechanisms.extend(t.get("mechanisms", []))
        all_claims.extend(t.get("key_claims", []))
    
    # Build unified theory
    unified_theory = {
        "statement": f"Synthesized theory integrating findings from {len(top_theories)} papers. "
                     f"Primary contribution: {winner.get('theory_name', '')}. "
                     f"Key insight: {'; '.join(all_claims[:3])}",
        "components": [
            f"Core variables: {', '.join(list(all_variables)[:8])}",
            f"Primary mechanism: {all_mechanisms[0] if all_mechanisms else 'Not identified'}",
            f"Key claims: {'; '.join(all_claims[:3])}",
        ],
        "winner_theory": winner.get("theory_name", ""),
        "winner_score": winner.get("composite_score", 0),
        "synthesis_method": "Ranked theory competition with assumption cost scoring",
        "num_theories_evaluated": len(ranked),
        "structural_themes": _extract_structural_themes(top_theories),
        "interdisciplinary_connections": _extract_interdisciplinary(top_theories),
    }
    
    return unified_theory


def _extract_structural_themes(theories: List[Dict]) -> List[str]:
    """Extract recurring structural patterns across theories."""
    themes = []
    
    all_text = " ".join(
        " ".join(t.get("key_claims", [])) + " " + " ".join(t.get("mechanisms", []))
        for t in theories
    ).lower()
    
    theme_patterns = {
        "feedback_loops": ["feedback", "loop", "circular", "self-reinforcing", "amplif"],
        "regime_shifts": ["regime", "shift", "transition", "break", "threshold", "tipping"],
        "information_asymmetry": ["information", "asymmetry", "signal", "uncertainty", "belief"],
        "network_effects": ["network", "spillover", "contagion", "interconnected", "cascade"],
        "adaptation": ["adapt", "adjust", "respond", "learn", "evolve", "transform"],
        "institutional_mediation": ["institution", "governance", "regulation", "policy", "framework"],
    }
    
    for theme, keywords in theme_patterns.items():
        if any(kw in all_text for kw in keywords):
            themes.append(theme)
    
    return themes[:5]


def _extract_interdisciplinary(theories: List[Dict]) -> List[str]:
    """Extract interdisciplinary connections across theories."""
    connections = []
    domains = set(t.get("domain", "general") for t in theories)
    
    if len(domains) > 1:
        connections.append(f"Bridges {', '.join(domains)} perspectives")
    
    domain_pairs = {
        ("finance", "economics"): "Connects financial market behavior with macroeconomic dynamics",
        ("finance", "political science"): "Links financial outcomes with political/institutional factors",
        ("economics", "political science"): "Integrates economic and political analysis",
        ("finance", "computer science"): "Applies computational methods to financial analysis",
        ("economics", "psychology"): "Incorporates behavioral insights into economic modeling",
    }
    
    for (d1, d2), description in domain_pairs.items():
        if d1 in domains and d2 in domains:
            connections.append(description)
    
    return connections[:4]


# ─── REV-3.7 Judgment Memory Layer ───

class JudgmentMemory:
    """REV-3.7: Store theory rankings permanently."""
    
    def __init__(self):
        self.rankings: List[Dict[str, Any]] = []
        self.winners: List[Dict[str, Any]] = []
        self.rejected: List[Dict[str, Any]] = []
    
    def record_ranking(self, ranking: Dict[str, Any]):
        self.rankings.append(ranking)
        if ranking.get("winner"):
            self.winners.append(ranking["winner"])
        ranked = ranking.get("ranked_theories", [])
        if len(ranked) > 1:
            self.rejected.extend(ranked[1:])
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_rankings": len(self.rankings),
            "unique_winners": len(set(w.get("theory_id", "") for w in self.winners)),
            "rejected_theories": len(self.rejected),
        }


# ─── REV-3 Master: Full Theory Competition Pipeline ───

def run_theory_competition(objects: List[Dict[str, Any]],
                           adversarial_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    REV-3 Master: Run full theory competition pipeline.
    
    Pipeline: extract theories → compete → score assumptions →
              analyze generalization → rank → synthesize
    """
    memory = JudgmentMemory()
    
    # Step 1: Extract theories
    theories = extract_theories(objects)
    
    # Step 2: Compete on explanatory power
    competed = compete_theories(theories)
    
    # Step 3-5: Score assumptions, analyze generalization, rank
    ranking = rank_theories(competed)
    
    # Step 6: Synthesize (only after ranking)
    synthesis = synthesize_theory(ranking, adversarial_result)
    
    # Record in memory
    memory.record_ranking(ranking)
    
    return {
        "theories_extracted": len(theories),
        "ranking": ranking,
        "synthesis": synthesis,
        "judgment_memory": memory.get_stats(),
        "adversarial_input": {
            "contradictions_found": adversarial_result.get("summary", {}).get("num_contradictions", 0),
            "attacks_generated": adversarial_result.get("summary", {}).get("total_attacks_generated", 0),
        },
    }
