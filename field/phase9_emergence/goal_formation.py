"""
9_emergence.goal_formation
==========================
Autonomous goal formation engine for the field.

Generates, evaluates, and manages goals for the field system.
Goals are formed from:
- detected needs (gaps between current and desired states)
- operator suggestions (human-in-the-loop goal input)
- emergent opportunities (patterns detected by emergence monitor)
- self-improvement drives (from self_model reflections)

Each goal has priority, progress tracking, dependencies, and a
lifecycle: proposed → evaluated → active → completed / abandoned.
"""

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from enum import Enum
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.emergence.goal_formation")


class GoalStatus(str, Enum):
    PROPOSED = "proposed"
    EVALUATING = "evaluating"
    ACTIVE = "active"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class Goal(BaseModel):
    """A field goal with lifecycle tracking."""
    goal_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str
    description: str = ""
    status: str = "proposed"
    priority: float = 0.5          # 0-1, higher = more important
    progress: float = 0.0          # 0-1, completion percentage
    source: str = "autonomous"     # autonomous, operator, emergent, self_improvement
    dependencies: List[str] = Field(default_factory=list)  # goal_ids
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GoalFormationConfig(BaseModel):
    """Configuration for goal_formation."""
    enabled: bool = True
    max_active_goals: int = 20
    max_total_goals: int = 500
    evaluation_threshold: float = 0.4   # min score to auto-activate
    priority_decay: float = 0.995       # per-cycle decay for stale goals
    need_detection_interval: int = 50   # cycles between need scans


