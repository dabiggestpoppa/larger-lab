"""
Workspace Progress Sync Agent
Syncs agent progress files -> working memory -> repo memory.
Runs as a daemon or one-shot.

Rules:
- Every 7 progress file updates -> sync to working memory
- Every 20 entries in a progress file -> LLM summarization trigger
- Every 5 team-chat messages -> sync to agent memory
"""

import os
import sys
import time
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

# Configuration
WORKSPACE_ROOT = Path(__file__).parent.parent
PROGRESS_DIR = WORKSPACE_ROOT / "progress"
MEMORY_DIR = WORKSPACE_ROOT / "memory"
TEAM_CHAT = WORKSPACE_ROOT / "shared-conversations" / "team-chat.md"
REPO_MEMORY = Path(__file__).parent.parent.parent / "memories" / "repo" / "workspace-state.md"

SYNC_INTERVAL_SECONDS = 300  # 5 minutes
PROGRESS_SYNC_THRESHOLD = 7  # updates before memory sync
CHAT_SYNC_THRESHOLD = 5  # messages before agent memory sync
SUMMARIZE_THRESHOLD = 20  # entries before LLM summarization

# Agent file mapping
AGENTS = {
    "CC": {"progress": "claude-code-progress.md", "memory": "claude-code-memory.md"},
    "OC2": {"progress": "openclaw-2-progress.md", "memory": "openclaw-2-memory.md"},
    "AS": {"progress": "assistant-progress.md", "memory": "assistant-memory.md"},
    "PM": {"progress": "polymorph-progress.md", "memory": "polymorph-memory.md"},
    "PM2": {"progress": "PM2-progress.md", "memory": "PM2-memory.md"},
    "RL": {"progress": "rl-progress.md", "memory": "rl-memory.md"},
    "Copilot": {"progress": "copilot-progress.md", "memory": "copilot-memory.md"},
}


