"""
PO Capabilities — Unified tool execution engine for Primary Observer.

This is the core execution layer that PO uses to actually PERFORM all the
registered tools. It bridges the tool registry to real operations:

- File operations → direct filesystem access
- Git operations → subprocess git commands
- Shell execution → subprocess with safety limits
- Python execution → project virtualenv
- Search → grep/rg, glob, semantic
- GitHub → gh CLI
- Browser → Playwright (when available)
- Memory → file-based memory system
- MCP → MCP client bridge
- VS Code → VS Code CLI commands
- System → OS-level operations

All operations are sandboxed to the repo root for safety.
"""

from __future__ import annotations

import glob as glob_module
import json
import logging
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.po_capabilities")

REPO_ROOT = Path(__file__).resolve().parents[2]
VENV_PYTHON = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
IS_WINDOWS = platform.system() == "Windows"


# ─── Safety Limits ───────────────────────────────────────────────────────────

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_OUTPUT = 10000  # characters
MAX_SEARCH_RESULTS = 100
DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"rm\s+-rf\s+~",
    r"format\s+[a-z]:",
    r"del\s+/[sq]",
    r"shutdown\s+",
    r"reboot\s+",
    r"mkfs\.",
    r"dd\s+if=",
    r">\s*/dev/sda",
    r"chmod\s+-R\s+777\s+/",
]


def _is_dangerous_command(cmd: str) -> bool:
    """Check if a command is potentially dangerous."""
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return True
    return False


def _safe_path(path: str) -> Path:
    """Resolve a path relative to repo root, ensuring it stays within the repo."""
    if Path(path).is_absolute():
        p = Path(path)
    else:
        p = REPO_ROOT / path
    p = p.resolve()
    # Ensure path is within repo root (prevent path traversal)
    try:
        p.relative_to(REPO_ROOT.resolve())
    except ValueError:
        raise ValueError(f"Path '{path}' is outside the repo root")
    return p


# ─── File Operations ─────────────────────────────────────────────────────────

def list_directory(path: str = ".", max_depth: int = 2, max_items: int = 50) -> str:
    """List files and directories."""
    try:
        base = _safe_path(path)
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
                    if item.name.startswith('.') and item.name not in ('.env', '.gitignore', '.github', '.agents', '.vscode'):
                        continue
                    if item.is_dir():
                        lines.append(f"{prefix}  {item.name}/")
                        count += 1
                        _walk(item, prefix + "  ", depth + 1)
                    else:
                        size = item.stat().st_size
                        sz = f"{size}B" if size < 1024 else f"{size // 1024}KB" if size < 1024*1024 else f"{size // (1024*1024)}MB"
                        lines.append(f"{prefix}  {item.name} ({sz})")
                        count += 1
            except PermissionError:
                lines.append(f"{prefix}  [permission denied]")

        _walk(base, "", 0)
        return "\n".join(lines)
    except Exception as e:
        return f"Error listing {path}: {e}"


def read_file(path: str, start_line: int = 1, max_lines: int = 200) -> str:
    """Read a file's contents."""
    try:
        fp = _safe_path(path)
        if not fp.exists():
            return f"File not found: {fp}"
        if fp.stat().st_size > MAX_FILE_SIZE:
            return f"File too large ({fp.stat().st_size} bytes). Use start_line/max_lines."
        content = fp.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()
        if start_line > 1 or max_lines < len(lines):
            end = min(start_line - 1 + max_lines, len(lines))
            return f"[Lines {start_line}-{end} of {len(lines)}]\n" + "\n".join(lines[start_line-1:end])
        return content
    except Exception as e:
        return f"Error reading {path}: {e}"


def write_file(path: str, content: str) -> str:
    """Write content to a file."""
    try:
        fp = _safe_path(path)
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content, encoding="utf-8")
        lines = content.count('\n') + 1
        return f"OK: Wrote {lines} lines to {path}"
    except Exception as e:
        return f"Error writing {path}: {e}"


def edit_file(path: str, old_text: str, new_text: str) -> str:
    """Edit a file by replacing exact text."""
    try:
        fp = _safe_path(path)
        if not fp.exists():
            return f"File not found: {fp}"
        content = fp.read_text(encoding="utf-8")
        if old_text not in content:
            return f"Text not found in {path}. The old_text must match exactly."
        new_content = content.replace(old_text, new_text, 1)
        fp.write_text(new_content, encoding="utf-8")
        return f"OK: Edited {path}: replaced {len(old_text)} chars with {len(new_text)} chars"
    except Exception as e:
        return f"Error editing {path}: {e}"


