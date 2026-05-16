#!/usr/bin/env python3
"""
claude_hermes_mcp.py — CLI wrapper for claude-hermes-mcp

MCP bridge that lets Claude Desktop/mobile delegate tasks to a local Hermes Agent.

Usage:
    python tools/claude_hermes_mcp.py doctor
    python tools/claude_hermes_mcp.py mint-client
    python tools/claude_hermes_mcp.py serve
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, check=True):
    """Run a shell command."""
    result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
    return result.stdout.strip() if result.stdout else ""

def doctor():
    """Run hermes-mcp doctor to verify setup."""
    print("Running hermes-mcp doctor...")
    try:
        result = run_cmd("hermes-mcp doctor", check=False)
        print(result)
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure hermes-mcp is installed: pipx install hermes-mcp")

def mint_client():
    """Generate OAuth client credentials."""
    print("Generating OAuth client credentials...")
    try:
        result = run_cmd("hermes-mcp mint-client", check=False)
        print(result)
    except Exception as e:
        print(f"Error: {e}")

def serve():
    """Start the MCP server."""
    print("Starting hermes-mcp server...")
    print("Make sure these env vars are set:")
    print("  OAUTH_CLIENT_ID")
    print("  OAUTH_CLIENT_SECRET")
    print("  OAUTH_ISSUER_URL")
    print("  HERMES_API_KEY")
    try:
        run_cmd("hermes-mcp serve", check=False)
    except Exception as e:
        print(f"Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Claude Hermes MCP wrapper")
    parser.add_argument("command", choices=["doctor", "mint-client", "serve"],
                       help="Command to run")
    args = parser.parse_args()
    
    if args.command == "doctor":
        doctor()
    elif args.command == "mint-client":
        mint_client()
    elif args.command == "serve":
        serve()

if __name__ == "__main__":
    main()