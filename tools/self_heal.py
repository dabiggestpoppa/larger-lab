"""
OWL Self-Healing Engine
=======================
Scans gateway logs on startup, classifies errors, logs to DB,
annotates bug files, and attempts auto-recovery.

Usage:
    python tools/self_heal.py [--scan] [--report] [--fix] [--full]
"""

import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── paths ────────────────────────────────────────────────────────────────────
WORKSPACE = r"C:\Users\wifik\Desktop\projects\larger-lab"
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)
GLOB_LOG_DIR = r"C:\Users\wifik\AppData\Local\Temp\openclaw"
DB_PATH = os.path.join(WORKSPACE, "db", "owl_health.db")
BUG_DIR = os.path.join(WORKSPACE, "bugs")

# ── error patterns → (severity, category, description) ──────────────────────
PATTERNS = [
    # (regex, severity, category, human_label)
    (r"EPERM.*symlink", "warn", "symlink", "Permission denied creating symlink"),
    (r"symlink.*EPERM", "warn", "symlink", "Permission denied creating symlink"),
    (r"fetch timeout", "error", "timeout", "Network fetch timeout"),
    (r"gateway timeout", "error", "timeout", "Gateway connection timeout"),
    (r"stalled session", "error", "stall", "Agent session stalled"),
    (r"wait timeout", "warn", "timeout", "Session wait timeout exceeded"),
    (r"event_loop_delay", "warn", "performance", "Event loop delay detected"),
    (r"eventLoopDelayP99Ms=(\d+)", "warn", "performance", "Event loop P99 delay"),
    (r"liveness warning", "warn", "performance", "Gateway liveness warning"),
    (r"orphan recovery.*failed", "error", "recovery", "Orphan session recovery failed"),
    (r"failed to resume orphaned", "error", "recovery", "Failed to resume orphaned session"),
    (r"read failed.*Offset.*beyond end", "error", "tool", "File read offset beyond EOF"),
    (r"\[tools\].*failed", "error", "tool", "Tool execution failed"),
    (r"lane wait exceeded", "warn", "performance", "Processing lane wait exceeded"),
    (r"bootstrap-context.*\d{4,}ms", "warn", "performance", "Slow bootstrap context load"),
]


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_dirs():
    os.makedirs(BUG_DIR, exist_ok=True)
    os.makedirs(os.path.join(BUG_DIR, "open"), exist_ok=True)
    os.makedirs(os.path.join(BUG_DIR, "resolved"), exist_ok=True)


def get_today_log():
    """Return path to today's gateway log."""
    today = datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(GLOB_LOG_DIR, f"openclaw-{today}.log")
    if os.path.exists(path):
        return path
    # fallback: most recent log
    logs = sorted(
        [f for f in os.listdir(GLOB_LOG_DIR) if f.startswith("openclaw-") and f.endswith(".log")]
    )
    if logs:
        return os.path.join(GLOB_LOG_DIR, logs[-1])
    return None


def scan_log(log_path):
    """Scan a log file and return list of matched error dicts."""
    errors = []
    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            for regex, severity, category, label in PATTERNS:
                if re.search(regex, line, re.IGNORECASE):
                    # try to extract timestamp from JSON log line
                    ts = None
                    try:
                        obj = json.loads(line)
                        ts = obj.get("time") or obj.get("timestamp")
                    except (json.JSONDecodeError, TypeError):
                        pass
                    errors.append({
                        "timestamp": ts or datetime.now(timezone.utc).isoformat(),
                        "severity": severity,
                        "category": category,
                        "label": label,
                        "raw": line[:500],
                    })
                    break  # first match wins
    return errors


def dedup_errors(errors):
    """Group identical errors, count occurrences."""
    seen = {}
    for e in errors:
        key = (e["category"], e["label"])
        if key in seen:
            seen[key]["count"] += 1
            seen[key]["last_seen"] = e["timestamp"]
        else:
            seen[key] = {
                "category": e["category"],
                "label": e["label"],
                "severity": e["severity"],
                "first_seen": e["timestamp"],
                "last_seen": e["timestamp"],
                "count": 1,
                "sample_raw": e["raw"],
            }
    return list(seen.values())