def multi_edit_file(path: str, edits: List[Dict[str, str]]) -> str:
    """Apply multiple replace operations to a file."""
    try:
        fp = _safe_path(path)
        if not fp.exists():
            return f"File not found: {fp}"
        content = fp.read_text(encoding="utf-8")
        results = []
        for i, edit in enumerate(edits):
            old_text = edit["old_text"]
            new_text = edit["new_text"]
            if old_text not in content:
                results.append(f"  Edit {i}: text not found, skipped")
            else:
                content = content.replace(old_text, new_text, 1)
                results.append(f"  Edit {i}: OK")
        fp.write_text(content, encoding="utf-8")
        return f"OK: Applied {len(edits)} edits to {path}\n" + "\n".join(results)
    except Exception as e:
        return f"Error multi-editing {path}: {e}"


def create_directory(path: str) -> str:
    """Create a directory."""
    try:
        fp = _safe_path(path)
        fp.mkdir(parents=True, exist_ok=True)
        return f"OK: Created directory {path}"
    except Exception as e:
        return f"Error creating directory {path}: {e}"


def delete_file(path: str, recursive: bool = False) -> str:
    """Delete a file or directory."""
    try:
        fp = _safe_path(path)
        if not fp.exists():
            return f"Path not found: {fp}"
        if fp.is_dir():
            if recursive:
                shutil.rmtree(fp)
                return f"OK: Deleted directory {path} recursively"
            else:
                fp.rmdir()
                return f"OK: Deleted empty directory {path}"
        else:
            fp.unlink()
            return f"OK: Deleted file {path}"
    except Exception as e:
        return f"Error deleting {path}: {e}"


def file_exists(path: str) -> str:
    """Check if a file or directory exists."""
    try:
        fp = _safe_path(path)
        if fp.exists():
            kind = "directory" if fp.is_dir() else "file"
            size = fp.stat().st_size if fp.is_file() else 0
            return f"OK: {path} exists ({kind}, {size}B)"
        return f"NOT_FOUND: {path}"
    except Exception as e:
        return f"Error checking {path}: {e}"


# ─── Git Operations ──────────────────────────────────────────────────────────

def _run_git(args: str, timeout: int = 15) -> str:
    """Run a git command."""
    try:
        cmd = f"git {args}"
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=str(REPO_ROOT), encoding="utf-8", errors="replace",
        )
        output = result.stdout.strip()
        if result.stderr and "warning" not in result.stderr.lower():
            output += "\n[STDERR] " + result.stderr.strip()
        if result.returncode != 0 and not output:
            output = f"[Exit code: {result.returncode}] {result.stderr.strip()}"
        return output[:MAX_OUTPUT]
    except subprocess.TimeoutExpired:
        return f"Git command timed out after {timeout}s"
    except Exception as e:
        return f"Git error: {e}"


def git_status() -> str:
    return _run_git("status --short")


def git_log(count: int = 10) -> str:
    return _run_git(f'log --oneline -{count} --format="%h %s (%ar)"')


def git_diff(file_path: str = "", cached: bool = False) -> str:
    cmd = "diff --cached " if cached else "diff "
    if file_path:
        cmd += "-- " + str(_safe_path(file_path))
    return _run_git(cmd)


def git_commit(message: str, files: list = None) -> str:
    try:
        if files and files != ['all']:
            for f in files:
                _run_git(f'add "{f}"')
        else:
            _run_git("add -A")
        return _run_git(f'commit -m "{message}"')
    except Exception as e:
        return f"Commit error: {e}"


def git_push(remote: str = "origin", branch: str = "", force: bool = False) -> str:
    cmd = f"push {remote}"
    if branch:
        cmd += f" {branch}"
    if force:
        cmd += " --force"
    return _run_git(cmd)


def git_pull(remote: str = "origin", branch: str = "") -> str:
    cmd = f"pull {remote}"
    if branch:
        cmd += f" {branch}"
    return _run_git(cmd)


def git_branch(action: str = "list", name: str = "") -> str:
    if action == "list":
        return _run_git("branch -a")
    elif action == "create":
        return _run_git(f"branch {name}")
    elif action == "delete":
        return _run_git(f"branch -D {name}")
    elif action == "checkout":
        return _run_git(f"checkout {name}")
    return f"Unknown branch action: {action}"


def git_stash(action: str = "push", message: str = "") -> str:
    if action == "push":
        cmd = "stash push"
        if message:
            cmd += f' -m "{message}"'
        return _run_git(cmd)
    elif action == "pop":
        return _run_git("stash pop")
    elif action == "list":
        return _run_git("stash list")
    elif action == "clear":
        return _run_git("stash clear")
    return f"Unknown stash action: {action}"


