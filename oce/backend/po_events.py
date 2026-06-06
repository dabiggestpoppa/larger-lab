"""
PO Event Schema — canonical event types for PO × VTuber integration.

These events are emitted by the PO streaming layer and consumed by
the VTuber frontend (as status cards) and OCE event fabric (for telemetry).
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional


class POEventType(str, Enum):
    """Known PO event types."""
    STATUS = "status"
    WORKSPACE_SCAN = "workspace_scan"
    VAULT_RETRIEVAL = "vault_retrieval"
    AGENT_SPAWN = "agent_spawn"
    STREAM_CHUNK = "chunk"
    STREAM_DONE = "done"
    STREAM_ERROR = "error"
    STREAM_CANCELLED = "cancelled"


class POEvent:
    """Base PO event."""

    def __init__(
        self,
        event_type: POEventType | str,
        ts: Optional[float] = None,
        **kwargs,
    ):
        self.type = event_type
        self.ts = ts  # will be set by stream generator
        self._extra = kwargs

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"type": self.type, "ts": self.ts}
        d.update(self._extra)
        return d


class StatusEvent(POEvent):
    """Stage indicator (thinking, scanning, etc.)."""

    def __init__(self, stage: str, message: str):
        super().__init__(POEventType.STATUS, stage=stage, message=message)


class WorkspaceScanEvent(POEvent):
    """Workspace scan results."""

    def __init__(self, files_scanned: int = 0, fresh: int = 0, patterns: list[str] | None = None):
        super().__init__(
            POEventType.WORKSPACE_SCAN,
            files_scanned=files_scanned,
            fresh=fresh,
            patterns=patterns or [],
        )


class VaultRetrievalEvent(POEvent):
    """Vault retrieval results."""

    def __init__(self, hits: int = 0, sources: list[str] | None = None):
        super().__init__(
            POEventType.VAULT_RETRIEVAL,
            hits=hits,
            sources=sources or [],
        )


class AgentSpawnEvent(POEvent):
    """Agent coordination event."""

    def __init__(self, agent: str, task: str, status: str = "spawned"):
        super().__init__(
            POEventType.AGENT_SPAWN,
            agent=agent,
            task=task,
            status=status,
        )


class StreamChunkEvent(POEvent):
    """LLM response chunk (OpenAI-shape for VTuber compat)."""

    def __init__(self, content: str, finish_reason: str | None = None):
        super().__init__(
            POEventType.STREAM_CHUNK,
            choices=[{"delta": {"content": content}}],
            finish_reason=finish_reason,
        )


class StreamDoneEvent(POEvent):
    """End of stream."""

    def __init__(self, usage: dict | None = None):
        super().__init__(
            POEventType.STREAM_DONE,
            usage=usage or {"prompt_tokens": 0, "completion_tokens": 0, "total": 0},
        )


class StreamErrorEvent(POEvent):
    """Stream error."""

    def __init__(self, message: str):
        super().__init__(POEventType.STREAM_ERROR, message=message)


class StreamCancelledEvent(POEvent):
    """Stream cancelled by user."""

    def __init__(self):
        super().__init__(POEventType.STREAM_CANCELLED)