#!/usr/bin/env python3
"""
Progress Update Hook
====================
Call this script after editing any progress file to increment the update counter
and trigger memory sync if the threshold (7) is reached.

Usage:
  python tools/progress-update-hook.py <filename1> [filename2 ...]

Examples:
  python tools/progress-update-hook.py PROJECT_PROGRESS.md
  python tools/progress-update-hook.py research-agents-progress.md p90-conversion-progress.md

This is designed to be called:
  1. Manually after editing progress files
  2. Via a git post-commit hook
  3. Via a VS Code task on save
  4. By agents after updating progress
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parent.parent
COUNTER_FILE = LAB_ROOT / ".progress-sync-counters.json"
SYNC_THRESHOLD = 7

VALID_FILES = {
    "PROJECT_PROGRESS.md",
    "PROJECT_PROGRESS_CLEAN.md",
    "research-agents-progress.md",
    "p90-conversion-progress.md",
    "xhaak-kulu-bridge-progress.md",
}


def load_counters() -> dict:
    if COUNTER_FILE.exists():
        try:
            with open(COUNTER_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"files": {}, "total_updates": 0, "last_sync_count": 0, "last_sync_time": None}


def save_counters(counters: dict):
    with open(COUNTER_FILE, "w") as f:
        json.dump(counters, f, indent=2)


def get_file_fingerprint(filepath: Path) -> str:
    if not filepath.exists():
        return ""
    stat = filepath.stat()
    return f"{stat.st_mtime}:{stat.st_size}"


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/progress-update-hook.py <filename1> [filename2 ...]")
        print(f"Valid files: {', '.join(sorted(VALID_FILES))}")
        sys.exit(1)

    filenames = sys.argv[1:]
    counters = load_counters()
    files_state = counters.get("files", {})

    total_before = sum(f.get("update_count", 0) for f in files_state.values())
    last_sync = counters.get("last_sync_count", 0)

    for fname in filenames:
        if fname not in VALID_FILES:
            print(f"⚠️  Skipping unknown file: {fname}")
            continue

        fpath = LAB_ROOT / fname
        current_fp = get_file_fingerprint(fpath)

        files_state[fname] = {
            "fingerprint": current_fp,
            "last_changed": datetime.now(timezone.utc).isoformat(),
            "update_count": files_state.get(fname, {}).get("update_count", 0) + 1,
        }
        print(f"  ✓ {fname} → update #{files_state[fname]['update_count']}")

    counters["files"] = files_state
    total_after = sum(f.get("update_count", 0) for f in files_state.values())
    counters["total_updates"] = total_after

    updates_since_sync = total_after - last_sync
    sync_triggered = updates_since_sync >= SYNC_THRESHOLD

    save_counters(counters)

    print(f"\n📊 Total updates: {total_after} | Since last sync: {updates_since_sync}/{SYNC_THRESHOLD}")

    if sync_triggered:
        print(f"🔄 Threshold reached! Running memory sync...")
        # Import and run the sync
        import importlib.util
        spec = importlib.util.spec_from_file_location("progress_sync", Path(__file__).parent / "progress-sync.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.sync_memory(counters)
    else:
        remaining = SYNC_THRESHOLD - updates_since_sync
        print(f"   {remaining} more update(s) needed before next sync.")


if __name__ == "__main__":
    main()
