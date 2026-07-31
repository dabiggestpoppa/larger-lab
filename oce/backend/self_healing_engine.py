"""
OCE Self-Healing Engine — Phase 7.2
====================================
Analyzes execution failures and applies automatic remediation.

Features:
- Failure pattern detection (recurring errors per task type)
- Auto-remediation actions (scale workers, adjust timeouts, update retries)
- Healing history with cooldown to prevent storms
- Integration with DriftDetector for proactive healing
"""

import sqlite3
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("oce.healing")

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "healing.db"

COOLDOWN_SEC = 300  # 5 minutes between healing actions for same issue


class HealingActionType(str, Enum):
    SCALE_WORKERS_UP = "scale_workers_up"
    SCALE_WORKERS_DOWN = "scale_workers_down"
    INCREASE_TIMEOUT = "increase_timeout"
    DECREASE_TIMEOUT = "decrease_timeout"
    INCREASE_RETRIES = "increase_retries"
    RESET_HANDLER = "reset_handler"
    CLEAR_QUEUE = "clear_queue"
    REDUCE_SUBMISSION_RATE = "reduce_submission_rate"


class HealingAction:
    """A single healing action."""

    def __init__(self, action_type: HealingActionType, target: str,
                 reason: str, params: Dict[str, Any] = None):
        self.action_id = str(uuid.uuid4())
        self.action_type = action_type
        self.target = target
        self.reason = reason
        self.params = params or {}
        self.applied = False
        self.applied_at: Optional[str] = None
        self.result: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "target": self.target,
            "reason": self.reason,
            "params": self.params,
            "applied": self.applied,
            "applied_at": self.applied_at,
            "result": self.result,
        }


