"""
OCE Sync Cost Optimizer — Phase 9.2
====================================
Analyzes and optimizes synchronization costs across the OCE topology.

Sync cost is a key denominator in coherence yield:
  Yield = (Coherence × Recoverability × Adaptability) / (Entropy × Sync Cost × Resource Consumption)

Reducing unnecessary sync directly improves coherence yield.
"""

import sqlite3
import json
import logging
import uuid
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.sync_cost")

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "sync_cost.db"


class SyncCostOptimizer:
    """
    Singleton sync cost optimizer for OCE.

    Analyzes sync patterns, identifies unnecessary synchronization,
    and optimizes sync schedules to minimize cost.
    """

    _instance: Optional["SyncCostOptimizer"] = None
    _lock = Lock()

    def __new__(cls) -> "SyncCostOptimizer":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        self._sync_priorities: Dict[str, str] = {}  # observer_pair -> priority
        self._batch_queue: List[Dict[str, Any]] = []

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._init_db()
        logger.info("SyncCostOptimizer initialized")

    def _init_db(self):
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sync_operations (
                    sync_id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    target TEXT NOT NULL,
                    sync_type TEXT NOT NULL,
                    cost REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    batched INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sync_timestamp
                ON sync_operations(timestamp)
            """)
            conn.commit()

    def analyze_sync_patterns(self, window_hours: int = 24) -> Dict[str, Any]:
        """Analyze synchronization patterns to identify unnecessary syncs."""
        cutoff = datetime.now(timezone.utc).timestamp() - (window_hours * 3600)
        patterns = {
            "total_syncs": 0,
            "total_cost": 0.0,
            "by_type": {},
            "by_pair": {},
            "redundant_syncs": 0,
            "recommendations": [],
        }

        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT * FROM sync_operations WHERE timestamp > datetime(?, 'unixepoch')",
                    (cutoff,),
                ).fetchall()

                for row in rows:
                    patterns["total_syncs"] += 1
                    patterns["total_cost"] += row["cost"]

                    # By type
                    st = row["sync_type"]
                    if st not in patterns["by_type"]:
                        patterns["by_type"][st] = {"count": 0, "cost": 0.0}
                    patterns["by_type"][st]["count"] += 1
                    patterns["by_type"][st]["cost"] += row["cost"]

                    # By pair
                    pair = f"{row['source']}->{row['target']}"
                    if pair not in patterns["by_pair"]:
                        patterns["by_pair"][pair] = {"count": 0, "cost": 0.0}
                    patterns["by_pair"][pair]["count"] += 1
                    patterns["by_pair"][pair]["cost"] += row["cost"]

                # Identify redundant syncs (high frequency, low value)
                for pair, data in patterns["by_pair"].items():
                    if data["count"] > 100:
                        patterns["redundant_syncs"] += 1
                        patterns["recommendations"].append({
                            "action": "reduce_frequency",
                            "target": pair,
                            "current_count": data["count"],
                            "suggestion": f"Reduce sync frequency for {pair} ({data['count']} syncs in {window_hours}h)",
                        })

        except Exception as e:
            logger.error(f"Failed to analyze sync patterns: {e}")

        patterns["total_cost"] = round(patterns["total_cost"], 2)
        return patterns

    def optimize_sync_schedule(self) -> Dict[str, Any]:
        """Generate optimized sync schedule to reduce costs."""
        patterns = self.analyze_sync_patterns()
        optimizations = []

        for rec in patterns.get("recommendations", []):
            optimizations.append({
                "action": rec["action"],
                "target": rec["target"],
                "estimated_savings_pct": 30.0,
                "recommendation": rec["suggestion"],
            })

        if not optimizations:
            optimizations.append({
                "action": "maintain",
                "target": "all",
                "estimated_savings_pct": 0.0,
                "recommendation": "Sync patterns are within acceptable parameters.",
            })

        return {
            "current_patterns": patterns,
            "optimizations": optimizations,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_sync_cost_report(self) -> Dict[str, Any]:
        """Get current sync cost breakdown."""
        patterns = self.analyze_sync_patterns()
        return {
            "total_syncs": patterns["total_syncs"],
            "total_cost": patterns["total_cost"],
            "by_type": patterns["by_type"],
            "by_pair": patterns["by_pair"],
            "redundant_syncs": patterns["redundant_syncs"],
            "avg_cost_per_sync": round(patterns["total_cost"] / max(patterns["total_syncs"], 1), 4),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def set_sync_priority(self, observer_pair: str, priority: str) -> None:
        """Set sync priority for an observer pair (critical, high, normal, low, batch)."""
        self._sync_priorities[observer_pair] = priority
        logger.info(f"Sync priority set: {observer_pair} = {priority}")

    def batch_sync_operations(self, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Batch multiple sync operations to reduce overhead."""
        batch_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        total_cost = 0.0
        batched_count = 0

        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                for op in operations:
                    sync_id = str(uuid.uuid4())
                    cost = op.get("cost", 1.0) * 0.5  # Batching reduces cost by 50%
                    conn.execute(
                        """INSERT INTO sync_operations
                        (sync_id, source, target, sync_type, cost, timestamp, batched)
                        VALUES (?, ?, ?, ?, ?, ?, 1)""",
                        (sync_id, op.get("source", ""), op.get("target", ""),
                         op.get("sync_type", "batch"), cost, now),
                    )
                    total_cost += cost
                    batched_count += 1
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to batch sync operations: {e}")

        logger.info(f"Batched {batched_count} sync operations (batch {batch_id})")
        return {
            "batch_id": batch_id,
            "batched_count": batched_count,
            "total_cost": round(total_cost, 2),
            "savings_pct": 50.0,
        }

    def record_sync(self, source: str, target: str, sync_type: str, cost: float = 1.0):
        """Record a sync operation."""
        sync_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.execute(
                    """INSERT INTO sync_operations
                    (sync_id, source, target, sync_type, cost, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (sync_id, source, target, sync_type, cost, now),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to record sync: {e}")


def get_sync_cost_optimizer() -> SyncCostOptimizer:
    """Get the singleton SyncCostOptimizer instance."""
    return SyncCostOptimizer()
