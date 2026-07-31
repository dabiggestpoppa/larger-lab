"""
Topology Introspector
======================
Phase 6: Recursive self-modeling — the system observes its own topology.

Tracks:
- Patch connectivity graph
- Synchronization cost per edge
- Repair density per region
- Routing efficiency
- Entropy accumulation zones

This is NOT consciousness — it's operational topology awareness.
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict


class TopologySnapshot:
    """A snapshot of the system topology at a point in time."""

    def __init__(self):
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.patches: Dict[str, dict] = {}
        self.edges: Dict[str, float] = {}  # edge_id -> weight
        self.repair_counts: Dict[str, int] = {}
        self.sync_costs: Dict[str, float] = {}
        self.entropy_zones: List[dict] = []

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "patch_count": len(self.patches),
            "edge_count": len(self.edges),
            "avg_edge_weight": round(
                sum(self.edges.values()) / max(len(self.edges), 1), 3
            ),
            "total_repairs": sum(self.repair_counts.values()),
            "entropy_zones": len(self.entropy_zones),
        }


class TopologyIntrospector:
    """
    Observes and analyzes the system's own topology.

    Provides answers to:
    - Which regions increase coherence vs entropy?
    - Where are the repair hotspots?
    - What's the synchronization cost distribution?
    - Are there isolated or overloaded patches?
    """

    def __init__(self):
        self._snapshots: List[TopologySnapshot] = []
        self._patch_activity: Dict[str, List[float]] = defaultdict(list)
        self._edge_usage: Dict[str, int] = defaultdict(int)
        self._repair_log: List[dict] = []

    def record_patch_activity(self, patch_id: str, activity_level: float):
        """Record activity level for a patch (0.0 to 1.0)."""
        self._patch_activity[patch_id].append(activity_level)
        # Keep last 100 entries per patch
        if len(self._patch_activity[patch_id]) > 100:
            self._patch_activity[patch_id] = self._patch_activity[patch_id][-100:]

    def record_edge_usage(self, edge_id: str):
        """Record usage of an edge (communication between patches)."""
        self._edge_usage[edge_id] += 1

    def record_repair(self, region: str, severity: float, resolved: bool):
        """Record a repair event."""
        self._repair_log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "region": region,
            "severity": round(severity, 3),
            "resolved": resolved,
        })

    def take_snapshot(self) -> TopologySnapshot:
        """Take a snapshot of the current topology state."""
        snapshot = TopologySnapshot()

        # Patch activity levels
        for patch_id, activities in self._patch_activity.items():
            recent = activities[-10:] if len(activities) >= 10 else activities
            snapshot.patches[patch_id] = {
                "activity_level": round(sum(recent) / len(recent), 3) if recent else 0,
                "total_observations": len(activities),
            }

        # Edge usage distribution
        for edge_id, count in self._edge_usage.items():
            snapshot.edges[edge_id] = count

        # Repair density per region
        region_repairs = defaultdict(int)
        for repair in self._repair_log[-50:]:  # Last 50 repairs
            region_repairs[repair["region"]] += 1
        snapshot.repair_counts = dict(region_repairs)

        # Identify entropy zones (high repair, low activity)
        for patch_id, patch_data in snapshot.patches.items():
            repair_count = snapshot.repair_counts.get(patch_id, 0)
            if repair_count > 5 and patch_data["activity_level"] < 0.3:
                snapshot.entropy_zones.append({
                    "patch": patch_id,
                    "repair_count": repair_count,
                    "activity_level": patch_data["activity_level"],
                })

        self._snapshots.append(snapshot)
        # Keep last 50 snapshots
        if len(self._snapshots) > 50:
            self._snapshots = self._snapshots[-50:]

        return snapshot

    def get_coherence_report(self) -> dict:
        """Generate a coherence report: which regions help vs hurt."""
        if not self._snapshots:
            return {"status": "no_data"}

        latest = self._snapshots[-1]

        # Coherence = high activity, low repairs
        coherence_scores = {}
        for patch_id, patch_data in latest.patches.items():
            repairs = latest.repair_counts.get(patch_id, 0)
            activity = patch_data["activity_level"]
            if activity > 0:
                coherence_scores[patch_id] = round(activity / (1 + repairs), 3)
            else:
                coherence_scores[patch_id] = 0.0

        # Sort by coherence
        sorted_patches = sorted(coherence_scores.items(), key=lambda x: x[1], reverse=True)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "top_coherent": sorted_patches[:5],
            "bottom_coherent": sorted_patches[-5:] if len(sorted_patches) >= 5 else [],
            "entropy_zones": latest.entropy_zones,
            "total_repairs_last_50": sum(latest.repair_counts.values()),
        }

    def get_optimization_candidates(self) -> List[dict]:
        """Identify topology regions that could be optimized."""
        if not self._snapshots:
            return []

        latest = self._snapshots[-1]
        candidates = []

        # High repair density regions
        for region, count in latest.repair_counts.items():
            if count > 3:
                candidates.append({
                    "type": "high_repair_density",
                    "region": region,
                    "repair_count": count,
                    "recommendation": "Consider splitting or reinforcing this region",
                })

        # Isolated patches (low activity, low repairs)
        for patch_id, patch_data in latest.patches.items():
            if patch_data["activity_level"] < 0.1 and latest.repair_counts.get(patch_id, 0) < 2:
                candidates.append({
                    "type": "isolated_patch",
                    "patch": patch_id,
                    "activity": patch_data["activity_level"],
                    "recommendation": "Consider merging or removing this patch",
                })

        return candidates

    def get_stats(self) -> dict:
        return {
            "snapshots_taken": len(self._snapshots),
            "tracked_patches": len(self._patch_activity),
            "tracked_edges": len(self._edge_usage),
            "total_repairs_logged": len(self._repair_log),
            "latest_snapshot": self._snapshots[-1].to_dict() if self._snapshots else None,
        }


if __name__ == "__main__":
    intro = TopologyIntrospector()

    # Simulate activity
    import random
    random.seed(42)

    patches = ["planner", "execution", "memory", "repair", "observer_1", "observer_2"]
    for i in range(50):
        for patch in patches:
            activity = random.uniform(0.3, 0.9) if patch != "observer_2" else random.uniform(0.0, 0.1)
            intro.record_patch_activity(patch, activity)

        # Record edge usage
        intro.record_edge_usage("planner-execution")
        intro.record_edge_usage("execution-memory")
        intro.record_edge_usage("memory-repair")
        if i % 5 == 0:
            intro.record_edge_usage("repair-planner")

        # Record repairs
        if i % 3 == 0:
            intro.record_repair("planner", random.uniform(0.1, 0.5), resolved=True)
        if i % 7 == 0:
            intro.record_repair("execution", random.uniform(0.2, 0.8), resolved=i % 2 == 0)

        # Take snapshot every 10 cycles
        if i % 10 == 0:
            intro.take_snapshot()

    print("Coherence report:")
    print(json.dumps(intro.get_coherence_report(), indent=2))

    print(f"\nOptimization candidates:")
    for c in intro.get_optimization_candidates():
        print(f"  {c}")

    print(f"\nStats: {json.dumps(intro.get_stats(), indent=2)}")