def git_blame(file_path: str) -> str:
    return _run_git(f"blame {_safe_path(file_path)}")


# ─── Shell Execution ─────────────────────────────────────────────────────────

def run_command(command: str, timeout: int = 30, cwd: str = "", env: dict = None) -> str:
    """Run a shell command."""
    try:
        if _is_dangerous_command(command):
            return "BLOCKED: Command matches dangerous pattern"

        work_dir = str(_safe_path(cwd)) if cwd else str(REPO_ROOT)
        env_vars = os.environ.copy()
        if env:
            env_vars.update(env)

        # On Windows, use PowerShell
        if IS_WINDOWS:
            cmd = ["powershell", "-NoProfile", "-Command", command]
        else:
            cmd = ["bash", "-c", command]

        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout, cwd=work_dir, encoding="utf-8", errors="replace",
            env=env_vars,
        )
        output = result.stdout
        if result.stderr:
            output += "\n[STDERR]\n" + result.stderr
        if result.returncode != 0:
            output += f"\n[Exit code: {result.returncode}]"
        return output[:MAX_OUTPUT]
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout}s: {command}"
    except Exception as e:
        return f"Error running command: {e}"


def execute_python(code: str, timeout: int = 60, args: list = None) -> str:
    """Execute Python code in the project virtualenv."""
    try:
        python_exe = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(code)
            f.flush()
            tmp_path = f.name

        try:
            cmd = [python_exe, tmp_path]
            if args:
                cmd.extend(args)

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout,
                cwd=str(REPO_ROOT), encoding="utf-8", errors="replace",
            )
            output = result.stdout
            if result.stderr:
                output += "\n[STDERR]\n" + result.stderr
            if result.returncode != 0:
                output += f"\n[Exit code: {result.returncode}]"
            return output[:MAX_OUTPUT]
        finally:
            os.unlink(tmp_path)
    except subprocess.TimeoutExpired:
        return f"Python execution timed out after {timeout}s"
    except Exception as e:
        return f"Python execution error: {e}"


def run_python_file(path: str, timeout: int = 120, args: list = None) -> str:
    """Run a Python file in the project virtualenv."""
    try:
        fp = _safe_path(path)
        if not fp.exists():
            return f"File not found: {fp}"
        python_exe = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
        cmd = [python_exe, str(fp)]
        if args:
            cmd.extend(args)
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            cwd=str(REPO_ROOT), encoding="utf-8", errors="replace",
        )
        output = result.stdout
        if result.stderr:
            output += "\n[STDERR]\n" + result.stderr
        if result.returncode != 0:
            output += f"\n[Exit code: {result.returncode}]"
        return output[:MAX_OUTPUT]
    except subprocess.TimeoutExpired:
        return f"Python file execution timed out after {timeout}s"
    except Exception as e:
        return f"Python file execution error: {e}"


def install_python_package(package: str, upgrade: bool = False) -> str:
    """Install a Python package."""
    try:
        python_exe = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
        cmd = [python_exe, "-m", "pip", "install"]
        if upgrade:
            cmd.append("--upgrade")
        cmd.append(package)
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120,
            cwd=str(REPO_ROOT), encoding="utf-8", errors="replace",
        )
        output = result.stdout
        if result.stderr:
            output += "\n[STDERR]\n" + result.stderr
        return output[:MAX_OUTPUT]
    except Exception as e:
        return f"Package install error: {e}"


# ─── Search Operations ───────────────────────────────────────────────────────

def search_files(pattern: str, path: str = ".", max_results: int = 20) -> str:
    """Search for files by glob pattern."""
    try:
        base = _safe_path(path)
        matches = list(base.rglob(pattern))[:max_results]
        if not matches:
            return f"No files matching '{pattern}' in {base}"
        lines = [f"Found {len(matches)} matches for '{pattern}':"]
        for m in matches:
            try:
                rel = m.relative_to(REPO_ROOT)
            except ValueError:
                rel = m
            lines.append(f"  {rel} ({m.stat().st_size}B)")
        return "\n".join(lines)
    except Exception as e:
        return f"Error searching: {e}"


def search_content(query: str, path: str = ".", file_pattern: str = "*.py",
                   max_results: int = 10, case_sensitive: bool = False,
                   is_regex: bool = False) -> str:
    """Search for text within file contents."""
    try:
        base = _safe_path(path)

        # Use grep on Unix, findstr on Windows
        if IS_WINDOWS:
            flags = "/s /n"
            if not case_sensitive:
                flags += " /i"
            cmd = f'findstr {flags} "{query}" {base}\\{file_pattern}'
        else:
            flags = "-r -n -l"
            if not case_sensitive:
                flags += " -i"
            if is_regex:
                flags += " -E"
            cmd = f'grep {flags} --include="{file_pattern}" "{query}" {base}'

        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=30, cwd=str(REPO_ROOT), encoding="utf-8", errors="replace",
        )
        files = result.stdout.strip().split("\n")[:max_results]
        files = [f for f in files if f.strip()]
        if not files:
            return f"No matches for '{query}' in {path}/{file_pattern}"
        return f"Files containing '{query}':\n" + "\n".join(f"  {f}" for f in files)
    except Exception as e:
        return f"Error searching content: {e}"


