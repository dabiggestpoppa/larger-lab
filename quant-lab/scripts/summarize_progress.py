#!/usr/bin/env python3
"""
SUMMARIZE PROGRESS — PO Daily Summary Generator
================================================
Replaces the missing summarize_progress.py that cron was calling.
Reads: team-chat.md, git log, demo bridge logs, agent states
Outputs: structured daily summary to stdout and optionally to a file.

Usage:
    python summarize_progress.py                  # print to stdout
    python summarize_progress.py --output FILE    # write to file
    python summarize_progress.py --days 3         # summarize last N days
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

# ─── Paths ───────────────────────────────────────────────────────────────────

WORKSPACE = Path(os.environ.get("WORKSPACE", r"C:\Users\wifik\Desktop\projects\larger-lab"))
TEAM_CHAT = WORKSPACE / "team-chat.md"
BRIDGE_LOG = WORKSPACE / "quant-lab" / "mt5" / "demo_logs" / "demo_bridge.log"
BRIDGE_STATE = WORKSPACE / "quant-lab" / "mt5" / "demo_logs" / "demo_bridge_state.json"
SIGNALS_LOG = WORKSPACE / "quant-lab" / "mt5" / "demo_logs" / "signals.jsonl"
OCE_AGENTS_DIR = WORKSPACE / "shared-conversations"

# ─── Git Log ─────────────────────────────────────────────────────────────────

def get_git_summary(days: int = 7) -> dict:
    """Get commit count and authors from git log."""
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    try:
        result = subprocess.run(
            ["git", "log", f"--since={since}", "--oneline", "--all"],
            capture_output=True, text=True, cwd=WORKSPACE, timeout=30
        )
        commits = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
        authors = set()
        for c in commits:
            parts = c.split(" ", 1)
            if len(parts) > 1:
                authors.add(parts[0])
        return {"commits": len(commits), "authors": len(authors), "latest": commits[:5]}
    except Exception as e:
        return {"error": str(e)}

# ─── Bridge Status ───────────────────────────────────────────────────────────

def parse_bridge_log(days: int = 1) -> dict:
    """Parse demo bridge log for recent activity."""
    if not BRIDGE_LOG.exists():
        return {"error": "Bridge log not found"}

    cutoff = datetime.now() - timedelta(days=days)
    stats = {
        "total_lines": 0,
        "scans": 0,
        "trades": 0,
        "wins": 0,
        "losses": 0,
        "errors": 0,
        "last_scan": None,
        "last_trade": None,
        "pnl_entries": [],
    }

    try:
        with open(BRIDGE_LOG, "r", encoding="utf-8") as f:
            for line in f:
                stats["total_lines"] += 1
                line = line.strip()

                if "Scan |" in line:
                    stats["scans"] += 1
                    # Extract timestamp
                    match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
                    if match:
                        ts = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
                        if ts > cutoff:
                            stats["last_scan"] = match.group(1)

                if "DEMO PNL:" in line:
                    stats["trades"] += 1
                    stats["pnl_entries"].append(line)
                    match = re.search(r"profit=([-\d.]+)", line)
                    if match:
                        pnl = float(match.group(1))
                        if pnl > 0:
                            stats["wins"] += 1
                        else:
                            stats["losses"] += 1

                if "DEMO Position closed:" in line:
                    match = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
                    if match:
                        stats["last_trade"] = match.group(1)

                if "ERROR" in line or "Error" in line:
                    stats["errors"] += 1

    except Exception as e:
        return {"error": str(e)}

    return stats

def parse_bridge_state() -> dict:
    """Parse current bridge state JSON."""
    if not BRIDGE_STATE.exists():
        return {"error": "Bridge state file not found"}
    try:
        with open(BRIDGE_STATE, "r") as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}

# ─── Agent States ────────────────────────────────────────────────────────────

def check_agent_states() -> dict:
    """Check for agent state files and summarize."""
    states = {}
    agents_dir = OCE_AGENTS_DIR

    if not agents_dir.exists():
        return {"error": "Agents directory not found"}

    for f in agents_dir.iterdir():
        if f.suffix in (".md", ".json", ".txt") and not f.name.startswith("archive"):
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                # Look for status keywords
                for status in ["STALE", "MISSING", "ACTIVE", "RUNNING", "DISCONNECTED"]:
                    if status in content.upper():
                        states[f.stem] = status
                        break
                if f.stem not in states:
                    states[f.stem] = "UNKNOWN"
            except Exception:
                states[f.stem] = "READ_ERROR"

    return states

# ─── Team Chat Summary ───────────────────────────────────────────────────────

def summarize_team_chat(days: int = 7) -> list:
    """Extract recent daily summaries from team-chat.md."""
    if not TEAM_CHAT.exists():
        return [{"error": "team-chat.md not found"}]

    summaries = []
    cutoff = datetime.now() - timedelta(days=days)

    try:
        content = TEAM_CHAT.read_text(encoding="utf-8")
        # Split by daily summary headers
        sections = re.split(r"(?=# Daily Summary)", content)

        for section in sections:
            match = re.search(r"(\d{4}-\d{2}-\d{2})", section)
            if match:
                date_str = match.group(1)
                try:
                    date = datetime.strptime(date_str, "%Y-%m-%d")
                    if date >= cutoff:
                        # Extract key lines
                        lines = [l.strip() for l in section.split("\n") if l.strip() and l.strip().startswith(("- ", "✅", "🔴", "⚠️", "🟢", "🟡"))]
                        summaries.append({
                            "date": date_str,
                            "lines": lines[:20],  # cap at 20 lines
                            "has_action_items": "Action Items" in section,
                        })
                except ValueError:
                    continue
    except Exception as e:
        return [{"error": str(e)}]

    return summaries

# ─── Main ─────────────────────────────────────────────────────────────────────

def generate_summary(days: int = 7) -> str:
    """Generate full daily summary report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append(f"# PO Daily Summary — {now}")
    lines.append("")

    # Git
    lines.append("## 📦 Git Activity")
    git = get_git_summary(days)
    if "error" in git:
        lines.append(f"- ⚠️ Error: {git['error']}")
    else:
        lines.append(f"- Commits (last {days}d): **{git['commits']}**")
        lines.append(f"- Active authors: **{git['authors']}**")
        if git.get("latest"):
            lines.append("- Latest commits:")
            for c in git["latest"]:
                lines.append(f"  - `{c}`")
    lines.append("")

    # Bridge
    lines.append("## 🌉 OC2 Bridge Status")
    bridge = parse_bridge_log(days)
    state = parse_bridge_state()
    if "error" in bridge:
        lines.append(f"- ⚠️ {bridge['error']}")
    else:
        lines.append(f"- Scans (last {days}d): **{bridge['scans']}**")
        lines.append(f"- Trades: **{bridge['trades']}** (W: {bridge['wins']} / L: {bridge['losses']})")
        lines.append(f"- Errors: **{bridge['errors']}**")
        if bridge.get("last_scan"):
            lines.append(f"- Last scan: **{bridge['last_scan']}**")
        else:
            lines.append("- Last scan: **NEVER** ⚠️")
        if bridge.get("last_trade"):
            lines.append(f"- Last trade: **{bridge['last_trade']}**")
        else:
            lines.append("- Last trade: **NONE** 🔴")

    if "error" not in state:
        active = state.get("positions", {})
        active_count = sum(1 for p in active.values() if p.get("active"))
        lines.append(f"- Active positions: **{active_count}**")
        ds = state.get("daily_stats", {})
        if ds:
            lines.append(f"- Daily stats: T={ds.get('trades',0)} W={ds.get('wins',0)} L={ds.get('losses',0)} PnL=${ds.get('pnl',0):.2f}")
    lines.append("")

    # Agents
    lines.append("## 👥 Agent States")
    agents = check_agent_states()
    if "error" in agents:
        lines.append(f"- ⚠️ {agents['error']}")
    else:
        for name, status in sorted(agents.items()):
            icon = "✅" if status == "ACTIVE" else "🔴" if status in ("STALE", "MISSING") else "🟡"
            lines.append(f"- {icon} **{name}**: {status}")
    lines.append("")

    # Team Chat
    lines.append("## 💬 Team Chat Highlights")
    chat = summarize_team_chat(days)
    for entry in chat:
        if "error" in entry:
            lines.append(f"- ⚠️ {entry['error']}")
        else:
            lines.append(f"- **{entry['date']}**: {'; '.join(entry['lines'][:5])}")
            if entry.get("has_action_items"):
                lines.append(f"  - 📋 Has action items — see team-chat.md")
    lines.append("")

    lines.append("---")
    lines.append(f"*Generated by PO at {now}*")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="PO Daily Summary Generator")
    parser.add_argument("--output", "-o", help="Write summary to file instead of stdout")
    parser.add_argument("--days", "-d", type=int, default=1, help="Number of days to summarize (default: 1)")
    args = parser.parse_args()

    summary = generate_summary(args.days)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(summary, encoding="utf-8")
        print(f"Summary written to {out_path}")
    else:
        print(summary)


if __name__ == "__main__":
    main()