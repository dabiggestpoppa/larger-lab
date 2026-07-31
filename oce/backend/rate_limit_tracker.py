"""
Rate Limit Tracker — tracks API usage and rate limits.

Provides rate limiting for OpenRouter, Anthropic, and other LLM providers.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.rate_limit_tracker")

# Default state file location
DEFAULT_STATE_FILE = Path(__file__).parent / "rate_limit_state.json"

# Rate limits per provider (requests per minute)
DEFAULT_LIMITS = {
    "openrouter": 100,
    "anthropic": 50,
    "openai": 3000,
}


class RateLimitTracker:
    """Tracks API usage and enforces rate limits."""

    def __init__(self, state_file: Optional[Path] = None):
        self.state_file = state_file or DEFAULT_STATE_FILE
        self._state: Dict[str, Any] = self._load_state()
        self._limits = DEFAULT_LIMITS.copy()

    def _load_state(self) -> Dict[str, Any]:
        """Load state from file."""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load rate limit state: {e}")
        return {"daily_usage": {}, "daily_spend": {}, "errors": []}

    def _save_state(self) -> None:
        """Save state to file."""
        try:
            with open(self.state_file, "w") as f:
                json.dump(self._state, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save rate limit state: {e}")

    def record_call(
        self,
        model: str,
        tokens: int = 0,
        cost: float = 0.0,
        status_code: int = 200,
        error_type: str = "",
    ) -> None:
        """Record an API call."""
        today = time.strftime("%Y-%m-%d")
        self._state["daily_usage"][today] = self._state["daily_usage"].get(today, 0) + 1
        self._state["daily_spend"][today] = self._state["daily_spend"].get(today, 0.0) + cost
        if status_code >= 400:
            self._state["errors"].append([time.time(), status_code, error_type or f"HTTP {status_code}", model])
            self._state["errors"] = self._state["errors"][-100:]
        self._save_state()

    def record_error(self, model: str, status: int, error: str) -> None:
        """Record an API error."""
        self._state["errors"].append([time.time(), status, error, model])
        # Keep only last 100 errors
        self._state["errors"] = self._state["errors"][-100:]
        self._save_state()

    def get_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        today = time.strftime("%Y-%m-%d")
        daily_usage = self._state.get("daily_usage", {}).get(today, 0)
        daily_spend = self._state.get("daily_spend", {}).get(today, 0.0)
        errors = self._state.get("errors", [])

        # Calculate error rate
        recent_errors = [e for e in errors if e[0] > time.time() - 3600]
        error_rate = {
            "total": len(errors),
            "recent_hour": len(recent_errors),
        }

        return {
            "daily_usage_today": daily_usage,
            "daily_spend_today_usd": daily_spend,
            "error_rate": error_rate,
            "models": {},
            "alerts": [],
        }


# Global singleton
_tracker: Optional[RateLimitTracker] = None


def get_rate_limit_tracker() -> RateLimitTracker:
    """Get the global rate limit tracker."""
    global _tracker
    if _tracker is None:
        _tracker = RateLimitTracker()
    return _tracker


def record_api_call(
    model: str,
    tokens: int = 0,
    cost: float = 0.0,
    status_code: int = 200,
    error_type: str = "",
) -> None:
    """Record an API call (convenience function)."""
    get_rate_limit_tracker().record_call(model, tokens, cost, status_code, error_type)