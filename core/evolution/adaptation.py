"""Phase 1.7.8 — Long-Term Adaptation Engine. Tracks system evolution over time."""
from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.evolution.adaptation")


class LongTermAdaptationEngine:
    """Tracks system evolution and adapts priorities over time."""

    def __init__(self):
        self._history: List[Dict[str, Any]] = []
        self._domain_growth: Dict[str, int] = {}

    def record_snapshot(self, stats: Dict[str, Any]):
        """Record a snapshot of system state."""
        from datetime import datetime, timezone
        self._history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stats": stats,
        })

    def record_domain_activity(self, domain: str):
        """Record activity in a domain."""
        self._domain_growth[domain] = self._domain_growth.get(domain, 0) + 1

    def get_trends(self) -> Dict[str, Any]:
        """Analyze trends over time."""
        if len(self._history) < 2:
            return {"trend": "insufficient_data"}

        recent = self._history[-10:]
        return {
            "snapshots": len(self._history),
            "recent_activity": len(recent),
            "domain_growth": dict(self._domain_growth),
        }

    def suggest_reallocation(self) -> List[str]:
        """Suggest resource reallocation based on trends."""
        suggestions = []
        sorted_domains = sorted(self._domain_growth.items(), key=lambda x: -x[1])
        if sorted_domains:
            top_domain = sorted_domains[0][0]
            suggestions.append(f"Consider allocating more resources to {top_domain} (highest activity)")
        return suggestions

    def get_stats(self) -> Dict[str, Any]:
        return {
            "history_length": len(self._history),
            "domain_growth": dict(self._domain_growth),
        }
