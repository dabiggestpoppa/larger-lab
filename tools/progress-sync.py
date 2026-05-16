#!/usr/bin/env python3
"""
Progress File → Memory Auto-Sync v2
====================================
Watches sub-progress files per agent. Every N updates:
  1. Syncs agent sub-progress → PROJECT_PROGRESS_CLEAN.md (agent's section)
  2. Syncs agent sub-progress → agent's local memory file
  3. Updates repo memory (/memories/repo/workspace-state.md)

Agent sub-progress files:
  progress/claude-code-progress.md  → CC section in main + claude-code-memory.md
  progress/openclaw-progress.md     → OC section in main + .openclaw/MEMORY.md
  progress/hermes-progress.md       → HR section in main + .hermes/MEMORY.md

Usage:
  python tools/progress-sync.py            # Check counts, sync if threshold met
  python tools/progress-sync.py --force    # Force sync regardless of count
  python tools/progress-sync.py --reset    # Reset all counters
  python tools/progress-sync.py --status   # Show current counts and last sync
  python tools/progress-sync.py --agent CC # Sync specific agent only
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Fix Windows console encoding for emoji output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── Configuration ────────────────────────────────────────────────────────────

LAB_ROOT = Path(__file__).resolve().parent.parent
COUNTER_FILE = LAB_ROOT / ".progress-sync-counters.json"
REPO_MEMORY_FILE = Path("/memories/repo/workspace-state.md")

# Agent registry: tag → {progress_file, memory_file, section_header}
AGENTS = {
    "CC": {
        "tag": "CC",
        "name": "Claude Code",
        "emoji": "🔵",
        "progress_file": "progress/claude-code-progress.md",
        "memory_file": "progress/claude-code-memory.md",
        "section_header": "🔵 [CC] Claude Code",
    },
    "OC": {
        "tag": "OC",
        "name": "OpenClaw",
        "emoji": "🟣",
        "progress_file": "progress/openclaw-progress.md",
        "memory_file": "progress/openclaw-memory.md",
        "section_header": "🟣 [OC] OpenClaw",
    },
    "HR": {
        "tag": "HR",
        "name": "Hermes",
        "emoji": "🟢",
        "progress_file": "progress/hermes-progress.md",
        "memory_file": "progress/hermes-memory.md",
        "section_header": "🟢 [HR] Hermes",
    },
    "PM": {
        "tag": "PM",
        "name": "Polymorph",
        "emoji": "🔴",
        "progress_file": "progress/polymorph-progress.md",
        "memory_file": "progress/polymorph-memory.md",
        "section_header": "🔴 [PM] Polymorph",
    },
    "AS": {
        "tag": "AS",
        "name": "Assistant Manager",
        "emoji": "🟡",
        "progress_file": "progress/assistant-progress.md",
        "memory_file": "progress/assistant-memory.md",
        "section_header": "🟡 [AS] Assistant Manager",
    },
}

# Legacy progress files (still tracked but not agent-specific)
LEGACY_FILES = [
    "PROJECT_PROGRESS.md",
    "research-agents-progress.md",
    "p90-conversion-progress.md",
    "xhaak-kulu-bridge-progress.md",
]

SYNC_THRESHOLD = 3  # Sync every 3 updates per agent

# ── Counter Management ───────────────────────────────────────────────────────


def load_counters() -> dict:
    """Load update counters from disk."""
    if COUNTER_FILE.exists():
        try:
            with open(COUNTER_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {
        "agents": {},
        "files": {},
        "total_updates": 0,
        "last_sync_count": 0,
        "last_sync_time": None,
    }


def save_counters(counters: dict):
    """Persist update counters to disk."""
    with open(COUNTER_FILE, "w") as f:
        json.dump(counters, f, indent=2)


def get_file_fingerprint(filepath: Path) -> str:
    """Get a fingerprint (mtime + size) for change detection."""
    if not filepath.exists():
        return ""
    stat = filepath.stat()
    return f"{stat.st_mtime}:{stat.st_size}"


def scan_agent_updates(counters: dict, agent_tag: str) -> bool:
    """Scan an agent's sub-progress file for changes. Returns True if changed."""
    agent = AGENTS[agent_tag]
    fpath = LAB_ROOT / agent["progress_file"]
    current_fp = get_file_fingerprint(fpath)

    agents_state = counters.setdefault("agents", {})
    agent_state = agents_state.get(agent_tag, {})
    previous_fp = agent_state.get("fingerprint", "")

    changed = (current_fp != previous_fp) and (current_fp != "")

    if changed:
        agent_state["fingerprint"] = current_fp
        agent_state["last_changed"] = datetime.now(timezone.utc).isoformat()
        agent_state["update_count"] = agent_state.get("update_count", 0) + 1
        agents_state[agent_tag] = agent_state

    return changed


