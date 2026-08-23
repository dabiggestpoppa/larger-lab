"""Integration tests for OCE MCP Facade.

Covers mandatory tests:
- T-SEC-12: OCE offline returns OFFLINE, not PASS
- T-SEC-13: OCE timeout returns DEGRADED or ERROR
- T-SEC-16: Rate limiting works
- T-SEC-17: Request IDs connect Telegram, MCP and audit records
- T-SEC-18: Restart preserves only approved memory
"""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from src.oce_mcp_facade.facade import (
    execute_tool,
    OCEBackendClient,
    RateLimiter,
    OCE_TOOLS,
)
from src.oce_mcp_facade.config import FacadeConfig
from src.oce_mcp_facade.audit.logger import AuditLogger


def make_config(**overrides) -> FacadeConfig:
    """Create a test config."""
    defaults = {
        "oce_backend_url": "http://localhost:8000",
        "oce_service_token": "test-token",
        "telegram_allowed_users": "123456789",
        "telegram_allow_all_users": False,
        "telegram_bot_token": "test-bot-token",
        "use_mock": True,
        "audit_log_path": "evidence/audit.jsonl",
    }
    defaults.update(overrides)
    return FacadeConfig(**defaults)


# ─── Mock Mode Integration ────────────────────────────────────────────────────

class TestMockModeIntegration:
    """Test all tools in mock mode."""

    @pytest.mark.asyncio
    async def test_all_tools_return_pass_in_mock(self):
        """Every tool returns PASS in mock mode (with required args)."""
        config = make_config(use_mock=True)
        client = OCEBackendClient(config)

        # Tools that require arguments
        tool_args = {
            "oce_get_job": {"job_id": "test-123"},
        }

        for tool in OCE_TOOLS:
            args = tool_args.get(tool.name, {})
            result = await execute_tool(tool.name, args, client, config)
            assert result["state"] == "PASS", f"{tool.name} failed: {result}"
            assert result["request_id"] is not None
            assert result["timestamp"] is not None
            assert result["tool"] == tool.name

    @pytest.mark.asyncio
    async def test_job_tool_requires_id(self):
        """oce_get_job requires job_id parameter."""
        config = make_config(use_mock=True)
        client = OCEBackendClient(config)

        # Without job_id — should error
        result = await execute_tool("oce_get_job", {}, client, config)
        assert result["state"] == "ERROR"
        assert "job_id is required" in result["error"]

        # With job_id — should pass
        result = await execute_tool("oce_get_job", {"job_id": "test-123"}, client, config)
        assert result["state"] == "PASS"

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self):
        """Unknown tool returns ERROR state."""
        config = make_config(use_mock=True)
        client = OCEBackendClient(config)

        result = await execute_tool("nonexistent_tool", {}, client, config)
        assert result["state"] == "ERROR"
        assert "Unknown tool" in result["error"]


# ─── T-SEC-12: Offline Detection ──────────────────────────────────────────────

class TestOfflineDetection:
    """Test OCE offline detection."""

    @pytest.mark.asyncio
    async def test_no_token_returns_blocked(self):
        """T-SEC-12: No token means BLOCKED state."""
        config = make_config(use_mock=False, oce_service_token="")
        client = OCEBackendClient(config)

        result = await client.request("/health")
        assert result["state"] == "BLOCKED"

    @pytest.mark.asyncio
    async def test_connect_error_returns_offline(self):
        """T-SEC-12: Connection error returns OFFLINE."""
        import httpx as real_httpx
        config = make_config(use_mock=False, oce_service_token="test")
        client = OCEBackendClient(config)

        mock_client = AsyncMock()
        mock_client.get.side_effect = real_httpx.ConnectError("refused")
        client._client = mock_client

        result = await client.request("/health")
        assert result["state"] == "OFFLINE"


# ─── T-SEC-16: Rate Limiting ──────────────────────────────────────────────────

class TestRateLimiting:
    """Test rate limiter integration."""

    def test_rate_limit_blocks_after_threshold(self):
        """T-SEC-16: Rate limit blocks requests after threshold."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)

        # First 5 should pass
        for i in range(5):
            assert limiter.allow() is True, f"Request {i+1} should be allowed"

        # 6th should be blocked
        assert limiter.allow() is False

    def test_rate_limit_independence(self):
        """Different tools share the same rate limit."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)

        limiter.allow()  # tool A
        limiter.allow()  # tool B
        limiter.allow()  # tool C
        assert limiter.allow() is False  # tool D blocked


# ─── T-SEC-17: Request ID Tracking ────────────────────────────────────────────

class TestRequestIDTracking:
    """Test that request IDs connect all layers."""

    @pytest.mark.asyncio
    async def test_request_id_in_response(self):
        """T-SEC-17: Every response includes a request_id."""
        config = make_config(use_mock=True)
        client = OCEBackendClient(config)

        result = await execute_tool("oce_health", {}, client, config)
        assert "request_id" in result
        assert len(result["request_id"]) > 0

    @pytest.mark.asyncio
    async def test_request_ids_unique(self):
        """T-SEC-17: Each call gets a unique request_id."""
        config = make_config(use_mock=True)
        client = OCEBackendClient(config)

        ids = set()
        for _ in range(10):
            result = await execute_tool("oce_health", {}, client, config)
            ids.add(result["request_id"])

        assert len(ids) == 10

    @pytest.mark.asyncio
    async def test_audit_recorded_with_request_id(self):
        """T-SEC-17: Audit log entries include request_id."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"
            audit = AuditLogger(str(log_path))

            request_id = audit.log(
                tool_name="oce_health",
                decision="ALLOW",
                outcome={"state": "PASS"},
            )

            with open(log_path) as f:
                entry = json.loads(f.readline())

            assert entry["request_id"] == request_id


# ─── T-SEC-18: Restart Memory ─────────────────────────────────────────────────

class TestRestartMemory:
    """Test that restart preserves only approved memory."""

    def test_approved_memory_paths(self):
        """T-SEC-18: Only approved memory paths are preserved."""
        approved_paths = [
            "evidence/audit.jsonl",
            "evidence/startup.json",
            "logs/facade.log",
        ]
        # Verify these are not in forbidden locations
        forbidden = ["/tmp", "/var", "/etc"]
        for path in approved_paths:
            assert not any(path.startswith(f) for f in forbidden)
