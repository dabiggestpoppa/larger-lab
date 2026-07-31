import sys, os, asyncio
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\.venv\Lib\site-packages")
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("hermes-mcp")

@mcp.tool()
def gateway_status() -> str:
    return "Hermes gateway is running"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mcp_server:app", host="127.0.0.1", port=8765, log_level="info")
