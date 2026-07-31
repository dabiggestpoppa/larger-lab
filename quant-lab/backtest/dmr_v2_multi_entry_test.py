"""
DMR v2 Multi-Entry Backtest Test
===================================
Tests: Multiple P90 entries per day (one per 2-hour window)
Rolls the chain: after first P90 fires, look for next one in next window
Removes AR filter (analog to what ST sweep did)

This is a BACKTEST test — does NOT touch live engine.
"""
import csv, sys, os, json
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from pathlib import Path
import numpy as np

WORKSPACE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")

PIP_SIZES = {
    "EURUSD": 0.0001, "GBPUSD": 0.0001, "USDCHF": 0.0001,
    "USDJPY": 0.01, "AUDUSD": 0.0001, "NZDUSD": 0.0001,
    "USDCAD": 0.0001, "EURGBP": 0.0001, "EURJPY": 0.01,
    "GBPJPY": 0.01, "AUDJPY": 0.01, "CHFJPY": 0.01,
    "AUDNZD": 0.0001, "EURAUD": 0.0001, "EURCHF": 0.0001,
    "GBPCHF": 0.0001, "GBPAUD": 0.0001, "GBPNZD": 0.0001,
    "NZDCHF": 0.0001, "NZDJPY": 0.01, "CADJPY": 0.01,
    "AUDCAD": 0.0001, "AUDCHF": 0.0001, "CADCHF": 0.0001,
    "EURNZD": 0.0001, "NZDCAD": 0.0001,
    "BTCUSD": 1.0, "ETHUSD": 0.01, "XAUUSD": 0.1,
    "XAGUSD": 0.001, "US500": 1.0,
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

# DMR Parameters
DEEP_MULT = 2.0
KILL_MULT = 2.2
MIN_AR = 3.0
MAX_AR = 45.0
ASIAN_START_H = 19
ASIAN_END_H = 3
TRADING_START_H = 2
TRADING_END_H = 11
DS_SCAN_END_H = 12
HARD_EXIT_H = 17

EST = timezone(timedelta(hours=-5))

# 2-hour P90 windows (from manual)
P90_WINDOWS = [
    (2, 4, 4.1),   # 2-4 AM >= 4.1 pips
    (4, 6, 4.6),   # 4-6 AM >= 4.6 pips
    (6, 8, 4.6),   # 6-8 AM >= 4.6 pips
    (8, 10, 5.9),  # 8-10 AM >= 5.9 pips
    (10, 11, 6.2), # 10-11 AM >= 6.2 pips
]


def load_csv(path):
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
    if dt.hour >= ASIAN_START_H:
        return (dt + timedelta(days=1)).date()
    return dt.date()


def price_to_pips(price_diff, pip_size):
    return price_diff / pip_size


def pips_to_price(pips, pip_size):
    return pips * pip_size


def get_p90_threshold(est_hour):
    """Get P90 threshold for a specific hour using 2-hour windows."""
    for start, end, threshold in P90_WINDOWS:
        if start <= est_hour < end:
            return threshold
    return 999.0


def run_dmr_v2(bars, pip_size, symbol):
    """Run DMR v2 with multi-entry: one P90 per 2-hour window."""
    days = defaultdict(list)
    for bar in bars:
        sd = session_date(bar["ts"])
        days[sd].append(bar)
    
    all_trades = []
    
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
        
        # ─── Multi-Entry: Scan each 2-hour window for P90 ───
        # Track which windows have fired
        windows_fired = set()
        open_trades = []  # Track open trades for this day
        
        for window_start, window_end, window_threshold in P90_WINDOWS:
            if window_start in windows_fired:
                continue
            
            # Get bars in this window
            window_bars = [b for b in day_bars if window_start <= b["est_h"] < window_end]
            if not window_bars:
                continue
            
            # Find P90 in this window
            p90_found = False
            p90_dir = 0
            activation = 0.0
            body_pips = 0.0
            p90_idx = -1
            
            for i, b in enumerate(window_bars):
                body = abs(b["c"] - b["o"])
                bp = price_to_pips(body, pip_size)
                threshold = get_p90_threshold(b["est_h"])
                if bp >= threshold:
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
            
            # DS Touch: scan forward from P90 time
            ds_touched = False
            ds_bar = None
            for b in day_bars:
                if b["ts"] <= window_bars[p90_idx]["ts"]:
                    continue
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
            
            # Validate geometry
            is_short = (p90_dir == 1)
            entry_price = ds
            
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
            
            if result == "UNKNOWN":
                last = day_bars[-1]
                pnl_pips = price_to_pips(entry_price - last["c"], pip_size) if is_short else price_to_pips(last["c"] - entry_price, pip_size)
                result = "EOD"
            
            windows_fired.add(window_start)
            
            all_trades.append({
                "date": str(sd),
                "result": result,
                "pnl": round(pnl_pips, 1),
                "dir": "SHORT" if is_short else "LONG",
                "body": round(body_pips, 1),
                "window": f"{window_start}-{window_start+2}h",
            })
    
    return all_trades


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
    wr = len(wins) / n * 100
    pf = gross_profit / gross_loss
    
    tp_count = sum(1 for t in trades if t["result"] == "TP")
    sl_count = sum(1 for t in trades if t["result"] == "SL")
    he_count = sum(1 for t in trades if t["result"] == "HARD_EXIT")
    
    return {
        "total": n,
        "wins": len(wins),
        "losses": len(losses),
        "wr": round(wr, 1),
        "pnl": round(total_pnl, 1),
        "pf": round(pf, 2),
        "tp": tp_count,
        "sl": sl_count,
        "hard_exit": he_count,
    }


def main():
    print("=" * 80)
    print("DMR v2 MULTI-ENTRY BACKTEST TEST")
    print("One P90 per 2-hour window, rolls the chain")
    print("=" * 80)
    
    all_results = {}
    
    for symbol, csv_rel in sorted(CSV_FILES.items()):
        csv_path = WORKSPACE / csv_rel
        if not csv_path.exists():
            continue
        
        pip_size = PIP_SIZES.get(symbol, 0.0001)
        bars = load_csv(str(csv_path))
        if len(bars) < 100:
            continue
        
        trades = run_dmr_v2(bars, pip_size, symbol)
        stats = compute_stats(trades)
        all_results[symbol] = stats
        
        if stats["total"] == 0:
            print(f"[----] {symbol:10s} | 0 trades")
        else:
            status = "OK" if stats["wr"] >= 70 else "LO" if stats["wr"] >= 40 else "XX"
            print(f"[{status}] {symbol:10s} | {stats['total']:4d} tr | "
                  f"WR={stats['wr']:5.1f}% | PF={stats['pf']:6.2f} | "
                  f"PnL={stats['pnl']:+8.1f}p | TP={stats['tp']} SL={stats['sl']} HE={stats['hard_exit']}")
    
    # Summary
    print("\n" + "=" * 80)
    print("COMPARISON: v1 (single entry) vs v2 (multi-entry)")
    print("=" * 80)
    
    total_v2 = sum(s["total"] for s in all_results.values())
    total_pnl_v2 = sum(s["pnl"] for s in all_results.values())
    total_wins_v2 = sum(s["wins"] for s in all_results.values())
    total_wr_v2 = total_wins_v2 / total_v2 * 100 if total_v2 > 0 else 0
    
    print(f"v2 Total: {total_v2} trades | WR={total_wr_v2:.1f}% | PnL={total_pnl_v2:+10.1f}p")
    
    # Save results
    out_path = WORKSPACE / "quant-lab" / "reports" / "dmr_v2_multi_entry_results.json"
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to: {out_path}")


if __name__ == "__main__":
    main()
