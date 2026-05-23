"""
Workspace Cleanup Utility
Cleans up temp files, old logs, and bloat when workspace gets sloppy.
Run periodically: python tools/workspace_cleanup.py
"""

import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta

WORKSPACE_ROOT = Path(__file__).parent.parent
TEMP_DIR = WORKSPACE_ROOT / "temp"
LOGS_DIR = WORKSPACE_ROOT / "logs"
STABILITY_DIR = WORKSPACE_ROOT / "stability"

# Thresholds
TEMP_MAX_FILES = 20
TEMP_MAX_AGE_DAYS = 7
LOG_MAX_AGE_DAYS = 30
PROGRESS_MAX_SIZE_KB = 500  # Per file


def cleanup_temp():
    """Clean up temp directory."""
    if not TEMP_DIR.exists():
        return 0, 0

    files = list(TEMP_DIR.iterdir()) if TEMP_DIR.exists() else []
    now = datetime.now()
    removed = 0
    total_size = 0

    for f in files:
        if f.is_file():
            age_days = (now - datetime.fromtimestamp(f.stat().st_mtime)).days
            size_kb = f.stat().st_size / 1024
            total_size += size_kb

            if age_days > TEMP_MAX_AGE_DAYS:
                f.unlink()
                removed += 1

    return removed, total_size


def cleanup_logs():
    """Clean up old log files."""
    if not LOGS_DIR.exists():
        return 0

    now = datetime.now()
    removed = 0

    for f in LOGS_DIR.rglob("*.log"):
        if f.is_file():
            age_days = (now - datetime.fromtimestamp(f.stat().st_mtime)).days
            if age_days > LOG_MAX_AGE_DAYS:
                f.unlink()
                removed += 1

    return removed


def check_progress_bloat():
    """Check for oversized progress files."""
    progress_dir = WORKSPACE_ROOT / "progress"
    if not progress_dir.exists():
        return []

    bloated = []
    for f in progress_dir.iterdir():
        if f.is_file() and f.suffix in (".md", ".json", ".txt"):
            size_kb = f.stat().st_size / 1024
            if size_kb > PROGRESS_MAX_SIZE_KB:
                bloated.append((f.name, round(size_kb, 1)))

    return bloated


def check_stability_bloat():
    """Check stability directory for old/large files."""
    if not STABILITY_DIR.exists():
        return 0, 0

    total_size = 0
    file_count = 0
    for f in STABILITY_DIR.rglob("*"):
        if f.is_file():
            total_size += f.stat().st_size / 1024
            file_count += 1

    return file_count, total_size


def main():
    print("=" * 50)
    print("  WORKSPACE CLEANUP")
    print("=" * 50)
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Temp cleanup
    temp_removed, temp_size = cleanup_temp()
    print(f"  [TEMP] Removed {temp_removed} old files ({temp_size:.1f} KB)")

    # Log cleanup
    log_removed = cleanup_logs()
    print(f"  [LOGS] Removed {log_removed} old log files")

    # Progress bloat check
    bloated = check_progress_bloat()
    if bloated:
        print(f"  [BLOAT] Oversized progress files:")
        for name, size in bloated:
            print(f"    {name}: {size} KB (consider summarization)")
    else:
        print(f"  [PROGRESS] No bloat detected")

    # Stability check
    stab_files, stab_size = check_stability_bloat()
    print(f"  [STABILITY] {stab_files} files, {stab_size:.1f} KB total")

    print()
    print("  Cleanup complete.")


if __name__ == "__main__":
    main()
