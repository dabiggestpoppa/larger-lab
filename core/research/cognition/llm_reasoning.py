"""
LLM Reasoning Gateway for the Research Cognition Engine.

Provides structured LLM calls for each RCE phase:
- R1: Extract claims, mechanisms, assumptions from papers
- R2: Build semantic relationships between concepts
- R3: Cross-document reasoning (contradictions, consensus)
- R4: Theory synthesis and report generation
- R5: Validation and quality judgment

Uses OpenRouterGateway with owl-alpha primary, auto-failover.
All prompts are designed for structured JSON output.

Usage:
    from core.research.cognition.llm_reasoning import LLMReasoning
    
    llm = LLMReasoning()
    result = await llm.extract_claims(paper_text, paper_title)
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.rce.llm")


# ─── Prompt Templates ───

R1_CLAIM_EXTRACTION_PROMPT = """You are a research scientist analyzing an academic paper. Extract the structural cognitive components.

Paper: {title}
Abstract/Text:
{text}

Extract the following as JSON:
{{
  "main_claims": [
    {{"claim": "...", "confidence": 0.0-1.0, "claim_type": "primary|secondary|implicit"}}
  ],
  "mechanisms": [
    {{"cause": "...", "mechanism": "...", "effect": "...", "confidence": 0.0-1.0}}
  ],
  "assumptions": [
    {{"assumption": "...", "explicit": true/false, "confidence": 0.0-1.0}}
  ],
  "equations": [
    {{"equation_type": "...", "variables": [...], "mathematical_framework": "...", "raw_text": "..."}}
  ],
  "limitations": [
    {{"limitation": "...", "severity": "low|medium|high", "is_stated": true/false}}
  ],
  "novel_contribution": {{"contribution": "...", "novelty_score": 0.0-1.0, "prior_literature_gap": "..."}},
  "causal_relationships": [
    {{"cause": "...", "relationship": "...", "effect": "..."}}
  ],
  "implicit_theory": "...",
  "methodology": "...",
  "domain": "..."
}}

Rules:
- Be precise. Extract actual claims, not summaries.
- confidence should reflect how certain the extraction is.
- mechanisms must have clear cause → mechanism → effect.
- assumptions: explicit=true if stated by authors, false if you inferred.
- domain: one of: finance, physics, biology, computer science, economics, medicine, mathematics, general.

Return ONLY valid JSON, no markdown fences.
"""

R2_RELATIONSHIP_PROMPT = """You are a research scientist building a knowledge graph from extracted paper components.

Topic: {topic}

Paper components:
{paper_json}

Build semantic relationships as JSON:
{{
  "concepts": [
    {{"name": "...", "domain": "...", "frequency": 1, "source_papers": ["..."]}}
  ],
  "relationships": [
    {{"source": "...", "target": "...", "type": "causes|influences|depends_on|amplifies|reduces|predicts|correlates_with", "confidence": 0.0-1.0, "source_paper": "..."}}
  ],
  "causal_chains": [
    {{"chain": ["A", "B", "C"], "length": 3, "confidence": 0.0-1.0, "type": "causal_chain"}}
  ],
  "clusters": [
    {{"domain": "...", "concepts": ["..."], "size": 2, "representative": "..."}}
  ],
  "dependencies": [
    {{"dependent": "...", "depends_on": "...", "type": "...", "strength": 0.0-1.0, "source_paper": "..."}}
  ]
}}

Rules:
- concepts should be specific scientific terms, not generic words.
- relationships must be typed (causes, influences, etc.).
- causal_chains should have at least 3 nodes.
- Only include relationships that are actually supported by the papers.

Return ONLY valid JSON, no markdown fences.
"""

R3_REASONING_PROMPT = """You are a research scientist performing adversarial cross-document reasoning.

Topic: {topic}

Papers analyzed:
{papers_json}