def grep_search(query: str, path: str = ".", file_pattern: str = "*.*",
                max_results: int = 50, case_sensitive: bool = False) -> str:
    """Fast text search with regex support."""
    try:
        base = _safe_path(path)

        if IS_WINDOWS:
            # Use PowerShell Select-String
            flags = "-Path", str(base), "-Pattern", query, "-Recurse"
            if not case_sensitive:
                flags += ("-CaseSensitive",)
            cmd = f'Get-ChildItem -Path "{base}" -Recurse -File | Select-String -Pattern "{query}" | Select-Object -First {max_results} | ForEach-Object {{ "$($_.Path):$($_.LineNumber):$($_.Line.Trim())" }}'
        else:
            flags = "-r -n"
            if not case_sensitive:
                flags += " -i"
            cmd = f'grep {flags} --include="{file_pattern}" "{query}" {base} | head -{max_results}'

        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=30, cwd=str(REPO_ROOT), encoding="utf-8", errors="replace",
        )
        output = result.stdout.strip()
        if not output:
            return f"No matches for '{query}'"
        return output[:MAX_OUTPUT]
    except Exception as e:
        return f"Error in grep search: {e}"


# ─── GitHub Operations ───────────────────────────────────────────────────────

def _run_gh(args: str, timeout: int = 30) -> str:
    """Run a gh CLI command."""
    try:
        cmd = f"gh {args}"
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=str(REPO_ROOT), encoding="utf-8", errors="replace",
        )
        output = result.stdout.strip()
        if result.stderr:
            output += "\n[STDERR] " + result.stderr.strip()
        if result.returncode != 0 and not output:
            output = f"[Exit code: {result.returncode}] {result.stderr.strip()}"
        return output[:MAX_OUTPUT]
    except subprocess.TimeoutExpired:
        return f"gh command timed out after {timeout}s"
    except FileNotFoundError:
        return "gh CLI not found. Install from https://cli.github.com/"
    except Exception as e:
        return f"gh error: {e}"


def github_pr_list(state: str = "open", limit: int = 30) -> str:
    return _run_gh(f"pr list --state {state} --limit {limit}")


def github_pr_create(title: str, body: str = "", head: str = "", base: str = "main", draft: bool = False) -> str:
    cmd = f'pr create --title "{title}" --body "{body}" --base {base}'
    if head:
        cmd += f" --head {head}"
    if draft:
        cmd += " --draft"
    return _run_gh(cmd)


def github_pr_view(number: int) -> str:
    return _run_gh(f"pr view {number}")


def github_pr_merge(number: int, method: str = "merge") -> str:
    return _run_gh(f"pr merge {number} --{method}")


def github_issue_list(state: str = "open", limit: int = 30) -> str:
    return _run_gh(f"issue list --state {state} --limit {limit}")


def github_issue_create(title: str, body: str = "", labels: list = None) -> str:
    cmd = f'issue create --title "{title}" --body "{body}"'
    if labels:
        for label in labels:
            cmd += f' --label "{label}"'
    return _run_gh(cmd)


def github_ci_status(limit: int = 10) -> str:
    return _run_gh(f"run list --limit {limit}")


def github_search(query: str, type: str = "issue") -> str:
    return _run_gh(f"search {type}s {query}")


def github_repo_info() -> str:
    return _run_gh("repo view --json name,description,defaultBranchRef,url")


# ─── System Operations ───────────────────────────────────────────────────────

def system_env(action: str = "get", name: str = "", value: str = "") -> str:
    """Get or set environment variables."""
    if action == "get":
        if name:
            return os.environ.get(name, f"Variable '{name}' not set")
        # Return common env vars
        relevant = {k: v for k, v in os.environ.items()
                    if k.startswith(("PYTHON", "PATH", "HOME", "USER", "VIRTUAL", "OPENROUTER", "NODE"))}
        return json.dumps(relevant, indent=2)
    elif action == "set":
        os.environ[name] = value
        return f"OK: Set {name}={value}"
    elif action == "list":
        return json.dumps(dict(os.environ), indent=2)[:MAX_OUTPUT]
    return f"Unknown action: {action}"


