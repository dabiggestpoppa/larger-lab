"""
OCE Economics Engine — Phase 9.1
=================================
Coherence economics as the governing system law.

Coherence Yield = (Coherence × Recoverability × Adaptability) / (Entropy × Sync Cost × Resource Consumption)

Manages:
- Entropy budgeting and allocation
- Coherence yield calculation and optimization
- Entropy debt tracking
- Sustainability forecasting
"""

import sqlite3
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.economics")

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "economics.db"

# ─── Default Budget Allocations ──────────────────────────────────────────────

DEFAULT_ENTROPY_BUDGET = {
    "total": 10000.0,
    "allocations": {
        "event_processing": 2000.0,
        "observer_runtime": 1500.0,
        "structural_memory": 1000.0,
        "execution_engine": 2000.0,
        "observability": 500.0,
        "governance": 500.0,
        "adaptive_evolution": 1000.0,
        "coevolution": 500.0,
        "reserve": 1000.0,
    }
}


class EconomicsEngine:
    """
    Singleton economics engine for OCE Entropy Economics.

    Manages entropy budgeting, coherence yield calculation,
    and sustainability forecasting.
    """

    _instance: Optional["EconomicsEngine"] = None
    _lock = Lock()

    def __new__(cls) -> "EconomicsEngine":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        self._budget = dict(DEFAULT_ENTROPY_BUDGET)
        self._consumption: Dict[str, float] = {k: 0.0 for k in self._budget["allocations"]}
        self._entropy_debt: float = 0.0
        self._coherence_score: float = 1.0
        self._recoverability_score: float = 1.0
        self._adaptability_score: float = 1.0
        self._sync_cost: float = 1.0
        self._resource_consumption: float = 1.0

        # Initialize SQLite
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._init_db()
        logger.info("EconomicsEngine initialized")

    def _init_db(self):
        """Initialize SQLite database for economics persistence."""
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS budget_history (
                    record_id TEXT PRIMARY KEY,
                    action TEXT NOT NULL,
                    task_type TEXT,
                    amount REAL,
                    reason TEXT,
                    created_at TEXT NOT NULL,
                    record_json TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS yield_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    coherence_yield REAL NOT NULL,
                    coherence REAL NOT NULL,
                    recoverability REAL NOT NULL,
                    adaptability REAL NOT NULL,
                    entropy REAL NOT NULL,
                    sync_cost REAL NOT NULL,
                    resource_consumption REAL NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def get_coherence_yield(self) -> Dict[str, Any]:
        """
        Calculate current coherence yield.
        Yield = (Coherence × Recoverability × Adaptability) / (Entropy × Sync Cost × Resource Consumption)
        """
        numerator = self._coherence_score * self._recoverability_score * self._adaptability_score
        denominator = max(self._entropy_debt, 0.01) * max(self._sync_cost, 0.01) * max(self._resource_consumption, 0.01)
        yield_value = numerator / denominator

        return {
            "coherence_yield": round(yield_value, 4),
            "coherence": round(self._coherence_score, 4),
            "recoverability": round(self._recoverability_score, 4),
            "adaptability": round(self._adaptability_score, 4),
            "entropy_debt": round(self._entropy_debt, 4),
            "sync_cost": round(self._sync_cost, 4),
            "resource_consumption": round(self._resource_consumption, 4),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def allocate_budget(self, task_type: str, amount: float,
                        reason: str = "") -> Dict[str, Any]:
        """Allocate entropy budget to a task type."""
        if task_type not in self._budget["allocations"]:
            self._budget["allocations"][task_type] = 0.0

        self._budget["allocations"][task_type] += amount
        self._log_budget_action("allocate", task_type, amount, reason)
        logger.info(f"Budget allocated: {task_type} += {amount}")
        return self.get_budget_status()

    def get_budget_status(self) -> Dict[str, Any]:
        """Get current budget allocation and consumption."""
        total_allocated = sum(self._budget["allocations"].values())
        total_consumed = sum(self._consumption.values())
        remaining = self._budget["total"] - total_consumed

        return {
            "total_budget": self._budget["total"],
            "total_allocated": total_allocated,
            "total_consumed": total_consumed,
            "remaining": remaining,
            "utilization_pct": round((total_consumed / max(self._budget["total"], 0.01)) * 100, 2),
            "allocations": dict(self._budget["allocations"]),
            "consumption": dict(self._consumption),
            "entropy_debt": self._entropy_debt,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def reallocate_budget(self, from_type: str, to_type: str,
                          amount: float, reason: str = "") -> Dict[str, Any]:
        """Reallocate entropy budget from one task type to another."""
        if from_type not in self._budget["allocations"]:
            raise ValueError(f"Unknown task type: {from_type}")
        if self._budget["allocations"][from_type] < amount:
            raise ValueError(f"Insufficient budget in {from_type}: has {self._budget['allocations'][from_type]}, requested {amount}")

        self._budget["allocations"][from_type] -= amount
        if to_type not in self._budget["allocations"]:
            self._budget["allocations"][to_type] = 0.0
        self._budget["allocations"][to_type] += amount

        self._log_budget_action("reallocate", f"{from_type}->{to_type}", amount, reason)
        logger.info(f"Budget reallocated: {amount} from {from_type} to {to_type}")
        return self.get_budget_status()

    def get_entropy_debt(self) -> Dict[str, Any]:
        """Get accumulated entropy debt."""
        return {
            "total_debt": round(self._entropy_debt, 4),
            "by_task_type": {k: round(v, 4) for k, v in self._consumption.items() if v > 0},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def record_consumption(self, task_type: str, amount: float):
        """Record entropy consumption for a task type."""
        if task_type not in self._consumption:
            self._consumption[task_type] = 0.0
        self._consumption[task_type] += amount

        # Track debt if over budget
        allocated = self._budget["allocations"].get(task_type, 0.0)
        if self._consumption[task_type] > allocated:
            self._entropy_debt += (self._consumption[task_type] - allocated)

    def update_scores(self, coherence: float = None, recoverability: float = None,
                      adaptability: float = None, sync_cost: float = None,
                      resource_consumption: float = None):
        """Update coherence economics scores."""
        if coherence is not None:
            self._coherence_score = max(0.0, min(1.0, coherence))
        if recoverability is not None:
            self._recoverability_score = max(0.0, min(1.0, recoverability))
        if adaptability is not None:
            self._adaptability_score = max(0.0, min(1.0, adaptability))
        if sync_cost is not None:
            self._sync_cost = max(0.01, sync_cost)
        if resource_consumption is not None:
            self._resource_consumption = max(0.01, resource_consumption)

    def forecast_sustainability(self, horizon_hours: int = 24) -> Dict[str, Any]:
        """
        Forecast long-term sustainability based on current consumption trends.
        """
        total_consumed = sum(self._consumption.values())
        remaining = self._budget["total"] - total_consumed

        # Simple linear projection
        hourly_consumption = total_consumed / max(1.0, 1.0)  # Per hour rate
        projected_consumption = hourly_consumption * horizon_hours
        projected_remaining = remaining - projected_consumption

        sustainable = projected_remaining > 0
        hours_until_depletion = remaining / max(hourly_consumption, 0.01) if hourly_consumption > 0 else float('inf')

        return {
            "horizon_hours": horizon_hours,
            "current_remaining": round(remaining, 2),
            "projected_remaining": round(projected_remaining, 2),
            "sustainable": sustainable,
            "hours_until_depletion": round(hours_until_depletion, 1),
            "recommendation": "reduce_consumption" if not sustainable else "maintain",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def optimize_yield(self) -> Dict[str, Any]:
        """
        Suggest changes to maximize coherence yield.
        """
        suggestions = []
        current_yield = self.get_coherence_yield()

        # Check entropy debt
        if self._entropy_debt > 100:
            suggestions.append({
                "action": "reduce_entropy_debt",
                "priority": "high",
                "detail": f"Entropy debt is {self._entropy_debt:.1f}. Reduce consumption or increase budget.",
            })

        # Check sync cost
        if self._sync_cost > 2.0:
            suggestions.append({
                "action": "reduce_sync_cost",
                "priority": "medium",
                "detail": f"Sync cost is {self._sync_cost:.2f}. Consider batching or reducing sync frequency.",
            })

        # Check resource consumption
        if self._resource_consumption > 2.0:
            suggestions.append({
                "action": "reduce_resource_consumption",
                "priority": "medium",
                "detail": f"Resource consumption is {self._resource_consumption:.2f}. Consider compression or pruning.",
            })

        # Check budget utilization
        status = self.get_budget_status()
        if status["utilization_pct"] > 90:
            suggestions.append({
                "action": "increase_budget_or_reduce_consumption",
                "priority": "high",
                "detail": f"Budget utilization is {status['utilization_pct']}%.",
            })

        if not suggestions:
            suggestions.append({
                "action": "maintain",
                "priority": "low",
                "detail": "System is operating within sustainable parameters.",
            })

        return {
            "current_yield": current_yield,
            "suggestions": suggestions,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _log_budget_action(self, action: str, task_type: str,
                           amount: float, reason: str):
        """Log a budget action to SQLite."""
        record_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.execute(
                    """INSERT INTO budget_history
                    (record_id, action, task_type, amount, reason, created_at, record_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (record_id, action, task_type, amount, reason, now,
                     json.dumps({"action": action, "task_type": task_type, "amount": amount, "reason": reason})),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to log budget action: {e}")

    def get_budget_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get budget action history."""
        results = []
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT * FROM budget_history ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                for row in rows:
                    results.append(dict(row))
        except Exception as e:
            logger.error(f"Failed to read budget history: {e}")
        return results


# ─── Singleton Access ───────────────────────────────────────────────────────

def get_economics_engine() -> EconomicsEngine:
    """Get the singleton EconomicsEngine instance."""
    return EconomicsEngine()
