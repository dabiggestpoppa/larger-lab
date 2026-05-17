"""Full trace of strategy execution for Jan 2-3."""
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

STRATEGY_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
sys.path.insert(0, str(STRATEGY_DIR))

from p90_cascade_activation import P90CascadeActivationStrategy, P90CascadeConfig, CascadeDirection, TierStatus, ActivationType

# Parse CSV
data_path = Path(r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv")
with open(data_path, 'r', encoding='utf-8', errors='ignore') as f:
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
    except (ValueError, IndexError): continue
df = pd.DataFrame(records)
df.set_index("timestamp", inplace=True)
df.sort_index(inplace=True)

# Use Jan 2-5 data
df_test = df[(df.index >= datetime(2023, 1, 2)) & (df.index < datetime(2023, 1, 5))].copy()
df_test["est_hour"] = df_test.index.hour.map(lambda h: (h - 5 + 24) % 24)
df_test["date"] = df_test.index.date

print(f"Data: {len(df_test)} bars, {df_test.index[0]} -> {df_test.index[-1]}")

# Manually replicate the strategy logic with tracing
cfg = P90CascadeConfig()
asian_high = None
asian_low = None
asian_range_pips = None
tier = TierStatus.NA
asian_range_complete = False
session_direction = CascadeDirection.NONE
initial_p90_time = None
initial_p90_price = None
cascade_count = 0
add_45min_done = False
kill_switch_triggered = False
last_date = None
daily_loss_limit_hit = False
active_trades = []
all_trades = []

for i in range(50, len(df_test)):
    row = df_test.iloc[i]
    ts = df_test.index[i]
    est_h = int(row["est_hour"])
    date = row["date"]
    o, h, l, c = float(row["open"]), float(row["high"]), float(row["low"]), float(row["close"])
    
    # New day
    if date != last_date:
        if last_date is not None:
            print(f"\n--- New day: {date} (was {last_date}) ---")
            print(f"    Active trades: {len(active_trades)}, asian_complete={asian_range_complete}, tier={tier}")
        for t in active_trades:
            if t.exit_time is None:
                direction_mult = 1 if t.direction == CascadeDirection.LONG else -1
                t.pnl_pips = (c - t.entry_price) * direction_mult * 10000
                t.exit_time = ts
                t.exit_price = c
                t.result = "win" if t.pnl_pips > 0 else "loss"
                t.exit_reason = "new_day"
                all_trades.append(t)
        active_trades = [t for t in active_trades if t.exit_time is None]
        asian_high = None
        asian_low = None
        asian_range_pips = None
        tier = TierStatus.NA
        asian_range_complete = False
        session_direction = CascadeDirection.NONE
        initial_p90_time = None
        initial_p90_price = None
        cascade_count = 0
        add_45min_done = False
        kill_switch_triggered = False
        daily_loss_limit_hit = False
        last_date = date
    
    # Asian session
    in_asian = est_h >= 19 or est_h < 3
    if in_asian:
        if asian_high is None:
            asian_high = h
            asian_low = l
        else:
            asian_high = max(asian_high, h)
            asian_low = min(asian_low, l)
        if est_h == 3 and asian_high is not None:
            asian_range_pips = (asian_high - asian_low) * 10000
            if asian_range_pips < 20: tier = TierStatus.T1
            elif asian_range_pips < 30: tier = TierStatus.T2
            elif asian_range_pips < 45: tier = TierStatus.T3
            else: tier = TierStatus.NO_GO
            asian_range_complete = True
            print(f"  Asian finalized at {ts}: AR={asian_range_pips:.1f}p, Tier={tier.value}")
        continue
    
    if not asian_range_complete:
        continue
    if tier == TierStatus.NO_GO:
        continue
    if daily_loss_limit_hit:
        continue
    
    # Hard exit
    if est_h >= 12:
        for t in active_trades:
            if t.exit_time is None:
                direction_mult = 1 if t.direction == CascadeDirection.LONG else -1
                t.pnl_pips = (c - t.entry_price) * direction_mult * 10000
                t.exit_time = ts
                t.exit_price = c
                t.result = "win" if t.pnl_pips > 0 else "loss"
                t.exit_reason = "hard_exit_12pm"
                all_trades.append(t)
        active_trades = [t for t in active_trades if t.exit_time is None]
        session_direction = CascadeDirection.NONE
        continue
    
    # Manage trades (simplified - just check SL/TP)
    to_remove = []
    for t in active_trades:
        if t.exit_time is not None: continue
        is_long = t.direction == CascadeDirection.LONG
        if is_long and l <= t.sl_price:
            t.pnl_pips = (t.sl_price - t.entry_price) * 10000
            t.exit_time = ts; t.exit_price = t.sl_price; t.result = "loss"; t.exit_reason = "sl"
            all_trades.append(t); to_remove.append(t); continue
        elif not is_long and h >= t.sl_price:
            t.pnl_pips = (t.entry_price - t.sl_price) * 10000
            t.exit_time = ts; t.exit_price = t.sl_price; t.result = "loss"; t.exit_reason = "sl"
            all_trades.append(t); to_remove.append(t); continue
        if is_long and h >= t.tp_price:
            t.pnl_pips = (t.tp_price - t.entry_price) * 10000
            t.exit_time = ts; t.exit_price = t.tp_price; t.result = "win"; t.exit_reason = "tp_50"
            all_trades.append(t); to_remove.append(t); continue
        elif not is_long and l <= t.tp_price:
            t.pnl_pips = (t.entry_price - t.tp_price) * 10000
            t.exit_time = ts; t.exit_price = t.tp_price; t.result = "win"; t.exit_reason = "tp_50"
            all_trades.append(t); to_remove.append(t); continue
    for t in to_remove:
        if t in active_trades: active_trades.remove(t)
    
    if not (2 <= est_h < 11):
        continue
    if asian_range_pips is None or asian_range_pips <= 0:
        continue
    
    # P90 check
    total_range = h - l
    if total_range <= 0: continue
    body_size = abs(c - o)
    body_pct = body_size / total_range
    body_pips = body_size * 10000
    
    thresholds = {(2,4):4.1, (4,6):4.6, (6,8):4.6, (8,10):5.9, (10,11):6.2}
    threshold = 6.2
    for (s,e), t2 in thresholds.items():
        if s <= est_h < e:
            threshold = t2
            break
    
    is_p90 = body_pct > 0.60 and body_pips >= threshold
    if not is_p90: continue
    
    direction = CascadeDirection.LONG if c > o else CascadeDirection.SHORT
    print(f"  P90 at {ts} (est={est_h}): {direction.value}, body={body_pips:.1f}p, thresh={threshold}")
    
    if session_direction == CascadeDirection.NONE:
        session_direction = direction
        initial_p90_time = ts
        initial_p90_price = c
        cascade_count = 1
        add_45min_done = False
        
        sl_pips = body_pips * 0.80
        sl_offset = sl_pips / 10000
        tp_offset = asian_range_pips * 0.50 / 10000
        
        if direction == CascadeDirection.LONG:
            sl_price = c - sl_offset
            tp_price = asian_high + tp_offset
        else:
            sl_price = c + sl_offset
            tp_price = asian_low - tp_offset
        
        print(f"    -> INITIAL: entry={c:.5f}, SL={sl_price:.5f}, TP={tp_price:.5f}")
        print(f"    -> Asian H/L: {asian_high:.5f}/{asian_low:.5f}, AR={asian_range_pips:.1f}p")
        
        trade = type('T', (), {
            'entry_time': ts, 'direction': direction, 'entry_price': c,
            'sl_price': sl_price, 'tp_price': tp_price, 'size_lots': 0.1,
            'activation_type': 'initial', 'cascade_num': 0,
            'exit_time': None, 'exit_price': None, 'pnl_pips': 0.0,
            'result': '', 'exit_reason': ''
        })()
        active_trades.append(trade)

print(f"\n=== RESULTS ===")
print(f"Total trades: {len(all_trades)}")
print(f"Active (unclosed): {len([t for t in active_trades if t.exit_time is None])}")
for t in all_trades:
    print(f"  {t.entry_time} {t.direction.value}: entry={t.entry_price:.5f}, exit={t.exit_price}, pnl={t.pnl_pips:.1f}p, {t.result} ({t.exit_reason})")
