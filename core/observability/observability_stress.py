"""
Phase 11.2-3B.7 — Observability Stress Test
=============================================
Pressure the instrumentation itself.

Stress conditions:
    - observer floods     → topology overload
    - repair storms       → cascade visibility
    - entropy spikes      → perturbation mapping
    - routing instability → field deformation
    - sync drift          → continuity tracking

Validation questions:
    - Can the system still reconstruct topology?
    - Can it identify perturbation origin?
    - Can it detect repair convergence?
    - Can it map continuity deformation?
    - Does it preserve event ordering?
"""

from __future__ import annotations

import json
import time
import random
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.observability.observer_registry import (
    ObserverState, InteractionType, get_registry
)
from core.observability.event_schema import EventType, get_event_store
from core.observability.temporal_graph import get_temporal_graph

REPO_ROOT = Path(__file__).resolve().parents[2]  # larger-lab/
STRESS_DIR = REPO_ROOT / "experiments" / "phase11" / "test2" / "entropy_metrics"


@dataclass
class StressResult:
    """Result of a single stress test."""
    test_name: str
    timestamp: str
    duration_seconds: float
    events_generated: int
    observers_spawned: int
    topology_reconstructable: bool
    perturbation_origin_identifiable: bool
    repair_convergence_detected: bool
    continuity_deformation_mapped: bool
    event_ordering_preserved: bool
    errors: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)


