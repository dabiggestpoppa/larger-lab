"""
L3.5 — Research task router.

Routes research tasks to:
- Local LLM (Ollama) for simple queries
- OpenRouter for complex queries
- Skip if budget exhausted

Usage:
    router = ResearchRouter()
    target = router.route(task)
    # Returns 'ollama', 'openrouter', or 'skip'
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Budget thresholds
DAILY_BUDGET_USD = 2.0
OLLAMA_COST_PER_CALL = 0.0  # Free (local)
OPENROUTER_COST_PER_CALL = 0.005  # Rough estimate for gpt-4o-mini

# Complexity thresholds for routing
SIMPLE_QUERY_MAX_WORDS = 10
COMPLEX_QUERY_MIN_WORDS = 20


class ResearchRouter:
    """
    Routes research tasks to appropriate LLM backend.
    
    Routing logic:
    - Simple queries → Ollama (free, local)
    - Complex queries → OpenRouter (if budget available)
    - Budget exhausted → skip
    """

    def __init__(
        self,
        daily_budget_usd: float = DAILY_BUDGET_USD,
        ollama_url: str = "http://localhost:11434",
        openrouter_key: str = "",
    ):
        self.daily_budget_usd = daily_budget_usd
        self.ollama_url = ollama_url
        self.openrouter_key = openrouter_key
        self._daily_spent = 0.0
        self._call_count = 0

    def route(self, task: Any) -> str:
        """
        Route a research task to appropriate backend.
        
        Args:
            task: ResearchTask object
            
        Returns:
            'ollama', 'openrouter', or 'skip'
        """
        # Check budget first
        if self._daily_spent >= self.daily_budget_usd:
            logger.warning(f"Router: daily budget exhausted (${self._daily_spent:.2f}/{self.daily_budget_usd:.2f})")
            return "skip"

        query = getattr(task, 'query', str(task))
        complexity = self._assess_complexity(query)

        if complexity == "simple":
            return "ollama"
        elif complexity == "complex":
            # Check if we can afford OpenRouter
            if self._daily_spent + OPENROUTER_COST_PER_CALL <= self.daily_budget_usd:
                return "openrouter"
            else:
                logger.info("Router: not enough budget for OpenRouter, falling back to Ollama")
                return "ollama"
        else:
            return "ollama"

    def record_call(self, backend: str, cost: float = 0.0) -> None:
        """Record an LLM call for budget tracking."""
        self._daily_spent += cost
        self._call_count += 1
        logger.debug(f"Router: {backend} call recorded (cost: ${cost:.4f}, daily: ${self._daily_spent:.2f})")

    def _assess_complexity(self, query: str) -> str:
        """Assess query complexity for routing."""
        word_count = len(query.split())
        
        if word_count <= SIMPLE_QUERY_MAX_WORDS:
            return "simple"
        elif word_count >= COMPLEX_QUERY_MIN_WORDS:
            return "complex"
        else:
            return "medium"

    def get_status(self) -> Dict[str, Any]:
        """Get current router status."""
        return {
            "daily_budget_usd": self.daily_budget_usd,
            "daily_spent_usd": round(self._daily_spent, 4),
            "remaining_usd": round(self.daily_budget_usd - self._daily_spent, 4),
            "call_count": self._call_count,
            "ollama_available": self._check_ollama(),
            "openrouter_configured": bool(self.openrouter_key),
        }

    def _check_ollama(self) -> bool:
        """Check if Ollama is available."""
        try:
            import httpx
            response = httpx.get(f"{self.ollama_url}/api/tags", timeout=2.0)
            return response.status_code == 200
        except Exception:
            return False

    def reset_daily_budget(self) -> None:
        """Reset daily budget counter."""
        self._daily_spent = 0.0
        self._call_count = 0
        logger.info("Router: daily budget reset")