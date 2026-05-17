"""
OWL Doctor Tool — Log Analysis + OpenClaw Docs Cross-Reference
==============================================================
Scans gateway logs, classifies errors, pulls official OpenClaw docs for
best-practice remedies, and outputs a structured PRESCRIPTION for MAD to review.

Usage:
    python tools/doctor.py [--scan] [--prescribe] [--full] [--report]

Flow:
    1. Doctor scans logs → finds errors
    2. Doctor cross-references with OpenClaw docs → builds prescription
    3. MAD reviews prescription → approves
    4. Self-heal executes approved fixes (with safety cron active)
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
PRESCRIPTION_PATH = os.path.join(WORKSPACE, "memory-bank", "doctor-prescription.md")
OPENCLAW_DOCS = r"C:\Users\wifik\AppData\Roaming\npm\node_modules\openclaw\docs"

# ── error patterns → (severity, category, description) ──────────────────────
PATTERNS = [
    # Gateway-level
    (r"EPERM.*symlink", "warn", "symlink", "Permission denied creating symlink"),
    (r"symlink.*EPERM", "warn", "symlink", "Permission denied creating symlink"),
    (r"drain timeout reached", "error", "gateway", "Gateway drain timeout (restart loop)"),
    (r"failed to reacquire gateway lock", "error", "gateway", "Gateway lock conflict (duplicate restart)"),
    (r"gateway timeout", "error", "timeout", "Gateway connection timeout"),
    (r"startup model warmup timed out", "warn", "gateway", "Model warmup timeout on startup"),
    (r"refusing to bind gateway.*without auth", "error", "gateway", "Gateway bind without auth config"),
    (r"another gateway instance is already listening", "error", "gateway", "Port conflict — duplicate gateway"),
    (r"EADDRINUSE", "error", "gateway", "Port already in use"),
    # Session / agent
    (r"stalled session", "error", "stall", "Agent session stalled"),
    (r"active_work_without_progress", "error", "stall", "Agent session stalled (no progress)"),
    (r"agent cleanup timed out", "error", "stall", "Agent cleanup timed out"),
    (r"marked \d+ interrupted main session", "warn", "recovery", "Interrupted sessions from stale locks"),
    (r"removed stale session lock", "warn", "recovery", "Stale session lock cleaned up"),
    # Performance
    (r"event_loop_delay", "warn", "performance", "Event loop delay detected"),
    (r"eventLoopDelayP99Ms=(\d+)", "warn", "performance", "Event loop P99 delay"),
    (r"liveness warning", "warn", "performance", "Gateway liveness warning"),
    (r"lane wait exceeded", "warn", "performance", "Processing lane wait exceeded"),
    (r"bootstrap-context.*\d{4,}ms", "warn", "performance", "Slow bootstrap context load"),
    # Network / Telegram
    (r"fetch timeout", "error", "timeout", "Network fetch timeout"),
    (r"fetch timeout reached", "error", "timeout", "Network fetch timeout"),
    (r"wait timeout", "warn", "timeout", "Session wait timeout exceeded"),
    (r"sendChatAction failed", "warn", "telegram", "Telegram sendChatAction failed"),
    (r"DNS-resolved IP unreachable", "warn", "telegram", "Telegram API IP unreachable (DNS fallback)"),
    (r"telegram deleteWebhook failed", "error", "telegram", "Telegram webhook deletion failed"),
    (r"Telegram limits bots to 100 commands", "warn", "telegram", "Telegram bot command limit exceeded"),
    # Tools
    (r"read failed.*ENOENT", "error", "tool", "File read failed — file not found"),
    (r"\[tools\].*failed", "error", "tool", "Tool execution failed"),
    (r"embedded_run_failover_decision.*aborted.*true", "error", "failover", "Embedded run aborted (surface error)"),
    # Config
    (r"Invalid config", "error", "config", "Invalid gateway config"),
    (r"config reload skipped", "warn", "config", "Config reload skipped (invalid)"),
    (r"protocol mismatch", "warn", "config", "WebSocket protocol mismatch (UI/gateway version skew)"),
    # Bootstrap / workspace
    (r"bootstrap file.*chars.*limit", "warn", "workspace", "Bootstrap file exceeds size limit"),
    (r"workspace bootstrap file.*truncating", "warn", "workspace", "Bootstrap file truncated"),
]


# ── OpenClaw Docs Best Practices Lookup ─────────────────────────────────────
# Maps (category, symptom_key) → doc reference + recommended action
DOCS_REFERENCE = {
    "gateway": {
        "drain_timeout": {
            "doc": "gateway/troubleshooting.md → Gateway service not running",
            "fix": "Run: openclaw gateway restart (or openclaw gateway install --force if service metadata is stale)",
            "severity": "high"
        },
        "lock_conflict": {
            "doc": "gateway/gateway-lock.md",
            "fix": "Wait 30s for lock to release. If persistent: openclaw gateway restart",
            "severity": "medium"
        },
        "port_conflict": {
            "doc": "gateway/troubleshooting.md → Gateway service not running",
            "fix": "Kill stale process on port 18790, then: openclaw gateway restart",
            "severity": "high"
        },
        "bind_no_auth": {
            "doc": "gateway/authentication.md",
            "fix": "Set gateway.auth.token or gateway.auth.password in openclaw.json",
            "severity": "critical"
        },
        "model_warmup_timeout": {
            "doc": "gateway/configuration.md → agents.defaults.models",
            "fix": "Normal on slow connections. If persistent, reduce model complexity or increase timeout",
            "severity": "low"
        },
    },
    "telegram": {
        "network_error": {
            "doc": "channels/telegram.md → Troubleshooting",
            "fix": "Check internet connectivity. Telegram API may be blocked. Consider using a proxy.",
            "severity": "high"
        },
        "webhook_failed": {
            "doc": "channels/telegram.md → Webhook setup",
            "fix": "Gateway auto-falls back to polling. If persistent: check bot token, run openclaw channels login --channel telegram",
            "severity": "medium"
        },
        "command_limit": {
            "doc": "channels/telegram.md → Bot commands",
            "fix": "Set channels.telegram.commands.native=false to stay under 100 command limit",
            "severity": "low"
        },
        "dns_unreachable": {
            "doc": "channels/telegram.md → Network issues",
            "fix": "DNS resolution failing for Telegram API. Check DNS settings, consider DoH or VPN",
            "severity": "high"
        },
    },
    "performance": {
        "event_loop_delay": {
            "doc": "gateway/health.md → Deep diagnostics",
            "fix": "Reduce concurrent sessions, check CPU load, consider scaling. Persistent delay >5s needs investigation.",
            "severity": "medium"
        },
        "liveness_warning": {
            "doc": "gateway/health.md → Health monitor config",
            "fix": "Check gateway.channelHealthCheckMinutes config. Reduce if too aggressive.",
            "severity": "medium"
        },
        "slow_bootstrap": {
            "doc": "gateway/doctor.md → Bootstrap file size",
            "fix": "Reduce AGENTS.md size. Run openclaw doctor to check bootstrap file limits.",
            "severity": "low"
        },
    },
    "stall": {
        "session_stall": {
            "doc": "gateway/troubleshooting.md → No replies",
            "fix": "Session may be wedged. Run: openclaw sessions list, then clear stuck sessions",
            "severity": "high"
        },
        "cleanup_timeout": {
            "doc": "gateway/troubleshooting.md → Cron and heartbeat delivery",
            "fix": "Agent cleanup is timing out. Check for runaway sub-agents or stuck tool calls.",
            "severity": "high"
        },
    },
    "config": {
        "invalid_config": {
            "doc": "gateway/troubleshooting.md → Gateway rejected invalid config",
            "fix": "Run: openclaw doctor --fix to repair config. Check openclaw.json for syntax errors.",
            "severity": "critical"
        },
        "protocol_mismatch": {
            "doc": "gateway/troubleshooting.md → Dashboard control UI connectivity",
            "fix": "Update Control UI to match gateway version. Run: openclaw gateway restart",
            "severity": "low"
        },
    },
    "workspace": {
        "bootstrap_oversized": {
            "doc": "gateway/doctor.md → Bootstrap file size (11b)",
            "fix": "Reduce AGENTS.md to under 12000 chars. Move detailed docs to separate files.",
            "severity": "medium"
        },
    },
    "tool": {
        "file_not_found": {
            "doc": "tools/ → File operations",
            "fix": "Check file paths in tool calls. Ensure files exist before reading.",
            "severity": "medium"
        },
        "tool_failed": {
            "doc": "gateway/troubleshooting.md → Node paired, tool fails",
            "fix": "Check tool permissions and approvals. Run: openclaw approvals get",
            "severity": "medium"
        },
    },
    "timeout": {
        "fetch_timeout": {
            "doc": "gateway/troubleshooting.md → Channel connected, messages not flowing",
            "fix": "Check network connectivity. Increase timeout in config if on slow connection.",
            "severity": "medium"
        },
    },
    "recovery": {
        "stale_locks": {
            "doc": "gateway/doctor.md → Session lock cleanup (3c)",
            "fix": "Run: openclaw doctor --fix to clear stale lock files",
            "severity": "low"
        },
        "interrupted_sessions": {
            "doc": "gateway/doctor.md → Session transcript branch repair (3d)",
            "fix": "Gateway auto-recovers. If persistent: openclaw doctor --fix",
            "severity": "low"
        },
    },
    "symlink": {
        "symlink_perms": {
            "doc": "gateway/troubleshooting.md → Skill symlink skipped as path escape",
            "fix": "Windows requires elevated perms for symlinks. This is expected, not a true error.",
            "severity": "info"
        },
    },
    "failover": {
        "run_aborted": {
            "doc": "gateway/configuration.md → Fallback models",
            "fix": "Add fallback models to config: deepseek/deepseek-v4-flash:free, poolside/laguna-m.1:free",
            "severity": "medium"
        },
    },
}


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_today_log():
    """Return path to today's gateway log."""
    today = datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(GLOB_LOG_DIR, f"openclaw-{today}.log")
    if os.path.exists(path):
        return path
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
                    break
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


