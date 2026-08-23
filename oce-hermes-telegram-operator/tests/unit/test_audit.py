"""Unit tests for the audit logger.

Covers mandatory test:
- T-SEC-17: Request IDs connect Telegram, MCP and audit records
"""

import json
import tempfile
from pathlib import Path
from src.oce_mcp_facade.audit.logger import AuditLogger


class TestAuditLogger:
    """Test structured audit logging."""

    def test_log_creates_entry(self):
        """Audit log creates a JSONL entry."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_audit.jsonl"
            logger = AuditLogger(str(log_path))

            request_id = logger.log(
                actor_id="123456789",
                chat_id="987654321",
                tool_name="oce_health",
                decision="ALLOW",
                latency_ms=42.5,
                outcome={"state": "PASS"},
            )

            assert request_id is not None
            assert log_path.exists()

            with open(log_path) as f:
                entry = json.loads(f.readline())

            assert entry["actor_id"] == "123456789"
            assert entry["chat_id"] == "987654321"
            assert entry["tool_name"] == "oce_health"
            assert entry["decision"] == "ALLOW"
            assert entry["latency_ms"] == 42.5
            assert entry["request_id"] == request_id
            assert "timestamp" in entry

    def test_request_id_unique(self):
        """Each log entry gets a unique request ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_audit.jsonl"
            logger = AuditLogger(str(log_path))

            ids = set()
            for _ in range(10):
                rid = logger.log(tool_name="test")
                ids.add(rid)

            assert len(ids) == 10

    def test_redacts_sensitive_data(self):
        """Sensitive data in outcomes is redacted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_audit.jsonl"
            logger = AuditLogger(str(log_path))

            logger.log(
                tool_name="test",
                outcome={"token": "secret123", "data": "safe"},
            )

            with open(log_path) as f:
                entry = json.loads(f.readline())

            assert entry["outcome"]["token"] == "[REDACTED]"
            assert entry["outcome"]["data"] == "safe"

    def test_multiple_entries_appended(self):
        """Multiple log entries are appended to the same file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_audit.jsonl"
            logger = AuditLogger(str(log_path))

            for i in range(5):
                logger.log(tool_name=f"tool_{i}")

            with open(log_path) as f:
                lines = f.readlines()

            assert len(lines) == 5

    def test_audit_decision_types(self):
        """All decision types are recorded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "test_audit.jsonl"
            logger = AuditLogger(str(log_path))

            for decision in ["ALLOW", "DENY", "ERROR", "RATE_LIMITED"]:
                logger.log(tool_name="test", decision=decision)

            with open(log_path) as f:
                entries = [json.loads(line) for line in f.readlines()]

            decisions = {e["decision"] for e in entries}
            assert decisions == {"ALLOW", "DENY", "ERROR", "RATE_LIMITED"}
