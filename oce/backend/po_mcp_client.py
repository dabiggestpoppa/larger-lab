"""
PO MCP Client — Bridge to Model Context Protocol servers.

Connects PO to all available MCP servers in the workspace, dynamically
discovers their tools, and exposes them through OCE's agent infrastructure.

MCP servers in workspace:
  - time (mcp-server-time) — timezone-aware time
  - ddg-search (duckduckgo-mcp-server) — web search
  - hermes-mcp (local, port 8765) — gateway status, memory sync

Plus any MCP servers configured in:
  - .vscode/mcp.json (VS Code MCP config)
  - vtuber_integration/Open-LLM-VTuber/mcp_servers.json
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.po_mcp")

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class MCPTool:
    """A tool exposed by an MCP server."""
    server_name: str
    name: str
    description: str
    input_schema: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    url: Optional[str] = None  # For HTTP/SSE servers


# ─── Known MCP Server Configurations ────────────────────────────────────────

BUILTIN_MCP_SERVERS: List[MCPServerConfig] = [
    MCPServerConfig(
        name="time",
        command="uvx",
        args=["mcp-server-time", "--local-timezone=Asia/Shanghai"],
    ),
    MCPServerConfig(
        name="ddg-search",
        command="uvx",
        args=["duckduckgo-mcp-server"],
    ),
    MCPServerConfig(
        name="hermes-mcp",
        command="python",
        args=[str(REPO_ROOT / "tools" / "mcp_server.py")],
    ),
]


def _discover_vscode_mcp_servers() -> List[MCPServerConfig]:
    """Discover MCP servers from VS Code settings."""
    configs: List[MCPServerConfig] = []

    # Check .vscode/mcp.json
    mcp_json = REPO_ROOT / ".vscode" / "mcp.json"
    if mcp_json.exists():
        try:
            data = json.loads(mcp_json.read_text(encoding="utf-8"))
            for name, server in data.get("servers", {}).items():
                configs.append(MCPServerConfig(
                    name=name,
                    command=server.get("command", ""),
                    args=server.get("args", []),
                    env=server.get("env", {}),
                    url=server.get("url"),
                ))
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse .vscode/mcp.json: {e}")

    return configs


def _discover_vtuber_mcp_servers() -> List[MCPServerConfig]:
    """Discover MCP servers from VTuber integration."""
    configs: List[MCPServerConfig] = []
    vtuber_mcp = REPO_ROOT / "vtuber_integration" / "Open-LLM-VTuber" / "mcp_servers.json"
    if vtuber_mcp.exists():
        try:
            data = json.loads(vtuber_mcp.read_text(encoding="utf-8"))
            for name, server in data.get("mcp_servers", {}).items():
                configs.append(MCPServerConfig(
                    name=name,
                    command=server.get("command", ""),
                    args=server.get("args", []),
                    env=server.get("env", {}),
                ))
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse vtuber mcp_servers.json: {e}")

    return configs


class MCPClient:
    """
    Lightweight MCP client that communicates with MCP servers via stdio.

    Implements the MCP protocol (JSON-RPC 2.0 over stdio) for tool
    discovery and invocation.
    """

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self._tools: List[MCPTool] = []
        self._connected = False
        self._request_id = 0

    async def connect(self) -> bool:
        """Start the MCP server process and initialize the connection."""
        try:
            cmd = [self.config.command] + self.config.args
            env = os.environ.copy()
            env.update(self.config.env)

            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                cwd=str(REPO_ROOT),
                encoding="utf-8",
            )

            # Send initialize request
            self._request_id += 1
            init_req = {
                "jsonrpc": "2.0",
                "id": self._request_id,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "oce-po", "version": "1.0.0"},
                },
            }
            self._send(init_req)
            response = await self._receive()

            if response and "result" in response:
                self._connected = True
                logger.info(f"MCP server '{self.config.name}' connected")
                return True
            else:
                logger.warning(f"MCP server '{self.config.name}' init failed: {response}")
                return False

        except Exception as e:
            logger.error(f"MCP connect error for '{self.config.name}': {e}")
            return False

    async def list_tools(self) -> List[MCPTool]:
        """List all tools available from this MCP server."""
        if not self._connected:
            return []

        try:
            self._request_id += 1
            req = {
                "jsonrpc": "2.0",
                "id": self._request_id,
                "method": "tools/list",
                "params": {},
            }
            self._send(req)
            response = await self._receive()

            if response and "result" in response:
                tools = []
                for t in response["result"].get("tools", []):
                    tools.append(MCPTool(
                        server_name=self.config.name,
                        name=t["name"],
                        description=t.get("description", ""),
                        input_schema=t.get("inputSchema", {}),
                    ))
                self._tools = tools
                return tools
        except Exception as e:
            logger.error(f"MCP list_tools error for '{self.config.name}': {e}")

        return []

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on this MCP server."""
        if not self._connected:
            return {"error": f"Server '{self.config.name}' not connected"}

        try:
            self._request_id += 1
            req = {
                "jsonrpc": "2.0",
                "id": self._request_id,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments},
            }
            self._send(req)
            response = await self._receive()

            if response and "result" in response:
                return response["result"]
            elif response and "error" in response:
                return {"error": response["error"]}
            else:
                return {"error": "No response from MCP server"}
        except Exception as e:
            logger.error(f"MCP call_tool error for '{self.config.name}/{tool_name}': {e}")
            return {"error": str(e)}

    def _send(self, message: Dict[str, Any]):
        """Send a JSON-RPC message to the server."""
        if self.process and self.process.stdin:
            line = json.dumps(message)
            self.process.stdin.write(line + "\n")
            self.process.stdin.flush()

    async def _receive(self, timeout: float = 10.0) -> Optional[Dict[str, Any]]:
        """Receive a JSON-RPC response from the server."""
        if not self.process or not self.process.stdout:
            return None

        try:
            # Use asyncio to read without blocking
            loop = asyncio.get_event_loop()
            line = await asyncio.wait_for(
                loop.run_in_executor(None, self.process.stdout.readline),
                timeout=timeout,
            )
            if line:
                return json.loads(line.strip())
        except asyncio.TimeoutError:
            logger.warning(f"MCP receive timeout for '{self.config.name}'")
        except Exception as e:
            logger.error(f"MCP receive error for '{self.config.name}': {e}")

        return None

    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                self.process.kill()
            self.process = None
        self._connected = False


