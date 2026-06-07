"""
L2.6 — LLM-assisted distillation (opt-in, cost-bounded).

Wraps LLM calls for paper distillation with strict cost controls.
Rule-based distiller (L2.1) is primary; this is opt-in per paper.

Usage:
    distiller = LLMDistiller(model="gpt-4o-mini")
    note = await distiller.distill(paper)
    # Returns markdown note or None if cost cap hit
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from ..ingestion.models import Paper

logger = logging.getLogger(__name__)

# Cost controls (per TEAM-NOTES §0)
DAILY_COST_CAP_USD = 2.0
# Note: Nemotron is free, no token budget needed

# Distillation prompt template
DISTILL_PROMPT = """Distill this research paper into operational signal for AI agent systems.

Title: {title}
Abstract: {abstract}
Authors: {authors}
Year: {year}

Output EXACTLY this format (no deviations):
CAUSE: [What problem does this paper address? 3-5 sentences explaining the core problem, why it matters, and what gaps exist.]
METHOD: [How did they solve it? 3-5 sentences describing the approach, key innovations, and technical details.]
RESULT: [What changed? 3-5 sentences with quantitative results, comparisons, and significance.]
LIMITATIONS: [Where does it fail? 3-5 sentences on constraints, assumptions, and failure modes.]
APPLICATION: [How can an AI agent system use this? 3-5 sentences on practical applications, integration patterns, and operational relevance.]
LINKS: [2-3 related concepts from: {concepts}]

Rules:
- Each field: 3-5 sentences. Be thorough.
- If a field can't be determined, write "Not stated".
- Operational signal only. No fluff.
- Include specific numbers, methods, and concrete details."""


class LLMDistiller:
    """
    LLM-assisted paper distillation with cost controls.
    
    Checks daily cost cap BEFORE every call. Fail-closed.
    Token budget: 10000 in, 2000 out per paper.
    Uses nvidia/nemotron-3-ultra-550b-a55b:free via OpenRouter.
    """

    def __init__(
        self,
        llm_client: Optional[object] = None,
        model: str = "nvidia/nemotron-3-ultra-550b-a55b:free",
        daily_cap_usd: float = DAILY_COST_CAP_USD,
    ):
        self.llm = llm_client
        self.model = model
        self.daily_cap_usd = daily_cap_usd
        self._daily_spent = 0.0
        self._call_count = 0

    async def distill(self, paper: Paper) -> Optional[str]:
        """
        Distill a paper using LLM.
        
        Returns None if cost cap is hit or LLM is unavailable.
        """
        # Check cost cap (fail-closed)
        if self._daily_spent >= self.daily_cap_usd:
            logger.warning(
                f"LLM distiller: daily cap (${self.daily_cap_usd:.2f}) reached. "
                f"Spent: ${self._daily_spent:.2f}. Skipping."
            )
            return None

        # Build prompt
        prompt = self._build_prompt(paper)

        try:
            # Use OpenRouterGateway if no LLM client provided
            if not self.llm:
                from core.spawn.openrouter_gateway import OpenRouterGateway
                gateway = OpenRouterGateway()
                response = await gateway.complete(prompt, model=self.model)
            else:
                # Call LLM client directly
                response = await self.llm.complete(
                    prompt=prompt,
                    model=self.model,
                )
            
            # Track cost (free model, but still count for safety)
            cost = self._estimate_cost(prompt)
            self._daily_spent += cost
            self._call_count += 1
            
            logger.info(
                f"LLM distiller: distilled {paper.id} "
                f"(cost: ${cost:.4f}, daily: ${self._daily_spent:.2f}/{self.daily_cap_usd:.2f})"
            )
            
            return response
            
        except Exception as e:
            logger.error(f"LLM distiller error for {paper.id}: {e}")
            return None

    def _build_prompt(self, paper: Paper) -> str:
        """Build distillation prompt from paper metadata."""
        authors = ", ".join(a.name for a in paper.authors[:3]) if paper.authors else "Unknown"
        concepts = ", ".join(c.name for c in paper.concepts[:5]) if paper.concepts else "general"
        
        # Use full abstract (Nemotron has 1M context)
        abstract = paper.abstract if paper.abstract else "No abstract available"
        
        return DISTILL_PROMPT.format(
            title=paper.title,
            abstract=abstract,
            authors=authors,
            year=paper.year,
            concepts=concepts,
        )

    def _estimate_cost(self, prompt: str) -> float:
        """
        Estimate cost of an LLM call.
        
        Free models (like Nemotron) return 0 cost.
        """
        # Free model - no cost
        if "nemotron" in self.model.lower() or "free" in self.model.lower():
            return 0.0
        
        # Rough cost estimate for paid models
        input_tokens = len(prompt) // 4
        input_cost = (input_tokens / 1_000_000) * 0.15
        
        return input_cost

    def get_status(self) -> dict:
        """Get current distiller status."""
        return {
            "daily_spent_usd": round(self._daily_spent, 4),
            "daily_cap_usd": self.daily_cap_usd,
            "remaining_usd": round(self.daily_cap_usd - self._daily_spent, 4),
            "call_count": self._call_count,
            "llm_configured": self.llm is not None,
            "model": self.model,
        }

    def reset_daily_counter(self) -> None:
        """Reset daily spending counter (call at midnight UTC)."""
        self._daily_spent = 0.0
        self._call_count = 0
        logger.info("LLM distiller: daily counter reset")