# Task Executor

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #observer

```python
"""
TaskExecutor — Executes real tasks from PO spawn pipeline.

Handles: file moves, directory creation, symlink removal,
file merges, import path updates, team-chat posts, vault writes.
"""
from __future__ import annotations

import json
import shutil
import re
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("observer.task_executor")

REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_DIR = REPO_ROOT / "archive"
TEAM_CHAT = REPO_ROOT / "shared-conversations" / "team-chat.md"


class TaskResult:
    """Result of a single task execution."""
    def __init__(self, action: str, success: bool, detail: str = "", error: str = ""):
        self.action = action
        self.success = success
        self.detail = detail
        self.error = error
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "success": self.success,
            "detail": self.detail,
            "error": self.error,
            "timestamp": self.timestamp,
        }


class TaskExecutor:
    """Executes concrete workspace tasks."""

    def __init__(self):
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    # ── Filesystem Operations ──────────────────────────────────────────

    def move_to_archive(self, source: str, archive_subdir: str | None = None) -> TaskResult:
        """Move a file/dir to archive/ (no permanent delete)."""
        src = REPO_ROOT / source
        if not src.exists():
            return TaskResult("move_to_archive", False, error=f"{source} does not exist")

        dest_name = archive_subdir or source.rstrip("/\\")
        dest = ARCHIVE_DIR / dest_name

        # If dest already exists, add timestamp suffix
        if dest.exists():
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            dest = ARCHIVE_DIR / f"{dest_name}-{ts}"

        try:
            shutil.move(str(src), str(dest))
            logger.info(f"Moved {src} -> {dest}")
            return TaskResult("move_to_archive", True, detail=f"{source} -> archive/{dest_name}")
        except Exception as e:
            logger.error(f"Failed to move {src}: {e}")
            return TaskResult("move_to_archive", False, error=str(e))

    def remove_symlink(self, path: str) -> TaskResult:
        """Remove a symlink (not its target)."""
        p = REPO_ROOT / path
        if not p.exists() and not p.is_symlink():
            return TaskResult("remove_symlink", False, error=f"{path} does not exist")
        if not p.is_symlink():
            return TaskResult("remove_symlink", False, error=f"{path} is not a symlink")

        try:
            p.unlink()
            logger.info(f"Removed symlink {p}")
            return TaskResult("remove_symlink", True, detail=f"removed symlink {path}")
        except Exception as e:
            return TaskResult("remove_symlink", False, error=str(e))

    def merge_directories(self, source: str, target: str) -> TaskResult:
        """Merge source dir contents into target dir. Source is removed after."""
        src = REPO_ROOT / source
        tgt = REPO_ROOT / target

        if not src.exists():
            return TaskResult("merge_directories", False, error=f"{source} does not exist")

        tgt.mkdir(parents=True, exist_ok=True)

        moved = []
        try:
            for item in src.iterdir():
                dest_item = tgt / item.name
                if dest_item.exists():
                    # Skip if target already has this file
                    logger.warning(f"Skip (exists): {dest_item}")
                    continue
                shutil.move(str(item), str(dest_item))
                moved.append(item.name)

            # Remove source dir if empty
            if not any(src.iterdir()):
                src.rmdir()
                logger.info(f"Removed empty source dir {src}")
            else:
                logger.warning(f"Source dir {src} not empty after merge, keeping")

            return TaskResult(
                "merge_directories", True,
                detail=f"merged {len(moved)} items from {source} into {target}: {moved}"
            )
        except Exception as e:
            return TaskResult("merge_directories", False, error=str(e))

    def create_directory(self, path: str) -> TaskResult:
        """Create a directory."""
        p = REPO_ROOT / path
        try:
            p.mkdir(parents=True, exist_ok=True)
            return TaskResult("create_directory", True, detail=f"created {path}")
        except Exception as e:
            return TaskResult("create_directory", False, error=str(e))

    def write_file(self, path: str, content: str) -> TaskResult:
        """Write content to a file."""
        p = REPO_ROOT / path
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return TaskResult("write_file", True, detail=f"wrote {len(content)} chars to {path}")
        except Exception as e:
            return TaskResult("write_file", False, error=str(e))

    # ── Communication ──────────────────────────────────────────────────

    def post_team_chat(self, message: str, tag: str = "PO") -> TaskResult:
        """Append a message to team-chat.md."""
        try:
            TEAM_CHAT.parent.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            with open(TEAM_CHAT, "a", encoding="utf-8") as f:
                f.write(f"\n## [{tag}] {ts} — {message}\n")
            return TaskResult("post_team_chat", True, detail=f"posted to team-chat")
        except Exception as e:
            return TaskResult("post_team_chat", False, error=str(e))

    def write_vault_note(self, category: str, title: str, content: str) -> TaskResult:
        """Write a note to the Obsidian vault."""
        try:
            from tools.obsidian_access import vault_write
            path = vault_write(category=category, title=title, content=content)
            return TaskResult("write_vault_note", True, detail=f"wrote {path}")
        except Exception as e:
            return TaskResult("write_vault_note", False, error=str(e))

    # ── Composite Tasks ────────────────────────────────────────────────

    def execute_phase1_cleanup(self) -> list[TaskResult]:
        """Execute the full Phase 1 workspace cleanup."""
        results = []

        # 1. Move .openclaw/ to archive/.openclaw/
        r = self.move_to_archive(".openclaw", ".openclaw")
        results.append(r)
        self.post_team_chat(f"Phase 1.1: {r.detail or r.error}", "PO-EXEC")

        # 2. Remove quant_lab symlink
        r = self.remove_symlink("quant_lab")
        results.append(r)
        self.post_team_chat(f"Phase 1.2: {r.detail or r.error}", "PO-EXEC")

        # 3. Merge shared/ into shared-conversations/
        r = self.merge_directories("shared", "shared-conversations")
        results.append(r)
        self.post_team_chat(f"Phase 1.3: {r.detail or r.error}", "PO-EXEC")

        # 4. Write vault note
        summary = "\n".join(
            f"- {r.action}: {'✅' if r.success else '❌'} {r.detail or r.error}"
            for r in results
        )
        self.write_vault_note(
            category="execution",
            title="PO Phase 1 Cleanup Complete",
            content=f"# PO Phase 1 Workspace Cleanup\n\n{summary}\n\nTimestamp: {datetime.now(timezone.utc).isoformat()}"
        )

        return results

    def execute_task(self, task_name: str, **kwargs) -> list[TaskResult]:
        """Dispatch a named task."""
        dispatch = {
            "phase1_cleanup": self.execute_phase1_cleanup,
        }

        handler = dispatch.get(task_name)
        if handler:
            return handler()
        
        return [TaskResult("execute_task", False, error=f"Unknown task: {task_name}")]

```

