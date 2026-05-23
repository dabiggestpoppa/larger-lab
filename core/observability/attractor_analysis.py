"""
Phase 11.2-3B.6 — Attractor + Field Maps
==========================================
Detects recurring stable operational states, repair convergence zones,
synchronization basins, and topology equilibrium regions.

This directly tests: "whether SRRA develops emergent operational geometry"

Metrics:
    stability_score, return_probability, repair_density,
    observer_coherence, routing_consistency, field_resonance

Outputs:
    attractor_regions.json
    field_resonance_map.json
    continuity_basins.graphml
"""

from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]  # larger-lab/
EXPORTS_DIR = REPO_ROOT / "experiments" / "exports" / "attractors"


@dataclass
class AttractorRegion:
    """A stable operational state that the system tends to converge toward."""
    region_id: str
    label: str
    stability_score: float = 0.0       # 0.0-1.0, how stable this state is
    return_probability: float = 0.0    # how often system returns here
    repair_density: float = 0.0        # repairs per unit time in this state
    observer_coherence: float = 0.0    # how synchronized observers are
    routing_consistency: float = 0.0   # how stable routing is
    field_resonance: float = 0.0       # composite resonance score
    visit_count: int = 0
    avg_duration_seconds: float = 0.0
    observer_signature: dict[str, str] = field(default_factory=dict)  # observer_id -> state
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FieldResonanceMap:
    """Map of field resonance across operational zones."""
    timestamp: str
    zones: dict[str, dict] = field(default_factory=dict)  # zone_name -> resonance data
    global_resonance: float = 0.0
    entropy_gradient: dict[str, float] = field(default_factory=dict)


