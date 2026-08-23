"""OCE MCP Facade Server — Read-only observer tools for Hermes Agent.

This server implements the MCP (Model Context Protocol) and exposes exactly
10 read-only tools that query the OCE backend. No write operations, no
arbitrary execution, no direct database access.

Transport: stdio (subprocess mode for Hermes integration)
"""

import asyncio
import json
import os
import sys
import time
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

# MCP SDK
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        TextContent,
        CallToolResult,
    )
    HAS_MCP_SDK = True
except ImportError:
    HAS_MCP_SDK = False

# HTTP client for OCE backend
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

from .config import FacadeConfig
from .audit.logger import get_audit_logger

logger = logging.getLogger("oce.mcp.facade")


# ─── Mock Data ────────────────────────────────────────────────────────────────

MOCK_DATA = {
    "/health": {"status": "healthy", "service": "oce-continuity-core", "mock": True},
    "/": {"message": "OCE Continuity Core API (MOCK)", "version": "0.0.0-mock", "mock": True},
    "/observers": [],
    "/execution/tasks": [],
    "/events": [],
    "/events?limit=20": [],
    "/execution/stats": {
        "total_tasks": 0,
        "success_rate": 0.0,
        "active_workers": 0,
        "mock": True,
    },
    "/execution/analytics": {
        "total_cost": 0.0,
        "period": "mock",
        "api_calls": 0,
        "mock": True,
    },
    "/evolution/status": {
        "status": "mock",
        "capabilities": [],
        "version": "0.0.0",
        "mock": True,
    },
}


# ─── Redaction ────────────────────────────────────────────────────────────────

SENSITIVE_PATTERNS = [
    "token", "password", "secret", "key", "credential",
    "bot_token", "service_token", "api_key", "auth",
]

SENSITIVE_PATH_COMPONENTS = [
    "home", "Users", ".ssh", ".env", ".hermes", "secrets",
]


def redact_value(value: Any) -> Any:
    """Redact sensitive values recursively."""
    if isinstance(value, dict):
        redacted = {}
        for k, v in value.items():
            k_lower = k.lower()
            if any(p in k_lower for p in SENSITIVE_PATTERNS):
                redacted[k] = "[REDACTED]"
            else:
                redacted[k] = redact_value(v)
        return redacted
    elif isinstance(value, list):
        return [redact_value(item) for item in value]
    elif isinstance(value, str):
        # Redact absolute paths
        if value.startswith("/") or (len(value) > 2 and value[1] == ":"):
            parts = value.replace("\\", "/").split("/")
            if any(p in SENSITIVE_PATH_COMPONENTS for p in parts):
                return f"[PATH_REDACTED]/{parts[-1]}"
        # Redact token-like strings
        if len(value) > 30 and ":" in value:
            return "[REDACTED]"
        return value
    return value


def redact_response(data: Any) -> Any:
    """Apply redaction rules to OCE response data."""
    return redact_value(data)


# ─── Tool Definitions ─────────────────────────────────────────────────────────

OCE_TOOLS = [
    Tool(
        name="oce_health",
        description="Check OCE backend health status. Returns PASS if healthy, OFFLINE if unreachable.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    Tool(
        name="oce_system_status",
        description="Get overall OCE system status including version and service info.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    Tool(
        name="oce_component_status",
        description="Get status of individual OCE components (observers, engines).",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    Tool(
        name="oce_list_jobs",
        description="List recent OCE execution tasks/jobs with their current status.",
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of jobs to return (default: 20)",
                    "minimum": 1,
                    "maximum": 100,
                }
            },
            "required": [],
        },
    ),
    Tool(
        name="oce_get_job",
        description="Get detailed information about a specific OCE job by its ID.",
        inputSchema={
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "The unique job identifier",
                }
            },
            "required": ["job_id"],
        },
    ),
    Tool(
        name="oce_get_recent_events",
        description="Get recent OCE system events with timestamps and types.",
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of events to return (default: 20)",
                    "minimum": 1,
                    "maximum": 100,
                }
            },
            "required": [],
        },
    ),
    Tool(
        name="oce_get_evidence_status",
        description="Get validation evidence status and execution statistics.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    Tool(
        name="oce_get_cost_status",
        description="Get cost analytics and usage data for OCE operations.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    Tool(
        name="oce_get_capability_manifest",
        description="Get the system capability manifest and evolution status.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    Tool(
        name="oce_get_backend_version",
        description="Get the OCE backend version information.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
]

# Map tool names to OCE endpoints
TOOL_ENDPOINT_MAP = {
    "oce_health": "/health",
    "oce_system_status": "/",
    "oce_component_status": "/observers",
    "oce_list_jobs": "/execution/tasks",
    "oce_get_job": "/execution/tasks/{job_id}",
    "oce_get_recent_events": "/events",
    "oce_get_evidence_status": "/execution/stats",
    "oce_get_cost_status": "/execution/analytics",
    "oce_get_capability_manifest": "/evolution/status",
    "oce_get_backend_version": "/",
}


# ─── Rate Limiter ─────────────────────────────────────────────────────────────

