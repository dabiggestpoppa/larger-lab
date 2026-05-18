#!/usr/bin/env python3
"""
Enhanced Post-Tool-Use Hook
Runs tests after code edits AND logs all tool calls.
Receives JSON via stdin, returns JSON via stdout.

Input JSON:
{
  "file_path": "srrs_opc/module.py",
  "tool_name": "edit",
  "agent": "OC2",
  "command": "...",
  "success": true
}
"""

import json
import sys
import subprocess
import os
from pathlib import Path
from datetime import datetime, timezone


def run_python_syntax_check(file_path: str) -> dict:
    """Run Python syntax check on edited file."""
    if not file_path.endswith(".py"):
        return {"skipped": True, "reason": "not a Python file"}

    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", file_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return {"passed": True, "check": "python_syntax"}
        else:
            return {
                "passed": False,
                "check": "python_syntax",
                "error": result.stderr.strip()[:500],
            }
    except subprocess.TimeoutExpired:
        return {"passed": False, "check": "python_syntax", "error": "timeout"}
    except Exception as e:
        return {"passed": False, "check": "python_syntax", "error": str(e)[:500]}


def run_json_validation(file_path: str) -> dict:
    """Validate JSON files after edit."""
    if not file_path.endswith(".json"):
        return {"skipped": True, "reason": "not a JSON file"}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            json.load(f)
        return {"passed": True, "check": "json_validation"}
    except json.JSONDecodeError as e:
        return {"passed": False, "check": "json_validation", "error": str(e)[:500]}
    except Exception as e:
        return {"passed": False, "check": "json_validation", "error": str(e)[:500]}


def run_yaml_validation(file_path: str) -> dict:
    """Validate YAML files after edit."""
    if not file_path.endswith((".yml", ".yaml")):
        return {"skipped": True, "reason": "not a YAML file"}

    try:
        import yaml
        with open(file_path, "r", encoding="utf-8") as f:
            yaml.safe_load(f)
        return {"passed": True, "check": "yaml_validation"}
    except ImportError:
        return {"skipped": True, "reason": "PyYAML not installed"}
    except Exception as e:
        return {"passed": False, "check": "yaml_validation", "error": str(e)[:500]}


def run_markdown_link_check(file_path: str) -> dict:
    """Basic markdown link validation."""
    if not file_path.endswith((".md", ".markdown")):
        return {"skipped": True, "reason": "not a markdown file"}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for broken markdown links [text](url) where url is empty
        import re
        broken_links = re.findall(r'\[([^\]]*)\]\(\s*\)', content)
        if broken_links:
            return {
                "passed": False,
                "check": "markdown_links",
                "error": f"Empty links found: {broken_links[:5]}",
            }

        # Check YAML frontmatter is valid
        if content.startswith("---"):
            try:
                import yaml
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    yaml.safe_load(parts[1])
            except ImportError:
                pass
            except Exception as e:
                return {
                    "passed": False,
                    "check": "yaml_frontmatter",
                    "error": f"Invalid YAML frontmatter: {e}",
                }

        return {"passed": True, "check": "markdown_validation"}
    except Exception as e:
        return {"passed": False, "check": "markdown_validation", "error": str(e)[:500]}


def log_tool_call(data: dict, workspace_root: str = None) -> dict:
    """Log all tool calls to audit file."""
    if not workspace_root:
        workspace_root = os.environ.get(
            "WORKSPACE_ROOT",
            str(Path(__file__).resolve().parent.parent.parent),
        )

    log_dir = Path(workspace_root) / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "tool-calls.jsonl"

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": data.get("agent", "unknown"),
        "tool_name": data.get("tool_name", "unknown"),
        "file_path": data.get("file_path", ""),
        "command": data.get("command", "")[:200],
        "success": data.get("success", True),
    }

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        return {"logged": True, "log_file": str(log_file)}
    except Exception as e:
        return {"logged": False, "error": str(e)}


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            print(json.dumps({"passed": True, "reason": "no input"}))
            sys.exit(0)

        data = json.loads(raw)
        file_path = data.get("file_path", "")
        tool_name = data.get("tool_name", "")

        # Always log the tool call
        log_result = log_tool_call(data)

        if not file_path:
            print(json.dumps({"passed": True, "reason": "no file_path", "log": log_result}))
            sys.exit(0)

        if not Path(file_path).exists():
            print(json.dumps({"passed": False, "reason": f"file not found: {file_path}", "log": log_result}))
            sys.exit(1)

        results = []

        # Run appropriate checks based on file type
        for check_fn in [
            run_python_syntax_check,
            run_json_validation,
            run_yaml_validation,
            run_markdown_link_check,
        ]:
            result = check_fn(file_path)
            results.append(result)

        # Filter to only non-skipped results
        active_results = [r for r in results if not r.get("skipped")]

        if not active_results:
            print(json.dumps({
                "passed": True,
                "reason": "no applicable checks",
                "results": results,
                "log": log_result,
            }))
            sys.exit(0)

        all_passed = all(r.get("passed", False) for r in active_results)
        output = {
            "passed": all_passed,
            "results": results,
            "log": log_result,
        }
        print(json.dumps(output, indent=2))
        sys.exit(0 if all_passed else 1)

    except json.JSONDecodeError as e:
        print(json.dumps({"passed": False, "reason": f"invalid JSON input: {e}"}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"passed": False, "reason": f"hook error: {e}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