class AttractorAnalyzer:
    """
    Analyzes temporal graph and event data to detect attractor regions
    and map field resonance.
    """

    def __init__(self):
        self._attractors: list[AttractorRegion] = []
        EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    def analyze_temporal_graph(self, temporal_summary: dict,
                               node_activity: dict[str, dict]) -> list[AttractorRegion]:
        """
        Analyze temporal graph data to identify attractor regions.

        An attractor is a recurring pattern of:
        - Similar observer states
        - Low entropy delta
        - Stable routing
        - High observer coherence
        """
        attractors = []

        # Identify high-activity nodes (potential attractor centers)
        sorted_nodes = sorted(
            node_activity.items(),
            key=lambda x: x[1].get("total_interactions", 0),
            reverse=True,
        )

        for i, (node_id, activity) in enumerate(sorted_nodes[:10]):
            total = activity.get("total_interactions", 0)
            if total == 0:
                continue

            # Compute stability metrics
            repair_ratio = activity.get("repair_triggers", 0) / total if total > 0 else 0
            entropy_trend = activity.get("total_entropy_delta", 0)

            # Stability: low repair ratio + low entropy = stable
            stability = max(0.0, 1.0 - repair_ratio - abs(entropy_trend) * 0.1)
            stability = min(1.0, stability)

            # Routing consistency: inverse of entropy trend
            routing_consistency = max(0.0, 1.0 - abs(entropy_trend) * 0.05)

            # Observer coherence: based on interaction balance
            as_source = activity.get("as_source", 0)
            as_target = activity.get("as_target", 0)
            if as_source + as_target > 0:
                balance = 1.0 - abs(as_source - as_target) / (as_source + as_target)
            else:
                balance = 0.0

            # Field resonance: composite
            field_resonance = round(
                (stability * 0.3 + routing_consistency * 0.3 +
                 balance * 0.2 + (1.0 - repair_ratio) * 0.2),
                4
            )

            attractor = AttractorRegion(
                region_id=f"attractor_{i:03d}",
                label=f"zone_{node_id}",
                stability_score=round(stability, 4),
                return_probability=round(min(1.0, total / 100), 4),
                repair_density=round(repair_ratio, 4),
                observer_coherence=round(balance, 4),
                routing_consistency=round(routing_consistency, 4),
                field_resonance=field_resonance,
                visit_count=total,
                avg_duration_seconds=round(activity.get("avg_latency_ms", 0) * total / 1000, 2),
                observer_signature={node_id: "active"},
            )
            attractors.append(attractor)

        self._attractors = attractors
        return attractors

    def compute_field_resonance(self, observer_states: dict[str, dict],
                                entropy_profile: dict) -> FieldResonanceMap:
        """
        Compute field resonance map across operational zones.

        Field resonance = how much the field is "in tune" —
        low entropy, high sync, stable routing = high resonance.
        """
        zones: dict[str, dict] = {}

        # Group observers by zone
        for oid, state in observer_states.items():
            zone = state.get("field_zone", "default")
            if zone not in zones:
                zones[zone] = {
                    "observers": [], "total_entropy": 0.0,
                    "total_tasks": 0, "total_errors": 0,
                }
            zones[zone]["observers"].append(oid)
            zones[zone]["total_entropy"] += state.get("entropy_score", 0)
            zones[zone]["total_tasks"] += state.get("tasks_completed", 0)
            zones[zone]["total_errors"] += state.get("errors", 0)

        # Compute resonance per zone
        total_observers = len(observer_states) or 1
        global_resonance = 0.0
        entropy_gradient: dict[str, float] = {}

        for zone_name, zone_data in zones.items():
            n_obs = len(zone_data["observers"]) or 1
            avg_entropy = zone_data["total_entropy"] / n_obs
            error_rate = zone_data["total_errors"] / max(1, zone_data["total_tasks"])

            # Resonance: low entropy + low error = high resonance
            resonance = max(0.0, 1.0 - avg_entropy - error_rate)
            resonance = min(1.0, resonance)

            zone_data["resonance"] = round(resonance, 4)
            zone_data["avg_entropy"] = round(avg_entropy, 4)
            zone_data["error_rate"] = round(error_rate, 4)
            zone_data["observer_count"] = n_obs

            entropy_gradient[zone_name] = round(avg_entropy, 4)
            global_resonance += resonance * (n_obs / total_observers)

        return FieldResonanceMap(
            timestamp=datetime.now(timezone.utc).isoformat(),
            zones=zones,
            global_resonance=round(global_resonance, 4),
            entropy_gradient=entropy_gradient,
        )

    def detect_continuity_basins(self, continuity_timeseries: list[dict]) -> list[dict]:
        """
        Detect basins of attraction from continuity timeseries.

        A basin is a period where continuity_score stays high (>0.8)
        for an extended duration.
        """
        basins = []
        current_basin = None

        for point in continuity_timeseries:
            score = point.get("continuity_score", 1.0)

            if score > 0.8:
                if current_basin is None:
                    current_basin = {
                        "start": point["timestamp"],
                        "end": point["timestamp"],
                        "min_score": score,
                        "max_score": score,
                        "points": 1,
                    }
                else:
                    current_basin["end"] = point["timestamp"]
                    current_basin["min_score"] = min(current_basin["min_score"], score)
                    current_basin["max_score"] = max(current_basin["max_score"], score)
                    current_basin["points"] += 1
            else:
                if current_basin is not None:
                    current_basin["stability"] = round(
                        current_basin["min_score"] / current_basin["max_score"]
                        if current_basin["max_score"] > 0 else 0, 4
                    )
                    basins.append(current_basin)
                    current_basin = None

        # Close last basin
        if current_basin is not None:
            current_basin["stability"] = round(
                current_basin["min_score"] / current_basin["max_score"]
                if current_basin["max_score"] > 0 else 0, 4
            )
            basins.append(current_basin)

        return basins

    def export(self, label: str = "attractor") -> dict[str, Path]:
        """Export all attractor analysis results."""
        results = {}

        # Attractor regions
        attractor_data = {
            "version": "0.1.0",
            "phase": "11.2-3B.6",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_attractors": len(self._attractors),
            "attractors": [asdict(a) for a in self._attractors],
        }
        path = EXPORTS_DIR / f"{label}_regions.json"
        with open(path, "w") as f:
            json.dump(attractor_data, f, indent=2, default=str)
        results["regions"] = path

        return results

    def summary(self) -> dict:
        """Quick summary of attractor analysis."""
        if not self._attractors:
            return {"status": "no_attractors_detected"}

        return {
            "total_attractors": len(self._attractors),
            "avg_stability": round(
                sum(a.stability_score for a in self._attractors) / len(self._attractors), 4
            ),
            "avg_resonance": round(
                sum(a.field_resonance for a in self._attractors) / len(self._attractors), 4
            ),
            "most_stable": max(self._attractors, key=lambda a: a.stability_score).label
                if self._attractors else None,
            "highest_resonance": max(self._attractors, key=lambda a: a.field_resonance).label
                if self._attractors else None,
        }
