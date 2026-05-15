#!/usr/bin/env python3
"""
Step 2: Backtest — Run CEREBUS strategies on prepared data.
Loads parquet files from nautilus/data/, runs strategies, saves results.
"""
import os, json, sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

DATA_DIR = Path(__file__).parent / "data"
REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)
LOG = REPORTS_DIR / "backtest.log"
RESULTS = REPORTS_DIR / "all_results.json"
PROGRESS = REPORTS_DIR / "progress.json"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    with open(LOG, "a") as f:
        f.write(line + "\n")
    print(line)

def load_data(key):
    """Load parquet data by key (e.g. EURUSD_M5)."""
    pq = DATA_DIR / f"{key}.parquet"
    if pq.exists():
        return pd.read_parquet(pq)
    csv_f = DATA_DIR / f"{key}.csv"
    if csv_f.exists():
        return pd.read_csv(csv_f, index_col=0, parse_dates=True)
    return None

def run_symmetry_trap(df, params):
    """
    CEREBUS Distribution Symmetry Trap.
    3-layer model: Bias Lock → Atomic Entry → Distribution Targets.
    """
    if df is None or len(df) < 200:
        return None
    
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')
    
    df = df.copy()
    df['hour'] = df.index.hour
    df['date'] = df.index.date
    
    tier = params.get("tier", "T2")
    tc = {
        "T1": {"atom_tp": 10, "trig": 12, "sl": 4},
        "T2": {"atom_tp": 12, "trig": 15, "sl": 6},
        "T3": {"atom_tp": 15, "trig": 19, "sl": 8},
    }.get(tier, {"atom_tp": 12, "trig": 15, "sl": 6})
    
    max_loops = params.get("max_loops", 8)
    lot_size = params.get("lot_size", 0.1)
    
    trades = []
    position = None
    asian_high = None
    asian_low = None
    asian_range_pips = None
    bias_locked = False
    loop_count = 0
    last_date = None
    impulse_hit = False
    impulse_extreme = 0
    impulse_bar_idx = 0
    
    for i in range(1, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1]
        hour = int(row['hour'])
        date = row['date']
        o, h, l, c = float(row['open']), float(row['high']), float(row['low']), float(row['close'])
        po, pc = float(prev['open']), float(prev['close'])
        
        # New day reset
        if date != last_date:
            asian_high = None
            asian_low = None
            asian_range_pips = None
            bias_locked = False
            loop_count = 0
            impulse_hit = False
            last_date = date
        
        # Asian session: 19:00-03:00 UTC
        if hour >= 19 or hour < 3:
            if asian_high is None:
                asian_high = h
                asian_low = l
            else:
                asian_high = max(asian_high, h)
                asian_low = min(asian_low, l)
            continue
        
        # End of Asian: classify tier
        if asian_high is not None and asian_range_pips is None:
            mid = (asian_high + asian_low) / 2
            pip_size = mid * 0.0001
            asian_range_pips = (asian_high - asian_low) / pip_size
            bias_locked = True
        
        # Hard exit at 17:00 UTC
        if hour >= 17 and position is not None:
            pnl = ((c - position['entry']) * position['size'] * 100000) if position['side'] == 'buy' \
                  else ((position['entry'] - c) * position['size'] * 100000)
            trades.append({'side': position['side'], 'pnl': round(pnl, 2), 'reason': 'hard_exit'})
            position = None
            loop_count = 0
            continue
        
        if hour < 8 or hour >= 17:
            continue
        if not bias_locked or asian_range_pips is None or asian_range_pips > 45:
            continue
        if loop_count >= max_loops:
            continue
        
        # Check existing position
        if position is not None:
            if position['side'] == 'buy':
                if c < asian_low:
                    pnl = (c - position['entry']) * position['size'] * 100000
                    trades.append({'side': 'buy', 'pnl': round(pnl, 2), 'reason': 'sl'})
                    position = None
                    continue
                if c >= position['tp']:
                    pnl = (c - position['entry']) * position['size'] * 100000
                    trades.append({'side': 'buy', 'pnl': round(pnl, 2), 'reason': 'tp'})
                    position = None
                    continue
            else:
                if c > asian_high:
                    pnl = (position['entry'] - c) * position['size'] * 100000
                    trades.append({'side': 'sell', 'pnl': round(pnl, 2), 'reason': 'sl'})
                    position = None
                    continue
                if c <= position['tp']:
                    pnl = (position['entry'] - c) * position['size'] * 100000
                    trades.append({'side': 'sell', 'pnl': round(pnl, 2), 'reason': 'tp'})
                    position = None
                    continue
            continue
        
        # Entry logic
        mid_price = (asian_high + asian_low) / 2
        pip_size = mid_price * 0.0001
        trig = tc['trig'] * 10 * pip_size
        
        # Bullish: price drops below Asian low
        if l <= asian_low - trig and not impulse_hit:
            impulse_hit = True
            impulse_extreme = l
            impulse_bar_idx = i
        
        if impulse_hit and impulse_extreme < mid_price:
            if pc < po:  # red candle pullback
                entry = c
                sl = entry - tc['sl'] * 10 * pip_size
                tp = entry + tc['atom_tp'] * 10 * pip_size
                position = {'side': 'buy', 'entry': entry, 'sl': sl, 'tp': tp, 'size': lot_size}
                loop_count += 1
                impulse_hit = False
                continue
        
        # Bearish: price rises above Asian high
        if h >= asian_high + trig and not impulse_hit:
            impulse_hit = True
            impulse_extreme = h
            impulse_bar_idx = i
        
        if impulse_hit and impulse_extreme > mid_price:
            if pc > po:  # green candle pullback
                entry = c
                sl = entry + tc['sl'] * 10 * pip_size
                tp = entry - tc['atom_tp'] * 10 * pip_size
                position = {'side': 'sell', 'entry': entry, 'sl': sl, 'tp': tp, 'size': lot_size}
                loop_count += 1
                impulse_hit = False
                continue
        
        # Reset impulse after 60 bars
        if impulse_hit and (i - impulse_bar_idx) > 60:
            impulse_hit = False
    
    return calc_metrics(trades, "symmetry_trap", params)

