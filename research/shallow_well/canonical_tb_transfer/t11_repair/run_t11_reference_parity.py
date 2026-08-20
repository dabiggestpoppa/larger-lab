#!/usr/bin/env python3
"""
CTBT T1.1 — Reference parity verification.

Independently reimplements the frozen canonical Triangular Basis lifecycle
from FIRST PRINCIPLES (basis, causal rolling-z, entry/exit/stop/hard-exit,
session) and verifies it reproduces the canonical reference trade log EXACTLY:

  CONTROL (z2.5 / exit 0.0)   -> 405 trades (canonical_trade_log.csv)
  PRIMARY (z3.0 / exit +-0.25) -> 194 entries

This is NOT a re-run of the canonical code — it is an independent
reconstruction checked against the sealed trade log as oracle.

Canonical frozen contract (source: tb_forward_config.py + strategy_freeze.json):
  basis    = ln(GBPAUD) - ln(GBPNZD) + ln(AUDNZD)
  z        = (basis - mean(prev 200)) / std(prev 200, ddof=0)  [current excluded]
  entry    = strict |z| > entry_z          (2.5 control / 3.0 primary)
  direction= z>0 -> SHORT, z<0 -> LONG
  exit     = control: SHORT z<=0.0, LONG z>=0.0
             primary: SHORT z<=-0.25, LONG z>=+0.25
  stop     = SHORT z>=+6.0, LONG z<=-6.0
  hardexit = est_hour >= 12  (TIMEOUT)
  session  = London 3-12 EST (fixed UTC-5, no DST); entry only 3<=est<12
  min time = entry only if est_hour <= 10 (>= 120 min to hard exit)
  lifecycle= max 1 concurrent basket; re-entry after close
  cost     = 10.2 pips round trip (frozen)
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[4]
DATA = REPO / "quant-lab" / "data"
HERE = Path(__file__).resolve().parent

# ── Frozen canonical constants ───────────────────────────────────────────
LOOKBACK = 200
STOP_Z = 6.0
LONDON_START_H_EST = 3
LONDON_END_H_EST = 12
HARD_EXIT_H_EST = 12
MIN_MINUTES_TO_EXIT = 120
ATR_PERIOD = 20
MAX_TOTAL_LEVERAGE = 3.0
COST_PIPS = 10.2
PIP = 0.0001  # all three legs are non-JPY

CANONICAL_SYMBOLS = ["GBPAUD", "GBPNZD", "AUDNZD"]
CANONICAL_FILES = {
    "GBPAUD": "GBPAUD_M5.csv",
    "GBPNZD": "GBPNZD_M5.csv",
    "AUDNZD": "AUDNZD_PRO_M5.csv",
}


def parse_ts(raw: str) -> datetime:
    raw = raw.strip()
    for fmt in (
        "%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M",
        "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M", "%Y-%m-%d",
        "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M",
        "%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M",
        "%Y%m%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    raise ValueError(f"cannot parse timestamp {raw!r}")


def load_csv(path: Path) -> dict:
    """Load a CSV, returning {datetime: (open, high, low, close)}."""
    out = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        first = f.readline()
        f.seek(0)
        delim = "\t" if "\t" in first else ","
        reader = csv.DictReader(f, delimiter=delim)
        for row in reader:
            c = {k.strip().strip("<").strip(">"): v for k, v in row.items()}
            ts_raw = (c.get("timestamp") or c.get("Timestamp") or c.get("TIMESTAMP")
                      or c.get("datetime") or c.get("Datetime") or c.get("DATETIME")
                      or c.get("time") or c.get("Time") or c.get("TIME"))
            if not ts_raw:
                continue
            o = float(c.get("OPEN") or c.get("open"))
            h = float(c.get("HIGH") or c.get("high"))
            l = float(c.get("LOW") or c.get("low"))
            cl = float(c.get("CLOSE") or c.get("close"))
            out[parse_ts(ts_raw)] = (o, h, l, cl)
    return out


def load_sync() -> list:
    """Load the three canonical legs and inner-join by timestamp."""
    series = {s: load_csv(DATA / CANONICAL_FILES[s]) for s in CANONICAL_SYMBOLS}
    common = sorted(set(series["GBPAUD"]) & set(series["GBPNZD"]) & set(series["AUDNZD"]))
    bars = []
    for ts in common:
        ga = series["GBPAUD"][ts]
        gn = series["GBPNZD"][ts]
        an = series["AUDNZD"][ts]
        bars.append({
            "ts": ts,
            "ga": ga[3], "gn": gn[3], "an": an[3],  # closes
            "ga_h": ga[1], "ga_l": ga[2],
            "gn_h": gn[1], "gn_l": gn[2],
            "an_h": an[1], "an_l": an[2],
        })
    return bars


def est_hour(ts: datetime) -> int:
    return (ts.hour - 5) % 24


def compute_z_incremental(basis_values: list) -> list:
    """Exact canonical rolling-z: window = prev 200 (current excluded), ddof=0."""
    z = []
    hist = []
    for b in basis_values:
        hist.append(b)
        if len(hist) > LOOKBACK:
            window = hist[-(LOOKBACK + 1):-1]
            mean = float(np.mean(window))
            std = float(np.std(window))
            z.append((b - mean) / std if std > 0 else 0.0)
        else:
            z.append(0.0)
    return z


def compute_atr_incremental(bars: list, key: str) -> list:
    """Exact canonical ATR (20-period), matching _update_atr_incrementally."""
    atr = []
    window = []
    for i, bar in enumerate(bars):
        h = bar[f"{key}_h"]
        l = bar[f"{key}_l"]
        prev_close = bars[i - 1][key] if i >= 1 else None
        if prev_close is None:
            tr = h - l
        else:
            tr = max(h - l, abs(h - prev_close), abs(l - prev_close))
        window.append(tr)
        if len(window) > ATR_PERIOD:
            window = window[-ATR_PERIOD:]
        if (i + 1) >= ATR_PERIOD:
            atr.append(sum(window) / len(window))
        else:
            atr.append(0.0)
    return atr


def run_lifecycle(bars, entry_z, short_exit_z, long_exit_z, stop_z):
    """Run the frozen canonical lifecycle. Returns list of trade dicts."""
    n = len(bars)
    basis = [np.log(b["ga"]) - np.log(b["gn"]) + np.log(b["an"]) for b in bars]
    z = compute_z_incremental(basis)
    atr = {k: compute_atr_incremental(bars, k) for k in ("ga", "gn", "an")}

    trades = []
    in_trade = False
    direction = None
    entry = None  # dict snapshot

    for i in range(n):
        bar = bars[i]
        z_val = z[i]
        eh = est_hour(bar["ts"])

        if in_trade:
            exit_reason = None
            # Frozen backtest engine order: hard noon exit is checked FIRST.
            if eh >= HARD_EXIT_H_EST:
                exit_reason = "TIMEOUT"
            elif direction == "SHORT" and z_val <= short_exit_z:
                exit_reason = "TP_HIT"
            elif direction == "LONG" and z_val >= long_exit_z:
                exit_reason = "TP_HIT"
            elif direction == "SHORT" and z_val >= stop_z:
                exit_reason = "SL_HIT"
            elif direction == "LONG" and z_val <= -stop_z:
                exit_reason = "SL_HIT"

            if exit_reason:
                sizes = entry["sizes"]
                pnl = leg_pnl(entry, bar, direction, sizes)
                gross = sum(pnl.values())
                cost = COST_PIPS  # total leverage == 3.0 -> constant 10.2
                trades.append({
                    "entry_ts": entry["ts"],
                    "exit_ts": bar["ts"],
                    "direction": direction,
                    "entry_basis": entry["basis"],
                    "exit_basis": basis[i],
                    "entry_z": entry["z"],
                    "exit_z": z_val,
                    "result": exit_reason,
                    "gross": gross,
                    "cost": cost,
                    "net": gross - cost,
                    "sizes": sizes,
                })
                in_trade = False
                direction = None
                entry = None
                continue  # no entry on the close bar (canonical early return)

        if not in_trade:
            london_ok = LONDON_START_H_EST <= eh < LONDON_END_H_EST
            enough_time = (HARD_EXIT_H_EST - eh) * 60 >= MIN_MINUTES_TO_EXIT
            if london_ok and enough_time:
                if z_val > entry_z:
                    direction = "SHORT"
                elif z_val < -entry_z:
                    direction = "LONG"
                else:
                    continue
                ga_a, gn_a, an_a = atr["ga"][i], atr["gn"][i], atr["an"][i]
                s_ga = 1.0 / ga_a if ga_a > 0 else 1.0
                s_gn = 1.0 / gn_a if gn_a > 0 else 1.0
                s_an = 1.0 / an_a if an_a > 0 else 1.0
                total = s_ga + s_gn + s_an
                scale = MAX_TOTAL_LEVERAGE / total
                sizes = {"ga": s_ga * scale, "gn": s_gn * scale, "an": s_an * scale}
                entry = {
                    "ts": bar["ts"],
                    "basis": basis[i],
                    "z": z_val,
                    "sizes": sizes,
                    "ga": bar["ga"], "gn": bar["gn"], "an": bar["an"],
                }
                in_trade = True

    return trades, basis, z


def leg_pnl(entry, exit_bar, direction, sizes):
    """Per-leg pip PnL matching the canonical engine."""
    if direction == "SHORT":
        ga = (entry["ga"] - exit_bar["ga"]) / PIP * sizes["ga"]
        gn = (exit_bar["gn"] - entry["gn"]) / PIP * sizes["gn"]
        an = (entry["an"] - exit_bar["an"]) / PIP * sizes["an"]
    else:  # LONG
        ga = (exit_bar["ga"] - entry["ga"]) / PIP * sizes["ga"]
        gn = (entry["gn"] - exit_bar["gn"]) / PIP * sizes["gn"]
        an = (exit_bar["an"] - entry["an"]) / PIP * sizes["an"]
    return {"ga": ga, "gn": gn, "an": an}


def load_canonical_log():
    rows = []
    with open(HERE / "reference" / "canonical_trade_log.csv", newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def fmt(ts: datetime) -> str:
    return ts.strftime("%Y-%m-%d %H:%M:%S")


def verify(trades, canon, label):
    """Compare reimplementation trades against the canonical log."""
    n_canon = len(canon)
    n_mine = len(trades)
    entry_match = direction_match = exit_match = result_match = z_match = 0
    gross_match = cost_match = net_match = size_match = 0
    mismatches = []
    max_gross_diff = max_size_diff = 0.0
    for idx in range(min(n_canon, n_mine)):
        c = canon[idx]
        m = trades[idx]
        em = m["entry_ts"].strftime("%Y-%m-%d %H:%M:%S") == c["entry_time"]
        dm = m["direction"] == c["direction"]
        xm = m["exit_ts"].strftime("%Y-%m-%d %H:%M:%S") == c["exit_time"]
        rm = m["result"] == c["result"]
        zm = abs(m["entry_z"] - float(c["entry_zscore"])) < 1e-6
        gm = abs(m["gross"] - float(c["pnl_gross_pips"])) < 1e-6
        cm = abs(m["cost"] - float(c["pnl_costs_pips"])) < 1e-6
        nm = abs(m["net"] - float(c["pnl_net_pips"])) < 1e-6
        sm = (abs(m["sizes"]["ga"] - float(c["size_gbp_aud"])) < 1e-9 and
              abs(m["sizes"]["gn"] - float(c["size_gbp_nzd"])) < 1e-9 and
              abs(m["sizes"]["an"] - float(c["size_aud_nzd"])) < 1e-9)
        entry_match += em
        direction_match += dm
        exit_match += xm
        result_match += rm
        z_match += zm
        gross_match += gm
        cost_match += cm
        net_match += nm
        size_match += sm
        max_gross_diff = max(max_gross_diff, abs(m["gross"] - float(c["pnl_gross_pips"])))
        max_size_diff = max(max_size_diff, max(
            abs(m["sizes"]["ga"] - float(c["size_gbp_aud"])),
            abs(m["sizes"]["gn"] - float(c["size_gbp_nzd"])),
            abs(m["sizes"]["an"] - float(c["size_aud_nzd"]))))
        if not (em and dm and xm and rm and zm and gm and cm and nm and sm):
            mismatches.append({
                "idx": idx,
                "canon": {k: c[k] for k in ("entry_time", "exit_time", "direction", "result", "entry_zscore", "pnl_gross_pips", "pnl_net_pips")},
                "mine": {"entry_ts": m["entry_ts"].strftime("%Y-%m-%d %H:%M:%S"),
                         "exit_ts": m["exit_ts"].strftime("%Y-%m-%d %H:%M:%S"),
                         "direction": m["direction"], "result": m["result"],
                         "entry_z": m["entry_z"], "gross": m["gross"], "net": m["net"]},
            })
    first_div = mismatches[0] if mismatches else None
    return {
        "label": label,
        "canon_count": n_canon,
        "mine_count": n_mine,
        "count_match": n_canon == n_mine,
        "entry_time_match": entry_match,
        "direction_match": direction_match,
        "exit_time_match": exit_match,
        "result_match": result_match,
        "entry_z_match": int(z_match),
        "gross_pnl_match": gross_match,
        "cost_match": cost_match,
        "net_pnl_match": net_match,
        "size_match": size_match,
        "max_gross_diff": max_gross_diff,
        "max_size_diff": max_size_diff,
        "n_compared": min(n_canon, n_mine),
        "first_divergence": first_div,
    }


def main():
    import time
    t0 = time.time()
    bars = load_sync()
    print(f"synced bars: {len(bars)}  ({time.time()-t0:.1f}s)")
    print(f"data range: {bars[0]['ts']} .. {bars[-1]['ts']}")

    canon = load_canonical_log()
    print(f"canonical trade log: {len(canon)} trades")

    # CONTROL
    ctl_trades, _, _ = run_lifecycle(bars, 2.5, 0.0, 0.0, STOP_Z)
    ctl_res = verify(ctl_trades, canon, "CONTROL z2.5")

    # PRIMARY
    pri_trades, _, _ = run_lifecycle(bars, 3.0, -0.25, 0.25, STOP_Z)
    pri_res = {
        "label": "PRIMARY z3.0",
        "canon_count": 194,
        "mine_count": len(pri_trades),
        "count_match": len(pri_trades) == 194,
    }

    out = {
        "checkpoint": "SW-CTBT-T1.1-REFERENCE-PARITY-AND-GATE-ENFORCEMENT-REPAIR",
        "reference": "AUD_GBP_NZD",
        "canonical_symbols": CANONICAL_SYMBOLS,
        "data_files": CANONICAL_FILES,
        "synced_bars": len(bars),
        "data_start": str(bars[0]["ts"]),
        "data_end": str(bars[-1]["ts"]),
        "control": ctl_res,
        "primary": pri_res,
    }

    print(json.dumps(ctl_res, indent=2, default=str))
    print(json.dumps(pri_res, indent=2, default=str))

    (HERE / "CTBT_T11_REFERENCE_EVENT_PARITY_RAW.json").write_text(
        json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("\nwrote CTBT_T11_REFERENCE_EVENT_PARITY_RAW.json")


if __name__ == "__main__":
    main()