class GoalFormationModule:
    """Autonomous goal formation engine for the field."""

    def __init__(self):
        self.config = GoalFormationConfig()
        self.running = False
        self._lock = Lock()
        self._goals: Dict[str, Goal] = {}
        self._active_goals: Dict[str, Goal] = {}
        self._completed_goals: Dict[str, Goal] = {}
        self._goal_history: List[Dict[str, Any]] = []
        self._needs: Dict[str, float] = {}  # need_name -> urgency (0-1)
        self._cycle_count: int = 0
        self._goals_formed: int = 0
        self._goals_completed: int = 0

    def start(self) -> None:
        """Start the goal formation engine."""
        self.running = True
        logger.info("GoalFormation started")

    def stop(self) -> None:
        """Stop the goal formation engine."""
        self.running = False
        # Mark all active goals as blocked
        with self._lock:
            for gid, goal in self._active_goals.items():
                goal.status = "blocked"
                goal.updated_at = datetime.now(timezone.utc).isoformat()
            self._active_goals.clear()
        logger.info("GoalFormation stopped — %d formed, %d completed",
                     self._goals_formed, self._goals_completed)

    def propose_goal(self, title: str, description: str = "",
                     priority: float = 0.5, source: str = "autonomous",
                     dependencies: Optional[List[str]] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> Goal:
        """
        Propose a new goal.

        Args:
            title: Short goal title.
            description: Detailed description.
            priority: Initial priority 0-1.
            source: Origin of the goal.
            dependencies: List of goal_ids that must complete first.
            metadata: Additional metadata.

        Returns:
            The proposed Goal.
        """
        goal = Goal(
            title=title,
            description=description,
            status="proposed",
            priority=round(max(0.0, min(1.0, priority)), 4),
            source=source,
            dependencies=dependencies or [],
            metadata=metadata or {},
        )

        with self._lock:
            self._goals[goal.goal_id] = goal
            self._goals_formed += 1

        logger.info("Goal proposed: [%s] %s (priority=%.2f, source=%s)",
                     goal.goal_id, title, goal.priority, source)
        return goal

    def evaluate_goal(self, goal_id: str) -> Dict[str, Any]:
        """
        Evaluate a proposed goal for activation readiness.

        Checks dependencies, computes feasibility score, and decides
        whether to activate, keep proposed, or abandon.

        Args:
            goal_id: The goal to evaluate.

        Returns:
            Evaluation result with decision and scores.
        """
        with self._lock:
            goal = self._goals.get(goal_id)
            if not goal:
                return {"error": "goal not found", "goal_id": goal_id}

            goal.status = "evaluating"
            goal.updated_at = datetime.now(timezone.utc).isoformat()

            # Check dependency satisfaction
            deps_met = all(
                dep_id in self._completed_goals
                for dep_id in goal.dependencies
            )
            blocked_by = [
                dep_id for dep_id in goal.dependencies
                if dep_id not in self._completed_goals
            ]

            # Feasibility: combination of priority and dependency readiness
            dep_score = 1.0 if deps_met else max(0.0, 1.0 - len(blocked_by) * 0.3)
            feasibility = 0.6 * goal.priority + 0.4 * dep_score

            # Need alignment: does this goal address a detected need?
            need_score = 0.0
            for need_name, urgency in self._needs.items():
                if need_name.lower() in goal.title.lower() or \
                   need_name.lower() in goal.description.lower():
                    need_score = max(need_score, urgency)

            total_score = 0.5 * feasibility + 0.3 * goal.priority + 0.2 * need_score

            if deps_met and total_score >= self.config.evaluation_threshold:
                decision = "activate"
                goal.status = "active"
                self._active_goals[goal_id] = goal
            elif not deps_met:
                decision = "wait"
                goal.status = "blocked"
            elif total_score < self.config.evaluation_threshold * 0.5:
                decision = "abandon"
                goal.status = "abandoned"
            else:
                decision = "hold"
                goal.status = "proposed"

            result = {
                "goal_id": goal_id,
                "decision": decision,
                "total_score": round(total_score, 4),
                "feasibility": round(feasibility, 4),
                "need_alignment": round(need_score, 4),
                "dependencies_met": deps_met,
                "blocked_by": blocked_by,
            }

        logger.info("Goal evaluation: [%s] %s → %s (score=%.3f)",
                     goal_id, goal.title, decision, total_score)
        return result

    def update_progress(self, goal_id: str, progress: float) -> Optional[Goal]:
        """
        Update goal progress.

        Args:
            goal_id: The goal to update.
            progress: New progress value 0-1.

        Returns:
            Updated Goal or None if not found.
        """
        progress = round(max(0.0, min(1.0, progress)), 4)
        now = datetime.now(timezone.utc).isoformat()

        with self._lock:
            goal = self._goals.get(goal_id)
            if not goal:
                return None

            goal.progress = progress
            goal.updated_at = now

            if progress >= 1.0:
                goal.status = "completed"
                goal.completed_at = now
                goal.progress = 1.0
                self._completed_goals[goal_id] = goal
                self._active_goals.pop(goal_id, None)
                self._goals_completed += 1
                logger.info("Goal completed: [%s] %s", goal_id, goal.title)

        return goal

    def detect_need(self, need_name: str, urgency: float = 0.5) -> None:
        """
        Register a detected need that may trigger goal formation.

        Args:
            need_name: Description of the need.
            urgency: How urgent this need is (0-1).
        """
        with self._lock:
            self._needs[need_name] = round(max(0.0, min(1.0, urgency)), 4)
        logger.debug("Need detected: %s (urgency=%.2f)", need_name, urgency)

    def get_active_goals(self, sorted_by_priority: bool = True) -> List[Dict]:
        """
        Get all active goals.

        Args:
            sorted_by_priority: Sort by priority descending.

        Returns:
            List of goal dicts.
        """
        with self._lock:
            goals = list(self._active_goals.values())
            if sorted_by_priority:
                goals.sort(key=lambda g: g.priority, reverse=True)
            return [g.model_dump() for g in goals]

    def get_goal(self, goal_id: str) -> Optional[Dict]:
        """Get a specific goal by ID."""
        with self._lock:
            goal = self._goals.get(goal_id)
            return goal.model_dump() if goal else None

    def get_goals_by_status(self, status: str, limit: int = 100) -> List[Dict]:
        """Get goals filtered by status."""
        with self._lock:
            goals = [g for g in self._goals.values() if g.status == status]
            goals.sort(key=lambda g: g.updated_at, reverse=True)
            return [g.model_dump() for g in goals[:limit]]

    def get_statistics(self) -> Dict[str, Any]:
        """Get goal formation statistics."""
        with self._lock:
            status_counts = defaultdict(int)
            for g in self._goals.values():
                status_counts[g.status] += 1
            avg_progress = 0.0
            if self._active_goals:
                avg_progress = sum(
                    g.progress for g in self._active_goals.values()
                ) / len(self._active_goals)
            return {
                "total_goals": len(self._goals),
                "active_goals": len(self._active_goals),
                "completed_goals": self._goals_completed,
                "status_counts": dict(status_counts),
                "avg_active_progress": round(avg_progress, 4),
                "detected_needs": len(self._needs),
                "goals_formed": self._goals_formed,
            }

    def run_cycle(self) -> List[Dict[str, Any]]:
        """
        Run one goal formation cycle:
        1. Decay stale goal priorities
        2. Re-evaluate blocked goals
  3. Auto-form goals from urgent needs

        Returns:
            List of actions taken.
        """
        actions = []
        self._cycle_count += 1

        with self._lock:
            # Decay priorities of stale active goals
            for gid, goal in list(self._active_goals.items()):
                if goal.progress < 0.1:
                    goal.priority = max(0.1, goal.priority * self.config.priority_decay)
                    goal.updated_at = datetime.now(timezone.utc).isoformat()

        # Re-evaluate blocked goals
        blocked = self.get_goals_by_status("blocked")
        for goal_dict in blocked:
            result = self.evaluate_goal(goal_dict["goal_id"])
            if result.get("decision") == "activate":
                actions.append({"action": "activated", "goal_id": goal_dict["goal_id"]})

        # Auto-form goals from urgent needs
        if self._cycle_count % self.config.need_detection_interval == 0:
            with self._lock:
                urgent_needs = {
                    k: v for k, v in self._needs.items()
                    if v > 0.7
                }
                for need_name, urgency in urgent_needs.items():
                    # Check if we already have an active goal for this need
                    already_covered = any(
                        need_name.lower() in g.title.lower()
                        for g in self._active_goals.values()
                    )
                    if not already_covered and len(self._active_goals) < self.config.max_active_goals:
                        goal = self.propose_goal(
                            title=f"Address need: {need_name}",
                            description=f"Auto-formed goal from detected need (urgency={urgency:.2f})",
                            priority=urgency,
                            source="autonomous",
                        )
                        self.evaluate_goal(goal.goal_id)
                        actions.append({"action": "formed", "goal_id": goal.goal_id, "need": need_name})

        # Trim total goals if exceeded
        with self._lock:
            if len(self._goals) > self.config.max_total_goals:
                # Remove oldest abandoned/completed
                removable = [
                    gid for gid, g in self._goals.items()
                    if g.status in ("abandoned", "completed")
                ]
                removable.sort(key=lambda gid: self._goals[gid].updated_at)
                to_remove = removable[:len(self._goals) - self.config.max_total_goals]
                for gid in to_remove:
                    del self._goals[gid]
                    self._completed_goals.pop(gid, None)
                if to_remove:
                    actions.append({"action": "trimmed", "count": len(to_remove)})

        return actions


from enum import Enum  # imported here to avoid circular issues with pydantic
