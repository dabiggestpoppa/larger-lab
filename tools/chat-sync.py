#!/usr/bin/env python3
"""
Team Chat → Agent Memory Auto-Sync
====================================
Watches team-chat.md for new messages. Every N new messages:
  1. Extracts context updates (new tasks, decisions, status changes)
  2. Distributes relevant updates to each agent's working memory file
  3. Posts a sync notification to team-chat.md
  4. Updates the chat-sync counter file

This ensures every agent automatically gets context updates from team chat
without having to manually read the full chat history.

Usage:
  python tools/chat-sync.py            # Check for new messages, sync if threshold met
  python tools/chat-sync.py --force    # Force sync regardless of count
  python tools/chat-sync.py --status   # Show current counts and last sync
  python tools/chat-sync.py --reset    # Reset all counters
  python tools/chat-sync.py --dry-run  # Show what would sync without writing
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
TEAM_CHAT_FILE = LAB_ROOT / "shared-conversations" / "team-chat.md"
COUNTER_FILE = LAB_ROOT / ".chat-sync-counters.json"
SYNC_THRESHOLD = 5  # Sync every 5 new messages

# Agent registry — maps agent tags to their memory files and chat identifiers
AGENTS = {
    "CC": {
        "tag": "CC",
        "name": "Claude Code",
        "emoji": "[CC]",
        "memory_file": "progress/claude-code-memory.md",
        "chat_identifiers": ["[CC]", "CC:", "@CC", "CC —"],
    },
    "OC": {
        "tag": "OC",
        "name": "OpenClaw",
        "emoji": "[OC]",
        "memory_file": "progress/openclaw-memory.md",
        "chat_identifiers": ["[OC]", "OC:", "@OC"],
    },
    "OC2": {
        "tag": "OC2",
        "name": "OpenClaw 2",
        "emoji": "[OC2]",
        "memory_file": "progress/openclaw-2-memory.md",
        "chat_identifiers": ["[OC2]", "OC2:", "@OC2"],
    },
    "AS": {
        "tag": "AS",
        "name": "Assistant Manager",
        "emoji": "[AS]",
        "memory_file": "progress/assistant-memory.md",
        "chat_identifiers": ["[AS]", "AS:", "@AS"],
    },
    "PM": {
        "tag": "PM",
        "name": "Polymorph",
        "emoji": "[PM]",
        "memory_file": "progress/polymorph-memory.md",
        "chat_identifiers": ["[PM]", "PM:", "@PM", "Polymorph"],
    },
    "RL": {
        "tag": "RL",
        "name": "OWL",
        "emoji": "[RL]",
        "memory_file": "progress/rl-memory.md",
        "chat_identifiers": ["[RL]", "RL:", "@RL", "OWL", "[OWL]"],
    },
}

# ── Counter Management ───────────────────────────────────────────────────────


def load_counters() -> dict:
    """Load chat sync counters from disk."""
    if COUNTER_FILE.exists():
        try:
            with open(COUNTER_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {
        "last_line_count": 0,
        "last_sync_line": 0,
        "total_messages_synced": 0,
        "last_sync_time": None,
        "sync_history": [],
    }


def save_counters(counters: dict):
    """Persist chat sync counters to disk."""
    with open(COUNTER_FILE, "w") as f:
        json.dump(counters, f, indent=2)


# ── Chat Parsing ─────────────────────────────────────────────────────────────


def parse_chat_messages(content: str) -> list:
    """
    Parse team-chat.md into individual messages.
    Each message starts with '### [TAG]' or '## [TAG]' header.
    Returns list of dicts: {header, tag, content, line_start}
    """
    messages = []
    current = None
    lines = content.split("\n")

    for i, line in enumerate(lines):
        # Match message headers: ### [TAG] name — date — subject
        # Also match: ## [TAG] name — date — subject
        header_match = re.match(r"^#{3,4}\s+\[(\w+)\]\s+(.+?)(?:\s+[—\-]\s+(.+))?$", line)
        if header_match:
            if current:
                messages.append(current)
            tag = header_match.group(1)
            name = header_match.group(2).strip()
            subject = header_match.group(3).strip() if header_match.group(3) else ""
            current = {
                "header": line,
                "tag": tag,
                "name": name,
                "subject": subject,
                "content": [],
                "line_start": i + 1,
            }
        elif current:
            current["content"].append(line)

    if current:
        messages.append(current)

    return messages


def extract_new_messages(content: str, last_line: int) -> list:
    """Extract messages that appeared after the last sync line."""
    all_messages = parse_chat_messages(content)
    new_messages = [m for m in all_messages if m["line_start"] > last_line]
    return new_messages


def classify_message_relevance(message: dict) -> dict:
    """
    Determine which agents a message is relevant to.
    Returns dict: {agent_tag: relevance_score}
    Scoring:
      +3: Directly addressed to agent (@AGENT or [AGENT] at start)
      +2: Mentions agent name/role in content
      +1: General team update (relevant to all)
    """
    relevance = {}
    header_lower = message["header"].lower()
    content_text = "\n".join(message["content"]).lower()
    full_text = header_lower + " " + content_text

    for tag, agent in AGENTS.items():
        score = 0

        # Check if directly addressed (header tag matches)
        if message["tag"] == tag:
            score += 3

        # Check chat identifiers in content
        for identifier in agent["chat_identifiers"]:
            if identifier.lower() in full_text:
                score += 2
                break

        # Check for role-based mentions
        role_keywords = {
            "CC": ["overseer", "architecture", "core build", "phase gate", "fastapi", "backend"],
            "OC": ["analysis", "planning", "coordination", "event fabric", "event types"],
            "OC2": ["frontend", "next.js", "ui", "shell", "testing", "discord"],
            "AS": ["quality", "documentation", "resource assessment", "review"],
            "PM": ["debug", "tool", "skill", "operator", "performance"],
            "RL": ["research", "dspy", "pipeline", "entropy", "integration"],
        }
        keywords = role_keywords.get(tag, [])
        for kw in keywords:
            if kw in full_text:
                score += 1
                break

        # General team updates get +1 for everyone
        if any(kw in full_text for kw in ["@oc", "@oc2", "@as", "@pm", "@rl", "@cc", "team", "everyone", "all agents"]):
            score = max(score, 1)

        if score > 0:
            relevance[tag] = score

    return relevance


def extract_key_updates(messages: list) -> dict:
    """
    Extract key updates from messages: tasks, decisions, status changes.
    Returns dict: {agent_tag: [update_strings]}

    Only extracts high-signal items:
    - Direct task assignments ("**TASK:**", "**ACTION:**", "**→**")
    - Decisions ("**Decision:**", "**Verdict:**")
    - Status changes ("**Status:**", "✅ Complete", "🔄 In Progress")
    - Phase transitions ("Phase X Complete", "Phase Y Kickoff")
    - Max 5 updates per agent per message to avoid noise
    """
    updates = {tag: [] for tag in AGENTS}

    for msg in messages:
        relevance = classify_message_relevance(msg)
        subject = msg.get("subject", "")

        for tag, score in relevance.items():
            update_parts = []

            # For highly relevant messages (directly addressed), extract key items
            if score >= 3:
                # Add subject as context
                if subject:
                    update_parts.append(f"**{subject}**")

                # Scan content for high-signal lines only
                for line in msg["content"]:
                    line_stripped = line.strip()
                    if not line_stripped or line_stripped.startswith("---"):
                        continue

                    # Task/action markers
                    if any(m in line_stripped for m in ["**TASK:**", "**ACTION:**", "**→**", "**First Action**"]):
                        clean = line_stripped.lstrip("#-*•").strip()
                        if len(clean) > 5:
                            update_parts.append(clean[:120])

                    # Decision markers
                    elif any(m in line_stripped for m in ["**Decision:**", "**Verdict:**", "**→**"]):
                        clean = line_stripped.lstrip("#-*•").strip()
                        if len(clean) > 5:
                            update_parts.append(clean[:120])

                    # Phase transitions
                    elif any(m in line_stripped for m in ["Phase", "✅", "🔄", "Complete", "Kickoff"]):
                        clean = line_stripped.lstrip("#-*•").strip()
                        if len(clean) > 10 and len(clean) < 150:
                            update_parts.append(clean[:120])

                # If no specific items found, add first meaningful line as summary
                if not update_parts:
                    for line in msg["content"]:
                        clean = line.strip().lstrip("#-*•").strip()
                        if clean and len(clean) > 15 and not clean.startswith("---") and not clean.startswith("@"):
                            update_parts.append(f"**{clean[:100]}**")
                            break

            # For moderately relevant messages (mentioned in content), only add subject
            elif score >= 2 and subject:
                update_parts.append(f"**{subject}**")

            # For general updates (score 1), only add phase transitions — not every bullet
            elif score >= 1:
                for line in msg["content"]:
                    line_stripped = line.strip()
                    # Only catch explicit phase transitions, not every line with "Phase"
                    if any(m in line_stripped for m in ["Kickoff:", "Status Update:", "Complete.", "In Progress."]):
                        clean = line_stripped.lstrip("#-*•").strip()
                        if len(clean) > 10 and len(clean) < 150:
                            update_parts.append(clean[:120])
                            break

            # Deduplicate and limit
            if update_parts:
                seen = set()
                unique = []
                for u in update_parts:
                    normalized = re.sub(r'\*+', '', u).strip().lower()[:60]
                    if normalized not in seen:
                        seen.add(normalized)
                        unique.append(u)
                updates[tag].extend(unique[:5])  # Max 5 per message per agent

    return updates


# ── Memory File Updates ──────────────────────────────────────────────────────


def update_agent_memory(agent_tag: str, new_updates: list, messages_count: int):
    """
    Update an agent's working memory file with new context from chat.
    Appends a '## Chat Context Update' section.
    """
    agent = AGENTS[agent_tag]
    memory_path = LAB_ROOT / agent["memory_file"]

    if not memory_path.exists():
        # Create minimal memory file
        memory_content = f"# {agent['emoji']} {agent['name']} — Working Memory\n\n"
    else:
        with open(memory_path, "r", encoding="utf-8") as f:
            memory_content = f.read()

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Build the chat context update section
    update_lines = [
        f"",
        f"## Chat Context Update ({now})",
        f"> **Source:** Auto-synced from team-chat.md ({messages_count} new messages)",
        f"> **Sync Threshold:** Every {SYNC_THRESHOLD} messages",
        f"",
    ]

    # Deduplicate and limit updates
    seen = set()
    unique_updates = []
    for u in new_updates:
        # Normalize for dedup
        normalized = re.sub(r'\*+', '', u).strip().lower()[:80]
        if normalized not in seen and len(normalized) > 5:
            seen.add(normalized)
            unique_updates.append(u)

    if unique_updates:
        for u in unique_updates[:15]:  # Max 15 updates per sync
            update_lines.append(f"- {u}")
    else:
        update_lines.append(f"- No new task-relevant updates this cycle.")

    update_lines.append("")
    update_lines.append("---")
    update_lines.append("")

    update_text = "\n".join(update_lines)

    # Check if there's already a Chat Context Update section
    chat_section_pattern = r"## Chat Context Update.*?(?=\n## |\Z)"
    if re.search(chat_section_pattern, memory_content, re.DOTALL):
        # Replace existing section
        memory_content = re.sub(chat_section_pattern, update_text.strip(), memory_content, flags=re.DOTALL)
    else:
        # Append before the Sync Metadata section, or at end
        sync_meta_pattern = r"(## Sync Metadata)"
        if re.search(sync_meta_pattern, memory_content):
            memory_content = re.sub(sync_meta_pattern, update_text + "\n" + r"\1", memory_content)
        else:
            memory_content = memory_content.rstrip() + "\n" + update_text

    # Write back
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    with open(memory_path, "w", encoding="utf-8") as f:
        f.write(memory_content)

    print(f"  ✅ {agent['name']} memory updated ({len(unique_updates)} updates)")


def post_sync_notification(counters: dict, messages_count: int, agents_updated: list):
    """Post a sync notification to team-chat.md."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    notification = f"""