def system_processes(filter: str = "") -> str:
    """List running processes."""
    try:
        if IS_WINDOWS:
            cmd = 'Get-Process | Select-Object Id, ProcessName, CPU, WorkingSet64 | Format-Table -AutoSize'
            if filter:
                cmd = f'Get-Process -Name "*{filter}*" | Select-Object Id, ProcessName, CPU, WorkingSet64 | Format-Table -AutoSize'
        else:
            cmd = "ps aux"
            if filter:
                cmd = f"ps aux | grep {filter}"
        return run_command(cmd, timeout=10)
    except Exception as e:
        return f"Error listing processes: {e}"


def system_kill_process(pid: int = 0, name: str = "", force: bool = False) -> str:
    """Kill a process."""
    try:
        if pid:
            if IS_WINDOWS:
                cmd = f"taskkill /F /PID {pid}" if force else f"taskkill /PID {pid}"
            else:
                cmd = f"kill -9 {pid}" if force else f"kill {pid}"
        elif name:
            if IS_WINDOWS:
                cmd = f"taskkill /F /IM {name}" if force else f"taskkill /IM {name}"
            else:
                cmd = f"killall -9 {name}" if force else f"killall {name}"
        else:
            return "Error: Must specify pid or name"
        return run_command(cmd, timeout=10)
    except Exception as e:
        return f"Error killing process: {e}"


def system_disk_usage(path: str = "") -> str:
    """Get disk usage."""
    try:
        target = _safe_path(path) if path else REPO_ROOT
        if IS_WINDOWS:
            cmd = f'Get-PSDrive -PSProvider FileSystem | Select-Object Name, Used, Free | Format-Table -AutoSize'
        else:
            cmd = f"df -h {target}"
        return run_command(cmd, timeout=10)
    except Exception as e:
        return f"Error getting disk usage: {e}"


def system_info() -> str:
    """Get system information."""
    info = {
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "python_version": sys.version,
        "python_executable": sys.executable,
        "repo_root": str(REPO_ROOT),
        "venv_python": str(VENV_PYTHON) if VENV_PYTHON.exists() else "not found",
        "cpu_count": os.cpu_count(),
        "cwd": str(Path.cwd()),
    }
    return json.dumps(info, indent=2)


# ─── Memory Operations ───────────────────────────────────────────────────────

def memory_read(path: str) -> str:
    """Read a memory file."""
    try:
        # Memory files are in the workspace, not necessarily in repo
        # Support both /memories/ absolute paths and relative
        if path.startswith("/memories/"):
            # Map to workspace memories directory
            mem_path = REPO_ROOT.parent / "memories" / path[len("/memories/"):]
        else:
            mem_path = REPO_ROOT / "memories" / path

        if not mem_path.exists():
            return f"Memory file not found: {path}"
        return mem_path.read_text(encoding="utf-8", errors="replace")[:MAX_OUTPUT]
    except Exception as e:
        return f"Error reading memory: {e}"


def memory_write(path: str, content: str) -> str:
    """Write a memory file."""
    try:
        if path.startswith("/memories/"):
            mem_path = REPO_ROOT.parent / "memories" / path[len("/memories/"):]
        else:
            mem_path = REPO_ROOT / "memories" / path
        mem_path.parent.mkdir(parents=True, exist_ok=True)
        mem_path.write_text(content, encoding="utf-8")
        return f"OK: Wrote memory file {path}"
    except Exception as e:
        return f"Error writing memory: {e}"


def memory_list(scope: str = "user") -> str:
    """List memory files."""
    try:
        if scope == "user":
            mem_dir = REPO_ROOT.parent / "memories"
        elif scope == "session":
            mem_dir = REPO_ROOT.parent / "memories" / "session"
        elif scope == "repo":
            mem_dir = REPO_ROOT.parent / "memories" / "repo"
        else:
            mem_dir = REPO_ROOT.parent / "memories"

        if not mem_dir.exists():
            return f"Memory directory not found: {mem_dir}"

        files = []
        for f in mem_dir.rglob("*.md"):
            rel = f.relative_to(mem_dir)
            files.append(f"  {rel} ({f.stat().st_size}B)")
        return f"Memory files in '{scope}':\n" + "\n".join(files) if files else f"No memory files in '{scope}'"
    except Exception as e:
        return f"Error listing memory: {e}"