def scan_legacy_updates(counters: dict) -> dict:
    """Scan legacy progress files for changes."""
    changes = {}
    files_state = counters.get("files", {})

    for fname in LEGACY_FILES:
        fpath = LAB_ROOT / fname
        current_fp = get_file_fingerprint(fpath)
        previous_fp = files_state.get(fname, {}).get("fingerprint", "")

        changed = (current_fp != previous_fp) and (current_fp != "")
        changes[fname] = changed

        if changed:
            files_state[fname] = {
                "fingerprint": current_fp,
                "last_changed": datetime.now(timezone.utc).isoformat(),
                "update_count": files_state.get(fname, {}).get("update_count", 0) + 1,
            }

    counters["files"] = files_state
    return changes


def should_sync_agent(counters: dict, agent_tag: str) -> bool:
    """Check if an agent has hit the sync threshold since last sync."""
    agents_state = counters.get("agents", {})
    agent_state = agents_state.get(agent_tag, {})
    total = agent_state.get("update_count", 0)
    last_sync = agent_state.get("last_sync_count", 0)
    return (total - last_sync) >= SYNC_THRESHOLD


# ── Sync Operations ──────────────────────────────────────────────────────────


def extract_recent_entries(filepath: Path, max_entries: int = 5) -> str:
    """Extract recent entries from an agent's sub-progress file."""
    if not filepath.exists():
        return "*No entries yet*\n"

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

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


def sync_agent_to_main_progress(agent_tag: str):
    """Sync an agent's sub-progress into their section of PROJECT_PROGRESS_CLEAN.md."""
    agent = AGENTS[agent_tag]
    progress_path = LAB_ROOT / agent["progress_file"]
    main_path = LAB_ROOT / "PROJECT_PROGRESS_CLEAN.md"

    if not progress_path.exists():
        return

    recent = extract_recent_entries(progress_path)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    section_lines = [
        f"## {agent['section_header']} — Last Sync: {now}",
        "",
        f"*Auto-synced from `{agent['progress_file']}`*",
        "",
        recent,
        "",
        "---",
        "",
    ]
    section_text = "\n".join(section_lines)

    if main_path.exists():
        with open(main_path, "r", encoding="utf-8") as f:
            main_content = f.read()
    else:
        main_content = "# Project Progress & Context\n"

    section_pattern = rf"## {re.escape(agent['section_header'])}.*?---\n"
    if re.search(section_pattern, main_content, re.DOTALL):
        main_content = re.sub(section_pattern, section_text, main_content, flags=re.DOTALL)
    else:
        insert_marker = "---\n\n## "
        if insert_marker in main_content:
            parts = main_content.split(insert_marker, 1)
            main_content = parts[0] + "---\n\n" + section_text + "## " + parts[1]
        else:
            main_content += "\n" + section_text

    with open(main_path, "w", encoding="utf-8") as f:
        f.write(main_content)

    print(f"  ✅ {agent['name']} → PROJECT_PROGRESS_CLEAN.md")


def sync_agent_memory(agent_tag: str):
    """Sync an agent's sub-progress into their local working memory file."""
    agent = AGENTS[agent_tag]
    progress_path = LAB_ROOT / agent["progress_file"]
    memory_path = LAB_ROOT / agent["memory_file"]

    if not progress_path.exists():
        return

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    with open(progress_path, "r", encoding="utf-8") as f:
        progress_content = f.read()

    status_match = re.search(r"## Status: (.+)", progress_content)
    status = status_match.group(1).strip() if status_match else "Unknown"

    phase_match = re.search(r"### Current Phase\n(.+)", progress_content)
    phase = phase_match.group(1).strip() if phase_match else "None"

    tasks = re.findall(r"- \[ \] (.+)", progress_content)
    tasks_text = "\n".join(f"- {t}" for t in tasks[:10]) if tasks else "- None"

    entries = extract_recent_entries(progress_path, max_entries=3)

    memory_content = f"""# {agent['emoji']} {agent['name']} — Working Memory

> **Auto-synced** from `{agent['progress_file']}` on every {SYNC_THRESHOLD}th update.
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
"""

    memory_path.parent.mkdir(parents=True, exist_ok=True)
    with open(memory_path, "w", encoding="utf-8") as f:
        f.write(memory_content)

    print(f"  ✅ {agent['name']} working memory → {agent['memory_file']}")


