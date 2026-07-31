"""
5_continuity.continuity_guardian
=================================
Ensures field continuity across restarts via checkpoint/restore.

Manages field state persistence, integrity verification,
and automatic recovery from last known good state.
"""

import json
import hashlib
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.continuity")

DEFAULT_CHECKPOINT_DIR = Path(__file__).parent.parent / "data" / "continuity"


class CheckpointMeta(BaseModel):
    checkpoint_id: str
    timestamp: str
    session_id: str
    module_count: int
    checksum: str
    size_bytes: int


class ContinuityGuardianConfig(BaseModel):
    """Configuration for continuity_guardian."""
    enabled: bool = True
    checkpoint_interval_sec: float = 300.0
    max_checkpoints: int = 50
    auto_restore: bool = True
    checkpoint_dir: str = ""  # empty = default


class ContinuityGuardianModule:
    """Ensures field continuity across restarts."""

    def __init__(self):
        self.config = ContinuityGuardianConfig()
        self.running = False
        self._lock = Lock()
        self._session_id: str = ""
        self._checkpoint_id: str = ""
        self._last_checkpoint_time: Optional[str] = None
        self._checkpoints: List[CheckpointMeta] = []
        self._checkpoint_dir = Path(self.config.checkpoint_dir) if self.config.checkpoint_dir else DEFAULT_CHECKPOINT_DIR
        self._checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def start(self) -> None:
        """Start the continuity guardian. Auto-restores from last checkpoint if enabled."""
        self.running = True
        self._session_id = f"session_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"
        logger.info("ContinuityGuardian started (session=%s)", self._session_id)

        if self.config.auto_restore:
            latest = self._find_latest_checkpoint()
            if latest:
                logger.info("Auto-restoring from checkpoint: %s", latest)
                self.restore_checkpoint(latest)
            else:
                logger.info("No previous checkpoint found — fresh start")

    def stop(self) -> None:
        """Stop and create a final checkpoint."""
        if self.running:
            self.create_checkpoint("shutdown")
        self.running = False
        logger.info("ContinuityGuardian stopped")

    def create_checkpoint(self, label: str = "manual") -> str:
        """Create a field state checkpoint. Returns checkpoint_id."""
        with self._lock:
            ts = datetime.now(timezone.utc)
            cid = f"chk_{ts.strftime('%Y%m%d_%H%M%S')}_{label}"
            data = {
                "checkpoint_id": cid,
                "session_id": self._session_id,
                "timestamp": ts.isoformat(),
                "label": label,
                "field_version": "4.0.0",
                "modules": {},
                "agents": {},
                "metadata": {},
            }
            raw = json.dumps(data, sort_keys=True).encode()
            checksum = hashlib.sha256(raw).hexdigest()

            data["checksum"] = checksum
            path = self._checkpoint_dir / f"{cid}.json"
            path.write_text(json.dumps(data, indent=2))

            meta = CheckpointMeta(
                checkpoint_id=cid,
                timestamp=ts.isoformat(),
                session_id=self._session_id,
                module_count=len(data["modules"]),
                checksum=checksum,
                size_bytes=path.stat().st_size,
            )
            self._checkpoints.append(meta)
            self._checkpoint_id = cid
            self._last_checkpoint_time = ts.isoformat()

            # Evict old checkpoints
            while len(self._checkpoints) > self.config.max_checkpoints:
                old = self._checkpoints.pop(0)
                old_path = self._checkpoint_dir / f"{old.checkpoint_id}.json"
                if old_path.exists():
                    old_path.unlink()
                logger.debug("Evicted old checkpoint: %s", old.checkpoint_id)

            logger.info("Checkpoint created: %s (%d bytes)", cid, meta.size_bytes)
            return cid

    def restore_checkpoint(self, checkpoint_id: str) -> bool:
        """Restore field state from a checkpoint. Returns success."""
        with self._lock:
            path = self._checkpoint_dir / f"{checkpoint_id}.json"
            if not path.exists():
                logger.error("Checkpoint not found: %s", checkpoint_id)
                return False
            try:
                data = json.loads(path.read_text())
                stored_checksum = data.pop("checksum", "")
                computed = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
                if stored_checksum and stored_checksum != computed:
                    logger.error("Checkpoint integrity check FAILED for %s", checkpoint_id)
                    return False
                self._checkpoint_id = checkpoint_id
                self._session_id = data.get("session_id", self._session_id)
                self._last_checkpoint_time = data.get("timestamp")
                logger.info("Restored from checkpoint: %s (session=%s)", checkpoint_id, self._session_id)
                return True
            except Exception as e:
                logger.error("Failed to restore checkpoint %s: %s", checkpoint_id, e)
                return False

    def get_continuity_status(self) -> Dict[str, Any]:
        """Get current continuity status."""
        with self._lock:
            return {
                "session_id": self._session_id,
                "current_checkpoint": self._checkpoint_id,
                "last_checkpoint_time": self._last_checkpoint_time,
                "total_checkpoints": len(self._checkpoints),
                "running": self.running,
                "auto_restore": self.config.auto_restore,
            }

    def verify_integrity(self) -> bool:
        """Verify integrity of all stored checkpoints."""
        with self._lock:
            ok = True
            for meta in self._checkpoints:
                path = self._checkpoint_dir / f"{meta.checkpoint_id}.json"
                if not path.exists():
                    logger.warning("Checkpoint file missing: %s", meta.checkpoint_id)
                    ok = False
                    continue
                try:
                    data = json.loads(path.read_text())
                    stored = data.pop("checksum", "")
                    computed = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
                    if stored and stored != computed:
                        logger.warning("Integrity fail: %s", meta.checkpoint_id)
                        ok = False
                except Exception:
                    ok = False
            return ok

    def _find_latest_checkpoint(self) -> Optional[str]:
        """Find the most recent valid checkpoint ID."""
        checkpoints = sorted(self._checkpoint_dir.glob("chk_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        for cp in checkpoints:
            cid = cp.stem
            if self.restore_checkpoint(cid):
                return cid
        return None
