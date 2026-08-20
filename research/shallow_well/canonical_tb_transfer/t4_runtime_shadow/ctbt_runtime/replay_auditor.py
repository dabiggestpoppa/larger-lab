"""
CTBT T4 — Independent signal completeness auditor.

Reconstructs eligible signals INDEPENDENTLY from raw completed M5 bars using
the sealed engine, then classifies each against the runtime shadow ledger.

It never derives expected signals from runtime output: replay is a separate
code path over raw bar data (provider fetch or stored fixture).

Classifications:
  MATCHED_SHADOW       runtime captured the event identically
  VALID_RUNTIME_BLOCK  runtime correctly declined (concurrency/session block)
  MISSED_SIGNAL        replay eligible event absent from runtime ledger
  RUNTIME_ONLY_SIGNAL  runtime event not reproducible from raw bars
  DATA_DIVERGENCE      replay/runtime differ due to data/provider divergence
  NO_SIGNAL            no eligible event
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .data_feed import TriSnapshot
from .sealed_engine import SealedStrategyEngine


class ReplayAuditor:
    def __init__(self, triangle: str, engine: SealedStrategyEngine):
        self.triangle = triangle
        self.engine = engine

    # ── independent replay ─────────────────────────────────────────────────
    def replay(self, snapshots: List[TriSnapshot]) -> List[dict]:
        """Independently compute eligible events from raw bars (primary lane)."""
        return self.engine.evaluate(snapshots)

    # ── classification ─────────────────────────────────────────────────────
    @staticmethod
    def _key(e: dict) -> Tuple[str, str, str]:
        return (e.get("decision_bar_timestamp", ""),
                e.get("exit_timestamp", ""),
                e.get("direction", ""))

    def classify(self, replay_events: List[dict],
                 runtime_events: List[dict],
                 blocked_intervals: Optional[List[Tuple[str, str]]] = None,
                 data_divergences: Optional[List[dict]] = None) -> List[dict]:
        """Classify every replay event against the runtime ledger."""
        blocked_intervals = blocked_intervals or []
        data_divergences = data_divergences or []
        runtime_keys = {self._key(e) for e in runtime_events}
        div_keys = {self._key(d) for d in data_divergences}
        rows = []
        for e in replay_events:
            k = self._key(e)
            if k in div_keys:
                cls, note = "DATA_DIVERGENCE", "raw-bar divergence recorded"
            elif k in runtime_keys:
                cls, note = "MATCHED_SHADOW", "runtime event matches independent replay"
            elif self._blocked(k, blocked_intervals):
                cls, note = "VALID_RUNTIME_BLOCK", "runtime correctly blocked (concurrency/session)"
            else:
                cls, note = "MISSED_SIGNAL", "runtime did not record an eligible event"
            rows.append({"event_id": e.get("event_id"), "classification": cls,
                         "note": note, "entry_ts": k[0], "direction": k[2]})
        # runtime-only signals
        replay_keys = {self._key(e) for e in replay_events}
        for e in runtime_events:
            if self._key(e) not in replay_keys:
                rows.append({"event_id": e.get("event_id"),
                             "classification": "RUNTIME_ONLY_SIGNAL",
                             "note": "runtime event not reproducible from raw bars",
                             "entry_ts": e.get("decision_bar_timestamp"),
                             "direction": e.get("direction")})
        return rows

    @staticmethod
    def _blocked(k: Tuple[str, str, str], intervals: List[Tuple[str, str]]) -> bool:
        try:
            ts = datetime.fromisoformat(k[0])
        except ValueError:
            return False
        for s, e in intervals:
            try:
                if datetime.fromisoformat(s) <= ts <= datetime.fromisoformat(e):
                    return True
            except ValueError:
                continue
        return False

    @staticmethod
    def summary(rows: List[dict]) -> dict:
        out = {}
        for r in rows:
            out[r["classification"]] = out.get(r["classification"], 0) + 1
        total = sum(out.values())
        out["_total"] = total
        out["_recognition_target_pct"] = 100.0
        return out
