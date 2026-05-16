#!/usr/bin/env python3
"""Python wrapper for beautiful-mermaid (npx-based)."""

import argparse
import subprocess
import sys
import json
from pathlib import Path


TOOL_NAME = "beautiful-mermaid"
NPX_CMD = "beautiful-mermaid"


def run_npx(args: list, json_output: bool = False) -> str:
    """Run the tool via npx."""
    cmd = ["npx", NPX_CMD] + args
    if json_output:
        cmd.append("--json")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr[:500]}", file=sys.stderr)
        sys.exit(result.returncode)
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description="<div align="center">")
    parser.add_argument("command", nargs="?", help="Command to run")
    parser.add_argument("args", nargs="*", help="Command arguments")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--help-tool", action="store_true", help="Show tool's own --help")

    args = parser.parse_args()

    if args.help_tool:
        print(run_npx(["--help"]))
        return

    if args.command:
        cmd_args = [args.command] + (args.args or [])
        output = run_npx(cmd_args, args.json)
    else:
        output = run_npx(["--help"])

    if args.output:
        Path(args.output).write_text(output)
        print(f"Output written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
