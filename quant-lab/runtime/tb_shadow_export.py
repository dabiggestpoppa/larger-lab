#!/usr/bin/env python3
"""QL-EXEC-R4.2 — additive legacy TB export writer (Option B).

The LEGACY worker writes this append-only JSONL stream AFTER its per-bar
decision, so the generic shadow can consume the same synchronized closed bars
and legacy PRIMARY/CONTROL decisions WITHOUT a second MT5 attach.

Non-interference contract (frozen):

- Never blocks or degrades legacy execution: failures are caught, logged, and
  counted; the exporter NEVER raises into the worker.
- Never holds a lock across strategy/broker execution (append + flush only).
- No shared mutable objects with the worker.
- Does not change strategy decisions, execution timing, order path, or broker
  path.
- Bounded disk: rotation at MAX_BYTES; hard cap on backups.

The integration point in the legacy worker is a THREE-LINE additive call after
the decision is computed:

    from runtime.tb_shadow_export import ShadowExporter
    shadow_exporter = ShadowExporter(path, generation, legacy_authority_sha)
    shadow_exporter.emit({...per-bar record...})   # failures tolerated inside

R4.2 does NOT wire this hook into the live worker; it ships the module, the
schema, and tests. The hook is enabled at live deployment under operator
supervision.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

_RUNTIME_DIR = Path(__file__).resolve().parent  # quant-lab/runtime/
if str(_RUNTIME_DIR) not in sys.path:
    sys.path.insert(0, str(_RUNTIME_DIR))

from runtime.tb_shadow_config import (  # noqa: E402
    DEPLOYMENT_GENERATION,
    LEGACY_EXPORT_FILE,
    LEGACY_AUTHORITY_SHA,
    MAX_LOG_BYTES,
)

EXPORT_SCHEMA_VERSION = 1
MAX_BYTES = 8 * 1024 * 1024      # rotate at 8 MB
BACKUP_SUFFIX = ".1"

# sub-fields required per bar record (validated leniently; never inferred)
_REQUIRED_TOP = ("bar_key", "source_timestamp", "market_open", "session", "bars")
_REQUIRED_TAG = ("basis", "z", "decision", "direction")


def content_hash(record: dict) -> str:
    body = {k: v for k, v in record.items() if k != "content_hash"}
    canon = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


class ShadowExporter:
    """Append-only, bounded, failure-tolerant export writer (legacy side)."""

    def __init__(
        self,
        path: str | Path = LEGACY_EXPORT_FILE,
        *,
        generation: str = DEPLOYMENT_GENERATION,
        legacy_authority_sha: str = LEGACY_AUTHORITY_SHA,
        max_bytes: int = MAX_BYTES,
    ) -> None:
        self.path = Path(path)
        self.generation = generation
        self.legacy_authority_sha = legacy_authority_sha
        self.max_bytes = max_bytes
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._seq = 0
        # bounded telemetry (failure counting; never raised to the worker)
        self.telemetry_ = {"records_written": 0, "failures": 0, "last_error": ""}

    def _next_seq(self) -> int:
        # monotonic from existing tail (restart-safe; no random identity)
        if self._seq == 0 and self.path.exists():
            last = -1
            try:
                with self.path.open("r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            last = int(json.loads(line).get("seq", -1))
                        except Exception:
                            continue
            except OSError:
                pass
            self._seq = last if last > 0 else 0
        self._seq += 1
        return self._seq

    def _rotate(self) -> None:
        try:
            if self.path.exists() and self.path.stat().st_size >= self.max_bytes:
                backup = self.path.with_name(self.path.name + BACKUP_SUFFIX)
                if backup.exists():
                    backup.unlink()
                self.path.rename(backup)
        except OSError:
            self.telemetry_["failures"] += 1

    def emit(self, record: dict) -> int:
        """Append one record; returns its seq. NEVER raises into the worker."""
        try:
            for key in _REQUIRED_TOP:
                if key not in record:
                    raise ValueError(f"export record missing {key!r}")
            for tag in ("primary", "control"):
                sub = record.get(tag) or {}
                for key in _REQUIRED_TAG:
                    if key not in sub:
                        raise ValueError(f"export record {tag} missing {key!r}")
            self._rotate()
            seq = self._next_seq()
            # The exporter OWNS identity fields (seq/generation/hash); a caller
            # payload can never clobber them.
            full = {
                **record,
                "schema_version": EXPORT_SCHEMA_VERSION,
                "seq": seq,
                "generation": self.generation,
                "legacy_authority_sha": self.legacy_authority_sha,
                "observed_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            full["content_hash"] = content_hash(full)
            line = json.dumps(full, sort_keys=True, default=str) + "\n"
            with self.path.open("a", encoding="utf-8") as f:
                f.write(line)
                f.flush()
                os.fsync(f.fileno())
            self.telemetry_["records_written"] += 1
            return seq
        except Exception as e:  # noqa: BLE001 — NEVER block legacy execution
            self.telemetry_["failures"] += 1
            self.telemetry_["last_error"] = str(e)[:500]
            return -1

    def telemetry(self) -> dict:
        return dict(self.telemetry_)
