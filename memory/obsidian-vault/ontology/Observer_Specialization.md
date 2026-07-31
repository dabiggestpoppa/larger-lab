# Observer Specialization

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #core

```python
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

```

LINKS:
[[Master Plan Observer Core]]
[[Observer Core Workspace State]]
[[Observer Core O1 O7]]
[[Ontology Core Summary]]
[[Cal]]
[[Citation Workflow]]
[[Server]]
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
[[Runtime Awareness]]
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
