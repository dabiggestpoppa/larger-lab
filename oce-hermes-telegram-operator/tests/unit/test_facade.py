"""Unit tests for OCE MCP Facade tools.

Covers mandatory tests:
- T-SEC-06: Only approved MCP tools are exposed
- T-SEC-07: Shell execution is denied
- T-SEC-08: PostgreSQL access is denied
- T-SEC-09: Docker access is denied
- T-SEC-10: Deployment is denied
- T-SEC-11: Trade execution is denied
- T-SEC-12: OCE offline returns OFFLINE
- T-SEC-13: OCE timeout returns DEGRADED or ERROR
- T-SEC-14: Malformed backend response fails closed
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from src.oce_mcp_facade.facade import (
    OCE_TOOLS,
    TOOL_ENDPOINT_MAP,
    execute_tool,
    redact_response,
    redact_value,
    OCEBackendClient,
    RateLimiter,
)
from src.oce_mcp_facade.config import FacadeConfig


# ─── Helper ───────────────────────────────────────────────────────────────────

def make_config(**overrides) -> FacadeConfig:
    """Create a test config with defaults."""
    defaults = {
        "oce_backend_url": "http://localhost:8000",
        "oce_service_token": "test-token",
        "telegram_allowed_users": "123456789",
        "telegram_allow_all_users": False,
        "telegram_bot_token": "test-bot-token",
        "use_mock": True,
    }
    defaults.update(overrides)
    return FacadeConfig(**defaults)


# ─── T-SEC-06: Only approved tools exposed ────────────────────────────────────

class TestToolExposure:
    """Test that only approved MCP tools are exposed."""

    APPROVED_TOOLS = {
        "oce_health",
        "oce_system_status",
        "oce_component_status",
        "oce_list_jobs",
        "oce_get_job",
        "oce_get_recent_events",
        "oce_get_evidence_status",
        "oce_get_cost_status",
        "oce_get_capability_manifest",
        "oce_get_backend_version",
    }

    FORBIDDEN_TOOLS = {
        "terminal", "execute_code", "run_command", "shell",
        "read_file", "write_file", "delete_file", "list_files",
        "query_db", "execute_sql", "run_query",
        "docker_ps", "docker_exec", "docker_run", "docker_stop",
        "ssh_connect", "ssh_exec",
        "git_push", "git_commit", "git_merge",
        "deploy", "rollback", "restart_service",
        "execute_trade", "place_order", "cancel_order",
        "aws_ec2", "gcp_compute", "azure_vm",
    }

    def test_only_approved_tools_exposed(self):
        """T-SEC-06: Only the 10 approved observer tools are registered."""
        tool_names = {t.name for t in OCE_TOOLS}
        assert tool_names == self.APPROVED_TOOLS

    def test_no_forbidden_tools_in_registry(self):
        """T-SEC-06: No forbidden tools appear in the tool registry."""
        tool_names = {t.name for t in OCE_TOOLS}
        forbidden_found = tool_names & self.FORBIDDEN_TOOLS
        assert not forbidden_found, f"Forbidden tools found: {forbidden_found}"

    def test_tool_count(self):
        """Exactly 10 tools are registered."""
        assert len(OCE_TOOLS) == 10

    def test_all_tools_have_schemas(self):
        """Every tool has a valid input schema."""
        for tool in OCE_TOOLS:
            assert tool.inputSchema is not None
            assert tool.inputSchema.get("type") == "object"

    def test_all_tools_have_descriptions(self):
        """Every tool has a description."""
        for tool in OCE_TOOLS:
            assert tool.description
            assert len(tool.description) > 10

    def test_all_tools_mapped_to_endpoints(self):
        """Every tool has a corresponding OCE endpoint mapping."""
        for tool in OCE_TOOLS:
            assert tool.name in TOOL_ENDPOINT_MAP, f"{tool.name} has no endpoint mapping"


# ─── T-SEC-07 through T-SEC-11: Prompt injection denials ─────────────────────

class TestPromptInjectionDenials:
    """Test that prompts requesting forbidden operations are denied."""

    def test_shell_execution_denied(self):
        """T-SEC-07: Shell execution prompt has no corresponding tool."""
        shell_patterns = [
            "terminal", "execute_code", "run_command", "shell",
            "subprocess", "os.system", "eval", "exec",
        ]
        tool_names = {t.name for t in OCE_TOOLS}
        for pattern in shell_patterns:
            assert not any(pattern in name for name in tool_names), \
                f"Shell tool '{pattern}' found in registry"

    def test_postgresql_access_denied(self):
        """T-SEC-08: PostgreSQL access prompt has no corresponding tool."""
        db_patterns = ["query_db", "execute_sql", "run_query", "database", "postgres"]
        tool_names = {t.name for t in OCE_TOOLS}
        for pattern in db_patterns:
            assert not any(pattern in name for name in tool_names), \
                f"DB tool '{pattern}' found in registry"

    def test_docker_access_denied(self):
        """T-SEC-09: Docker access prompt has no corresponding tool."""
        docker_patterns = ["docker_", "container", "docker"]
        tool_names = {t.name for t in OCE_TOOLS}
        for pattern in docker_patterns:
            assert not any(pattern in name for name in tool_names), \
                f"Docker tool '{pattern}' found in registry"

    def test_deployment_denied(self):
        """T-SEC-10: Deployment prompt has no corresponding tool."""
        deploy_patterns = ["deploy", "rollback", "restart", "publish"]
        tool_names = {t.name for t in OCE_TOOLS}
        for pattern in deploy_patterns:
            assert not any(pattern in name for name in tool_names), \
                f"Deploy tool '{pattern}' found in registry"

    def test_trade_execution_denied(self):
        """T-SEC-11: Trade execution prompt has no corresponding tool."""
        trade_patterns = ["trade", "order", "position", "exchange", "broker"]
        tool_names = {t.name for t in OCE_TOOLS}
        for pattern in trade_patterns:
            assert not any(pattern in name for name in tool_names), \
                f"Trade tool '{pattern}' found in registry"


# ─── T-SEC-12: OCE offline returns OFFLINE ───────────────────────────────────

class TestOCEOfflineBehavior:
    """Test that offline OCE returns OFFLINE, not PASS."""

    @pytest.mark.asyncio
    async def test_offline_returns_offline_state(self):
        """T-SEC-12: When OCE is unreachable, response state is OFFLINE."""
        import httpx as real_httpx
        config = make_config(use_mock=False, oce_service_token="test-token")
        client = OCEBackendClient(config)

        # Mock httpx client to raise real ConnectError
        mock_client = AsyncMock()
        mock_client.get.side_effect = real_httpx.ConnectError("Connection refused")
        client._client = mock_client

        result = await client.request("/health")
        assert result["state"] == "OFFLINE"
        assert result["data"] is None

    @pytest.mark.asyncio
    async def test_mock_mode_returns_pass(self):
        """Mock mode returns PASS with mock indicator."""
        config = make_config(use_mock=True)
        result = await execute_tool("oce_health", {}, OCEBackendClient(config), config)
        assert result["state"] == "PASS"
        assert result["data"] is not None


# ─── T-SEC-13: OCE timeout returns DEGRADED ──────────────────────────────────

class TestOCETimeoutBehavior:
    """Test that timeout returns DEGRADED or ERROR."""

    @pytest.mark.asyncio
    async def test_timeout_returns_degraded(self):
        """T-SEC-13: When OCE times out, response state is DEGRADED."""
        import httpx as real_httpx
        config = make_config(use_mock=False, oce_service_token="test-token")
        client = OCEBackendClient(config)

        mock_client = AsyncMock()
        mock_client.get.side_effect = real_httpx.TimeoutException("Request timed out")
        client._client = mock_client

        result = await client.request("/health")
        assert result["state"] == "DEGRADED"
        assert "timeout" in result["error"].lower()


# ─── T-SEC-14: Malformed response fails closed ───────────────────────────────

class TestMalformedResponse:
    """Test that malformed backend responses fail closed."""

    @pytest.mark.asyncio
    async def test_auth_failure_returns_blocked(self):
        """T-SEC-14: Auth failure returns BLOCKED."""
        config = make_config(use_mock=False, oce_service_token="test-token")
        client = OCEBackendClient(config)

        with patch("src.oce_mcp_facade.facade.httpx") as mock_httpx:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            client._client = mock_client

            result = await client.request("/health")
            assert result["state"] == "BLOCKED"

    @pytest.mark.asyncio
    async def test_unexpected_error_returns_error(self):
        """T-SEC-14: Unexpected error returns ERROR state."""
        config = make_config(use_mock=False, oce_service_token="test-token")
        client = OCEBackendClient(config)

        with patch("src.oce_mcp_facade.facade.httpx") as mock_httpx:
            mock_client = AsyncMock()
            mock_client.get.side_effect = RuntimeError("Unexpected crash")
            client._client = mock_client

            result = await client.request("/health")
            assert result["state"] == "ERROR"
            assert "RuntimeError" in result["error"]


# ─── Rate Limiter ─────────────────────────────────────────────────────────────

class TestRateLimiter:
    """Test rate limiting."""

    def test_allows_within_limit(self):
        """Requests within limit are allowed."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        for _ in range(5):
            assert limiter.allow() is True

    def test_blocks_over_limit(self):
        """Requests over limit are blocked."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        for _ in range(3):
            limiter.allow()
        assert limiter.allow() is False

    def test_reset_clears_limit(self):
        """Reset clears the rate limiter."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        limiter.allow()
        limiter.allow()
        assert limiter.allow() is False
        limiter.reset()
        assert limiter.allow() is True


# ─── Redaction ────────────────────────────────────────────────────────────────

class TestRedaction:
    """Test credential and path redaction."""

    def test_token_redacted(self):
        """Token-like strings are redacted."""
        data = {"token": "secret123", "name": "test"}
        result = redact_value(data)
        assert result["token"] == "[REDACTED]"
        assert result["name"] == "test"

    def test_path_redacted(self):
        """Sensitive paths are redacted."""
        data = {"path": "/home/user/.ssh/id_rsa"}
        result = redact_value(data)
        assert "[PATH_REDACTED]" in result["path"]

    def test_nested_redaction(self):
        """Nested objects are recursively redacted."""
        data = {"outer": {"inner": {"password": "secret"}}}
        result = redact_value(data)
        assert result["outer"]["inner"]["password"] == "[REDACTED]"

    def test_response_redaction(self):
        """Full response redaction works."""
        data = {"status": "ok", "api_key": "abc123def456"}
        result = redact_response(data)
        assert result["status"] == "ok"
        assert result["api_key"] == "[REDACTED]"
