#!/usr/bin/env python3
"""
OWL Self-Heal Diagnostic Tool
Scans files, memory, and patterns to diagnose drift, auto-work bugs, and persistent issues.

Usage: python tools/self_heal.py [--full] [--auto-work-only]
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Force UTF-8 on Windows
sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
MEMORY_BANK = WORKSPACE / "memory-bank"
REPORT_FILE = MEMORY_BANK / "self-heal-report.md"
STATE_FILE = MEMORY_BANK / "self_heal_state.json"
ERROR_DB = MEMORY_BANK / "error-db.json"
ERROR_LOG = MEMORY_BANK / "errors-and-solutions.md"
MEMORY_FILE = WORKSPACE / "MEMORY.md"
AGENTS_FILE = WORKSPACE / "AGENTS.md"
SOUL_FILE = WORKSPACE / "SOUL.md"
HEARTBEAT_FILE = WORKSPACE / "HEARTBEAT.md"

# Bootstrap file limits
LIMITS = {
    "AGENTS.md": 100,      # lines
    "MEMORY.md": 15000,    # chars
    "HEARTBEAT.md": 4000,  # chars
    "SOUL.md": 200,        # lines
}


def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def count_lines(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return len(f.readlines())
    except Exception:
        return -1


def count_chars(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return len(f.read())
    except Exception:
        return -1


def file_age_days(path):
    try:
        mtime = os.path.getmtime(path)
        return (time.time() - mtime) / 86400
    except Exception:
        return -1


def check_bootstrap_bloat():
    """Check if bootstrap files have grown too large."""
    results = []
    checks = {
        "AGENTS.md": (AGENTS_FILE, "lines", LIMITS["AGENTS.md"]),
        "MEMORY.md": (MEMORY_FILE, "chars", LIMITS["MEMORY.md"]),
        "HEARTBEAT.md": (HEARTBEAT_FILE, "chars", LIMITS["HEARTBEAT.md"]),
        "SOUL.md": (SOUL_FILE, "lines", LIMITS["SOUL.md"]),
    }

    for name, (path, mode, limit) in checks.items():
        if not path.exists():
            results.append((name, "MISSING", 0, limit))
            continue
        val = count_lines(path) if mode == "lines" else count_chars(path)
        status = "OK" if val <= limit else "BLOAT"
        results.append((name, status, val, limit))

    return results


def check_memory_drift():
    """Check if MEMORY.md has stale entries."""
    issues = []
    if not MEMORY_FILE.exists():
        issues.append("MEMORY.md not found")
        return issues

    content = MEMORY_FILE.read_text(encoding="utf-8")
    age = file_age_days(MEMORY_FILE)

    if age > 7:
        issues.append(f"MEMORY.md last updated {age:.0f} days ago — may be stale")

    # Check for old date entries that reference "active" or "running"
    lines = content.split("\n")
    for i, line in enumerate(lines):
        # Look for date headers older than 14 days with active status
        if line.startswith("## ") and ("2026-05" in line or "2026-04" in line):
            # Check surrounding context for stale active markers
            context = "\n".join(lines[max(0, i):min(len(lines), i + 20)])
            if "Active" in context or "Running" in context or "PAUSED" in context:
                age_hint = line.strip()
                if age_hint not in [i[:20] for i in issues]:
                    issues.append(f"Potentially stale section: {age_hint}")

    return issues


def check_error_patterns():
    """Check for recurring error patterns."""
    findings = []

    error_db = load_json(ERROR_DB)
    if error_db and "entries" in error_db:
        pattern_counts = {}
        for entry in error_db["entries"]:
            pid = entry.get("pattern_id", "UNKNOWN")
            pattern_counts[pid] = pattern_counts.get(pid, 0) + 1

        for pid, count in pattern_counts.items():
            if count > 2:
                findings.append(f"Pattern {pid} appears {count} times")

    if not findings:
        findings.append("No recurring patterns detected")

    return findings


def check_stale_state():
    """Check for stale processes, temp files, etc."""
    issues = []

    # Check for __pycache__ directories
    pycache_count = sum(1 for _ in WORKSPACE.rglob("__pycache__") if _.is_dir())
    if pycache_count > 0:
        issues.append(f"{pycache_count} __pycache__ directories found")

    # Check for .bak/.tmp files
    bak_files = list(WORKSPACE.rglob("*.bak")) + list(WORKSPACE.rglob("*.tmp"))
    if bak_files:
        issues.append(f"{len(bak_files)} .bak/.tmp files found")

    # Check memory-bank for old session files
    if MEMORY_BANK.exists():
        session_files = list(MEMORY_BANK.glob("session-*.md"))
        old_sessions = [f for f in session_files if file_age_days(f) > 14]
        if old_sessions:
            issues.append(f"{len(old_sessions)} session logs older than 14 days")

    if not issues:
        issues.append("No stale state detected")

    return issues


def load_state():
    data = load_json(STATE_FILE)
    if not data:
        return {"version": 1, "runs": 0, "last_run": None, "auto_work_bug_count": 0, "findings": []}
    return data


def save_state(state):
    state["runs"] += 1
    state["last_run"] = datetime.now().isoformat()
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def generate_report(bootstrap, drift, errors, stale, auto_work_detected=False, auto_work_detail=""):
    """Generate the self-heal report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M EDT")

    # Bootstrap bloat table
    bootstrap_rows = []
    for name, status, val, limit in bootstrap:
        icon = "OK" if status == "OK" else ("BLOAT" if status == "BLOAT" else "MISSING")
        bootstrap_rows.append(f"| {name} | {icon} | {val}/{limit} |")

    # Determine overall status
    has_issues = any(s == "BLOAT" or s == "MISSING" for _, s, _, _ in bootstrap) or len(drift) > 0
    overall = "NEEDS ATTENTION" if has_issues else "HEALTHY"

    report = f"""# SELF-HEAL REPORT
**Date:** {now}
**Trigger:** {'MAD directive' if not auto_work_detected else 'Auto-work bug detected + MAD directive'}
**Overall:** {overall}

## DIAGNOSIS

### Bootstrap Bloat
| File | Status | Size |
|------|--------|------|
{chr(10).join(bootstrap_rows)}

### Memory Drift
"""
    for d in drift:
        report += f"- {d}\n"

    report += "\n### Error Patterns\n"
    for e in errors:
        report += f"- {e}\n"

    report += "\n### Stale State\n"
    for s in stale:
        report += f"- {s}\n"

    if auto_work_detected:
        report += f"""
### AUTO-WORK BUG DETECTED
- **Detail:** {auto_work_detail}
- **Prescription:** Before executing ANY tools, read the user's message and ask: "Did they ask me to do something, or are they talking to me?" If talking, respond conversationally. If doing, confirm scope before spawning agents.

"""

    report += "\n## PRESCRIPTIONS\n"
    prescriptions = []

    for name, status, val, limit in bootstrap:
        if status == "BLOAT":
            prescriptions.append(f"Compress {name} ({val} → target {limit})")
        elif status == "MISSING":
            prescriptions.append(f"Restore {name} — file is missing!")

    if drift:
        prescriptions.append("Review and update MEMORY.md — stale entries detected")

    if auto_work_detected:
        prescriptions.append("AUTO-WORK BUG: Add a hard pause before tool execution. Read → Understand → THEN act.")

    if not prescriptions:
        prescriptions.append("No action needed — system is healthy")

    for i, p in enumerate(prescriptions, 1):
        report += f"{i}. {p}\n"

    report += f"\n---\n_Generated by self_heal.py v1.0 | Run #{load_state()['runs'] + 1}_\n"

    return report


def main():
    args = sys.argv[1:]
    full_mode = "--full" in args
    auto_work_only = "--auto-work-only" in args

    print("=== OWL SELF-HEAL DIAGNOSTIC ===\n")

    # Run checks
    print("[1/4] Checking bootstrap bloat...")
    bootstrap = check_bootstrap_bloat()
    for name, status, val, limit in bootstrap:
        print(f"  {name}: {status} ({val}/{limit})")

    print("\n[2/4] Checking memory drift...")
    drift = check_memory_drift()
    for d in drift:
        print(f"  {d}")

    print("\n[3/4] Checking error patterns...")
    errors = check_error_patterns()
    for e in errors:
        print(f"  {e}")

    print("\n[4/4] Checking stale state...")
    stale = check_stale_state()
    for s in stale:
        print(f"  {s}")

    # Generate report
    report = generate_report(bootstrap, drift, errors, stale)

    # Save report
    MEMORY_BANK.mkdir(exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)

    # Update state
    state = load_state()
    save_state(state)

    print(f"\n=== REPORT SAVED TO {REPORT_FILE} ===\n")
    print(report)


if __name__ == "__main__":
    main()
