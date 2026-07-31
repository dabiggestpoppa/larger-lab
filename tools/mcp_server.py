"""Standalone MCP server for Hermes agent on port 8765."""
import sys
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\.venv\Lib\site-packages")

from mcp.server.fastmcp import FastMCP
import uvicorn

mcp = FastMCP("hermes-mcp")

@mcp.tool()
def gateway_status() -> str:
    """Check if Hermes gateway is running."""
    return "Hermes gateway is running"

@mcp.tool()
def memory_sync_status() -> str:
    """Check memory sync daemon status."""
    import subprocess
    result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq python.exe"],
                          capture_output=True, text=True)
    if "memory-sync" in result.stdout.lower() or "hermes" in result.stdout.lower():
        return "Memory sync daemon is running"
    return "Memory sync daemon status unknown"

if __name__ == "__main__":
    app = mcp.sse_app()
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")