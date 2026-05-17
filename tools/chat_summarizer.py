#!/usr/bin/env python3
"""
Team Chat Summarizer
====================
Condenses team-chat.md when it grows beyond a threshold (default: 100 messages).

Strategy:
- Count top-level message entries (## / ### headers with agent tags)
- Keep last N messages intact (default: 30 recent)
- Summarize older messages into compact "epoch" blocks by date
- Preserve: MAD directives, phase kickoffs, critical alerts, current goals
- Archive: duplicate status checks, resolved issues, verbose sub-agent reports

Usage:
  python chat_summarizer.py                    # Auto-summarize if >100 messages
  python chat_summarizer.py --threshold 80     # Custom threshold
  python chat_summarizer.py --keep 40          # Keep last N messages intact
  python chat_summarizer.py --dry-run          # Show what would change
  python chat_summarizer.py --force            # Summarize even if under threshold
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path

CHAT_FILE = Path(__file__).parent.parent / "shared-conversations" / "team-chat.md"
ARCHIVE_DIR = Path(__file__).parent.parent / "shared-conversations" / "chat-archive"

# Patterns that indicate high-priority messages to always preserve
PRIORITY_PATTERNS = [
    r"MAD DIRECTIVE",
    r"PHASE \d+",
    r"KICKOFF",
    r"CRITICAL",
    r"ALERT",
    r"ALL SYSTEMS",
    r"FINAL STATUS",
    r"HANDOFF",
    r"Complete.*\d+/\d+",
    r"tests? passing",
    r"OCE-\d+\.\d+",
]

# Patterns that indicate low-priority / verbose messages to summarize
LOW_PRIORITY_PATTERNS = [
    r"STATUS CHECK",
    r"Maintenance",
    r"Watchdog",
    r"Sub-agent",
    r"Spawned",
    r"Running",
    r"Installed",
]


def count_messages(content: str) -> int:
    """Count top-level message entries (## headers with agent tags)."""
    return len(re.findall(r'^## [🟣🟠🟡🔴🔵🦉]', content, re.MULTILINE))


def extract_messages(content: str) -> list[dict]:
    """Split content into individual message blocks."""
    # Split on ## headers (top-level messages)
    parts = re.split(r'^(?=## )', content, flags=re.MULTILINE)
    messages = []
    for part in parts:
        if not part.strip():
            continue
        # Extract header
        header_match = re.match(r'^(## .+?)$', part, re.MULTILINE)
        if header_match:
            header = header_match.group(1)
            # Extract date
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', header)
            date = date_match.group(1) if date_match else "unknown"
            # Extract agent
            agent_match = re.search(r'\[(\w+)\]', header)
            agent = agent_match.group(1) if agent_match else "unknown"
            # Check priority
            is_priority = any(re.search(p, header) for p in PRIORITY_PATTERNS)
            is_low = any(re.search(p, header) for p in LOW_PRIORITY_PATTERNS)
            messages.append({
                "header": header,
                "content": part,
                "date": date,
                "agent": agent,
                "is_priority": is_priority,
                "is_low": is_low,
                "lines": part.count('\n'),
            })
    return messages


def summarize_message(msg: dict) -> str:
    """Create a 1-2 line summary of a message."""
    header = msg["header"]
    content = msg["content"]

    # Extract key info
    lines = content.strip().split('\n')
    key_lines = []
    for line in lines[1:10]:  # Skip header, check first 10 lines
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('---'):
            # Keep lines with key info
            if any(kw in line.lower() for kw in ['complete', '✅', '❌', 'status', 'passing',
                                                    'failed', 'blocked', 'unblocked', 'file:',
                                                    'endpoint', 'test', 'port', 'pid']):
                key_lines.append(line[:120])

    summary = header
    if key_lines:
        summary += '\n' + '\n'.join(key_lines[:3])  # Max 3 key lines
    summary += '\n'
    return summary


def group_by_date(messages: list[dict]) -> dict:
    """Group messages by date."""
    groups = {}
    for msg in messages:
        date = msg["date"]
        if date not in groups:
            groups[date] = []
        groups[date].append(msg)
    return groups


def build_summary(old_messages: list[dict], keep_count: int) -> str:
    """Build condensed summary of old messages."""
    if not old_messages:
        return ""

    groups = group_by_date(old_messages)
    lines = []
    lines.append("---")
    lines.append("")
    lines.append("## 📋 Chat History Summary (Condensed)")
    lines.append("")
    lines.append(f"> {len(old_messages)} older messages condensed. Full history in `shared-conversations/chat-archive/`.")
    lines.append("")

    for date in sorted(groups.keys()):
        msgs = groups[date]
        lines.append(f"### {date}")
        lines.append("")

        # Separate priority from regular
        priorities = [m for m in msgs if m["is_priority"]]
        regular = [m for m in msgs if not m["is_priority"]]

        # Keep priority messages more detailed
        for msg in priorities:
            lines.append(summarize_message(msg))

        # Group regular messages by agent
        if regular:
            by_agent = {}
            for m in regular:
                agent = m["agent"]
                if agent not in by_agent:
                    by_agent[agent] = []
                by_agent[agent].append(m)

            for agent, agent_msgs in by_agent.items():
                if len(agent_msgs) == 1:
                    lines.append(summarize_message(agent_msgs[0]))
                else:
                    # Multiple messages from same agent — condense
                    lines.append(f"**[{agent}]** — {len(agent_msgs)} updates:")
                    for m in agent_msgs:
                        # Extract the core action from header
                        header_text = m["header"].replace('## ', '').replace('### ', '')
                        # Get first meaningful line after header
                        body_lines = [l.strip() for l in m["content"].split('\n')[1:5]
                                      if l.strip() and not l.startswith('#') and not l.startswith('---')]
                        first_line = body_lines[0][:100] if body_lines else ""
                        lines.append(f"  • {header_text}: {first_line}")
                    lines.append("")

    return '\n'.join(lines)


def archive_full_chat(content: str):
    """Save full chat to archive before condensing."""
    ARCHIVE_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_file = ARCHIVE_DIR / f"team-chat-full-{timestamp}.md"
    archive_file.write_text(content, encoding='utf-8')
    return archive_file


def summarize_chat(threshold: int = 100, keep: int = 30, dry_run: bool = False, force: bool = False) -> dict:
    """Main summarization logic. Returns stats."""
    content = CHAT_FILE.read_text(encoding='utf-8')

    # Extract header (everything before first ## message)
    header_match = re.match(r'^(.*?)(?=\n## )', content, re.DOTALL)
    file_header = header_match.group(1) if header_match else content[:200]

    messages = extract_messages(content)
    msg_count = len(messages)

    stats = {
        "total_messages": msg_count,
        "threshold": threshold,
        "keep": keep,
        "summarized": 0,
        "preserved": 0,
        "archived": False,
    }

    if msg_count <= threshold and not force:
        stats["action"] = "skipped (under threshold)"
        return stats

    # Split into old (to summarize) and recent (to keep)
    old_messages = messages[:-keep] if msg_count > keep else []
    recent_messages = messages[-keep:] if msg_count > keep else messages

    stats["summarized"] = len(old_messages)
    stats["preserved"] = len(recent_messages)

    if dry_run:
        stats["action"] = "dry_run"
        return stats

    # Archive full chat
    archive_path = archive_full_chat(content)
    stats["archived"] = True
    stats["archive_path"] = str(archive_path)

    # Build new content
    summary_block = build_summary(old_messages, keep)
    recent_content = '\n---\n'.join(m["content"] for m in recent_messages)

    # Update header timestamp
    now = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    new_header = re.sub(r'\*\*Last Cleaned:\*\* .+', f'**Last Cleaned:** {now}', file_header)
    if '**Last Cleaned:**' not in new_header:
        new_header = new_header.rstrip() + f'\n> **Last Cleaned:** {now}'

    new_content = f"{new_header}\n\n{summary_block}\n\n{recent_content}"

    CHAT_FILE.write_text(new_content, encoding='utf-8')
    stats["action"] = "summarized"
    return stats


def main():
    parser = argparse.ArgumentParser(description="Team Chat Summarizer")
    parser.add_argument("--threshold", type=int, default=100,
                        help="Message count threshold to trigger summarization (default: 100)")
    parser.add_argument("--keep", type=int, default=30,
                        help="Number of recent messages to keep intact (default: 30)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would change without modifying the file")
    parser.add_argument("--force", action="store_true",
                        help="Summarize even if under threshold")
    parser.add_argument("--count", action="store_true",
                        help="Just count messages and exit")
    args = parser.parse_args()

    content = CHAT_FILE.read_text(encoding='utf-8')
    messages = extract_messages(content)

    if args.count:
        print(f"Team chat: {len(messages)} messages")
        # Show date distribution
        groups = group_by_date(messages)
        for date in sorted(groups.keys()):
            print(f"  {date}: {len(groups[date])} messages")
        return

    stats = summarize_chat(
        threshold=args.threshold,
        keep=args.keep,
        dry_run=args.dry_run,
        force=args.force,
    )

    print(f"Team chat summarizer:")
    print(f"  Total messages: {stats['total_messages']}")
    print(f"  Threshold: {stats['threshold']}")
    print(f"  Action: {stats['action']}")

    if stats['action'] in ('summarized', 'dry_run'):
        print(f"  Summarized: {stats['summarized']} messages")
        print(f"  Preserved: {stats['preserved']} recent messages")

    if stats.get('archived'):
        print(f"  Archived to: {stats['archive_path']}")


if __name__ == "__main__":
    main()
