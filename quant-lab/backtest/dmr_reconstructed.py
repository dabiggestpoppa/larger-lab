"""
DMR Reconstructed Backtest — Full Strategy Per CEREBUS Manual
================================================================
Strategy B: Deep Mean Rebalancing (Resolution Output Stall Play)

Reconstructed from:
  - CEREBUS FX v4.0 Manual (Strategy B, pages 8-9)
  - USDCHF MT5 EA backtest (91.9% WR, 804 trades, PF 131.9)
  - USDCHF live executor (per-hour P90 calibration)

Key Specifications from Manual:
  Entry: LIMIT ORDER at 200% Deep State Level
  SL: 8 pips beyond 200% (~220% extension)
  TP1: Return to 0% (P90 activation close)
  TP2: -50% Daily Range
  R:R: 1:5 to 1:7
  Filter: Before 12PM EST, -50% target NOT hit, AR < 45p

P90 Windows (2-hour, from manual for EURUSD):
  2-4 AM: >= 4.1p | 4-6 AM: >= 4.6p | 6-8 AM: >= 4.6p
  8-10 AM: >= 5.9p | 10-11 AM: >= 6.2p

Per-asset calibration: compute_p90_per_hour() from each pair's own data
"""

import csv, sys, os, json, numpy as np
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

# DMR Parameters (from CEREBUS manual)
DEEP_MULT = 2.0      # 200% Deep State
KILL_MULT = 2.2      # 220% = ~8 pips beyond 200%
MIN_AR = 3.0
MAX_AR = 45.0        # AR > 45p = NO-GO (constraint deficit too wide)
ASIAN_START_H = 19
ASIAN_END_H = 3
TRADING_START_H = 2
TRADING_END_H = 11
DS_SCAN_END_H = 12   # Must touch DS before noon
HARD_EXIT_H = 17

# P90 2-hour windows (EURUSD master reference from manual)
P90_WINDOWS = [
    (2, 4, 4.1),   # 2-4 AM >= 4.1 pips
    (4, 6, 4.6),   # 4-6 AM >= 4.6 pips
    (6, 8, 4.6),   # 6-8 AM >= 4.6 pips
    (8, 10, 5.9),  # 8-10 AM >= 5.9 pips
    (10, 11, 6.2), # 10-11 AM >= 6.2 pips
]

EST = timezone(timedelta(hours=-5))


def load_csv(path):
    """Load M5 bars from CSV. Handles both Unix epoch and datetime string formats."""
    bars = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ts_raw = row.get("timestamp") or row.get("time")
                if not ts_raw:
                    continue
                try:
                    ts = datetime.fromtimestamp(int(float(ts_raw)), tz=EST)
                except (ValueError, OSError):
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


def price_to_pips(price_diff, pip_size):
    return price_diff / pip_size


def pips_to_price(pips, pip_size):
    return pips * pip_size


def get_p90_threshold_eurusd(est_hour):
    """EURUSD 2-hour window P90 thresholds from CEREBUS manual."""
    for start, end, threshold in P90_WINDOWS:
        if start <= est_hour < end:
            return threshold
    return 999.0  # Outside activation window


def compute_p90_per_hour(bars, pip_size):
    """Compute per-hour P90 thresholds from each pair's own data.
    Uses 2-hour windows matching the CEREBUS manual structure.
    Returns dict: {est_hour: threshold_in_pips}
    """
    hourly_bodies = defaultdict(list)
    for b in bars:
        body_pips = price_to_pips(abs(b["c"] - b["o"]), pip_size)
        hourly_bodies[b["est_h"]].append(body_pips)
    
    hourly_p90 = {}
    for h in range(2, 11):
        if len(hourly_bodies[h]) >= 20:
            hourly_p90[h] = round(np.percentile(hourly_bodies[h], 90), 1)
        else:
            hourly_p90[h] = None
    
    return hourly_p90


