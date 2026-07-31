"""
DMR Proper Sweep Backtest — Multi-Pair
=========================================
Fixes 3 critical bugs from old CSV backtest:
  1. DS touch direction (low<=DS for bull, high>=DS for bear) — was inverted
  2. Entry at ds_bar['close'] — was at DS level (limit)
  3. Per-asset P90 thresholds from asset_configs.py — was hardcoded EURUSD

Matches MT5 EA logic that produced 91.9% WR on USDCHF.
"""

import csv, sys, os, json
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from pathlib import Path

WORKSPACE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")

# ─── Asset Config ───────────────────────────────────────────
PIP_SIZES = {
    "EURUSD": 0.0001, "GBPUSD": 0.0001, "USDCHF": 0.0001,
    "USDJPY": 0.01,   "AUDUSD": 0.0001, "NZDUSD": 0.0001,
    "USDCAD": 0.0001, "EURGBP": 0.0001, "EURJPY": 0.01,
    "GBPJPY": 0.01,   "AUDJPY": 0.01,   "CHFJPY": 0.01,
    "AUDNZD": 0.0001, "EURAUD": 0.0001, "EURCHF": 0.0001,
    "GBPCHF": 0.0001, "GBPAUD": 0.0001, "GBPNZD": 0.0001,
    "NZDCHF": 0.0001, "NZDJPY": 0.01,   "CADJPY": 0.01,
    "AUDCAD": 0.0001, "AUDCHF": 0.0001, "CADCHF": 0.0001,
    "EURNZD": 0.0001, "NZDCAD": 0.0001,
    "BTCUSD": 1.0,     "ETHUSD": 0.01,   "XAUUSD": 0.1,
    "XAGUSD": 0.001,  "US500": 1.0,     "USTEC100": 1.0,
}

# Per-asset P90 thresholds (from asset_configs.py)
P90_THRESHOLDS = {
    "EURUSD": 4.6,  "GBPUSD": 5.98, "USDCHF": 5.06,
    "USDJPY": 7.36, "AUDUSD": 5.06, "NZDUSD": 6.44,
    "USDCAD": 5.0,  "EURGBP": 3.36, "EURJPY": 6.0,
    "GBPJPY": 9.12, "AUDJPY": 6.0,  "CHFJPY": 6.72,
    "AUDNZD": 5.0,  "EURAUD": 5.0,  "EURCHF": 4.5,
    "GBPCHF": 8.64, "GBPAUD": 10.08,"GBPNZD": 11.52,
    "NZDCHF": 5.0,  "NZDJPY": 6.0,  "CADJPY": 6.0,
    "AUDCAD": 5.0,  "AUDCHF": 5.0,  "CADCHF": 5.0,
    "EURNZD": 5.0,  "NZDCAD": 5.0,
    "BTCUSD": 50.0,  "ETHUSD": 5.0,   "XAUUSD": 5.0,
    "XAGUSD": 0.5,  "US500": 8.0,    "USTEC100": 8.0,
}

