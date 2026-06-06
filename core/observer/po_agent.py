"""
PO Agent — Full VS Code Agent Capability for Primary Observer
=============================================================

Transforms PO from a hardcoded slash-command bot into a full agent
with the same capabilities as CC (Claude Code):

- OpenAI/Anthropic native tool calling (not custom ```tool blocks)
- File read/write/edit
- Shell command execution
- OCE API integration
- GitHub operations (via gh CLI)
- Semantic search over codebase
- Subagent delegation
- Task management
- Browser automation (via Playwright)
- VS Code command execution

Architecture:
    Telegram message → POAgent.chat() → LLM with tools → tool execution loop → response

The agent uses a proper tool-calling loop compatible with OpenRouter models
that support the OpenAI function_calling format.
"""

import os
import json
import time
import datetime
import threading
import requests
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

from oce.backend.rate_limit_tracker import record_api_call

REPO_ROOT = Path(__file__).resolve().parents[2]

# ─── Model Configuration ────────────────────────────────────────────────────

MODEL_CHAIN = [
    "inclusionai/ring-2.6-1t",
    "minimax/minimax-m3",
    "nvidia/nemotron-3-ultra-550b-a55b",
]

# ─── Tool Definitions (OpenAI function calling format) ─────────────────────

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files and directories. Use to explore workspace structure.",
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
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file's contents. Use to examine code, configs, logs, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path from repo root"},
                    "start_line": {"type": "integer", "description": "Starting line number (1-indexed, default 1)"},
                    "max_lines": {"type": "integer", "description": "Max lines to read (default 200)"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file. Creates the file if it doesn't exist, overwrites if it does. Creates parent directories as needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path from repo root"},
                    "content": {"type": "string", "description": "Full file content to write"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Edit a file by replacing exact text. The oldText must match exactly including whitespace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path from repo root"},
                    "old_text": {"type": "string", "description": "Exact text to find and replace (must match exactly)"},
                    "new_text": {"type": "string", "description": "New text to replace the old text with"},
                },
                "required": ["path", "old_text", "new_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
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
    },
    {
        "type": "function",
        "function": {
            "name": "git_status",
            "description": "Get git status — shows modified, added, deleted files.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
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
    },
    {
        "type": "function",
        "function": {
            "name": "git_diff",
            "description": "Get git diff for a file or the whole repo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Specific file path, or empty for all"},
                    "cached": {"type": "boolean", "description": "Show staged changes (default false)"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "git_commit",
            "description": "Stage and commit changes. Use after writing/editing files.",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Commit message"},
                    "files": {"type": "array", "items": {"type": "string"}, "description": "Specific files to stage, or ['all'] for git add -A"},
                },
                "required": ["message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
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
    },
    {
        "type": "function",
        "function": {
            "name": "search_content",
            "description": "Search for text within file contents. Use to find code, references, etc.",
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
    },
    {
        "type": "function",
        "function": {
            "name": "oce_api_call",
            "description": "Call the OCE backend API. Use to interact with observers, events, topology, execution, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "method": {"type": "string", "description": "HTTP method: GET, POST, PUT, DELETE"},
                    "endpoint": {"type": "string", "description": "API endpoint path, e.g. /health, /observers, /events"},
                    "body": {"type": "object", "description": "Request body for POST/PUT (optional)"},
                    "params": {"type": "object", "description": "Query parameters (optional)"},
                },
                "required": ["method", "endpoint"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "github_operation",
            "description": "Perform GitHub operations via gh CLI. Use for PRs, issues, CI checks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "Operation: pr-list, pr-create, pr-view, issue-list, issue-create, ci-status, ci-run, search-issues, search-prs",
                    },
                    "args": {"type": "string", "description": "Additional arguments for the gh command"},
                },
                "required": ["operation"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "spawn_subagent",
            "description": "Spawn a subagent for complex multi-step tasks. Use for research, code exploration, or parallel work.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "Detailed task description for the subagent"},
                    "agent_type": {
                        "type": "string",
                        "description": "Type of agent: explore (research), build (implement), debug (fix issues)",
                    },
                },
                "required": ["task", "agent_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_action",
            "description": "Control the browser. Use to open pages, take screenshots, interact with web UIs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "Action: open (navigate to URL), screenshot (capture page), click (click element), type (input text), read (get page content)",
                    },
                    "url": {"type": "string", "description": "URL to open (for open action)"},
                    "ref": {"type": "string", "description": "Element reference for click/type actions"},
                    "text": {"type": "string", "description": "Text to type (for type action)"},
                },
                "required": ["action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "vault_search",
            "description": "Search the Obsidian vault for notes. Use to find knowledge, documentation, research.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search keywords"},
                    "max_results": {"type": "integer", "description": "Max results (default 10)"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "vault_read",
            "description": "Read a specific vault note by path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path relative to vault root"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_python",
            "description": "Execute Python code in the project virtualenv. Use for data analysis, testing, automation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python code to execute"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds (default 60)"},
                },
                "required": ["code"],
            },
        },
    },
]


