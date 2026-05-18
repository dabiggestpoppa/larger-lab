#!/usr/bin/env python3
"""
Validation Gate Script
Checks each system (Quant Lab, Content Farm, Agent Environment) for basic readiness.
Outputs PASS/FAIL per system. Use as a gate before any expansion.

Usage:
  python tools/validation-gate.py [--verbose]
"""

import os
import sys
import json
import argparse
import io
from datetime import datetime, timezone
from pathlib import Path

# Fix Windows console encoding for emoji output
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

WORKSPACE = Path(__file__).resolve().parent.parent

# ─── Checks ───────────────────────────────────────────────────────────────────

def check_quant_lab(verbose: bool) -> dict:
    """Quant Lab: Does the strategy have cost-validated results?"""
    results_dir = WORKSPACE / "quant-lab" / "results"
    cost_files = list(results_dir.glob("cost-validation-*.md")) if results_dir.exists() else []

    # Also check for any backtest results
    backtest_dir = WORKSPACE / "quant-lab" / "backtests"
    has_backtests = backtest_dir.exists() and any(backtest_dir.iterdir())

    passed = len(cost_files) > 0
    details = []
    details.append(f"  Cost validation files: {len(cost_files)}")
    for f in cost_files:
        details.append(f"    - {f.name}")
    details.append(f"  Has backtest data: {has_backtests}")

    if not passed:
        details.append("  ❌ FAIL: No cost-validation-*.md found in quant-lab/results/")
        details.append("     → Run cost validation before expanding strategies")
    else:
        details.append("  ✅ PASS: Cost validation results found")

    return {"system": "Quant Lab", "passed": passed, "details": details}


def check_content_farm(verbose: bool) -> dict:
    """Content Farm: Does content exist locally in day* directories?"""
    farm_dir = WORKSPACE / "content-farm"
    if not farm_dir.exists():
        return {"system": "Content Farm", "passed": False,
                "details": ["  ❌ FAIL: content-farm/ directory does not exist"]}

    day_dirs = sorted([d for d in farm_dir.iterdir() if d.is_dir() and d.name.startswith("day")])

    # Count content files (non-directory files in day* subdirs)
    content_files = []
    for day_dir in day_dirs:
        for subdir in day_dir.iterdir():
            if subdir.is_dir():
                content_files.extend([f for f in subdir.iterdir() if f.is_file()])

    # Also check output/ for generated content
    output_dir = farm_dir / "output"
    output_files = []
    if output_dir.exists():
        for platform_dir in output_dir.iterdir():
            if platform_dir.is_dir():
                output_files.extend([f for f in platform_dir.rglob("*") if f.is_file()])

    has_local_content = len(content_files) > 0
    has_output = len(output_files) > 0
    passed = has_local_content or has_output

    details = []
    details.append(f"  Day directories: {len(day_dirs)} ({', '.join(d.name for d in day_dirs)})")
    details.append(f"  Content files in day*/: {len(content_files)}")
    details.append(f"  Output files in output/: {len(output_files)}")

    if not passed:
        details.append("  ❌ FAIL: No content found in day*/ or output/ directories")
        details.append("     → Produce local content before expanding to platforms")
    else:
        details.append("  ✅ PASS: Local content exists")

    return {"system": "Content Farm", "passed": passed, "details": details}


def check_agent_environment(verbose: bool) -> dict:
    """Agent Environment: Are any agents registered?"""
    rooms_file = WORKSPACE / "agent-environment" / "data" / "rooms.json"
    agents_file = WORKSPACE / "agent-environment" / "data" / "agents.json"

    details = []
    agent_count = 0
    room_count = 0

    if rooms_file.exists():
        try:
            with open(rooms_file) as f:
                rooms = json.load(f)
            room_count = len(rooms) if isinstance(rooms, (list, dict)) else 0
            details.append(f"  Rooms registered: {room_count}")
        except (json.JSONDecodeError, IOError) as e:
            details.append(f"  Rooms file error: {e}")
    else:
        details.append("  rooms.json not found")

    if agents_file.exists():
        try:
            with open(agents_file) as f:
                agents = json.load(f)
            agent_count = len(agents) if isinstance(agents, (list, dict)) else 0
            details.append(f"  Agents registered: {agent_count}")
        except (json.JSONDecodeError, IOError) as e:
            details.append(f"  Agents file error: {e}")
    else:
        details.append("  agents.json not found")

    passed = agent_count > 0 or room_count > 0

    if not passed:
        details.append("  ❌ FAIL: No agents or rooms registered in agent-environment")
        details.append("     → Register at least one agent before expanding the environment")
    else:
        details.append("  ✅ PASS: Agents/rooms are registered")

    return {"system": "Agent Environment", "passed": passed, "details": details}


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Validation Gate — System Readiness Check")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    checks = [
        check_quant_lab(args.verbose),
        check_content_farm(args.verbose),
        check_agent_environment(args.verbose),
    ]

    all_passed = all(c["passed"] for c in checks)

    if args.json:
        output = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall": "PASS" if all_passed else "FAIL",
            "checks": [
                {"system": c["system"], "passed": c["passed"]}
                for c in checks
            ],
        }
        print(json.dumps(output, indent=2))
    else:
        print("=" * 60)
        print("🔒 VALIDATION GATE — System Readiness Check")
        print(f"   {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("=" * 60)

        for check in checks:
            status = "✅ PASS" if check["passed"] else "❌ FAIL"
            print(f"\n{status} — {check['system']}")
            if args.verbose:
                for detail in check["details"]:
                    print(detail)

        print("\n" + "=" * 60)
        if all_passed:
            print("🟢 OVERALL: PASS — All systems validated. Expansion permitted.")
        else:
            failed = [c["system"] for c in checks if not c["passed"]]
            print(f"🔴 OVERALL: FAIL — {len(failed)} system(s) not ready: {', '.join(failed)}")
            print("   → Fix failures before expanding any system.")
        print("=" * 60)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
