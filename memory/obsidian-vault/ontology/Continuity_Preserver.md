# Continuity Preserver

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #core

```python
"""
O7-B5: ContinuityPreserver
===========================
Maintain operational continuity across restarts.

Tracks workflows, topology evolution, observer states, orchestration
memory, and runtime lineage — preserves true persistent operational memory.
"""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTINUITY_DIR = REPO_ROOT / "data" / "persistent_field" / "continuity"

logger = logging.getLogger("persistent_field.continuity_preserver")


@dataclass
class ContinuityRecord:
    """A continuity preservation record."""
    record_id: str
    record_type: str  # workflow, topology, observer, orchestration, runtime
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class ContinuityPreserver:
    """
    Preserve long-horizon operational continuity.

    Tracks: workflows, topology evolution, observer states,
    orchestration memory, runtime lineage.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._records: list[ContinuityRecord] = []
        self._load()

    def preserve(self, record_type: str, data: dict[str, Any]) -> ContinuityRecord:
        """Preserve a continuity record."""
        with self._lock:
            record = ContinuityRecord(
                record_id=f"{record_type}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                record_type=record_type,
                data=data,
            )
            self._records.append(record)
            self._persist_record(record)
            return record

    def get_records(self, record_type: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """Get continuity records."""
        records = self._records
        if record_type:
            records = [r for r in records if r.record_type == record_type]
        return [self._record_to_dict(r) for r in records[-limit:]]

    def get_continuity_score(self) -> float:
        """Calculate overall continuity score."""
        if not self._records:
            return 1.0

        # Score based on recency and completeness
        now = datetime.now(timezone.utc)
        scores = []
        for record in self._records[-20:]:
            try:
                record_time = datetime.fromisoformat(record.timestamp)
                age_hours = (now - record_time).total_seconds() / 3600
                # Newer records score higher
                recency = max(0, 1.0 - (age_hours / 168))  # 168 hours = 1 week
                scores.append(recency)
            except (ValueError, TypeError):
                scores.append(0.5)

        return round(sum(scores) / len(scores), 3) if scores else 1.0

    def get_summary(self) -> dict[str, Any]:
        """Get continuity preservation summary."""
        by_type: dict[str, int] = {}
        for r in self._records:
            by_type[r.record_type] = by_type.get(r.record_type, 0) + 1

        return {
            "total_records": len(self._records),
            "by_type": by_type,
            "continuity_score": self.get_continuity_score(),
            "oldest_record": self._records[0].timestamp if self._records else None,
            "newest_record": self._records[-1].timestamp if self._records else None,
        }

    def _record_to_dict(self, record: ContinuityRecord) -> dict[str, Any]:
        return {
            "record_id": record.record_id,
            "record_type": record.record_type,
            "data": record.data,
            "timestamp": record.timestamp,
        }

    def _persist_record(self, record: ContinuityRecord) -> None:
        """Persist a record to disk."""
        try:
            CONTINUITY_DIR.mkdir(parents=True, exist_ok=True)
            file_path = CONTINUITY_DIR / f"{record.record_id}.json"
            file_path.write_text(json.dumps(self._record_to_dict(record), indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to persist continuity record: {e}")

    def _load(self) -> None:
        """Load persisted continuity records."""
        try:
            if CONTINUITY_DIR.exists():
                for file_path in sorted(CONTINUITY_DIR.glob("*.json")):
                    try:
                        data = json.loads(file_path.read_text(encoding="utf-8"))
                        self._records.append(ContinuityRecord(**data))
                    except Exception:
                        pass
        except Exception:
            pass

```

LINKS:
[[Cg 5 Continuity Intelligence]]
[[Ontology Core Summary]]
[[Cal]]
[[Citation Workflow]]
[[Server]]
[[Workflow]]
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
[[Consensus Replay]]
[[Context Injector]]
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