def append_to_persistent_memory(agent_tag: str):
    """Append a summary line to the agent's persistent MEMORY.md (without overwriting)."""
    agent = AGENTS[agent_tag]
    progress_path = LAB_ROOT / agent["progress_file"]

    if not progress_path.exists():
        return

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    with open(progress_path, "r", encoding="utf-8") as f:
        progress_content = f.read()

    phase_match = re.search(r"### Current Phase\n(.+)", progress_content)
    phase = phase_match.group(1).strip() if phase_match else "None"

    status_match = re.search(r"## Status: (.+)", progress_content)
    status = status_match.group(1).strip() if status_match else "Unknown"

    # Persistent memory file paths (hand-managed, contains credentials etc.)
    persistent_map = {
        "OC": ".openclaw/MEMORY.md",
        "HR": ".hermes/MEMORY.md",
        "CC": "MEMORY.md",  # Claude Code doesn't have a separate persistent file
        "AS": "progress/assistant-progress.md",  # AS uses its sub-progress as persistent
    }

    persistent_path = LAB_ROOT / persistent_map.get(agent_tag, "")
    if not persistent_path or not persistent_path.exists():
        return

    # Read existing persistent memory
    with open(persistent_path, "r", encoding="utf-8") as f:
        existing = f.read()

    # Check if there's a sync summary section
    sync_marker = f"## Progress Sync Summary ({agent['tag']})"
    summary_line = (
        f"\n## Progress Sync Summary ({agent['tag']})\n"
        f"> **Last Sync:** {now}\n"
        f"> **Status:** {status}\n"
        f"> **Active Phase:** {phase}\n"
        f"> **Working Memory:** `{agent['memory_file']}`\n"
    )

    if sync_marker in existing:
        # Replace existing summary section
        pattern = rf"## Progress Sync Summary \({agent['tag']}\).*?(?=\n## |\Z)"
        existing = re.sub(pattern, summary_line.strip(), existing, flags=re.DOTALL)
    else:
        # Append at end
        existing = existing.rstrip() + "\n" + summary_line

    with open(persistent_path, "w", encoding="utf-8") as f:
        f.write(existing)

    print(f"  ✅ {agent['name']} persistent memory ← sync summary appended")


