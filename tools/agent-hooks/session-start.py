#!/usr/bin/env python3
"""
Session-Start Hook
Loads project context at the beginning of a session.
Receives JSON via stdin, returns JSON via stdout.
"""

import json
import sys
import os
from pathlib import Path


def load_project_context(workspace_root: str = None) -> dict:
    """Load key project files to bootstrap session context."""
    if not workspace_root:
        workspace_root = os.environ.get(
            "WORKSPACE_ROOT",
            str(Path(__file__).resolve().parent.parent.parent),
        )

    context = {
        "workspace_root": workspace_root,
        "files_loaded": [],
        "errors": [],
    }

    # Key files to load for context
    key_files = [
        "AGENTS.md",
        "SOUL.md",
        "IDENTITY.md",
        "USER.md",
        ".phase-state.json",
        ".agent-tags.json",
    ]

    for filename in key_files:
        filepath = Path(workspace_root) / filename
        if filepath.exists():
            try:
                content = filepath.read_text(encoding="utf-8", errors="replace")
                # Include first 500 chars of each file as summary
                context[filename] = {
                    "exists": True,
                    "size": len(content),
                    "preview": content[:500],
                }
                context["files_loaded"].append(filename)
            except Exception as e:
                context["errors"].append(f"{filename}: {e}")
        else:
            context[filename] = {"exists": False}
            context["files_loaded"].append(f"{filename} (missing)")

    # Load phase state if available
    phase_file = Path(workspace_root) / ".phase-state.json"
    if phase_file.exists():
        try:
            phase_data = json.loads(phase_file.read_text(encoding="utf-8"))
            context["current_phase"] = phase_data.get("current_phase", "unknown")
            context["phase_status"] = phase_data.get("status", "unknown")
        except Exception:
            context["current_phase"] = "unknown"

    return context


def main():
    try:
        raw = sys.stdin.read()
        data = {}
        if raw.strip():
            data = json.loads(raw)

        workspace_root = data.get("workspace_root")
        context = load_project_context(workspace_root)

        print(json.dumps(context, indent=2, default=str))
        sys.exit(0)

    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"invalid JSON input: {e}"}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"hook error: {e}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
