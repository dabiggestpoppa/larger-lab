"""
OCE VS Code Bridge — Phase B
==============================
Controls VS Code via its CLI (`code` command) and desktop input simulation.

Uses:
- subprocess to run `code` CLI commands
- DesktopController (from desktop_control) for hotkey-based editor control
- VS Code CLI path: C:\\Users\\wifik\\AppData\\Local\\Programs\\Microsoft VS Code\\bin\\code.cmd

Architecture:
    VSCodeBridge
    ├── File Operations     (open, open_folder, new_file, save, close)
    ├── Editor Control      (go_to_line, find, replace, format)
    ├── Terminal Control    (open_terminal, run_command, run_in_terminal)
    ├── Extension Management (install, list, uninstall)
    ├── Workspace Management (active_file, workspace_folders, open_files)
    └── Git Integration     (status, commit, push, pull)
"""

import subprocess
import json
import os
import sys
import shutil
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

# ─── Constants ───────────────────────────────────────────────────────────────

CODE_CLI = r"C:\Users\wifik\AppData\Local\Programs\Microsoft VS Code\bin\code.cmd"
FALLBACK_CODE = "code"  # if the above doesn't exist, try PATH


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _find_code_cli() -> str:
    """Resolve the VS Code CLI path. Raises if not found."""
    if os.path.isfile(CODE_CLI):
        return CODE_CLI
    found = shutil.which("code")
    if found:
        return found
    raise FileNotFoundError(
        "VS Code CLI not found. Expected at:\n"
        f"  {CODE_CLI}\n"
        "Or on PATH as 'code'. Install VS Code or add it to PATH."
    )


def _run_code(args: List[str], timeout: int = 30, capture: bool = True) -> Tuple[int, str, str]:
    """
    Run a `code` CLI command.
    Returns (returncode, stdout, stderr).
    """
    exe = _find_code_cli()
    cmd = [exe] + args
    try:
        proc = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except FileNotFoundError:
        raise FileNotFoundError(f"VS Code CLI not found: {exe}")
    except subprocess.TimeoutExpired:
        raise TimeoutError(f"VS Code CLI timed out after {timeout}s: {' '.join(cmd)}")


def _get_desktop_controller():
    """Lazy-import DesktopController to avoid circular deps."""
    try:
        from tools.operator.desktop_control import DesktopController
        return DesktopController()
    except ImportError:
        # Fallback: try direct import if running from tools/operator/
        try:
            from desktop_control import DesktopController
            return DesktopController()
        except ImportError:
            raise ImportError(
                "Cannot import DesktopController. "
                "Run from workspace root or ensure tools/operator/ is on PYTHONPATH."
            )


# ─── VS Code Bridge ──────────────────────────────────────────────────────────

