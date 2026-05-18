"""
🦉 RL — Team Chat Monitor
Polls team-chat.md for CC entries and triggers RL action.
Runs as a persistent background process.
"""

import hashlib
import os
import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
TEAM_CHAT = WORKSPACE / "shared-conversations" / "team-chat.md"
LOG_FILE = WORKSPACE / "progress" / "rl-monitor.log"
CC_PROGRESS = WORKSPACE / "progress" / "claude-code-progress.md"

def log(msg: str):
    ts = time.strftime("%H:%M:%S")
    line = f"{ts} [RL-MONITOR] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def get_hash(path: Path) -> str:
    if not path.exists():
        return ""
    return hashlib.md5(path.read_bytes()).hexdigest()

def check_chat():
    """Check team-chat for new CC entries."""
    if not TEAM_CHAT.exists():
        return None
    content = TEAM_CHAT.read_text(encoding="utf-8", errors="replace")
    # Look for CC entries
    lines = content.split("\n")
    cc_entries = []
    for i, line in enumerate(lines):
        if line.startswith("## 🔵 [CC]") or line.startswith("### 🔵 [CC]"):
            # Extract the full entry
            entry_lines = [line]
            for j in range(i + 1, min(i + 30, len(lines))):
                if lines[j].startswith("## ") or lines[j].startswith("### "):
                    break
                entry_lines.append(lines[j])
            cc_entries.append("\n".join(entry_lines))
    return cc_entries

def main():
    log("Monitor started")
    last_chat_hash = get_hash(TEAM_CHAT)
    last_cc_hash = get_hash(CC_PROGRESS)
    poll_count = 0

    while True:
        poll_count += 1
        time.sleep(90)  # Poll every 90 seconds

        try:
            cur_chat_hash = get_hash(TEAM_CHAT)
            cur_cc_hash = get_hash(CC_PROGRESS)

            if cur_chat_hash != last_chat_hash:
                log(f"CHAT CHANGED (poll #{poll_count})")
                last_chat_hash = cur_chat_hash

                # Check for CC entries
                cc_entries = check_chat()
                if cc_entries:
                    log(f"Found {len(cc_entries)} CC entries")
                    for entry in cc_entries:
                        # Log first 200 chars of each CC entry
                        preview = entry[:200].replace("\n", " ")
                        log(f"CC: {preview}...")
                else:
                    log("No CC entries found in chat")

            if cur_cc_hash != last_cc_hash:
                log(f"CC PROGRESS CHANGED (poll #{poll_count})")
                last_cc_hash = cur_cc_hash

            if poll_count % 10 == 0:
                log(f"Still alive — poll #{poll_count}")

        except Exception as e:
            log(f"ERROR: {e}")

if __name__ == "__main__":
    main()
