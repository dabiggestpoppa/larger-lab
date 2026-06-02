# Runtime Awareness

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #observer

```python
"""
O-1-B3: RuntimeAwareness
========================
Maintains awareness of topology, active observers, entropy, repair state,
spawned agents, execution systems.

Inputs: event_bus, topology_state, observer_registry, runtime_metrics,
entropy_metrics.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable


@dataclass
class RuntimeSnapshot:
    """Point-in-time runtime awareness snapshot."""
    timestamp: str
    topology_node_count: int = 0
    topology_edge_count: int = 0
    active_observers: list[str] = field(default_factory=list)
    entropy_level: float = 0.0
    entropy_trend: str = "stable"  # "rising", "falling", "stable"
    repair_active: bool = False
    repair_targets: list[str] = field(default_factory=list)
    spawned_agents: int = 0
    execution_systems: dict[str, str] = field(default_factory=dict)
    alerts: list[dict[str, Any]] = field(default_factory=list)


class RuntimeAwareness:
    """
    Maintains live awareness of the runtime environment.
    
    Subscribes to events and topology changes to keep an accurate
    picture of the current system state.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._snapshot = RuntimeSnapshot(
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        self._history: list[RuntimeSnapshot] = []
        self._max_history = 100
        self._listeners: list[Callable] = []

    @property
    def snapshot(self) -> RuntimeSnapshot:
        return self._snapshot

    def update_topology(self, node_count: int, edge_count: int) -> None:
        with self._lock:
            self._snapshot.topology_node_count = node_count
            self._snapshot.topology_edge_count = edge_count
            self._snapshot.timestamp = datetime.now(timezone.utc).isoformat()
            self._check_topology_alerts()

    def update_observers(self, observer_ids: list[str]) -> None:
        with self._lock:
            self._snapshot.active_observers = list(observer_ids)
            self._snapshot.timestamp = datetime.now(timezone.utc).isoformat()

    def update_entropy(self, level: float, trend: str = "stable") -> None:
        with self._lock:
            prev = self._snapshot.entropy_level
            self._snapshot.entropy_level = max(0.0, min(1.0, level))
            self._snapshot.entropy_trend = trend
            self._snapshot.timestamp = datetime.now(timezone.utc).isoformat()
            if level > 0.7 and prev <= 0.7:
                self._add_alert("entropy_spike", f"Entropy rose to {level:.2f}")
            self._notify_listeners("entropy", level)

    def update_repair(self, active: bool, targets: list[str] | None = None) -> None:
        with self._lock:
            self._snapshot.repair_active = active
            self._snapshot.repair_targets = targets or []
            self._snapshot.timestamp = datetime.now(timezone.utc).isoformat()

    def update_spawned_agents(self, count: int) -> None:
        with self._lock:
            self._snapshot.spawned_agents = count
            self._snapshot.timestamp = datetime.now(timezone.utc).isoformat()

    def update_execution_systems(self, systems: dict[str, str]) -> None:
        with self._lock:
            self._snapshot.execution_systems = dict(systems)
            self._snapshot.timestamp = datetime.now(timezone.utc).isoformat()

    def get_snapshot_dict(self) -> dict[str, Any]:
        s = self._snapshot
        return {
            "timestamp": s.timestamp,
            "topology": {
                "nodes": s.topology_node_count,
                "edges": s.topology_edge_count,
            },
            "active_observers": s.active_observers,
            "entropy": {
                "level": s.entropy_level,
                "trend": s.entropy_trend,
            },
            "repair": {
                "active": s.repair_active,
                "targets": s.repair_targets,
            },
            "spawned_agents": s.spawned_agents,
            "execution_systems": s.execution_systems,
            "alerts": s.alerts[-10:],  # last 10 alerts
        }

    def take_snapshot(self) -> None:
        """Save current snapshot to history."""
        with self._lock:
            import copy
            self._history.append(copy.deepcopy(self._snapshot))
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]

    def subscribe(self, callback: Callable) -> None:
        self._listeners.append(callback)

    def _add_alert(self, alert_type: str, message: str) -> None:
        self._snapshot.alerts.append({
            "type": alert_type,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    def _check_topology_alerts(self) -> None:
        if self._snapshot.topology_node_count == 0:
            self._add_alert("topology_empty", "No topology nodes detected")

    def _notify_listeners(self, key: str, value: Any) -> None:
        for cb in self._listeners:
            try:
                cb(key, value)
            except Exception:
                pass

```

