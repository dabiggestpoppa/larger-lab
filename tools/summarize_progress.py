#!/usr/bin/env python3
"""
Progress File Summarizer — Standalone Tool
===========================================
Summarizes agent progress files using LLM (Nemotron 3 Nano Omni via OpenRouter).
Can be called independently or by the memory sync daemon.

Usage:
  python tools/summarize_progress.py --agent PM
  python tools/summarize_progress.py --all
  python tools/summarize_progress.py --agent PM --dry-run
  python tools/summarize_progress.py --agent PM --keep 10
"""

import argparse
import json
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

LAB_ROOT = Path(__file__).resolve().parent.parent

OPENROUTER_API_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
SUMMARIZE_MODEL = "nvidia/nemotron-3-nano-omni-30b-a3b:free"

AGENTS = {
    "CC": {"tag": "CC", "name": "Claude Code", "emoji": "🔵", "progress_file": "progress/claude-code-progress.md"},
    "OC": {"tag": "OC", "name": "OpenClaw", "emoji": "🟣", "progress_file": "progress/openclaw-progress.md"},
    "OC2": {"tag": "OC2", "name": "OpenClaw 2", "emoji": "🟠", "progress_file": "progress/openclaw-2-progress.md"},
    "PM": {"tag": "PM", "name": "Polymorph", "emoji": "🔴", "progress_file": "progress/polymorph-progress.md"},
    "AS": {"tag": "AS", "name": "Assistant Manager", "emoji": "🟡", "progress_file": "progress/assistant-progress.md"},
    "RL": {"tag": "RL", "name": "OWL", "emoji": "🦉", "progress_file": "progress/rl-progress.md"},
}


def count_entries(filepath: Path) -> int:
    if not filepath.exists():
        return 0
    return filepath.read_text(encoding="utf-8").count("#### ")


def extract_entries(filepath: Path) -> tuple:
    """Return (header_lines, entry_blocks) from a progress file."""
    if not filepath.exists():
        return [], []

    lines = filepath.read_text(encoding="utf-8").split("\n")
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

    return header_lines, entry_blocks


def summarize_via_llm(entries_text: str, agent_name: str) -> str:
    """Call OpenRouter API to summarize entries."""
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


def summarize_agent(agent_tag: str, keep: int = 5, dry_run: bool = False) -> dict:
    """Summarize a single agent's progress file."""
    agent = AGENTS[agent_tag]
    filepath = LAB_ROOT / agent["progress_file"]

    if not filepath.exists():
        return {"agent": agent["name"], "status": "not_found"}

    header_lines, entry_blocks = extract_entries(filepath)
    total = len(entry_blocks)

    if total <= keep:
        return {"agent": agent["name"], "status": "skipped", "entries": total, "reason": f"≤{keep} entries"}

    to_summarize = entry_blocks[:-keep]
    keep_blocks = entry_blocks[-keep:]
    entries_text = "\n\n".join(to_summarize)

    if dry_run:
        return {
            "agent": agent["name"],
            "status": "dry_run",
            "total_entries": total,
            "would_summarize": len(to_summarize),
            "would_keep": keep,
        }

    # Summarize
    summary = summarize_via_llm(entries_text, agent["name"])
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    summary_block = (
        f"#### 📦 SUMMARIZED BLOCK — {now}\n"
        f"*({len(to_summarize)} older entries compressed via LLM)*\n\n"
        f"{summary}\n"
    )

    # Reconstruct
    header_text = "\n".join(header_lines)
    new_content = header_text + "\n\n" + summary_block + "\n" + "\n\n".join(keep_blocks) + "\n"
    filepath.write_text(new_content, encoding="utf-8")

    new_count = count_entries(filepath)
    return {
        "agent": agent["name"],
        "status": "summarized",
        "before": total,
        "after": new_count,
        "compressed": len(to_summarize),
    }


def main():
    parser = argparse.ArgumentParser(description="Progress File Summarizer")
    parser.add_argument("--agent", choices=list(AGENTS.keys()), help="Specific agent to summarize")
    parser.add_argument("--all", action="store_true", help="Summarize all agents")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without changes")
    parser.add_argument("--keep", type=int, default=5, help="Number of newest entries to keep (default: 5)")
    args = parser.parse_args()

    if not args.agent and not args.all:
        parser.print_help()
        return

    tags = list(AGENTS.keys()) if args.all else [args.agent]

    print(f"📝 Progress File Summarizer")
    print(f"   Model: {SUMMARIZE_MODEL}")
    print(f"   Keep: {args.keep} newest entries")
    if args.dry_run:
        print(f"   Mode: DRY RUN (no changes)")
    print()

    results = []
    for tag in tags:
        result = summarize_agent(tag, keep=args.keep, dry_run=args.dry_run)
        results.append(result)

        status = result["status"]
        if status == "summarized":
            print(f"  ✅ {result['agent']}: {result['before']} → {result['after']} entries ({result['compressed']} compressed)")
        elif status == "dry_run":
            print(f"  🔍 {result['agent']}: would compress {result['would_summarize']} of {result['total_entries']} entries")
        elif status == "skipped":
            print(f"  ⏭ {result['agent']}: skipped ({result['reason']})")
        elif status == "not_found":
            print(f"  ❌ {result['agent']}: progress file not found")

    print(f"\n✅ Done. {len(results)} agent(s) processed.")


if __name__ == "__main__":
    main()
