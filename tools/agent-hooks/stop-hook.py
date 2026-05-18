#!/usr/bin/env python3
"""
Stop Hook — Verify task completion before allowing session end.
Checks that all stated goals were met and no critical errors remain.

Input JSON:
{
  "session_id": "...",
  "agent": "OC2",
  "stated_goals": ["goal1", "goal2"],
  "completed_goals": ["goal1", "goal2"],
  "errors": [],
  "files_modified": ["file1.py", "file2.md"],
  "workspace_root": "C:/Users/wifik/Desktop/projects/larger-lab"
}
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone


def verify_goals(stated: list, completed: list) -> dict:
    """Check that all stated goals were completed."""
    stated_set = set(stated)
    completed_set = set(completed)
    missing = stated_set - completed_set

    if missing:
        return {
            "complete": False,
            "missing_goals": list(missing),
            "message": f"⚠️  {len(missing)} goal(s) not completed: {', '.join(missing)}",
        }

    return {"complete": True, "message": "All stated goals completed."}


def verify_files_exist(files: list, workspace_root: str) -> dict:
    """Verify that modified files actually exist."""
    missing_files = []
    for f in files:
        full_path = Path(workspace_root) / f
        if not full_path.exists():
            missing_files.append(f)

    if missing_files:
        return {
            "complete": False,
            "missing_files": missing_files,
            "message": f"⚠️  {len(missing_files)} modified file(s) not found: {', '.join(missing_files)}",
        }

    return {"complete": True, "message": "All modified files verified."}


def verify_no_critical_errors(errors: list) -> dict:
    """Check for critical errors that should block session end."""
    critical_keywords = ["security", "data_loss", "corruption", "unauthorized", "breach"]
    critical_errors = []

    for error in errors:
        error_lower = str(error).lower()
        for keyword in critical_keywords:
            if keyword in error_lower:
                critical_errors.append(error)
                break

    if critical_errors:
        return {
            "complete": False,
            "critical_errors": critical_errors,
            "message": f"🚨 {len(critical_errors)} critical error(s) must be resolved before session end.",
        }

    return {"complete": True, "message": "No critical errors."}


def write_session_summary(data: dict, workspace_root: str) -> dict:
    """Write a session summary for audit trail."""
    log_dir = Path(workspace_root) / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "session-summaries.jsonl"

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": data.get("session_id", "unknown"),
        "agent": data.get("agent", "unknown"),
        "stated_goals": data.get("stated_goals", []),
        "completed_goals": data.get("completed_goals", []),
        "errors": data.get("errors", []),
        "files_modified": data.get("files_modified", []),
        "status": data.get("status", "completed"),
    }

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        return {"logged": True}
    except Exception as e:
        return {"logged": False, "error": str(e)}


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            print(json.dumps({"can_stop": True, "reason": "no input"}))
            sys.exit(0)

        data = json.loads(raw)
        workspace_root = data.get("workspace_root", str(Path(__file__).resolve().parent.parent.parent))

        checks = []

        # Check goals
        stated = data.get("stated_goals", [])
        completed = data.get("completed_goals", [])
        if stated:
            goal_check = verify_goals(stated, completed)
            checks.append(("goals", goal_check))

        # Check files
        files = data.get("files_modified", [])
        if files:
            file_check = verify_files_exist(files, workspace_root)
            checks.append(("files", file_check))

        # Check errors
        errors = data.get("errors", [])
        error_check = verify_no_critical_errors(errors)
        checks.append(("errors", error_check))

        # Write summary
        summary_result = write_session_summary(data, workspace_root)

        # Determine if session can stop
        all_passed = all(c[1].get("complete", True) for c in checks)
        messages = [c[1].get("message", "") for c in checks]

        output = {
            "can_stop": all_passed,
            "checks": {name: result for name, result in checks},
            "messages": messages,
            "summary_logged": summary_result.get("logged", False),
        }

        if not all_passed:
            output["warning"] = "Session has unresolved issues. Review before ending."

        print(json.dumps(output, indent=2))
        sys.exit(0 if all_passed else 1)

    except json.JSONDecodeError as e:
        print(json.dumps({"can_stop": False, "reason": f"invalid JSON input: {e}"}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"can_stop": False, "reason": f"hook error: {e}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
