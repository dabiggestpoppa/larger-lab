# Consensus Memory

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #core

```python
"""
O2-B8: ConsensusMemory
=======================
Store orchestration outcome history.

Persists consensus decisions for learning and replay.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
MEMORY_DIR = REPO_ROOT / "data" / "consensus"
MEMORY_FILE = MEMORY_DIR / "consensus_history.json"


class ConsensusMemory:
    """
    Persistent storage for consensus decisions.

    Records consensus outcomes for learning, replay, and analysis.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._records: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        """Load records from disk."""
        try:
            if MEMORY_FILE.exists():
                data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
                self._records = data.get("records", [])
        except Exception:
            self._records = []

    def _save(self) -> None:
        """Save records to disk."""
        try:
            MEMORY_DIR.mkdir(parents=True, exist_ok=True)
            data = {
                "records": self._records[-1000:],  # Keep last 1000
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            MEMORY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass  # Non-critical

    def record_consensus(self, result: Any) -> None:
        """Record a consensus result."""
        with self._lock:
            record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "task_type": result.task_type,
                "complexity": result.complexity,
                "confidence": result.confidence,
                "routing_path": result.routing_path,
                "recommended_model": result.recommended_model,
                "spawn_required": result.spawn_required,
                "agreement_score": result.agreement_score,
                "voter_count": result.voter_count,
            }
            self._records.append(record)
            self._save()

    def get_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent consensus records."""
        with self._lock:
            return self._records[-limit:]

    @property
    def total_records(self) -> int:
        return len(self._records)

    @property
    def avg_agreement(self) -> float:
        if not self._records:
            return 0.0
        scores = [r.get("agreement_score", 0) for r in self._records]
        return round(sum(scores) / len(scores), 3)

    @property
    def task_type_distribution(self) -> dict[str, int]:
        dist: dict[str, int] = {}
        for r in self._records:
            tt = r.get("task_type", "unknown")
            dist[tt] = dist.get(tt, 0) + 1
        return dist

    @property
    def model_distribution(self) -> dict[str, int]:
        dist: dict[str, int] = {}
        for r in self._records:
            m = r.get("recommended_model", "unknown")
            dist[m] = dist.get(m, 0) + 1
        return dist

```

LINKS:
[[Ontology Core Summary]]
[[Cal]]
[[Citation Workflow]]
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
