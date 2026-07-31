"""
Topology Observer
==================
Phase 6: Recursive self-modeling — the system observes its own topology.

Tracks:
- Internal topology structure (coupling graph, sync density, repair hotspots)
- Synchronization cost analysis (which connections are expensive)
- Repair efficiency metrics (which repairs stabilize vs. propagate entropy)
- Adaptive restructuring candidates (which topology changes would help)
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from collections import defaultdict


class TopologySnapshot:
    """A snapshot of the system's topology at a point in time."""

    def __init__(self, patches: List[str], edges: Dict[str, float],
                 sync_costs: Dict[str, float], repair_counts: Dict[str, int]):
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.patch_count = len(patches)
        self.edge_count = len(edges)
        self.avg_coupling = round(sum(edges.values()) / max(len(edges), 1), 3)
        self.total_sync_cost = round(sum(sync_costs.values()), 3)
        self.total_repairs = sum(repair_counts.values())
        self.hotspots = sorted(repair_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "patch_count": self.patch_count,
            "edge_count": self.edge_count,
            "avg_coupling": self.avg_coupling,
            "total_sync_cost": self.total_sync_cost,
            "total_repairs": self.total_repairs,
            "hotspots": self.hotspots,
        }


class TopologyObserver:
    """
    Observes and analyzes the system's own topology.
    Enables recursive self-modeling without centralization.
    """

    def __init__(self):
        self._snapshots: List[TopologySnapshot] = []
        self._sync_costs: Dict[str, float] = defaultdict(float)
        self._repair_counts: Dict[str, int] = defaultdict(int)
        self._coupling_edges: Dict[str, float] = {}
        self._patches: List[str] = []

    def register_patch(self, patch_id: str):
        """Register a patch in the topology."""
        if patch_id not in self._patches:
            self._patches.append(patch_id)

    def record_edge(self, patch_a: str, patch_b: str, weight: float):
        """Record a coupling edge between patches."""
        key = f"{min(patch_a, patch_b)}-{max(patch_a, patch_b)}"
        self._coupling_edges[key] = weight
        self.register_patch(patch_a)
        self.register_patch(patch_b)

    def record_sync(self, patch_a: str, patch_b: str, cost: float):
        """Record a synchronization event and its cost."""
        key = f"{min(patch_a, patch_b)}-{max(patch_a, patch_b)}"
        self._sync_costs[key] += cost

    def record_repair(self, patch_a: str, patch_b: str):
        """Record a repair event between patches."""
        key = f"{min(patch_a, patch_b)}-{max(patch_a, patch_b)}"
        self._repair_counts[key] += 1

    def take_snapshot(self) -> TopologySnapshot:
        """Take a snapshot of the current topology."""
        snapshot = TopologySnapshot(
            patches=list(self._patches),
            edges=dict(self._coupling_edges),
            sync_costs=dict(self._sync_costs),
            repair_counts=dict(self._repair_counts),
        )
        self._snapshots.append(snapshot)
        return snapshot

    def get_topology_map(self) -> dict:
        """Get the current topology as a structured map."""
        return {
            "patches": self._patches,
            "edges": self._coupling_edges,
            "sync_costs": dict(self._sync_costs),
            "repair_hotspots": dict(self._repair_counts),
            "snapshot_count": len(self._snapshots),
        }

    def analyze_efficiency(self) -> dict:
        """Analyze synchronization efficiency."""
        if not self._sync_costs:
            return {"status": "no_data"}

        costs = list(self._sync_costs.values())
        repairs = list(self._repair_counts.values())

        return {
            "total_sync_cost": round(sum(costs), 3),
            "avg_sync_cost": round(sum(costs) / len(costs), 3),
            "max_sync_cost_edge": max(self._sync_costs.items(), key=lambda x: x[1]) if self._sync_costs else None,
            "total_repairs": sum(repairs),
            "avg_repairs_per_edge": round(sum(repairs) / max(len(repairs), 1), 2),
            "efficiency_ratio": round(
                sum(self._coupling_edges.values()) / max(sum(costs), 0.001), 3
            ),
        }

    def suggest_restructuring(self) -> List[dict]:
        """
        Suggest topology changes that would improve efficiency.
        Returns candidates ranked by potential improvement.
        """
        suggestions = []

        # High-cost, low-weight edges are candidates for weakening
        for edge_key, cost in self._sync_costs.items():
            weight = self._coupling_edges.get(edge_key, 0.5)
            if cost > 1.0 and weight < 0.4:
                suggestions.append({
                    "type": "weaken_edge",
                    "edge": edge_key,
                    "reason": f"High sync cost ({cost:.2f}) with low coupling ({weight:.2f})",
                    "potential_savings": round(cost * 0.5, 2),
                })

        # High-repair edges are candidates for strengthening or isolation
        for edge_key, count in self._repair_counts.items():
            if count > 5:
                suggestions.append({
                    "type": "strengthen_or_isolate",
                    "edge": edge_key,
                    "reason": f"High repair count ({count}) indicates instability",
                    "potential_improvement": "reduce repair propagation",
                })

        suggestions.sort(key=lambda s: s.get("potential_savings", 0), reverse=True)
        return suggestions

    def get_stats(self) -> dict:
        return {
            "patches": len(self._patches),
            "edges": len(self._coupling_edges),
            "snapshots": len(self._snapshots),
            "total_sync_events": sum(1 for _ in self._sync_costs),
            "total_repairs": sum(self._repair_counts.values()),
        }


if __name__ == "__main__":
    observer = TopologyObserver()

    # Simulate topology activity
    observer.record_edge("planner", "execution", 0.8)
    observer.record_edge("execution", "memory", 0.6)
    observer.record_edge("memory", "repair", 0.5)
    observer.record_edge("repair", "planner", 0.7)

    # Simulate sync costs
    for i in range(20):
        observer.record_sync("planner", "execution", 0.5)
        observer.record_sync("execution", "memory", 0.3)
        if i % 5 == 0:
            observer.record_sync("memory", "repair", 1.2)  # Expensive

    # Simulate repairs
    for i in range(10):
        observer.record_repair("planner", "execution")
    for i in range(3):
        observer.record_repair("memory", "repair")

    snapshot = observer.take_snapshot()
    print(f"Snapshot: {json.dumps(snapshot.to_dict(), indent=2)}")

    print(f"\nEfficiency: {json.dumps(observer.analyze_efficiency(), indent=2)}")

    print(f"\nSuggestions:")
    for s in observer.suggest_restructuring():
        print(f"  {s}")

    print(f"\nStats: {json.dumps(observer.get_stats(), indent=2)}")