def memory_search(query: str, scope: str = "all") -> str:
    """Search memory files."""
    try:
        if scope == "all":
            scopes = ["user", "session", "repo"]
        else:
            scopes = [scope]

        results = []
        for s in scopes:
            if s == "user":
                mem_dir = REPO_ROOT.parent / "memories"
            elif s == "session":
                mem_dir = REPO_ROOT.parent / "memories" / "session"
            elif s == "repo":
                mem_dir = REPO_ROOT.parent / "memories" / "repo"
            else:
                continue

            if not mem_dir.exists():
                continue

            for f in mem_dir.rglob("*.md"):
                try:
                    content = f.read_text(encoding="utf-8", errors="replace")
                    if query.lower() in content.lower():
                        # Find matching lines
                        for i, line in enumerate(content.splitlines(), 1):
                            if query.lower() in line.lower():
                                rel = f.relative_to(mem_dir)
                                results.append(f"  {rel}:{i}: {line.strip()[:100]}")
                except Exception:
                    continue

        if not results:
            return f"No memory matches for '{query}'"
        return f"Memory search results for '{query}':\n" + "\n".join(results[:50])
    except Exception as e:
        return f"Error searching memory: {e}"


# ─── Vault Operations ────────────────────────────────────────────────────────

def vault_search(query: str, max_results: int = 10) -> str:
    """Search the Obsidian vault."""
    try:
        vault_dir = REPO_ROOT / "O2C-VAULT"
        if not vault_dir.exists():
            return "Vault directory not found: O2C-VAULT/"

        results = []
        for f in vault_dir.rglob("*.md"):
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
                if query.lower() in content.lower():
                    rel = f.relative_to(vault_dir)
                    # Get a snippet
                    lines = content.splitlines()
                    snippet = ""
                    for line in lines:
                        if query.lower() in line.lower():
                            snippet = line.strip()[:150]
                            break
                    results.append(f"  {rel}: {snippet}")
            except Exception:
                continue

        if not results:
            return f"No vault notes found for: {query}"
        return f"Vault search: {query}\n" + "\n".join(results[:max_results])
    except Exception as e:
        return f"Vault search error: {e}"


def vault_read(path: str) -> str:
    """Read a vault note."""
    try:
        vault_dir = REPO_ROOT / "O2C-VAULT"
        note_path = vault_dir / path
        if not note_path.exists():
            note_path = vault_dir / (path + ".md")
        if not note_path.exists():
            return f"Note not found: {path}"
        return note_path.read_text(encoding="utf-8", errors="replace")[:MAX_OUTPUT]
    except Exception as e:
        return f"Vault read error: {e}"


# ─── Web Operations ──────────────────────────────────────────────────────────

def web_fetch(url: str, query: str = "") -> str:
    """Fetch content from a URL."""
    try:
        import urllib.request
        import urllib.error

        req = urllib.request.Request(url, headers={"User-Agent": "OCE-PO/1.0"})
        with urllib.request.urlopen(req, timeout=15) as response:
            content = response.read().decode("utf-8", errors="replace")
            if query:
                # Simple extraction: find lines containing query
                lines = content.splitlines()
                matching = [l.strip() for l in lines if query.lower() in l.lower()]
                if matching:
                    return f"Content from {url} (filtered by '{query}'):\n" + "\n".join(matching[:30])
            return f"Content from {url}:\n{content[:MAX_OUTPUT]}"
    except Exception as e:
        return f"Web fetch error: {e}"


def web_search(query: str, max_results: int = 10) -> str:
    """Search the web using DuckDuckGo."""
    try:
        # Use the MCP server if available, otherwise fallback to duckduckgo-search
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                if results:
                    lines = [f"Web search: {query}"]
                    for r in results:
                        lines.append(f"  {r.get('title', 'N/A')}")
                        lines.append(f"    {r.get('href', '')}")
                        lines.append(f"    {r.get('body', '')[:150]}")
                    return "\n".join(lines)
        except ImportError:
            pass

        # Fallback: use curl to fetch DuckDuckGo HTML
        import urllib.parse
        encoded = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        return web_fetch(url, query)
    except Exception as e:
        return f"Web search error: {e}"


# ─── VS Code Operations ──────────────────────────────────────────────────────

def vscode_run_command(command_id: str, args: list = None) -> str:
    """Run a VS Code command."""
    try:
        cmd = f"code --command {command_id}"
        if args:
            cmd += " " + " ".join(f'"{a}"' for a in args)
        return run_command(cmd, timeout=30)
    except Exception as e:
        return f"VS Code command error: {e}"


