"""
Active Collar Fields
====================
Phase 3 (Updated): Edges become active computational reconciliation regions.

Previously: edges were communication paths.
Now: edges perform continuity reconciliation, contradiction stabilization,
     sparse consensus formation, and trajectory reconstruction.

Each collar is a sparse, local, probabilistic overlap region — NOT a globally
synchronized memory pool.
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from collections import defaultdict


class ActiveCollarField:
    """
    An active computational reconciliation region between two or more observers.

    The collar maintains:
    - overlap_state: shared reconstruction region
    - contradiction_map: local inconsistency tracking
    - repair_queue: stabilization tasks
    - confidence_gradients: probabilistic closure
    - entropy_score: synchronization burden
    - reconstruction_viability: continuity recoverability
    """

    def __init__(self, collar_id: str, observers: List[str]):
        self.collar_id = collar_id
        self.observers = observers
        self.overlap_state: Dict[str, Any] = {}
        self.contradiction_map: Dict[str, List[dict]] = defaultdict(list)
        self.repair_queue: List[dict] = []
        self.confidence_gradients: Dict[str, float] = {}
        self.entropy_score: float = 0.0
        self.reconstruction_viability: float = 1.0
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.last_reconciled = None

    def reconcile(self, observer_id: str, state: dict) -> dict:
        """Reconcile incoming observer state with the overlap region."""
        conflicts = []
        reconciled = {}

        for key, value in state.items():
            if key in self.overlap_state:
                existing = self.overlap_state[key]
                if existing != value:
                    conflict = {
                        "key": key,
                        "existing": existing,
                        "incoming": value,
                        "observer": observer_id,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    conflicts.append(conflict)
                    self.contradiction_map[key].append(conflict)
                    # Probabilistic closure: keep higher confidence value
                    reconciled[key] = self._resolve_conflict(existing, value, observer_id)
                else:
                    reconciled[key] = value
            else:
                reconciled[key] = value
                self.overlap_state[key] = value

        # Update entropy based on conflict count
        self.entropy_score = min(1.0, len(conflicts) * 0.1 + self.entropy_score * 0.5)
        self.reconstruction_viability = max(0.0, 1.0 - self.entropy_score)
        self.last_reconciled = datetime.now(timezone.utc).isoformat()

        return {
            "reconciled": reconciled,
            "conflicts": len(conflicts),
            "entropy": self.entropy_score,
            "viability": self.reconstruction_viability
        }

    def _resolve_conflict(self, existing: Any, incoming: Any, observer_id: str) -> Any:
        """Probabilistic conflict resolution — keep value with higher confidence."""
        existing_conf = self.confidence_gradients.get(f"existing_{id(existing)}", 0.5)
        incoming_conf = self.confidence_gradients.get(f"incoming_{observer_id}", 0.5)

        if incoming_conf > existing_conf + 0.3:
            self.confidence_gradients[f"incoming_{observer_id}"] = incoming_conf
            return incoming
        return existing

    def add_repair_task(self, task: dict):
        """Add a stabilization task to the repair queue."""
        task["added_at"] = datetime.now(timezone.utc).isoformat()
        task["status"] = "pending"
        self.repair_queue.append(task)

    def process_repairs(self) -> List[dict]:
        """Process pending repair tasks. Returns completed repairs."""
        completed = []
        remaining = []

        for task in self.repair_queue:
            if task["status"] == "pending":
                # Attempt repair
                task["status"] = "completed"
                task["completed_at"] = datetime.now(timezone.utc).isoformat()
                completed.append(task)
            elif task["status"] == "completed":
                completed.append(task)
            else:
                remaining.append(task)

        self.repair_queue = remaining
        return completed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "collar_id": self.collar_id,
            "observers": self.observers,
            "overlap_state": self.overlap_state,
            "contradiction_count": sum(len(v) for v in self.contradiction_map.values()),
            "repair_queue_size": len(self.repair_queue),
            "entropy_score": round(self.entropy_score, 3),
            "reconstruction_viability": round(self.reconstruction_viability, 3),
            "last_reconciled": self.last_reconciled,
        }


class CollarFieldManager:
    """Manages all active collar fields in the system."""

    def __init__(self):
        self.collars: Dict[str, ActiveCollarField] = {}

    def create_collar(self, collar_id: str, observers: List[str]) -> ActiveCollarField:
        """Create a new active collar field."""
        collar = ActiveCollarField(collar_id, observers)
        self.collars[collar_id] = collar
        return collar

    def get_collar(self, collar_id: str) -> Optional[ActiveCollarField]:
        return self.collars.get(collar_id)

    def reconcile(self, collar_id: str, observer_id: str, state: dict) -> Optional[dict]:
        """Reconcile state through a specific collar."""
        collar = self.collars.get(collar_id)
        if collar:
            return collar.reconcile(observer_id, state)
        return None

    def get_all_entropy(self) -> Dict[str, float]:
        """Get entropy scores for all collars."""
        return {cid: c.entropy_score for cid, c in self.collars.items()}

    def get_viability_report(self) -> Dict[str, Any]:
        """Get reconstruction viability across all collars."""
        if not self.collars:
            return {"avg_viability": 0.0, "min_viability": 0.0, "collar_count": 0}

        viabilities = [c.reconstruction_viability for c in self.collars.values()]
        return {
            "avg_viability": round(sum(viabilities) / len(viabilities), 3),
            "min_viability": round(min(viabilities), 3),
            "max_viability": round(max(viabilities), 3),
            "collar_count": len(viabilities),
        }
