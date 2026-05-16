#!/usr/bin/env python3
"""
FULL PIPELINE: Data prep → Strategy backtest → Results.
Runs continuously until 2 profitable strategies are found.
Outputs all results to files (terminal output may be swallowed).
"""
import os, sys, json, glob, csv, time
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

# ── Paths ────────────────────────────────────────────────────────────────────
DOWNLOADS = Path(r"C:\Users\wifik\Downloads")
DATA_DIR = Path(__file__).parent / "data"
REPORTS_DIR = Path(__file__).parent / "reports"
DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)
LOG = REPORTS_DIR / "pipeline.log"
RESULTS = REPORTS_DIR / "all_results.json"
PROGRESS = REPORTS_DIR / "progress.json"

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    with open(LOG, "a") as f:
        f.write(line + "\n")
    try: print(line)
    except: pass

# ── Data Prep ───────────────────────────────────────────────────────────────
def parse_csv_file(filepath):
    """Parse a single CSV file, return (symbol, timeframe, df) or None."""
    name = Path(filepath).stem
    
    # Extract symbol and timeframe from filename
    # Pattern: EURUSD!_M5_202301020000_202605061250
    parts = name.replace('!', '').split('_')
    symbol = None
    timeframe = None
    for i, p in enumerate(parts):
        if p in ['M1','M5','M15','M30','H1','H4','D1','W1']:
            timeframe = p
            symbol = '_'.join(parts[:i])
            break
    if not symbol or not timeframe:
        return None
    
    # Try reading with different separators
    for sep in [',', ';', '\t']:
        try:
            df = pd.read_csv(filepath, sep=sep)
            if len(df.columns) >= 4:
                break
        except:
            continue
    else:
        try:
            df = pd.read_csv(filepath)
        except:
            return None
    
    # Standardize columns
    col_map = {}
    for c in df.columns:
        cl = c.lower().strip()
        if cl in ['open','o']: col_map[c] = 'open'
        elif cl in ['high','h']: col_map[c] = 'high'
        elif cl in ['low','l']: col_map[c] = 'low'
        elif cl in ['close','c']: col_map[c] = 'close'
        elif cl in ['volume','vol','v','tick_volume','tickvolume']: col_map[c] = 'volume'
        elif cl in ['time','date','datetime','timestamp']: col_map[c] = 'time'
    
    df = df.rename(columns=col_map)
    
    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'], errors='coerce')
        df = df.dropna(subset=['time']).set_index('time')
    
    for col in ['open','high','low','close']:
        if col not in df.columns:
            return None
    
    if 'volume' not in df.columns:
        df['volume'] = 0
    
    df = df[['open','high','low','close','volume']].sort_index()
    df = df[~df.index.duplicated(keep='first')]
    
    return (symbol, timeframe, df)

