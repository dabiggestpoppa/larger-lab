"""Phase 1.7.3 — Recursive Learning Loop. Continuous self-learning cycle."""
from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.evolution.learning")


class RecursiveLearningLoop:
    """Continuous self-learning: detect weakness → research → integrate → re-evaluate."""

    def __init__(self, evaluator=None, research_generator=None):
        self.evaluator = evaluator
        self.research_generator = research_generator
        self._cycle_count = 0
        self._max_cycles = 100

    async def run_cycle(self, domain: str, query: str = "") -> Dict[str, Any]:
        """Run one complete learning cycle for a domain."""
        self._cycle_count += 1
        logger.info(f"Learning cycle #{self._cycle_count} for: {domain}")

        result = {
            "cycle": self._cycle_count,
            "domain": domain,
            "steps": [],
        }

        # Step 1: Evaluate current state
        if self.evaluator:
            report = self.evaluator.evaluate()
            weak_domains = self.evaluator.get_weak_domains()
            result["steps"].append({"evaluation": report.overall_confidence, "weak_domains": weak_domains})

        # Step 2: Generate research objective
        if self.research_generator:
            obj = self.research_generator.generate_from_gap(domain, 0.3)
            if obj:
                result["steps"].append({"objective": obj.title, "priority": obj.priority})

        # Step 3: Mark complete (actual research would happen here)
        if self.research_generator:
            pending = self.research_generator.get_pending_objectives(1)
            for p in pending:
                self.research_generator.mark_complete(p.objective_id)

        return result

    def get_stats(self) -> Dict[str, Any]:
        return {"cycles_completed": self._cycle_count, "max_cycles": self._max_cycles}