# ─── Tool Implementations ───────────────────────────────────────────────────

def list_directory(path: str = ".", max_depth: int = 2, max_items: int = 50) -> str:
    """List files and directories at the given path."""
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
        fp = REPO_ROOT / path if not Path(path).is_absolute() else Path(path)
        if not fp.exists():
            return f"File not found: {fp}"
        if fp.stat().st_size > 1024 * 1024:
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
    """Write content to a file. Creates parent directories as needed."""
    try:
        fp = REPO_ROOT / path if not Path(path).is_absolute() else Path(path)
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content, encoding="utf-8")
        lines = content.count('\n') + 1
        return f"✅ Wrote {lines} lines to {path}"
    except Exception as e:
        return f"Error writing {path}: {e}"


def edit_file(path: str, old_text: str, new_text: str) -> str:
    """Edit a file by replacing exact text."""
    try:
        fp = REPO_ROOT / path if not Path(path).is_absolute() else Path(path)
        if not fp.exists():
            return f"File not found: {fp}"
        content = fp.read_text(encoding="utf-8")
        if old_text not in content:
            return f"Text not found in {path}. The old_text must match exactly."
        new_content = content.replace(old_text, new_text, 1)
        fp.write_text(new_content, encoding="utf-8")
        return f"✅ Edited {path}: replaced {len(old_text)} chars with {len(new_text)} chars"
    except Exception as e:
        return f"Error editing {path}: {e}"


def run_command(command: str, timeout: int = 30, cwd: str = "") -> str:
    """Run a shell command and return stdout+stderr."""
    try:
        work_dir = str(REPO_ROOT / cwd) if cwd else str(REPO_ROOT)
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=work_dir, encoding="utf-8", errors="replace",
        )
        output = result.stdout
        if result.stderr:
            output += "\n[STDERR]\n" + result.stderr
        if result.returncode != 0:
            output += f"\n[Exit code: {result.returncode}]"
        return output[:5000]
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout}s: {command}"
    except Exception as e:
        return f"Error running command: {e}"


def git_status() -> str:
    return run_command("git status --short", timeout=10)


def git_log(count: int = 10) -> str:
    return run_command(f'git log --oneline -{count} --format="%h %s (%ar)"', timeout=10)


def git_diff(file_path: str = "", cached: bool = False) -> str:
    cmd = "git diff --cached " if cached else "git diff "
    if file_path:
        cmd += "-- " + file_path
    return run_command(cmd, timeout=10)


def git_commit(message: str, files: list = None) -> str:
    try:
        if files and files != ['all']:
            for f in files:
                run_command(f'git add "{f}"', timeout=10)
        else:
            run_command("git add -A", timeout=10)
        return run_command(f'git commit -m "{message}"', timeout=15)
    except Exception as e:
        return f"Error committing: {e}"


def search_files(pattern: str, path: str = ".", max_results: int = 20) -> str:
    try:
        base = REPO_ROOT / path if not Path(path).is_absolute() else Path(path)
        matches = list(base.rglob(pattern))[:max_results]
        if not matches:
            return f"No files matching '{pattern}' in {base}"
        lines = [f"Found {len(matches)} matches for '{pattern}':"]
        for m in matches:
            rel = m.relative_to(REPO_ROOT) if str(REPO_ROOT) in str(m) else m
            lines.append(f"  {rel} ({m.stat().st_size}B)")
        return "\n".join(lines)
    except Exception as e:
        return f"Error searching: {e}"