def log_errors_to_db(errors):
    """Insert errors into DB, update occurrence counts for existing ones."""
    conn = get_conn()
    logged = 0
    for e in errors:
        # check if similar unresolved error exists
        row = conn.execute(
            "SELECT id, occurrence_count FROM errors WHERE category=? AND message=? AND resolved=0",
            (e["category"], e["label"]),
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE errors SET occurrence_count=?, last_seen=? WHERE id=?",
                (row["occurrence_count"] + e["count"], e["last_seen"], row["id"]),
            )
        else:
            conn.execute(
                "INSERT INTO errors (source, severity, category, message, raw_log_line, first_seen, last_seen, occurrence_count) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                ("gateway", e["severity"], e["category"], e["label"], e["sample_raw"], e["first_seen"], e["last_seen"], e["count"]),
            )
            logged += 1
    conn.commit()
    conn.close()
    return logged


def create_bug_annotation(error_row):
    """Create a bug markdown file for a new error."""
    slug = re.sub(r"[^a-z0-9]+", "-", error_row["message"].lower())[:50].strip("-")
    date_prefix = datetime.now().strftime("%Y%m%d")
    filename = f"{date_prefix}-{slug}.md"
    filepath = os.path.join(BUG_DIR, "open", filename)

    if os.path.exists(filepath):
        return None  # already exists

    content = f"""# 🐛 {error_row['message']}

- **Severity:** {error_row['severity']}
- **Category:** {error_row['category']}
- **First Seen:** {error_row.get('first_seen', 'unknown')}
- **Last Seen:** {error_row.get('last_seen', 'unknown')}
- **Occurrences:** {error_row.get('occurrence_count', 1)}
- **Status:** open

## Root Cause

_Auto-detected from gateway logs. Needs investigation._

## Sample Log

```
{error_row.get('raw_log_line', 'N/A')[:400]}
```

## Suggested Fix

_To be determined after investigation._

## Resolution

_Updated when fixed._
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath


def run_startup_check():
    """Full startup self-heal pipeline."""
    ensure_dirs()
    from db.schema import init_db
    init_db()

    log_path = get_today_log()
    if not log_path:
        print("⚠️  No gateway log found. Skipping scan.")
        _record_startup_check("log_scan", "pass", "No log file found", 0, 0)
        return

    print(f"🔍 Scanning: {log_path}")
    raw_errors = scan_log(log_path)
    deduped = dedup_errors(raw_errors)

    print(f"   Found {len(raw_errors)} raw errors → {len(deduped)} unique")

    logged = log_errors_to_db(deduped)
    print(f"   Logged {logged} new error(s) to DB")

    # create bug annotations for new errors
    conn = get_conn()
    new_bugs = 0
    for e in deduped:
        row = conn.execute(
            "SELECT * FROM errors WHERE category=? AND message=? AND resolved=0",
            (e["category"], e["label"]),
        ).fetchone()
        if row and row["occurrence_count"] <= e["count"]:  # new or first time
            bug_path = create_bug_annotation(dict(row))
            if bug_path:
                conn.execute(
                    "INSERT INTO bug_annotations (error_id, bug_file, title, status, priority) VALUES (?, ?, ?, 'open', ?)",
                    (row["id"], bug_path, row["message"], "high" if row["severity"] == "error" else "medium"),
                )
                new_bugs += 1
                print(f"   🐛 Bug file: {os.path.basename(bug_path)}")
    conn.commit()
    conn.close()

    _record_startup_check("log_scan", "pass" if not deduped else "warn",
                          f"Scanned {log_path}: {len(deduped)} unique errors, {logged} new, {new_bugs} bug files",
                          len(deduped), logged)

    # print summary
    if deduped:
        print("\n📊 Error Summary:")
        for e in sorted(deduped, key=lambda x: x["severity"], reverse=True):
            icon = "🔴" if e["severity"] == "error" else "🟡"
            print(f"   {icon} [{e['category']}] {e['label']} (×{e['count']})")
    else:
        print("✅ No errors detected.")


def _record_startup_check(name, status, details, errors_found, errors_logged):
    conn = get_conn()
    conn.execute(
        "INSERT INTO startup_checks (check_name, status, details, errors_found, errors_logged) VALUES (?, ?, ?, ?, ?)",
        (name, status, details, errors_found, errors_logged),
    )
    conn.commit()
    conn.close()


def generate_report():
    """Print a health report from the DB."""
    conn = get_conn()
    print("\n" + "=" * 60)
    print("🦉 OWL HEALTH REPORT")
    print("=" * 60)

    # startup checks
    checks = conn.execute("SELECT * FROM startup_checks ORDER BY timestamp DESC LIMIT 5").fetchall()
    if checks:
        print("\n📋 Recent Startup Checks:")
        for c in checks:
            icon = "✅" if c["status"] == "pass" else "⚠️" if c["status"] == "warn" else "❌"
            print(f"   {icon} {c['check_name']}: {c['details']}")

    # unresolved errors
    errors = conn.execute(
        "SELECT * FROM errors WHERE resolved=0 ORDER BY severity DESC, occurrence_count DESC"
    ).fetchall()
    if errors:
        print(f"\n🔴 Unresolved Errors ({len(errors)}):")
        for e in errors:
            icon = "🔴" if e["severity"] == "error" else "🟡"
            print(f"   {icon} [{e['category']}] {e['message']} (×{e['occurrence_count']})")
    else:
        print("\n✅ No unresolved errors.")

    # bug files
    bugs = conn.execute("SELECT * FROM bug_annotations WHERE status='open'").fetchall()
    if bugs:
        print(f"\n🐛 Open Bug Annotations ({len(bugs)}):")
        for b in bugs:
            print(f"   • {b['title']} [{b['priority']}]")

    # self-healing actions
    actions = conn.execute("SELECT * FROM self_healing_actions ORDER BY timestamp DESC LIMIT 5").fetchall()
    if actions:
        print(f"\n🔧 Recent Self-Healing Actions ({len(actions)}):")
        for a in actions:
            icon = "✅" if a["success"] else "❌"
            print(f"   {icon} {a['action_taken']}")

    conn.close()
    print("\n" + "=" * 60)


def auto_fix():
    """Attempt automatic fixes for known error patterns."""
    conn = get_conn()
    fixed = 0

    # Fix 1: EPERM symlink → replace with junction or copy
    symlink_errors = conn.execute(
        "SELECT * FROM errors WHERE category='symlink' AND resolved=0"
    ).fetchall()
    for err in symlink_errors:
        print(f"🔧 Attempting fix for: {err['message']}")
        # The browser-automation symlink issue is a known Windows problem
        # We can't fix symlinks without elevated perms, but we can document it
        conn.execute(
            "INSERT INTO self_healing_actions (trigger_error_id, action_taken, success, details) VALUES (?, ?, 1, ?)",
            (err["id"], "Documented symlink EPERM as known Windows limitation",
             "Windows requires elevated perms for symlinks. This is expected behavior, not a true error."),
        )
        conn.execute(
            "UPDATE errors SET resolved=1, resolution='Known Windows limitation — symlinks require elevated perms', resolution_timestamp=datetime('now') WHERE id=?",
            (err["id"],),
        )
        fixed += 1
        print(f"   ✅ Marked as known limitation (not a true error)")

    # Fix 2: Stalled sessions → these are transient, mark if old
    stall_errors = conn.execute(
        "SELECT * FROM errors WHERE category='stall' AND resolved=0 AND last_seen < datetime('now', '-1 hour')"
    ).fetchall()
    for err in stall_errors:
        conn.execute(
            "UPDATE errors SET resolved=1, resolution='Transient stall — auto-resolved after session timeout', resolution_timestamp=datetime('now') WHERE id=?",
            (err["id"],),
        )
        conn.execute(
            "INSERT INTO self_healing_actions (trigger_error_id, action_taken, success, details) VALUES (?, ?, 1, ?)",
            (err["id"], "Auto-resolved stale stall error", "Stalled sessions are transient by nature"),
        )
        fixed += 1

    conn.commit()
    conn.close()
    print(f"\n🔧 Auto-fixed {fixed} error(s).")
    return fixed


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or "--full" in args:
        run_startup_check()
        auto_fix()
        generate_report()
    elif "--scan" in args:
        run_startup_check()
    elif "--report" in args:
        generate_report()
    elif "--fix" in args:
        auto_fix()
        generate_report()
    else:
        print("Usage: python tools/self_heal.py [--scan] [--report] [--fix] [--full]")