Perform cross-document reasoning as JSON:
{{
  "comparisons": [
    {{"paper_a": "...", "paper_b": "...", "claim_similarity": 0.0-1.0, "mechanism_similarity": 0.0-1.0, "domain_match": 0.0|1.0, "similarity": 0.0-1.0}}
  ],
  "contradictions": [
    {{"type": "claim_contradiction|mechanism_contradiction", "paper_a": "...", "paper_b": "...", "claim_a": "...", "claim_b": "...", "severity": 0.0-1.0, "explanation": "..."}}
  ],
  "consensus": [
    {{"type": "claim_consensus", "domain": "...", "claim": "...", "supporting_papers": ["..."], "consensus_strength": 0.0-1.0, "num_supporting": 1}}
  ],
  "assumption_conflicts": [
    {{"type": "assumption_conflict", "paper_a": "...", "paper_b": "...", "assumption_a": "...", "assumption_b": "...", "conflict_type": "...", "severity": 0.0-1.0}}
  ],
  "explanatory_ranking": [
    {{"paper": "...", "domain": "...", "explanatory_score": 0.0-1.0, "factors": {{}}}}
  ],
  "reasoning_chains": [
    {{"chain": ["A", "B", "C"], "length": 3, "confidence": 0.0-1.0, "papers_involved": ["..."], "type": "cross_paper_reasoning"}}
  ],
  "unified_reasoning": {{
    "landscape": "mature|contested|developing|insufficient_data",
    "maturity_note": "...",
    "key_tensions": [{{"between": ["...", "..."], "issue": "...", "severity": 0.0-1.0}}],
    "strongest_theories": [{{"paper": "...", "score": 0.0-1.0, "domain": "..."}}],
    "overall_confidence": 0.0-1.0
  }}
}}

Rules:
- contradictions: only flag genuine conflicts, not different perspectives on the same topic.
- consensus: only flag when 2+ papers independently support the same claim.
- explanatory_ranking: rank papers by how well they explain the topic domain.
- unified_reasoning.landscape: mature if consensus > contradictions, contested if contradictions > consensus*2, developing otherwise.

Return ONLY valid JSON, no markdown fences.
"""

R4_SYNTHESIS_PROMPT = """You are a senior research scientist synthesizing a unified theory from multiple papers.

Topic: {topic}

Cross-document reasoning results:
{reasoning_json}

Generate a unified theory and research report as JSON:
{{
  "unified_theory": {{
    "statement": "...",
    "components": ["..."],
    "consensus_basis": ["..."],
    "mechanism_basis": ["..."],
    "open_questions": ["..."],
    "contradictions_remaining": 0,
    "consensus_areas": 0
  }},
  "research_report": {{
    "title": "...",
    "sections": {{
      "executive_summary": "...",
      "introduction": "...",
      "literature_review": "...",
      "theoretical_framework": "...",
      "key_mechanisms": "...",
      "consensus_and_conflict": "...",
      "open_questions": "...",
      "limitations": "...",
      "conclusion": "..."
    }},
    "full_report": "...",
    "word_count": 0,
    "num_references": 0
  }},
  "confidence": 0.0-1.0,
  "num_papers_synthesized": 0,
  "domains_covered": ["..."]
}}

Rules:
- unified_theory.statement should be a novel synthesis, NOT a summary of individual papers.
- The theory should connect findings across papers into a coherent framework.
- research_report.full_report should be a complete academic-style report (500+ words).
- Use proper section headers in the report.
- confidence should reflect the quality and coherence of the evidence.

Return ONLY valid JSON, no markdown fences.
"""

R5_VALIDATION_PROMPT = """You are a senior research scientist validating the quality of a research synthesis.

Topic: {topic}

Research report:
{report_text}

Validation criteria:
1. Hallucination Rate < 3% (are claims supported by the source papers?)
2. Citation Accuracy > 95% (are references correctly attributed?)
3. Cross-Paper Relation Detection > 90% (are connections between papers valid?)
4. Contradiction Detection > 90% (are conflicts properly identified?)
5. Theory Novelty Score (is the synthesis novel, not just summary?)
6. Reasoning Depth (does it demonstrate PhD-level analysis?)

Score each criterion 0-1 and provide an overall pass/fail.