def lookup_docs_remedy(category, label):
    """Cross-reference error with OpenClaw docs best practices."""
    cat_refs = DOCS_REFERENCE.get(category, {})
    # Try exact match first, then partial
    for key, ref in cat_refs.items():
        if key in label.lower().replace(" ", "_") or key in category:
            return ref
    # Try matching by keywords in label
    label_lower = label.lower()
    for key, ref in cat_refs.items():
        kw = key.replace("_", " ")
        if kw in label_lower:
            return ref
    return None


def generate_prescription(errors):
    """Generate a structured prescription from scanned errors."""
    os.makedirs(os.path.dirname(PRESCRIPTION_PATH), exist_ok=True)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append(f"# 🏥 OWL DOCTOR PRESCRIPTION")
    lines.append(f"")
    lines.append(f"**Generated:** {now}")
    lines.append(f"**Errors Found:** {len(errors)}")
    lines.append(f"**Status:** ⏳ PENDING MAD APPROVAL")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    if not errors:
        lines.append("## ✅ No Errors Detected")
        lines.append("")
        lines.append("System is healthy. No prescription needed.")
        lines.append("")
    else:
        # Group by severity
        critical = [e for e in errors if e["severity"] in ("critical", "error")]
        warnings = [e for e in errors if e["severity"] == "warn"]
        infos = [e for e in errors if e["severity"] in ("info", "low")]

        lines.append(f"## 🔴 Critical/Errors ({len(critical)})")
        lines.append("")
        for i, e in enumerate(critical, 1):
            remedy = lookup_docs_remedy(e["category"], e["label"])
            lines.append(f"### {i}. {e['label']} (×{e['count']})")
            lines.append(f"- **Category:** {e['category']}")
            lines.append(f"- **Severity:** {e['severity']}")
            lines.append(f"- **Occurrences:** {e['count']}")
            if remedy:
                lines.append(f"- **📖 Doc Reference:** `{remedy['doc']}`")
                lines.append(f"- **💊 Recommended Fix:** {remedy['fix']}")
                lines.append(f"- **Priority:** {remedy['severity']}")
            else:
                lines.append(f"- **💊 Recommended Fix:** Manual investigation needed")
            lines.append("")

        lines.append(f"## 🟡 Warnings ({len(warnings)})")
        lines.append("")
        for i, e in enumerate(warnings, 1):
            remedy = lookup_docs_remedy(e["category"], e["label"])
            lines.append(f"### {i}. {e['label']} (×{e['count']})")
            lines.append(f"- **Category:** {e['category']}")
            lines.append(f"- **Severity:** {e['severity']}")
            lines.append(f"- **Occurrences:** {e['count']}")
            if remedy:
                lines.append(f"- **📖 Doc Reference:** `{remedy['doc']}`")
                lines.append(f"- **💊 Recommended Fix:** {remedy['fix']}")
            lines.append("")

        if infos:
            lines.append(f"## ℹ️ Info ({len(infos)})")
            lines.append("")
            for i, e in enumerate(infos, 1):
                lines.append(f"### {i}. {e['label']} (×{e['count']})")
                lines.append(f"- **Category:** {e['category']}")
                lines.append(f"- **Severity:** {e['severity']}")
                lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("## 📋 APPROVAL REQUIRED")
        lines.append("")
        lines.append("Review the fixes above. To approve and execute:")
        lines.append("1. Reply **APPROVE** to execute all recommended fixes via self-heal")
        lines.append("2. Reply **APPROVE <number>** to execute specific fix (e.g., `APPROVE 1 3`)")
        lines.append("3. Reply **REJECT** to skip healing this cycle")
        lines.append("4. Reply **DETAIL <number>** for full log context on an error")
        lines.append("")
        lines.append("⚠️ Self-heal will activate a 1-min safety cron before executing.")
        lines.append("   If self-heal fails or hangs, the safety cron will recover the gateway.")
        lines.append("")

    content = "\n".join(lines)
    with open(PRESCRIPTION_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    return content


def run_doctor_scan():
    """Full doctor scan pipeline."""
    from db.schema import init_db
    init_db()

    log_path = get_today_log()
    if not log_path:
        print("⚠️  No gateway log found. Skipping scan.")
        return []

    print(f"🔍 Doctor scanning: {log_path}")
    raw_errors = scan_log(log_path)
    deduped = dedup_errors(raw_errors)

    print(f"   Found {len(raw_errors)} raw → {len(deduped)} unique errors")

    # Log to DB
    conn = get_conn()
    for e in deduped:
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
                ("gateway", e["severity"], e["category"], e["label"], e["sample_raw"],
                 e["first_seen"], e["last_seen"], e["count"]),
            )
    conn.commit()
    conn.close()

    return deduped


