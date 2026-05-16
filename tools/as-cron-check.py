#!/usr/bin/env python3
"""
AS Cron Check — Assistant Manager Team Monitor
===============================================
Run periodically to check team progress, run tests, and flag blockers.
"""

import json
import os
import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parent.parent
PROGRESS_DIR = LAB_ROOT / "progress"
TEAM_CHAT = LAB_ROOT / "shared-conversations" / "team-chat.md"
REPORTS_DIR = LAB_ROOT / "srrs_opc" / "reports"

def run_tests():
    """Run all SRRA-OPH tests and return results."""
    results = {}
    test_modules = [
        "srrs_opc.tests.test_phase2_e2e",
        "srrs_opc.tests.test_phase3_e2e",
        "srrs_opc.tests.test_phase3_book2",
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(LAB_ROOT)
    for mod in test_modules:
        try:
            r = subprocess.run(
                [sys.executable, "-m", mod],
                capture_output=True, text=True, timeout=60,
                cwd=str(LAB_ROOT), env=env
            )
            passed = r.returncode == 0
            results[mod] = {"passed": passed, "output": r.stdout[-200:] if passed else r.stderr[-200:]}
        except subprocess.TimeoutExpired:
            results[mod] = {"passed": False, "output": "TIMEOUT"}
        except Exception as e:
            results[mod] = {"passed": False, "output": str(e)}
    return results

def check_progress_files():
    """Check for recent updates in team progress files."""
    files = {
        "CC": PROGRESS_DIR / "claude-code-progress.md",
        "OC": PROGRESS_DIR / "openclaw-progress.md",
        "HR": PROGRESS_DIR / "hermes-progress.md",
        "AS": PROGRESS_DIR / "assistant-progress.md",
    }
    status = {}
    for agent, path in files.items():
        if path.exists():
            mtime = path.stat().st_mtime
            age_min = (datetime.now().timestamp() - mtime) / 60
            status[agent] = {"exists": True, "age_min": round(age_min, 1)}
        else:
            status[agent] = {"exists": False}
    return status

def check_team_chat():
    """Check for open items in team chat."""
    if not TEAM_CHAT.exists():
        return "Team chat not found"
    content = TEAM_CHAT.read_text(encoding="utf-8")
    # Count open items
    open_count = content.count("🔴 Open Items")
    return {"open_items": open_count, "last_lines": content[-500:]}

def main():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"\n{'='*60}")
    print(f"AS Cron Check — {now}")
    print(f"{'='*60}")

    # 1. Run tests
    print("\n📊 Running tests...")
    test_results = run_tests()
    all_pass = all(r["passed"] for r in test_results.values())
    for mod, r in test_results.items():
        status = "✅ PASS" if r["passed"] else "❌ FAIL"
        print(f"  {status} {mod}")
    print(f"\n  Overall: {'✅ ALL PASS' if all_pass else '❌ SOME FAILURES'}")

    # 2. Check progress files
    print("\n📁 Progress files:")
    progress = check_progress_files()
    for agent, info in progress.items():
        if info["exists"]:
            print(f"  {agent}: updated {info['age_min']}min ago")
        else:
            print(f"  {agent}: NOT FOUND")

    # 3. Check team chat
    print("\n💬 Team chat:")
    chat = check_team_chat()
    if isinstance(chat, dict):
        print(f"  Open items: {chat['open_items']}")
    else:
        print(f"  {chat}")

    # 4. Summary
    print(f"\n{'='*60}")
    if all_pass:
        print("✅ System healthy — all tests passing")
    else:
        print("❌ ATTENTION NEEDED — test failures detected")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
