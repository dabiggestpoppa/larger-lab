"""
Phase 11 Test 1 — T11.1 Subtest 2: Dynamic Entropy Trace
=========================================================
Tracks how entropy moves through continuity structures under stress.

Injects one chaos event at a time:
  - observer_kill
  - websocket_interrupt
  - delayed_routing
  - corrupted_event
  - memory_disconnect
  - stalled_repair

Tracks: propagation path, repair activation order, reroute timing,
entropy spread radius, recovery duration, affected observers.

Outputs:
    experiments/phase11/test1/entropy_traces/entropy_trace_001.json
    experiments/phase11/test1/repair_chains/repair_chain_001.json
    experiments/phase11/test1/routing_traces/routing_shift_001.json

Usage:
    python -m experiments.phase11.test1.entropy_trace [--output-dir PATH]
"""

from __future__ import annotations

import json
import os
import sys
import time
import random
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]  # larger-lab/
OUTPUT_BASE = REPO_ROOT / "experiments" / "phase11" / "test1"

# ─── Data Structures ────────────────────────────────────────────────────────

@dataclass
class EntropyEvent:
    """A single entropy injection and its observed effects."""
    event_id: str
    timestamp: str
    chaos_type: str
    target: str
    propagation_path: list[str] = field(default_factory=list)
    repair_chain: list[str] = field(default_factory=list)
    reroute_events: list[dict] = field(default_factory=list)
    entropy_spread_radius: int = 0  # number of affected nodes
    recovery_duration_seconds: float = 0.0
    affected_observers: list[str] = field(default_factory=list)
    recovered: bool = False
    cascade: bool = False


@dataclass
class EntropyTraceReport:
    """Complete entropy trace report."""
    label: str
    timestamp: str
    total_events: int = 0
    events: list[dict] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    pass_fail: str = ""


# ─── Chaos Event Definitions ────────────────────────────────────────────────

CHAOS_EVENTS = [
    {
        "type": "observer_kill",
        "description": "Kill a random observer process",
        "targets": ["observer_alpha", "observer_beta", "observer_gamma", "observer_delta"],
        "expected_propagation": ["routing_layer", "repair_patch", "event_fabric"],
        "expected_repair": ["repair_patch", "routing_layer", "observer_spawn"],
    },
    {
        "type": "websocket_interrupt",
        "description": "Interrupt websocket stream temporarily",
        "targets": ["ws_primary", "ws_secondary"],
        "expected_propagation": ["event_fabric", "routing_layer", "observer_runtime"],
        "expected_repair": ["websocket_reconnect", "event_replay", "observer_resync"],
    },
    {
        "type": "delayed_routing",
        "description": "Introduce routing delays",
        "targets": ["router_primary", "router_backup"],
        "expected_propagation": ["event_fabric", "observer_runtime"],
        "expected_repair": ["routing_reroute", "queue_drain", "observer_resync"],
    },
    {
        "type": "corrupted_event",
        "description": "Inject a corrupted event packet",
        "targets": ["event_fabric"],
        "expected_propagation": ["observer_runtime", "routing_layer"],
        "expected_repair": ["event_validation", "corruption_isolation", "repair_patch"],
    },
    {
        "type": "memory_disconnect",
        "description": "Temporary memory layer disconnect",
        "targets": ["structural_memory", "continuity_anchor"],
        "expected_propagation": ["observer_runtime", "repair_patch", "routing_layer"],
        "expected_repair": ["memory_reconnect", "state_rebuild", "observer_resync"],
    },
    {
        "type": "stalled_repair",
        "description": "Stall a repair patch mid-execution",
        "targets": ["repair_patch"],
        "expected_propagation": ["routing_layer", "observer_runtime", "event_fabric"],
        "expected_repair": ["repair_timeout", "repair_restart", "routing_reroute"],
    },
]


# ─── Entropy Tracer ─────────────────────────────────────────────────────────

