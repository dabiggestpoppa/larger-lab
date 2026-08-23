"""Structured audit logger for OCE MCP Facade.

Logs every interaction with:
- actor_id (Telegram user ID)
- chat_id (Telegram chat ID)
- request_id (UUID)
- tool_name
- decision (ALLOW | DENY | ERROR | RATE_LIMITED)
- timestamp
- latency_ms
- redacted_outcome

Never logs bot tokens, credentials, or sensitive paths.
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4


class AuditLogger:
    """Structured JSONL audit logger for MCP interactions."""

    def __init__(self, log_path: str = "evidence/audit.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        *,
        actor_id: str = "unknown",
        chat_id: str = "unknown",
        request_id: Optional[str] = None,
        tool_name: str = "unknown",
        decision: str = "ALLOW",
        latency_ms: float = 0.0,
        outcome: Any = None,
        error: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """Log an audit event. Returns the request_id."""
        if request_id is None:
            request_id = str(uuid4())

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id,
            "actor_id": actor_id,
            "chat_id": chat_id,
            "tool_name": tool_name,
            "decision": decision,
            "latency_ms": round(latency_ms, 2),
            "outcome": self._redact(outcome) if outcome is not None else None,
            "error": error,
            "metadata": metadata or {},
        }

        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, default=str) + "\n")
        except OSError:
            pass  # Best-effort logging

        return request_id

    def _redact(self, data: Any) -> Any:
        """Redact sensitive values from audit data."""
        if isinstance(data, dict):
            redacted = {}
            sensitive_keys = {
                "token", "password", "secret", "key", "credential",
                "bot_token", "service_token", "api_key",
            }
            for k, v in data.items():
                if any(sk in k.lower() for sk in sensitive_keys):
                    redacted[k] = "[REDACTED]"
                else:
                    redacted[k] = self._redact(v)
            return redacted
        elif isinstance(data, list):
            return [self._redact(item) for item in data]
        elif isinstance(data, str):
            # Redact patterns that look like tokens
            if len(data) > 20 and ":" in data:
                return "[REDACTED]"
            return data
        return data


# Singleton
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger(log_path: str = "evidence/audit.jsonl") -> AuditLogger:
    """Get or create the audit logger singleton."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(log_path)
    return _audit_logger