class RateLimiter:
    """Simple sliding window rate limiter."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: list[float] = []

    def allow(self) -> bool:
        """Check if a request is allowed under the rate limit."""
        now = time.time()
        cutoff = now - self.window_seconds
        self._requests = [t for t in self._requests if t > cutoff]
        if len(self._requests) >= self.max_requests:
            return False
        self._requests.append(now)
        return True

    def reset(self):
        """Reset the rate limiter."""
        self._requests.clear()


# ─── OCE Backend Client ──────────────────────────────────────────────────────

class OCEBackendClient:
    """Client for communicating with the OCE backend API."""

    def __init__(self, config: FacadeConfig):
        self.config = config
        self.base_url = config.oce_backend_url.rstrip("/")
        self.token = config.oce_service_token
        self.timeout = config.oce_request_timeout
        self._client: Optional[Any] = None

    async def _get_client(self) -> Any:
        """Get or create HTTP client."""
        if self._client is None and HAS_HTTPX:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bearer {self.token}" if self.token else "",
                    "Accept": "application/json",
                },
            )
        return self._client

    async def request(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Make a request to the OCE backend.

        Returns:
            dict with 'state', 'data', 'error', 'latency_ms'

        States:
            - PASS: Successful response
            - OFFLINE: Backend unreachable
            - DEGRADED: Partial data
            - ERROR: Unexpected failure
            - BLOCKED: Auth failure
        """
        start = time.time()

        if not self.token:
            return {
                "state": "BLOCKED",
                "data": None,
                "error": "No OCE service token configured",
                "latency_ms": 0,
            }

        try:
            client = await self._get_client()
            if client is None:
                return {
                    "state": "OFFLINE",
                    "data": None,
                    "error": "HTTP client not available (install httpx)",
                    "latency_ms": round((time.time() - start) * 1000, 2),
                }

            response = await client.get(endpoint, params=params)
            latency_ms = round((time.time() - start) * 1000, 2)

            if response.status_code == 200:
                data = response.json()
                return {
                    "state": "PASS",
                    "data": data,
                    "error": None,
                    "latency_ms": latency_ms,
                }
            elif response.status_code == 401 or response.status_code == 403:
                return {
                    "state": "BLOCKED",
                    "data": None,
                    "error": f"OCE auth failure: {response.status_code}",
                    "latency_ms": latency_ms,
                }
            else:
                return {
                    "state": "ERROR",
                    "data": None,
                    "error": f"OCE returned {response.status_code}: {response.text[:200]}",
                    "latency_ms": latency_ms,
                }

        except Exception as e:
            latency_ms = round((time.time() - start) * 1000, 2)
            exc_name = type(e).__name__
            # Classify known httpx exceptions (works even when httpx is mocked)
            if "Timeout" in exc_name:
                return {
                    "state": "DEGRADED",
                    "data": None,
                    "error": f"OCE timeout after {self.timeout}s",
                    "latency_ms": latency_ms,
                }
            elif "Connect" in exc_name:
                return {
                    "state": "OFFLINE",
                    "data": None,
                    "error": f"Cannot connect to OCE at {self.base_url}",
                    "latency_ms": latency_ms,
                }
            else:
                return {
                    "state": "ERROR",
                    "data": None,
                    "error": f"Unexpected error: {exc_name}: {str(e)[:200]}",
                    "latency_ms": latency_ms,
                }

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# ─── Tool Executor ────────────────────────────────────────────────────────────