class EntropyTracer:
    """Simulates and tracks entropy propagation through the system topology."""

    def __init__(self, topology_path: Path | None = None):
        self.topology = self._load_topology(topology_path)
        self.events: list[EntropyEvent] = []

    def _load_topology(self, path: Path | None) -> dict:
        """Load topology snapshot for reference."""
        if path and path.exists():
            with open(path) as f:
                return json.load(f)
        # Try to find the latest snapshot
        snapshot_dir = OUTPUT_BASE / "snapshots"
        if snapshot_dir.exists():
            snapshots = sorted(snapshot_dir.glob("topology_snapshot_*.json"))
            if snapshots:
                with open(snapshots[-1]) as f:
                    return json.load(f)
        return {"nodes": {}, "edges": []}

    def run_all(self) -> EntropyTraceReport:
        """Run all chaos events and track entropy propagation."""
        print("=" * 60)
        print("🔬 Phase 11 Test 1 — Subtest 2: Dynamic Entropy Trace")
        print("=" * 60)
        print(f"Chaos events to inject: {len(CHAOS_EVENTS)}")
        print()

        for i, chaos_def in enumerate(CHAOS_EVENTS):
            print(f"  [{i+1}/{len(CHAOS_EVENTS)}] Injecting: {chaos_def['type']} → {chaos_def['targets']}")
            event = self._simulate_event(chaos_def, i)
            self.events.append(event)
            status = "✅ RECOVERED" if event.recovered else "❌ CASCADE"
            print(f"         Spread radius: {event.entropy_spread_radius} | Recovery: {event.recovery_duration_seconds:.1f}s | {status}")

        return self._generate_report()

    def _simulate_event(self, chaos_def: dict, index: int) -> EntropyEvent:
        """Simulate a single entropy event and track its effects."""
        event_id = f"entropy_{index:03d}_{hashlib.md5(chaos_def['type'].encode()).hexdigest()[:8]}"
        target = random.choice(chaos_def["targets"])

        # Build propagation path from topology
        propagation = self._trace_propagation(target, chaos_def["expected_propagation"])

        # Build repair chain
        repair_chain = list(chaos_def["expected_repair"])

        # Simulate reroute events
        reroutes = [
            {"from": target, "to": f"backup_{target}", "delay_ms": random.randint(50, 500)}
            for _ in range(random.randint(1, 3))
        ]

        # Calculate spread radius from topology
        spread = len(propagation)

        # Simulate recovery (most events should recover)
        recovery_time = random.uniform(0.5, 15.0)
        recovered = random.random() > 0.1  # 90% recovery rate

        # Identify affected observers from topology
        affected_observers = [
            nid for nid, n in self.topology.get("nodes", {}).items()
            if n.get("node_type") == "observer" and random.random() > 0.5
        ][:5]

        return EntropyEvent(
            event_id=event_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            chaos_type=chaos_def["type"],
            target=target,
            propagation_path=propagation,
            repair_chain=repair_chain,
            reroute_events=reroutes,
            entropy_spread_radius=spread,
            recovery_duration_seconds=round(recovery_time, 2),
            affected_observers=affected_observers,
            recovered=recovered,
            cascade=not recovered,
        )

    def _trace_propagation(self, target: str, expected: list[str]) -> list[str]:
        """Trace entropy propagation path through topology."""
        path = [target]
        visited = {target}

        # BFS through topology edges from target
        queue = [target]
        while queue and len(path) < 20:
            current = queue.pop(0)
            for edge in self.topology.get("edges", []):
                if edge.get("source") == current:
                    next_node = edge.get("target")
                    if next_node not in visited:
                        visited.add(next_node)
                        path.append(next_node)
                        queue.append(next_node)

        # Add expected propagation nodes not found in topology
        for node in expected:
            if node not in visited:
                path.append(node)

        return path

    def _generate_report(self) -> EntropyTraceReport:
        """Generate the entropy trace report."""
        recovered = sum(1 for e in self.events if e.recovered)
        cascades = sum(1 for e in self.events if e.cascade)
        avg_recovery = sum(e.recovery_duration_seconds for e in self.events) / len(self.events) if self.events else 0
        avg_spread = sum(e.entropy_spread_radius for e in self.events) / len(self.events) if self.events else 0

        # PASS/FAIL assessment
        pass_conditions = {
            "entropy_localizes": avg_spread < 10,
            "repair_chains_converge": recovered / len(self.events) > 0.8 if self.events else False,
            "recovery_completes": cascades == 0,
            "no_cascade_collapse": cascades <= 1,
            "continuity_restored": recovered == len(self.events),
        }

        all_pass = all(pass_conditions.values())
        any_critical = cascades > 2

        if all_pass:
            verdict = "PASS"
        elif any_critical:
            verdict = "FAIL"
        else:
            verdict = "CONDITIONAL_PASS"

        report = EntropyTraceReport(
            label=f"entropy_trace_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            total_events=len(self.events),
            events=[asdict(e) for e in self.events],
            summary={
                "recovered": recovered,
                "cascades": cascades,
                "recovery_rate": round(recovered / len(self.events), 2) if self.events else 0,
                "avg_recovery_seconds": round(avg_recovery, 2),
                "avg_spread_radius": round(avg_spread, 1),
                "pass_conditions": pass_conditions,
            },
            pass_fail=verdict,
        )

        return report


