"""
PO Tool Registry — Dynamic tool discovery and invocation for Primary Observer.

Provides a unified registry of ALL tools available to PO, including:
1. Native Python tools (file ops, git, search, exec)
2. MCP server tools (time, search, hermes, etc.)
3. OCE internal API calls
4. VS Code command execution
5. GitHub operations
6. Browser automation
7. Memory system access
8. Semantic search
9. Notebook operations
10. PDF/document tools

Each tool is registered with its name, description, input schema (OpenAI format),
and an async callable. POAgent uses this registry to build its TOOL_DEFINITIONS
dynamically, so when new MCP servers are added, PO automatically gets their tools.
"""

from __future__ import annotations

import json
import logging
import subprocess
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional

logger = logging.getLogger("oce.po_tools")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass
class ToolDefinition:
    """A single tool definition in OpenAI function calling format."""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Optional[Callable[..., Awaitable[Any]]] = None
    category: str = "general"

    def to_openai(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    """
    Central registry for all PO tools.

    Tools are organized by category:
    - file: read, write, edit, list, search
    - git: status, log, diff, commit, push, branch
    - exec: run_command, execute_python
    - search: content_search, semantic_search, file_search
    - github: pr, issue, ci, search
    - browser: open, click, type, screenshot, read
    - memory: read_memory, write_memory, search_memory
    - mcp: dynamic MCP server tools
    - vscode: command_execution, symbol_rename, find_usages
    - notebook: read_cell, run_cell, edit_cell
    - pdf: extract_text, merge, split, compress
    - system: get_env, set_env, get_processes, kill_process
    """

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._categories: Dict[str, List[str]] = {}
        self._register_all()

    def register(self, tool: ToolDefinition):
        """Register a tool."""
        self._tools[tool.name] = tool
        cat = tool.category
        if cat not in self._categories:
            self._categories[cat] = []
        self._categories[cat].append(tool.name)

    def get(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self, category: str = None) -> List[ToolDefinition]:
        """List all tools, optionally filtered by category."""
        if category:
            names = self._categories.get(category, [])
            return [self._tools[n] for n in names if n in self._tools]
        return list(self._tools.values())

    def to_openai_tools(self) -> List[Dict[str, Any]]:
        """Export all tools in OpenAI function calling format."""
        return [t.to_openai() for t in self._tools.values()]

    def to_json_schema(self) -> Dict[str, Any]:
        """Export registry as JSON schema for frontend consumption."""
        return {
            "tools": [
                {
                    "name": t.name,
                    "description": t.description,
                    "category": t.category,
                    "parameters": t.parameters,
                }
                for t in self._tools.values()
            ],
            "categories": {
                cat: [{"name": n, "description": self._tools[n].description}
                      for n in names if n in self._tools]
                for cat, names in self._categories.items()
            },
            "total": len(self._tools),
        }

    # ─── Register All Tools ──────────────────────────────────────────────

    def _register_all(self):
        """Register all available tools."""
        self._register_file_tools()
        self._register_git_tools()
        self._register_exec_tools()
        self._register_search_tools()
        self._register_github_tools()
        self._register_browser_tools()
        self._register_memory_tools()
        self._register_vscode_tools()
        self._register_notebook_tools()
        self._register_pdf_tools()
        self._register_system_tools()
        self._register_semantic_tools()
        self._register_task_tools()

    def _register_file_tools(self):
        """File operation tools."""
        self.register(ToolDefinition(
            name="list_directory",
            description="List files and directories. Use to explore workspace structure.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path from repo root, or '.' for root"},
                    "max_depth": {"type": "integer", "description": "Max directory depth (default 2)"},
                    "max_items": {"type": "integer", "description": "Max items to list (default 50)"},
                },
                "required": [],
            },
            category="file",
        ))
        self.register(ToolDefinition(
            name="read_file",
            description="Read a file's contents. Use to examine code, configs, logs, etc.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path from repo root"},
                    "start_line": {"type": "integer", "description": "Starting line number (1-indexed, default 1)"},
                    "max_lines": {"type": "integer", "description": "Max lines to read (default 200)"},
                },
                "required": ["path"],
            },
            category="file",
        ))
        self.register(ToolDefinition(
            name="write_file",
            description="Write content to a file. Creates the file if it doesn't exist, overwrites if it does.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path from repo root"},
                    "content": {"type": "string", "description": "Full file content to write"},
                },
                "required": ["path", "content"],
            },
            category="file",
        ))
        self.register(ToolDefinition(
            name="edit_file",
            description="Edit a file by replacing exact text. The old_text must match exactly including whitespace.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path from repo root"},
                    "old_text": {"type": "string", "description": "Exact text to find and replace"},
                    "new_text": {"type": "string", "description": "New text to replace the old text with"},
                },
                "required": ["path", "old_text", "new_text"],
            },
            category="file",
        ))
        self.register(ToolDefinition(
            name="multi_edit_file",
            description="Apply multiple replace operations to a file in a single call.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path from repo root"},
                    "edits": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "old_text": {"type": "string"},
                                "new_text": {"type": "string"},
                            },
                            "required": ["old_text", "new_text"],
                        },
                        "description": "List of edit operations",
                    },
                },
                "required": ["path", "edits"],
            },
            category="file",
        ))
        self.register(ToolDefinition(
            name="create_directory",
            description="Create a new directory structure. Creates all intermediate directories.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path from repo root"},
                },
                "required": ["path"],
            },
            category="file",
        ))
        self.register(ToolDefinition(
            name="delete_file",
            description="Delete a file or directory. Use with caution.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path from repo root"},
                    "recursive": {"type": "boolean", "description": "Delete directory recursively (default false)"},
                },
                "required": ["path"],
            },
            category="file",
        ))
        self.register(ToolDefinition(
            name="file_exists",
            description="Check if a file or directory exists.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path from repo root"},
                },
                "required": ["path"],
            },
            category="file",
        ))

    def _register_git_tools(self):
        """Git operation tools."""
        for name, desc, params in [
            ("git_status", "Get git status — shows modified, added, deleted files.", {}),
            ("git_log", "Get recent git commit history.", {
                "count": {"type": "integer", "description": "Number of commits (default 10)"},
            }),
            ("git_diff", "Get git diff for a file or the whole repo.", {
                "file_path": {"type": "string", "description": "Specific file path, or empty for all"},
                "cached": {"type": "boolean", "description": "Show staged changes (default false)"},
            }),
            ("git_commit", "Stage and commit changes.", {
                "message": {"type": "string", "description": "Commit message"},
                "files": {"type": "array", "items": {"type": "string"}, "description": "Files to stage, or ['all'] for git add -A"},
            }),
            ("git_push", "Push commits to remote.", {
                "remote": {"type": "string", "description": "Remote name (default 'origin')"},
                "branch": {"type": "string", "description": "Branch name (default current)"},
                "force": {"type": "boolean", "description": "Force push (default false)"},
            }),
            ("git_pull", "Pull latest changes from remote.", {
                "remote": {"type": "string", "description": "Remote name (default 'origin')"},
                "branch": {"type": "string", "description": "Branch name (default current)"},
            }),
            ("git_branch", "List, create, or delete branches.", {
                "action": {"type": "string", "description": "Action: list, create, delete, checkout"},
                "name": {"type": "string", "description": "Branch name (for create/delete/checkout)"},
            }),
            ("git_stash", "Stash current changes.", {
                "action": {"type": "string", "description": "Action: push, pop, list, clear"},
                "message": {"type": "string", "description": "Stash message (for push)"},
            }),
            ("git_blame", "Show who last modified each line of a file.", {
                "file_path": {"type": "string", "description": "File path"},
            }),
        ]:
            props = {k: v for k, v in params.items()}
            req = []
            for k, v in props.items():
                if k in ("message", "file_path", "action"):
                    req.append(k)
            self.register(ToolDefinition(
                name=name,
                description=desc,
                parameters={
                    "type": "object",
                    "properties": props,
                    "required": req,
                },
                category="git",
            ))

    def _register_exec_tools(self):
        """Execution tools."""
        self.register(ToolDefinition(
            name="run_command",
            description="Run a shell command (PowerShell on Windows). Use for git, python, npm, etc. Be careful with destructive commands.",
            parameters={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds (default 30)"},
                    "cwd": {"type": "string", "description": "Working directory relative to repo root"},
                    "env": {"type": "object", "description": "Environment variables to set"},
                },
                "required": ["command"],
            },
            category="exec",
        ))
        self.register(ToolDefinition(
            name="execute_python",
            description="Execute Python code in the project virtualenv. Use for data analysis, testing, automation.",
            parameters={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Python code to execute"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds (default 60)"},
                    "args": {"type": "array", "items": {"type": "string"}, "description": "Command-line arguments"},
                },
                "required": ["code"],
            },
            category="exec",
        ))
        self.register(ToolDefinition(
            name="run_python_file",
            description="Run a Python file in the project virtualenv.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to Python file"},
                    "timeout": {"type": "integer", "description": "Timeout in seconds (default 120)"},
                    "args": {"type": "array", "items": {"type": "string"}, "description": "Command-line arguments"},
                },
                "required": ["path"],
            },
            category="exec",
        ))
        self.register(ToolDefinition(
            name="install_python_package",
            description="Install a Python package in the project virtualenv.",
            parameters={
                "type": "object",
                "properties": {
                    "package": {"type": "string", "description": "Package name (e.g., 'requests', 'numpy>=1.24')"},
                    "upgrade": {"type": "boolean", "description": "Upgrade if already installed (default false)"},
                },
                "required": ["package"],
            },
            category="exec",
        ))

    def _register_search_tools(self):
        """Search tools."""
        self.register(ToolDefinition(
            name="search_files",
            description="Search for files by name pattern (glob). Use *.py for Python files, *.md for markdown, etc.",
            parameters={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Glob pattern like *.py, *.md, *test*"},
                    "path": {"type": "string", "description": "Directory to search in (default repo root)"},
                    "max_results": {"type": "integer", "description": "Max results (default 20)"},
                },
                "required": ["pattern"],
            },
            category="search",
        ))
        self.register(ToolDefinition(
            name="search_content",
            description="Search for text within file contents. Use to find code, references, etc.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Text to search for"},
                    "path": {"type": "string", "description": "Directory to search in"},
                    "file_pattern": {"type": "string", "description": "File glob pattern (default *.py)"},
                    "max_results": {"type": "integer", "description": "Max files to return (default 10)"},
                    "case_sensitive": {"type": "boolean", "description": "Case sensitive search (default false)"},
                    "is_regex": {"type": "boolean", "description": "Treat query as regex (default false)"},
                },
                "required": ["query"],
            },
            category="search",
        ))
        self.register(ToolDefinition(
            name="grep_search",
            description="Fast text search with regex support. More powerful than search_content.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Regex pattern to search for"},
                    "path": {"type": "string", "description": "Directory or file to search in"},
                    "file_pattern": {"type": "string", "description": "File glob pattern (default *.*)"},
                    "max_results": {"type": "integer", "description": "Max results (default 50)"},
                    "case_sensitive": {"type": "boolean", "description": "Case sensitive (default false)"},
                },
                "required": ["query"],
            },
            category="search",
        ))

    def _register_github_tools(self):
        """GitHub operation tools."""
        for name, desc, params in [
            ("github_pr_list", "List pull requests.", {
                "state": {"type": "string", "description": "State: open, closed, merged, all (default open)"},
                "limit": {"type": "integer", "description": "Max results (default 30)"},
            }),
            ("github_pr_create", "Create a pull request.", {
                "title": {"type": "string", "description": "PR title"},
                "body": {"type": "string", "description": "PR body/description"},
                "head": {"type": "string", "description": "Head branch"},
                "base": {"type": "string", "description": "Base branch (default main)"},
                "draft": {"type": "boolean", "description": "Create as draft (default false)"},
            }),
            ("github_pr_view", "View a pull request.", {
                "number": {"type": "integer", "description": "PR number"},
            }),
            ("github_pr_merge", "Merge a pull request.", {
                "number": {"type": "integer", "description": "PR number"},
                "method": {"type": "string", "description": "Merge method: merge, squash, rebase (default merge)"},
            }),
            ("github_issue_list", "List issues.", {
                "state": {"type": "string", "description": "State: open, closed, all (default open)"},
                "limit": {"type": "integer", "description": "Max results (default 30)"},
            }),
            ("github_issue_create", "Create an issue.", {
                "title": {"type": "string", "description": "Issue title"},
                "body": {"type": "string", "description": "Issue body"},
                "labels": {"type": "array", "items": {"type": "string"}, "description": "Labels"},
            }),
            ("github_ci_status", "Check CI/workflow status.", {
                "limit": {"type": "integer", "description": "Number of runs (default 10)"},
            }),
            ("github_search", "Search GitHub for issues or PRs.", {
                "query": {"type": "string", "description": "Search query"},
                "type": {"type": "string", "description": "Type: issue, pr (default issue)"},
            }),
            ("github_repo_info", "Get repository information.", {}),
        ]:
            props = {k: v for k, v in params.items()}
            req = [k for k in props if k in ("title", "number", "query", "head")]
            self.register(ToolDefinition(
                name=name,
                description=desc,
                parameters={
                    "type": "object",
                    "properties": props,
                    "required": req,
                },
                category="github",
            ))

    def _register_browser_tools(self):
        """Browser automation tools."""
        self.register(ToolDefinition(
            name="browser_open",
            description="Open a URL in the browser.",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to open"},
                    "new_tab": {"type": "boolean", "description": "Open in new tab (default true)"},
                },
                "required": ["url"],
            },
            category="browser",
        ))
        self.register(ToolDefinition(
            name="browser_screenshot",
            description="Take a screenshot of the current browser page.",
            parameters={
                "type": "object",
                "properties": {
                    "ref": {"type": "string", "description": "Element reference to capture (optional, default full page)"},
                    "save_path": {"type": "string", "description": "Path to save screenshot (optional)"},
                },
                "required": [],
            },
            category="browser",
        ))
        self.register(ToolDefinition(
            name="browser_click",
            description="Click an element in the browser.",
            parameters={
                "type": "object",
                "properties": {
                    "ref": {"type": "string", "description": "Element reference to click"},
                    "double_click": {"type": "boolean", "description": "Double click (default false)"},
                },
                "required": ["ref"],
            },
            category="browser",
        ))
        self.register(ToolDefinition(
            name="browser_type",
            description="Type text into an element in the browser.",
            parameters={
                "type": "object",
                "properties": {
                    "ref": {"type": "string", "description": "Element reference"},
                    "text": {"type": "string", "description": "Text to type"},
                    "clear_first": {"type": "boolean", "description": "Clear existing text (default true)"},
                },
                "required": ["ref", "text"],
            },
            category="browser",
        ))
        self.register(ToolDefinition(
            name="browser_read",
            description="Read the current browser page content.",
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
            category="browser",
        ))
        self.register(ToolDefinition(
            name="browser_navigate",
            description="Navigate the browser (back, forward, reload, or to URL).",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Action: back, forward, reload, url"},
                    "url": {"type": "string", "description": "URL (for url action)"},
                },
                "required": ["action"],
            },
            category="browser",
        ))

    def _register_memory_tools(self):
        """Memory system tools."""
        self.register(ToolDefinition(
            name="memory_read",
            description="Read a memory file. Scopes: user, session, repo.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path relative to /memories/ (e.g., 'notes.md', 'session/plan.md')"},
                },
                "required": ["path"],
            },
            category="memory",
        ))
        self.register(ToolDefinition(
            name="memory_write",
            description="Write/create a memory file.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path relative to /memories/"},
                    "content": {"type": "string", "description": "File content"},
                },
                "required": ["path", "content"],
            },
            category="memory",
        ))
        self.register(ToolDefinition(
            name="memory_list",
            description="List memory files in a scope.",
            parameters={
                "type": "object",
                "properties": {
                    "scope": {"type": "string", "description": "Scope: user, session, repo (default user)"},
                },
                "required": [],
            },
            category="memory",
        ))
        self.register(ToolDefinition(
            name="memory_search",
            description="Search across all memory files for a query string.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "scope": {"type": "string", "description": "Scope: user, session, repo, or all (default all)"},
                },
                "required": ["query"],
            },
            category="memory",
        ))

    def _register_vscode_tools(self):
        """VS Code integration tools."""
        self.register(ToolDefinition(
            name="vscode_run_command",
            description="Run a VS Code command by ID.",
            parameters={
                "type": "object",
                "properties": {
                    "command_id": {"type": "string", "description": "VS Code command ID (e.g., 'workbench.action.files.save')"},
                    "args": {"type": "array", "items": {"type": "string"}, "description": "Command arguments"},
                },
                "required": ["command_id"],
            },
            category="vscode",
        ))
        self.register(ToolDefinition(
            name="vscode_find_symbol_usages",
            description="Find all usages/references of a code symbol across the workspace.",
            parameters={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Symbol name (function, class, variable, etc.)"},
                    "file_path": {"type": "string", "description": "File where the symbol appears"},
                    "line_content": {"type": "string", "description": "Line content containing the symbol"},
                },
                "required": ["symbol", "line_content"],
            },
            category="vscode",
        ))
        self.register(ToolDefinition(
            name="vscode_rename_symbol",
            description="Rename a code symbol across the workspace.",
            parameters={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Current symbol name"},
                    "new_name": {"type": "string", "description": "New name for the symbol"},
                    "file_path": {"type": "string", "description": "File where the symbol appears"},
                    "line_content": {"type": "string", "description": "Line content containing the symbol"},
                },
                "required": ["symbol", "new_name", "line_content"],
            },
            category="vscode",
        ))
        self.register(ToolDefinition(
            name="vscode_get_errors",
            description="Get compile/lint errors for a file or the whole workspace.",
            parameters={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Specific file path, or empty for all"},
                },
                "required": [],
            },
            category="vscode",
        ))
        self.register(ToolDefinition(
            name="vscode_list_extensions",
            description="List installed VS Code extensions.",
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
            category="vscode",
        ))

    def _register_notebook_tools(self):
        """Jupyter notebook tools."""
        self.register(ToolDefinition(
            name="notebook_list",
            description="List Jupyter notebooks in the workspace.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory to search (default repo root)"},
                },
                "required": [],
            },
            category="notebook",
        ))
        self.register(ToolDefinition(
            name="notebook_read",
            description="Read a notebook's structure (cells, types, languages).",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to .ipynb file"},
                },
                "required": ["path"],
            },
            category="notebook",
        ))
        self.register(ToolDefinition(
            name="notebook_run_cell",
            description="Run a code cell in a notebook.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to .ipynb file"},
                    "cell_id": {"type": "string", "description": "Cell ID to run"},
                },
                "required": ["path", "cell_id"],
            },
            category="notebook",
        ))
        self.register(ToolDefinition(
            name="notebook_edit_cell",
            description="Edit a cell in a notebook.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to .ipynb file"},
                    "cell_id": {"type": "string", "description": "Cell ID to edit"},
                    "new_code": {"type": "string", "description": "New cell content"},
                    "language": {"type": "string", "description": "Cell language: python, markdown, etc."},
                },
                "required": ["path", "cell_id", "new_code"],
            },
            category="notebook",
        ))

    def _register_pdf_tools(self):
        """PDF/document tools."""
        self.register(ToolDefinition(
            name="pdf_extract_text",
            description="Extract text from a PDF file.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to PDF file"},
                    "pages": {"type": "string", "description": "Page range (e.g., '1-5', 'all')"},
                },
                "required": ["path"],
            },
            category="pdf",
        ))
        self.register(ToolDefinition(
            name="pdf_merge",
            description="Merge multiple PDF files into one.",
            parameters={
                "type": "object",
                "properties": {
                    "files": {"type": "array", "items": {"type": "string"}, "description": "PDF file paths"},
                    "output": {"type": "string", "description": "Output file path"},
                },
                "required": ["files", "output"],
            },
            category="pdf",
        ))
        self.register(ToolDefinition(
            name="pdf_split",
            description="Split a PDF into individual pages or ranges.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "PDF file path"},
                    "output_dir": {"type": "string", "description": "Output directory"},
                    "pages": {"type": "string", "description": "Page range to split (e.g., '1-5')"},
                },
                "required": ["path"],
            },
            category="pdf",
        ))
        self.register(ToolDefinition(
            name="pdf_compress",
            description="Compress a PDF to reduce file size.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "PDF file path"},
                    "output": {"type": "string", "description": "Output file path"},
                    "quality": {"type": "string", "description": "Quality: low, medium, high (default medium)"},
                },
                "required": ["path"],
            },
            category="pdf",
        ))

    def _register_system_tools(self):
        """System/OS tools."""
        self.register(ToolDefinition(
            name="system_env",
            description="Get or set environment variables.",
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "Action: get, set, list (default get)"},
                    "name": {"type": "string", "description": "Variable name"},
                    "value": {"type": "string", "description": "Variable value (for set action)"},
                },
                "required": [],
            },
            category="system",
        ))
        self.register(ToolDefinition(
            name="system_processes",
            description="List running processes.",
            parameters={
                "type": "object",
                "properties": {
                    "filter": {"type": "string", "description": "Filter by process name (optional)"},
                },
                "required": [],
            },
            category="system",
        ))
        self.register(ToolDefinition(
            name="system_kill_process",
            description="Kill a process by PID or name.",
            parameters={
                "type": "object",
                "properties": {
                    "pid": {"type": "integer", "description": "Process ID"},
                    "name": {"type": "string", "description": "Process name (alternative to PID)"},
                    "force": {"type": "boolean", "description": "Force kill (default false)"},
                },
                "required": [],
            },
            category="system",
        ))
        self.register(ToolDefinition(
            name="system_disk_usage",
            description="Get disk usage information.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to check (default repo root)"},
                },
                "required": [],
            },
            category="system",
        ))
        self.register(ToolDefinition(
            name="system_info",
            description="Get system information (OS, CPU, memory, Python version).",
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
            category="system",
        ))

    def _register_semantic_tools(self):
        """Semantic search and AI tools."""
        self.register(ToolDefinition(
            name="semantic_search",
            description="Natural language search for relevant code or documentation in the workspace. Uses AI to find semantically related content.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language query describing what you're looking for"},
                },
                "required": ["query"],
            },
            category="search",
        ))
        self.register(ToolDefinition(
            name="web_fetch",
            description="Fetch and extract content from a URL.",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"},
                    "query": {"type": "string", "description": "Optional: specific content to extract"},
                },
                "required": ["url"],
            },
            category="search",
        ))
        self.register(ToolDefinition(
            name="web_search",
            description="Search the web using DuckDuckGo.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "description": "Max results (default 10)"},
                },
                "required": ["query"],
            },
            category="search",
        ))

    def _register_task_tools(self):
        """Task management tools."""
        self.register(ToolDefinition(
            name="task_list",
            description="Get the current task/todo list.",
            parameters={
                "type": "object",
                "properties": {},
                "required": [],
            },
            category="system",
        ))
        self.register(ToolDefinition(
            name="task_update",
            description="Update the task/todo list.",
            parameters={
                "type": "object",
                "properties": {
                    "tasks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "title": {"type": "string"},
                                "status": {"type": "string", "enum": ["not-started", "in-progress", "completed"]},
                            },
                            "required": ["id", "title", "status"],
                        },
                    },
                },
                "required": ["tasks"],
            },
            category="system",
        ))
        self.register(ToolDefinition(
            name="spawn_subagent",
            description="Spawn a subagent for complex multi-step tasks. Use for research, code exploration, or parallel work.",
            parameters={
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "Detailed task description"},
                    "agent_type": {"type": "string", "description": "Type: explore, build, debug, research"},
                },
                "required": ["task", "agent_type"],
            },
            category="system",
        ))
        self.register(ToolDefinition(
            name="vault_search",
            description="Search the Obsidian vault for notes.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search keywords"},
                    "max_results": {"type": "integer", "description": "Max results (default 10)"},
                },
                "required": ["query"],
            },
            category="memory",
        ))
        self.register(ToolDefinition(
            name="vault_read",
            description="Read a specific vault note by path.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path relative to vault root"},
                },
                "required": ["path"],
            },
            category="memory",
        ))
