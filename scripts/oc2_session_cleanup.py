"""
OC2 Session Cleanup — Prevents session file bloat that causes OC2 to crash.
Run via: python scripts/oc2_session_cleanup.py
Schedule via: python scripts/oc2_session_cleanup.py --watch (runs every 5 min)
"""
import os, sys, time, glob, json
from pathlib import Path

SESSION_DIR = Path.home() / ".openclaw-2/.openclaw/agents/main/sessions"
MAX_SESSION_SIZE_KB = 200  # Max size for a single session file before cleanup
MAX_TRAJECTORY_SIZE_KB = 300
CLEANUP_INTERVAL_SEC = 300  # 5 minutes in watch mode

def get_size_kb(path):
    return path.stat().st_size / 1024 if path.exists() else 0

def cleanup(force=False):
    """Remove bloated session files. Returns list of cleaned files."""
    cleaned = []
    if not SESSION_DIR.exists():
        return cleaned

    for f in SESSION_DIR.iterdir():
        if not f.is_file():
            continue
        size_kb = get_size_kb(f)
        
        # Always clean backup files
        if ".bak-" in f.name and size_kb > 50:
            f.unlink()
            cleaned.append(f"{f.name} ({size_kb:.1f}KB)")
            continue
        
        # Clean trajectory files over limit
        if "trajectory.jsonl" in f.name and size_kb > MAX_TRAJECTORY_SIZE_KB:
            f.unlink()
            cleaned.append(f"{f.name} ({size_kb:.1f}KB)")
            continue
        
        # Clean main session files over limit
        if f.name.endswith(".jsonl") and not ".bak-" in f.name and size_kb > MAX_SESSION_SIZE_KB:
            f.unlink()
            cleaned.append(f"{f.name} ({size_kb:.1f}KB)")
            continue

    return cleaned

def watch_mode():
    """Run cleanup every CLEANUP_INTERVAL_SEC seconds."""
    print(f"[OC2 Cleanup] Watching {SESSION_DIR} every {CLEANUP_INTERVAL_SEC}s")
    print(f"[OC2 Cleanup] Thresholds: session={MAX_SESSION_SIZE_KB}KB, trajectory={MAX_TRAJECTORY_SIZE_KB}KB")
    while True:
        cleaned = cleanup()
        if cleaned:
            ts = time.strftime("%H:%M:%S")
            for c in cleaned:
                print(f"[{ts}] Cleaned: {c}")
        time.sleep(CLEANUP_INTERVAL_SEC)

if __name__ == "__main__":
    if "--watch" in sys.argv:
        watch_mode()
    else:
        cleaned = cleanup(force="--force" in sys.argv)
        if cleaned:
            print(f"Cleaned {len(cleaned)} files:")
            for c in cleaned:
                print(f"  - {c}")
        else:
            print("No files needed cleanup. Session dir is healthy.")
