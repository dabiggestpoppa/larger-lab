"""
OCE Tracing Engine — Phase 5.2
==============================
Distributed event tracing through the OCE topology.

Traces show:
- Full event flow path (source → observers → outcome)
- Per-hop latency (time spent at each observer)
- Observer actions taken per event
- Outcome (success, error, dropped)

Traces are stored in-memory with configurable TTL and persisted to SQLite.
"""

import sqlite3
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("oce.tracing")

# ─── Constants ───────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "traces.db"
DEFAULT_TRACE_TTL_SEC = 3600  # 1 hour


# ─── Data Models ─────────────────────────────────────────────────────────────

class TraceOutcome(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    DROPPED = "dropped"
    TIMEOUT = "timeout"
    IN_PROGRESS = "in_progress"


class TraceHop(BaseModel):
    """A single hop in a trace (observer processing step)."""
    observer_id: str
    action: str  # e.g., "process", "forward", "filter", "transform"
    latency_ms: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Trace(BaseModel):
    """A full event trace through the topology."""
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_id: str
    event_type: str
    source: str
    hops: List[TraceHop] = Field(default_factory=list)
    outcome: TraceOutcome = TraceOutcome.IN_PROGRESS
    total_latency_ms: float = 0.0
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_hop(self, observer_id: str, action: str, latency_ms: float, **meta):
        hop = TraceHop(
            observer_id=observer_id,
            action=action,
            latency_ms=latency_ms,
            metadata=meta,
        )
        self.hops.append(hop)
        self.total_latency_ms += latency_ms

    def complete(self, outcome: TraceOutcome, error_message: str = None):
        self.outcome = outcome
        self.ended_at = datetime.now(timezone.utc)
        self.error_message = error_message


# ─── Tracing Engine ──────────────────────────────────────────────────────────

class TracingEngine:
    """
    Singleton tracing engine for OCE.

    Tracks event flow through the observer topology:
    - Start trace when event enters the fabric
    - Add hop when observer processes the event
    - Complete trace when event reaches final outcome
    - Query traces by observer, time range, outcome
    """

    _instance: Optional["TracingEngine"] = None
    _lock = Lock()

    def __new__(cls) -> "TracingEngine":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        self._active_traces: Dict[str, Trace] = {}
        self._completed_traces: List[Trace] = []
        self._max_completed = 10000
        self._ttl_sec = DEFAULT_TRACE_TTL_SEC

        # Initialize SQLite
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._init_db()
        logger.info("TracingEngine initialized")

    def _init_db(self):
        """Initialize SQLite database for trace persistence."""
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS traces (
                    trace_id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    total_latency_ms REAL,
                    hop_count INTEGER,
                    trace_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_traces_event_type
                ON traces(event_type)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_traces_outcome
                ON traces(outcome)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_traces_created
                ON traces(created_at)
            """)
            conn.commit()

    # ─── Trace Lifecycle ─────────────────────────────────────────────────

    def start_trace(
        self,
        event_id: str,
        event_type: str,
        source: str,
        **metadata,
    ) -> str:
        """Start a new trace for an event. Returns trace_id."""
        trace = Trace(
            event_id=event_id,
            event_type=event_type,
            source=source,
            metadata=metadata,
        )
        self._active_traces[trace.trace_id] = trace
        logger.debug(f"Trace started: {trace.trace_id} for event {event_id}")
        return trace.trace_id

    def add_hop(
        self,
        trace_id: str,
        observer_id: str,
        action: str,
        latency_ms: float,
        **metadata,
    ):
        """Add a processing hop to an active trace."""
        trace = self._active_traces.get(trace_id)
        if trace is None:
            logger.warning(f"Trace {trace_id} not found for hop add")
            return
        trace.add_hop(observer_id, action, latency_ms, **metadata)

    def end_trace(
        self,
        trace_id: str,
        outcome: str = "success",
        error_message: str = None,
    ):
        """Complete a trace with an outcome."""
        trace = self._active_traces.pop(trace_id, None)
        if trace is None:
            logger.warning(f"Trace {trace_id} not found for completion")
            return

        try:
            trace_outcome = TraceOutcome(outcome)
        except ValueError:
            trace_outcome = TraceOutcome.ERROR

        trace.complete(trace_outcome, error_message)

        # Store in completed list
        self._completed_traces.append(trace)
        if len(self._completed_traces) > self._max_completed:
            self._completed_traces = self._completed_traces[-self._max_completed:]

        # Persist to SQLite
        self._persist_trace(trace)
        logger.debug(
            f"Trace completed: {trace_id} outcome={outcome} "
            f"hops={len(trace.hops)} latency={trace.total_latency_ms:.1f}ms"
        )

    def _persist_trace(self, trace: Trace):
        """Persist a trace to SQLite."""
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO traces
                    (trace_id, event_id, event_type, source, outcome,
                     total_latency_ms, hop_count, trace_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        trace.trace_id,
                        trace.event_id,
                        trace.event_type,
                        trace.source,
                        trace.outcome.value,
                        trace.total_latency_ms,
                        len(trace.hops),
                        json.dumps(trace.model_dump(), default=str),
                        trace.started_at.isoformat(),
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to persist trace: {e}")

    # ─── Query Methods ───────────────────────────────────────────────────

    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get a full trace by ID (active or completed)."""
        # Check active
        trace = self._active_traces.get(trace_id)
        if trace:
            return trace.model_dump()

        # Check completed (recent)
        for t in reversed(self._completed_traces):
            if t.trace_id == trace_id:
                return t.model_dump()

        # Check SQLite
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT trace_json FROM traces WHERE trace_id = ?", (trace_id,)
            ).fetchone()
            if row:
                return json.loads(row["trace_json"])

        return None

    def get_active_traces(self) -> List[Dict[str, Any]]:
        """Get all currently active (in-flight) traces."""
        return [t.model_dump() for t in self._active_traces.values()]

    def get_traces_by_observer(self, observer_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all traces that passed through a specific observer."""
        results = []
        for trace in reversed(self._completed_traces):
            if any(h.observer_id == observer_id for h in trace.hops):
                results.append(trace.model_dump())
                if len(results) >= limit:
                    break
        return results

    def search_traces(
        self,
        event_type: Optional[str] = None,
        outcome: Optional[str] = None,
        source: Optional[str] = None,
        min_latency_ms: Optional[float] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Search traces with filters."""
        # Build SQL query dynamically
        conditions = []
        params = []

        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)
        if outcome:
            conditions.append("outcome = ?")
            params.append(outcome)
        if source:
            conditions.append("source = ?")
            params.append(source)
        if min_latency_ms is not None:
            conditions.append("total_latency_ms >= ?")
            params.append(min_latency_ms)

        where = " AND ".join(conditions) if conditions else "1=1"
        params.append(limit)

        results = []
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    f"SELECT trace_json FROM traces WHERE {where} ORDER BY created_at DESC LIMIT ?",
                    params,
                ).fetchall()
                for row in rows:
                    results.append(json.loads(row["trace_json"]))
        except Exception as e:
            logger.error(f"Trace search failed: {e}")

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get tracing statistics."""
        total_active = len(self._active_traces)
        total_completed = len(self._completed_traces)

        # Compute avg latency from recent completed
        recent = self._completed_traces[-100:]
        avg_latency = (
            sum(t.total_latency_ms for t in recent) / len(recent)
            if recent
            else 0.0
        )

        # Outcome distribution
        outcomes: Dict[str, int] = {}
        for t in self._completed_traces[-500:]:
            key = t.outcome.value
            outcomes[key] = outcomes.get(key, 0) + 1

        return {
            "active_traces": total_active,
            "completed_traces": total_completed,
            "avg_latency_ms": round(avg_latency, 2),
            "outcome_distribution": outcomes,
            "ttl_sec": self._ttl_sec,
        }

    def expire_old_traces(self):
        """Remove traces older than TTL from active and completed."""
        cutoff = time.time() - self._ttl_sec
        # Expire active
        expired_active = [
            tid
            for tid, t in self._active_traces.items()
            if t.started_at.timestamp() < cutoff
        ]
        for tid in expired_active:
            trace = self._active_traces.pop(tid)
            trace.complete(TraceOutcome.TIMEOUT, "Trace expired (TTL)")
            self._completed_traces.append(trace)
            self._persist_trace(trace)

        # Trim completed
        if len(self._completed_traces) > self._max_completed:
            self._completed_traces = self._completed_traces[-self._max_completed:]

        if expired_active:
            logger.info(f"Expired {len(expired_active)} old traces")


# ─── Singleton Access ───────────────────────────────────────────────────────

def get_tracing_engine() -> TracingEngine:
    """Get the singleton TracingEngine instance."""
    return TracingEngine()
