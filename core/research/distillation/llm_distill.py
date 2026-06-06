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
MAX_TOKENS_INPUT = 500
MAX_TOKENS_OUTPUT = 300
DAILY_COST_CAP_USD = 2.0

# Distillation prompt template
DISTILL_PROMPT = """Distill this research paper into operational signal. Be concise.

Title: {title}
Abstract: {abstract}
Authors: {authors}
Year: {year}

Output EXACTLY this format (no deviations):
CAUSE: [What problem does this paper address? One sentence.]
METHOD: [How did they solve it? One sentence.]
RESULT: [What changed? Include numbers if available. One sentence.]
LIMITATIONS: [Where does it fail? One sentence.]
APPLICATION: [How can an AI agent system use this? One sentence.]
LINKS: [2-3 related concepts from: {concepts}]

Rules:
- No essays. No rambling. No AI sludge.
- Each field: ONE sentence max.
- If a field can't be determined, write "Not stated".
- Operational signal only."""


class LLMDistiller:
    """
    LLM-assisted paper distillation with cost controls.
    
    Checks daily cost cap BEFORE every call. Fail-closed.
    Token budget: 500 in, 300 out per paper.
    """

    def __init__(
        self,
        llm_client: Optional[object] = None,
        model: str = "gpt-4o-mini",
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

        if not self.llm:
            logger.debug("LLM distiller: no client configured, skipping")
            return None

        # Build prompt
        prompt = self._build_prompt(paper)

        try:
            # Call LLM (placeholder — actual implementation uses OpenRouter/Ollama)
            # response = await self.llm.complete(
            #     prompt=prompt,
            #     max_tokens=MAX_TOKENS_OUTPUT,
            #     model=self.model,
            # )
            
            # Track cost (placeholder)
            cost = self._estimate_cost(prompt)
            self._daily_spent += cost
            self._call_count += 1
            
            logger.info(
                f"LLM distiller: distilled {paper.id} "
                f"(cost: ${cost:.4f}, daily: ${self._daily_spent:.2f}/{self.daily_cap_usd:.2f})"
            )
            
            # Return placeholder — actual implementation returns LLM response
            return None
            
        except Exception as e:
            logger.error(f"LLM distiller error for {paper.id}: {e}")
            return None

    def _build_prompt(self, paper: Paper) -> str:
        """Build distillation prompt from paper metadata."""
        authors = ", ".join(a.name for a in paper.authors[:3]) if paper.authors else "Unknown"
        concepts = ", ".join(c.name for c in paper.concepts[:5]) if paper.concepts else "general"
        
        return DISTILL_PROMPT.format(
            title=paper.title,
            abstract=paper.abstract[:1000] if paper.abstract else "No abstract available",
            authors=authors,
            year=paper.year,
            concepts=concepts,
        )

    def _estimate_cost(self, prompt: str) -> float:
        """
        Estimate cost of an LLM call.
        
        Uses rough token estimation: ~4 chars per token.
        """
        input_tokens = len(prompt) // 4
        output_tokens = MAX_TOKENS_OUTPUT
        
        # Rough cost estimate for gpt-4o-mini
        # $0.15 / 1M input tokens, $0.60 / 1M output tokens
        input_cost = (input_tokens / 1_000_000) * 0.15
        output_cost = (output_tokens / 1_000_000) * 0.60
        
        return input_cost + output_cost

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