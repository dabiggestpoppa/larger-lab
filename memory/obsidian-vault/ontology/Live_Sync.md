# Live Sync

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #obsidian

```python
"""
O2C Phase 0G — Live Sync
========================
Obsidian vault folder synchronization.

Watches the O2C-VAULT directory for changes and syncs with Obsidian.
Also provides sync monitoring — detects new notes, triggers linking.

Key principle: Direct markdown writes first. No plugins/APIs initially.
Obsidian auto-detects file changes in its vault folder.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("o2c.live_sync")

# ── Configuration ──────────────────────────────────────────────────────────────

DEFAULT_VAULT_PATH = Path("O2C-VAULT")
OBSIDIAN_VAULT_NAME = "O2C-VAULT"
SYNC_STATE_FILE = ".sync_state.json"
OBSIDIAN_CONFIG_DIR = ".obsidian"


# ── Vault Path Resolution ─────────────────────────────────────────────────────

def find_obsidian_vault() -> Optional[Path]:
    """
    Find the Obsidian vault path.
    Checks common locations:
    1. OBSIDIAN_VAULT_PATH environment variable
    2. ~/Documents/Obsidian Vault/
    3. ~/Obsidian/
    4. ~/O2C-VAULT/
    5. Walk up from DEFAULT_VAULT_PATH to find .obsidian config
    """
    # 1. Environment variable
    env_path = os.environ.get("OBSIDIAN_VAULT_PATH")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p

    # 2. Common locations
    home = Path.home()
    candidates = [
        home / "Documents" / "Obsidian Vault",
        home / "Documents" / OBSIDIAN_VAULT_NAME,
        home / "Obsidian",
        home / OBSIDIAN_VAULT_NAME,
        home / "Desktop" / OBSIDIAN_VAULT_NAME,
    ]
    for candidate in candidates:
        if candidate.exists() and (candidate / OBSIDIAN_CONFIG_DIR).exists():
            return candidate

    # 3. Check if DEFAULT_VAULT_PATH has .obsidian config
    if DEFAULT_VAULT_PATH.exists() and (DEFAULT_VAULT_PATH / OBSIDIAN_CONFIG_DIR).exists():
        return DEFAULT_VAULT_PATH.resolve()

    # 4. Check parent directories
    for parent in [DEFAULT_VAULT_PATH.resolve()] + list(DEFAULT_VAULT_PATH.resolve().parents):
        if (parent / OBSIDIAN_CONFIG_DIR).exists():
            return parent

    return None


def ensure_obsidian_vault(vault_path: Path) -> Path:
    """
    Ensure the Obsidian vault directory exists with proper structure.
    Creates .obsidian config if missing.
    """
    vault_path.mkdir(parents=True, exist_ok=True)

    # Create .obsidian config directory
    obsidian_config = vault_path / OBSIDIAN_CONFIG_DIR
    obsidian_config.mkdir(exist_ok=True)

    # Create basic Obsidian config if missing
    app_config = obsidian_config / "app.json"
    if not app_config.exists():
        app_config.write_text(json.dumps({
            "legacyEditor": False,
            "livePreview": True,
            "promptDelete": False,
            "alwaysUpdateLinks": True,
        }, indent=2))

    # Create plugins config for auto-detection
    community_plugins = obsidian_config / "community-plugins.json"
    if not community_plugins.exists():
        community_plugins.write_text(json.dumps([], indent=2))

    return vault_path


# ── Sync State Management ─────────────────────────────────────────────────────

class SyncState:
    """Tracks sync state between O2C-VAULT and Obsidian vault."""

    def __init__(self, vault_path: Path):
        self._state_file = vault_path / SYNC_STATE_FILE
        self._state: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if self._state_file.exists():
            try:
                return json.loads(self._state_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, IOError):
                pass
        return {"files": {}, "last_sync": None, "sync_count": 0}

    def _save(self):
        self._state_file.write_text(
            json.dumps(self._state, indent=2, default=str),
            encoding="utf-8",
        )

    def get_file_hash(self, relative_path: str) -> Optional[str]:
        return self._state.get("files", {}).get(relative_path, {}).get("hash")

    def update_file(self, relative_path: str, content: str):
        if "files" not in self._state:
            self._state["files"] = {}
        self._state["files"][relative_path] = {
            "hash": hashlib.md5(content.encode()).hexdigest(),
            "modified": datetime.now(timezone.utc).isoformat(),
            "size": len(content),
        }
        self._save()

    def remove_file(self, relative_path: str):
        if "files" in self._state and relative_path in self._state["files"]:
            del self._state["files"][relative_path]
            self._save()

    def get_all_tracked(self) -> Dict[str, Any]:
        return self._state.get("files", {})

    def update_sync_count(self):
        self._state["sync_count"] = self._state.get("sync_count", 0) + 1
        self._state["last_sync"] = datetime.now(timezone.utc).isoformat()
        self._save()

    @property
    def sync_count(self) -> int:
        return self._state.get("sync_count", 0)

    @property
    def last_sync(self) -> Optional[str]:
        return self._state.get("last_sync")


# ── Live Sync Engine ──────────────────────────────────────────────────────────

class LiveSync:
    """
    Syncs O2C-VAULT markdown files with Obsidian vault folder.

    Obsidian auto-detects file changes, so we just need to:
    1. Write markdown files to the vault directory
    2. Track sync state to detect changes
    3. Trigger linking after new notes are written
    """

    def __init__(
        self,
        source_path: Optional[Path] = None,
        obsidian_path: Optional[Path] = None,
    ):
        self.source_path = source_path or DEFAULT_VAULT_PATH.resolve()
        self.obsidian_path = obsidian_path or find_obsidian_vault()
        self._state: Optional[SyncState] = None

    @property
    def state(self) -> SyncState:
        if self._state is None:
            if self.obsidian_path and self.obsidian_path.exists():
                self._state = SyncState(self.obsidian_path)
            else:
                self._state = SyncState(self.source_path)
        return self._state

    def resolve_target_path(self) -> Path:
        """Resolve the target path for sync (Obsidian vault or local)."""
        if self.obsidian_path and self.obsidian_path.exists():
            return self.obsidian_path
        return self.source_path

    def sync_file(self, relative_path: str, content: str) -> bool:
        """
        Sync a single file to the vault.
        Returns True if the file was written/updated.
        """
        target = self.resolve_target_path()

        # Check if content changed
        existing_hash = self.state.get_file_hash(relative_path)
        new_hash = hashlib.md5(content.encode()).hexdigest()

        if existing_hash == new_hash:
            return False  # No change

        # Write file
        file_path = target / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

        # Update state
        self.state.update_file(relative_path, content)
        logger.info(f"Synced: {relative_path}")
        return True

    def sync_all(self) -> Tuple[int, int]:
        """
        Sync all markdown files from source to target.
        Returns (files_written, files_skipped).
        """
        target = self.resolve_target_path()
        written = 0
        skipped = 0

        if not self.source_path.exists():
            logger.warning(f"Source path does not exist: {self.source_path}")
            return (0, 0)

        for md_file in self.source_path.rglob("*.md"):
            # Skip hidden files and sync state
            if md_file.name.startswith(".") or md_file.name == SYNC_STATE_FILE:
                continue

            relative = md_file.relative_to(self.source_path)
            relative_str = str(relative).replace("\\", "/")

            content = md_file.read_text(encoding="utf-8")
            if self.sync_file(relative_str, content):
                written += 1
            else:
                skipped += 1

        self.state.update_sync_count()
        logger.info(f"Sync complete: {written} written, {skipped} skipped")
        return (written, skipped)

    def remove_file(self, relative_path: str) -> bool:
        """Remove a file from the vault."""
        target = self.resolve_target_path()
        file_path = target / relative_path

        if file_path.exists():
            file_path.unlink()
            self.state.remove_file(relative_path)
            logger.info(f"Removed: {relative_path}")
            return True
        return False

    def get_status(self) -> Dict[str, Any]:
        """Get sync status."""
        target = self.resolve_target_path()
        return {
            "source_path": str(self.source_path),
            "obsidian_path": str(self.obsidian_path) if self.obsidian_path else None,
            "target_path": str(target),
            "obsidian_detected": self.obsidian_path is not None and self.obsidian_path.exists(),
            "sync_count": self.state.sync_count,
            "last_sync": self.state.last_sync,
            "tracked_files": len(self.state.get_all_tracked()),
        }


# ── Convenience Functions ─────────────────────────────────────────────────────

_live_sync_instance: Optional[LiveSync] = None


def get_live_sync() -> LiveSync:
    """Get or create the LiveSync singleton."""
    global _live_sync_instance
    if _live_sync_instance is None:
        _live_sync_instance = LiveSync()
    return _live_sync_instance


def sync_to_obsidian() -> Tuple[int, int]:
    """Sync all O2C-VAULT files to Obsidian. Returns (written, skipped)."""
    return get_live_sync().sync_all()


def write_and_sync(
    relative_path: str,
    content: str,
) -> bool:
    """Write a file and sync to Obsidian."""
    sync = get_live_sync()

    # Write to source first
    source_file = sync.source_path / relative_path
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text(content, encoding="utf-8")

    # Sync to target
    return sync.sync_file(relative_path, content)

```

LINKS:
[[Hermes Obsidian Test   Vault Working]]
[[Journal 20260602T004840Z Command Sync]]
[[Journal 20260602T004840Z Sync]]
[[Live Deployment Status]]
[[Obsidian Vault Connection Info]]
[[Ontology Core Summary]]
[[Sage Audit Environment Utilization]]
[[Cal]]
[[Citation Workflow]]
[[Configuration]]
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
[[Task Executor]]
[[Task Intent Analyzer]]
[[Vault]]
[[Compressor]]
[[Error Intelligence]]
[[Knowledge Importer]]
[[Linker]]
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
