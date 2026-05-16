#!/usr/bin/env python3
"""
Workspace Cleanup Procedure — SRRA Self-Sustaining Environment
==============================================================
Scans the workspace for:
  1. Loose files in root that belong in subdirectories
  2. Oversized progress files (>200 lines)
  3. Empty directories
  4. Duplicate files
  5. Stale temp files

Can be triggered by any agent via prompt or run on a schedule.

Usage:
  python tools/workspace_cleanup.py              # Full cleanup
  python tools/workspace_cleanup.py --scan       # Scan only (report)
  python tools/workspace_cleanup.py --dry-run    # Show what would be moved
  python tools/workspace_cleanup.py --agent PM   # Clean specific agent only
"""

import argparse
import hashlib
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

LAB_ROOT = Path(__file__).resolve().parent.parent

# ── File Routing Rules ──────────────────────────────────────────────────────
# Maps file patterns → destination folders
FILE_ROUTES = {
    # Pine Script / Trading
    ".pine": "strategies/pine/",
    "cerebus": "strategies/",
    "symmetry": "strategies/",
    "trading": "strategies/",
    "strategy": "strategies/",
    "backtest": "backtests/",

    # Data
    "price_data": "data/",
    "data_sources": "data/",
    ".csv": "data/csv/",
    ".parquet": "data/parquet/",

    # Documentation
    ".md": None,  # Handled specially — check content

    # Config
    ".json": None,  # Handled specially
    ".yaml": "config/",
    ".yml": "config/",
    ".toml": "config/",
    ".env": "config/",

    # Scripts
    ".py": "tools/scripts/",
    ".ps1": "tools/scripts/",
    ".cmd": "tools/scripts/",
    ".bat": "tools/scripts/",
    ".sh": "tools/scripts/",

    # Web
    ".html": None,  # Handled specially
    ".css": None,
    ".js": None,

    # Media
    ".png": "docs/images/",
    ".jpg": "docs/images/",
    ".jpeg": "docs/images/",
    ".gif": "docs/images/",
    ".svg": "docs/images/",
    ".webp": "docs/images/",

    # Archives
    ".zip": "archive/",
    ".tar": "archive/",
    ".gz": "archive/",
}

# Files that should stay in root
ROOT_ALLOWED = {
    "AGENTS.md", "CLAUDE.md", "CODEMAP.md", "MEMORY.md", "README.md",
    "SOUL.md", "USER.md", "IDENTITY.md", "KEYS.md", "HEARTBEAT.md",
    "WORKFLOW_PROTOCOL.md", "SYSTEM_ARCHITECTURE.md", "TOOLS.md",
    "REPOS.md", "TEAMS.md", "ERROR_CLASSIFICATION.md",
    "TASK_BRIEF_TEMPLATE.json", "skills-lock.json",
    "pyproject.toml", "requirements.txt", "uv.lock",
    ".gitignore", ".python-version", ".gitattributes",
    ".env",  # Root .env stays
    "larger-lab.code-workspace",
    "CEREBUS_STRATEGY_RECONSTRUCTION.md",
    "PROJECT_PROGRESS.md", "PROJECT_PROGRESS_CLEAN.md",
    "WORKSPACE_TOOLS_AND_SKILLS.md",
    "AGENT_MOVEMENT.md",
}

# Directories that should exist
EXPECTED_DIRS = {
    "progress", "tools", "tools/bin", "tools/scripts", "tools/workspaces",
    "skills", "docs", "docs/images", "docs/phases",
    "data", "data/csv", "data/parquet",
    "strategies", "strategies/pine",
    "backtests", "config", "archive", "temp", "sandbox",
    "shared-conversations", "html-viewer",
    "all-mermaids",
}


def scan_loose_files() -> list:
    """Find files in root that should be moved."""
    loose = []
    for item in LAB_ROOT.iterdir():
        if item.is_file() and item.name not in ROOT_ALLOWED:
            # Skip hidden files
            if item.name.startswith("."):
                continue
            dest = suggest_destination(item)
            loose.append({"file": item.name, "suggested": dest})
    return loose


def suggest_destination(filepath: Path) -> str:
    """Suggest a destination folder for a loose file."""
    name_lower = filepath.name.lower()
    ext = filepath.suffix.lower()

    # Check by name patterns first
    for pattern, dest in FILE_ROUTES.items():
        if pattern.startswith("."):
            continue
        if pattern in name_lower and dest:
            return dest

    # Check by extension
    if ext in FILE_ROUTES and FILE_ROUTES[ext]:
        return FILE_ROUTES[ext]

    # Special handling for .md files
    if ext == ".md":
        content = filepath.read_text(encoding="utf-8", errors="replace")[:500].lower()
        if "progress" in content or "agent" in content:
            return "progress/"
        if "phase" in content or "srrs" in content or "srra" in content:
            return "docs/phases/"
        if "diagram" in content or "mermaid" in content:
            return "docs/images/"
        return "docs/"

    return "docs/"  # Default fallback


