"""
CTBT T4 — Sealed strategy engine.

Loads the frozen strategy specification, verifies its sha256 against the
sealed T3 hash (config drift detection), and runs the EXACT T1.1 lifecycle
primitives (verified 405/405 + 194/194 against the canonical trade log) on
completed M5 bars.  Current/forming bars never enter evaluation.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .config import (BASIS_LEGS, STRATEGY_HASHES, STRATEGY_VERSIONS,
                     T11_REPAIR, ENGINE, RUNTIME)
from .data_feed import M5Bar, TriSnapshot

# Sealed T1.1 engine primitives — the exact lifecycle, reused verbatim.
sys.path.insert(0, str(T11_REPAIR))
from run_t11_screen import (compute_basis_z, run_lifecycle,  # noqa: E402
                            triangle_cost_bps, triangle_cost_bps_documented,
                            TRIANGLES, LEG_FILES)


class StrategyHashMismatch(RuntimeError):
    """Sealed strategy spec no longer matches its frozen hash (config drift)."""


def load_sealed_spec(triangle: str) -> dict:
    """Load the T3 candidate seal spec and verify its hash."""
    t3_dir = T11_REPAIR.parent / "t3_forward_prereg"
    seal = json.loads((t3_dir / f"CTBT_T3_{triangle}_CANDIDATE_SEAL.json").read_text(
        encoding="utf-8"))
    spec = seal["strategy_spec"]
    h = hashlib.sha256(
        json.dumps(spec, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    if h != STRATEGY_HASHES[triangle]:
        raise StrategyHashMismatch(
            f"{triangle}: spec hash {h} != sealed {STRATEGY_HASHES[triangle]}")
    return spec


class SealedStrategyEngine:
    """Frozen candidate adapter: snapshots -> shadow events."""

    def __init__(self, triangle: str, spec: Optional[dict] = None):
        if triangle not in STRATEGY_HASHES:
            raise ValueError(f"triangle {triangle} is not a sealed CTBT candidate")
        self.triangle = triangle
        self.spec = spec if spec is not None else load_sealed_spec(triangle)
        self.version = STRATEGY_VERSIONS[triangle]
        self.hash = STRATEGY_HASHES[triangle]
        self.legs = BASIS_LEGS[triangle]
        # self-verify on construction
        h = hashlib.sha256(json.dumps(
            self.spec, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        if h != self.hash:
            raise StrategyHashMismatch(f"{triangle}: hash drift at load ({h})")

    # ── evaluation ─────────────────────────────────────────────────────────
    def evaluate(self, snapshots: List[TriSnapshot],
                 warmup: int = 200) -> List[dict]:
        """Run the frozen lifecycle over synchronized snapshots (completed
        bars only).  Returns shadow events with modeled cost attached."""
        if not snapshots:
            return []
        # build bar records in the exact T1.1 engine shape
        bars = []
        for s in snapshots:
            rec = {"ts": s.timestamp}
            for leg in self.legs:
                b = s.legs[leg]
                rec[leg] = {"open": b.open, "high": b.high, "low": b.low, "close": b.close}
            bars.append(rec)
        if len(bars) < warmup + 10:
            return []
        basis, z = compute_basis_z(bars, TRIANGLES[self.triangle])
        for b, bv in zip(bars, basis):
            b["basis"] = bv
        trades = run_lifecycle(bars, z, ENGINE["entry_primary"],
                               ENGINE["exit_e1"]["short_exit_z"],
                               ENGINE["exit_e1"]["long_exit_z"])
        cost_bps = triangle_cost_bps(bars, TRIANGLES[self.triangle])
        events = []
        for i, t in enumerate(trades):
            events.append({
                "strategy_version": self.version,
                "strategy_hash": self.hash,
                "event_id": f"{self.triangle}-FWD-{i + 1:05d}",
                "triangle": self.triangle,
                "decision_bar_timestamp": str(t["entry_ts"]),
                "signal_timestamp": str(t["entry_ts"]),
                "direction": t["direction"],
                "entry_z": round(t["entry_z"], 6),
                "exit_timestamp": str(t["exit_ts"]),
                "exit_z": round(t["exit_z"], 6),
                "exit_reason": t["result"],
                "hold_minutes": round(t["hold_min"], 2),
                "gross_bps": round(t["gross_bps"], 6),
                "modeled_cost_bps": round(cost_bps, 6),
                "net_modeled_bps": round(t["gross_bps"] - cost_bps, 6),
            })
        return events

    @staticmethod
    def modeled_cost(snapshots: List[TriSnapshot], triangle: str) -> float:
        bars = []
        for s in snapshots:
            rec = {"ts": s.timestamp}
            for leg in BASIS_LEGS[triangle]:
                b = s.legs[leg]
                rec[leg] = {"open": b.open, "high": b.high, "low": b.low, "close": b.close}
            bars.append(rec)
        return triangle_cost_bps(bars, TRIANGLES[triangle])
