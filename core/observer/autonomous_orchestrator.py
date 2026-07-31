"""Phase 3: Autonomous Operational Orchestration.

Wires Telegram slash commands to the real O-2/O-3 spawn engine:
- /spawn → AgentSpawner.spawn() with consensus + blueprint + lifecycle
- /task → Long-horizon task tracking with disk persistence
- /report → Autonomous report loop (agent output → compression → vault → Telegram)
- Runtime state tracking + strategic queue for deferred execution
"""
import os
import json
import uuid
import datetime
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from core.observer.vault import Vault
from core.observer.journal import Journal
from core.observer.report_return import ReportReturnSystem


@dataclass
class TaskRecord:
    """Persistent task record for long-horizon continuity."""
    task_id: str
    name: str
    status: str = "pending"  # pending, active, blocked, complete, failed
    created_at: str = ""
    updated_at: str = ""
    agent_id: str = ""
    output: str = ""
    error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.datetime.utcnow().isoformat() + "Z"
        if not self.updated_at:
            self.updated_at = self.created_at


class TaskOrchestrator:
    """Long-horizon task tracking with disk persistence.

    Tasks persist across crashes, restarts, model resets, and session changes.
    """

    def __init__(self, vault: Vault = None, journal: Journal = None, state_path: str = None):
        self.vault = vault or Vault()
        self.journal = journal or Journal(self.vault)
        self.state_path = state_path or os.path.join(os.getcwd(), "data", "task_state.json")
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
        self._tasks: Dict[str, TaskRecord] = {}
        self._queue: List[str] = []  # strategic queue: ordered task_ids
        self._load_state()

    def _load_state(self):
        """Load persisted task state from disk."""
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for tid, t in data.get("tasks", {}).items():
                    self._tasks[tid] = TaskRecord(**t)
                self._queue = data.get("queue", [])
            except Exception:
                pass

    def _save_state(self):
        """Persist task state to disk."""
        try:
            data = {
                "tasks": {tid: asdict(t) for tid, t in self._tasks.items()},
                "queue": self._queue,
                "saved_at": datetime.datetime.utcnow().isoformat() + "Z"
            }
            with open(self.state_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def create_task(self, name: str, metadata: Dict[str, Any] = None) -> TaskRecord:
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task = TaskRecord(task_id=task_id, name=name, metadata=metadata or {})
        self._tasks[task_id] = task
        self._queue.append(task_id)
        self._save_state()
        self.journal.record_event({"type": "task_create", "task_id": task_id, "name": name})
        return task

    def update_task(self, task_id: str, **kwargs) -> Optional[TaskRecord]:
        task = self._tasks.get(task_id)
        if not task:
            return None
        for k, v in kwargs.items():
            if hasattr(task, k):
                setattr(task, k, v)
        task.updated_at = datetime.datetime.utcnow().isoformat() + "Z"
        self._save_state()
        self.journal.record_event({"type": "task_update", "task_id": task_id, "changes": list(kwargs.keys())})
        return task

    def get_task(self, task_id: str) -> Optional[TaskRecord]:
        return self._tasks.get(task_id)

    def list_tasks(self, status: str = None) -> List[TaskRecord]:
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return sorted(tasks, key=lambda t: t.updated_at, reverse=True)

    def get_queue(self) -> List[TaskRecord]:
        """Return tasks in strategic queue order."""
        return [self._tasks[tid] for tid in self._queue if tid in self._tasks]

    def summary(self) -> str:
        counts: Dict[str, int] = {}
        for t in self._tasks.values():
            counts[t.status] = counts.get(t.status, 0) + 1
        parts = [f"{k}: {v}" for k, v in sorted(counts.items())]
        return f"Tasks: {len(self._tasks)} total ({', '.join(parts)}), {len(self._queue)} queued"


class AutonomousOrchestrator:
    """Main Phase 3 orchestrator: Telegram → Spawn Engine → Agents → Reports."""

    def __init__(self, vault: Vault = None, journal: Journal = None):
        self.vault = vault or Vault()
        self.journal = journal or Journal(self.vault)
        self.tasks = TaskOrchestrator(vault=self.vault, journal=self.journal)
        self.reports = ReportReturnSystem(vault=self.vault, journal=self.journal)
        self._active_spawns: Dict[str, Any] = {}

    async def spawn_agent(self, task_type: str, user_input: str, session_context: Dict = None) -> Dict[str, Any]:
        """Spawn an agent via the real O-3 AgentSpawner pipeline."""
        from core.spawn.agent_spawner import AgentSpawner

        spawner = AgentSpawner()
        result = await spawner.spawn(
            user_input=user_input,
            session_context=session_context or {},
        )

        # Track in task orchestrator
        task = self.tasks.create_task(
            name=f"spawn_{task_type}",
            metadata={"spawn_id": result.spawn_id, "task_type": task_type}
        )
        self.tasks.update_task(task.task_id, status="active", agent_id=result.spawn_id)

        # Store active spawn
        self._active_spawns[result.spawn_id] = {
            "task_id": task.task_id,
            "result": result,
            "started": datetime.datetime.utcnow().isoformat() + "Z"
        }

        self.journal.record_event({
            "type": "orchestrated_spawn",
            "spawn_id": result.spawn_id,
            "task_type": task_type,
            "task_id": task.task_id,
        })

        return {
            "spawn_id": result.spawn_id,
            "task_id": task.task_id,
            "status": result.status,
            "output": result.output,
            "error": result.error,
        }

    def get_runtime_state(self) -> Dict[str, Any]:
        """Return current runtime state for /status command."""
        return {
            "active_spawns": len(self._active_spawns),
            "tasks": self.tasks.summary(),
            "queue_depth": len(self.tasks.get_queue()),
            "recent_reports": len(self.reports.recent_reports(5)),
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        }

    def format_status(self) -> str:
        state = self.get_runtime_state()
        lines = [
            "🧠 Primary Observer — Runtime State",
            f"Active spawns: {state['active_spawns']}",
            f"Tasks: {state['tasks']}",
            f"Queue depth: {state['queue_depth']}",
            f"Recent reports: {state['recent_reports']}",
            f"Updated: {state['timestamp']}",
        ]
        return "\n".join(lines)


if __name__ == "__main__":
    import asyncio
    ao = AutonomousOrchestrator()
    print(ao.format_status())
    print()

    # Test task creation
    t = ao.tasks.create_task("test_phase3", {"source": "cli"})
    print(f"Created: {t.task_id} — {t.name}")
    ao.tasks.update_task(t.task_id, status="complete", output="Phase 3 test OK")
    print(f"Updated: {t.task_id} → complete")
    print(ao.tasks.summary())