class VSCodeBridge:
    """
    High-level interface to control VS Code.

    Combines CLI commands (for file ops, extensions, git) with
    desktop input simulation (for editor control like save, format, etc.).
    """

    def __init__(self, workspace: Optional[str] = None):
        """
        Args:
            workspace: Optional workspace folder path. Passed to --folder-uri where supported.
        """
        self.workspace = workspace
        self._dc = None  # lazy DesktopController
        # Verify CLI is available on init
        _find_code_cli()

    @property
    def desktop(self):
        """Lazy-init DesktopController for hotkey-based control."""
        if self._dc is None:
            self._dc = _get_desktop_controller()
        return self._dc

    # ── File Operations ───────────────────────────────────────────────────

    def open_file(self, path: str, line: Optional[int] = None) -> Dict[str, Any]:
        """Open a file in VS Code. Optionally jump to a line number."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {path}")
        args = ["--goto", str(p)] if line is None else ["--goto", f"{p}:{line}"]
        rc, out, err = _run_code(args)
        return {"ok": rc == 0, "action": "open_file", "path": str(path), "line": line, "stderr": err}

    def open_folder(self, path: str) -> Dict[str, Any]:
        """Open a folder/workspace in VS Code."""
        p = Path(path)
        if not p.is_dir():
            raise NotADirectoryError(f"Directory not found: {path}")
        rc, out, err = _run_code(["--new-window", str(p)])
        return {"ok": rc == 0, "action": "open_folder", "path": str(path), "stderr": err}

    def new_file(self, path: str) -> Dict[str, Any]:
        """Create and open a new file. Parent directory must exist."""
        p = Path(path)
        if not p.parent.exists():
            raise FileNotFoundError(f"Parent directory not found: {p.parent}")
        p.touch(exist_ok=True)
        return self.open_file(str(p))

    def save_file(self) -> Dict[str, Any]:
        """Save the current file (Ctrl+S)."""
        self.desktop.hotkey("control", "s")
        return {"ok": True, "action": "save_file"}

    def close_file(self) -> Dict[str, Any]:
        """Close the current editor tab (Ctrl+W)."""
        self.desktop.hotkey("control", "w")
        return {"ok": True, "action": "close_file"}

    # ── Editor Control ────────────────────────────────────────────────────

    def go_to_line(self, line: int) -> Dict[str, Any]:
        """Jump to a specific line (Ctrl+G, type line number, Enter)."""
        self.desktop.hotkey("control", "g")
        time.sleep(0.1)
        self.desktop.type(str(line))
        time.sleep(0.05)
        self.desktop.hotkey("enter")
        return {"ok": True, "action": "go_to_line", "line": line}

    def find_text(self, text: str) -> Dict[str, Any]:
        """Open find dialog and search for text (Ctrl+F)."""
        self.desktop.hotkey("control", "f")
        time.sleep(0.1)
        self.desktop.type(text)
        return {"ok": True, "action": "find_text", "text": text}

    def replace_text(self, find: str, replace: str) -> Dict[str, Any]:
        """Open replace dialog (Ctrl+H), fill in find/replace, execute."""
        self.desktop.hotkey("control", "h")
        time.sleep(0.1)
        self.desktop.type(find)
        time.sleep(0.05)
        self.desktop.hotkey("tab")
        time.sleep(0.05)
        self.desktop.type(replace)
        time.sleep(0.05)
        # Ctrl+Alt+Enter = Replace All
        self.desktop.hotkey("control", "alt", "enter")
        return {"ok": True, "action": "replace_text", "find": find, "replace": replace}

    def format_document(self) -> Dict[str, Any]:
        """Format the current document (Shift+Alt+F)."""
        self.desktop.hotkey("shift", "alt", "f")
        return {"ok": True, "action": "format_document"}

    # ── Terminal Control ──────────────────────────────────────────────────

    def open_terminal(self) -> Dict[str, Any]:
        """Open the integrated terminal (Ctrl+`)."""
        self.desktop.hotkey("control", "`")
        return {"ok": True, "action": "open_terminal"}

    def run_command(self, cmd: str) -> Dict[str, Any]:
        """
        Run a command in the integrated terminal.
        Assumes terminal is already open.
        """
        self.desktop.type(cmd)
        time.sleep(0.05)
        self.desktop.hotkey("enter")
        return {"ok": True, "action": "run_command", "command": cmd}

    def run_in_terminal(self, cmd: str) -> Dict[str, Any]:
        """Open terminal and run a command."""
        self.open_terminal()
        time.sleep(0.3)
        return self.run_command(cmd)

    # ── Extension Management ──────────────────────────────────────────────

    def install_extension(self, ext_id: str) -> Dict[str, Any]:
        """Install a VS Code extension by ID (e.g., 'ms-python.python')."""
        rc, out, err = _run_code(["--install-extension", ext_id, "--force"])
        return {"ok": rc == 0, "action": "install_extension", "extension": ext_id, "output": out, "stderr": err}

    def list_extensions(self) -> Dict[str, Any]:
        """List all installed extensions."""
        rc, out, err = _run_code(["--list-extensions", "--show-versions"])
        if rc != 0:
            return {"ok": False, "error": err}
        extensions = []
        for line in out.splitlines():
            line = line.strip()
            if "@' in line:
                name, version = line.rsplit("@", 1)
                extensions.append({"id": name, "version": version})
            elif line:
                extensions.append({"id": line, "version": None})
        return {"ok": True, "action": "list_extensions", "extensions": extensions, "count": len(extensions)}

    def uninstall_extension(self, ext_id: str) -> Dict[str, Any]:
        """Uninstall a VS Code extension by ID."""
        rc, out, err = _run_code(["--uninstall-extension", ext_id])
        return {"ok": rc == 0, "action": "uninstall_extension", "extension": ext_id, "stderr": err}

    # ── Workspace Management ──────────────────────────────────────────────

    def get_active_file(self) -> Dict[str, Any]:
        """
        Get the currently active file path.
        Uses the VS Code CLI with --status (which includes active editor info).
        """
        rc, out, err = _run_code(["--status"])
        if rc != 0:
            return {"ok": False, "error": err}
        # Parse the output for window info
        for line in out.splitlines():
            if "Window:" in line or "Workspace:" in line:
                return {"ok": True, "action": "get_active_file", "info": line.strip()}
        return {"ok": True, "action": "get_active_file", "raw": out}

    def get_workspace_folders(self) -> Dict[str, Any]:
        """Get workspace folders from the running VS Code instance."""
        # VS Code doesn't have a direct CLI for this, so we check common workspace files
        candidates = []
        workspace = self.workspace or os.getcwd()
        ws_path = Path(workspace)
        # Check for .code-workspace files
        for f in ws_path.glob("*.code-workspace"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                folders = data.get("folders", [])
                candidates.append({"workspace_file": str(f), "folders": folders})
            except (json.JSONDecodeError, OSError):
                candidates.append({"workspace_file": str(f), "error": "Could not parse"})
        return {"ok": True, "action": "get_workspace_folders", "workspaces": candidates}

    def get_open_files(self) -> Dict[str, Any]:
        """
        Get list of open editor tabs.
        VS Code CLI doesn't directly expose this, so we use --status as a proxy.
        """
        rc, out, err = _run_code(["--status"])
        if rc != 0:
            return {"ok": False, "error": err}
        return {"ok": True, "action": "get_open_files", "status_output": out}

    # ── Git Integration ───────────────────────────────────────────────────

    def _run_git_via_terminal(self, cmd: str) -> Dict[str, Any]:
        """Run a git command in the integrated terminal."""
        return self.run_in_terminal(cmd)

    def git_status(self) -> Dict[str, Any]:
        """Show git status via integrated terminal."""
        return self._run_git_via_terminal("git status")

    def git_commit(self, message: str) -> Dict[str, Any]:
        """Stage all changes and commit with a message."""
        self._run_git_via_terminal("git add .")
        time.sleep(0.2)
        # Escape quotes in message
        escaped = message.replace('"', '\\"')
        return self._run_git_via_terminal(f'git commit -m "{escaped}"')

    def git_push(self) -> Dict[str, Any]:
        """Push to remote."""
        return self._run_git_via_terminal("git push")

    def git_pull(self) -> Dict[str, Any]:
        """Pull from remote."""
        return self._run_git_via_terminal("git pull")

    def git_log(self, count: int = 10) -> Dict[str, Any]:
        """Show recent git log."""
        return self._run_git_via_terminal(f"git log --oneline -{count}")

    def git_diff(self) -> Dict[str, Any]:
        """Show git diff."""
        return self._run_git_via_terminal("git diff")

    def git_branch(self) -> Dict[str, Any]:
        """List git branches."""
        return self._run_git_via_terminal("git branch -a")


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="OCE VS Code Bridge")
    sub = parser.add_subparsers(dest="command", help="Command to execute")

    # File operations
    p = sub.add_parser("open", help="Open a file")
    p.add_argument("path", help="File path")
    p.add_argument("--line", "-l", type=int, default=None, help="Line number")

    p = sub.add_parser("folder", help="Open a folder/workspace")
    p.add_argument("path", help="Folder path")

    p = sub.add_parser("new", help="Create and open a new file")
    p.add_argument("path", help="File path")

    sub.add_parser("save", help="Save current file")
    sub.add_parser("close", help="Close current tab")

    # Editor control
    p = sub.add_parser("goto", help="Go to line")
    p.add_argument("line", type=int, help="Line number")

    p = sub.add_parser("find", help="Find text")
    p.add_argument("text", help="Text to find")

    p = sub.add_parser("replace", help="Find and replace")
    p.add_argument("find", help="Text to find")
    p.add_argument("replace", help="Replacement text")

    sub.add_parser("format", help="Format document")

    # Terminal
    sub.add_parser("terminal", help="Open integrated terminal")

    p = sub.add_parser("run", help="Run command in terminal")
    p.add_argument("cmd", help="Command to run")

    # Extensions
    p = sub.add_parser("install-ext", help="Install extension")
    p.add_argument("ext_id", help="Extension ID (e.g., ms-python.python)")

    sub.add_parser("list-ext", help="List installed extensions")

    p = sub.add_parser("uninstall-ext", help="Uninstall extension")
    p.add_argument("ext_id", help="Extension ID")

    # Workspace
    sub.add_parser("active", help="Get active file info")
    sub.add_parser("workspaces", help="Get workspace folders")
    sub.add_parser("tabs", help="Get open files/tabs")

    # Git
    sub.add_parser("git-status", help="Git status")
    sub.add_parser("git-push", help="Git push")
    sub.add_parser("git-pull", help="Git pull")
    sub.add_parser("git-log", help="Git log")
    sub.add_parser("git-diff", help="Git diff")
    sub.add_parser("git-branch", help="Git branches")

    p = sub.add_parser("git-commit", help="Git commit")
    p.add_argument("message", help="Commit message")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    try:
        bridge = VSCodeBridge()
    except FileNotFoundError as e:
        print(json.dumps({"ok": False, "error": str(e)}, indent=2))
        sys.exit(1)

    result = None

    # File operations
    if args.command == "open":
        result = bridge.open_file(args.path, args.line)
    elif args.command == "folder":
        result = bridge.open_folder(args.path)
    elif args.command == "new":
        result = bridge.new_file(args.path)
    elif args.command == "save":
        result = bridge.save_file()
    elif args.command == "close":
        result = bridge.close_file()

    # Editor control
    elif args.command == "goto":
        result = bridge.go_to_line(args.line)
    elif args.command == "find":
        result = bridge.find_text(args.text)
    elif args.command == "replace":
        result = bridge.replace_text(args.find, args.replace)
    elif args.command == "format":
        result = bridge.format_document()

    # Terminal
    elif args.command == "terminal":
        result = bridge.open_terminal()
    elif args.command == "run":
        result = bridge.run_in_terminal(args.cmd)

    # Extensions
    elif args.command == "install-ext":
        result = bridge.install_extension(args.ext_id)
    elif args.command == "list-ext":
        result = bridge.list_extensions()
    elif args.command == "uninstall-ext":
        result = bridge.uninstall_extension(args.ext_id)

    # Workspace
    elif args.command == "active":
        result = bridge.get_active_file()
    elif args.command == "workspaces":
        result = bridge.get_workspace_folders()
    elif args.command == "tabs":
        result = bridge.get_open_files()

    # Git
    elif args.command == "git-status":
        result = bridge.git_status()
    elif args.command == "git-commit":
        result = bridge.git_commit(args.message)
    elif args.command == "git-push":
        result = bridge.git_push()
    elif args.command == "git-pull":
        result = bridge.git_pull()
    elif args.command == "git-log":
        result = bridge.git_log()
    elif args.command == "git-diff":
        result = bridge.git_diff()
    elif args.command == "git-branch":
        result = bridge.git_branch()

    if result:
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
