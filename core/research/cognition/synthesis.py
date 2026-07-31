"""
R4 — Theory Synthesis Engine

The most important layer — generates higher-order understanding.
Input: decomposed knowledge objects + relationship graph + reasoning results
Output: unified theories + research reports

This is where machine cognition actually begins.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional

from .schema import KnowledgeObject

logger = logging.getLogger("oce.rce.synthesis")


class TheorySynthesizer:
    """
    R4 — Theory Synthesis Engine.
    
    Constructs unified theories from decomposed knowledge.
    
    Pipeline:
    1. Aggregate claims across papers
    2. Identify dominant mechanisms
    3. Resolve contradictions (where possible)
    4. Build unified theoretical framework
    5. Generate research report
    
    Usage:
        synthesizer = TheorySynthesizer()
        theory = synthesizer.synthesize(knowledge_objects, reasoning_results)
    """
    
    def __init__(self, min_consensus: float = 0.3):
        self.min_consensus = min_consensus
    
    def synthesize(
        self,
        knowledge_objects: List[KnowledgeObject],
        reasoning_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Synthesize a unified theory from all available knowledge.
        
        Returns:
            Dict with: unified_theory, theory_components, research_report, confidence
        """
        if not knowledge_objects:
            return self._empty_synthesis()
        
        # 1. Aggregate all claims
        claim_clusters = self._aggregate_claims(knowledge_objects)
        
        # 2. Identify dominant mechanisms
        dominant_mechanisms = self._identify_dominant_mechanisms(knowledge_objects)
        
        # 3. Build unified theory
        unified_theory = self._build_unified_theory(
            claim_clusters, dominant_mechanisms, reasoning_results
        )
        
        # 4. Generate research report
        report = self._generate_research_report(
            unified_theory, knowledge_objects, reasoning_results
        )
        
        # 5. Calculate overall confidence
        confidence = self._calculate_synthesis_confidence(
            unified_theory, knowledge_objects, reasoning_results
        )
        
        return {
            "unified_theory": unified_theory,
            "theory_components": {
                "claim_clusters": claim_clusters,
                "dominant_mechanisms": dominant_mechanisms,
            },
            "research_report": report,
            "confidence": confidence,
            "num_papers_synthesized": len(knowledge_objects),
            "domains_covered": list(set(obj.domain for obj in knowledge_objects if obj.domain)),
        }
    
    def _aggregate_claims(
        self, knowledge_objects: List[KnowledgeObject]
    ) -> List[Dict[str, Any]]:
        """Aggregate claims across papers into clusters."""
        all_claims: List[Dict[str, Any]] = []
        
        for obj in knowledge_objects:
            for claim in obj.main_claims:
                all_claims.append({
                    "claim": claim.claim,
                    "confidence": claim.confidence,
                    "paper": obj.paper_title or obj.paper_id,
                    "domain": obj.domain,
                })
        
        # Simple clustering by domain
        domain_claims: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for claim in all_claims:
            domain_claims[claim.get("domain", "general")].append(claim)
        
        clusters = []
        for domain, claims in domain_claims.items():
            if claims:
                avg_confidence = sum(c["confidence"] for c in claims) / len(claims)
                clusters.append({
                    "domain": domain,
                    "claims": claims,
                    "num_claims": len(claims),
                    "avg_confidence": avg_confidence,
                    "representative_claim": claims[0]["claim"] if claims else "",
                })
        
        return clusters
    
    def _identify_dominant_mechanisms(
        self, knowledge_objects: List[KnowledgeObject]
    ) -> List[Dict[str, Any]]:
        """Identify the most common mechanisms across papers."""
        mechanism_counts: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"count": 0, "papers": [], "avg_confidence": 0.0}
        )
        
        for obj in knowledge_objects:
            for mech in obj.mechanisms:
                key = mech.mechanism.lower().strip()[:60]
                mechanism_counts[key]["count"] += 1
                mechanism_counts[key]["papers"].append(obj.paper_title or obj.paper_id)
                mechanism_counts[key]["avg_confidence"] += mech.confidence
        
        # Calculate averages and sort
        dominant = []
        for mechanism, data in mechanism_counts.items():
            if data["count"] >= 1:
                data["avg_confidence"] /= data["count"]
                dominant.append({
                    "mechanism": mechanism,
                    "frequency": data["count"],
                    "papers": list(set(data["papers"])),
                    "avg_confidence": data["avg_confidence"],
                })
        
        dominant.sort(key=lambda x: x["frequency"] * x["avg_confidence"], reverse=True)
        return dominant[:10]
    
    def _build_unified_theory(
        self,
        claim_clusters: List[Dict[str, Any]],
        dominant_mechanisms: List[Dict[str, Any]],
        reasoning_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build the unified theoretical framework."""
        # Extract consensus areas
        consensus_areas = reasoning_results.get("consensus", [])
        
        # Extract contradictions
        contradictions = reasoning_results.get("contradictions", [])
        
        # Build theory statement
        theory_parts = []
        
        # From dominant mechanisms
        if dominant_mechanisms:
            top_mech = dominant_mechanisms[0]
            theory_parts.append(
                f"Primary mechanism: {top_mech['mechanism']} "
                f"(observed in {top_mech['frequency']} papers)"
            )
        
        # From consensus
        if consensus_areas:
            top_consensus = consensus_areas[0]
            theory_parts.append(
                f"Established consensus: {top_consensus.get('claim', '')}"
            )
        
        # From claim clusters
        for cluster in claim_clusters[:3]:
            if cluster["num_claims"] >= 2:
                theory_parts.append(
                    f"In {cluster['domain']}: {cluster['representative_claim']} "
                    f"(supported by {cluster['num_claims']} claims)"
                )
        
        # Identify open questions
        open_questions = []
        for contradiction in contradictions[:3]:
            open_questions.append(
                f"Conflict between '{contradiction.get('paper_a', '?')}' and "
                f"'{contradiction.get('paper_b', '?')}': {contradiction.get('explanation', '')}"
            )
        
        return {
            "statement": "\n".join(theory_parts) if theory_parts else "Insufficient data for theory construction.",
            "components": theory_parts,
            "consensus_basis": [c.get("claim", "") for c in consensus_areas[:5]],
            "mechanism_basis": [m["mechanism"] for m in dominant_mechanisms[:5]],
            "open_questions": open_questions,
            "contradictions_remaining": len(contradictions),
            "consensus_areas": len(consensus_areas),
        }
    
    def _generate_research_report(
        self,
        unified_theory: Dict[str, Any],
        knowledge_objects: List[KnowledgeObject],
        reasoning_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate a structured research report."""
        # Title
        domains = list(set(obj.domain for obj in knowledge_objects if obj.domain))
        title = f"Synthesis Report: {' × '.join(domains[:3])}" if domains else "Research Synthesis Report"
        
        # Executive summary
        summary_parts = [
            f"Analysis of {len(knowledge_objects)} papers across {len(domains)} domains.",
        ]
        if unified_theory["statement"] != "Insufficient data for theory construction.":
            summary_parts.append(f"Key finding: {unified_theory['components'][0] if unified_theory['components'] else 'N/A'}")
        
        # Sections
        sections = {
            "executive_summary": "\n".join(summary_parts),
            "introduction": self._generate_introduction(knowledge_objects, domains),
            "literature_review": self._generate_literature_review(knowledge_objects),
            "theoretical_framework": unified_theory["statement"],
            "key_mechanisms": self._format_mechanisms(unified_theory.get("mechanism_basis", [])),
            "consensus_and_conflict": self._format_consensus_conflicts(
                reasoning_results.get("consensus", []),
                reasoning_results.get("contradictions", []),
            ),
            "open_questions": "\n".join(
                f"- {q}" for q in unified_theory.get("open_questions", [])
            ) or "No major open questions identified.",
            "limitations": self._generate_limitations(knowledge_objects),
            "conclusion": self._generate_conclusion(unified_theory, reasoning_results),
        }
        
        # Full report text
        full_report = "\n\n".join(
            f"## {section_name.replace('_', ' ').title()}\n{content}"
            for section_name, content in sections.items()
        )
        
        return {
            "title": title,
            "sections": sections,
            "full_report": full_report,
            "word_count": len(full_report.split()),
            "num_references": len(knowledge_objects),
        }
    
    def _generate_introduction(
        self, knowledge_objects: List[KnowledgeObject], domains: List[str]
    ) -> str:
        """Generate introduction section."""
        return (
            f"This report synthesizes findings from {len(knowledge_objects)} research papers "
            f"spanning the domain(s) of {', '.join(domains)}. "
            f"The analysis employs structured knowledge decomposition, cross-document reasoning, "
            f"and theory synthesis to identify dominant mechanisms, consensus areas, and open questions. "
            f"Unlike simple summarization, this approach extracts atomic knowledge structures "
            f"(claims, mechanisms, assumptions, equations, limitations) and reasons across them "
            f"to construct a unified theoretical framework."
        )
    
    def _generate_literature_review(
        self, knowledge_objects: List[KnowledgeObject]
    ) -> str:
        """Generate literature review section."""
        lines = []
        for i, obj in enumerate(knowledge_objects, 1):
            title = obj.paper_title or f"Paper {i}"
            claims_summary = "; ".join(c.claim[:80] for c in obj.main_claims[:2])
            lines.append(f"{i}. **{title}** — {claims_summary}")
        return "\n".join(lines) if lines else "No papers analyzed."
    
    def _format_mechanisms(self, mechanisms: List[str]) -> str:
        """Format mechanisms for report."""
        if not mechanisms:
            return "No dominant mechanisms identified."
        return "\n".join(f"- {m}" for m in mechanisms)
    
    def _format_consensus_conflicts(
        self, consensus: List[Dict], contradictions: List[Dict]
    ) -> str:
        """Format consensus and conflict section."""
        lines = []
        if consensus:
            lines.append("### Areas of Consensus")
            for c in consensus[:3]:
                lines.append(f"- {c.get('claim', '')} (supported by {c.get('num_supporting', 0)} papers)")
        if contradictions:
            lines.append("\n### Areas of Conflict")
            for c in contradictions[:3]:
                lines.append(f"- {c.get('explanation', '')}")
        return "\n".join(lines) if lines else "No consensus or conflict detected."
    
    def _generate_limitations(
        self, knowledge_objects: List[KnowledgeObject]
    ) -> str:
        """Generate limitations section."""
        all_limitations = []
        for obj in knowledge_objects:
            for lim in obj.limitations:
                all_limitations.append(lim.limitation)
        
        if all_limitations:
            return "\n".join(f"- {l}" for l in all_limitations[:5])
        return "No limitations identified from analyzed papers."
    
    def _generate_conclusion(
        self, unified_theory: Dict[str, Any], reasoning_results: Dict[str, Any]
    ) -> str:
        """Generate conclusion section."""
        parts = []
        
        landscape = reasoning_results.get("unified_reasoning", {}).get("landscape", "unknown")
        parts.append(f"The research landscape is assessed as **{landscape}**.")
        
        if unified_theory.get("consensus_areas", 0) > 0:
            parts.append(
                f"{unified_theory['consensus_areas']} areas of consensus were identified, "
                f"with {unified_theory['contradictions_remaining']} unresolved contradictions."
            )
        
        if unified_theory.get("open_questions"):
            parts.append(f"{len(unified_theory['open_questions'])} open questions remain for future research.")
        
        return " ".join(parts)
    
    def _calculate_synthesis_confidence(
        self,
        unified_theory: Dict[str, Any],
        knowledge_objects: List[KnowledgeObject],
        reasoning_results: Dict[str, Any],
    ) -> float:
        """Calculate overall confidence in the synthesis."""
        # Base confidence from extraction completeness
        avg_completeness = sum(obj.extraction_completeness for obj in knowledge_objects) / max(len(knowledge_objects), 1)
        
        # Boost from consensus
        consensus_count = len(reasoning_results.get("consensus", []))
        consensus_boost = min(consensus_count * 0.05, 0.2)
        
        # Penalty from contradictions
        contradiction_count = len(reasoning_results.get("contradictions", []))
        contradiction_penalty = min(contradiction_count * 0.03, 0.15)
        
        return min(max(avg_completeness + consensus_boost - contradiction_penalty, 0.0), 1.0)
    
    def _empty_synthesis(self) -> Dict[str, Any]:
        """Return empty synthesis result."""
        return {
            "unified_theory": {"statement": "No data available."},
            "theory_components": {"claim_clusters": [], "dominant_mechanisms": []},
            "research_report": {"title": "Empty Report", "full_report": "No data."},
            "confidence": 0.0,
            "num_papers_synthesized": 0,
            "domains_covered": [],
        }