def search_content(query: str, path: str = ".", file_pattern: str = "*.py", max_results: int = 10) -> str:
    try:
        cmd = f'grep -r -l --include="{file_pattern}" "{query}" {path} 2>/dev/null | head -{max_results}'
        result = run_command(cmd, timeout=15)
        if not result.strip():
            return f"No matches for '{query}' in {path}/{file_pattern}"
        return f"Files containing '{query}':\n{result}"
    except Exception as e:
        return f"Error searching content: {e}"


def oce_api_call(method: str, endpoint: str, body: dict = None, params: dict = None) -> str:
    """Call the OCE backend API. Use /agent/execute for file operations."""
    try:
        base = os.environ.get("OCE_API_URL", "http://localhost:8000")
        url = f"{base}{endpoint}"
        if method.upper() == "GET":
            r = requests.get(url, params=params, timeout=15)
        elif method.upper() == "POST":
            r = requests.post(url, json=body, params=params, timeout=30)
        elif method.upper() == "PUT":
            r = requests.put(url, json=body, params=params, timeout=30)
        elif method.upper() == "DELETE":
            r = requests.delete(url, params=params, timeout=15)
        else:
            return f"Unsupported method: {method}"
        try:
            return json.dumps(r.json(), indent=2, default=str)[:3000]
        except:
            return r.text[:3000]
    except Exception as e:
        return f"OCE API error: {e}"


def agent_execute(action: str, params: dict = None) -> str:
    """Execute an action through the OCE agent API. Preferred for file ops."""
    try:
        base = os.environ.get("OCE_API_URL", "http://localhost:8000")
        r = requests.post(
            f"{base}/agent/execute",
            json={"action": action, "params": params or {}, "agent_id": "po"},
            timeout=60,
        )
        data = r.json()
        if data.get("ok"):
            return str(data.get("result", "OK"))
        return f"Agent action failed: {data.get('error', 'unknown error')}"
    except Exception as e:
        return f"Agent execute error: {e}"


def github_operation(operation: str, args: str = "") -> str:
    """Perform GitHub operations via gh CLI."""
    commands = {
        "pr-list": f"gh pr list --state all {args}",
        "pr-create": f"gh pr create {args}",
        "pr-view": f"gh pr view {args}",
        "issue-list": f"gh issue list --state all {args}",
        "issue-create": f"gh issue create {args}",
        "ci-status": f"gh run list --limit 10 {args}",
        "ci-run": f"gh run view {args}",
        "search-issues": f"gh search issues {args}",
        "search-prs": f"gh search prs {args}",
    }
    cmd = commands.get(operation)
    if not cmd:
        return f"Unknown operation: {operation}. Available: {', '.join(commands.keys())}"
    return run_command(cmd, timeout=30)


def spawn_subagent(task: str, agent_type: str = "explore") -> str:
    """Spawn a subagent for complex tasks. Returns a summary of what to do."""
    return (
        f"🤖 SUBAGENT SPAWN REQUEST\n"
        f"Type: {agent_type}\n"
        f"Task: {task}\n\n"
        f"In a full VS Code agent environment, this would spawn a {agent_type} agent.\n"
        f"For now, execute this task directly using available tools."
    )


def browser_action(action: str, url: str = "", ref: str = "", text: str = "") -> str:
    """Browser control. In Telegram context, returns guidance."""
    if action == "open" and url:
        return f"🌐 Browser would open: {url}\nIn Telegram context, use oce_api_call or run_command to interact with web services."
    elif action == "screenshot":
        return "📸 Screenshot requires browser automation. Use run_command with playwright if needed."
    return f"Browser action '{action}' requested. Use run_command for CLI-based web interactions."


def vault_search(query: str, max_results: int = 10) -> str:
    """Search the Obsidian vault."""
    try:
        from core.observer.vault import Vault
        v = Vault()
        hits = v.search_notes(query.split(), max_results=max_results)
        if not hits:
            return f"No notes found for: {query}"
        lines = [f"🔍 Vault search: {query}", ""]
        for h in hits[:max_results]:
            lines.append(f"  📄 {h['path']}")
            if h.get('snippet'):
                lines.append(f"     {h['snippet'][:100]}")
        return "\n".join(lines)
    except Exception as e:
        return f"Vault search error: {e}"


