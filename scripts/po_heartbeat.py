"""
PO Heartbeat Worker — keeps PO alive and aware in the field.
Runs on a loop, checks the workspace, posts updates to team chat.

Usage: python scripts/po_heartbeat.py [--interval 300] [--once]
"""
import subprocess
import sys
import time
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parent.parent
TEAM_CHAT = REPO_ROOT / "shared-conversations" / "team-chat.md"
MEMORY_FILE = REPO_ROOT / "MEMORY.md"
STATE_FILE = REPO_ROOT / ".po_heartbeat_state.json"
HEARTBEAT_LOG = REPO_ROOT / "heartbeat.md"

DEFAULT_INTERVAL = 300  # 5 minutes


def utcnow_str():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def run_cmd(cmd, cwd=None):
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd or REPO_ROOT))
    return r.stdout.strip(), r.stderr.strip(), r.returncode


def git_status():
    out, _, _ = run_cmd(["git", "status", "--porcelain"])
    lines = [l for l in out.splitlines() if l.strip()]
    return lines


def git_log_last(n=3):
    out, _, _ = run_cmd(["git", "log", f"-{n}", "--oneline"])
    return out.splitlines()


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"last_check": None, "last_status_hash": None, "checks_done": 0}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def post_to_team_chat(message):
    """Append a PO message to the team shared chat."""
    timestamp = utcnow_str()
    entry = f"\n---\n\n### [PO] {timestamp}\n{message}\n"

    if TEAM_CHAT.exists():
        content = TEAM_CHAT.read_text(encoding="utf-8", errors="replace")
        TEAM_CHAT.write_text(content + entry, encoding="utf-8")
    else:
        TEAM_CHAT.write_text(f"# Team Chat\n{entry}", encoding="utf-8")

    print(f"[heartbeat] Posted to team chat: {message[:80]}")


def append_heartbeat_log(message):
    """Keep a local heartbeat log."""
    timestamp = utcnow_str()
    entry = f"\n## {timestamp}\n{message}\n"
    if HEARTBEAT_LOG.exists():
        content = HEARTBEAT_LOG.read_text(encoding="utf-8", errors="replace")
        HEARTBEAT_LOG.write_text(content + entry, encoding="utf-8")
    else:
        HEARTBEAT_LOG.write_text(f"# PO Heartbeat Log\n{entry}", encoding="utf-8")


def compute_status_hash(status_lines):
    """Hash of current git status to detect changes."""
    return hashlib.md5("".join(status_lines).encode()).hexdigest()


def check_field():
    """Main field check — returns a status report string."""
    state = load_state()
    state["checks_done"] = state.get("checks_done", 0) + 1
    check_num = state["checks_done"]

    report_parts = [f"**Field Check #{check_num}** — {utcnow_str()}"]
    actions_taken = []

    # 1. Git status
    status = git_status()
    status_hash = compute_status_hash(status)
    prev_hash = state.get("last_status_hash")

    if not status:
        report_parts.append("✅ Workspace clean — no uncommitted changes")
    elif status_hash == prev_hash:
        report_parts.append(f"⚠️ {len(status)} uncommitted files (unchanged since last check)")
    else:
        report_parts.append(f"🔄 {len(status)} uncommitted files changed:")
        for line in status[:10]:
            report_parts.append(f"  {line}")
        if len(status) > 10:
            report_parts.append(f"  ... and {len(status) - 10} more")

    state["last_status_hash"] = status_hash

    # 2. Recent commits
    recent = git_log_last(3)
    if recent:
        report_parts.append("\n📋 Recent commits:")
        for line in recent:
            report_parts.append(f"  {line}")

    # 3. Memory file check
    if MEMORY_FILE.exists():
        mem_mtime = MEMORY_FILE.stat().st_mtime
        report_parts.append(f"\n🧠 Memory file: {MEMORY_FILE.name} (modified {datetime.fromtimestamp(mem_mtime).strftime('%Y-%m-%d %H:%M')})")
    else:
        report_parts.append("\n⚠️ No MEMORY.md found")

    # 4. Vault check
    vault_dir = REPO_ROOT / "vault"
    if vault_dir.exists():
        vault_notes = list(vault_dir.rglob("*.md"))
        report_parts.append(f"📚 Vault: {len(vault_notes)} notes")

    # 5. Check for junk files to clean
    junk_patterns = ["*.tmp", "*.bak", "*~", "*.orig"]
    junk_found = []
    for pattern in junk_patterns:
        junk_found.extend(REPO_ROOT.glob(pattern))
    if junk_found:
        report_parts.append(f"\n🗑️ {len(junk_found)} junk files found — consider cleaning")
        actions_taken.append(f"Found {len(junk_found)} junk files")

    # 6. Pre-commit hook health
    hook_file = REPO_ROOT / ".git" / "hooks" / "pre-commit"
    if hook_file.exists():
        report_parts.append("🔒 Pre-commit hook: active")
    else:
        report_parts.append("⚠️ Pre-commit hook: MISSING!")
        actions_taken.append("Pre-commit hook missing!")

    # Save state
    state["last_check"] = utcnow_str()
    save_state(state)

    # Build final report
    full_report = "\n".join(report_parts)

    if actions_taken:
        full_report += "\n\n**Actions needed:** " + "; ".join(actions_taken)

    return full_report, len(status) == 0


def run_once():
    """Run a single heartbeat check."""
    print(f"[heartbeat] Field check starting at {utcnow_str()}")

    report, is_clean = check_field()

    # Post to team chat
    post_to_team_chat(report)

    # Log locally
    append_heartbeat_log(report)

    print(f"[heartbeat] Check complete. Workspace clean: {is_clean}")
    return is_clean


def run_loop(interval=DEFAULT_INTERVAL):
    """Run heartbeat on a loop."""
    print(f"[heartbeat] Starting loop — interval {interval}s")
    post_to_team_chat("🟢 Heartbeat started — PO is in the field")

    try:
        while True:
            run_once()
            print(f"[heartbeat] Sleeping {interval}s...")
            time.sleep(interval)
    except KeyboardInterrupt:
        post_to_team_chat("🔴 Heartbeat stopped")
        print("[heartbeat] Stopped.")


if __name__ == "__main__":
    args = sys.argv[1:]
    interval = DEFAULT_INTERVAL

    if "--interval" in args:
        idx = args.index("--interval")
        if idx + 1 < len(args):
            interval = int(args[idx + 1])

    if "--once" in args:
        run_once()
    else:
        run_loop(interval)
