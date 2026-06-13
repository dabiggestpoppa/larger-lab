"""
Phase 1.7.2 — Autonomous Research Generator

Generates research tasks internally — no human trigger needed.
Detects knowledge gaps and creates learning objectives.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.evolution.research")


@dataclass
class ResearchObjective:
    """An autonomously generated research objective."""
    objective_id: str = field(default_factory=lambda: str(uuid.uuid4())[:10])
    title: str = ""
    description: str = ""
    target_domain: str = ""
    priority: float = 0.5  # 0-1, higher = more important
    source: str = "gap_detection"  # How this objective was created
    status: str = "pending"  # pending, in_progress, complete
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


class AutonomousResearchGenerator:
    """
    Generates research tasks internally.
    
    Example flow:
    1. System detects weak quantum computing knowledge
    2. Creates objective: "Acquire 500 papers on quantum computing"
    3. Queues for execution
    4. System learns autonomously
    """

    def __init__(self):
        self._objectives: Dict[str, ResearchObjective] = {}
        self._completed: List[str] = []

    def generate_from_gap(
        self,
        domain: str,
        current_confidence: float,
        target_confidence: float = 0.7,
    ) -> Optional[ResearchObjective]:
        """Generate a research objective from a detected knowledge gap."""
        if current_confidence >= target_confidence:
            return None

        gap = target_confidence - current_confidence
        priority = min(1.0, gap * 2)  # Higher gap = higher priority

        obj = ResearchObjective(
            title=f"Strengthen {domain} knowledge",
            description=(
                f"Autonomous research objective: Acquire and synthesize knowledge "
                f"in {domain}. Current confidence: {current_confidence:.0%}, "
                f"target: {target_confidence:.0%}. "
                f"Gap: {gap:.0%}."
            ),
            target_domain=domain,
            priority=priority,
            source="gap_detection",
        )

        self._objectives[obj.objective_id] = obj
        logger.info(f"Research objective created: {obj.title} (priority={priority:.2f})")
        return obj

    def generate_from_curiosity(
        self,
        known_domains: List[str],
        adjacent_domains: Dict[str, List[str]],
    ) -> List[ResearchObjective]:
        """
        Generate objectives based on curiosity — exploring unknown domains
        adjacent to known knowledge.
        """
        objectives = []
        for domain in known_domains:
            adjacent = adjacent_domains.get(domain, [])
            for adj_domain in adjacent:
                # Check if we already know this domain
                if adj_domain not in known_domains:
                    obj = ResearchObjective(
                        title=f"Explore {adj_domain} (adjacent to {domain})",
                        description=(
                            f"Curiosity-driven research: {adj_domain} is adjacent to "
                            f"known domain {domain}. Exploring to expand knowledge frontier."
                        ),
                        target_domain=adj_domain,
                        priority=0.3,  # Lower priority than gap-driven
                        source="curiosity",
                    )
                    self._objectives[obj.objective_id] = obj
                    objectives.append(obj)

        logger.info(f"Curiosity generated {len(objectives)} research objectives")
        return objectives

    def get_pending_objectives(self, limit: int = 10) -> List[ResearchObjective]:
        """Get pending research objectives, sorted by priority."""
        pending = [
            obj for obj in self._objectives.values()
            if obj.status == "pending"
        ]
        pending.sort(key=lambda o: o.priority, reverse=True)
        return pending[:limit]

    def mark_in_progress(self, objective_id: str):
        obj = self._objectives.get(objective_id)
        if obj:
            obj.status = "in_progress"

    def mark_complete(self, objective_id: str):
        obj = self._objectives.get(objective_id)
        if obj:
            obj.status = "complete"
            self._completed.append(objective_id)

    def get_stats(self) -> Dict[str, Any]:
        total = len(self._objectives)
        pending = sum(1 for o in self._objectives.values() if o.status == "pending")
        in_progress = sum(1 for o in self._objectives.values() if o.status == "in_progress")
        complete = sum(1 for o in self._objectives.values() if o.status == "complete")
        return {
            "total": total,
            "pending": pending,
            "in_progress": in_progress,
            "complete": complete,
        }