class ProgressSyncAgent:
    """Syncs agent progress files to memory and team chat."""

    def __init__(self):
        self.update_counts = {agent: 0 for agent in AGENTS}
        self.last_chat_lines = 0
        self.last_progress_hashes = {agent: "" for agent in AGENTS}
        self._load_state()

    def _load_state(self):
        """Load sync state from disk."""
        state_file = WORKSPACE_ROOT / "tools" / ".sync-state.json"
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text())
                self.update_counts = state.get("update_counts", self.update_counts)
                self.last_chat_lines = state.get("last_chat_lines", 0)
                self.last_progress_hashes = state.get("last_progress_hashes", self.last_progress_hashes)
            except Exception:
                pass

    def _save_state(self):
        """Persist sync state to disk."""
        state_file = WORKSPACE_ROOT / "tools" / ".sync-state.json"
        state = {
            "update_counts": self.update_counts,
            "last_chat_lines": self.last_chat_lines,
            "last_progress_hashes": self.last_progress_hashes,
            "last_sync": datetime.now().isoformat(),
        }
        state_file.write_text(json.dumps(state, indent=2))

    def _file_hash(self, path: Path) -> str:
        """Get MD5 hash of file content."""
        if not path.exists():
            return ""
        content = path.read_text(encoding="utf-8", errors="replace")
        return hashlib.md5(content.encode()).hexdigest()

    def _count_entries(self, path: Path) -> int:
        """Count update entries in a progress file (lines starting with ## or ###)."""
        if not path.exists():
            return 0
        content = path.read_text(encoding="utf-8", errors="replace")
        return sum(1 for line in content.splitlines() if line.strip().startswith("##"))

    def check_progress_changes(self):
        """Check all agent progress files for changes."""
        changes = {}
        for agent, files in AGENTS.items():
            prog_path = PROGRESS_DIR / files["progress"]
            current_hash = self._file_hash(prog_path)
            if current_hash != self.last_progress_hashes.get(agent, ""):
                entries = self._count_entries(prog_path)
                changes[agent] = {
                    "path": str(prog_path),
                    "entries": entries,
                    "changed": prog_path.exists(),
                }
                self.last_progress_hashes[agent] = current_hash
                if prog_path.exists():
                    self.update_counts[agent] = self.update_counts.get(agent, 0) + 1
        return changes

    def sync_agent_to_memory(self, agent: str):
        """Sync agent progress highlights to their working memory."""
        files = AGENTS.get(agent)
        if not files:
            return

        prog_path = PROGRESS_DIR / files["progress"]
        mem_path = PROGRESS_DIR / files["memory"]

        if not prog_path.exists():
            return

        # Read last few entries from progress
        content = prog_path.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()

        # Find the last status update section
        last_status_lines = []
        in_status = False
        for line in reversed(lines):
            if line.strip().startswith("## Status:"):
                in_status = True
                last_status_lines.insert(0, line)
                break
            if in_status:
                last_status_lines.insert(0, line)

        if not last_status_lines:
            return

        # Append to memory file
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
        sync_entry = f"\n---\n## Sync: {timestamp}\n"
        sync_entry += "\n".join(last_status_lines[-10:])  # Last 10 lines of status

        existing = ""
        if mem_path.exists():
            existing = mem_path.read_text(encoding="utf-8", errors="replace")

        # Avoid duplicate syncs
        if sync_entry.strip() not in existing:
            mem_path.write_text(existing + sync_entry, encoding="utf-8")
            print(f"[SYNC] {agent}: progress -> memory synced")

    def check_team_chat(self):
        """Check team chat for new messages."""
        if not TEAM_CHAT.exists():
            return 0

        content = TEAM_CHAT.read_text(encoding="utf-8", errors="replace")
        current_lines = len(content.splitlines())

        new_lines = current_lines - self.last_chat_lines
        self.last_chat_lines = current_lines
        return new_lines

    def check_stale_agents(self, threshold_hours: int = 6):
        """Find agents that haven't updated progress recently."""
        stale = []
        now = datetime.now()
        for agent, files in AGENTS.items():
            prog_path = PROGRESS_DIR / files["progress"]
            if prog_path.exists():
                mtime = datetime.fromtimestamp(prog_path.stat().st_mtime)
                age_hours = (now - mtime).total_seconds() / 3600
                if age_hours > threshold_hours:
                    stale.append((agent, round(age_hours, 1)))
            else:
                stale.append((agent, -1))  # Missing file
        return stale

    def run_sync_cycle(self):
        """Run one sync cycle."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] === SYNC CYCLE ===")

        # 1. Check progress changes
        changes = self.check_progress_changes()
        if changes:
            for agent, info in changes.items():
                print(f"  [CHANGE] {agent}: {info['entries']} entries")
                # Sync to memory if threshold reached
                if self.update_counts.get(agent, 0) >= PROGRESS_SYNC_THRESHOLD:
                    self.sync_agent_to_memory(agent)
                    self.update_counts[agent] = 0

        # 2. Check team chat
        new_chat_lines = self.check_team_chat()
        if new_chat_lines > 0:
            print(f"  [CHAT] {new_chat_lines} new lines")

        # 3. Check stale agents
        stale = self.check_stale_agents()
        if stale:
            for agent, age in stale:
                age_str = f"{age}h ago" if age >= 0 else "MISSING"
                print(f"  [STALE] {agent}: {age_str}")

        # 4. Save state
        self._save_state()

        return changes, stale

    def run_daemon(self):
        """Run as a continuous daemon."""
        print("=" * 50)
        print("  WORKSPACE SYNC DAEMON")
        print("=" * 50)
        print(f"  Interval: {SYNC_INTERVAL_SECONDS}s")
        print(f"  Progress dir: {PROGRESS_DIR}")
        print(f"  Team chat: {TEAM_CHAT}")
        print(f"  Started: {datetime.now().isoformat()}")
        print("=" * 50)

        try:
            while True:
                self.run_sync_cycle()
                time.sleep(SYNC_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            self._save_state()
            print("\n[SYNC] Daemon stopped. State saved.")


def main():
    """Entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Workspace Progress Sync")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--once", action="store_true", help="Run one sync cycle")
    parser.add_argument("--interval", type=int, default=SYNC_INTERVAL_SECONDS,
                        help=f"Sync interval in seconds (default: {SYNC_INTERVAL_SECONDS})")
    args = parser.parse_args()

    agent = ProgressSyncAgent()

    if args.once:
        changes, stale = agent.run_sync_cycle()
        if not changes and not stale:
            print("  No changes detected.")
    elif args.daemon:
        agent.run_daemon()
    else:
        # Default: run once
        changes, stale = agent.run_sync_cycle()
        if not changes and not stale:
            print("  No changes detected.")


if __name__ == "__main__":
    main()