def vault_read(path: str) -> str:
    """Read a vault note."""
    try:
        from core.observer.vault import Vault
        v = Vault()
        note_path = v.path / path
        if not note_path.exists():
            # Try with .md extension
            note_path = v.path / (path + ".md")
        if not note_path.exists():
            return f"Note not found: {path}"
        return note_path.read_text(encoding="utf-8")[:3000]
    except Exception as e:
        return f"Vault read error: {e}"


def execute_python(code: str, timeout: int = 60) -> str:
    """Execute Python code in the project virtualenv."""
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
            f.write(code)
            f.flush()
            tmp_path = f.name
        python_exe = str(REPO_ROOT / ".venv" / "Scripts" / "python.exe")
        result = subprocess.run(
            [python_exe, tmp_path],
            capture_output=True, text=True, timeout=timeout,
            cwd=str(REPO_ROOT), encoding="utf-8", errors="replace",
        )
        os.unlink(tmp_path)
        output = result.stdout
        if result.stderr:
            output += "\n[STDERR]\n" + result.stderr
        if result.returncode != 0:
            output += f"\n[Exit code: {result.returncode}]"
        return output[:5000]
    except subprocess.TimeoutExpired:
        return f"Python execution timed out after {timeout}s"
    except Exception as e:
        return f"Python execution error: {e}"


# ─── Tool Function Map ──────────────────────────────────────────────────────

TOOL_FUNCTIONS: Dict[str, Callable] = {
    "list_directory": list_directory,
    "read_file": read_file,
    "write_file": write_file,
    "edit_file": edit_file,
    "run_command": run_command,
    "git_status": git_status,
    "git_log": git_log,
    "git_diff": git_diff,
    "git_commit": git_commit,
    "search_files": search_files,
    "search_content": search_content,
    "oce_api_call": oce_api_call,
    "agent_execute": agent_execute,
    "github_operation": github_operation,
    "spawn_subagent": spawn_subagent,
    "browser_action": browser_action,
    "vault_search": vault_search,
    "vault_read": vault_read,
    "execute_python": execute_python,
}


# ─── PO Agent ───────────────────────────────────────────────────────────────

