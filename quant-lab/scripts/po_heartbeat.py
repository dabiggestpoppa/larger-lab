#!/usr/bin/env python3
"""
PO HEARTBEAT LOOP — Primary Observer Autonomous Monitor
========================================================
Runs every 5-10 minutes to:
  1. Read vault notes (stay current)
  2. Check git status (any changes?)
  3. Check workspace health (files, processes)
  4. Review own memory files
  5. Check OCE API for agent states
  6. If something needs action → log it or fix it
  7. If all good → log "all good" and exit

Designed to be called by cron or PM2.
Usage: python po_heartbeat.py [--verbose]
"""

import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ─── Config ──────────────────────────────────────────────────────────────────

WORKSPACE_ROOT = Path(__file__).parent.parent  # larger-lab/
VAULT_DIR = WORKSPACE_ROOT / "vault"
TEAM_CHAT = WORKSPACE_ROOT / "team-chat.md"
OCE_API_URL = os.environ.get("OCE_API_URL", "http://localhost:8000")
LOG_DIR = WORKSPACE_ROOT / "quant-lab" / "po_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

HEARTBEAT_LOG = LOG_DIR / "heartbeat.jsonl"
VERBOSE = "--verbose" in sys.argv

logging.basicConfig(
    level=logging.DEBUG if VERBOSE else logging.INFO,
    format="%(asctime)s [PO-HEARTBEAT] %(message)s",
)
log = logging.getLogger("po_heartbeat")


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def check_git_status() -> dict:
    """Check git status for uncommitted changes."""
    result = {"has_changes": False, "modified": [], "untracked": [], "ahead": 0}
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=WORKSPACE_ROOT, timeout=15
        )
        lines = proc.stdout.strip().split("\n") if proc.stdout.strip() else []
        for line in lines:
            status = line[:2].strip()
            path = line[3:].strip()
            if status == "??":
                result["untracked"].append(path)
            else:
                result["modified"].append(path)
        result["has_changes"] = len(result["modified"]) + len(result["untracked"]) > 0

        # Check if ahead of remote
        branch_proc = subprocess.run(
            ["git", "rev-list", "--left-right", "--count", "HEAD...@{u}"],
            capture_output=True, text=True, cwd=WORKSPACE_ROOT, timeout=15
        )
        if branch_proc.stdout.strip():
            behind, ahead = branch_proc.stdout.strip().split()
            result["ahead"] = int(ahead)
            result["behind"] = int(behind)
    except Exception as e:
        log.error(f"Git check failed: {e}")
        result["error"] = str(e)
    return result


def check_vault() -> dict:
    """Check vault for recent changes."""
    result = {"note_count": 0, "recently_modified": []}
    try:
        if VAULT_DIR.exists():
            md_files = list(VAULT_DIR.rglob("*.md"))
            result["note_count"] = len(md_files)
            # Find files modified in last 24h
            for f in sorted(md_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
                result["recently_modified"].append({
                    "file": str(f.relative_to(WORKSPACE_ROOT)),
                    "mtime": datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).isoformat()
                })
    except Exception as e:
        log.error(f"Vault check failed: {e}")
        result["error"] = str(e)
    return result


def check_team_chat() -> dict:
    """Check team-chat.md for recent entries."""
    result = {"exists": False, "last_entry": None, "line_count": 0}
    try:
        if TEAM_CHAT.exists():
            result["exists"] = True
            lines = TEAM_CHAT.read_text().split("\n")
            result["line_count"] = len(lines)
            # Find last daily summary header
            for line in reversed(lines):
                if line.startswith("# Daily Summary"):
                    result["last_entry"] = line.strip()
                    break
    except Exception as e:
        log.error(f"Team chat check failed: {e}")
        result["error"] = str(e)
    return result


