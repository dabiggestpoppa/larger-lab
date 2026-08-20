"""
CTBT T4 — Sealed-engine parity test.

The runtime sealed engine, fed the SAME raw 2025 M5 bars used at T2, must
reproduce the T2 forward/confirmation event ledger EXACTLY (entry ts,
exit ts, direction, exit reason, gross bps).  This proves the runtime path
is the research engine — no silent divergence.
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ctbt_runtime.config import T11_REPAIR, T4_DIR  # noqa: E402
from ctbt_runtime.data_feed import M5Bar, TriSnapshot  # noqa: E402
from ctbt_runtime.sealed_engine import (SealedStrategyEngine,  # noqa: E402
                                        StrategyHashMismatch)

sys.path.insert(0, str(T11_REPAIR))
from run_t11_screen import LEG_FILES, load_leg  # noqa: E402

T2 = T11_REPAIR.parent / "t2_confirmation"

EXPECTED = {
    "EUR_GBP_USD": 146,
    "GBP_NZD_USD": 81,
}


def load_2025_snapshots(triangle: str):
    from run_t11_screen import TRIANGLES
    legs = TRIANGLES[triangle]["legs"]
    series = {leg: load_leg(leg) for leg in legs}
    common = sorted(set.intersection(*(set(series[l]) for l in legs)))
    common = [ts for ts in common
              if datetime(2025, 1, 1) <= ts <= datetime(2025, 12, 31, 23, 59, 59)]
    snapshots = []
    for ts in common:
        bars = {}
        for leg in legs:
            o, h, l, c = series[leg][ts]
            bars[leg] = M5Bar(timestamp=ts, open=o, high=h, low=l, close=c,
                              volume=0, raw_time=0)
        snapshots.append(TriSnapshot(timestamp=ts, legs=bars))
    return snapshots


def t2_events(triangle: str):
    out = {}
    with open(T2 / "CTBT_T2_EVENT_LEDGER.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["triangle"] != triangle:
                continue
            out[(r["entry_timestamp"], r["exit_timestamp"], r["direction"])] = {
                "exit_reason": r["exit_reason"],
                "gross_bps": round(float(r["gross_bps"]), 6),
            }
    return out


def test_hash_drift_detected():
    eng = SealedStrategyEngine("EUR_GBP_USD")
    eng.spec["rolling_z"]["lookback"] = 999  # tamper
    try:
        SealedStrategyEngine("EUR_GBP_USD", spec=eng.spec)
    except StrategyHashMismatch:
        return
    raise AssertionError("hash drift was not detected")


def test_parity_eur_gbp_usd():
    _parity("EUR_GBP_USD")


def test_parity_gbp_nzd_usd():
    _parity("GBP_NZD_USD")


def _parity(triangle: str):
    eng = SealedStrategyEngine(triangle)
    snaps = load_2025_snapshots(triangle)
    events = eng.evaluate(snaps)
    got = {(e["decision_bar_timestamp"], e["exit_timestamp"], e["direction"]): e
           for e in events}
    want = t2_events(triangle)
    assert len(events) == EXPECTED[triangle], (
        f"{triangle}: runtime produced {len(events)} events, "
        f"T2 ledger has {EXPECTED[triangle]}")
    assert set(got.keys()) == set(want.keys()), (
        f"{triangle}: event identity mismatch "
        f"(runtime-only: {sorted(set(got) - set(want))[:3]}, "
        f"missing: {sorted(set(want) - set(got))[:3]})")
    for k, w in want.items():
        g = got[k]
        assert g["exit_reason"] == w["exit_reason"], (k, g["exit_reason"], w["exit_reason"])
        assert abs(g["gross_bps"] - w["gross_bps"]) < 1e-6, (k, g["gross_bps"], w["gross_bps"])


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    print(f"sealed-engine parity: {len(tests)}/{len(tests)} passed")


if __name__ == "__main__":
    main()
