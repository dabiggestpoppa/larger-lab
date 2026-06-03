"""
PO Tool Set — File system, git, and shell access for the Primary Observer.

These tools are exposed to the LLM via the ChatAgent's tool-calling loop.
Each tool has a name, description, and JSON schema for the LLM to call.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]


def list_directory(path: str = ".", max_depth: int = 2, max_items: int = 50) -> str:
    """List files and directories at the given path. Returns a tree-like listing."""
    try:
        base = REPO_ROOT / path if not Path(path).is_absolute() else Path(path)
        if not base.exists():
            return f"Path not found: {base}"
        if not base.is_dir():
            return f"Not a directory: {base}"

        lines = [f"{base}/"]
        count = 0

        def _walk(dir_path: Path, prefix: str, depth: int):
            nonlocal count
            if depth > max_depth or count >= max_items:
                return
            try:
                items = sorted(dir_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
                for item in items:
                    if count >= max_items:
                        lines.append(f"{prefix}  ... (truncated)")
                        return
                    if item.name.startswith('.') and item.name not in ('.env', '.gitignore'):
                        continue
                    if item.is_dir():
                        lines.append(f"{prefix}  {item.name}/")
                        count += 1
                        _walk(item, prefix + "  ", depth + 1)
                    else:
                        size = item.stat().st_size
                        if size < 1024:
                            sz = f"{size}B"
                        elif size < 1024 * 1024:
                            sz = f"{size // 1024}KB"
                        else:
                            sz = f"{size // (1024 * 1024)}MB"
                        lines.append(f"{prefix}  {item.name} ({sz})")
                        count += 1
            except PermissionError:
                lines.append(f"{prefix}  [permission denied]")

        _walk(base, "", 0)
        return "\n".join(lines)
    except Exception as e:
        return f"Error listing {path}: {e}"


def read_file(path: str, start_line: int = 1, max_lines: int = 200) -> str:
    """Read a file's contents. Supports line range for large files."""
    try:
        fp = REPO_ROOT / path if not Path(path).is_absolute() else Path(path)
        if not fp.exists():
            return f"File not found: {fp}"
        if fp.stat().st_size > 1024 * 1024:
            return f"File too large ({fp.stat().st_size} bytes). Use start_line/max_lines to read a portion."

        content = fp.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()

        if start_line > 1 or max_lines < len(lines):
            end = min(start_line - 1 + max_lines, len(lines))
            selected = lines[start_line - 1:end]
            header = f"[Lines {start_line}-{end} of {len(lines)}]\n"
            return header + "\n".join(selected)

        return content
    except Exception as e:
        return f"Error reading {path}: {e}"


def run_command(command: str, timeout: int = 30, cwd: str = "") -> str:
    """Run a shell command and return stdout+stderr. Use sparingly."""
    try:
        work_dir = REPO_ROOT / cwd if cwd else REPO_ROOT
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(work_dir),
            encoding="utf-8",
            errors="replace",
        )
        output = result.stdout
        if result.stderr:
            output += "\n[STDERR]\n" + result.stderr
        if result.returncode != 0:
            output += f"\n[Exit code: {result.returncode}]"
        return output[:5000]  # Cap output
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout}s: {command}"
    except Exception as e:
        return f"Error running command: {e}"


def git_status() -> str:
    """Get git status of the repository."""
    return run_command("git status --short", timeout=10)


def git_log(count: int = 10) -> str:
    """Get recent git commits."""
    return run_command(
        f'git log --oneline -{count} --format="%h %s (%ar)"',
        timeout=10,
    )


def git_diff(file_path: str = "", cached: bool = False) -> str:
    """Get git diff for a file or the whole repo."""
    cmd = "git diff --cached " if cached else "git diff "
    if file_path:
        cmd += "-- " + file_path
    return run_command(cmd, timeout=10)


def search_files(pattern: str, path: str = ".", max_results: int = 20) -> str:
    """Search for files matching a glob pattern."""
    try:
        base = REPO_ROOT / path if not Path(path).is_absolute() else Path(path)
        matches = list(base.rglob(pattern))[:max_results]
        if not matches:
            return f"No files matching '{pattern}' in {base}"
        lines = [f"Found {len(matches)} matches for '{pattern}':"]
        for m in matches:
            rel = m.relative_to(REPO_ROOT) if str(REPO_ROOT) in str(m) else m
            size = m.stat().st_size
            lines.append(f"  {rel} ({size}B)")
        return "\n".join(lines)
    except Exception as e:
        return f"Error searching: {e}"


def search_content(query: str, path: str = ".", file_pattern: str = "*.py", max_results: int = 10) -> str:
    """Search for text content within files using grep."""
    try:
        cmd = f'grep -r -l --include="{file_pattern}" "{query}" {path} 2>/dev/null | head -{max_results}'
        result = run_command(cmd, timeout=15)
        if not result.strip():
            return f"No matches for '{query}' in {path}/{file_pattern}"
        return f"Files containing '{query}':\n{result}"
    except Exception as e:
        return f"Error searching content: {e}"


# Tool definitions for the LLM
TOOL_DEFINITIONS = [
    {
        "name": "list_directory",
        "description": "List files and directories. Use this to explore the workspace structure.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path from repo root, or '.' for root"},
                "max_depth": {"type": "integer", "description": "Max directory depth (default 2)"},
                "max_items": {"type": "integer", "description": "Max items to list (default 50)"},
            },
            "required": [],
        },
    },
    {
        "name": "read_file",
        "description": "Read a file's contents. Use this to examine code, configs, logs, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path from repo root"},
                "start_line": {"type": "integer", "description": "Starting line number (1-indexed)"},
                "max_lines": {"type": "integer", "description": "Max lines to read (default 200)"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "run_command",
        "description": "Run a shell command. Use for git, python, npm, etc. Be careful with destructive commands.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"},
                "timeout": {"type": "integer", "description": "Timeout in seconds (default 30)"},
                "cwd": {"type": "string", "description": "Working directory relative to repo root"},
            },
            "required": ["command"],
        },
    },
    {
        "name": "git_status",
        "description": "Get git status — shows modified, added, deleted files.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "git_log",
        "description": "Get recent git commit history.",
        "parameters": {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "description": "Number of commits (default 10)"},
            },
            "required": [],
        },
    },
    {
        "name": "search_files",
        "description": "Search for files by name pattern (glob). Use *.py for Python files, *.md for markdown, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern like *.py, *.md, *test*"},
                "path": {"type": "string", "description": "Directory to search in (default repo root)"},
                "max_results": {"type": "integer", "description": "Max results (default 20)"},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "search_content",
        "description": "Search for text within file contents. Use this to find code, references, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Text to search for"},
                "path": {"type": "string", "description": "Directory to search in"},
                "file_pattern": {"type": "string", "description": "File glob pattern (default *.py)"},
                "max_results": {"type": "integer", "description": "Max files to return (default 10)"},
            },
            "required": ["query"],
        },
    },
]

# Map tool names to functions
TOOL_FUNCTIONS = {
    "list_directory": list_directory,
    "read_file": read_file,
    "run_command": run_command,
    "git_status": git_status,
    "git_log": git_log,
    "search_files": search_files,
    "search_content": search_content,
}