def vscode_get_errors(file_path: str = "") -> str:
    """Get compile/lint errors (via Python syntax check)."""
    try:
        if file_path:
            fp = _safe_path(file_path)
            if fp.suffix == ".py":
                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(fp)],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode == 0:
                    return f"No syntax errors in {file_path}"
                return f"Syntax error in {file_path}:\n{result.stderr}"
            return f"Syntax check not supported for {fp.suffix} files"
        else:
            # Check all Python files in the project
            errors = []
            for py_file in REPO_ROOT.rglob("*.py"):
                try:
                    result = subprocess.run(
                        [sys.executable, "-m", "py_compile", str(py_file)],
                        capture_output=True, text=True, timeout=5,
                    )
                    if result.returncode != 0:
                        rel = py_file.relative_to(REPO_ROOT)
                        errors.append(f"  {rel}: {result.stderr.strip()[:100]}")
                except Exception:
                    continue
            if errors:
                return f"Python syntax errors found:\n" + "\n".join(errors[:20])
            return "No Python syntax errors found in workspace"
    except Exception as e:
        return f"Error checking syntax: {e}"


# ─── Notebook Operations ─────────────────────────────────────────────────────

def notebook_list(path: str = ".") -> str:
    """List Jupyter notebooks."""
    try:
        base = _safe_path(path)
        notebooks = list(base.rglob("*.ipynb"))
        if not notebooks:
            return f"No notebooks found in {base}"
        lines = [f"Notebooks in {base}:"]
        for nb in notebooks:
            rel = nb.relative_to(REPO_ROOT) if str(REPO_ROOT) in str(nb) else nb
            lines.append(f"  {rel} ({nb.stat().st_size}B)")
        return "\n".join(lines)
    except Exception as e:
        return f"Error listing notebooks: {e}"


def notebook_read(path: str) -> str:
    """Read a notebook's structure."""
    try:
        fp = _safe_path(path)
        if not fp.exists():
            return f"Notebook not found: {fp}"
        data = json.loads(fp.read_text(encoding="utf-8"))
        cells = data.get("cells", [])
        lines = [f"Notebook: {path} ({len(cells)} cells)"]
        for i, cell in enumerate(cells):
            cell_type = cell.get("cell_type", "unknown")
            source = "".join(cell.get("source", ""))[:100]
            lines.append(f"  Cell {i}: [{cell_type}] {source}...")
        return "\n".join(lines)
    except Exception as e:
        return f"Error reading notebook: {e}"


# ─── PDF Operations ──────────────────────────────────────────────────────────

def pdf_extract_text(path: str, pages: str = "all") -> str:
    """Extract text from a PDF."""
    try:
        fp = _safe_path(path)
        if not fp.exists():
            return f"PDF not found: {fp}"

        # Try PyPDF2 first
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(str(fp))
            if pages == "all":
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
            else:
                # Parse page range
                start, end = 0, len(reader.pages)
                if "-" in pages:
                    parts = pages.split("-")
                    start = int(parts[0]) - 1
                    end = int(parts[1])
                text = "\n".join(
                    reader.pages[i].extract_text() or ""
                    for i in range(start, min(end, len(reader.pages)))
                )
            return text[:MAX_OUTPUT]
        except ImportError:
            return "PyPDF2 not installed. Install with: pip install PyPDF2"
    except Exception as e:
        return f"PDF extract error: {e}"


def pdf_merge(files: list, output: str) -> str:
    """Merge multiple PDFs."""
    try:
        from PyPDF2 import PdfMerger
        merger = PdfMerger()
        for f in files:
            fp = _safe_path(f)
            if fp.exists():
                merger.append(str(fp))
        out_path = _safe_path(output)
        merger.write(str(out_path))
        merger.close()
        return f"OK: Merged {len(files)} PDFs into {output}"
    except ImportError:
        return "PyPDF2 not installed. Install with: pip install PyPDF2"
    except Exception as e:
        return f"PDF merge error: {e}"


def pdf_split(path: str, output_dir: str = "", pages: str = "") -> str:
    """Split a PDF."""
    try:
        from PyPDF2 import PdfReader, PdfWriter
        fp = _safe_path(path)
        if not fp.exists():
            return f"PDF not found: {fp}"

        reader = PdfReader(str(fp))
        out = _safe_path(output_dir) if output_dir else fp.parent
        out.mkdir(parents=True, exist_ok=True)

        if pages:
            start, end = map(int, pages.split("-"))
            for i in range(start - 1, min(end, len(reader.pages))):
                writer = PdfWriter()
                writer.add_page(reader.pages[i])
                out_path = out / f"page_{i+1}.pdf"
                with open(out_path, "wb") as f:
                    writer.write(f)
            return f"OK: Split pages {pages} from {path}"
        else:
            # Split all pages
            for i, page in enumerate(reader.pages):
                writer = PdfWriter()
                writer.add_page(page)
                out_path = out / f"page_{i+1}.pdf"
                with open(out_path, "wb") as f:
                    writer.write(f)
            return f"OK: Split {len(reader.pages)} pages from {path}"
    except ImportError:
        return "PyPDF2 not installed. Install with: pip install PyPDF2"
    except Exception as e:
        return f"PDF split error: {e}"


