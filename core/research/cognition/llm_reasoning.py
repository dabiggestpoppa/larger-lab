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

import asyncio
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
    
    Two-model strategy:
    - FAST_MODEL (nemotron): R1 extraction, R2 relationships, R3 reasoning, R5 validation
    - POWER_MODEL (nex-n2-pro): R4 final theory synthesis and report generation
    
    Wraps OpenRouterGateway with structured prompts and JSON parsing.
    Each method corresponds to one RCE phase.
    """
    
    FAST_MODEL = "nvidia/nemotron-3-ultra-550b-a55b:free"
    POWER_MODEL = "nex-agi/nex-n2-pro:free"
    
    def __init__(self, gateway: Optional[Any] = None, max_concurrent: int = 3):
        """
        Initialize with an OpenRouterGateway instance.
        
        If no gateway creates one with default config.
        max_concurrent: max parallel LLM calls (to avoid rate limiting).
        """
        if gateway is None:
            from core.spawn.openrouter_gateway import OpenRouterGateway
            self.gateway = OpenRouterGateway()
        else:
            self.gateway = gateway
        self._semaphore = asyncio.Semaphore(max_concurrent)
    
    async def _call_llm(
        self,
        prompt: str,
        max_tokens: int = 2000,
        model: str = "",
    ) -> str:
        """Call the LLM and return the response text."""
        if not model:
            model = self.FAST_MODEL
        try:
            async with self._semaphore:
                response = await self.gateway.complete(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    model=model,
                )
            return response
        except Exception as e:
            error_str = str(e)
            logger.error(f"LLM call failed ({model}): {error_str}")
            
            # If it's a 400 error, the model may not be available — failover
            if "400" in error_str or "Provider returned error" in error_str:
                fallback_models = [
                    "openrouter/owl-alpha",
                    "nvidia/nemotron-3-ultra-550b-a55b:free",
                    "nex-agi/nex-n2-pro:free",
                ]
                for fallback in fallback_models:
                    if fallback == model:
                        continue
                    try:
                        logger.info(f"Trying fallback model: {fallback}")
                        response = await self.gateway.complete(
                            prompt=prompt,
                            max_tokens=max_tokens,
                            model=fallback,
                        )
                        return response
                    except Exception as e2:
                        logger.warning(f"Fallback {fallback} also failed: {e2}")
                        continue
            
            # Re-raise if no fallback worked
            raise
    
    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown fences and truncation."""
        import re as _re
        
        text = text.strip()
        
        # Strip markdown fences
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[-1].strip() == "```":
                lines = lines[1:-1]
            else:
                lines = lines[1:]
            text = "\n".join(lines)
        
        text = text.strip()
        
        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON object in text (find first { to last })
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end >= 0 and end > start:
            candidate = text[start:end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                # Try to fix truncated JSON by closing open brackets
                open_braces = candidate.count("{") - candidate.count("}")
                open_brackets = candidate.count("[") - candidate.count("]")
                if open_braces > 0 or open_brackets > 0:
                    fixed = candidate + "}" * open_braces + "]" * open_brackets
                    try:
                        return json.loads(fixed)
                    except json.JSONDecodeError:
                        pass
        
        # Try to extract JSON from ```json ... ``` blocks
        json_blocks = _re.findall(r'```(?:json)?\s*\n?(.*?)\n?```', text, _re.DOTALL)
        for block in json_blocks:
            try:
                return json.loads(block.strip())
            except json.JSONDecodeError:
                continue
        
        logger.warning(f"Failed to parse JSON from LLM response: {text[:300]}...")
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
        # nemotron has 1M context, so we can use more text and higher max_tokens
        # Limit to 12000 chars to stay well within context
        prompt = R1_CLAIM_EXTRACTION_PROMPT.format(
            title=title or "Unknown",
            text=text[:12000],
        )
        
        # nemotron: 1M context, can use high max_tokens
        response = await self._call_llm(prompt, max_tokens=8000, model=self.FAST_MODEL)
        result = self._parse_json(response)
        
        if not result:
            logger.warning(f"R1 extraction returned empty for: {title}")
            return {
                "paper_title": title,
                "main_claims": [],
                "mechanisms": [],
                "assumptions": [],
                "equations": [],
                "limitations": [],
                "error": "LLM extraction failed",
            }
        
        return result
    
    async def extract_knowledge_batch(
        self,
        papers: List[Dict[str, str]],
    ) -> List[Dict[str, Any]]:
        """R1: Extract knowledge from multiple papers (parallel)."""
        import asyncio
        
        tasks = []
        for paper in papers:
            task = self.extract_knowledge_safe(
                text=paper.get("text", ""),
                title=paper.get("title", ""),
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"R1 batch failed for paper {i}: {result}")
                processed.append({
                    "paper_title": papers[i].get("title", ""),
                    "error": str(result),
                })
            else:
                processed.append(result)
        
        return processed
    
    async def extract_knowledge_safe(
        self,
        text: str,
        title: str = "",
    ) -> Dict[str, Any]:
        """R1: Extract knowledge with error handling."""
        try:
            result = await self.extract_knowledge(text, title)
            result["paper_title"] = title
            return result
        except Exception as e:
            logger.error(f"R1 extraction failed for '{title}': {e}")
            return {
                "paper_title": title,
                "main_claims": [],
                "mechanisms": [],
                "assumptions": [],
                "equations": [],
                "limitations": [],
                "error": str(e),
            }
    
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
        
        response = await self._call_llm(prompt, max_tokens=4000, model=self.FAST_MODEL)
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
        
        response = await self._call_llm(prompt, max_tokens=5000, model=self.FAST_MODEL)
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
        # nex-n2-pro has 128K context — truncate reasoning to stay within limits
        reasoning_truncated = reasoning_json[:4000]
        prompt = R4_SYNTHESIS_PROMPT.format(
            topic=topic,
            reasoning_json=reasoning_truncated,
        )
        response = await self._call_llm(prompt, max_tokens=6000, model=self.POWER_MODEL)
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
        
        response = await self._call_llm(prompt, max_tokens=3000, model=self.FAST_MODEL)
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
        
        Two-model strategy:
        - R1-R3, R5: FAST_MODEL (nemotron) — fast extraction, reasoning, validation
        - R4: POWER_MODEL (nex-n2-pro) — deep synthesis and report generation
        
        R1 extractions run in parallel for speed.
        
        Args:
            topic: Research topic/query
            papers: List of dicts with 'text', 'title', 'id' keys
            
        Returns:
            Complete pipeline results with all phases.
        """
        logger.info(f"RCE pipeline starting: {topic} ({len(papers)} papers)")
        logger.info(f"Fast model: {self.FAST_MODEL}")
        logger.info(f"Power model: {self.POWER_MODEL}")
        
        # R1: Extract knowledge (PARALLEL for speed)
        logger.info("R1: Extracting knowledge from papers (parallel)...")
        r1_results = await self.extract_knowledge_batch(papers)
        logger.info(f"R1: Extracted {len(r1_results)} knowledge objects")
        
        # R2: Build relationships (fast model)
        logger.info("R2: Building semantic relationships...")
        r2_results = await self.build_relationships(topic, r1_results)
        logger.info(f"R2: Found {len(r2_results.get('relationships', []))} relationships")
        
        # R3: Cross-document reasoning (fast model)
        logger.info("R3: Cross-document reasoning...")
        papers_json = json.dumps(r1_results, ensure_ascii=False, indent=2)
        r3_results = await self.cross_document_reason(topic, papers_json)
        logger.info(f"R3: Found {len(r3_results.get('contradictions', []))} contradictions, "
                     f"{len(r3_results.get('consensus', []))} consensus areas")
        
        # R4: Theory synthesis (POWER MODEL for deep reasoning)
        logger.info("R4: Synthesizing theory (power model)...")
        reasoning_json = json.dumps(r3_results, ensure_ascii=False, indent=2)
        r4_results = await self.synthesize_theory(topic, reasoning_json)
        logger.info(f"R4: Synthesis confidence: {r4_results.get('confidence', 0):.3f}")
        
        # R5: Validation (fast model)
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