def run_option_b(df, params):
    """CEREBUS Option B — Continuous Loop Super Scalper."""
    if df is None or len(df) < 200:
        return None
    
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')
    
    df = df.copy()
    df['hour'] = df.index.hour
    df['date'] = df.index.date
    
    tier_trigger = params.get("tier_trigger", 19)
    sl_pips = params.get("stop_loss", 15)
    tp_pips = params.get("take_profit", 19)
    max_loops = params.get("max_loops", 8)
    lot_size = params.get("lot_size", 0.1)
    
    trades = []
    position = None
    asian_high = None
    asian_low = None
    loop_count = 0
    last_date = None
    
    for i in range(1, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1]
        hour = int(row['hour'])
        date = row['date']
        o, h, l, c = float(row['open']), float(row['high']), float(row['low']), float(row['close'])
        po, pc = float(prev['open']), float(prev['close'])
        
        if date != last_date:
            asian_high = None
            asian_low = None
            loop_count = 0
            last_date = date
        
        # Asian session
        if hour >= 19 or hour < 3:
            if asian_high is None:
                asian_high = h
                asian_low = l
            else:
                asian_high = max(asian_high, h)
                asian_low = min(asian_low, l)
            continue
        
        # Hard exit
        if hour >= 17 and position is not None:
            pnl = ((c - position['entry']) * position['size'] * 100000) if position['side'] == 'buy' \
                  else ((position['entry'] - c) * position['size'] * 100000)
            trades.append({'side': position['side'], 'pnl': round(pnl, 2), 'reason': 'hard_exit'})
            position = None
            loop_count = 0
            continue
        
        if hour < 8 or hour >= 17:
            continue
        if asian_high is None:
            continue
        if loop_count >= max_loops:
            continue
        
        # Check position
        if position is not None:
            if position['side'] == 'buy':
                if c < asian_low:
                    pnl = (c - position['entry']) * position['size'] * 100000
                    trades.append({'side': 'buy', 'pnl': round(pnl, 2), 'reason': 'sl'})
                    position = None
                    continue
                if c >= position['tp']:
                    pnl = (c - position['entry']) * position['size'] * 100000
                    trades.append({'side': 'buy', 'pnl': round(pnl, 2), 'reason': 'tp'})
                    position = None
                    continue
            else:
                if c > asian_high:
                    pnl = (position['entry'] - c) * position['size'] * 100000
                    trades.append({'side': 'sell', 'pnl': round(pnl, 2), 'reason': 'sl'})
                    position = None
                    continue
                if c <= position['tp']:
                    pnl = (position['entry'] - c) * position['size'] * 100000
                    trades.append({'side': 'sell', 'pnl': round(pnl, 2), 'reason': 'tp'})
                    position = None
                    continue
            continue
        
        # Entry: Impulse >= Tier Trigger + opposite close in density zone
        mid_price = (asian_high + asian_low) / 2
        pip_size = mid_price * 0.0001
        impulse_pips = abs(c - o) / pip_size
        
        if impulse_pips >= tier_trigger:
            if c > o and pc < po:  # green impulse + red pullback
                if asian_low <= c <= asian_high:  # in density zone
                    entry = c
                    sl = entry - sl_pips * 10 * pip_size
                    tp = entry + tp_pips * 10 * pip_size
                    position = {'side': 'buy', 'entry': entry, 'sl': sl, 'tp': tp, 'size': lot_size}
                    loop_count += 1
                    continue
            elif c < o and pc > po:  # red impulse + green pullback
                if asian_low <= c <= asian_high:
                    entry = c
                    sl = entry + sl_pips * 10 * pip_size
                    tp = entry - tp_pips * 10 * pip_size
                    position = {'side': 'sell', 'entry': entry, 'sl': sl, 'tp': tp, 'size': lot_size}
                    loop_count += 1
                    continue
    
    return calc_metrics(trades, "option_b", params)

