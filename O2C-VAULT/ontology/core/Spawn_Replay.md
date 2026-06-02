# Spawn Replay

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #core

```python
"""
O3-B9: SpawnReplay
===================
Replay spawned agent behavior.

Records and replays spawn decisions for debugging, testing,
and consensus replay (O2-B10).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("spawn.replay")


@dataclass
class SpawnRecord:
    """Record of a spawn decision and its outcome."""
    record_id: str
    timestamp: str
    task_type: str
    complexity: str
    model: str
    context_keys: list[str]
    tools: list[str]
    consensus_confidence: float = 0.0
    status: str = "pending"
    duration_seconds: float = 0.0
    tokens_used: int = 0
    error: str | None = None


class SpawnReplay:
    """
    Records and replays spawn decisions.
    
    Enables debugging of routing decisions, testing of spawn
    configurations, and feeds into consensus replay.
    """

    def __init__(self):
        self._records: list[SpawnRecord] = []

    def record_spawn(
        self,
        record_id: str,
        task_type: str,
        complexity: str,
        model: str,
        context_keys: list[str],
        tools: list[str],
        consensus_confidence: float = 0.0,
    ) -> SpawnRecord:
        """Record a spawn decision."""
        record = SpawnRecord(
            record_id=record_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_type=task_type,
            complexity=complexity,
            model=model,
            context_keys=context_keys,
            tools=tools,
            consensus_confidence=consensus_confidence,
        )
        self._records.append(record)
        return record

    def update_record(
        self, record_id: str, status: str, **kwargs: Any
    ) -> bool:
        """Update a spawn record with outcome data."""
        for r in self._records:
            if r.record_id == record_id:
                r.status = status
                for k, v in kwargs.items():
                    if hasattr(r, k):
                        setattr(r, k, v)
                return True
        return False

    def replay(self, record_id: str) -> dict[str, Any]:
        """Replay a spawn decision — returns the original decision context."""
        for r in self._records:
            if r.record_id == record_id:
                return {
                    "record_id": r.record_id,
                    "timestamp": r.timestamp,
                    "task_type": r.task_type,
                    "complexity": r.complexity,
                    "model": r.model,
                    "context_keys": r.context_keys,
                    "tools": r.tools,
                    "consensus_confidence": r.consensus_confidence,
                    "outcome": {
                        "status": r.status,
                        "duration_seconds": r.duration_seconds,
                        "tokens_used": r.tokens_used,
                        "error": r.error,
                    },
                }
        return {"error": "Record not found"}

    def replay_all(
        self, task_type: str | None = None, status: str | None = None
    ) -> list[dict[str, Any]]:
        """Replay all matching spawn records."""
        records = self._records
        if task_type:
            records = [r for r in records if r.task_type == task_type]
        if status:
            records = [r for r in records if r.status == status]
        return [self.replay(r.record_id) for r in records]

    def get_stats(self) -> dict[str, Any]:
        """Get replay statistics."""
        total = len(self._records)
        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}
        by_model: dict[str, int] = {}
        for r in self._records:
            by_type[r.task_type] = by_type.get(r.task_type, 0) + 1
            by_status[r.status] = by_status.get(r.status, 0) + 1
            by_model[r.model] = by_model.get(r.model, 0) + 1

        return {
            "total_records": total,
            "by_type": by_type,
            "by_status": by_status,
            "by_model": by_model,
        }

```

LINKS:
[[Debugging]]
[[Testing]]
[[Tools]]
[[Journal 20260602T005953Z Command Spawn]]
[[Journal 20260602T005953Z Orchestrated Spawn]]
[[Journal 20260602T005953Z Spawn Research]]
[[Ontology Core Summary]]
[[Citation Workflow]]
[[Configuration]]
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