---

### [SYNC] {now} — Chat Context Auto-Sync

📬 **{messages_count} new messages** processed from team-chat.md.
🔄 **Agents updated:** {', '.join(agents_updated) if agents_updated else 'None (no task-relevant updates)'}
📊 **Total synced:** {counters['total_messages_synced']} messages since tracking began.
⚙️ **Sync threshold:** Every {SYNC_THRESHOLD} new messages.

> This is an automatic context sync. Each agent's working memory file has been updated
> with relevant tasks, decisions, and status changes from team chat.
> Agents: check your `progress/*-memory.md` for the latest context.

---
"""

    with open(TEAM_CHAT_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Check if there's already a recent sync notification and remove old ones
    content = re.sub(
        r"\n---\n\n### \[SYNC\].*?\n---\n",
        "\n",
        content,
        flags=re.DOTALL,
    )

    content = content.rstrip("\n") + "\n" + notification

    with open(TEAM_CHAT_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  ✅ Sync notification posted to team-chat.md")


# ── Main Sync Logic ──────────────────────────────────────────────────────────


def run_sync(force: bool = False, dry_run: bool = False):
    """Main sync logic: check for new messages and update agent memories."""
    counters = load_counters()

    if not TEAM_CHAT_FILE.exists():
        print("❌ team-chat.md not found!")
        return

    with open(TEAM_CHAT_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    total_lines = len(content.split("\n"))
    last_sync_line = counters.get("last_sync_line", 0)

    # Extract new messages
    new_messages = extract_new_messages(content, last_sync_line)

    if not new_messages and not force:
        print(f"📬 No new messages since last sync (line {last_sync_line}).")
        print(f"   Total chat lines: {total_lines}")
        return

    if not new_messages and force:
        # Force sync: re-process last N messages
        all_messages = parse_chat_messages(content)
        new_messages = all_messages[-SYNC_THRESHOLD:] if len(all_messages) > SYNC_THRESHOLD else all_messages
        print(f"🔄 Force sync: processing last {len(new_messages)} messages.")

    print(f"📬 {len(new_messages)} new message(s) found (lines {last_sync_line+1}-{total_lines}).")

    if dry_run:
        print("\n🔍 DRY RUN — no files will be written.\n")
        for msg in new_messages:
            relevance = classify_message_relevance(msg)
            print(f"  Line {msg['line_start']}: {msg['header'][:80]}")
            print(f"    Relevance: {relevance}")
        return

    # Extract key updates per agent
    updates = extract_key_updates(new_messages)

    # Update each agent's memory
    agents_updated = []
    for tag, agent_updates in updates.items():
        if agent_updates:
            update_agent_memory(tag, agent_updates, len(new_messages))
            agents_updated.append(AGENTS[tag]["name"])

    # Update counters
    counters["last_line_count"] = total_lines
    counters["last_sync_line"] = total_lines
    counters["total_messages_synced"] += len(new_messages)
    counters["last_sync_time"] = datetime.now(timezone.utc).isoformat()
    counters["sync_history"].append({
        "time": datetime.now(timezone.utc).isoformat(),
        "messages_processed": len(new_messages),
        "agents_updated": agents_updated,
        "line_range": f"{last_sync_line+1}-{total_lines}",
    })
    # Keep only last 50 sync records
    counters["sync_history"] = counters["sync_history"][-50:]

    save_counters(counters)

    # Post sync notification to team-chat
    post_sync_notification(counters, len(new_messages), agents_updated)

    print(f"\n✅ Sync complete. {len(new_messages)} messages → {len(agents_updated)} agents updated.")


# ── CLI ──────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Team Chat → Agent Memory Auto-Sync")
    parser.add_argument("--force", action="store_true", help="Force sync regardless of count")
    parser.add_argument("--reset", action="store_true", help="Reset all counters")
    parser.add_argument("--status", action="store_true", help="Show current counts and last sync")
    parser.add_argument("--dry-run", action="store_true", help="Show what would sync without writing")
    args = parser.parse_args()

    if args.reset:
        counters = {
            "last_line_count": 0,
            "last_sync_line": 0,
            "total_messages_synced": 0,
            "last_sync_time": None,
            "sync_history": [],
        }
        save_counters(counters)
        print("🔄 Chat sync counters reset.")
        return

    if args.status:
        counters = load_counters()
        print(f"📊 Chat Sync Status")
        print(f"   Last sync line: {counters.get('last_sync_line', 0)}")
        print(f"   Total messages synced: {counters.get('total_messages_synced', 0)}")
        print(f"   Last sync time: {counters.get('last_sync_time', 'Never')}")
        print(f"   Sync threshold: {SYNC_THRESHOLD} messages")
        print(f"   Sync history entries: {len(counters.get('sync_history', []))}")
        if counters.get("sync_history"):
            last = counters["sync_history"][-1]
            print(f"   Last sync: {last['time']} ({last['messages_processed']} messages, agents: {', '.join(last['agents_updated']) or 'none'})")
        return

    run_sync(force=args.force, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