async def execute_tool(
    tool_name: str,
    arguments: dict,
    backend: OCEBackendClient,
    config: FacadeConfig,
) -> dict:
    """Execute an MCP tool and return structured result."""
    request_id = str(uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    backend_version = "unknown"

    # Resolve endpoint
    endpoint = TOOL_ENDPOINT_MAP.get(tool_name)
    if endpoint is None:
        return {
            "state": "ERROR",
            "request_id": request_id,
            "timestamp": timestamp,
            "backend_version": backend_version,
            "tool": tool_name,
            "data": None,
            "error": f"Unknown tool: {tool_name}",
        }

    # Handle endpoint with parameters
    if "{job_id}" in endpoint:
        job_id = arguments.get("job_id", "")
        if not job_id:
            return {
                "state": "ERROR",
                "request_id": request_id,
                "timestamp": timestamp,
                "backend_version": backend_version,
                "tool": tool_name,
                "data": None,
                "error": "job_id is required",
            }
        endpoint = endpoint.replace("{job_id}", job_id)

    # Handle query parameters
    params = {}
    if "limit" in arguments:
        params["limit"] = arguments["limit"]

    # Execute against backend or mock
    if config.use_mock:
        result = _get_mock_response(tool_name, endpoint, arguments)
    else:
        result = await backend.request(endpoint, params=params if params else None)

    # Get backend version if available
    if result["data"] and isinstance(result["data"], dict):
        bv = result["data"].get("version", "")
        if bv:
            backend_version = bv

    # Apply redaction
    if result["data"]:
        result["data"] = redact_response(result["data"])

    return {
        "state": result["state"],
        "request_id": request_id,
        "timestamp": timestamp,
        "backend_version": backend_version,
        "tool": tool_name,
        "data": result["data"],
        "error": result.get("error"),
        "latency_ms": result.get("latency_ms", 0),
    }


def _get_mock_response(tool_name: str, endpoint: str, arguments: dict) -> dict:
    """Return mock data for a tool call."""
    # Normalize endpoint for mock lookup
    lookup_key = endpoint
    if "?" in endpoint:
        lookup_key = endpoint.split("?")[0]

    # Try exact match first
    data = MOCK_DATA.get(lookup_key)
    if data is None:
        # Try base endpoint
        data = MOCK_DATA.get(endpoint.split("?")[0])

    if data is None:
        return {
            "state": "PASS",
            "data": {"mock": True, "tool": tool_name, "message": "Mock response"},
            "error": None,
            "latency_ms": 1.0,
        }

    return {
        "state": "PASS",
        "data": data,
        "error": None,
        "latency_ms": 1.0,
    }


# ─── MCP Server ───────────────────────────────────────────────────────────────

def create_server(config: FacadeConfig) -> "Server":
    """Create and configure the MCP server."""
    if not HAS_MCP_SDK:
        raise RuntimeError(
            "MCP SDK not installed. Install with: pip install mcp"
        )

    server = Server("oce-observer")
    rate_limiter = RateLimiter(max_requests=config.rate_limit_per_minute)
    backend = OCEBackendClient(config)
    audit = get_audit_logger(config.audit_log_path)

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """Return the list of allowed MCP tools."""
        return OCE_TOOLS

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Execute an MCP tool call."""
        # Rate limit check
        if not rate_limiter.allow():
            audit.log(
                tool_name=name,
                decision="RATE_LIMITED",
                outcome={"error": "Rate limit exceeded"},
            )
            return [TextContent(
                type="text",
                text=json.dumps({
                    "state": "BLOCKED",
                    "error": "Rate limit exceeded. Try again later.",
                    "tool": name,
                }),
            )]

        start_time = time.time()
        result = await execute_tool(name, arguments, backend, config)
        latency_ms = (time.time() - start_time) * 1000

        # Audit log
        audit.log(
            tool_name=name,
            decision="ALLOW" if result["state"] in ("PASS", "DEGRADED") else result["state"],
            latency_ms=latency_ms,
            outcome={"state": result["state"], "tool": name},
        )

        return [TextContent(
            type="text",
            text=json.dumps(result, default=str),
        )]

    return server


# ─── Entry Point ──────────────────────────────────────────────────────────────

async def run_stdio(config: FacadeConfig):
    """Run the MCP server in stdio mode."""
    if not HAS_MCP_SDK:
        logger.error("MCP SDK not available. Running in standalone mode.")
        print(json.dumps({"error": "MCP SDK not installed"}, indent=2))
        sys.exit(1)

    server = create_server(config)

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main():
    """Main entry point for the OCE MCP Facade."""
    logging.basicConfig(
        level=getattr(logging, os.environ.get("LOG_LEVEL", "INFO")),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    config = FacadeConfig.from_env()

    logger.info("OCE MCP Facade starting...")
    logger.info(f"Backend URL: {config.oce_backend_url}")
    logger.info(f"Mock mode: {config.use_mock}")
    logger.info(f"Rate limit: {config.rate_limit_per_minute}/min")

    if HAS_MCP_SDK:
        asyncio.run(run_stdio(config))
    else:
        # Fallback: run as simple HTTP server
        logger.warning("MCP SDK not available, running in HTTP fallback mode")
        asyncio.run(run_http_fallback(config))


async def run_http_fallback(config: FacadeConfig):
    """HTTP fallback when MCP SDK is not available."""
    try:
        from aiohttp import web

        rate_limiter = RateLimiter(max_requests=config.rate_limit_per_minute)
        backend = OCEBackendClient(config)
        audit = get_audit_logger(config.audit_log_path)

        async def handle_tools(request):
            """List available tools."""
            tools = [
                {"name": t.name, "description": t.description, "inputSchema": t.inputSchema}
                for t in OCE_TOOLS
            ]
            return web.json_response({"tools": tools})

        async def handle_call(request):
            """Execute a tool."""
            if not rate_limiter.allow():
                return web.json_response(
                    {"error": "Rate limit exceeded"}, status=429
                )

            body = await request.json()
            tool_name = body.get("tool")
            arguments = body.get("arguments", {})

            result = await execute_tool(tool_name, arguments, backend, config)

            audit.log(
                tool_name=tool_name,
                decision="ALLOW" if result["state"] in ("PASS", "DEGRADED") else result["state"],
                latency_ms=result.get("latency_ms", 0),
                outcome={"state": result["state"]},
            )

            return web.json_response(result)

        app = web.Application()
        app.router.add_get("/tools", handle_tools)
        app.router.add_post("/call", handle_call)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 9090)
        await site.start()
        logger.info("OCE MCP Facade HTTP running on 127.0.0.1:9090")

        # Keep running
        await asyncio.Event().wait()

    except ImportError:
        logger.error("Neither MCP SDK nor aiohttp available. Install one.")
        sys.exit(1)


if __name__ == "__main__":
    main()