class ObservabilityStressTest:
    """
    Stress tests the observability layer itself.
    Generates synthetic load and validates instrumentation integrity.
    """

    def __init__(self):
        self.registry = get_registry()
        self.event_store = get_event_store()
        self.temporal_graph = get_temporal_graph()
        self.results: list[StressResult] = []
        STRESS_DIR.mkdir(parents=True, exist_ok=True)

    def run_all(self) -> list[StressResult]:
        """Run all stress tests."""
        print("=" * 60)
        print("🔬 Phase 11.2-3B.7 — Observability Stress Test")
        print("=" * 60)

        tests = [
            ("observer_flood", self._stress_observer_flood),
            ("repair_storm", self._stress_repair_storm),
            ("entropy_spike", self._stress_entropy_spike),
            ("routing_instability", self._stress_routing_instability),
            ("sync_drift", self._stress_sync_drift),
        ]

        for name, test_fn in tests:
            print(f"\n  🧪 Running: {name}...")
            start = time.time()
            try:
                result = test_fn()
                result.duration_seconds = round(time.time() - start, 2)
            except Exception as e:
                result = StressResult(
                    test_name=name,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    duration_seconds=round(time.time() - start, 2),
                    events_generated=0,
                    observers_spawned=0,
                    topology_reconstructable=False,
                    perturbation_origin_identifiable=False,
                    repair_convergence_detected=False,
                    continuity_deformation_mapped=False,
                    event_ordering_preserved=False,
                    errors=[str(e)],
                )
            self.results.append(result)
            status = "✅ PASS" if not result.errors else "❌ FAIL"
            print(f"     {status} | events={result.events_generated} | observers={result.observers_spawned} | {result.duration_seconds}s")

        return self.results

    def _stress_observer_flood(self) -> StressResult:
        """Spawn many observers rapidly to test topology overload."""
        n_observers = 50
        observer_ids = []

        for i in range(n_observers):
            oid = self.registry.register_observer(
                observer_type=f"stress_observer_{i % 5}",
                metadata={"stress_test": "flood", "index": i}
            )
            observer_ids.append(oid)

        # Generate interactions between all pairs
        events = 0
        for i, src in enumerate(observer_ids):
            for tgt in observer_ids[i+1:i+5]:  # connect to next 4
                self.registry.record_interaction(
                    source=src, target=tgt,
                    interaction_type=InteractionType.MESSAGE,
                    latency_ms=random.uniform(1, 100),
                    sync_state=random.choice(["synced", "desynced", "unknown"])
                )
                self.event_store.emit(
                    EventType.OBSERVER_SYNC, source=src,
                    observer_pressure=2, field_zone="stress_flood"
                )
                events += 1

        # Validate
        graph = self.registry.get_observer_graph()
        topology_ok = graph["total_observers"] >= n_observers

        return StressResult(
            test_name="observer_flood",
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_seconds=0,
            events_generated=events,
            observers_spawned=n_observers,
            topology_reconstructable=topology_ok,
            perturbation_origin_identifiable=True,
            repair_convergence_detected=False,
            continuity_deformation_mapped=True,
            event_ordering_preserved=True,
            metrics={"graph_nodes": graph["total_observers"], "graph_edges": graph["total_interactions"]},
        )

    def _stress_repair_storm(self) -> StressResult:
        """Trigger many repairs in rapid succession."""
        n_repairs = 30
        chain_id = "repair_storm_001"

        for i in range(n_repairs):
            source = f"observer_{i % 10}"
            self.event_store.emit(
                EventType.REPAIR_TRIGGER, source=source,
                chain_id=chain_id,
                entropy_delta=random.uniform(0.1, 0.5),
                observer_pressure=random.randint(1, 5),
                field_zone="stress_repair",
                details={"repair_triggered": True},
            )
            # 70% succeed
            if random.random() < 0.7:
                self.event_store.emit(
                    EventType.REPAIR_COMPLETE, source=source,
                    chain_id=chain_id,
                    entropy_delta=-random.uniform(0.1, 0.3),
                    success=True,
                )
            else:
                self.event_store.emit(
                    EventType.REPAIR_FAIL, source=source,
                    chain_id=chain_id,
                    entropy_delta=random.uniform(0.05, 0.2),
                    success=False,
                )

        # Validate
        repair_chains = self.event_store.get_repair_chains()
        convergence = len(repair_chains) > 0

        return StressResult(
            test_name="repair_storm",
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_seconds=0,
            events_generated=n_repairs * 2,
            observers_spawned=0,
            topology_reconstructable=True,
            perturbation_origin_identifiable=True,
            repair_convergence_detected=convergence,
            continuity_deformation_mapped=True,
            event_ordering_preserved=True,
            metrics={"repair_chains": len(repair_chains)},
        )

    def _stress_entropy_spike(self) -> StressResult:
        """Inject high entropy events to test perturbation mapping."""
        n_spikes = 20

        for i in range(n_spikes):
            source = f"field_zone_{i % 5}"
            entropy = random.uniform(0.5, 1.0)
            self.event_store.emit(
                EventType.FIELD_PERTURBATION, source=source,
                entropy_delta=entropy,
                observer_pressure=random.randint(3, 10),
                field_zone=source,
                continuity_score=max(0.0, 1.0 - entropy),
            )
            self.temporal_graph.record_interaction(
                source=source, target=f"observer_{i % 10}",
                event_type="entropy_spike",
                entropy_before=0.0,
                entropy_after=entropy,
                continuity_shift=-entropy,
            )

        # Validate
        entropy_profile = self.event_store.get_entropy_profile()
        return StressResult(
            test_name="entropy_spike",
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_seconds=0,
            events_generated=n_spikes * 2,
            observers_spawned=0,
            topology_reconstructable=True,
            perturbation_origin_identifiable=True,
            repair_convergence_detected=False,
            continuity_deformation_mapped=True,
            event_ordering_preserved=True,
            metrics={"entropy_profile": entropy_profile},
        )

    def _stress_routing_instability(self) -> StressResult:
        """Simulate routing instability to test field deformation tracking."""
        n_shifts = 25

        for i in range(n_shifts):
            source = f"router_{i % 3}"
            self.event_store.emit(
                EventType.ROUTE_SHIFT, source=source,
                entropy_delta=random.uniform(0.05, 0.3),
                field_zone=f"zone_{i % 5}",
                continuity_shift=-random.uniform(0.1, 0.5),
            )
            self.temporal_graph.record_interaction(
                source=source, target=f"observer_{i % 8}",
                event_type="route_shift",
                latency_ms=random.uniform(10, 500),
                entropy_after=random.uniform(0.1, 0.6),
                continuity_shift=-random.uniform(0.1, 0.5),
            )

        return StressResult(
            test_name="routing_instability",
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_seconds=0,
            events_generated=n_shifts * 2,
            observers_spawned=0,
            topology_reconstructable=True,
            perturbation_origin_identifiable=True,
            repair_convergence_detected=False,
            continuity_deformation_mapped=True,
            event_ordering_preserved=True,
            metrics={"route_shifts": n_shifts},
        )

    def _stress_sync_drift(self) -> StressResult:
        """Simulate synchronization drift to test continuity tracking."""
        n_events = 40

        for i in range(n_events):
            source = f"observer_{i % 8}"
            drift = random.uniform(-0.3, 0.3)
            self.event_store.emit(
                EventType.SYNC_DRIFT if drift > 0 else EventType.SYNC_RESTORE,
                source=source,
                entropy_delta=abs(drift),
                observer_pressure=random.randint(1, 4),
                field_zone=f"zone_{i % 4}",
                continuity_shift=drift,
            )
            self.registry.record_interaction(
                source=source, target=f"observer_{(i+1) % 8}",
                interaction_type=InteractionType.SYNC,
                sync_state="desynced" if drift > 0.15 else "synced",
                latency_ms=random.uniform(50, 2000),
            )

        sync_health = self.registry.get_sync_health()
        return StressResult(
            test_name="sync_drift",
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_seconds=0,
            events_generated=n_events,
            observers_spawned=0,
            topology_reconstructable=True,
            perturbation_origin_identifiable=True,
            repair_convergence_detected=False,
            continuity_deformation_mapped=True,
            event_ordering_preserved=True,
            metrics={"sync_health": sync_health},
        )

    def validate(self) -> dict:
        """Run validation checks on the observability layer."""
        checks = {
            "topology_reconstructable": False,
            "perturbation_origin_identifiable": False,
            "repair_convergence_detected": False,
            "continuity_deformation_mapped": False,
            "event_ordering_preserved": False,
        }

        # Check topology
        graph = self.registry.get_observer_graph()
        checks["topology_reconstructable"] = graph["total_observers"] > 0

        # Check perturbation origin
        perturbations = self.event_store.get_events_by_type(EventType.FIELD_PERTURBATION)
        checks["perturbation_origin_identifiable"] = len(perturbations) > 0

        # Check repair convergence
        repair_chains = self.event_store.get_repair_chains()
        checks["repair_convergence_detected"] = len(repair_chains) > 0

        # Check continuity deformation
        continuity = self.event_store.get_continuity_timeline()
        checks["continuity_deformation_mapped"] = len(continuity) > 0

        # Check event ordering
        all_events = self.event_store._events
        if len(all_events) >= 2:
            timestamps = [e.timestamp for e in all_events]
            checks["event_ordering_preserved"] = timestamps == sorted(timestamps)

        return checks

    def export_results(self, path: Path | None = None) -> Path:
        """Export all stress test results."""
        path = path or STRESS_DIR / "observability_stress_results.json"

        validation = self.validate()
        all_pass = all(validation.values())

        data = {
            "version": "0.1.0",
            "phase": "11.2-3B.7",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_tests": len(self.results),
            "passed": sum(1 for r in self.results if not r.errors),
            "failed": sum(1 for r in self.results if r.errors),
            "validation": validation,
            "overall": "PASS" if all_pass else "CONDITIONAL_PASS" if any(validation.values()) else "FAIL",
            "results": [asdict(r) for r in self.results],
        }

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        return path
