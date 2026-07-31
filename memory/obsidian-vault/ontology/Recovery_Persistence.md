# Recovery Persistence

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #core

```python
"""
O7-B10: RecoveryPersistence
============================
Preserve continuity during failure.

Handles crashes, restarts, machine reboots, observer failures,
runtime corruption. Features: state snapshots, continuity restoration,
topology reconstruction, observer recovery.
"""

from __future__ import annotations

import json
import logging
import shutil
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
SNAPSHOT_DIR = REPO_ROOT / "data" / "persistent_field" / "snapshots"

logger = logging.getLogger("persistent_field.recovery")


@dataclass
class Snapshot:
    """A recovery snapshot."""
    snapshot_id: str
    timestamp: str
    components: list[str] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)
    integrity_hash: str = ""


class RecoveryPersistence:
    """
    Preserve runtime continuity during failure.

    Handles: crashes, restarts, machine reboots, observer failures, runtime corruption.
    """

    MAX_SNAPSHOTS = 10

    def __init__(self):
        self._lock = threading.Lock()
        self._snapshots: list[Snapshot] = []
        self._load_snapshots()

    def create_snapshot(self, components: list[str], data: dict[str, Any]) -> Snapshot:
        """Create a recovery snapshot."""
        with self._lock:
            snapshot = Snapshot(
                snapshot_id=f"snap_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                components=components,
                data=data,
                integrity_hash=self._compute_hash(data),
            )
            self._snapshots.append(snapshot)
            self._persist_snapshot(snapshot)

            # Prune old snapshots
            if len(self._snapshots) > self.MAX_SNAPSHOTS:
                self._snapshots = self._snapshots[-self.MAX_SNAPSHOTS:]

            logger.info(f"Snapshot created: {snapshot.snapshot_id} ({len(components)} components)")
            return snapshot

    def restore_snapshot(self, snapshot_id: str | None = None) -> dict[str, Any] | None:
        """Restore from a snapshot."""
        with self._lock:
            if snapshot_id:
                snapshot = next((s for s in self._snapshots if s.snapshot_id == snapshot_id), None)
            elif self._snapshots:
                snapshot = self._snapshots[-1]
            else:
                return None

            if snapshot:
                # Verify integrity
                current_hash = self._compute_hash(snapshot.data)
                if current_hash != snapshot.integrity_hash:
                    logger.warning(f"Snapshot {snapshot.snapshot_id} integrity check failed")
                    return None

                logger.info(f"Snapshot restored: {snapshot.snapshot_id}")
                return {
                    "snapshot_id": snapshot.snapshot_id,
                    "timestamp": snapshot.timestamp,
                    "components": snapshot.components,
                    "data": snapshot.data,
                }
            return None

    def get_latest_snapshot(self) -> dict[str, Any] | None:
        """Get the latest snapshot."""
        if self._snapshots:
            latest = self._snapshots[-1]
            return {
                "snapshot_id": latest.snapshot_id,
                "timestamp": latest.timestamp,
                "components": latest.components,
            }
        return None

    def get_recovery_status(self) -> dict[str, Any]:
        """Get recovery persistence status."""
        return {
            "total_snapshots": len(self._snapshots),
            "latest_snapshot": self.get_latest_snapshot(),
            "max_snapshots": self.MAX_SNAPSHOTS,
            "snapshot_dir_exists": SNAPSHOT_DIR.exists(),
        }

    def _compute_hash(self, data: dict[str, Any]) -> str:
        """Compute a simple integrity hash."""
        import hashlib
        content = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(content.encode()).hexdigest()

    def _persist_snapshot(self, snapshot: Snapshot) -> None:
        """Persist snapshot to disk."""
        try:
            SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
            file_path = SNAPSHOT_DIR / f"{snapshot.snapshot_id}.json"
            file_path.write_text(json.dumps({
                "snapshot_id": snapshot.snapshot_id,
                "timestamp": snapshot.timestamp,
                "components": snapshot.components,
                "data": snapshot.data,
                "integrity_hash": snapshot.integrity_hash,
            }, indent=2, default=str), encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to persist snapshot: {e}")

    def _load_snapshots(self) -> None:
        """Load persisted snapshots."""
        try:
            if SNAPSHOT_DIR.exists():
                for file_path in sorted(SNAPSHOT_DIR.glob("*.json")):
                    try:
                        data = json.loads(file_path.read_text(encoding="utf-8"))
                        self._snapshots.append(Snapshot(**data))
                    except Exception:
                        pass
        except Exception:
            pass

```

LINKS:
[[Ontology Core Summary]]
[[Citation Workflow]]
[[Failures]]
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
[[Observer Specialization]]
[[Openrouter Gateway]]
[[Operational Drift Detect]]
[[Operational Replay]]
[[Operational Scoring]]
[[Passive Awareness]]
[[Pattern Memory]]
[[Persistent Runtime]]
[[Persistent Scheduler]]
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
