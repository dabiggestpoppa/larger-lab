# Consensus Replay

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #core

```python
"""
O2-B10: ConsensusReplay
=========================
Replay observer decisions from history.

Enables analysis and debugging of past consensus decisions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.consensus.consensus_memory import ConsensusMemory


class ConsensusReplay:
    """
    Replays observer decisions from consensus history.

    Useful for debugging, analysis, and testing.
    """

    def __init__(self, memory: ConsensusMemory | None = None):
        self.memory = memory or ConsensusMemory()

    def replay(
        self,
        task_type: str | None = None,
        complexity: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Replay consensus decisions matching criteria.

        Args:
            task_type: Filter by task type (optional)
            complexity: Filter by complexity (optional)
            limit: Maximum records to return

        Returns:
            List of matching consensus records
        """
        records = self.memory.get_recent(limit=limit * 3)  # Get extra for filtering

        filtered = []
        for record in records:
            if task_type and record.get("task_type") != task_type:
                continue
            if complexity and record.get("complexity") != complexity:
                continue
            filtered.append(record)
            if len(filtered) >= limit:
                break

        return filtered

    def get_decision_chain(self, timestamp: str) -> list[dict[str, Any]]:
        """
        Get the full decision chain for a specific timestamp.

        Returns all records within 5 seconds of the given timestamp.
        """
        records = self.memory.get_recent(limit=100)
        matching = [r for r in records if r.get("timestamp") == timestamp]

        if not matching:
            return []

        # Get records within 5 seconds
        target = matching[0]
        target_time = target.get("timestamp", "")
        chain = [r for r in records if abs(
            self._time_diff(r.get("timestamp", ""), target_time)
        ) < 5.0]

        return sorted(chain, key=lambda r: r.get("timestamp", ""))

    def _time_diff(self, t1: str, t2: str) -> float:
        """Calculate time difference in seconds."""
        try:
            dt1 = datetime.fromisoformat(t1)
            dt2 = datetime.fromisoformat(t2)
            return abs((dt1 - dt2).total_seconds())
        except Exception:
            return float("inf")

    def get_stats(self) -> dict[str, Any]:
        """Get replay statistics."""
        records = self.memory.get_recent(limit=1000)
        return {
            "total_records": len(records),
            "task_types": list(set(r.get("task_type", "unknown") for r in records)),
            "complexities": list(set(r.get("complexity", "unknown") for r in records)),
            "avg_agreement": self.memory.avg_agreement,
            "task_distribution": self.memory.task_type_distribution,
        }

```

LINKS:
[[Debugging]]
[[Testing]]
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
[[Memory]]
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