# CSV file mapping
CSV_FILES = {
    "EURUSD": "quant-lab/data/EURUSDPRO_M5_2023_2026.csv",
    "USDCHF": "quant-lab/data/USDCHFPRO_M5.csv",
    "GBPUSD": "quant-lab/data/GBPUSD_M5.csv",
    "USDJPY": "quant-lab/data/USDJPY_M5.csv",
    "AUDUSD": "quant-lab/data/AUDUSD_M5.csv",
    "NZDUSD": "quant-lab/data/NZDUSD_M5.csv",
    "USDCAD": "quant-lab/data/USDCAD_PRO_M5.csv",
    "EURGBP": "quant-lab/data/EURGBP_PRO_M5.csv",
    "EURJPY": "quant-lab/data/EURJPY_PRO_M5.csv",
    "GBPJPY": "quant-lab/data/GBPJPY_M5.csv",
    "AUDJPY": "quant-lab/data/AUDJPY_PRO_M5.csv",
    "CHFJPY": "quant-lab/data/CHFJPY_M5.csv",
    "AUDNZD": "quant-lab/data/AUDNZD_PRO_M5.csv",
    "EURAUD": "quant-lab/data/EURAUD_PRO_M5.csv",
    "EURCHF": "quant-lab/data/EURCHF_PRO_M5.csv",
    "GBPCHF": "quant-lab/data/GBPCHF_M5.csv",
    "GBPAUD": "quant-lab/data/GBPAUD_M5.csv",
    "GBPNZD": "quant-lab/data/GBPNZD_M5.csv",
    "NZDCHF": "quant-lab/data/NZDCHF_PRO_M5.csv",
    "NZDJPY": "quant-lab/data/NZDJPY_PRO_M5.csv",
    "CADJPY": "quant-lab/data/CADJPY_PRO_M5.csv",
    "AUDCAD": "quant-lab/data/AUDCAD_PRO_M5.csv",
    "AUDCHF": "quant-lab/data/AUDCHF_PRO_M5.csv",
    "CADCHF": "quant-lab/data/CADCHF_PRO_M5.csv",
    "EURNZD": "quant-lab/data/EURNZD_PRO_M5.csv",
    "NZDCAD": "quant-lab/data/NZDCAD_PRO_M5.csv",
    "BTCUSD": "quant-lab/data/BTCUSD_M5.csv",
    "ETHUSD": "quant-lab/data/ETHUSD_M5.csv",
    "XAUUSD": "quant-lab/data/XAUUSD_M5.csv",
    "XAGUSD": "quant-lab/data/XAGUSD_M5.csv",
    "US500": "quant-lab/data/US500_M5.csv",
}

# DMR Parameters (matching MT5 EA)
DEEP_MULT = 2.0
KILL_MULT = 2.2
MIN_AR = 3.0
MAX_AR = 50.0
ASIAN_START_H = 19
ASIAN_END_H = 3
TRADING_START_H = 2
TRADING_END_H = 11
DS_SCAN_END_H = 12   # MT5 EA scans for DS touch until noon
HARD_EXIT_H = 17

EST = timezone(timedelta(hours=-5))


def load_csv(path):
    bars = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ts_raw = row.get("timestamp") or row.get("time")
                if not ts_raw:
                    continue
                # Handle both Unix epoch and datetime string formats
                try:
                    ts = datetime.fromtimestamp(int(float(ts_raw)), tz=EST)
                except (ValueError, OSError):
                    # Try parsing as datetime string
                    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"]:
                        try:
                            dt_naive = datetime.strptime(ts_raw.strip(), fmt)
                            ts = dt_naive.replace(tzinfo=EST)
                            break
                        except ValueError:
                            continue
                    else:
                        continue
                o = float(row.get("open") or row.get("Open"))
                h = float(row.get("high") or row.get("High"))
                lo = float(row.get("low") or row.get("Low"))
                c = float(row.get("close") or row.get("Close"))
                bars.append({"ts": ts, "est_h": ts.hour, "o": o, "h": h, "l": lo, "c": c})
            except (ValueError, KeyError):
                continue
    bars.sort(key=lambda b: b["ts"])
    return bars


def session_date(dt):
    h = dt.hour
    if h >= ASIAN_START_H:
        return (dt + timedelta(days=1)).date()
    return dt.date()


def pips_to_price(pips, pip_size):
    return pips * pip_size


def price_to_pips(price_diff, pip_size):
    return price_diff / pip_size