class POAgent:
    """
    Full agent with tool-calling loop for Primary Observer.

    Uses OpenAI/Anthropic native function calling format.
    Falls back to custom ```tool block parsing for models that don't support it.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self._history: List[Dict[str, str]] = []
        self._max_history = 20
        self._model_index = 0
        self._lock = threading.Lock()

    def _load_configured_model(self) -> Optional[str]:
        """Load model from config file if it exists."""
        try:
            model_config_path = REPO_ROOT / "data" / "po_model.json"
            if model_config_path.exists():
                data = json.loads(model_config_path.read_text(encoding="utf-8"))
                return data.get("model")
        except Exception:
            pass
        return None

    @property
    def current_model(self) -> str:
        configured = self._load_configured_model()
        if configured:
            return configured
        return MODEL_CHAIN[self._model_index % len(MODEL_CHAIN)]

    def _build_system_prompt(self, sovereign_context: str = "") -> str:
        ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        return (
            "You are PO (Primary Observer) — a full autonomous agent for Larger-Lab.\n"
            "You have the same capabilities as Claude Code: you can read/write/edit files, "
            "run shell commands, call OCE APIs, perform GitHub operations, search code, "
            "execute Python, and manage the entire workspace.\n\n"
            f"Current time: {ts}\n"
            f"Workspace: C:\\Users\\wifik\\Desktop\\projects\\larger-lab\n"
            f"Branch: master (default: main)\n\n"
            "## Available Tools\n"
            "list_directory, read_file, write_file, edit_file, run_command, "
            "git_status, git_log, git_diff, git_commit, search_files, search_content, "
            "oce_api_call, github_operation, vault_search, vault_read, execute_python, "
            "spawn_subagent, browser_action\n\n"
            "## Rules\n"
            "1. Use tools to accomplish tasks — don't just describe what to do\n"
            "2. Read files before editing them\n"
            "3. Use edit_file for small changes, write_file for new files or full rewrites\n"
            "4. Run tests after code changes\n"
            "5. Be concise in Telegram responses — summarize tool outputs\n"
            "6. For long operations, send progress updates\n"
            "7. Never exfiltrate private data\n"
            "8. Ask before destructive operations (rm, force push, etc.)\n\n"
            "## Response Format\n"
            "Respond in Markdown. Use emoji sparingly: ✅ ❌ ⚠️ 🔄 📊 🔍\n"
            "Keep Telegram responses under 4000 chars. Summarize long outputs.\n"
            + (f"\n## Operational Context\n{sovereign_context}\n" if sovereign_context else "")
        )

    def _sanitize_message(self, msg: Dict) -> Dict:
        """Ensure message content is always a string — prevents OpenRouter 400 errors
        from corrupted history entries where content becomes a list/dict."""
        if not isinstance(msg, dict):
            return {"role": "user", "content": str(msg)}
        content = msg.get("content", "")
        if not isinstance(content, str):
            content = json.dumps(content, default=str)[:2000]
        return {
            "role": msg.get("role", "user"),
            "content": content,
        }

    def _call_llm(self, messages: List[Dict], model: str = None, tools: list = None, tool_choice: str = "auto"):
        """Call LLM with optional tool definitions. Returns (response, tool_calls, model, error)."""
        if model is None:
            model = self.current_model

        # Sanitize all messages to prevent content-type errors
        safe_messages = [self._sanitize_message(m) for m in messages]

        payload = {
            "model": model,
            "messages": safe_messages,
            "max_tokens": 4096,
            "temperature": 0.7,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice

        try:
            r = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=120,
            )
            if r.status_code == 429:
                record_api_call(model=model, status_code=429, error_type="rate_limited")
                return None, None, model, "rate_limited"
            if r.status_code >= 400:
                record_api_call(model=model, status_code=r.status_code, error_type=f"http_{r.status_code}")
                return None, None, model, f"http_{r.status_code}: {r.text[:200]}"
            data = r.json()

            # Extract response
            choice = data.get("choices", [{}])[0]
            msg = choice.get("message", {})

            # Check for native tool_calls (OpenAI format)
            tool_calls = msg.get("tool_calls", None)
            content = msg.get("content", "")

            # Also check for ```tool fallback format
            if not tool_calls and content:
                tool_calls = self._parse_fallback_tool_calls(content)

            record_api_call(model=model, status_code=200, tokens=len(content or ""))
            return content, tool_calls, model, None
        except requests.exceptions.Timeout:
            record_api_call(model=model, status_code=0, error_type="timeout")
            return None, None, model, "timeout"
        except Exception as e:
            record_api_call(model=model, status_code=0, error_type=str(e)[:200])
            return None, None, model, str(e)[:200]

    def _parse_fallback_tool_calls(self, content: str) -> Optional[List[Dict]]:
        """Parse ```tool blocks as fallback for models without native function calling."""
        if "```tool" not in content:
            return None
        try:
            start = content.index("```tool") + len("```tool")
            end = content.index("```", start)
            tool_json = content[start:end].strip()
            data = json.loads(tool_json)
            # Convert to OpenAI tool_calls format
            return [{
                "id": "fallback_1",
                "type": "function",
                "function": {
                    "name": data.get("tool", ""),
                    "arguments": json.dumps(data.get("args", {})),
                }
            }]
        except (ValueError, json.JSONDecodeError):
            return None

    def _execute_tool(self, tool_call: Dict) -> str:
        """Execute a tool call and return the result."""
        try:
            func = tool_call.get("function", {})
            tool_name = func.get("name", "")
            args_str = func.get("arguments", "{}")
            args = json.loads(args_str) if isinstance(args_str, str) else args_str
        except (json.JSONDecodeError, AttributeError) as e:
            return f"Error parsing tool call: {e}"

        if tool_name not in TOOL_FUNCTIONS:
            return f"Unknown tool: {tool_name}. Available: {', '.join(TOOL_FUNCTIONS.keys())}"

        try:
            result = TOOL_FUNCTIONS[tool_name](**args)
            return str(result)
        except Exception as e:
            return f"Error executing {tool_name}: {e}"

    def chat(self, message: str, sovereign_context: str = "", max_tool_rounds: int = 15,
             progress_callback=None, history: Optional[List[Dict[str, str]]] = None,
             session_id: str = "") -> str:
        """
        Full agent chat with tool-calling loop.

        Args:
            message: User message
            sovereign_context: Operational context to inject
            max_tool_rounds: Maximum tool-calling iterations
            progress_callback: Optional callable(text) for sending progress updates
                              during tool execution. Used by Telegram gateway.
            history: Optional list of previous messages to include in context.
            session_id: Optional session identifier for logging/tracking.

        Flow:
        1. Send message + system prompt + tool definitions to LLM
        2. If LLM returns tool_calls, execute them and send results back
        3. After each tool execution, call progress_callback with update
        4. Repeat until LLM returns a final response or max rounds reached
        5. Return final response
        """
        if not self.api_key:
            return "LLM not configured. Set OPENROUTER_API_KEY."

        def _notify(event_type, data=None):
            """Send progress update if callback is available."""
            if progress_callback:
                try:
                    progress_callback(event_type, data or {})
                except Exception:
                    pass

        system_prompt = self._build_system_prompt(sovereign_context)
        messages = [{"role": "system", "content": system_prompt}]
        with self._lock:
            for h in self._history[-self._max_history:]:
                messages.append(h)
        messages.append({"role": "user", "content": message})

        _notify("round", {"round": 1, "max": max_tool_rounds})

        for round_num in range(max_tool_rounds):
            # Try configured model first, then current model, then chain fallback
            resp, tool_calls, used_model, err = None, None, None, None
            configured = self._load_configured_model()
            models_to_try = []
            if configured:
                models_to_try.append(configured)
            if self.current_model not in models_to_try:
                models_to_try.append(self.current_model)
            for m in MODEL_CHAIN:
                if m not in models_to_try:
                    models_to_try.append(m)

            for attempt, model in enumerate(models_to_try):
                resp, tool_calls, used_model, err = self._call_llm(
                    messages, model=model, tools=TOOL_DEFINITIONS, tool_choice="auto"
                )
                if resp or tool_calls:
                    if used_model in MODEL_CHAIN:
                        self._model_index = MODEL_CHAIN.index(used_model)
                    break

            if not resp and not tool_calls:
                error_msg = f"⚠️ All LLM providers failed. Last error: {err}"
                _notify("error", {"message": error_msg})
                return error_msg

            if tool_calls:
                # Add assistant message with tool calls
                messages.append({
                    "role": "assistant",
                    "content": resp or "",
                    "tool_calls": [
                        {
                            "id": tc.get("id", f"tc_{i}"),
                            "type": "function",
                            "function": {
                                "name": tc.get("function", {}).get("name", ""),
                                "arguments": tc.get("function", {}).get("arguments", "{}"),
                            }
                        }
                        for i, tc in enumerate(tool_calls)
                    ]
                })

                # Execute each tool call and report progress
                for tc in tool_calls:
                    func = tc.get("function", {})
                    tool_name = func.get("name", "unknown")
                    args_str = func.get("arguments", "{}")
                    try:
                        args = json.loads(args_str) if isinstance(args_str, str) else args_str
                    except Exception:
                        args = {}

                    _notify("tool_call", {"tool": tool_name, "args": args})
                    result = self._execute_tool(tc)

                    # Send truncated result as progress update
                    result_preview = result[:300] + ("..." if len(result) > 300 else "")
                    _notify("tool_result", {"tool": tool_name, "result": result_preview})

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.get("id", "unknown"),
                        "content": result[:2000],  # Cap tool result size
                    })

                next_round = round_num + 2
                if next_round <= max_tool_rounds:
                    _notify("round", {"round": next_round, "max": max_tool_rounds})
                continue
            else:
                # Final response — no more tool calls
                # Thread-safe history write
                with self._lock:
                    self._history.append({"role": "user", "content": message})
                    self._history.append({"role": "assistant", "content": resp})
                _notify("complete", {})
                return resp

        # Max rounds — ask for final response
        _notify("max_rounds", {})
        messages.append({"role": "user", "content": "Max tool calls reached. Provide your final response now."})
        configured = self._load_configured_model()
        models_to_try = []
        if configured:
            models_to_try.append(configured)
        models_to_try.append(self.current_model)
        for m in MODEL_CHAIN:
            if m not in models_to_try:
                models_to_try.append(m)
        for model in models_to_try:
            resp, _, used_model, err = self._call_llm(messages, model=model)
            if resp:
                with self._lock:
                    self._history.append({"role": "user", "content": message})
                    self._history.append({"role": "assistant", "content": resp})
                return resp

        return "⚠️ All LLM providers failed after tool calls."

    def clear_history(self):
        with self._lock:
            self._history.clear()
