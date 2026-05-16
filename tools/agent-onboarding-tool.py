#!/usr/bin/env python3
"""
Agent Onboarding Tool
=====================
Creates a complete agent presence in the workspace.

Usage:
  python tools/agent-onboarding-tool.py --name "OWL" --tag "RL" --emoji "🦉" --role "Research Lead"
  python tools/agent-onboarding-tool.py --name "Sentinel" --tag "ST" --emoji "🛡️" --role "Security Monitor" --reports-to CC
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

LAB_ROOT = Path(__file__).resolve().parent.parent
AGENT_TAGS_FILE = LAB_ROOT / ".agent-tags.json"
PROGRESS_SYNC_FILE = LAB_ROOT / "tools" / "progress-sync.py"


def create_identity_file(tag, name, emoji, role, reports_to):
    """Create progress/{TAG}_IDENTITY.md"""
    filepath = LAB_ROOT / "progress" / f"{tag}_IDENTITY.md"
    content = f"""# {tag} IDENTITY — {name}

- **Name:** {name}
- **Tag:** {tag}
- **Emoji:** {emoji}
- **Role:** {role}
- **Reports to:** {reports_to}

## Purpose
{role} agent.

## Signature
{emoji} [{tag}] — All progress entries tagged with this signature
"""
    filepath.write_text(content, encoding="utf-8")
    print(f"  ✅ Identity: {filepath.relative_to(LAB_ROOT)}")
    return filepath


def create_progress_file(tag, name, emoji):
    """Create progress/{tag}-progress.md"""
    filepath = LAB_ROOT / "progress" / f"{tag.lower()}-progress.md"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    content = f"""# {emoji} [{tag}] {name} — Progress

> Auto-synced to PROJECT_PROGRESS_CLEAN.md every 3 updates

---

#### {emoji} [{tag}] {now} — Agent Initialized
- Created identity file at `progress/{tag}_IDENTITY.md`
- Registered in `.agent-tags.json` as {tag}
- Added to `tools/progress-sync.py` AGENTS registry
- Standing by for task assignments
"""
    filepath.write_text(content, encoding="utf-8")
    print(f"  ✅ Progress: {filepath.relative_to(LAB_ROOT)}")
    return filepath


def create_memory_file(tag, name, emoji):
    """Create progress/{tag}-memory.md"""
    filepath = LAB_ROOT / "progress" / f"{tag.lower()}-memory.md"
    content = f"""# {emoji} [{tag}] {name} — Working Memory

> Auto-synced from {tag.lower()}-progress.md every 3 updates

## Key Findings

_(Empty — awaiting first research)_
"""
    filepath.write_text(content, encoding="utf-8")
    print(f"  ✅ Memory: {filepath.relative_to(LAB_ROOT)}")
    return filepath


def create_standby_prompt(tag, name, emoji, role, reports_to):
    """Create shared-conversations/{tag.lower()}-prompt.md"""
    filepath = LAB_ROOT / "shared-conversations" / f"{tag.lower()}-prompt.md"
    content = f"""# {emoji} {name} — Standby Prompt

> **Agent:** {name}
> **Tag:** {emoji} [{tag}]
> **Role:** {role}
> **Reports to:** {reports_to}
> **Sub-progress file:** `progress/{tag.lower()}-progress.md`

## Purpose
You are the {role}. Your job is to:
1. Execute your role responsibilities
2. Check team-chat.md for messages directed at @{tag}
3. Write to your own sub-progress file — never touch another agent's
4. Run progress-sync after completing work
5. Stand by for task assignments

## Key Commands
```bash
python tools/progress-sync.py --agent {tag} --force
python tools/phase-gate.py --status
python -m srrs_opc.tests.test_phase2_e2e  # Run Phase 2 tests
```

## Error Handling
- On rate limit: wait 30s, retry
- On 2nd consecutive rate limit: wait 120s, retry
- On 3rd: wait 300s, then flag to CC via team-chat.md
- Never stall silently — always log what happened

## Current Build Status
- **All Phases 0-7:** ✅ Complete — 38/38 tests passing
- **Phase 8-9:** ⏳ Planned

