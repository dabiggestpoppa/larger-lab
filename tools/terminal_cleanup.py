#!/usr/bin/env python3
"""
Terminal Cleanup Utility
========================
Kills stale terminal processes that are no longer needed.
Run this at the start of each agent session to free resources.

Usage:
  python tools/terminal_cleanup.py           # Show what would be killed
  python tools/terminal_cleanup.py --force   # Kill stale processes
  python tools/terminal_cleanup.py --all     # Kill ALL python/node processes (careful)
"""

import subprocess
import sys
import os
from datetime import datetime, timedelta

def get_stale_processes(max_age_minutes=60):
    """Find python/node processes older than max_age_minutes that are not actively serving."""
    stale = []
    try:
        # Get all python and node processes
        result = subprocess.run(
            ['wmic', 'process', 'where', 'name="python.exe" or name="node.exe"',
             'get', 'ProcessId,CommandLine,CreationDate', '/format:csv'],
            capture_output=True, text=True, timeout=10
        )
        lines = result.stdout.strip().split('\n')
        for line in lines[2:]:  # Skip header lines
            if not line.strip():
                continue
            parts = line.split(',')
            if len(parts) >= 4:
                pid = parts[1].strip()
                cmdline = parts[2].strip() if len(parts) > 2 else ''
                creation = parts[3].strip() if len(parts) > 3 else ''
                
                # Skip current process
                if pid == str(os.getpid()):
                    continue
                    
                # Parse creation time
                try:
                    if creation:
                        # WMIC format: 20260516154434.000000+000
                        dt = datetime.strptime(creation[:14], '%Y%m%d%H%M%S')
                        age = datetime.now() - dt
                        if age > timedelta(minutes=max_age_minutes):
                            stale.append({
                                'pid': pid,
                                'cmdline': cmdline[:80],
                                'age_min': int(age.total_seconds() / 60)
                            })
                except ValueError:
                    pass
    except Exception as e:
        print(f"  ⚠ Error scanning: {e}")
    return stale

def kill_process(pid):
    """Kill a process by PID."""
    try:
        subprocess.run(['taskkill', '/PID', pid, '/F'], 
                      capture_output=True, timeout=5)
        return True
    except Exception:
        return False

def main():
    force = '--force' in sys.argv
    kill_all = '--all' in sys.argv
    
    print("🧹 Terminal Cleanup Utility")
    print(f"   Mode: {'FORCE KILL' if force else 'DRY RUN'}")
    print()
    
    if kill_all:
        # Kill all python/node except current
        print("  ⚠ Killing ALL python/node processes...")
        for name in ['python.exe', 'node.exe']:
            subprocess.run(['taskkill', '/IM', name, '/F'], 
                          capture_output=True, timeout=5)
        print("  ✅ Done.")
        return
    
    stale = get_stale_processes(max_age_minutes=30 if not force else 0)
    
    if not stale:
        print("  ✅ No stale processes found.")
        return
    
    print(f"  Found {len(stale)} stale process(es):")
    for p in stale:
        print(f"    PID {p['pid']:>6} | {p['age_min']:>3}m old | {p['cmdline']}")
    
    if force:
        killed = 0
        for p in stale:
            if kill_process(p['pid']):
                killed += 1
        print(f"\n  ✅ Killed {killed}/{len(stale)} processes.")
    else:
        print(f"\n  Run with --force to kill these processes.")

if __name__ == "__main__":
    main()
