#!/usr/bin/env python
"""Launch Hermes MCP server from workspace venv (has mcp package)."""
import sys, os

# Add AppData hermes to path for hermes_constants, hermes_state etc.
sys.path.insert(0, r"C:\Users\wifik\AppData\Local\hermes\hermes-agent")
# Add workspace venv site-packages for mcp package
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\.venv\Lib\site-packages")

# Now run the mcp_serve from AppData
exec(open(r"C:\Users\wifik\AppData\Local\hermes\hermes-agent\mcp_serve.py").read())