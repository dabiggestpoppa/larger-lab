"""
O2-B9: ObserverSpecialization
===============================
Allow observers to specialize based on task history.

Tracks observer performance and adjusts routing weights.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
SPECIALIZATION_FILE = REPO_ROOT / "data" / "consensus" / "specializations.json"


class ObserverSpecialization:
    """
    Tracks and applies observer specialization.

    Observers become better at tasks they handle frequently.
    Routing weights are adjusted based on historical performance.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._specializations: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        try:
            if SPECIALIZATION_FILE.exists():
                data = json.loads(SPECIALIZATION_FILE.read_text(encoding="utf-8"))
                self._specializations = data.get("observers", {})
        except Exception:
            self._specializations = {}

    def _save(self) -> None:
        try:
            SPECIALIZATION_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "observers": self._specializations,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            SPECIALIZATION_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def record_outcome(
        self,
        observer_id: str,
        task_type: str,
        success: bool,
        duration_ms: float = 0.0,
    ) -> None:
        """Record an outcome for an observer."""
        with self._lock:
            if observer_id not in self._specializations:
                self._specializations[observer_id] = {
                    "total_tasks": 0,
                    "success_count": 0,
                    "task_types": {},
                    "avg_duration_ms": 0.0,
                }

            spec = self._specializations[observer_id]
            spec["total_tasks"] += 1
            if success:
                spec["success_count"] += 1

            if task_type not in spec["task_types"]:
                spec["task_types"][task_type] = {"count": 0, "success": 0}
            spec["task_types"][task_type]["count"] += 1
            if success:
                spec["task_types"][task_type]["success"] += 1

            # Update running average duration
            total = spec["total_tasks"]
            spec["avg_duration_ms"] = (
                (spec["avg_duration_ms"] * (total - 1) + duration_ms) / total
            )

            self._save()

    def get_weight(self, observer_id: str, task_type: str) -> float:
        """
        Get routing weight for an observer on a task type.

        Higher weight = more likely to be selected.
        """
        with self._lock:
            spec = self._specializations.get(observer_id)
            if not spec:
                return 1.0  # Default weight

            task_info = spec.get("task_types", {}).get(task_type)
            if not task_info or task_info["count"] < 3:
                return 1.0  # Not enough data

            success_rate = task_info["success"] / task_info["count"]
            experience_bonus = min(0.5, task_info["count"] * 0.05)

            return round(1.0 + success_rate + experience_bonus, 2)

    def get_specializations(self) -> dict[str, Any]:
        """Get all specializations."""
        with self._lock:
            return dict(self._specializations)