Return as JSON:
{{
  "passed": true/false,
  "metrics": {{
    "hallucination_rate": 0.0-1.0,
    "citation_accuracy": 0.0-1.0,
    "cross_paper_relation_detection": 0.0-1.0,
    "contradiction_detection": 0.0-1.0,
    "theory_novelty": 0.0-1.0,
    "reasoning_depth": 0.0-1.0,
    "overall_quality": 0.0-1.0
  }},
  "benchmarks": [
    {{"name": "...", "passed": true/false, "description": "...", "details": "..."}}
  ],
  "recommendations": ["..."]
}}

Return ONLY valid JSON, no markdown fences.
"""


class LLMReasoning:
    """
    LLM-powered reasoning for all RCE phases.
    
    Wraps OpenRouterGateway with structured prompts and JSON parsing.
    Each method corresponds to one RCE phase.
    """
    
    def __init__(self, gateway: Optional[Any] = None):
        """
        Initialize with an OpenRouterGateway instance.
        
        If no gateway creates one with default config (owl-alpha primary).
        """
        if gateway is None:
            from core.spawn.openrouter_gateway import OpenRouterGateway
            self.gateway = OpenRouterGateway()
        else:
            self.gateway = gateway
    
    async def _call_llm(
        self,
        prompt: str,
        max_tokens: int = 2000,
        model: str = "openrouter/owl-alpha",
    ) -> str:
        """Call the LLM and return the response text."""
        try:
            response = await self.gateway.complete(
                prompt=prompt,
                max_tokens=max_tokens,
                model=model,
            )
            return response
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
    
    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown fences."""
        # Strip markdown fences
        text = text.strip()
        if text.startswith("```"):
            # Remove first line (```json or ```) and last line (```)
            lines = text.split("\n")
            if lines[-1].strip() == "```":
                lines = lines[1:-1]
            else:
                lines = lines[1:]
            text = "\n".join(lines)
        
        # Try to find JSON in the response
        text = text.strip()
        
        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON object in text
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end >= 0:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass
        
        logger.warning(f"Failed to parse JSON from LLM response: {text[:200]}...")
        return {}
    
    # ─── R1: Knowledge Decomposition ───
    
    async def extract_knowledge(
        self,
        text: str,
        title: str = "",
    ) -> Dict[str, Any]:
        """
        R1: Extract structured knowledge from a paper.
        
        Returns dict with: main_claims, mechanisms, assumptions,
        equations, limitations, novel_contribution, etc.
        """
        prompt = R1_CLAIM_EXTRACTION_PROMPT.format(
            title=title or "Unknown",
            text=text[:4000],  # Limit to first 4000 chars
        )
        
        response = await self._call_llm(prompt, max_tokens=1500)
        result = self._parse_json(response)
        
        if not result:
            logger.warning(f"R1 extraction returned empty for: {title}")
        
        return result
    
    async def extract_knowledge_batch(
        self,
        papers: List[Dict[str, str]],
    ) -> List[Dict[str, Any]]:
        """R1: Extract knowledge from multiple papers."""
        results = []
        for paper in papers:
            try:
                result = await self.extract_knowledge(
                    text=paper.get("text", ""),
                    title=paper.get("title", ""),
                )
                result["paper_title"] = paper.get("title", "")
                result["paper_id"] = paper.get("id", "")
                results.append(result)
            except Exception as e:
                logger.error(f"R1 batch extraction failed for '{paper.get('title', '?')}': {e}")
                results.append({"paper_title": paper.get("title", ""), "error": str(e)})
        return results
    
    # ─── R2: Semantic Relationships ───
    
    async def build_relationships(
        self,
        topic: str,
        paper_components: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        R2: Build semantic relationships between paper components.
        
        Returns dict with: concepts, relationships, causal_chains, clusters, dependencies.
        """
        # Serialize paper components (truncate for token limit)
        papers_json = json.dumps(paper_components[:10], ensure_ascii=False, indent=2)[:6000]
        
        prompt = R2_RELATIONSHIP_PROMPT.format(
            topic=topic,
            paper_json=papers_json,
        )
        
        response = await self._call_llm(prompt, max_tokens=2000)
        result = self._parse_json(response)
        
        if not result:
            logger.warning("R2 relationship building returned empty")
        
        return result
    
    # ─── R3: Cross-Document Reasoning ───
    
    async def cross_document_reason(
        self,
        topic: str,
        papers_json: str,
    ) -> Dict[str, Any]:
        """
        R3: Perform adversarial cross-document reasoning.
        
        Returns dict with: comparisons, contradictions, consensus,
        assumption_conflicts, explanatory_ranking, reasoning_chains, unified_reasoning.
        """
        prompt = R3_REASONING_PROMPT.format(
            topic=topic,
            papers_json=papers_json[:8000],
        )
        
        response = await self._call_llm(prompt, max_tokens=2500)
        result = self._parse_json(response)
        
        if not result:
            logger.warning("R3 reasoning returned empty")
        
        return result
    
    # ─── R4: Theory Synthesis ───
    
    async def synthesize_theory(
        self,
        topic: str,
        reasoning_json: str,
    ) -> Dict[str, Any]:
        """
        R4: Synthesize a unified theory and generate research report.
        
        Returns dict with: unified_theory, research_report, confidence.
        """
        prompt = R4_SYNTHESIS_PROMPT.format(
            topic=topic,
            reasoning_json=reasoning_json[:6000],
        )
        
        response = await self._call_llm(prompt, max_tokens=3000)
        result = self._parse_json(response)
        
        if not result:
            logger.warning("R4 synthesis returned empty")
        
        return result
    
    # ─── R5: Validation ───
    
    async def validate_synthesis(
        self,
        topic: str,
        report_text: str,
    ) -> Dict[str, Any]:
        """
        R5: Validate the quality of a research synthesis.
        
        Returns dict with: passed, metrics, benchmarks, recommendations.
        """
        prompt = R5_VALIDATION_PROMPT.format(
            topic=topic,
            report_text=report_text[:6000],
        )
        
        response = await self._call_llm(prompt, max_tokens=1500)
        result = self._parse_json(response)
        
        if not result:
            logger.warning("R5 validation returned empty")
        
        return result
    
    # ─── Full Pipeline ───
    
    async def run_full_pipeline(
        self,
        topic: str,
        papers: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """
        Run the full RCE pipeline (R1→R5) on a set of papers.
        
        Args:
            topic: Research topic/query
            papers: List of dicts with 'text', 'title', 'id' keys
            
        Returns:
            Complete pipeline results with all phases.
        """
        logger.info(f"RCE pipeline starting: {topic} ({len(papers)} papers)")
        
        # R1: Extract knowledge
        logger.info("R1: Extracting knowledge from papers...")
        r1_results = await self.extract_knowledge_batch(papers)
        logger.info(f"R1: Extracted {len(r1_results)} knowledge objects")
        
        # R2: Build relationships
        logger.info("R2: Building semantic relationships...")
        r2_results = await self.build_relationships(topic, r1_results)
        logger.info(f"R2: Found {len(r2_results.get('relationships', []))} relationships")
        
        # R3: Cross-document reasoning
        logger.info("R3: Cross-document reasoning...")
        papers_json = json.dumps(r1_results, ensure_ascii=False, indent=2)
        r3_results = await self.cross_document_reason(topic, papers_json)
        logger.info(f"R3: Found {len(r3_results.get('contradictions', []))} contradictions, "
                     f"{len(r3_results.get('consensus', []))} consensus areas")
        
        # R4: Theory synthesis
        logger.info("R4: Synthesizing theory...")
        reasoning_json = json.dumps(r3_results, ensure_ascii=False, indent=2)
        r4_results = await self.synthesize_theory(topic, reasoning_json)
        logger.info(f"R4: Synthesis confidence: {r4_results.get('confidence', 0):.3f}")
        
        # R5: Validation
        logger.info("R5: Validating synthesis...")
        report_text = r4_results.get("research_report", {}).get("full_report", "")
        r5_results = await self.validate_synthesis(topic, report_text)
        logger.info(f"R5: Passed: {r5_results.get('passed', False)}")
        
        return {
            "topic": topic,
            "num_papers": len(papers),
            "r1": r1_results,
            "r2": r2_results,
            "r3": r3_results,
            "r4": r4_results,
            "r5": r5_results,
        }
