#!/usr/bin/env python3
"""
Pre-Tool-Use Hook
Validates commands against a denylist before execution.
Receives JSON via stdin, returns JSON via stdout.
"""

import json
import sys
import re

# Denylist: regex patterns for dangerous commands
DENYLIST = [
    r"rm\s+-rf\s+/",
    r"rm\s+-rf\s+~",
    r"rm\s+-rf\s+\*",
    r"format\s+[a-zA-Z]:",
    r"del\s+/[sfq]\s+.*\\",
    r"Remove-Item\s+.*-Recurse\s+.*-Force",
    r"shutdown\s+/[sr]",
    r"Stop-Computer",
    r"Clear-Disk",
    r"Reset-ComputerMachinePassword",
    r"Invoke-Expression\s+.*http",
    r"iex\s+.*http",
    r"curl\s+.*\|\s*(bash|sh|powershell)",
    r"wget\s+.*\|\s*(bash|sh|powershell)",
    r"pip\s+install\s+--break-system-packages",
    r"--no-sandbox",
    r"chmod\s+777\s+/",
    r"chown\s+-R\s+root",
    r"mkfs\.",
    r"dd\s+if=.*of=/dev/",
    r">\s*/dev/sda",
    r":\(\)\{\s*:\|\:&\s*\};:",  # fork bomb
]

COMPILED_DENYLIST = [re.compile(p, re.IGNORECASE) for p in DENYLIST]


def validate_command(command: str) -> dict:
    """Check command against denylist. Returns result dict."""
    if not command or not isinstance(command, str):
        return {"allowed": True, "reason": "empty or invalid command"}

    for pattern in COMPILED_DENYLIST:
        if pattern.search(command):
            return {
                "allowed": False,
                "reason": f"Command matches denylist pattern: {pattern.pattern}",
                "command": command[:200],  # truncate for safety
            }

    return {"allowed": True, "reason": "passed denylist check"}


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            print(json.dumps({"allowed": True, "reason": "no input"}))
            sys.exit(0)

        data = json.loads(raw)
        command = data.get("command", "")

        result = validate_command(command)
        print(json.dumps(result))
        sys.exit(0 if result["allowed"] else 1)

    except json.JSONDecodeError as e:
        print(json.dumps({"allowed": False, "reason": f"invalid JSON input: {e}"}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"allowed": False, "reason": f"hook error: {e}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
