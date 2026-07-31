"""
Phase 1.6.3 — Planner Engine

Task decomposition and execution sequencing.
Breaks objectives into ordered subtasks with dependency resolution.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.planner")


@dataclass
class Subtask:
    """A decomposed unit of work."""
    subtask_id: str = field(default_factory=lambda: str(uuid.uuid4())[:10])
    title: str = ""
    description: str = ""
    dependencies: List[str] = field(default_factory=list)  # subtask_ids that must complete first
    assigned_agent: str = ""
    is_complete: bool = False
    output: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionPlan:
    """A complete execution plan for an objective."""
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    objective: str = ""
    subtasks: List[Subtask] = field(default_factory=list)
    created_at: str = ""

    @property
    def is_complete(self) -> bool:
        return all(s.is_complete for s in self.subtasks)

    @property
    def completion_pct(self) -> float:
        if not self.subtasks:
            return 0.0
        complete = sum(1 for s in self.subtasks if s.is_complete)
        return complete / len(self.subtasks)

    def get_ready_subtasks(self) -> List[Subtask]:
        """Get subtasks whose dependencies are all complete."""
        completed_ids = {s.subtask_id for s in self.subtasks if s.is_complete}
        ready = []
        for subtask in self.subtasks:
            if subtask.is_complete:
                continue
            if all(dep in completed_ids for dep in subtask.dependencies):
                ready.append(subtask)
        return ready


class PlannerEngine:
    """
    Decomposes objectives into execution plans.
    
    Example:
        "Research semantic memory systems" →
        1. retrieve papers
        2. parse papers  
        3. compare architectures
        4. synthesize findings
        5. update topology
        6. generate report
    """

    # Template plans for common objectives
    TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
        "research": [
            {"title": "Retrieve sources", "agent": "ingestion", "deps": []},
            {"title": "Analyze sources", "agent": "synthesis", "deps": ["Retrieve sources"]},
            {"title": "Cross-reference findings", "agent": "synthesis", "deps": ["Analyze sources"]},
            {"title": "Detect contradictions", "agent": "reflection", "deps": ["Cross-reference findings"]},
            {"title": "Generate report", "agent": "synthesis", "deps": ["Detect contradictions"]},
            {"title": "Generate PDF", "agent": "synthesis", "deps": ["Generate report"]},
            {"title": "Update knowledge graph", "agent": "topology", "deps": ["Generate report"]},
            {"title": "Store in vault", "agent": "storage", "deps": ["Update knowledge graph"]},
        ],
        "ingest": [
            {"title": "Fetch from OpenAlex", "agent": "ingestion", "deps": []},
            {"title": "Normalize data", "agent": "ingestion", "deps": ["Fetch from OpenAlex"]},
            {"title": "Chunk and embed", "agent": "embedding", "deps": ["Normalize data"]},
            {"title": "Store in vector DB", "agent": "storage", "deps": ["Chunk and embed"]},
        ],
        "retrieve": [
            {"title": "Embed query", "agent": "embedding", "deps": []},
            {"title": "Vector search", "agent": "retrieval", "deps": ["Embed query"]},
            {"title": "Rerank results", "agent": "retrieval", "deps": ["Vector search"]},
            {"title": "Assemble context", "agent": "retrieval", "deps": ["Rerank results"]},
        ],
    }

    def plan(self, objective: str, objective_type: str = "research") -> ExecutionPlan:
        """
        Create an execution plan for an objective.
        
        Uses templates for common objectives, falls back to LLM-based planning.
        """
        plan = ExecutionPlan(objective=objective)

        # Use template if available
        template = self.TEMPLATES.get(objective_type, self.TEMPLATES["research"])

        prev_id = None
        for i, step in enumerate(template):
            subtask = Subtask(
                title=step["title"],
                description=f"Step {i+1}: {step['title']}",
                assigned_agent=step.get("agent", "general"),
            )
            # Chain dependencies
            if prev_id:
                subtask.dependencies.append(prev_id)
            plan.subtasks.append(subtask)
            prev_id = subtask.subtask_id

        logger.info(f"Created plan for '{objective}': {len(plan.subtasks)} subtasks")
        return plan

    def plan_custom(self, objective: str, steps: List[Dict[str, Any]]) -> ExecutionPlan:
        """Create a custom execution plan from explicit steps."""
        plan = ExecutionPlan(objective=objective)

        id_map: Dict[str, str] = {}  # title -> subtask_id
        for i, step in enumerate(steps):
            subtask = Subtask(
                title=step.get("title", f"Step {i+1}"),
                description=step.get("description", ""),
                assigned_agent=step.get("agent", "general"),
            )
            # Resolve dependency titles to IDs
            for dep_title in step.get("deps", []):
                if dep_title in id_map:
                    subtask.dependencies.append(id_map[dep_title])

            plan.subtasks.append(subtask)
            id_map[subtask.title] = subtask.subtask_id

        return plan

    def mark_complete(self, plan: ExecutionPlan, subtask_title: str) -> bool:
        """Mark a subtask as complete."""
        for subtask in plan.subtasks:
            if subtask.title == subtask_title:
                subtask.is_complete = True
                logger.info(f"Subtask complete: {subtask_title} ({plan.completion_pct:.0%})")
                return True
        return False