def get_p90_threshold(est_hour, hourly_p90, fallback):
    """Get P90 for specific hour, with fallback chain."""
    if est_hour in hourly_p90 and hourly_p90[est_hour] is not None:
        return hourly_p90[est_hour]
    # Use nearest hour with data
    for offset in range(1, 9):
        for candidate in [est_hour - offset, est_hour + offset]:
            if candidate in hourly_p90 and hourly_p90[candidate] is not None:
                return hourly_p90[candidate]
    return fallback


def run_dmr(bars, pip_size, p90_threshold_fallback, symbol):
    """Run DMR backtest on single pair with full manual specification."""
    
    # Step 1: Compute per-hour P90 calibration from this pair's data
    hourly_p90 = compute_p90_per_hour(bars, pip_size)
    
    # Group by session date
    days = defaultdict(list)
    for bar in bars:
        sd = session_date(bar["ts"])
        days[sd].append(bar)
    
    trades = []
    
    for sd in sorted(days.keys()):
        day_bars = sorted(days[sd], key=lambda b: b["ts"])
        if len(day_bars) < 5:
            continue
        
        # ─── Asian Range ───
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
        
        # ─── Trading window ───
        trading = [b for b in day_bars if TRADING_START_H <= b["est_h"] < TRADING_END_H]
        if not trading:
            continue
        
        # ─── P90 scan with per-hour calibration ───
        p90_found = False
        p90_dir = 0
        activation = 0.0
        body_pips = 0.0
        p90_idx = -1
        
        for i, b in enumerate(trading):
            body = abs(b["c"] - b["o"])
            bp = price_to_pips(body, pip_size)
            threshold = get_p90_threshold(b["est_h"], hourly_p90, p90_threshold_fallback)
            if bp >= threshold:
                p90_found = True
                p90_dir = 1 if b["c"] > b["o"] else -1
                activation = b["c"]
                body_pips = bp
                p90_idx = i
                break
        
        if not p90_found:
            continue
        
        # ─── Deep State (200%) and Kill Switch (220%) ───
        ds = activation + pips_to_price(body_pips * DEEP_MULT, pip_size) * p90_dir
        ks = activation + pips_to_price(body_pips * KILL_MULT, pip_size) * p90_dir
        
        # ─── DS Touch Detection (correct direction per manual) ───
        # Bull P90: DS is ABOVE → price must retrace DOWN → check low <= ds
        # Bear P90: DS is BELOW → price must retrace UP → check high >= ds
        ds_touched = False
        ds_bar = None
        for b in trading[p90_idx + 1:]:
            if b["est_h"] >= DS_SCAN_END_H:
                break
            if p90_dir == 1 and b["l"] <= ds:
                ds_touched = True
                ds_bar = b
                break
            if p90_dir == -1 and b["h"] >= ds:
                ds_touched = True
                ds_bar = b
                break
        
        if not ds_touched:
            continue
        
        # ─── Entry: LIMIT ORDER at DS level (per manual) ───
        is_short = (p90_dir == 1)  # Bull P90 → DMR SHORT
        entry_price = ds  # LIMIT ORDER at 200% Deep State Level
        
        # Validate geometry
        if is_short:
            if activation >= entry_price or ks <= entry_price:
                continue
        else:
            if activation <= entry_price or ks >= entry_price:
                continue
        
        # ─── Simulate trade ───
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
                # TP: price falls back to origin (activation = P90 close)
                if tb["l"] <= activation:
                    pnl_pips = price_to_pips(entry_price - activation, pip_size)
                    result = "TP"
                    break
                # SL: price rises to kill switch (220%)
                if tb["h"] >= ks:
                    pnl_pips = price_to_pips(entry_price - ks, pip_size)
                    result = "SL"
                    break
            else:
                # LONG: TP when price rises to origin
                if tb["h"] >= activation:
                    pnl_pips = price_to_pips(activation - entry_price, pip_size)
                    result = "TP"
                    break
                # SL: price falls to kill switch
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
    
    return trades, compute_stats(trades), hourly_p90


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
    print("=" * 80)
    print("DMR RECONSTRUCTED BACKTEST — Full Strategy Per CEREBUS Manual")
    print("Entry: LIMIT at 200% DS | SL: 220% | TP: return to activation")
    print("P90: per-hour calibration from each pair's own data")
    print("=" * 80)
    
    all_results = {}
    all_p90 = {}
    
    for symbol, csv_rel in sorted(CSV_FILES.items()):
        csv_path = WORKSPACE / csv_rel
        if not csv_path.exists():
            print(f"[SKIP] {symbol} — no data file")
            continue
        
        pip_size = PIP_SIZES.get(symbol, 0.0001)
        # Use EURUSD manual thresholds as fallback
        p90_fallback = get_p90_threshold_eurusd(3)  # 4.1p as minimum fallback
        
        bars = load_csv(str(csv_path))
        if len(bars) < 100:
            print(f"[SKIP] {symbol} — only {len(bars)} bars")
            continue
        
        trades, stats, hourly_p90 = run_dmr(bars, pip_size, p90_fallback, symbol)
        all_results[symbol] = stats
        all_p90[symbol] = hourly_p90
        
        if stats["total"] == 0:
            p90_str = ", ".join(f"{h}:{hourly_p90.get(h, 'N/A')}" for h in range(2, 11))
            print(f"[----] {symbol:10s} | 0 trades | P90=[{p90_str}]")
        else:
            status = "OK" if stats["wr"] >= 70 else "LO" if stats["wr"] >= 40 else "XX"
            print(f"[{status}] {symbol:10s} | {stats['total']:4d} tr | "
                  f"WR={stats['wr']:5.1f}% | PF={stats['pf']:6.2f} | "
                  f"PnL={stats['pnl']:+8.1f}p | MaxDD={stats['max_dd']:6.1f}p | "
                  f"TP={stats['tp']} SL={stats['sl']} HE={stats['hard_exit']}")
    
    # ─── Summary Table ───
    print("\n" + "=" * 80)
    print("MASTER DMR RECONSTRUCTED SUMMARY")
    print("=" * 80)
    print(f"{'Pair':<10} {'Trades':>6} {'WR%':>6} {'PF':>7} {'PnL':>9} {'MaxDD':>7} "
          f"{'TP':>4} {'SL':>4} {'HE':>4} {'AvgW':>5} {'AvgL':>5}")
    print("-" * 80)
    
    for symbol in sorted(all_results.keys()):
        s = all_results[symbol]
        if s["total"] == 0:
            continue
        print(f"{symbol:<10} {s['total']:6d} {s['wr']:6.1f} {s['pf']:7.2f} "
              f"{s['pnl']:+9.1f} {s['max_dd']:7.1f} {s['tp']:4d} {s['sl']:4d} {s['hard_exit']:4d} "
              f"{s['avg_win']:5.1f} {s['avg_loss']:5.1f}")
    
    # ─── P90 Calibration Table ───
    print("\n" + "=" * 80)
    print("P90 PER-HOUR CALIBRATION (90th percentile from each pair's data)")
    print("=" * 80)
    print(f"{'Pair':<10} {'2AM':>5} {'3AM':>5} {'4AM':>5} {'5AM':>5} {'6AM':>5} "
          f"{'7AM':>5} {'8AM':>5} {'9AM':>5} {'10AM':>5}")
    print("-" * 80)
    
    for symbol in sorted(all_p90.keys()):
        p90 = all_p90[symbol]
        vals = [str(p90.get(h, "--"))[:4] for h in range(2, 11)]
        print(f"{symbol:<10} {vals[0]:>5} {vals[1]:>5} {vals[2]:>5} {vals[3]:>5} {vals[4]:>5} "
              f"{vals[5]:>5} {vals[6]:>5} {vals[7]:>5} {vals[8]:>5}")
    
    # Save JSON
    out_path = WORKSPACE / "quant-lab" / "reports" / "dmr_reconstructed_results.json"
    with open(out_path, "w") as f:
        json.dump({"results": all_results, "p90_calibration": {k: {str(k2): v2 for k2, v2 in v.items()} for k, v in all_p90.items()}}, f, indent=2, default=str)
    print(f"\nResults saved to: {out_path}")


if __name__ == "__main__":
    main()