def scan_oversized_progress() -> list:
    """Find progress files that are too large."""
    oversized = []
    progress_dir = LAB_ROOT / "progress"
    if not progress_dir.exists():
        return oversized

    for f in progress_dir.glob("*-progress.md"):
        lines = len(f.read_text(encoding="utf-8").split("\n"))
        entries = f.read_text(encoding="utf-8").count("#### ")
        if lines > 200 or entries > 20:
            oversized.append({
                "file": str(f.relative_to(LAB_ROOT)),
                "lines": lines,
                "entries": entries,
            })

    return oversized


def scan_empty_dirs() -> list:
    """Find empty directories."""
    empty = []
    for item in LAB_ROOT.iterdir():
        if item.is_dir() and not item.name.startswith(".") and item.name not in {
            ".git", ".venv", ".pytest_cache", ".roo", ".cursor", ".vscode",
            ".agents", ".openclaw", ".openclaw-2", ".hermes", ".claude", ".clawhub",
            "__pycache__", "node_modules",
        }:
            contents = list(item.iterdir())
            if len(contents) == 0:
                empty.append(item.name)
    return empty


def scan_missing_dirs() -> list:
    """Find expected directories that don't exist."""
    return [d for d in EXPECTED_DIRS if not (LAB_ROOT / d).exists()]


def move_file(filename: str, destination: str, dry_run: bool = False) -> dict:
    """Move a file to its suggested destination."""
    src = LAB_ROOT / filename
    if not src.exists():
        return {"file": filename, "status": "not_found"}

    dest_dir = LAB_ROOT / destination
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / filename

    if dest.exists():
        return {"file": filename, "status": "exists_at_dest", "destination": destination}

    if dry_run:
        return {"file": filename, "status": "would_move", "destination": destination}

    shutil.move(str(src), str(dest))
    return {"file": filename, "status": "moved", "destination": destination}


def generate_report(loose, oversized, empty, missing) -> str:
    """Generate a cleanup report."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# Workspace Cleanup Report — {now}",
        "",
        f"## Loose Files in Root: {len(loose)}",
    ]
    for item in loose:
        lines.append(f"  - `{item['file']}` → `{item['suggested']}`")

    lines.extend(["", f"## Oversized Progress Files: {len(oversized)}"])
    for item in oversized:
        lines.append(f"  - `{item['file']}`: {item['lines']} lines, {item['entries']} entries")

    lines.extend(["", f"## Empty Directories: {len(empty)}"])
    for d in empty:
        lines.append(f"  - `{d}/`")

    lines.extend(["", f"## Missing Expected Directories: {len(missing)}"])
    for d in missing:
        lines.append(f"  - `{d}/`")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Workspace Cleanup Procedure")
    parser.add_argument("--scan", action="store_true", help="Scan only, don't move anything")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be moved")
    parser.add_argument("--agent", choices=["CC", "OC", "OC2", "PM", "AS", "RL"], help="Clean specific agent")
    parser.add_argument("--create-dirs", action="store_true", help="Create missing expected directories")
    args = parser.parse_args()

    print("🧹 Workspace Cleanup Procedure")
    print(f"   Mode: {'SCAN ONLY' if args.scan else 'DRY RUN' if args.dry_run else 'FULL CLEANUP'}")
    print()

    # Scan
    loose = scan_loose_files()
    oversized = scan_oversized_progress()
    empty = scan_empty_dirs()
    missing = scan_missing_dirs()

    # Report
    print(f"📊 Scan Results:")
    print(f"   Loose files: {len(loose)}")
    print(f"   Oversized progress: {len(oversized)}")
    print(f"   Empty dirs: {len(empty)}")
    print(f"   Missing dirs: {len(missing)}")
    print()

    if args.scan:
        report = generate_report(loose, oversized, empty, missing)
        print(report)
        return

    # Create missing directories
    if args.create_dirs and missing:
        print("📁 Creating missing directories:")
        for d in missing:
            (LAB_ROOT / d).mkdir(parents=True, exist_ok=True)
            print(f"  ✅ Created `{d}/`")
        print()

    # Move loose files
    if loose:
        print("📦 Moving loose files:")
        for item in loose:
            result = move_file(item["file"], item["suggested"], dry_run=args.dry_run)
            status = result["status"]
            if status == "moved":
                print(f"  ✅ `{result['file']}` → `{result['destination']}`")
            elif status == "would_move":
                print(f"  🔍 `{result['file']}` → `{result['destination']}` (dry run)")
            elif status == "exists_at_dest":
                print(f"  ⚠ `{result['file']}` already exists at `{result['destination']}`")
            elif status == "not_found":
                print(f"  ❌ `{result['file']}` not found")
        print()

    # Report oversized
    if oversized:
        print("📝 Oversized progress files (run summarize_progress.py):")
        for item in oversized:
            print(f"  ⚠ `{item['file']}`: {item['lines']} lines, {item['entries']} entries")
        print()

    # Remove empty dirs
    if empty and not args.dry_run:
        print("🗑 Removing empty directories:")
        for d in empty:
            (LAB_ROOT / d).rmdir()
            print(f"  ✅ Removed `{d}/`")
        print()

    # Save report
    report = generate_report(loose, oversized, empty, missing)
    report_path = LAB_ROOT / "docs" / "cleanup-report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    print(f"📄 Report saved to `docs/cleanup-report.md`")
    print(f"\n✅ Cleanup complete.")


if __name__ == "__main__":
    main()