LINKS:
[[All Mermaid Graphs]]
[[Module Guide]]
[[Tools]]
[[Executor Crash 20260531]]
[[Journal 20260602T005953Z Command Task]]
[[Journal 20260602T005953Z Task Create]]
[[Journal 20260602T005953Z Task Update]]
[[Ontology Core Summary]]
[[Task Flow]]
[[Action]]
[[Citation Workflow]]
[[Server]]
[[System]]
[[Asset Configs]]
[[Convergence Indicator]]
[[Dmr Standalone Backtest]]
[[P90 Backtest]]
[[P90 Count Ews]]
[[P90 Dmr Backtest]]
[[P90 Dmr Combo Backtest]]
[[P90 Dmr Overlay Backtest]]
[[P90 Engine]]
[[P90 Engine Dmr]]
[[P90 Gap Check]]
[[P90 Trace Trades]]
[[P90 Usdchf Backtest]]
[[Run Majors Backtest]]
[[Run St Multi Asset]]
[[Run Top5 Backtest Mc]]
[[St Batch2 Runner]]
[[St Batch Runner]]
[[Symmetry Trap]]
[[Symmetry Trap Backtest]]
[[Symmetry Trap Monte Carlo]]
[[Atomic Sym Trap]]
[[Blind Chain Debug]]
[[Blind Chain Diag]]
[[Blind Chain Engine]]
[[Blind Chain Exact]]
[[Blind Chain V2 Debug]]
[[Blind Chain V2 Sl Calibrated]]
[[Blind Chain V3]]
[[Cerebus Resolution Engine]]
[[Constraint Anchor Engine]]
[[Debug Days]]
[[Debug One Day]]
[[Debug St]]
[[Debug Trace]]
[[Diag Option B]]
[[Diag V5]]
[[Dmr Strategy]]
[[Dual Engine]]
[[Naut Asset Config]]
[[P90 Cfd Expansion Engine]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine V3]]
[[P90 Cfd Expansion Engine V4]]
[[P90 Cfd Expansion Engine V5]]
[[P90 Strategy]]
[[Shared]]
[[Stall Harvest Cfd Engine]]
[[Symmetry Trap Engine]]
[[Symmetry Trap Exact]]
[[Symmetry Trap Option B]]
[[Symmetry Trap Strategy]]
[[Symmetry Trap V4]]
[[Symmetry Trap V5]]
[[Symmetry Trap V6 Exact]]
[[Symmetry Trap V7B Sl Calibrated]]
[[Symmetry Trap V7 Sl Calibrated]]
[[Two Plays Engine]]
[[Adaptation Engine]]
[[Agent Lifecycle]]
[[Agent Spawner]]
[[Attractor Analysis]]
[[Autonomous Repair]]
[[Capability Matcher]]
[[Complexity Scorer]]
[[Consensus Memory]]
[[Consensus Replay]]
[[Context Injector]]
[[Continuity Preserver]]
[[Data Fetcher]]
[[Dormant State Manager]]
[[Environmental Monitor]]
[[Event Schema]]
[[Execution Boundary]]
[[Failure Analyzer]]
[[Indicators]]
[[Journal]]
[[Loader]]
[[Long Horizon Memory]]
[[Metrics]]
[[Model Selector]]
[[Multi Agent Coordinator]]
[[Observability Stress]]
[[Observer Consensus]]
[[Observer Evolution]]
[[Observer Persistence]]
[[Observer Registry]]
[[Observer Specialization]]
[[Openrouter Gateway]]
[[Operational Drift Detect]]
[[Operational Replay]]
[[Operational Scoring]]
[[Passive Awareness]]
[[Pattern Memory]]
[[Persistent Runtime]]
[[Persistent Scheduler]]
[[Recovery Persistence]]
[[Routing Consensus]]
[[Routing Learning]]
[[Runtime Heartbeat]]
[[Spawn Blueprint]]
[[Spawn Planner]]
[[Spawn Registry]]
[[Spawn Replay]]
[[Structural Anchor]]
[[Synthesizer]]
[[Task Classifier]]
[[Temporal Graph]]
[[Test Journal]]
[[Test Loader]]
[[Topology Learning]]
[[Trace Collector]]
[[Trace Feedback]]
[[Workflow Distiller]]
[[Workflow Memory]]
[[Autonomous Orchestrator]]
[[Chat Log]]
[[Command Router]]
[[Context Distiller]]
[[Continuity Memory]]
[[Event Awareness]]
[[Graph Traversal]]
[[Observer Conversation Runtime]]
[[Observer Lifecycle]]
[[Observer Session]]
[[Observer State]]
[[Pattern Distillation]]
[[Primary Observer]]
[[Report Return]]
[[Runtime Awareness]]
[[Semantic Retrieval]]
[[Task Intent Analyzer]]
[[Vault]]
[[Compressor]]
[[Error Intelligence]]
[[Knowledge Importer]]
[[Linker]]
[[Live Sync]]
[[Memory Distiller]]
[[Note Standard]]
[[Pattern Crystallizer]]
[[Taxonomy]]
[[Test Compressor]]
[[Test Context Injector]]
[[Test Error Intelligence]]
[[Test Linker]]
[[Test Memory Distiller]]
[[Test Note Standard]]
[[Test Pattern Crystallizer]]
[[Test Taxonomy]]
[[Test Vault Writer]]
[[Vault Writer]]
[[Interpreter]]
[[Semantic State]]
[[Telegram Gateway]]
