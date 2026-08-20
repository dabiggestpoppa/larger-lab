"""
CTBT T4 — Activation routine.

Verifies (read-only):
  - provider connection (OxSecurities-Demo)
  - sealed strategy hashes load without drift
  - all required symbols mapped and trading
  - M5 bars available for every leg
then stamps CTBT_T4_ACTIVATION_SEAL.json + CTBT_T4_FORWARD_CLOCK.json.

NO orders, NO account mutation, NO capital routing.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from .config import BASIS_LEGS, PROVIDER, REPO, SYMBOL_MAP  # noqa: E402
from .data_feed import CTBTDataFeed  # noqa: E402
from .forward_clock import ForwardClock  # noqa: E402
from .sealed_engine import SealedStrategyEngine  # noqa: E402


def run_activation(commit_sha: str | None = None,
                   activation_ts: datetime | None = None) -> dict:
    feed = CTBTDataFeed()
    if not feed.init():
        return {"ok": False, "error": f"MT5 initialize failed: {feed.mt5.last_error()}"}
    try:
        acct = feed.account_summary()
        if not acct.get("connected"):
            return {"ok": False, "error": f"not connected: {acct}"}
        if acct.get("trade_mode") != 0:
            return {"ok": False,
                    "error": f"expected DEMO (trade_mode=0), got {acct}"}

        # symbol availability
        missing = []
        for leg, sym in SYMBOL_MAP.items():
            if feed.mt5.symbol_info(sym) is None:
                missing.append(sym)
        if missing:
            return {"ok": False, "error": f"missing symbols: {missing}"}

        # M5 bars available for every leg (warmup feasibility)
        depth = {}
        for tri, legs in BASIS_LEGS.items():
            per_leg = {}
            for leg in legs:
                bars = feed.fetch_latest_completed_bars(leg, 260)
                per_leg[leg] = len(bars)
            depth[tri] = per_leg
        shallow = {k: v for k, v in depth.items()
                   if any(n < 200 for n in v.values())}
        if shallow:
            return {"ok": False,
                    "error": f"insufficient M5 warmup history: {shallow}"}

        # strategy hash integrity
        for tri in BASIS_LEGS:
            SealedStrategyEngine(tri)  # raises on hash drift

        seal = ForwardClock().stamp(REPO, activation_ts or datetime.utcnow(),
                                    commit_sha=commit_sha)
        return {"ok": True, "account": acct, "warmup_depth": depth,
                "seal": seal}
    finally:
        feed.shutdown()


if __name__ == "__main__":
    res = run_activation()
    print(json.dumps(res, indent=2, default=str))
    sys.exit(0 if res.get("ok") else 1)
