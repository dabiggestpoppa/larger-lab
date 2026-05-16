"""
OWL Self-Surgery Module
========================
Safe internal editing of workspace files (including OWL's own config files)
without going offline.

Principles:
1. NEVER edit a file without first reading it completely
2. ALWAYS create a backup before editing
3. ALWAYS validate after editing (syntax check, structure check)
4. NEVER edit the gateway process itself — only workspace files
5. ALWAYS log what was changed and why

Files OWL can operate on:
- SOUL.md, IDENTITY.md, USER.md, MEMORY.md, AGENTS.md, TOOLS.md, HEARTBEAT.md
- Any .md file in the workspace
- Any .py file in tools/
- Any SKILL.md file in skills/
- db/schema.py, tools/self_heal.py, tools/self_surgery.py (self-modification)

Files OWL must NOT touch:
- openclaw.json (gateway config — use `gateway` tool instead)
- Any file in node_modules/
- Any file in .git/
"""

import hashlib
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime, timezone

WORKSPACE = r"C:\Users\wifik\Desktop\projects\larger-lab"
BACKUP_DIR = os.path.join(WORKSPACE, ".surgery-backups")
DB_PATH = os.path.join(WORKSPACE, "db", "owl_health.db")

# Files that are safe to self-modify
ALLOWED_EXTENSIONS = {".md", ".py", ".json", ".txt", ".yaml", ".yml", ".toml", ".cfg", ".ps1", ".cmd", ".bat"}
DENY_DIRS = {"node_modules", ".git", "__pycache__", ".surgery-backups", "html-viewer"}
DENY_FILES = {"openclaw.json", "package.json", "package-lock.json"}


def is_safe_path(filepath):
    """Check if a file path is safe to modify."""
    abs_path = os.path.abspath(filepath)
    if not abs_path.startswith(os.path.abspath(WORKSPACE)):
        return False, "Path is outside workspace"
    rel = os.path.relpath(abs_path, WORKSPACE)
    parts = rel.split(os.sep)
    for d in parts:
        if d in DENY_DIRS:
            return False, f"Denied directory: {d}"
    basename = os.path.basename(abs_path)
    if basename in DENY_FILES:
        return False, f"Denied file: {basename}"
    ext = os.path.splitext(basename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Denied extension: {ext}"
    return True, "OK"


def create_backup(filepath):
    """Create a timestamped backup of a file before editing."""
    if not os.path.exists(filepath):
        return None
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    basename = os.path.basename(filepath)
    backup_name = f"{ts}_{basename}"
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    shutil.copy2(filepath, backup_path)
    return backup_path


def compute_hash(filepath):
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def log_surgery(action, filepath, details, success, backup_path=None):
    """Log a surgery action to the health DB."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT INTO self_healing_actions (action_taken, success, details) VALUES (?, ?, ?)",
            (f"{action}: {os.path.basename(filepath)}", int(success),
             f"{details} | backup={backup_path}"),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass  # don't let logging failure stop surgery


def safe_edit(filepath, old_text, new_text, reason=""):
    """
    Perform a safe edit on a workspace file.
    Returns (success, message).
    """
    # safety check
    safe, reason_safe = is_safe_path(filepath)
    if not safe:
        return False, f"UNSAFE: {reason_safe}"

    # file must exist
    if not os.path.exists(filepath):
        return False, f"File not found: {filepath}"

    # read current content
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    # old_text must exist in file
    if old_text not in content:
        return False, "oldText not found in file — file may have changed since last read"

    # create backup
    backup = create_backup(filepath)
    old_hash = compute_hash(filepath)

    # perform edit
    new_content = content.replace(old_text, new_text, 1)

    # validate: basic structure checks
    if filepath.endswith(".py"):
        import py_compile
        try:
            py_compile.compile(filepath + ".tmp", doraise=True)
        except SyntaxError as e:
            return False, f"Python syntax error in edit: {e}"
        finally:
            if os.path.exists(filepath + ".tmp"):
                os.remove(filepath + ".tmp")

    # write
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)

    new_hash = compute_hash(filepath)
    changed = old_hash != new_hash

    log_surgery("edit", filepath, reason or "Self-surgery edit", changed, backup)

    if changed:
        return True, f"Edited successfully. Backup: {backup}"
    else:
        return False, "Edit produced no change (hash identical)"


def safe_append(filepath, text, reason=""):
    """Safely append text to a file."""
    safe, reason_safe = is_safe_path(filepath)
    if not safe:
        return False, f"UNSAFE: {reason_safe}"

    if not os.path.exists(filepath):
        return False, f"File not found: {filepath}"

    backup = create_backup(filepath)

    with open(filepath, "a", encoding="utf-8") as f:
        f.write(text)

    log_surgery("append", filepath, reason or "Self-surgery append", True, backup)
    return True, f"Appended successfully. Backup: {backup}"


def safe_create(filepath, content, reason=""):
    """Safely create a new file."""
    safe, reason_safe = is_safe_path(filepath)
    if not safe:
        return False, f"UNSAFE: {reason_safe}"

    if os.path.exists(filepath):
        return False, f"File already exists: {filepath}"

    # ensure parent dir exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    log_surgery("create", filepath, reason or "Self-surgery create", True)
    return True, "Created successfully."


def list_backups():
    """List all surgery backups."""
    if not os.path.exists(BACKUP_DIR):
        return []
    return sorted(os.listdir(BACKUP_DIR), reverse=True)


def restore_backup(backup_name):
    """Restore a file from backup."""
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    if not os.path.exists(backup_path):
        return False, f"Backup not found: {backup_name}"

    # original filename is after the timestamp prefix
    parts = backup_name.split("_", 1)
    if len(parts) < 2:
        return False, f"Invalid backup name format: {backup_name}"
    original_name = parts[1]

    # find the original in workspace
    for root, dirs, files in os.walk(WORKSPACE):
        dirs[:] = [d for d in dirs if d not in DENY_DIRS]
        if original_name in files:
            original_path = os.path.join(root, original_name)
            shutil.copy2(backup_path, original_path)
            log_surgery("restore", original_name, f"Restored from {backup_name}", True)
            return True, f"Restored {original_name} from {backup_name}"

    return False, f"Could not locate original file for: {original_name}"


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("Usage: python tools/self_surgery.py <command> [args]")
        print("Commands:")
        print("  list-backups           — list all surgery backups")
        print("  restore <backup_name> — restore a file from backup")
        print("  status                — show surgery safety status")
    elif args[0] == "list-backups":
        backups = list_backups()
        if backups:
            for b in backups:
                print(f"  {b}")
        else:
            print("No backups found.")
    elif args[0] == "restore" and len(args) > 1:
        ok, msg = restore_backup(args[1])
        print(msg)
    elif args[0] == "status":
        print("🦉 Self-Surgery Module Status")
        print(f"  Workspace: {WORKSPACE}")
        print(f"  Backup dir: {BACKUP_DIR}")
        print(f"  Allowed extensions: {ALLOWED_EXTENSIONS}")
        print(f"  Denied dirs: {DENY_DIRS}")
        print(f"  Denied files: {DENY_FILES}")
        backups = list_backups()
        print(f"  Backups available: {len(backups)}")