def prep_all_data():
    """Load and merge all CSV files from Downloads."""
    log("="*60)
    log("DATA PREP")
    log("="*60)
    
    csv_files = list(DOWNLOADS.glob("*.csv"))
    log(f"Found {len(csv_files)} CSV files")
    
    # Group by symbol_timeframe
    groups = {}
    for f in csv_files:
        result = parse_csv_file(f)
        if result is None:
            log(f"  SKIP {f.name}: could not parse")
            continue
        symbol, tf, df = result
        key = f"{symbol}_{tf}"
        if key not in groups:
            groups[key] = []
        groups[key].append((f.name, df))
    
    log(f"Grouped into {len(groups)} symbol/timeframe combos")
    
    # Merge and save
    summary = {}
    for key in sorted(groups.keys()):
        items = groups[key]
        dfs = [df for _, df in items]
        combined = pd.concat(dfs).sort_index()
        combined = combined[~combined.index.duplicated(keep='first')]
        
        # Save parquet
        pq_path = DATA_DIR / f"{key}.parquet"
        csv_path = DATA_DIR / f"{key}.csv"
        combined.to_parquet(pq_path)
        combined.to_csv(csv_path)
        
        summary[key] = {
            "rows": len(combined),
            "start": str(combined.index[0]),
            "end": str(combined.index[-1]),
            "files": len(items),
        }
        log(f"  {key}: {len(combined):,} rows ({combined.index[0]} → {combined.index[-1]})")
    
    with open(DATA_DIR / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    log(f"Data prep complete: {len(summary)} datasets")
    return summary

# ── Backtest Engine ─────────────────────────────────────────────────────────
def run_cerebus_backtest(df, symbol, strategy_name, params):
    """
    Run a CEREBUS strategy backtest on a DataFrame.
    Returns metrics dict.
    """
    if df is None or len(df) < 200:
        return None
    
    # Ensure UTC
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')
    
    df = df.copy()
    df['hour'] = df.index.hour
    df['date'] = df.index.date
    
    trades = []
    position = None
    
    # Strategy parameters
    if strategy_name == "symmetry_trap":
        tier = params.get("tier", "T2")
        tc = {"T1": {"atom_tp": 10, "trig": 12, "sl": 4},
              "T2": {"atom_tp": 12, "trig": 15, "sl": 6},
              "T3": {"atom_tp": 15, "trig": 19, "sl": 8}}[tier]
        max_loops = params.get("max_loops", 8)
        lot_size = params.get("lot_size", 0.1)
    elif strategy_name == "option_b":
        tier_trigger = params.get("tier_trigger", 19)
        sl_pips = params.get("stop_loss", 15)
        tp_pips = params.get("take_profit", 19)
        max_loops = params.get("max_loops", 8)
        lot_size = params.get("lot_size", 0.1)
    else:
        return None
    
    asian_high = None
    asian_low = None
    asian_range_pips = None
    bias_locked = False
    loop_count = 0
    daily_pnl = 0
    last_date = None
    impulse_hit = False
    impulse_extreme = 0
    impulse_time = None
    
    for i in range(1, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1]
        hour = row['hour']
        date = row['date']
        o, h, l, c = row['open'], row['high'], row['low'], row['close']
        po, pc = prev['open'], prev['close']
        
        # New day reset
        if date != last_date:
            asian_high = None
            asian_low = None
            asian_range_pips = None
            bias_locked = False
            loop_count = 0
            daily_pnl = 0
            impulse_hit = False
            impulse_extreme = 0
            impulse_time = None
            last_date = date
        
        # ── Asian Session: 19:00-03:00 UTC ──
        if hour >= 19 or hour < 3:
            if asian_high is None:
                asian_high = h
                asian_low = l
            else:
                asian_high = max(asian_high, h)
                asian_low = min(asian_low, l)
            continue
        
        # ── End of Asian: classify tier ──
        if asian_high is not None and asian_range_pips is None:
            mid_price = (asian_high + asian_low) / 2
            pip_size = mid_price * 0.0001
            asian_range_pips = (asian_high - asian_low) / pip_size
            bias_locked = True
        
        # ── Hard exit at 17:00 UTC ──
        if hour >= 17 and position is not None:
            if position['side'] == 'buy':
                pnl = (c - position['entry']) * position['size'] * 100000
            else:
                pnl = (position['entry'] - c) * position['size'] * 100000
            daily_pnl += pnl
            trades.append({'side': position['side'], 'entry': position['entry'],
                          'exit': c, 'pnl': round(pnl, 2), 'reason': 'hard_exit'})
            position = None
            loop_count = 0
            continue
        
        # ── Bias window: 08:00-17:00 UTC ──
        if hour < 8 or hour >= 17:
            continue
        
        if not bias_locked or asian_range_pips is None:
            continue
        
        if asian_range_pips > 45:  # NO-GO
            continue
        
        if loop_count >= max_loops:
            continue
        
        # ── Check existing position ──
        if position is not None:
            # SL check
            if position['side'] == 'buy':
                if c < asian_low:
                    pnl = (c - position['entry']) * position['size'] * 100000
                    daily_pnl += pnl
                    trades.append({'side': 'buy', 'entry': position['entry'],
                                  'exit': c, 'pnl': round(pnl, 2), 'reason': 'sl'})
                    position = None
                    continue
                if c >= position['tp']:
                    pnl = (c - position['entry']) * position['size'] * 100000
                    daily_pnl += pnl
                    trades.append({'side': 'buy', 'entry': position['entry'],
                                  'exit': c, 'pnl': round(pnl, 2), 'reason': 'tp'})
                    position = None
                    continue
            else:  # sell
                if c > asian_high:
                    pnl = (position['entry'] - c) * position['size'] * 100000
                    daily_pnl += pnl
                    trades.append({'side': 'sell', 'entry': position['entry'],
                                  'exit': c, 'pnl': round(pnl, 2), 'reason': 'sl'})
                    position = None
                    continue
                if c <= position['tp']:
                    pnl = (position['entry'] - c) * position['size'] * 100000
                    daily_pnl += pnl
                    trades.append({'side': 'sell', 'entry': position['entry'],
                                  'exit': c, 'pnl': round(pnl, 2), 'reason': 'tp'})
                    position = None
                    continue
            continue
        
        # ── Entry logic ──
        if strategy_name == "symmetry_trap":
            trig = tc['trig'] * 10 * pip_size
            # Bullish: price drops below Asian low
            if l <= asian_low - trig and not impulse_hit:
                impulse_hit = True
                impulse_extreme = l
                impulse_time = i
                continue
            if impulse_hit and impulse_extreme < (asian_high + asian_low) / 2:
                # Pullback: red candle
                if pc < po:
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
                impulse_time = i
                continue
            if impulse_hit and impulse_extreme > (asian_high + asian_low) / 2:
                if pc > po:
                    entry = c
                    sl = entry + tc['sl'] * 10 * pip_size
                    tp = entry - tc['atom_tp'] * 10 * pip_size
                    position = {'side': 'sell', 'entry': entry, 'sl': sl, 'tp': tp, 'size': lot_size}
                    loop_count += 1
                    impulse_hit = False
                    continue
            # Reset impulse after 60 bars
            if impulse_hit and (i - impulse_time) > 60:
                impulse_hit = False
        
        elif strategy_name == "option_b":
            trig = tier_trigger * 10 * pip_size
            # Bullish impulse
            if l <= asian_low - trig:
                if pc < po:  # pullback
                    entry = c
                    sl = entry - sl_pips * 10 * pip_size
                    tp = entry + tp_pips * 10 * pip_size
                    position = {'side': 'buy', 'entry': entry, 'sl': sl, 'tp': tp, 'size': lot_size}
                    loop_count += 1
                    continue
            # Bearish impulse
            if h >= asian_high + trig:
                if pc > po:
                    entry = c
                    sl = entry + sl_pips * 10 * pip_size
                    tp = entry - tp_pips * 10 * pip_size
                    position = {'side': 'sell', 'entry': entry, 'sl': sl, 'tp': tp, 'size': lot_size}
                    loop_count += 1
                    continue
    
    # ── Calculate metrics ──
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
        "symbol": symbol,
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
        "is_profitable": total_pnl > 0 and max_dd > -200 and win_rate > 35,
    }