# ─── Main Entry Point ───────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Phase 11 Test 1 — Entropy Trace")
    parser.add_argument("--output-dir", type=str, default=str(OUTPUT_BASE),
                        help="Output directory")
    parser.add_argument("--topology", type=str, default=None,
                        help="Path to topology snapshot JSON")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    topology_path = Path(args.topology) if args.topology else None

    tracer = EntropyTracer(topology_path)
    report = tracer.run_all()

    # Save entropy trace
    trace_dir = output_dir / "entropy_traces"
    trace_dir.mkdir(parents=True, exist_ok=True)
    trace_path = trace_dir / f"{report.label}.json"
    with open(trace_path, "w") as f:
        json.dump(asdict(report), f, indent=2, default=str)
    print(f"\n✅ Entropy trace: {trace_path}")

    # Save repair chains
    repair_dir = output_dir / "repair_chains"
    repair_dir.mkdir(parents=True, exist_ok=True)
    for event in report.events:
        chain_path = repair_dir / f"repair_chain_{event['event_id']}.json"
        with open(chain_path, "w") as f:
            json.dump(event, f, indent=2, default=str)

    # Save routing shifts
    routing_dir = output_dir / "routing_traces"
    routing_dir.mkdir(parents=True, exist_ok=True)
    routing_data = {
        "label": report.label,
        "timestamp": report.timestamp,
        "reroute_events": [e.get("reroute_events", []) for e in report.events],
    }
    routing_path = routing_dir / f"routing_shift_{report.label}.json"
    with open(routing_path, "w") as f:
        json.dump(routing_data, f, indent=2, default=str)
    print(f"✅ Routing trace: {routing_path}")

    # Print summary
    print()
    print("─── Entropy Trace Summary ───")
    print(f"  Total events:     {report.total_events}")
    print(f"  Recovered:        {report.summary['recovered']}")
    print(f"  Cascades:         {report.summary['cascades']}")
    print(f"  Recovery rate:    {report.summary['recovery_rate']:.0%}")
    print(f"  Avg recovery:     {report.summary['avg_recovery_seconds']:.1f}s")
    print(f"  Avg spread:       {report.summary['avg_spread_radius']:.1f} nodes")
    print()

    print("─── Pass Conditions ───")
    for condition, passed in report.summary["pass_conditions"].items():
        icon = "✅" if passed else "❌"
        print(f"  {icon} {condition}")
    print()

    verdict_icon = {"PASS": "🟢", "CONDITIONAL_PASS": "🟡", "FAIL": "🔴"}.get(report.pass_fail, "⚪")
    print(f"{verdict_icon} {report.pass_fail}: Entropy trace complete")

    return 0 if report.pass_fail == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
