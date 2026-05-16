#!/usr/bin/env python3
"""
Memory Sync Daemon — Background Agent Memory Tracker
=====================================================
Runs continuously in the background. Every 60 seconds, scans all agent
progress files for changes. When an agent hits 7 updates since last sync,
triggers:
  1. Memory sync (progress → working memory → persistent memory)
  2. Progress file summarization (if entries > 20)
  3. Repo memory update
  4. Team chat notification

Uses OpenRouter (Nemotron 3 Nano Omni — free) for summarization.

Usage:
  python tools/memory_sync_daemon.py              # Run in foreground
  python tools/memory_sync_daemon.py --background # Run in background (Windows)
  python tools/memory_sync_daemon.py --stop       # Stop background daemon
  python tools/memory_sync_daemon.py --status     # Check daemon status
"""

import argparse
import json
import os
import sys
import time
import signal
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

LAB_ROOT = Path(__file__).resolve().parent.parent
PID_FILE = LAB_ROOT / ".memory-sync-daemon.pid"
STATUS_FILE = LAB_ROOT / ".memory-sync-daemon.status.json"
COUNTER_FILE = LAB_ROOT / ".progress-sync-counters.json"

# ── Configuration ────────────────────────────────────────────────────────────

SYNC_THRESHOLD = 7  # Sync every 7 updates per agent
SUMMARIZE_THRESHOLD = 20  # Summarize progress file when entries exceed this
SCAN_INTERVAL = 60  # Seconds between scans

# OpenRouter config
OPENROUTER_API_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
SUMMARIZE_MODEL = "nvidia/nemotron-3-nano-omni-30b-a3b:free"

AGENTS = {
    "CC": {
        "tag": "CC", "name": "Claude Code", "emoji": "🔵",
        "progress_file": "progress/claude-code-progress.md",
        "memory_file": "progress/claude-code-memory.md",
        "section_header": "🔵 [CC] Claude Code",
    },
    "OC": {
        "tag": "OC", "name": "OpenClaw", "emoji": "🟣",
        "progress_file": "progress/openclaw-progress.md",
        "memory_file": "progress/openclaw-memory.md",
        "section_header": "🟣 [OC] OpenClaw",
    },
    "OC2": {
        "tag": "OC2", "name": "OpenClaw 2", "emoji": "🟠",
        "progress_file": "progress/openclaw-2-progress.md",
        "memory_file": "progress/openclaw-2-memory.md",
        "section_header": "🟠 [OC2] OpenClaw 2",
    },
    "PM": {
        "tag": "PM", "name": "Polymorph", "emoji": "🔴",
        "progress_file": "progress/polymorph-progress.md",
        "memory_file": "progress/polymorph-memory.md",
        "section_header": "🔴 [PM] Polymorph",
    },
    "AS": {
        "tag": "AS", "name": "Assistant Manager", "emoji": "🟡",
        "progress_file": "progress/assistant-progress.md",
        "memory_file": "progress/assistant-memory.md",
        "section_header": "🟡 [AS] Assistant Manager",
    },
    "RL": {
        "tag": "RL", "name": "OWL", "emoji": "🦉",
        "progress_file": "progress/rl-progress.md",
        "memory_file": "progress/rl-memory.md",
        "section_header": "🦉 [RL] OWL",
    },
}


# ── Daemon Lifecycle ─────────────────────────────────────────────────────────

def write_pid():
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))


def remove_pid():
    if PID_FILE.exists():
        PID_FILE.unlink()


def is_running() -> bool:
    if not PID_FILE.exists():
        return False
    try:
        pid = int(PID_FILE.read_text().strip())
        if sys.platform == "win32":
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True, text=True
            )
            return str(pid) in result.stdout
        else:
            os.kill(pid, 0)
            return True
    except (ValueError, ProcessLookupError, OSError):
        return False


def write_status(status: dict):
    status["timestamp"] = datetime.now(timezone.utc).isoformat()
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2)


# ── File Fingerprinting ─────────────────────────────────────────────────────

def get_fingerprint(filepath: Path) -> str:
    if not filepath.exists():
        return ""
    stat = filepath.stat()
    return f"{stat.st_mtime}:{stat.st_size}"


