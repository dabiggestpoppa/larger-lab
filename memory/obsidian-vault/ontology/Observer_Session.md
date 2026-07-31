# Observer Session

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #observer

```python
"""
O-1-B8: ObserverSession
========================
Session continuity management.

Tracks observer sessions across time, handles session creation,
resumption, and archival.
"""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
SESSION_DIR = REPO_ROOT / "data" / "observer" / "sessions"
SESSION_FILE = SESSION_DIR / "active_sessions.json"


@dataclass
class SessionData:
    """Single observer session."""
    session_id: str
    observer_id: str
    created_at: str
    last_active: str
    status: str = "active"  # "active", "paused", "closed"
    context: dict[str, Any] = field(default_factory=dict)
    task_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class ObserverSession:
    """
    Manages observer session lifecycle.
    
    Sessions track continuity across interactions and enable
    resumption after restarts.
    """

    def __init__(self):
        self._lock = threading.RLock()
        SESSION_DIR.mkdir(parents=True, exist_ok=True)
        self._sessions: dict[str, SessionData] = {}
        self._active_session_id: str | None = None
        self._load()

    @property
    def active_session(self) -> SessionData | None:
        if self._active_session_id:
            return self._sessions.get(self._active_session_id)
        return None

    def create_session(
        self,
        observer_id: str = "primary",
        context: dict[str, Any] | None = None,
    ) -> SessionData:
        """Create a new session."""
        with self._lock:
            session = SessionData(
                session_id=f"session_{uuid.uuid4().hex[:8]}",
                observer_id=observer_id,
                created_at=datetime.now(timezone.utc).isoformat(),
                last_active=datetime.now(timezone.utc).isoformat(),
                context=context or {},
            )
            self._sessions[session.session_id] = session
            self._active_session_id = session.session_id
            self._persist()
            return session

    def resume_session(self, session_id: str) -> SessionData | None:
        """Resume an existing session."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session and session.status != "closed":
                session.status = "active"
                session.last_active = datetime.now(timezone.utc).isoformat()
                self._active_session_id = session_id
                self._persist()
                return session
            return None

    def close_session(self, session_id: str | None = None) -> None:
        """Close a session."""
        with self._lock:
            sid = session_id or self._active_session_id
            if sid and sid in self._sessions:
                self._sessions[sid].status = "closed"
                self._sessions[sid].last_active = datetime.now(timezone.utc).isoformat()
                if self._active_session_id == sid:
                    self._active_session_id = None
                self._persist()

    def touch_session(self, task_increment: int = 1) -> None:
        """Update active session's last active time."""
        with self._lock:
            session = self.active_session
            if session:
                session.last_active = datetime.now(timezone.utc).isoformat()
                session.task_count += task_increment
                self._persist()

    def get_all_sessions(self) -> list[dict[str, Any]]:
        """Get all sessions as dicts."""
        with self._lock:
            return [
                {
                    "session_id": s.session_id,
                    "observer_id": s.observer_id,
                    "created_at": s.created_at,
                    "last_active": s.last_active,
                    "status": s.status,
                    "task_count": s.task_count,
                    "context": s.context,
                }
                for s in self._sessions.values()
            ]

    def _persist(self) -> None:
        try:
            data = {
                sid: {
                    "session_id": s.session_id,
                    "observer_id": s.observer_id,
                    "created_at": s.created_at,
                    "last_active": s.last_active,
                    "status": s.status,
                    "context": s.context,
                    "task_count": s.task_count,
                    "metadata": s.metadata,
                }
                for sid, s in self._sessions.items()
            }
            data["_active_session_id"] = self._active_session_id
            SESSION_FILE.write_text(json.dumps(data, indent=2))
        except Exception:
            pass

    def _load(self) -> None:
        if SESSION_FILE.exists():
            try:
                data = json.loads(SESSION_FILE.read_text())
                self._active_session_id = data.pop("_active_session_id", None)
                for sid, sdata in data.items():
                    self._sessions[sid] = SessionData(**sdata)
            except Exception:
                pass

```

LINKS:
[[All Mermaid Graphs]]
[[Master Plan Observer Core]]
[[Module Guide]]
[[Observer Core Workspace State]]
[[Observer Core O1 O7]]
[[Ontology Core Summary]]
[[Session 20260531 2200]]
[[Session Testagent 20260531 0245]]
[[Session Testagent 20260531 0245 Full]]
[[Action]]
[[Citation Workflow]]
[[Interaction]]
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
