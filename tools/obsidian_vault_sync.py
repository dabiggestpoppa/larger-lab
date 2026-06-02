"""Obsidian Vault Sync — Auto-syncs workspace vault to real Obsidian vault.

Rules:
- Every 5 file changes (create/edit/delete) -> sync to real vault
- Bidirectional: workspace -> real AND real -> workspace
- Runs as a daemon with configurable interval
- Tracks file hashes to detect changes efficiently

Usage:
    python tools/obsidian_vault_sync.py          # Run daemon
    python tools/obsidian_vault_sync.py --once   # Single sync
    python tools/obsidian_vault_sync.py --status # Show sync status
"""
import os
import sys
import time
import json
import hashlib
import shutil
from pathlib import Path
from datetime import datetime

# Configuration
WORKSPACE_ROOT = Path(__file__).parent.parent
WS_VAULT = WORKSPACE_ROOT / "memory" / "obsidian-vault"
REAL_VAULT = Path(r"C:\Users\wifik\Downloads\o2c")
STATE_FILE = WORKSPACE_ROOT / "tools" / ".obsidian-sync-state.json"

SYNC_INTERVAL = 60  # seconds between checks
CHANGE_THRESHOLD = 5  # files changed before sync triggers


def file_hash(filepath):
    """Get MD5 hash of a file."""
    try:
        with open(filepath, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return ""


def scan_vault(vault_path):
    """Scan vault and return dict of relative_path -> hash."""
    files = {}
    if not vault_path.exists():
        return files
    for f in vault_path.rglob("*.md"):
        rel = f.relative_to(vault_path)
        files[str(rel)] = file_hash(f)
    return files


def load_state():
    """Load sync state from disk."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"ws_hashes": {}, "real_hashes": {}, "last_sync": None, "changes_since_sync": 0}


def save_state(state):
    """Save sync state to disk."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def sync_vault(ws_files, real_files, ws_path, real_path):
    """Bidirectional sync. Returns (synced_count, details)."""
    synced = 0
    details = []

    # Workspace -> Real (new or changed)
    for rel, ws_hash in ws_files.items():
        real_file = real_path / rel
        real_hash = real_files.get(rel, "")
        if ws_hash != real_hash:
            real_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ws_path / rel, real_file)
            synced += 1
            details.append(f"WS->REAL: {rel}")

    # Real -> Workspace (new or changed)
    for rel, real_hash in real_files.items():
        ws_file = ws_path / rel
        ws_hash = ws_files.get(rel, "")
        if real_hash != ws_hash:
            ws_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(real_path / rel, ws_file)
            synced += 1
            details.append(f"REAL->WS: {rel}")

    return synced, details


def count_changes(old_hashes, new_hashes):
    """Count how many files changed between two hash dicts."""
    changes = 0
    all_keys = set(old_hashes.keys()) | set(new_hashes.keys())
    for key in all_keys:
        if old_hashes.get(key) != new_hashes.get(key):
            changes += 1
    return changes


def run_sync(force=False):
    """Run a single sync cycle. Returns sync result."""
    state = load_state()

    # Scan both vaults
    ws_files = scan_vault(WS_VAULT)
    real_files = scan_vault(REAL_VAULT)

    # Count changes since last sync
    ws_changes = count_changes(state.get("ws_hashes", {}), ws_files)
    real_changes = count_changes(state.get("real_hashes", {}), real_files)
    total_changes = ws_changes + real_changes

    # Update change counter
    state["changes_since_sync"] = state.get("changes_since_sync", 0) + total_changes

    result = {
        "timestamp": datetime.now().isoformat(),
        "ws_files": len(ws_files),
        "real_files": len(real_files),
        "changes_detected": total_changes,
        "changes_since_sync": state["changes_since_sync"],
        "synced": 0,
        "details": [],
    }

    # Sync if threshold reached or forced
    if force or state["changes_since_sync"] >= CHANGE_THRESHOLD:
        synced, details = sync_vault(ws_files, real_files, WS_VAULT, REAL_VAULT)
        result["synced"] = synced
        result["details"] = details
        result["changes_since_sync"] = 0

        # Update state
        state["ws_hashes"] = ws_files
        state["real_hashes"] = real_files
        state["last_sync"] = datetime.now().isoformat()
        state["changes_since_sync"] = 0
        save_state(state)
    else:
        save_state(state)

    return result


def run_daemon():
    """Run continuous sync daemon."""
    print(f"[Obsidian Sync] Daemon started")
    print(f"[Obsidian Sync] Workspace: {WS_VAULT}")
    print(f"[Obsidian Sync] Real vault: {REAL_VAULT}")
    print(f"[Obsidian Sync] Threshold: {CHANGE_THRESHOLD} changes")
    print(f"[Obsidian Sync] Interval: {SYNC_INTERVAL}s")
    print(f"[Obsidian Sync] Press Ctrl-C to stop")
    print()

    while True:
        try:
            result = run_sync()
            ts = datetime.now().strftime("%H:%M:%S")

            if result["synced"] > 0:
                print(f"[{ts}] SYNCED {result['synced']} files (WS:{result['ws_files']} REAL:{result['real_files']})")
                for d in result["details"][:10]:
                    print(f"  {d}")
                if len(result["details"]) > 10:
                    print(f"  ... and {len(result['details']) - 10} more")
            else:
                pending = result["changes_since_sync"]
                print(f"[{ts}] Watching... {pending}/{CHANGE_THRESHOLD} changes pending")

        except Exception as e:
            print(f"[ERROR] {e}")

        time.sleep(SYNC_INTERVAL)


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--status" in args:
        state = load_state()
        ws_files = scan_vault(WS_VAULT)
        real_files = scan_vault(REAL_VAULT)
        print(f"Workspace vault: {len(ws_files)} files")
        print(f"Real vault: {len(real_files)} files")
        print(f"Changes since sync: {state.get('changes_since_sync', 0)}/{CHANGE_THRESHOLD}")
        print(f"Last sync: {state.get('last_sync', 'never')}")

    elif "--once" in args:
        result = run_sync(force=True)
        print(f"Synced {result['synced']} files")
        for d in result["details"][:20]:
            print(f"  {d}")

    else:
        run_daemon()
