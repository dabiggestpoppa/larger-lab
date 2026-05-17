#!/usr/bin/env python3
"""
Session-End Hook
Writes an audit log entry when a session ends.
Receives JSON via stdin, returns JSON via stdout.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone


def write_audit_log(session_data: dict, workspace_root: str = None) -> dict:
    """Write session audit entry to the log file."""
    if not workspace_root:
        workspace_root = os.environ.get(
            "WORKSPACE_ROOT",
            str(Path(__file__).resolve().parent.parent.parent),
        )

    log_dir = Path(workspace_root) / "logs"
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / "session-audit.jsonl"

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_data.get("session_id", "unknown"),
        "agent": session_data.get("agent", "unknown"),
        "channel": session_data.get("channel", "unknown"),
        "tool_calls": session_data.get("tool_calls", 0),
        "files_modified": session_data.get("files_modified", []),
        "errors": session_data.get("errors", []),
        "status": session_data.get("status", "completed"),
        "duration_seconds": session_data.get("duration_seconds", 0),
    }

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

        return {
            "logged": True,
            "log_file": str(log_file),
            "entry": entry,
        }
    except Exception as e:
        return {
            "logged": False,
            "error": str(e),
        }


def main():
    try:
        raw = sys.stdin.read()
        data = {}
        if raw.strip():
            data = json.loads(raw)

        workspace_root = data.get("workspace_root")
        result = write_audit_log(data, workspace_root)

        print(json.dumps(result, indent=2, default=str))
        sys.exit(0 if result.get("logged") else 1)

    except json.JSONDecodeError as e:
        print(json.dumps({"logged": False, "error": f"invalid JSON input: {e}"}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"logged": False, "error": f"hook error: {e}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