def run_dmr(bars, pip_size, p90_threshold, symbol):
    days = defaultdict(list)
    for bar in bars:
        sd = session_date(bar["ts"])
        days[sd].append(bar)

    trades = []

    for sd in sorted(days.keys()):
        day_bars = sorted(days[sd], key=lambda b: b["ts"])
        if len(day_bars) < 5:
            continue

        # Asian Range
        ah, al = 0.0, 99999.0
        ar_locked = False
        skip_day = False
        for b in day_bars:
            if b["est_h"] >= ASIAN_START_H or b["est_h"] < ASIAN_END_H:
                ah = max(ah, b["h"])
                al = min(al, b["l"])
            if b["est_h"] == ASIAN_END_H and not ar_locked:
                ar_locked = True
                if ah > 0 and al < 99999:
                    ar_pips = price_to_pips(ah - al, pip_size)
                    if ar_pips < MIN_AR or ar_pips > MAX_AR:
                        skip_day = True
                break
        if skip_day:
            continue

        # Trading window
        trading = [b for b in day_bars if TRADING_START_H <= b["est_h"] < TRADING_END_H]
        if not trading:
            continue

        # P90 scan
        p90_found = False
        p90_dir = 0
        activation = 0.0
        body_pips = 0.0
        p90_idx = -1

        for i, b in enumerate(trading):
            body = abs(b["c"] - b["o"])
            bp = price_to_pips(body, pip_size)
            if bp >= p90_threshold:
                p90_found = True
                p90_dir = 1 if b["c"] > b["o"] else -1
                activation = b["c"]
                body_pips = bp
                p90_idx = i
                break

        if not p90_found:
            continue

        # Deep State & Kill Switch
        ds = activation + pips_to_price(body_pips * DEEP_MULT, pip_size) * p90_dir
        ks = activation + pips_to_price(body_pips * KILL_MULT, pip_size) * p90_dir

        # DS Touch Detection (FIXED: correct direction)
        ds_touched = False
        ds_bar = None
        for b in trading[p90_idx + 1:]:
            if b["est_h"] >= DS_SCAN_END_H:
                break
            if p90_dir == 1 and b["l"] <= ds:  # Bull P90 → DS above → price retraces DOWN
                ds_touched = True
                ds_bar = b
                break
            if p90_dir == -1 and b["h"] >= ds:  # Bear P90 → DS below → price retraces UP
                ds_touched = True
                ds_bar = b
                break

        if not ds_touched:
            continue

        # Entry at ds_bar close (FIXED: not at DS level)
        is_short = (p90_dir == 1)
        entry_price = ds_bar["c"]

        # Validate geometry
        if is_short:
            if activation >= entry_price or ks <= entry_price:
                continue
        else:
            if activation <= entry_price or ks >= entry_price:
                continue

        # Simulate trade
        pnl_pips = 0.0
        result = "UNKNOWN"

        for tb in day_bars:
            if tb["ts"] <= ds_bar["ts"]:
                continue
            if tb["est_h"] >= HARD_EXIT_H:
                if is_short:
                    pnl_pips = price_to_pips(entry_price - tb["c"], pip_size)
                else:
                    pnl_pips = price_to_pips(tb["c"] - entry_price, pip_size)
                result = "HARD_EXIT"
                break
            if is_short:
                if tb["l"] <= activation:
                    pnl_pips = price_to_pips(entry_price - activation, pip_size)
                    result = "TP"
                    break
                if tb["h"] >= ks:
                    pnl_pips = price_to_pips(entry_price - ks, pip_size)
                    result = "SL"
                    break
            else:
                if tb["h"] >= activation:
                    pnl_pips = price_to_pips(activation - entry_price, pip_size)
                    result = "TP"
                    break
                if tb["l"] <= ks:
                    pnl_pips = price_to_pips(ks - entry_price, pip_size)
                    result = "SL"
                    break
        else:
            last = day_bars[-1]
            pnl_pips = price_to_pips(entry_price - last["c"], pip_size) if is_short else price_to_pips(last["c"] - entry_price, pip_size)
            result = "EOD"

        trades.append({
            "date": str(sd),
            "result": result,
            "pnl": round(pnl_pips, 1),
            "dir": "SHORT" if is_short else "LONG",
            "body": round(body_pips, 1),
            "est_h": ds_bar["est_h"],
            "entry": round(entry_price, 8),
            "sl": round(ks, 8),
            "tp": round(activation, 8),
        })

    return trades, compute_stats(trades)


