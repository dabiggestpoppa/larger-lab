"""
CTBT T4 — Append-only forward shadow event ledger.

Every natural forward event (strictly after activation) is appended as one
JSONL record with full schema: strategy identity, decision/exit data, leg
directions, W2 model weights, observed quotes, modeled + observed crossing
cost, MAE/MFE placeholders (filled when the basket would have been live),
and completeness classification (set later by the independent auditor).

Ledger files live under state/ and are never rewritten in place.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .config import RUNTIME

LEDGER_KEYS = [
    "strategy_version", "strategy_hash", "event_id", "provider", "environment",
    "decision_bar_timestamp", "signal_timestamp", "triangle", "direction",
    "entry_z", "basis", "leg_symbols", "leg_directions", "w2_model_weights",
    "bid", "ask", "mid", "spread_per_leg", "modeled_cost_bps",
    "observed_quote_crossing_cost_bps", "observed_model_cost_multiple",
    "theoretical_entry_state", "exit_timestamp", "exit_z", "exit_reason",
    "gross_bps", "net_modeled_bps", "net_observed_cost_bps", "mae_bps",
    "mfe_bps", "hold_minutes", "completeness_classification", "quote_freshness",
    "cross_leg_skew_seconds", "missing_leg", "stale_quote", "spread_anomaly",
    "data_validity",
]


class ShadowEventLedger:
    def __init__(self, triangle: str, path: Optional[Path] = None):
        self.triangle = triangle
        self.path = path or (RUNTIME["ledger_dir"] / f"ledger_{triangle}.jsonl")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: dict) -> None:
        rec = {k: record.get(k) for k in LEDGER_KEYS}
        rec["event_id"] = record.get("event_id") or self._next_id()
        rec.setdefault("provider", "OxSecurities-Demo")
        rec.setdefault("environment", "READ_ONLY_SHADOW")
        rec.setdefault("observed_quote_crossing_cost_bps", None)
        rec.setdefault("observed_model_cost_multiple", None)
        rec.setdefault("net_observed_cost_bps", None)
        rec.setdefault("mae_bps", None)
        rec.setdefault("mfe_bps", None)
        rec.setdefault("completeness_classification", "PENDING_AUDIT")
        rec.setdefault("theoretical_entry_state", "OPEN")
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")

    def _next_id(self) -> str:
        n = 0
        if self.path.exists():
            n = sum(1 for _ in open(self.path, encoding="utf-8"))
        return f"{self.triangle}-FWD-{n + 1:05d}"

    def read_all(self) -> List[dict]:
        if not self.path.exists():
            return []
        return [json.loads(l) for l in open(self.path, encoding="utf-8") if l.strip()]

    def count(self) -> int:
        return len(self.read_all())

    def update_classification(self, event_id: str, classification: str,
                              note: str = "") -> None:
        """Completeness auditor writes classifications back (append-only
        mirror keeps the original; classification lives in the audit table)."""
        # Keep the raw ledger immutable; classifications go to the audit table.
        audit_path = self.path.with_suffix(".audit.jsonl")
        with open(audit_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"event_id": event_id,
                                "classification": classification,
                                "note": note,
                                "audited_at": datetime.utcnow().isoformat() + "Z"},
                               default=str) + "\n")