def load_counters() -> dict:
    if COUNTER_FILE.exists():
        try:
            with open(COUNTER_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"agents": {}, "files": {}, "total_updates": 0, "last_sync_count": 0, "last_sync_time": None}


def save_counters(counters: dict):
    with open(COUNTER_FILE, "w") as f:
        json.dump(counters, f, indent=2)


# ── Entry Counting ───────────────────────────────────────────────────────────

def count_entries(filepath: Path) -> int:
    """Count the number of #### entries in a progress file."""
    if not filepath.exists():
        return 0
    content = filepath.read_text(encoding="utf-8")
    return content.count("#### ")


# ── LLM Summarization via OpenRouter ────────────────────────────────────────

def summarize_entries(entries_text: str, agent_name: str) -> str:
    """Send old entries to Nemotron 3 Nano Omni for summarization."""
    import urllib.request
    import urllib.error

    prompt = f"""You are summarizing progress log entries for {agent_name}.
Compress these entries into a compact summary (max 300 words).
Preserve: key accomplishments, decisions made, systems built, bugs fixed, phase transitions.
Remove: redundant details, repeated context, verbose explanations.
Format: Use bullet points. Start with date range covered.

ENTRIES TO SUMMARIZE:
{entries_text}

COMPACT SUMMARY:"""

    payload = json.dumps({
        "model": SUMMARIZE_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500,
        "temperature": 0.3,
    }).encode("utf-8")

    req = urllib.request.Request(
        OPENROUTER_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"⚠ Summarization failed ({e}). Original entries preserved."


# ── Progress File Summarization ─────────────────────────────────────────────

def summarize_progress_file(agent_tag: str) -> bool:
    """
    When a progress file has > SUMMARIZE_THRESHOLD entries:
    1. Extract oldest entries (1 through N-5)
    2. Summarize them via LLM
    3. Replace oldest entries with summary block
    4. Keep newest 5 entries intact
    Returns True if summarization was performed.
    """
    agent = AGENTS[agent_tag]
    filepath = LAB_ROOT / agent["progress_file"]

    if not filepath.exists():
        return False

    total_entries = count_entries(filepath)
    if total_entries <= SUMMARIZE_THRESHOLD:
        return False

    print(f"  📝 {agent['name']}: {total_entries} entries — summarizing...")

    content = filepath.read_text(encoding="utf-8")

    # Split into sections: header + entries
    lines = content.split("\n")
    header_lines = []
    entry_blocks = []
    current_block = []
    in_entry = False

    for line in lines:
        if line.startswith("#### "):
            if current_block:
                entry_blocks.append("\n".join(current_block))
            current_block = [line]
            in_entry = True
        elif in_entry:
            current_block.append(line)
        else:
            header_lines.append(line)

    if current_block:
        entry_blocks.append("\n".join(current_block))

    if len(entry_blocks) <= SUMMARIZE_THRESHOLD:
        return False

    # Summarize oldest entries (keep newest 5)
    keep_newest = 5
    to_summarize = entry_blocks[:-keep_newest]
    keep_blocks = entry_blocks[-keep_newest:]

    entries_text = "\n\n".join(to_summarize)
    summary = summarize_entries(entries_text, agent["name"])

    # Build summarized block
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    summary_block = (
        f"#### 📦 SUMMARIZED BLOCK — {now}\n"
        f"*({len(to_summarize)} older entries compressed via LLM)*\n\n"
        f"{summary}\n"
    )

    # Reconstruct file
    header_text = "\n".join(header_lines)
    new_content = header_text + "\n\n" + summary_block + "\n" + "\n\n".join(keep_blocks) + "\n"

    filepath.write_text(new_content, encoding="utf-8")
    new_count = count_entries(filepath)
    print(f"  ✅ {agent['name']}: {total_entries} → {new_count} entries")
    return True


# ── Sync Operations (reuse progress-sync.py logic) ───────────────────────────

def extract_recent_entries(filepath: Path, max_entries: int = 5) -> str:
    if not filepath.exists():
        return "*No entries yet*\n"
    content = filepath.read_text(encoding="utf-8")
    entries = []
    current_entry = []
    in_entry = False
    for line in content.split("\n"):
        if line.startswith("#### "):
            if current_entry:
                entries.append("\n".join(current_entry))
            current_entry = [line]
            in_entry = True
        elif in_entry and line.strip():
            current_entry.append(line)
        elif in_entry and not line.strip():
            if current_entry:
                entries.append("\n".join(current_entry))
            current_entry = []
            in_entry = False
    if current_entry:
        entries.append("\n".join(current_entry))
    recent = entries[-max_entries:] if entries else ["*No entries yet*"]
    return "\n\n".join(recent)


def sync_agent_memory(agent_tag: str):
    """Sync agent progress → working memory file."""
    agent = AGENTS[agent_tag]
    progress_path = LAB_ROOT / agent["progress_file"]
    memory_path = LAB_ROOT / agent["memory_file"]

    if not progress_path.exists():
        return

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    progress_content = progress_path.read_text(encoding="utf-8")

    import re
    status_match = re.search(r"## Status: (.+)", progress_content)
    status = status_match.group(1).strip() if status_match else "Unknown"
    phase_match = re.search(r"### (?:Current Phase|Active Phase)\n(.+)", progress_content)
    phase = phase_match.group(1).strip() if phase_match else "None"
    tasks = re.findall(r"- \[ \] (.+)", progress_content)
    tasks_text = "\n".join(f"- {t}" for t in tasks[:10]) if tasks else "- None"
    entries = extract_recent_entries(progress_path, max_entries=3)

    memory_content = f"""# {agent['emoji']} {agent['name']} — Working Memory

> **Auto-synced** from `{agent['progress_file']}` every {SYNC_THRESHOLD} updates.
> This is working memory — compact, current, task-focused.
> Max ~2,000 chars. Prune old entries when full.

---

## Current Context ({now})

### Status
{status}

### Active Phase
{phase}

### Pending Tasks
{tasks_text}

### Recent Activity
{entries}

---

## Sync Metadata
- **Last Sync:** {now}
- **Progress File:** `{agent['progress_file']}`
- **Working Memory:** `{agent['memory_file']}`
- **Sync Threshold:** {SYNC_THRESHOLD} updates
- **Summarize Threshold:** {SUMMARIZE_THRESHOLD} entries
"""

    memory_path.parent.mkdir(parents=True, exist_ok=True)
    memory_path.write_text(memory_content, encoding="utf-8")
    print(f"  ✅ {agent['name']} working memory synced")


def sync_agent_to_team_chat(agent_tag: str):
    """Post a brief sync notification to team chat."""
    agent = AGENTS[agent_tag]
    chat_path = LAB_ROOT / "shared-conversations" / "team-chat.md"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    entry = (
        f"\n#### {agent['emoji']} [{agent['tag']}] Auto-Sync — {now}\n"
        f"- Memory synced ({SYNC_THRESHOLD} update threshold reached)\n"
        f"- Progress file: `{agent['progress_file']}`\n"
        f"- Working memory: `{agent['memory_file']}`\n"
    )

    if chat_path.exists():
        content = chat_path.read_text(encoding="utf-8")
        chat_path.write_text(content + entry, encoding="utf-8")
    else:
        chat_path.parent.mkdir(parents=True, exist_ok=True)
        chat_path.write_text(f"# Team Chat\n{entry}", encoding="utf-8")


# ── Main Scan Loop ───────────────────────────────────────────────────────────

def scan_and_sync():
    """Single scan pass: check all agents, sync if needed."""
    counters = load_counters()
    any_synced = False

    for tag, agent in AGENTS.items():
        progress_path = LAB_ROOT / agent["progress_file"]
        current_fp = get_fingerprint(progress_path)

        agents_state = counters.setdefault("agents", {})
        agent_state = agents_state.get(tag, {})
        previous_fp = agent_state.get("fingerprint", "")

        changed = (current_fp != previous_fp) and (current_fp != "")

        if changed:
            agent_state["fingerprint"] = current_fp
            agent_state["last_changed"] = datetime.now(timezone.utc).isoformat()
            agent_state["update_count"] = agent_state.get("update_count", 0) + 1
            agents_state[tag] = agent_state
            counters["agents"] = agents_state

            total = agent_state["update_count"]
            last_sync = agent_state.get("last_sync_count", 0)

            # Check if we should sync (every 7 updates)
            if (total - last_sync) >= SYNC_THRESHOLD:
                print(f"\n🔄 [{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Syncing {agent['name']} (update {total})...")

                # 1. Sync memory
                sync_agent_memory(tag)

                # 2. Summarize if file is getting large
                summarize_progress_file(tag)

                # 3. Update team chat
                sync_agent_to_team_chat(tag)

                # 4. Update counters
                agent_state["last_sync_count"] = total
                agent_state["last_sync_time"] = datetime.now(timezone.utc).isoformat()
                counters["agents"][tag] = agent_state

                any_synced = True
                print(f"  ✅ {agent['name']} fully synced")

    if any_synced:
        save_counters(counters)

    return any_synced


def run_daemon():
    """Main daemon loop."""
    write_pid()
    write_status({"status": "running", "scans": 0, "syncs": 0})
    print(f"🧠 Memory Sync Daemon started (PID {os.getpid()})")
    print(f"   Scan interval: {SCAN_INTERVAL}s | Sync threshold: {SYNC_THRESHOLD} updates")
    print(f"   Summarize threshold: {SUMMARIZE_THRESHOLD} entries")
    print(f"   Model: {SUMMARIZE_MODEL}")
    print(f"   Press Ctrl+C to stop\n")

    scans = 0
    syncs = 0

    def handle_signal(signum, frame):
        print("\n🛑 Daemon stopping...")
        remove_pid()
        write_status({"status": "stopped", "scans": scans, "syncs": syncs})
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    while True:
        try:
            scans += 1
            if scans % 10 == 0:
                print(f"  📊 Scan #{scans} | Syncs: {syncs} | {datetime.now(timezone.utc).strftime('%H:%M:%S')}")

            if scan_and_sync():
                syncs += 1

            write_status({"status": "running", "scans": scans, "syncs": syncs})

        except Exception as e:
            print(f"  ⚠ Error in scan: {e}")

        time.sleep(SCAN_INTERVAL)


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Memory Sync Daemon — Background Agent Memory Tracker")
    parser.add_argument("--background", action="store_true", help="Run as background process (Windows)")
    parser.add_argument("--stop", action="store_true", help="Stop background daemon")
    parser.add_argument("--status", action="store_true", help="Check daemon status")
    parser.add_argument("--once", action="store_true", help="Run single scan and exit")
    args = parser.parse_args()

    if args.stop:
        if is_running():
            pid = int(PID_FILE.read_text().strip())
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
            else:
                os.kill(pid, signal.SIGTERM)
            remove_pid()
            print(f"🛑 Daemon stopped (PID {pid})")
        else:
            print("ℹ Daemon not running")
        return

    if args.status:
        if is_running():
            pid = int(PID_FILE.read_text().strip())
            status = {}
            if STATUS_FILE.exists():
                status = json.loads(STATUS_FILE.read_text())
            print(f"🧠 Daemon running (PID {pid})")
            print(f"   Scans: {status.get('scans', '?')} | Syncs: {status.get('syncs', '?')}")
            print(f"   Last update: {status.get('timestamp', '?')}")
        else:
            print("ℹ Daemon not running")
        return

    if args.background:
        if is_running():
            print("ℹ Daemon already running")
            return
        # Launch as hidden background process
        if sys.platform == "win32":
            subprocess.Popen(
                [sys.executable, __file__],
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(1)
            if is_running():
                pid = int(PID_FILE.read_text().strip())
                print(f"🧠 Daemon started in background (PID {pid})")
            else:
                print("⚠ Failed to start daemon")
        else:
            subprocess.Popen(
                [sys.executable, __file__],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            print("🧠 Daemon started in background")
        return

    if args.once:
        print("🔍 Running single scan...")
        scan_and_sync()
        return

    # Default: run in foreground
    run_daemon()


if __name__ == "__main__":
    main()
