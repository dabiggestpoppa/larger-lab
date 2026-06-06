#!/usr/bin/env python
"""Standalone Hermes MCP server using workspace venv's mcp package."""
import sys, os, asyncio

# Ensure workspace venv packages are available
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\.venv\Lib\site-packages")
# Ensure hermes agent modules are available
sys.path.insert(0, r"C:\Users\wifik\AppData\Local\hermes\hermes-agent")

from mcp.server.fastmcp import FastMCP

async def main():
    mcp = FastMCP("hermes-mcp")

    @mcp.tool()
    def hello(name: str = "world") -> str:
        return f"Hello, {name}!"

    @mcp.tool()
    def gateway_status() -> str:
        import urllib.request
        try:
            req = urllib.request.Request("http://127.0.0.1:8642/api/v1/status")
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.read().decode()
        except Exception as e:
            return f"Gateway check: {e}"

    await mcp.run(transport="stdio")

if __name__ == "__main__":
    asyncio.run(main())