def check_oci_api() -> dict:
    """Check OCE API health and agent states."""
    result = {"reachable": False, "agents": {}}
    try:
        import urllib.request
        req = urllib.request.Request(f"{OCE_API_URL}/health", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            result["reachable"] = True
            result["health"] = data

        # Check observer states
        req2 = urllib.request.Request(f"{OCE_API_URL}/observers", method="GET")
        with urllib.request.urlopen(req2, timeout=5) as resp2:
            observers = json.loads(resp2.read())
            result["observers"] = observers
    except Exception as e:
        log.warning(f"OCE API check failed: {e}")
        result["error"] = str(e)
    return result


def check_bridge_status() -> dict:
    """Check demo bridge log for recent activity."""
    result = {"running": False, "last_scan": None, "has_signals": False}
    log_file = WORKSPACE_ROOT / "quant-lab" / "mt5" / "demo_logs" / "demo_bridge.log"
    try:
        if log_file.exists():
            lines = log_file.read_text().strip().split("\n")
            result["running"] = True
            for line in reversed(lines):
                if "Scan" in line or "scan" in line:
                    result["last_scan"] = line.strip()
                    break
            # Check for signals
            for line in lines[-50:]:
                if "SIGNAL" in line or "signal" in line:
                    result["has_signals"] = True
                    break
    except Exception as e:
        log.error(f"Bridge status check failed: {e}")
        result["error"] = str(e)
    return result


def check_stale_agents() -> dict:
    """Check for stale agent state files."""
    result = {"stale_count": 0, "agents": []}
    try:
        import urllib.request
        req = urllib.request.Request(f"{OCE_API_URL}/observers", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            observers = json.loads(resp.read())
            stale = []
            for obs in observers:
                status = obs.get("status", "").upper()
                if status in ("MISSING", "STALE", "DISCONNECTED"):
                    stale.append({
                        "name": obs.get("name", "unknown"),
                        "status": status,
                        "last_seen": obs.get("last_seen", "unknown")
                    })
            result["stale_count"] = len(stale)
            result["agents"] = stale
    except Exception as e:
        log.warning(f"Stale agent check failed: {e}")
        result["error"] = str(e)
    return result


def run_heartbeat(verbose=False) -> dict:
    """Run full heartbeat cycle."""
    report = {
        "timestamp": timestamp(),
        "checks": {}
    }

    log.info("💓 PO Heartbeat starting...")

    # 1. Git status
    report["checks"]["git"] = check_git_status()
    if report["checks"]["git"]["has_changes"]:
        log.warning(f"⚠️  Git: {len(report['checks']['git']['modified'])} modified, {len(report['checks']['git']['untracked'])} untracked")

    # 2. Vault check
    report["checks"]["vault"] = check_vault()
    log.info(f"📚 Vault: {report['checks']['vault']['note_count']} notes")

    # 3. Team chat check
    report["checks"]["team_chat"] = check_team_chat()
    if report["checks"]["team_chat"]["last_entry"]:
        log.info(f"📝 Team chat: {report['checks']['team_chat']['last_entry']}")

    # 4. OCE API check
    report["checks"]["oce_api"] = check_oci_api()
    if report["checks"]["oce_api"]["reachable"]:
        log.info("🔌 OCE API: reachable")
    else:
        log.warning("🔌 OCE API: unreachable")

    # 5. Bridge status
    report["checks"]["bridge"] = check_bridge_status()
    if report["checks"]["bridge"]["running"]:
        if report["checks"]["bridge"]["has_signals"]:
            log.info("📡 Bridge: running, signals detected")
        else:
            log.warning("📡 Bridge: running, NO signals detected")

    # 6. Stale agents
    report["checks"]["stale_agents"] = check_stale_agents()
    if report["checks"]["stale_agents"]["stale_count"] > 0:
        log.warning(f"👻 Stale agents: {report['checks']['stale_agents']['stale_count']}")

    # Summary
    issues = []
    if report["checks"]["git"]["has_changes"]:
        issues.append("uncommitted_changes")
    if not report["checks"]["oce_api"]["reachable"]:
        issues.append("oce_api_down")
    if report["checks"]["bridge"].get("running") and not report["checks"]["bridge"].get("has_signals"):
        issues.append("bridge_no_signals")
    if report["checks"]["stale_agents"]["stale_count"] > 0:
        issues.append(f"{report['checks']['stale_agents']['stale_count']}_stale_agents")

    report["issues"] = issues
    report["status"] = "needs_attention" if issues else "all_clear"

    if issues:
        log.warning(f"🚨 Issues: {', '.join(issues)}")
    else:
        log.info("✅ All clear — field is healthy")

    # Write to JSONL log
    with open(HEARTBEAT_LOG, "a") as f:
        f.write(json.dumps(report) + "\n")

    log.info(f"💓 Heartbeat complete — {report['status']}")
    return report


if __name__ == "__main__":
    report = run_heartbeat(verbose=VERBOSE)
    if VERBOSE:
        print(json.dumps(report, indent=2))
    sys.exit(0 if report["status"] == "all_clear" else 1)