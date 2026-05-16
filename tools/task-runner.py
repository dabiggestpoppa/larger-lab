#!/usr/bin/env python3
"""
Task Runner — Lightweight Agent Task Queue
===========================================
Simple task queue system for delegating work between agents.

Tasks are stored as JSON files in tasks/ directory.
Each task has: id, agent, status, description, command, output.

Usage:
  python tools/task-runner.py --list           # List all tasks
  python tools/task-runner.py --create         # Create a new task (interactive)
  python tools/task-runner.py --run CC         # Run next pending task for CC
  python tools/task-runner.py --status TASK-01 # Check task status
  python tools/task-runner.py --complete TASK-01 --output "Done"
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Fix Windows console encoding for emoji output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

LAB_ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = LAB_ROOT / "tasks"

AGENT_CHOICES = ["CC", "OC", "HR"]
STATUS_CHOICES = ["pending", "in_progress", "complete", "failed", "blocked"]


def ensure_tasks_dir():
    TASKS_DIR.mkdir(exist_ok=True)


def list_tasks(agent_filter: str = None, status_filter: str = None) -> list:
    """List all tasks, optionally filtered."""
    ensure_tasks_dir()
    tasks = []

    for f in sorted(TASKS_DIR.glob("*.json")):
        try:
            with open(f) as fh:
                task = json.load(fh)
            if agent_filter and task.get("agent") != agent_filter:
                continue
            if status_filter and task.get("status") != status_filter:
                continue
            tasks.append(task)
        except (json.JSONDecodeError, IOError):
            continue

    return tasks


def create_task(agent: str, description: str, command: str = "",
                priority: str = "medium", depends_on: str = None) -> dict:
    """Create a new task."""
    ensure_tasks_dir()
    task_id = f"TASK-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"

    task = {
        "task_id": task_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "agent": agent,
        "description": description,
        "command": command,
        "priority": priority,
        "status": "pending",
        "depends_on": depends_on,
        "output": None,
        "completed_at": None,
    }

    task_file = TASKS_DIR / f"{task_id}.json"
    with open(task_file, "w") as f:
        json.dump(task, f, indent=2)

    return task


def get_task(task_id: str) -> dict:
    """Get a task by ID."""
    task_file = TASKS_DIR / f"{task_id}.json"
    if not task_file.exists():
        return None
    with open(task_file) as f:
        return json.load(f)


def update_task(task_id: str, **kwargs) -> dict:
    """Update a task."""
    task = get_task(task_id)
    if not task:
        return None

    task.update(kwargs)
    task_file = TASKS_DIR / f"{task_id}.json"
    with open(task_file, "w") as f:
        json.dump(task, f, indent=2)

    return task


def get_next_pending(agent: str) -> dict:
    """Get the next pending task for an agent."""
    tasks = list_tasks(agent_filter=agent, status_filter="pending")
    if not tasks:
        return None
    # Sort by priority (high > medium > low) then by created_at
    priority_order = {"high": 0, "medium": 1, "low": 2}
    tasks.sort(key=lambda t: (priority_order.get(t.get("priority", "medium"), 1), t.get("created_at", "")))
    return tasks[0]


def print_task(task: dict):
    """Pretty print a task."""
    status_emoji = {
        "pending": "⏳",
        "in_progress": "🔄",
        "complete": "✅",
        "failed": "❌",
        "blocked": "🚫",
    }
    emoji = status_emoji.get(task.get("status", "pending"), "❓")
    print(f"  {emoji} {task['task_id']} [{task.get('agent', '?')}] {task.get('description', 'No description')}")
    if task.get("command"):
        print(f"     Command: {task['command']}")
    if task.get("output"):
        print(f"     Output: {task['output'][:100]}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Task Runner — Agent Task Queue")
    parser.add_argument("--list", action="store_true", help="List all tasks")
    parser.add_argument("--agent", choices=AGENT_CHOICES, help="Filter by agent")
    parser.add_argument("--status", choices=STATUS_CHOICES, help="Filter by status")
    parser.add_argument("--create", action="store_true", help="Create a new task")
    parser.add_argument("--run", choices=AGENT_CHOICES, help="Run next pending task for agent")
    parser.add_argument("--complete", metavar="TASK_ID", help="Mark task as complete")
    parser.add_argument("--fail", metavar="TASK_ID", help="Mark task as failed")
    parser.add_argument("--output", type=str, help="Output for completed/failed task")
    parser.add_argument("--show", metavar="TASK_ID", help="Show task details")
    args = parser.parse_args()

    if args.list or (not args.create and not args.run and not args.complete and not args.fail and not args.show):
        tasks = list_tasks(agent_filter=args.agent, status_filter=args.status)
        if not tasks:
            print("📋 No tasks found.")
        else:
            print(f"📋 Tasks ({len(tasks)}):")
            for task in tasks:
                print_task(task)

    elif args.create:
        print("📝 Create new task")
        agent = input("Agent (CC/OC/HR) [OC]: ").strip().upper() or "OC"
        if agent not in AGENT_CHOICES:
            agent = "OC"
        description = input("Description: ").strip()
        if not description:
            print("❌ Description required.")
            return
        command = input("Command (optional): ").strip()
        priority = input("Priority (high/medium/low) [medium]: ").strip().lower() or "medium"
        task = create_task(agent, description, command, priority)
        print(f"✅ Created {task['task_id']}")

    elif args.run:
        task = get_next_pending(args.run)
        if not task:
            print(f"📋 No pending tasks for {args.run}.")
            return
        update_task(task["task_id"], status="in_progress")
        print(f"🔄 Running {task['task_id']}:")
        print_task(task)
        if task.get("command"):
            print(f"  → Execute: {task['command']}")

    elif args.complete:
        output = args.output or "Completed"
        task = update_task(args.complete, status="complete", output=output,
                           completed_at=datetime.now(timezone.utc).isoformat())
        if task:
            print(f"✅ {args.complete} marked complete.")
        else:
            print(f"❌ Task {args.complete} not found.")

    elif args.fail:
        output = args.output or "Failed"
        task = update_task(args.fail, status="failed", output=output,
                           completed_at=datetime.now(timezone.utc).isoformat())
        if task:
            print(f"❌ {args.fail} marked failed.")
        else:
            print(f"❌ Task {args.fail} not found.")

    elif args.show:
        task = get_task(args.show)
        if task:
            print_task(task)
        else:
            print(f"❌ Task {args.show} not found.")


if __name__ == "__main__":
    main()