# ── Main Loop ───────────────────────────────────────────────────────────────
def main():
    log("="*60)
    log("CEREBUS NAUTILUS BACKTEST PIPELINE")
    log(f"Started: {datetime.now()}")
    log("="*60)
    
    # Step 1: Data prep
    summary = prep_all_data()
    
    if not summary:
        log("ERROR: No data prepared. Exiting.")
        return
    
    # Find available datasets
    available = {}
    for key, info in summary.items():
        parts = key.rsplit('_', 1)
        if len(parts) == 2:
            symbol, tf = parts
            if symbol not in available:
                available[symbol] = {}
            available[symbol][tf] = key
    
    log(f"\nAvailable: {list(available.keys())}")
    
    # Step 2: Define strategies to test
    strategies = [
        {
            "name": "symmetry_trap",
            "param_sets": [
                {"tier": "T1", "max_loops": 8, "lot_size": 0.1},
                {"tier": "T2", "max_loops": 8, "lot_size": 0.1},
                {"tier": "T3", "max_loops": 8, "lot_size": 0.1},
                {"tier": "T2", "max_loops": 6, "lot_size": 0.05},
                {"tier": "T2", "max_loops": 10, "lot_size": 0.2},
            ],
        },
        {
            "name": "option_b",
            "param_sets": [
                {"tier_trigger": 19, "stop_loss": 15, "take_profit": 19, "max_loops": 8, "lot_size": 0.1},
                {"tier_trigger": 15, "stop_loss": 12, "take_profit": 15, "max_loops": 6, "lot_size": 0.05},
                {"tier_trigger": 21, "stop_loss": 18, "take_profit": 21, "max_loops": 10, "lot_size": 0.1},
                {"tier_trigger": 17, "stop_loss": 14, "take_profit": 17, "max_loops": 8, "lot_size": 0.1},
            ],
        },
    ]
    
    # Step 3: Run backtests in loop
    all_results = []
    winners = []
    iteration = 0
    max_iterations = 50
    
    # Pairs to test (prioritize EURUSD)
    priority_pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF", "CHFJPY"]
    timeframes = ["M5", "M1"]
    
    log(f"\n{'='*60}")
    log("BACKTEST LOOP")
    log(f"{'='*60}")
    
    while iteration < max_iterations and len(winners) < 2:
        iteration += 1
        log(f"\n--- Iteration {iteration} | Winners: {len(winners)}/2 ---")
        
        for strategy in strategies:
            # Skip if this strategy is already a winner
            strategy_won = any(w['strategy'] == strategy['name'] for w in winners)
            
            for pair in priority_pairs:
                if pair not in available:
                    continue
                
                for tf in timeframes:
                    if tf not in available[pair]:
                        continue
                    
                    data_key = available[pair][tf]
                    
                    # Load data
                    try:
                        df = pd.read_parquet(DATA_DIR / f"{data_key}.parquet")
                    except:
                        try:
                            df = pd.read_csv(DATA_DIR / f"{data_key}.csv", index_col=0, parse_dates=True)
                        except:
                            continue
                    
                    # Test each param set
                    for params in strategy["param_sets"]:
                        result = run_cerebus_backtest(df, pair, strategy["name"], params)
                        
                        if result is None:
                            continue
                        
                        result['data_key'] = data_key
                        result['iteration'] = iteration
                        result['timestamp'] = datetime.now().isoformat()
                        
                        all_results.append(result)
                        
                        status = "✅ PROFITABLE" if result['is_profitable'] else "❌"
                        log(f"  {status} {strategy['name']} {pair} {tf} {params['tier'] if 'tier' in params else ''}: "
                            f"PnL=${result['total_pnl']:.0f} WR={result['win_rate']:.0f}% "
                            f"DD={result['max_drawdown']:.0f} PF={result['profit_factor']:.2f} "
                            f"Trades={result['total_trades']}")
                        
                        if result['is_profitable'] and not strategy_won:
                            winners.append(result)
                            log(f"  🏆 WINNER! {strategy['name']} on {pair} {tf}")
                            
                            # Save winner report
                            winner_path = REPORTS_DIR / f"winner_{strategy['name']}_{pair}_{tf}.json"
                            with open(winner_path, 'w') as f:
                                json.dump(result, f, indent=2)
                            
                            if len(winners) >= 2:
                                break
                    
                    if len(winners) >= 2:
                        break
                if len(winners) >= 2:
                    break
            if len(winners) >= 2:
                break
        
        # Save progress
        progress = {
            "iteration": iteration,
            "winners": len(winners),
            "total_tests": len(all_results),
            "timestamp": datetime.now().isoformat(),
        }
        with open(PROGRESS, "w") as f:
            json.dump(progress, f, indent=2)
        
        if len(winners) >= 2:
            break
    
    # ── Final Summary ──
    log(f"\n{'='*60}")
    log("FINAL RESULTS")
    log(f"{'='*60}")
    log(f"Total tests run: {len(all_results)}")
    log(f"Winners found: {len(winners)}/2")
    
    for w in winners:
        log(f"\n🏆 {w['strategy']} on {w['symbol']}:")
        log(f"   P&L: ${w['total_pnl']:.2f} | Win Rate: {w['win_rate']}%")
        log(f"   Max DD: ${w['max_drawdown']:.2f} | Profit Factor: {w['profit_factor']}")
        log(f"   Trades: {w['total_trades']} (W:{w['wins']} L:{w['losses']})")
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
    
    log(f"\nAll results saved to: {RESULTS}")
    log(f"Pipeline complete: {datetime.now()}")

if __name__ == "__main__":
    main()