def calc_metrics(trades, strategy_name, params):
    """Calculate backtest metrics from trades list."""
    if not trades:
        return None
    
    pnls = [t['pnl'] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    total_pnl = sum(pnls)
    win_rate = len(wins) / len(pnls) * 100 if pnls else 0
    
    cum = [0]
    for p in pnls:
        cum.append(cum[-1] + p)
    peak = cum[0]
    max_dd = 0
    for v in cum:
        if v > peak: peak = v
        dd = v - peak
        if dd < max_dd: max_dd = dd
    
    gross_profit = sum(wins) if wins else 0
    gross_loss = abs(sum(losses)) if losses else 1
    pf = gross_profit / gross_loss if gross_loss > 0 else 0
    
    return {
        "strategy": strategy_name,
        "params": params,
        "total_trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(win_rate, 1),
        "total_pnl": round(total_pnl, 2),
        "avg_win": round(sum(wins)/len(wins), 2) if wins else 0,
        "avg_loss": round(sum(losses)/len(losses), 2) if losses else 0,
        "max_drawdown": round(max_dd, 2),
        "profit_factor": round(pf, 2),
        "is_profitable": total_pnl > 0 and max_dd > -200 and win_rate > 30,
    }

def main():
    log("="*60)
    log("STEP 2: BACKTEST")
    log("="*60)
    
    # Load summary
    summary_path = DATA_DIR / "summary.json"
    if not summary_path.exists():
        log("ERROR: No data summary. Run step1_prep_data.py first.")
        return
    
    with open(summary_path) as f:
        summary = json.load(f)
    
    log(f"Available datasets: {list(summary.keys())}")
    
    # Define tests
    tests = []
    
    # Symmetry Trap on EURUSD M5 (primary)
    for tier in ["T1", "T2", "T3"]:
        for loops in [6, 8, 10]:
            tests.append({
                "data_key": "EURUSD_M5",
                "strategy": "symmetry_trap",
                "params": {"tier": tier, "max_loops": loops, "lot_size": 0.1},
            })
    
    # Option B on EURUSD M5
    for tt in [15, 17, 19, 21]:
        for sl in [12, 15, 18]:
            tests.append({
                "data_key": "EURUSD_M5",
                "strategy": "option_b",
                "params": {"tier_trigger": tt, "stop_loss": sl, "take_profit": tt, "max_loops": 8, "lot_size": 0.1},
            })
    
    # Also test on other pairs if data available
    for pair in ["GBPUSD", "USDJPY", "AUDUSD"]:
        key = f"{pair}_M5"
        if key in summary:
            for tier in ["T2", "T3"]:
                tests.append({
                    "data_key": key,
                    "strategy": "symmetry_trap",
                    "params": {"tier": tier, "max_loops": 8, "lot_size": 0.1},
                })
    
    log(f"Total tests to run: {len(tests)}")
    
    # Run tests
    all_results = []
    winners = []
    
    for idx, test in enumerate(tests):
        key = test["data_key"]
        strategy = test["strategy"]
        params = test["params"]
        
        # Check if we already have 2 winners
        if len(winners) >= 2:
            break
        
        # Load data
        df = load_data(key)
        if df is None:
            log(f"  [{idx+1}/{len(tests)}] SKIP {key}: no data")
            continue
        
        # Run strategy
        if strategy == "symmetry_trap":
            result = run_symmetry_trap(df, params)
        elif strategy == "option_b":
            result = run_option_b(df, params)
        else:
            continue
        
        if result is None:
            log(f"  [{idx+1}/{len(tests)}] {strategy} {key} {params.get('tier','')}: no trades")
            continue
        
        result['data_key'] = key
        result['timestamp'] = datetime.now().isoformat()
        all_results.append(result)
        
        status = "✅ PROFITABLE" if result['is_profitable'] else "❌"
        log(f"  [{idx+1}/{len(tests)}] {status} {strategy} {key}: "
            f"PnL=${result['total_pnl']:.0f} WR={result['win_rate']:.0f}% "
            f"DD={result['max_drawdown']:.0f} PF={result['profit_factor']:.2f} "
            f"Trades={result['total_trades']}")
        
        if result['is_profitable']:
            # Check if this strategy type is already a winner
            already_won = any(w['strategy'] == strategy for w in winners)
            if not already_won:
                winners.append(result)
                log(f"  🏆 WINNER! {strategy} on {key}")
                
                # Save winner
                w_path = REPORTS_DIR / f"winner_{strategy}_{key}.json"
                with open(w_path, "w") as f:
                    json.dump(result, f, indent=2)
        
        # Save progress
        with open(PROGRESS, "w") as f:
            json.dump({
                "tests_run": idx + 1,
                "total_tests": len(tests),
                "winners": len(winners),
                "timestamp": datetime.now().isoformat(),
            }, f, indent=2)
    
    # Summary
    log(f"\n{'='*60}")
    log("RESULTS")
    log(f"{'='*60}")
    log(f"Tests run: {len(all_results)}")
    log(f"Winners: {len(winners)}/2")
    
    for w in winners:
        log(f"\n🏆 {w['strategy']} on {w['data_key']}:")
        log(f"   P&L: ${w['total_pnl']:.2f} | WR: {w['win_rate']}% | DD: ${w['max_drawdown']:.2f}")
        log(f"   PF: {w['profit_factor']} | Trades: {w['total_trades']}")
        log(f"   Params: {w['params']}")
    
    # Save all results
    with open(RESULTS, "w") as f:
        json.dump({
            "winners": winners,
            "all_results": all_results,
            "summary": {
                "total_tests": len(all_results),
                "winners_found": len(winners),
                "timestamp": datetime.now().isoformat(),
            }
        }, f, indent=2, default=str)
    
    log(f"\nResults saved to: {RESULTS}")

if __name__ == "__main__":
    main()