def sync_repo_memory(counters: dict):
    """Sync overall state to repo memory."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    sections = [
        f"# Workspace State — Repo Memory\n",
        f"> **Last Synced:** {now}",
        f"> **Source:** Auto-sync from agent sub-progress files",
        f"> **Sync Threshold:** {SYNC_THRESHOLD} updates per agent",
        "",
        "---",
        "",
    ]

    for tag, agent in AGENTS.items():
        progress_path = LAB_ROOT / agent["progress_file"]
        if progress_path.exists():
            sections.append(f"## {agent['section_header']}")
            sections.append("")
            recent = extract_recent_entries(progress_path, max_entries=3)
            sections.append(recent)
            sections.append("")
            sections.append("---")
            sections.append("")

    total = sum(
        counters.get("agents", {}).get(tag, {}).get("update_count", 0)
        for tag in AGENTS
    )
    counters["last_sync_count"] = total
    counters["last_sync_time"] = datetime.now(timezone.utc).isoformat()
    save_counters(counters)

    REPO_MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REPO_MEMORY_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(sections))

    print(f"  ✅ Repo memory → /memories/repo/workspace-state.md")


def sync_agent(counters: dict, agent_tag: str, force: bool = False):
    """Full sync for one agent: main progress + local memory + repo memory."""
    agent = AGENTS[agent_tag]
    print(f"\n🔄 Syncing {agent['name']} ({agent_tag})...")

    if force or should_sync_agent(counters, agent_tag):
        sync_agent_to_main_progress(agent_tag)
        sync_agent_memory(agent_tag)
        append_to_persistent_memory(agent_tag)

        agents_state = counters.setdefault("agents", {})
        agent_state = agents_state.get(agent_tag, {})
        agent_state["last_sync_count"] = agent_state.get("update_count", 0)
        agent_state["last_sync_time"] = datetime.now(timezone.utc).isoformat()
        agents_state[agent_tag] = agent_state
        save_counters(counters)

        return True
    else:
        agents_state = counters.get("agents", {})
        agent_state = agents_state.get(agent_tag, {})
        total = agent_state.get("update_count", 0)
        last_sync = agent_state.get("last_sync_count", 0)
        remaining = SYNC_THRESHOLD - (total - last_sync)
        print(f"  ⏳ {agent['name']}: {remaining} more update(s) before sync.")
        return False


# ── CLI ──────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Progress File → Memory Auto-Sync v2")
    parser.add_argument("--force", action="store_true", help="Force sync regardless of count")
    parser.add_argument("--reset", action="store_true", help="Reset all counters")
    parser.add_argument("--status", action="store_true", help="Show current counts and last sync")
    parser.add_argument("--agent", choices=["CC", "OC", "HR"], help="Sync specific agent only")
    args = parser.parse_args()

    counters = load_counters()

    if args.reset:
        counters = {
            "agents": {},
            "files": {},
            "total_updates": 0,
            "last_sync_count": 0,
            "last_sync_time": None,
        }
        save_counters(counters)
        print("🔄 Counters reset.")
        return

    if args.status:
        print(f"📊 Progress Sync Status (v2)")
        print(f"   Sync threshold: {SYNC_THRESHOLD} updates per agent")
        print(f"   Last global sync: {counters.get('last_sync_time', 'never')}")
        print()

        for tag, agent in AGENTS.items():
            agents_state = counters.get("agents", {})
            agent_state = agents_state.get(tag, {})
            count = agent_state.get("update_count", 0)
            last_sync = agent_state.get("last_sync_count", 0)
            last_changed = agent_state.get("last_changed", "never")
            progress_exists = (LAB_ROOT / agent["progress_file"]).exists()
            memory_exists = (LAB_ROOT / agent["memory_file"]).exists()
            remaining = max(0, SYNC_THRESHOLD - (count - last_sync))

            print(f"   {agent['emoji']} {agent['name']} ({tag})")
            print(f"      Updates: {count} | Last sync: {last_sync} | Next in: {remaining}")
            print(f"      Progress: {'✅' if progress_exists else '❌'} | Memory: {'✅' if memory_exists else '❌'}")
            print(f"      Last changed: {last_changed}")
            print()

        print(f"   Legacy files:")
        for fname in LEGACY_FILES:
            fstate = counters.get("files", {}).get(fname, {})
            count = fstate.get("update_count", 0)
            exists = (LAB_ROOT / fname).exists()
            print(f"      {fname}: {count} updates [{'exists' if exists else 'MISSING'}]")
        return

    # Determine which agents to sync
    if args.agent:
        agent_tags = [args.agent]
    else:
        agent_tags = list(AGENTS.keys())

    # Scan for updates first
    print("🔍 Scanning for updates...")
    for tag in agent_tags:
        changed = scan_agent_updates(counters, tag)
        agent = AGENTS[tag]
        if changed:
            print(f"  📝 {agent['name']}: change detected")
        else:
            agents_state = counters.get("agents", {})
            count = agents_state.get(tag, {}).get("update_count", 0)
            print(f"  ➖ {agent['name']}: no changes (total: {count})")

    legacy_changes = scan_legacy_updates(counters)
    for fname, changed in legacy_changes.items():
        if changed:
            print(f"  📝 {fname}: change detected")

    save_counters(counters)

    # Run syncs
    any_synced = False
    for tag in agent_tags:
        if sync_agent(counters, tag, force=args.force):
            any_synced = True

    if any_synced or args.force:
        print("\n🔄 Syncing repo memory...")
        sync_repo_memory(counters)

    print("\n✅ Sync complete.")


if __name__ == "__main__":
    main()