def print_prescription_summary(prescription_text):
    """Print a concise summary of the prescription."""
    print("\n" + "=" * 60)
    print("🏥 OWL DOCTOR PRESCRIPTION SUMMARY")
    print("=" * 60)
    print(prescription_text[:3000])
    if len(prescription_text) > 3000:
        print(f"\n... (full prescription at {PRESCRIPTION_PATH})")
    print("=" * 60)


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or "--full" in args:
        errors = run_doctor_scan()
        prescription = generate_prescription(errors)
        print_prescription_summary(prescription)
    elif "--scan" in args:
        errors = run_doctor_scan()
        print(f"Scanned. Found {len(errors)} unique errors.")
    elif "--prescribe" in args:
        # Re-generate prescription from existing DB data
        conn = get_conn()
        rows = conn.execute(
            "SELECT category, message as label, severity, occurrence_count as count, "
            "first_seen, last_seen, raw_log_line as sample_raw "
            "FROM errors WHERE resolved=0 ORDER BY severity DESC, occurrence_count DESC"
        ).fetchall()
        errors = [dict(r) for r in rows]
        conn.close()
        prescription = generate_prescription(errors)
        print_prescription_summary(prescription)
    elif "--report" in args:
        conn = get_conn()
        print("\n" + "=" * 60)
        print("🏥 OWL DOCTOR REPORT")
        print("=" * 60)
        errors = conn.execute(
            "SELECT * FROM errors WHERE resolved=0 ORDER BY severity DESC, occurrence_count DESC"
        ).fetchall()
        if errors:
            print(f"\n🔴 Unresolved Errors ({len(errors)}):")
            for e in errors:
                icon = "🔴" if e["severity"] in ("error", "critical") else "🟡"
                print(f"   {icon} [{e['category']}] {e['message']} (×{e['occurrence_count']})")
        else:
            print("\n✅ No unresolved errors.")
        conn.close()
        print("\n" + "=" * 60)
    else:
        print("Usage: python tools/doctor.py [--scan] [--prescribe] [--full] [--report]")
