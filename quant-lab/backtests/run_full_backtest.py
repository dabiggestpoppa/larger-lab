#!/usr/bin/env python3
"""
P90 Cascade Activation — Full Backtest
=======================================
Runs on full dataset (249K bars) with fixed TP logic.
"""
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd
import numpy as np


# ═══════════════════════════════════════════════════════════════════════════════
# Config
# ═══════════════════════════════════════════════════════════════════════════════

class Cfg:
    asian_start_est = 19
    asian_end_est = 3
    entry_start_est = 2
    entry_end_est = 11
    hard_exit_est = 12

    p90_thresholds = {
        (2, 4): 4.1, (4, 6): 4.6, (6, 8): 4.6,
        (8, 10): 5.9, (10, 11): 6.2,
    }
    p90_body_pct = 0.60

    max_cascades = 3
    cascade_window_min = 30
    cascade_window_max = 120
    cascade_sl_mult = 1.68
    cascade_size_1 = 0.20
    cascade_size_2 = 0.10

    add_time_minutes = 45
    add_time_window = 10
    add_extension_pips = 8.0
    add_size = 0.30

    initial_size = 0.40
    initial_sl_mult = 0.80

    hold_time_minutes = 120
    kill_switch_pct = 1.32
    tp2_pct = 0.50
    position_size_lots = 0.1


def to_pips(pd): return pd * 10000
def to_price(pips): return pips / 10000
def utc_to_est(uh): return (uh - 5 + 24) % 24


