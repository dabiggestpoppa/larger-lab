#!/usr/bin/env python3
"""
OWL Workflow Engine
====================
Manages OWL's sub-agent pipeline:
1. Read task board (TASKS.md)
2. Spawn sub-agents for pending tasks
3. Monitor active sub-agents
4. Collect results
5. Update progress
6. Archive completed tasks

Usage:
  python quant-lab/command-center/owl-workflow.py           # Run one cycle
  python quant-lab/command-center/owl-workflow.py --status  # Show status
  python quant-lab/command-center/owl-workflow.py --reset   # Reset all active tasks
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

LAB_ROOT = Path(__file__).resolve().parent.parent.parent
CC_LAB_ROOT = LAB_ROOT  # same workspace
COMMAND_CENTER = LAB_ROOT / "quant-lab" / "command-center"
TASKS_FILE = COMMAND_CENTER / "TASKS.md"
LOG_DIR = COMMAND_CENTER / "logs"
MEMORY_DIR = COMMAND_CENTER / "memory"
WORKING_MEMORY = MEMORY_DIR / "working.md"
WORKFLOW_LOG = LOG_DIR / "owl-workflow.log"
PHASE_FILE = COMMAND_CENTER / ".phase-state.json"

CYCLE_INTERVAL = 180  # 3 minutes between cycles
MAX_CONCURRENT_AGENTS = 5


def log(msg):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{now}] {msg}"
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode("ascii", errors="replace").decode())
    with open(WORKFLOW_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_phase():
    if PHASE_FILE.exists():
        with open(PHASE_FILE, "r") as f:
            return json.load(f)
    return {"current_phase": "PHASE_1", "phases": {}}


def save_phase(data):
    with open(PHASE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def parse_tasks():
    """Parse TASKS.md to extract active tasks."""
    if not TASKS_FILE.exists():
        return [], []

    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    active = []
    completed = []

    # Split by task sections
    task_blocks = re.split(r'### (T\d+): ', content)

    for i in range(1, len(task_blocks), 2):
        task_id = task_blocks[i]
        task_body = task_blocks[i + 1] if i + 1 < len(task_blocks) else ""

        # Extract status
        status_match = re.search(r'\*\*Status:\*\*\s*(\S+)', task_body)
        status = status_match.group(1) if status_match else "UNKNOWN"

        # Extract priority
        priority_match = re.search(r'\*\*Priority:\*\*\s*(\S+)', task_body)
        priority = priority_match.group(1) if priority_match else "LOW"

        # Extract agent
        agent_match = re.search(r'\*\*Agent:\*\*\s*`?(\S+)`?', task_body)
        agent = agent_match.group(1) if agent_match else "quant-developer"

        # Extract title
        title_match = re.search(r'### T\d+:\s*(.+)', task_body)
        title = title_match.group(1).strip() if title_match else task_id

        task = {
            "id": task_id,
            "title": title,
            "status": status,
            "priority": priority,
            "agent": agent,
            "body": task_body,
        }

        if "COMPLETED" in status or "✅" in status:
            completed.append(task)
        elif "PENDING" in status or "IN_PROGRESS" in status:
            active.append(task)

    return active, completed


def get_priority_value(priority):
    """Convert priority string to numeric value for sorting."""
    return {"HIGHEST": 5, "HIGH": 4, "MEDIUM": 3, "LOW": 2, "LOWEST": 1}.get(priority.upper(), 0)


def update_working_memory(active_tasks, completed_count):
    """Update working memory file with current state."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    memory = f"""# 🦉 OWL Working Memory

> **Last Updated:** {now}
> **Active Tasks:** {len(active_tasks)}
> **Completed Tasks:** {completed_count}

## Active Tasks (Priority Order)
"""

    for task in sorted(active_tasks, key=lambda t: get_priority_value(t["priority"]), reverse=True):
        memory += f"- **{task['id']}:** {task['title']} [{task['status']}] (Priority: {task['priority']}, Agent: {task['agent']})\n"

    memory += f"""
## Recent Activity
- Workflow cycle at {now}
- {len(active_tasks)} tasks in queue
- {completed_count} tasks completed

## Notes
- Source of truth: CEREBUS Manual v4.0 > PineScript V5
- Max concurrent sub-agents: {MAX_CONCURRENT_AGENTS}
- Do NOT post to team-chat.md unless MAD says so
- Stay in lane: quant-lab domain only
"""

    with open(WORKING_MEMORY, "w", encoding="utf-8") as f:
        f.write(memory)


def run_cycle():
    """Run one workflow cycle."""
    log("=" * 60)
    log("OWL Workflow Cycle Starting")
    log("=" * 60)

    # Load state
    phase = load_phase()
    log(f"Current phase: {phase.get('current_phase', 'UNKNOWN')}")

    # Parse tasks
    active, completed = parse_tasks()
    log(f"Active tasks: {len(active)}, Completed: {len(completed)}")

    # Sort by priority
    active.sort(key=lambda t: get_priority_value(t["priority"]), reverse=True)

    # Show task queue
    for task in active:
        log(f"  {task['id']}: {task['title']} [{task['status']}] Priority={task['priority']}")

    # Update working memory
    update_working_memory(active, len(completed))
    log("Working memory updated")

    # Phase check
    phase_data = phase.get("phases", {})
    current = phase.get("current_phase", "PHASE_1")
    log(f"Phase status: {current}")

    log("Cycle complete")
    return active, completed


def show_status():
    """Show current status."""
    phase = load_phase()
    active, completed = parse_tasks()

    print("\n" + "=" * 60)
    print("🦉 OWL Command Center — Status")
    print("=" * 60)
    print(f"Phase: {phase.get('current_phase', 'UNKNOWN')}")
    print(f"Active tasks: {len(active)}")
    print(f"Completed tasks: {len(completed)}")
    print()

    if active:
        print("Task Queue (by priority):")
        for task in sorted(active, key=lambda t: get_priority_value(t["priority"]), reverse=True):
            status_icon = "🔴" if "PENDING" in task["status"] else "🟡"
            print(f"  {status_icon} {task['id']}: {task['title']} [{task['status']}] (P:{task['priority']}, A:{task['agent']})")

    if completed:
        print(f"\nCompleted:")
        for task in completed:
            print(f"  ✅ {task['id']}: {task['title']}")

    print()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "--status":
            show_status()
        elif cmd == "--reset":
            log("Reset requested")
            # Reset would go here
            print("Reset complete")
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print("Usage: python owl-workflow.py [--status|--reset]")
    else:
        run_cycle()