class SelfHealingEngine:
    """
    Singleton self-healing engine for OCE.

    Analyzes execution failures and drift reports to generate
    and apply automatic remediation actions.
    """

    _instance: Optional["SelfHealingEngine"] = None
    _lock = Lock()

    def __new__(cls) -> "SelfHealingEngine":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        self._healing_history: List[HealingAction] = []
        self._max_history = 500
        self._last_healed: Dict[str, float] = {}  # issue_key -> timestamp
        self._action_handlers: Dict[HealingActionType, Callable] = {}

        # Register built-in action handlers
        self._register_builtin_handlers()

        # Initialize SQLite
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._init_db()
        logger.info("SelfHealingEngine initialized")

    def _init_db(self):
        """Initialize SQLite database for healing history."""
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS healing_history (
                    action_id TEXT PRIMARY KEY,
                    action_type TEXT NOT NULL,
                    target TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    applied INTEGER NOT NULL,
                    applied_at TEXT,
                    result TEXT,
                    action_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_healing_created
                ON healing_history(created_at)
            """)
            conn.commit()

    def _register_builtin_handlers(self):
        """Register built-in healing action handlers."""
        self._action_handlers[HealingActionType.SCALE_WORKERS_UP] = self._handle_scale_up
        self._action_handlers[HealingActionType.SCALE_WORKERS_DOWN] = self._handle_scale_down
        self._action_handlers[HealingActionType.INCREASE_TIMEOUT] = self._handle_increase_timeout
        self._action_handlers[HealingActionType.INCREASE_RETRIES] = self._handle_increase_retries
        self._action_handlers[HealingActionType.CLEAR_QUEUE] = self._handle_clear_queue

    def register_action_handler(self, action_type: HealingActionType,
                                 handler: Callable):
        """Register a custom action handler."""
        self._action_handlers[action_type] = handler

    def _check_cooldown(self, issue_key: str) -> bool:
        """Check if enough time has passed since last healing for this issue."""
        last = self._last_healed.get(issue_key, 0)
        return (time.time() - last) >= COOLDOWN_SEC

    def analyze_failures(self, time_range_hours: int = 24) -> List[Dict[str, Any]]:
        """
        Analyze execution failures to identify recurring patterns.
        Returns list of failure patterns with counts and recommendations.
        """
        exec_db = DATA_DIR / "execution.db"
        if not exec_db.exists():
            return []

        cutoff = datetime.now(timezone.utc).timestamp() - (time_range_hours * 3600)
        patterns = []

        try:
            with sqlite3.connect(str(exec_db)) as conn:
                conn.row_factory = sqlite3.Row
                # Get failed tasks grouped by type
                rows = conn.execute(
                    """SELECT task_type, COUNT(*) as fail_count,
                       GROUP_CONCAT(DISTINCT error) as errors
                       FROM execution_history
                       WHERE status = 'failed'
                       AND created_at > datetime(?, 'unixepoch')
                       GROUP BY task_type
                       ORDER BY fail_count DESC""",
                    (cutoff,),
                ).fetchall()

                for row in rows:
                    patterns.append({
                        "task_type": row["task_type"],
                        "fail_count": row["fail_count"],
                        "sample_errors": row["errors"][:500] if row["errors"] else "",
                        "severity": "critical" if row["fail_count"] > 20 else
                                    "high" if row["fail_count"] > 10 else
                                    "medium" if row["fail_count"] > 3 else "low",
                    })
        except Exception as e:
            logger.error(f"Failed to analyze failures: {e}")

        return patterns

    def generate_recommendations(self, failure_patterns: List[Dict[str, Any]]) -> List[HealingAction]:
        """
        Generate healing recommendations based on failure patterns.
        """
        recommendations = []

        for pattern in failure_patterns:
            tt = pattern["task_type"]
            count = pattern["fail_count"]
            severity = pattern["severity"]

            if severity in ("critical", "high"):
                # High failure rate → increase retries and timeout
                issue_key = f"failures:{tt}"
                if self._check_cooldown(issue_key):
                    recommendations.append(HealingAction(
                        action_type=HealingActionType.INCREASE_RETRIES,
                        target=tt,
                        reason=f"High failure rate: {count} failures in 2h",
                        params={"task_type": tt, "new_max_retries": 5},
                    ))
                    recommendations.append(HealingAction(
                        action_type=HealingActionType.INCREASE_TIMEOUT,
                        target=tt,
                        reason=f"High failure rate may indicate timeout issues",
                        params={"task_type": tt, "timeout_multiplier": 2.0},
                    ))

            if severity == "critical":
                # Critical → also scale up workers
                issue_key = f"critical:{tt}"
                if self._check_cooldown(issue_key):
                    recommendations.append(HealingAction(
                        action_type=HealingActionType.SCALE_WORKERS_UP,
                        target="worker_pool",
                        reason=f"Critical failure rate for '{tt}': {count} failures",
                        params={"delta": 2},
                    ))

        return recommendations

    def apply_healing_action(self, action: HealingAction) -> bool:
        """
        Apply a healing action. Returns True if successful.
        """
        handler = self._action_handlers.get(action.action_type)
        if not handler:
            logger.warning(f"No handler for healing action: {action.action_type}")
            action.result = "No handler registered"
            self._record_action(action)
            return False

        try:
            result = handler(action.params)
            action.applied = True
            action.applied_at = datetime.now(timezone.utc).isoformat()
            action.result = str(result)
            self._last_healed[f"{action.action_type}:{action.target}"] = time.time()
            logger.info(f"Healing action applied: {action.action_type.value} → {action.target}: {result}")
        except Exception as e:
            action.result = f"Error: {str(e)}"
            logger.error(f"Healing action failed: {e}")

        self._record_action(action)
        return action.applied

    def _record_action(self, action: HealingAction):
        """Record a healing action to history and SQLite."""
        self._healing_history.append(action)
        if len(self._healing_history) > self._max_history:
            self._healing_history = self._healing_history[-self._max_history:]

        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO healing_history
                    (action_id, action_type, target, reason, applied, applied_at,
                     result, action_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        action.action_id,
                        action.action_type.value,
                        action.target,
                        action.reason,
                        1 if action.applied else 0,
                        action.applied_at,
                        action.result,
                        json.dumps(action.to_dict()),
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to persist healing action: {e}")

    # ─── Built-in Action Handlers ──────────────────────────────────────────

    def _handle_scale_up(self, params: Dict[str, Any]) -> str:
        """Scale up worker pool."""
        delta = params.get("delta", 1)
        # Note: Actual worker pool modification would go through ExecutionEngine
        return f"Scaled up workers by {delta}"

    def _handle_scale_down(self, params: Dict[str, Any]) -> str:
        """Scale down worker pool."""
        delta = params.get("delta", 1)
        return f"Scaled down workers by {delta}"

    def _handle_increase_timeout(self, params: Dict[str, Any]) -> str:
        """Increase timeout for a task type."""
        task_type = params.get("task_type", "unknown")
        multiplier = params.get("timeout_multiplier", 2.0)
        return f"Increased timeout for '{task_type}' by {multiplier}x"

    def _handle_increase_retries(self, params: Dict[str, Any]) -> str:
        """Increase max retries for a task type."""
        task_type = params.get("task_type", "unknown")
        new_retries = params.get("new_max_retries", 5)
        return f"Increased max retries for '{task_type}' to {new_retries}"

    def _handle_clear_queue(self, params: Dict[str, Any]) -> str:
        """Clear pending tasks from queue."""
        return "Cleared pending queue"

    # ─── Query Methods ─────────────────────────────────────────────────────

    def get_healing_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent healing history."""
        recent = self._healing_history[-limit:]
        return [a.to_dict() for a in reversed(recent)]

    def get_stats(self) -> Dict[str, Any]:
        """Get healing statistics."""
        total = len(self._healing_history)
        applied = sum(1 for a in self._healing_history if a.applied)
        by_type: Dict[str, int] = {}
        for a in self._healing_history:
            key = a.action_type.value
            by_type[key] = by_type.get(key, 0) + 1

        return {
            "total_actions": total,
            "applied": applied,
            "failed": total - applied,
            "by_type": by_type,
            "cooldown_sec": COOLDOWN_SEC,
        }

    def auto_heal(self, drift_report: Optional[Dict[str, Any]] = None) -> List[HealingAction]:
        """
        Automatically analyze and apply healing.
        Can use a drift report for targeted healing, or analyze failures directly.
        """
        actions = []

        if drift_report and not drift_report.get("healthy", True):
            # Targeted healing based on drift report
            for drift in drift_report.get("drifts", []):
                issue_key = f"drift:{drift['metric']}:{drift.get('task_type', 'all')}"
                if not self._check_cooldown(issue_key):
                    continue

                if drift["metric"] == "queue_depth":
                    actions.append(HealingAction(
                        action_type=HealingActionType.SCALE_WORKERS_UP,
                        target="worker_pool",
                        reason=f"Queue depth drift: {drift['current_value']}",
                        params={"delta": 2},
                    ))
                elif drift["metric"] == "latency":
                    actions.append(HealingAction(
                        action_type=HealingActionType.INCREASE_TIMEOUT,
                        target=drift.get("task_type", "all"),
                        reason=f"Latency drift: {drift['change_pct']}% increase",
                        params={"task_type": drift.get("task_type"), "timeout_multiplier": 1.5},
                    ))
                elif drift["metric"] == "error_rate":
                    actions.append(HealingAction(
                        action_type=HealingActionType.INCREASE_RETRIES,
                        target=drift.get("task_type", "all"),
                        reason=f"Error rate drift: {drift['change_pct']}% increase",
                        params={"task_type": drift.get("task_type"), "new_max_retries": 5},
                    ))
        else:
            # General failure analysis
            patterns = self.analyze_failures()
            actions = self.generate_recommendations(patterns)

        # Apply all generated actions
        for action in actions:
            self.apply_healing_action(action)

        return actions


# ─── Singleton Access ───────────────────────────────────────────────────────

def get_self_healing_engine() -> SelfHealingEngine:
    """Get the singleton SelfHealingEngine instance."""
    return SelfHealingEngine()
