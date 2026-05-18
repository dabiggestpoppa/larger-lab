"""
V3 Phase 7 — Scale-Adaptive Routing
Information classified by scale relevance.

Local info stays local. Regional info routes to cluster.
Global info broadcasts sparingly. This prevents information overload
and ensures each scale only processes what's relevant to it.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ScaleLevel(Enum):
    LOCAL = "local"
    REGIONAL = "regional"
    GLOBAL = "global"


@dataclass
class RoutedMessage:
    """A message routed according to its scale relevance."""
    message_id: str
    source: str
    content: str
    scale_level: ScaleLevel
    target_ids: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    delivered: bool = False


class ScaleAdaptiveRouter:
    """
    Routes information based on scale relevance.
    
    Classification:
    - Local: Relevant to a single observer (stays local)
    - Regional: Relevant to a cluster (routes to cluster members)
    - Global: Relevant to entire field (broadcasts sparingly)
    
    This prevents information overload and ensures each scale
    only processes what's relevant to it.
    """

    def __init__(self):
        self._routing_log: list[RoutedMessage] = []

    def classify_message(self, content: str, source_scope: str = "local") -> ScaleLevel:
        """Classify a message's scale relevance."""
        # Simple heuristic classification
        global_keywords = ["strategic", "mission", "global", "all", "system-wide"]
        regional_keywords = ["cluster", "regional", "team", "group", "shared"]

        content_lower = content.lower()

        if any(kw in content_lower for kw in global_keywords) or source_scope == "global":
            return ScaleLevel.GLOBAL
        elif any(kw in content_lower for kw in regional_keywords) or source_scope == "regional":
            return ScaleLevel.REGIONAL
        else:
            return ScaleLevel.LOCAL

    def route(
        self, content: str, source: str,
        local_targets: list[str] = None,
        regional_targets: list[str] = None,
        global_targets: list[str] = None,
        source_scope: str = "local",
    ) -> RoutedMessage:
        """Route a message to the appropriate targets based on scale."""
        scale = self.classify_message(content, source_scope)

        # Determine targets based on scale
        if scale == ScaleLevel.GLOBAL:
            targets = global_targets or []
        elif scale == ScaleLevel.REGIONAL:
            targets = regional_targets or local_targets or []
        else:
            targets = local_targets or []

        msg = RoutedMessage(
            message_id=f"msg_{int(time.time())}",
            source=source,
            content=content[:200],
            scale_level=scale,
            target_ids=targets,
            delivered=len(targets) > 0,
        )

        self._routing_log.append(msg)
        return msg

    def get_routing_stats(self) -> dict:
        """Get routing statistics."""
        if not self._routing_log:
            return {"total_messages": 0}

        local = sum(1 for m in self._routing_log if m.scale_level == ScaleLevel.LOCAL)
        regional = sum(1 for m in self._routing_log if m.scale_level == ScaleLevel.REGIONAL)
        global_ = sum(1 for m in self._routing_log if m.scale_level == ScaleLevel.GLOBAL)

        return {
            "total_messages": len(self._routing_log),
            "local": local,
            "regional": regional,
            "global": global_,
            "delivery_rate": round(
                sum(1 for m in self._routing_log if m.delivered) / len(self._routing_log), 4
            ),
        }

    @property
    def stats(self) -> dict:
        return self.get_routing_stats()


from enum import Enum  # Needed for ScaleLevel