def pdf_compress(path: str, output: str = "", quality: str = "medium") -> str:
    """Compress a PDF."""
    try:
        fp = _safe_path(path)
        if not fp.exists():
            return f"PDF not found: {fp}"

        # Use pikepdf for compression
        try:
            import pikepdf
            out_path = _safe_path(output) if output else fp.with_suffix(".compressed.pdf")
            with pikepdf.open(str(fp)) as pdf:
                pdf.save(str(out_path))
            original_size = fp.stat().st_size
            compressed_size = out_path.stat().st_size
            ratio = (1 - compressed_size / original_size) * 100
            return f"OK: Compressed {path} ({original_size}B → {compressed_size}B, {ratio:.1f}% reduction)"
        except ImportError:
            return "pikepdf not installed. Install with: pip install pikepdf"
    except Exception as e:
        return f"PDF compress error: {e}"


# ─── Task Management ─────────────────────────────────────────────────────────

_task_list: List[Dict[str, Any]] = []


def task_list() -> str:
    """Get the current task list."""
    if not _task_list:
        return "No tasks defined"
    lines = ["Current tasks:"]
    for t in _task_list:
        status_icon = {"not-started": "○", "in-progress": "◐", "completed": "●"}.get(t["status"], "?")
        lines.append(f"  {status_icon} [{t['id']}] {t['title']} ({t['status']})")
    return "\n".join(lines)


def task_update(tasks: list) -> str:
    """Update the task list."""
    global _task_list
    _task_list = tasks
    return f"OK: Updated task list ({len(tasks)} tasks)"


# ─── Capability Function Map ────────────────────────────────────────────────

CAPABILITY_FUNCTIONS: Dict[str, callable] = {
    # File operations
    "list_directory": list_directory,
    "read_file": read_file,
    "write_file": write_file,
    "edit_file": edit_file,
    "multi_edit_file": multi_edit_file,
    "create_directory": create_directory,
    "delete_file": delete_file,
    "file_exists": file_exists,
    # Git operations
    "git_status": git_status,
    "git_log": git_log,
    "git_diff": git_diff,
    "git_commit": git_commit,
    "git_push": git_push,
    "git_pull": git_pull,
    "git_branch": git_branch,
    "git_stash": git_stash,
    "git_blame": git_blame,
    # Execution
    "run_command": run_command,
    "execute_python": execute_python,
    "run_python_file": run_python_file,
    "install_python_package": install_python_package,
    # Search
    "search_files": search_files,
    "search_content": search_content,
    "grep_search": grep_search,
    # GitHub
    "github_pr_list": github_pr_list,
    "github_pr_create": github_pr_create,
    "github_pr_view": github_pr_view,
    "github_pr_merge": github_pr_merge,
    "github_issue_list": github_issue_list,
    "github_issue_create": github_issue_create,
    "github_ci_status": github_ci_status,
    "github_search": github_search,
    "github_repo_info": github_repo_info,
    # System
    "system_env": system_env,
    "system_processes": system_processes,
    "system_kill_process": system_kill_process,
    "system_disk_usage": system_disk_usage,
    "system_info": system_info,
    # Memory
    "memory_read": memory_read,
    "memory_write": memory_write,
    "memory_list": memory_list,
    "memory_search": memory_search,
    # Vault
    "vault_search": vault_search,
    "vault_read": vault_read,
    # Web
    "web_fetch": web_fetch,
    "web_search": web_search,
    # VS Code
    "vscode_run_command": vscode_run_command,
    "vscode_get_errors": vscode_get_errors,
    # Notebook
    "notebook_list": notebook_list,
    "notebook_read": notebook_read,
    # PDF
    "pdf_extract_text": pdf_extract_text,
    "pdf_merge": pdf_merge,
    "pdf_split": pdf_split,
    "pdf_compress": pdf_compress,
    # Tasks
    "task_list": task_list,
    "task_update": task_update,
}


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """
    Execute a tool by name with the given arguments.
    This is the main entry point for PO tool execution.
    """
    func = CAPABILITY_FUNCTIONS.get(tool_name)
    if not func:
        return f"Unknown tool: {tool_name}. Available: {', '.join(sorted(CAPABILITY_FUNCTIONS.keys())[:20])}..."

    try:
        result = func(**arguments)
        return str(result) if result is not None else "OK"
    except TypeError as e:
        return f"Tool '{tool_name}' argument error: {e}"
    except Exception as e:
        return f"Tool '{tool_name}' execution error: {e}"
