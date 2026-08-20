"""
CTBT T4 — Forward clock & activation seal.

The activation seal is written by the runtime at first successful activation
(after the T4 commit exists) and contains:

  T4 commit SHA, UTC activation timestamp, provider, account environment,
  runtime version, strategy hashes, symbol mappings, first causally complete
  M5 bar eligible for forward evidence.

FORWARD EVIDENCE STARTS ONLY AFTER THIS SEAL.  No earlier bar may be
relabeled as forward evidence.
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

from .config import (DEMO_CANARY, ENGINE, HORIZONS, PROVIDER, RUNTIME,
                     STRATEGY_HASHES, STRATEGY_VERSIONS, SYMBOL_MAP)

RUNTIME_VERSION = "ctbt-runtime-0.1.0"


def _git_head_sha(repo: Path) -> Optional[str]:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                             text=True, cwd=repo, timeout=15)
        return out.stdout.strip() if out.returncode == 0 else None
    except Exception:
        return None


def first_eligible_m5_bar(now: Optional[datetime] = None) -> str:
    """First causally complete M5 bar strictly after activation.

    Completed M5 bars close at :00, :05, ... :55.  A bar whose close time is
    strictly after `now` is not yet complete, so the first eligible bar is
    the next bar boundary at or after now + 5 minutes, minus a safety margin
    of one bar (ensures the bar is fully closed and causally complete).
    """
    now = now or datetime.utcnow()
    # next M5 boundary strictly after now
    secs = (now.minute % 5) * 60 + now.second
    next_close = now + timedelta(seconds=(300 - secs))
    # require the bar to be fully closed: boundary + 1 full bar of margin
    eligible = next_close + timedelta(minutes=5)
    return eligible.replace(microsecond=0).isoformat() + "Z"


class ForwardClock:
    def __init__(self, seal_path: Optional[Path] = None,
                 clock_path: Optional[Path] = None):
        self.seal_path = seal_path or RUNTIME["activation_seal"]
        self.clock_path = clock_path or RUNTIME["forward_clock"]

    # ── activation ─────────────────────────────────────────────────────────
    def build_seal(self, repo: Path, first_bar: str, activation_ts: datetime,
                   commit_sha: Optional[str] = None) -> dict:
        return {
            "checkpoint": "SW-CTBT-T4-TRANSFER-FAMILY-RUNTIME-SHADOW-INTEGRATION",
            "activation_commit": commit_sha or _git_head_sha(repo),
            "activation_timestamp_utc": activation_ts.isoformat() + "Z",
            "provider": PROVIDER,
            "runtime_version": RUNTIME_VERSION,
            "strategy_hashes": STRATEGY_HASHES,
            "strategy_versions": STRATEGY_VERSIONS,
            "symbol_mappings": SYMBOL_MAP,
            "first_eligible_m5_bar": first_bar,
            "forward_evidence_rule": "Every eligible event strictly after "
                                     "activation_timestamp_utc is FORWARD evidence. "
                                     "No earlier bar may be relabeled as forward evidence.",
            "status": "ACTIVE",
        }

    def stamp(self, repo: Path, activation_ts: Optional[datetime] = None,
              commit_sha: Optional[str] = None) -> dict:
        activation_ts = activation_ts or datetime.utcnow()
        seal = self.build_seal(repo, first_eligible_m5_bar(activation_ts),
                               activation_ts, commit_sha)
        self.seal_path.parent.mkdir(parents=True, exist_ok=True)
        self.seal_path.write_text(json.dumps(seal, indent=2), encoding="utf-8")
        self._write_clock(seal, {})
        return seal

    # ── clock ──────────────────────────────────────────────────────────────
    def _write_clock(self, seal: dict, counts: Dict[str, int]) -> dict:
        act = datetime.fromisoformat(seal["activation_timestamp_utc"].replace("Z", "+00:00"))
        clock = {
            "activation_timestamp_utc": seal["activation_timestamp_utc"],
            "activation_commit": seal["activation_commit"],
            "first_eligible_m5_bar": seal["first_eligible_m5_bar"],
            "elapsed_days": round((datetime.utcnow() - act.replace(tzinfo=None)).total_seconds() / 86400.0, 4),
            "completed_events": {
                "EUR_GBP_USD": counts.get("EUR_GBP_USD", 0),
                "GBP_NZD_USD": counts.get("GBP_NZD_USD", 0),
            },
            "horizons": HORIZONS,
            "demo_canary": DEMO_CANARY,
            "authoritative": True,
        }
        self.clock_path.write_text(json.dumps(clock, indent=2), encoding="utf-8")
        return clock

    def update_clock(self, counts: Dict[str, int]) -> dict:
        seal = json.loads(self.seal_path.read_text(encoding="utf-8"))
        return self._write_clock(seal, counts)

    def is_active(self) -> bool:
        if not self.seal_path.exists():
            return False
        try:
            seal = json.loads(self.seal_path.read_text(encoding="utf-8"))
            return seal.get("status") == "ACTIVE" and seal.get("activation_commit")
        except Exception:
            return False