def parse_csv(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        raw = f.readlines()
    records = []
    for line in raw[1:]:
        parts = line.strip().split()
        if len(parts) < 7: continue
        try:
            ts = datetime.strptime(f"{parts[0]} {parts[1]}", "%Y.%m.%d %H:%M:%S")
            records.append({"timestamp": ts, "open": float(parts[2]),
                           "high": float(parts[3]), "low": float(parts[4]),
                           "close": float(parts[5])})
        except: continue
    df = pd.DataFrame(records)
    df.set_index("timestamp", inplace=True)
    df.sort_index(inplace=True)
    return df


def run_backtest(df, cfg):
    df = df.copy()
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    df["est_hour"] = df.index.hour.map(utc_to_est)
    df["date"] = df.index.date

    ah = None; al = None; ar_pips = None
    ar_complete = False; tier = "NA"
    sess_dir = None; init_time = None; init_price = None
    cascade_cnt = 0; add_done = False; ks = False
    active = []; all_trades = []
    daily_pnl = 0.0; last_date = None

    for i in range(50, len(df) - 1):
        row = df.iloc[i]
        ts = df.index[i]
        eh = int(row["est_hour"])
        day = row["date"]
        o, h, l, c = float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"])

        if day != last_date:
            for t in active:
                if t["exit_time"] is None:
                    dm = 1 if t["direction"] == "LONG" else -1
                    pp = to_pips((c - t["entry_price"]) * dm)
                    t.update({"pnl_pips": pp, "exit_time": ts, "exit_price": c,
                             "result": "win" if pp > 0 else "loss", "exit_reason": "new_day"})
                    all_trades.append(t)
                    daily_pnl += pp
            active = [t for t in active if t["exit_time"] is None]
            ah = None; al = None; ar_pips = None
            ar_complete = False; tier = "NA"
            sess_dir = None; init_time = None; init_price = None
            cascade_cnt = 0; add_done = False; ks = False
            daily_pnl = 0.0; last_date = day

        in_asian = (eh >= cfg.asian_start_est or eh <= cfg.asian_end_est)
        if in_asian:
            if ah is None: ah = h; al = l
            else: ah = max(ah, h); al = min(al, l)
            if eh == cfg.asian_end_est and ah is not None:
                ar_pips = to_pips(ah - al)
                if ar_pips < 20: tier = "T1"
                elif ar_pips < 30: tier = "T2"
                elif ar_pips < 45: tier = "T3"
                else: tier = "NO_GO"
                ar_complete = True
            if eh >= cfg.asian_start_est or eh < cfg.asian_end_est:
                continue

        if not ar_complete or tier == "NO_GO":
            if active:
                ks = _manage(active, all_trades, h, l, c, ts, ah, al, ar_pips, cfg, init_time, ks)
            continue

        if eh >= cfg.hard_exit_est:
            for t in active:
                if t["exit_time"] is None:
                    dm = 1 if t["direction"] == "LONG" else -1
                    pp = to_pips((c - t["entry_price"]) * dm)
                    t.update({"pnl_pips": pp, "exit_time": ts, "exit_price": c,
                             "result": "win" if pp > 0 else "loss", "exit_reason": "hard_exit"})
                    all_trades.append(t)
            active = [t for t in active if t["exit_time"] is None]
            sess_dir = None
            continue

        ks = _manage(active, all_trades, h, l, c, ts, ah, al, ar_pips, cfg, init_time, ks)
        if ks:
            for t in active:
                if t["exit_time"] is None:
                    dm = 1 if t["direction"] == "LONG" else -1
                    pp = to_pips((c - t["entry_price"]) * dm)
                    t.update({"pnl_pips": pp, "exit_time": ts, "exit_price": c,
                             "result": "win" if pp > 0 else "loss", "exit_reason": "kill_switch"})
                    all_trades.append(t)
            active = [t for t in active if t["exit_time"] is None]
            continue

        if not (cfg.entry_start_est <= eh < cfg.entry_end_est): continue
        if ar_pips is None or ar_pips <= 0: continue

        # P90 detection
        tr = h - l
        if tr <= 0: continue
        body = abs(c - o)
        if body / tr <= cfg.p90_body_pct: continue
        is_bull = c > ah
        is_bear = c < al
        if not is_bull and not is_bear: continue

        body_pips = to_pips(body)
        thr = None
        for (s, e), t in cfg.p90_thresholds.items():
            if s <= eh < e: thr = t; break
        if thr is None or body_pips < thr: continue

        sdir = "LONG" if is_bull else "SHORT"

        if sess_dir is None:
            sess_dir = sdir; init_time = ts; init_price = c
            cascade_cnt = 1; add_done = False
            sl_off = to_price(body_pips * cfg.initial_sl_mult)
            tp_off = to_price(ar_pips * cfg.tp2_pct)
            sl = c - sl_off if sdir == "LONG" else c + sl_off
            tp = c + tp_off if sdir == "LONG" else c - tp_off
            active.append({"entry_time": ts, "direction": sdir, "entry_price": c,
                          "sl_price": sl, "tp_price": tp, "size_lots": cfg.position_size_lots,
                          "activation_type": "initial", "cascade_num": 0,
                          "exit_time": None, "exit_price": None, "pnl_pips": 0,
                          "result": "", "exit_reason": ""})
            continue

        if sess_dir == sdir:
            if cascade_cnt >= cfg.max_cascades: continue
            if init_time is not None:
                mins = (ts - init_time).total_seconds() / 60.0
                if mins < cfg.cascade_window_min or mins > cfg.cascade_window_max: continue
            cascade_cnt += 1
            sl_off = to_price(body_pips * cfg.cascade_sl_mult)
            tp_off = to_price(ar_pips * cfg.tp2_pct)
            sl = c - sl_off if sdir == "LONG" else c + sl_off
            tp = c + tp_off if sdir == "LONG" else c - tp_off
            if cascade_cnt == 2:
                sz = cfg.position_size_lots * cfg.cascade_size_1 / cfg.initial_size
                at = "cascade_1"
            elif cascade_cnt == 3:
                sz = cfg.position_size_lots * cfg.cascade_size_2 / cfg.initial_size
                at = "cascade_2"
            else: continue
            active.append({"entry_time": ts, "direction": sdir, "entry_price": c,
                          "sl_price": sl, "tp_price": tp, "size_lots": sz,
                          "activation_type": at, "cascade_num": cascade_cnt - 1,
                          "exit_time": None, "exit_price": None, "pnl_pips": 0,
                          "result": "", "exit_reason": ""})

        # 45-min add
        if init_time is not None and not add_done and cascade_cnt >= 1 and len(active) > 0:
            mins = (ts - init_time).total_seconds() / 60.0
            if cfg.add_time_minutes <= mins < cfg.add_time_minutes + cfg.add_time_window:
                ext = to_pips(c - init_price) if sess_dir == "LONG" else to_pips(init_price - c)
                if ext >= cfg.add_extension_pips and not ks:
                    add_done = True
                    tp_off = to_price(ar_pips * cfg.tp2_pct)
                    if sess_dir == "LONG":
                        tp = c + tp_off; sl = init_price
                    else:
                        tp = c - tp_off; sl = init_price
                    active.append({"entry_time": ts, "direction": sess_dir, "entry_price": c,
                                  "sl_price": sl, "tp_price": tp,
                                  "size_lots": cfg.position_size_lots * cfg.add_size / cfg.initial_size,
                                  "activation_type": "add_45min", "cascade_num": 0,
                                  "exit_time": None, "exit_price": None, "pnl_pips": 0,
                                  "result": "", "exit_reason": ""})

    # Close remaining
    if active:
        lr = df.iloc[-1]; lts = df.index[-1]; lc = float(lr["close"])
        for t in active:
            if t["exit_time"] is None:
                dm = 1 if t["direction"] == "LONG" else -1
                pp = to_pips((lc - t["entry_price"]) * dm)
                t.update({"pnl_pips": pp, "exit_time": lts, "exit_price": lc,
                         "result": "win" if pp > 0 else "loss", "exit_reason": "end_of_data"})
                all_trades.append(t)

    return all_trades


def _manage(active, all_trades, h, l, c, ts, ah, al, ar_pips, cfg, init_time, ks):
    remove = []
    for t in active:
        if t["exit_time"] is not None: continue
        il = t["direction"] == "LONG"

        if il and l <= t["sl_price"]:
            t["pnl_pips"] = to_pips(t["sl_price"] - t["entry_price"])
            t.update({"exit_time": ts, "exit_price": t["sl_price"], "result": "loss", "exit_reason": "sl"})
            all_trades.append(t); remove.append(t); continue
        elif not il and h >= t["sl_price"]:
            t["pnl_pips"] = to_pips(t["entry_price"] - t["sl_price"])
            t.update({"exit_time": ts, "exit_price": t["sl_price"], "result": "loss", "exit_reason": "sl"})
            all_trades.append(t); remove.append(t); continue

        if il and h >= t["tp_price"]:
            t["pnl_pips"] = to_pips(t["tp_price"] - t["entry_price"])
            t.update({"exit_time": ts, "exit_price": t["tp_price"], "result": "win", "exit_reason": "tp_50"})
            all_trades.append(t); remove.append(t); continue
        elif not il and l <= t["tp_price"]:
            t["pnl_pips"] = to_pips(t["entry_price"] - t["tp_price"])
            t.update({"exit_time": ts, "exit_price": t["tp_price"], "result": "win", "exit_reason": "tp_50"})
            all_trades.append(t); remove.append(t); continue

        if ar_pips and ah is not None and al is not None:
            koff = to_price(ar_pips * cfg.kill_switch_pct)
            if il and l <= al - koff: ks = True
            elif not il and h >= ah + koff: ks = True

        if init_time is not None:
            mh = (ts - init_time).total_seconds() / 60.0
            if mh >= cfg.hold_time_minutes:
                dm = 1 if il else -1
                pp = to_pips((c - t["entry_price"]) * dm)
                t.update({"pnl_pips": pp, "exit_time": ts, "exit_price": c,
                         "result": "win" if pp > 0 else "loss", "exit_reason": "hold_time"})
                all_trades.append(t); remove.append(t)

    for t in remove:
        if t in active: active.remove(t)
    return ks


def calc_results(trades):
    if not trades:
        return {"total_trades": 0, "error": "No trades generated"}
    pnls = [t["pnl_pips"] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    total = sum(pnls)
    wr = len(wins) / len(pnls) * 100 if pnls else 0

    cum = [0]
    for p in pnls: cum.append(cum[-1] + p)
    peak = cum[0]; mdd = 0
    for v in cum:
        if v > peak: peak = v
        dd = v - peak
        if dd < mdd: mdd = dd

    gp = sum(wins) if wins else 0
    gl = abs(sum(losses)) if losses else 1
    pf = gp / gl if gl > 0 else 0

    by_type = {}
    for t in trades:
        at = t["activation_type"]
        if at not in by_type: by_type[at] = {"trades": 0, "wins": 0, "pnl": 0}
        by_type[at]["trades"] += 1
        by_type[at]["pnl"] += t["pnl_pips"]
        if t["pnl_pips"] > 0: by_type[at]["wins"] += 1

    by_exit = {}
    for t in trades:
        er = t["exit_reason"]
        by_exit[er] = by_exit.get(er, 0) + 1

    sessions = set(t["entry_time"].date() for t in trades)

    return {
        "total_trades": len(trades), "total_sessions": len(sessions),
        "wins": len(wins), "losses": len(losses), "win_rate": round(wr, 1),
        "total_pnl_pips": round(total, 2),
        "avg_win_pips": round(sum(wins) / len(wins), 2) if wins else 0,
        "avg_loss_pips": round(sum(losses) / len(losses), 2) if losses else 0,
        "max_drawdown_pips": round(mdd, 2),
        "profit_factor": round(pf, 2),
        "by_activation_type": {at: {
            "trades": d["trades"],
            "wins": d["wins"],
            "win_rate": round(d["wins"] / d["trades"] * 100, 1) if d["trades"] > 0 else 0,
            "pnl_pips": round(d["pnl"], 2),
        } for at, d in by_type.items()},
        "by_exit_reason": by_exit,
    }


def main():
    data_path = r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv"
    print(f"Loading data...")
    df = parse_csv(data_path)
    print(f"  Loaded {len(df):,} bars ({df.index[0]} -> {df.index[-1]})")

    cfg = Cfg()
    print(f"\nRunning full P90 Cascade Activation backtest...")
    trades = run_backtest(df, cfg)

    results = calc_results(trades)

    print(f"\n{'='*60}")
    print(f"P90 CASCADE ACTIVATION — FULL BACKTEST RESULTS")
    print(f"{'='*60}")
    print(f"  Total Trades:   {results.get('total_trades', 0)}")
    print(f"  Total Sessions: {results.get('total_sessions', 0)}")
    print(f"  Wins:           {results.get('wins', 0)} ({results.get('win_rate', 0)}%)")
    print(f"  Losses:         {results.get('losses', 0)}")
    print(f"  Total P&L:      {results.get('total_pnl_pips', 0)} pips")
    print(f"  Avg Win:        {results.get('avg_win_pips', 0)} pips")
    print(f"  Avg Loss:       {results.get('avg_loss_pips', 0)} pips")
    print(f"  Max Drawdown:   {results.get('max_drawdown_pips', 0)} pips")
    print(f"  Profit Factor:  {results.get('profit_factor', 0)}")

    if results.get("by_activation_type"):
        print(f"\n  By Activation Type:")
        for at, data in results["by_activation_type"].items():
            print(f"    {at:15s}: {data['trades']:3d} trades | "
                  f"{data['win_rate']:5.1f}% WR | {data['pnl_pips']:+7.2f} pips")

    if results.get("by_exit_reason"):
        print(f"\n  By Exit Reason:")
        for reason, count in sorted(results["by_exit_reason"].items(), key=lambda x: -x[1]):
            print(f"    {reason:25s}: {count}")
    print(f"{'='*60}")

    # Save results
    output_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\backtests")
    output_dir.mkdir(parents=True, exist_ok=True)
    output = {
        "strategy": "P90_Cascade_Activation",
        "pair": "EUR/USD",
        "timeframe": "M5",
        "data_bars": len(df),
        "data_range": f"{df.index[0]} to {df.index[-1]}",
        "results": results,
        "trades": [{
            "entry_time": str(t["entry_time"]),
            "exit_time": str(t["exit_time"]) if t["exit_time"] else None,
            "direction": t["direction"],
            "entry_price": t["entry_price"],
            "exit_price": t["exit_price"],
            "sl_price": t["sl_price"],
            "tp_price": t["tp_price"],
            "activation_type": t["activation_type"],
            "pnl_pips": round(t["pnl_pips"], 2),
            "result": t["result"],
            "exit_reason": t["exit_reason"],
        } for t in trades],
    }
    results_file = output_dir / "p90_cascade_results.json"
    with open(results_file, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nResults saved to {results_file}")

    return len(trades)


if __name__ == "__main__":
    count = main()
    sys.exit(0 if count > 0 else 1)