LINKS:
[[All Mermaid Graphs]]
[[Agents]]
[[Module Guide]]
[[Daily Runtime 20260531]]
[[Ontology Core Summary]]
[[Cal]]
[[Citation Workflow]]
[[Inputs]]
[[Server]]
[[System]]
[[Asset Configs]]
[[Convergence Indicator]]
[[Dmr Standalone Backtest]]
[[P90 Backtest]]
[[P90 Count Ews]]
[[P90 Dmr Backtest]]
[[P90 Dmr Combo Backtest]]
[[P90 Dmr Overlay Backtest]]
[[P90 Engine]]
[[P90 Engine Dmr]]
[[P90 Gap Check]]
[[P90 Trace Trades]]
[[P90 Usdchf Backtest]]
[[Run Majors Backtest]]
[[Run St Multi Asset]]
[[Run Top5 Backtest Mc]]
[[St Batch2 Runner]]
[[St Batch Runner]]
[[Symmetry Trap]]
[[Symmetry Trap Backtest]]
[[Symmetry Trap Monte Carlo]]
[[Atomic Sym Trap]]
[[Blind Chain Debug]]
[[Blind Chain Diag]]
[[Blind Chain Engine]]
[[Blind Chain Exact]]
[[Blind Chain V2 Debug]]
[[Blind Chain V2 Sl Calibrated]]
[[Blind Chain V3]]
[[Cerebus Resolution Engine]]
[[Constraint Anchor Engine]]
[[Debug Days]]
[[Debug One Day]]
[[Debug St]]
[[Debug Trace]]
[[Diag Option B]]
[[Diag V5]]
[[Dmr Strategy]]
[[Dual Engine]]
[[Naut Asset Config]]
[[P90 Cfd Expansion Engine]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine V3]]
[[P90 Cfd Expansion Engine V4]]
[[P90 Cfd Expansion Engine V5]]
[[P90 Strategy]]
[[Shared]]
[[Stall Harvest Cfd Engine]]
[[Symmetry Trap Engine]]
[[Symmetry Trap Exact]]
[[Symmetry Trap Option B]]
[[Symmetry Trap Strategy]]
[[Symmetry Trap V4]]
[[Symmetry Trap V5]]
[[Symmetry Trap V6 Exact]]
[[Symmetry Trap V7B Sl Calibrated]]
[[Symmetry Trap V7 Sl Calibrated]]
[[Two Plays Engine]]
[[Adaptation Engine]]
[[Agent Lifecycle]]
[[Agent Spawner]]
[[Attractor Analysis]]
[[Autonomous Repair]]
[[Capability Matcher]]
[[Complexity Scorer]]
[[Consensus Memory]]
[[Consensus Replay]]
[[Context Injector]]
[[Continuity Preserver]]
[[Data Fetcher]]
[[Dormant State Manager]]
[[Environmental Monitor]]
[[Event Schema]]
[[Execution Boundary]]
[[Failure Analyzer]]
[[Indicators]]
[[Journal]]
[[Loader]]
[[Long Horizon Memory]]
[[Metrics]]
[[Model Selector]]
[[Multi Agent Coordinator]]
[[Observability Stress]]
[[Observer Consensus]]
[[Observer Evolution]]
[[Observer Persistence]]
[[Observer Registry]]
[[Observer Specialization]]
[[Openrouter Gateway]]
[[Operational Drift Detect]]
[[Operational Replay]]
[[Operational Scoring]]
[[Passive Awareness]]
[[Pattern Memory]]
[[Persistent Runtime]]
[[Persistent Scheduler]]
[[Recovery Persistence]]
[[Routing Consensus]]
[[Routing Learning]]
[[Runtime Heartbeat]]
[[Spawn Blueprint]]
[[Spawn Planner]]
[[Spawn Registry]]
[[Spawn Replay]]
[[Structural Anchor]]
[[Synthesizer]]
[[Task Classifier]]
[[Temporal Graph]]
[[Test Journal]]
[[Test Loader]]
[[Topology Learning]]
[[Trace Collector]]
[[Trace Feedback]]
[[Workflow Distiller]]
[[Workflow Memory]]
[[Autonomous Orchestrator]]
[[Chat Log]]
[[Command Router]]
[[Context Distiller]]
[[Continuity Memory]]
[[Event Awareness]]
[[Graph Traversal]]
[[Observer Conversation Runtime]]
[[Observer Lifecycle]]
[[Observer Session]]
[[Observer State]]
[[Pattern Distillation]]
[[Primary Observer]]
[[Report Return]]
[[Semantic Retrieval]]
[[Task Executor]]
[[Task Intent Analyzer]]
[[Vault]]
[[Compressor]]
[[Error Intelligence]]
[[Knowledge Importer]]
[[Linker]]
[[Live Sync]]
[[Memory Distiller]]
[[Note Standard]]
[[Pattern Crystallizer]]
[[Taxonomy]]
[[Test Compressor]]
[[Test Context Injector]]
[[Test Error Intelligence]]
[[Test Linker]]
[[Test Memory Distiller]]
[[Test Note Standard]]
[[Test Pattern Crystallizer]]
[[Test Taxonomy]]
[[Test Vault Writer]]
[[Vault Writer]]
[[Interpreter]]
[[Semantic State]]
[[Telegram Gateway]]
