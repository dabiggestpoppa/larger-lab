#!/usr/bin/env python3
"""
Enhanced Pre-Tool-Use Hook
Validates commands against denylist AND blocks edits to generated/config files without approval.
Receives JSON via stdin, returns JSON via stdout.

Input JSON:
{
  "command": "rm -rf /",           # shell command (optional)
  "file_path": "config/app.json",  # file being edited (optional)
  "tool_name": "edit",             # tool being used (optional)
  "agent": "OC2"                   # agent name (optional)
}
"""

import json
import sys
import re
from pathlib import Path

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

# Protected file patterns: require explicit approval before editing
PROTECTED_PATTERNS = [
    r"\.openclaw.*\.json$",          # OpenClaw config
    r"config/.*\.(json|yaml|yml)$",  # Config files
    r"\.env$",                        # Environment files
    r"\.phase-state\.json$",         # Phase state
    r"\.agent-tags\.json$",          # Agent registry
    r"AGENTS\.md$",                  # Agent manifest
    r"SOUL\.md$",                    # Soul file
    r"IDENTITY\.md$",                # Identity file
    r"OPERATOR_RULES\.md$",          # Operator rules
    r".*\.generated\..*$",           # Generated files
    r".*\.min\.(js|css)$",           # Minified files
    r"node_modules/",                # Dependencies
    r"__pycache__/",                 # Python cache
    r"\.git/",                       # Git internals
]

COMPILED_PROTECTED = [re.compile(p, re.IGNORECASE) for p in PROTECTED_PATTERNS]


def validate_command(command: str) -> dict:
    """Check command against denylist."""
    if not command or not isinstance(command, str):
        return {"allowed": True, "reason": "empty or invalid command"}

    for pattern in COMPILED_DENYLIST:
        if pattern.search(command):
            return {
                "allowed": False,
                "reason": f"Command matches denylist pattern: {pattern.pattern}",
                "command": command[:200],
            }

    return {"allowed": True, "reason": "passed denylist check"}


def check_file_protection(file_path: str) -> dict:
    """Check if file is protected (config/generated)."""
    if not file_path or not isinstance(file_path, str):
        return {"protected": False, "reason": "no file_path"}

    for pattern in COMPILED_PROTECTED:
        if pattern.search(file_path):
            return {
                "protected": True,
                "reason": f"File matches protected pattern: {pattern.pattern}",
                "file_path": file_path,
                "action_required": "EXPLICIT_APPROVAL",
                "message": f"⚠️  {file_path} is a protected/config file. Explicit approval required before editing.",
            }

    return {"protected": False, "reason": "file is not protected"}


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            print(json.dumps({"allowed": True, "reason": "no input"}))
            sys.exit(0)

        data = json.loads(raw)
        command = data.get("command", "")
        file_path = data.get("file_path", "")
        tool_name = data.get("tool_name", "")

        # Check command denylist
        if command:
            cmd_result = validate_command(command)
            if not cmd_result["allowed"]:
                print(json.dumps({"allowed": False, "checks": {"command": cmd_result}}))
                sys.exit(1)

        # Check file protection (only for edit/write tools)
        if file_path and tool_name in ("edit", "write", "file_write"):
            file_result = check_file_protection(file_path)
            if file_result.get("protected"):
                print(json.dumps({
                    "allowed": False,
                    "checks": {"file_protection": file_result},
                    "message": file_result["message"],
                }))
                sys.exit(1)

        print(json.dumps({
            "allowed": True,
            "reason": "all checks passed",
            "checks": {
                "command": {"allowed": True},
                "file_protection": {"protected": False},
            }
        }))
        sys.exit(0)

    except json.JSONDecodeError as e:
        print(json.dumps({"allowed": False, "reason": f"invalid JSON input: {e}"}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"allowed": False, "reason": f"hook error: {e}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
