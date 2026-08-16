"""
TB-R2 — Rolling Triangle Snapshot Capture (audit tool)
=======================================================

Collects N synchronized triangle snapshots (signal + execution) and saves them
as JSONL for audit. DATA COLLECTION ONLY — never submits orders.

Usage:
    python -m tb_live.snapshot_capture --count 60 --interval 5 --out captures.jsonl
    python -m tb_live.snapshot_capture --count 1 --once

Run from the quant-lab directory (or with quant-lab on PYTHONPATH).
With no MT5 terminal available this fails closed and records zero snapshots.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tb_live.market_data import (  # noqa: E402
    TBMarketDataConfig, TriangleSnapshotHealth,
)
from tb_live.snapshot import (  # noqa: E402
    MT5MarketDataAdapter, SymbolResolver, SynchronizedTriangleFeed,
)


def capture_once(feed: SynchronizedTriangleFeed, cfg: TBMarketDataConfig,
                 ) -> dict:
    """Capture one synchronized signal + execution snapshot pair."""
    sig = feed.get_synchronized_closed_triangle()
    health = feed.get_health()
    record = {
        "captured_at_utc": datetime.utcnow().isoformat() + "Z",
        "signal_snapshot_valid": sig.signal_snapshot_valid,
        "failure_code": sig.failure_code.value,
        "signal_bar_close_time": (sig.signal_bar_close_time.isoformat()
                                  if sig.signal_snapshot_valid else None),
        "signal_snapshot_id": sig.snapshot_id,
        "bars": {
            sym: {
                "bar_open_time": b.bar_open_time.isoformat(),
                "open": b.open, "high": b.high, "low": b.low, "close": b.close,
                "bar_id": b.bar_id,
            }
            for sym, b in sig.bars.items()
        } if sig.signal_snapshot_valid else {},
        "health": {
            "state": health.overall_state().value,
            "signal_valid": health.signal_valid,
            "execution_valid": health.execution_valid,
            "signal_reason": health.signal_reason,
            "execution_reason": health.execution_reason,
            "max_quote_age_ms": health.max_quote_age_ms,
            "cross_leg_skew_ms": health.cross_leg_skew_ms,
            "spread_ga": health.spread_ga,
            "spread_gn": health.spread_gn,
            "spread_an": health.spread_an,
        },
    }
    return record


def main():
    ap = argparse.ArgumentParser(description="TB-R2 triangle snapshot capture")
    ap.add_argument("--count", type=int, default=60)
    ap.add_argument("--interval", type=float, default=5.0)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--out", default="tb_snapshot_capture.jsonl")
    ap.add_argument("--max-quote-age-ms", type=float, default=2000.0)
    ap.add_argument("--max-skew-ms", type=float, default=1000.0)
    args = ap.parse_args()

    cfg = TBMarketDataConfig(
        max_quote_age_ms=args.max_quote_age_ms,
        max_cross_leg_skew_ms=args.max_skew_ms,
    )
    adapter = MT5MarketDataAdapter(bar_seconds=cfg.bar_seconds)
    ok = adapter.initialize()
    if not ok:
        print("FAIL_CLOSED: MT5 unavailable — zero snapshots captured.", flush=True)
        return 1

    feed = SynchronizedTriangleFeed(adapter=adapter, config=cfg)
    try:
        feed.resolver.resolve()
    except Exception as e:  # noqa: BLE001
        print(f"FAIL_CLOSED: symbol resolution failed: {e}", flush=True)
        adapter.shutdown()
        return 1

    out = Path(args.out)
    n = 1 if args.once else args.count
    captured = 0
    try:
        with out.open("a", encoding="utf-8") as f:
            for i in range(n):
                rec = capture_once(feed, cfg)
                f.write(json.dumps(rec) + "\n")
                f.flush()
                captured += 1
                print(f"[{i + 1}/{n}] {rec['health']['state']} "
                      f"signal_valid={rec['signal_snapshot_valid']}", flush=True)
                if not args.once and i < n - 1:
                    time.sleep(args.interval)
    finally:
        adapter.shutdown()

    print(f"captured={captured} -> {out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