def compute_stats(trades):
    if not trades:
        return {"total": 0, "wr": 0, "pf": 0, "pnl": 0}

    pnls = [t["pnl"] for t in trades]
    n = len(pnls)
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]

    total_pnl = sum(pnls)
    gross_profit = sum(wins) if wins else 0
    gross_loss = abs(sum(losses)) if losses else 0.001
    wr = len(wins) / n * 100 if n > 0 else 0
    pf = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    eq = peak = max_dd = 0
    for p in pnls:
        eq += p
        if eq > peak:
            peak = eq
        dd = peak - eq
        if dd > max_dd:
            max_dd = dd

    cw = cl = mcw = mcl = 0
    for p in pnls:
        if p > 0:
            cw += 1
            cl = 0
            mcw = max(mcw, cw)
        elif p < 0:
            cl += 1
            cw = 0
            mcl = max(mcl, cl)

    tp_count = sum(1 for t in trades if t["result"] == "TP")
    sl_count = sum(1 for t in trades if t["result"] == "SL")
    he_count = sum(1 for t in trades if t["result"] == "HARD_EXIT")
    eod_count = sum(1 for t in trades if t["result"] == "EOD")

    return {
        "total": n,
        "wins": len(wins),
        "losses": len(losses),
        "wr": round(wr, 1),
        "pnl": round(total_pnl, 1),
        "pf": round(pf, 2),
        "avg_trade": round(total_pnl / n, 2),
        "avg_win": round(sum(wins) / len(wins), 1) if wins else 0,
        "avg_loss": round(sum(losses) / len(losses), 1) if losses else 0,
        "max_dd": round(max_dd, 1),
        "tp": tp_count,
        "sl": sl_count,
        "hard_exit": he_count,
        "eod": eod_count,
        "max_consec_wins": mcw,
        "max_consec_losses": mcl,
    }


def main():
    print("=" * 70)
    print("DMR PROPER SWEEP BACKTEST — Multi-Pair")
    print("Fixed: DS touch direction, entry price, per-asset P90")
    print("=" * 70)

    all_results = {}

    for symbol, csv_rel in sorted(CSV_FILES.items()):
        csv_path = WORKSPACE / csv_rel
        if not csv_path.exists():
            print(f"[SKIP] {symbol} — no data file")
            continue

        pip_size = PIP_SIZES.get(symbol, 0.0001)
        p90_thresh = P90_THRESHOLDS.get(symbol, 5.0)

        bars = load_csv(str(csv_path))
        if len(bars) < 100:
            print(f"[SKIP] {symbol} — only {len(bars)} bars")
            continue

        trades, stats = run_dmr(bars, pip_size, p90_thresh, symbol)
        all_results[symbol] = stats

        if stats["total"] == 0:
            print(f"[----] {symbol:10s} | 0 trades | P90={p90_thresh}p | {len(bars):,} bars")
        else:
            status = "OK" if stats["wr"] >= 70 else "LO" if stats["wr"] >= 40 else "XX"
            print(f"[{status}] {symbol:10s} | {stats['total']:4d} tr | "
                  f"WR={stats['wr']:5.1f}% | PF={stats['pf']:6.2f} | "
                  f"PnL={stats['pnl']:+8.1f}p | MaxDD={stats['max_dd']:6.1f}p | "
                  f"TP={stats['tp']} SL={stats['sl']} HE={stats['hard_exit']}")

    # Summary Table
    print("\n" + "=" * 70)
    print("MASTER DMR SWEEP SUMMARY")
    print("=" * 70)
    print(f"{'Pair':<10} {'Trades':>6} {'WR%':>6} {'PF':>7} {'PnL':>9} {'MaxDD':>7} {'TP':>4} {'SL':>4} {'HE':>4}")
    print("-" * 70)

    for symbol in sorted(all_results.keys()):
        s = all_results[symbol]
        if s["total"] == 0:
            continue
        print(f"{symbol:<10} {s['total']:6d} {s['wr']:6.1f} {s['pf']:7.2f} "
              f"{s['pnl']:+9.1f} {s['max_dd']:7.1f} {s['tp']:4d} {s['sl']:4d} {s['hard_exit']:4d}")

    # Save JSON
    out_path = WORKSPACE / "quant-lab" / "reports" / "dmr_proper_sweep_results.json"
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to: {out_path}")


if __name__ == "__main__":
    main()