class MCPToolRegistry:
    """
    Registry of all MCP tools across all configured servers.

    Provides a unified interface for PO to discover and call any MCP tool.
    """

    def __init__(self):
        self._servers: Dict[str, MCPClient] = {}
        self._tools: Dict[str, MCPTool] = {}  # "server/tool" -> MCPTool
        self._configs: List[MCPServerConfig] = []

    def discover_servers(self):
        """Discover all MCP server configurations."""
        self._configs = []
        self._configs.extend(BUILTIN_MCP_SERVERS)
        self._configs.extend(_discover_vscode_mcp_servers())
        self._configs.extend(_discover_vtuber_mcp_servers())
        logger.info(f"Discovered {len(self._configs)} MCP server configs")

    async def connect_all(self):
        """Connect to all discovered MCP servers."""
        for config in self._configs:
            client = MCPClient(config)
            if await client.connect():
                tools = await client.list_tools()
                self._servers[config.name] = client
                for tool in tools:
                    key = f"{config.name}/{tool.name}"
                    self._tools[key] = tool
                logger.info(f"MCP server '{config.name}': {len(tools)} tools")
            else:
                logger.warning(f"Failed to connect MCP server '{config.name}'")

    def list_all_tools(self) -> List[Dict[str, Any]]:
        """List all available MCP tools."""
        return [
            {
                "key": key,
                "server": tool.server_name,
                "name": tool.name,
                "description": tool.description,
                "schema": tool.input_schema,
            }
            for key, tool in self._tools.items()
        ]

    async def call_tool(self, server: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific MCP tool."""
        client = self._servers.get(server)
        if not client:
            return {"error": f"MCP server '{server}' not connected"}
        return await client.call_tool(tool_name, arguments)

    async def disconnect_all(self):
        """Disconnect from all MCP servers."""
        for client in self._servers.values():
            await client.disconnect()
        self._servers.clear()
        self._tools.clear()