## What to Do Right Now
1. Read `shared-conversations/team-chat.md` — check for open items
2. Read your sub-progress file for any pending tasks
3. Stand by for task assignments
"""
    filepath.write_text(content, encoding="utf-8")
    print(f"  ✅ Standby prompt: {filepath.relative_to(LAB_ROOT)}")
    return filepath


def register_agent_tags(tag, name, emoji, role):
    """Add agent to .agent-tags.json"""
    with open(AGENT_TAGS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if tag.lower() in data["agents"]:
        print(f"  ⚠️  Agent '{tag}' already in .agent-tags.json — skipping")
        return
    data["agents"][tag.lower()] = {
        "tag": tag,
        "name": name,
        "role": role,
        "color": emoji,
        "progress_prefix": tag,
    }
    with open(AGENT_TAGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  ✅ Registered in .agent-tags.json")


def add_to_progress_sync(tag, name, emoji):
    """Add agent to tools/progress-sync.py AGENTS dict"""
    with open(PROGRESS_SYNC_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    if f'"{tag}":' in content:
        print(f"  ⚠️  Agent '{tag}' already in progress-sync.py — skipping")
        return
    new_entry = f'''    "{tag}": {{
        "tag": "{tag}",
        "name": "{name}",
        "emoji": "{emoji}",
        "progress_file": "progress/{tag.lower()}-progress.md",
        "memory_file": "progress/{tag.lower()}-memory.md",
        "section_header": "{emoji} [{tag}] {name}",
    }},'''
    pattern = r'(    "AS": \{[^}]+\},)'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        insert_pos = match.end()
        content = content[:insert_pos] + "\n" + new_entry + content[insert_pos:]
        with open(PROGRESS_SYNC_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✅ Added to progress-sync.py")
    else:
        print(f"  ⚠️  Could not find insertion point in progress-sync.py — add manually")


def update_memory_md(tag, name, emoji, role):
    """Add entry to MEMORY.md"""
    memory_file = LAB_ROOT / "MEMORY.md"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with open(memory_file, "r", encoding="utf-8") as f:
        content = f.read()
    new_entry = f"""
## {emoji} [{tag}] {name}
- **Role:** {role}
- **Registered:** {now}
- **Identity:** `progress/{tag}_IDENTITY.md`
"""
    content = content.rstrip() + "\n" + new_entry
    with open(memory_file, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ Updated MEMORY.md")


def post_team_chat_intro(tag, name, emoji, role):
    """Post intro message to team-chat.md"""
    team_chat = LAB_ROOT / "shared-conversations" / "team-chat.md"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    with open(team_chat, "r", encoding="utf-8") as f:
        content = f.read()
    intro = f"""
### {emoji} [{tag}] {name} — {now}Z — Agent Onboarded
- Registered in `.agent-tags.json` as {tag}
- Identity: `progress/{tag}_IDENTITY.md`
- Progress: `progress/{tag.lower()}-progress.md`
- Memory: `progress/{tag.lower()}-memory.md`
- Standby prompt: `shared-conversations/{tag.lower()}-prompt.md`
- Added to `tools/progress-sync.py` AGENTS registry
- Standing by for task assignments
"""
    content = content.replace(
        "_(Newest at bottom)_",
        f"_(Newest at bottom)_{intro}"
    )
    with open(team_chat, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✅ Posted intro to team-chat.md")


def main():
    parser = argparse.ArgumentParser(description="Onboard a new agent into the workspace")
    parser.add_argument("--name", required=True, help="Agent name")
    parser.add_argument("--tag", required=True, help="Agent tag (2-3 letters)")
    parser.add_argument("--emoji", required=True, help="Agent emoji")
    parser.add_argument("--role", required=True, help="Agent role description")
    parser.add_argument("--reports-to", default="CC", help="Reports to (default: CC)")
    args = parser.parse_args()

    tag = args.tag.upper()
    print(f"\n🦉 Onboarding agent: {args.emoji} [{tag}] {args.name}")
    print(f"   Role: {args.role}")
    print(f"   Reports to: {args.reports_to}\n")

    create_identity_file(tag, args.name, args.emoji, args.role, args.reports_to)
    create_progress_file(tag, args.name, args.emoji)
    create_memory_file(tag, args.name, args.emoji)
    create_standby_prompt(tag, args.name, args.emoji, args.role, args.reports_to)
    register_agent_tags(tag, args.name, args.emoji, args.role)
    add_to_progress_sync(tag, args.name, args.emoji)
    update_memory_md(tag, args.name, args.emoji, args.role)
    post_team_chat_intro(tag, args.name, args.emoji, args.role)

    print(f"\n✅ Agent {args.emoji} [{tag}] {args.name} onboarded successfully!")


if __name__ == "__main__":
    main()
