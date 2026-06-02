"""
Replay today's 37 bridge signals through engine SL/TP logic to determine
hypothetical wins/losses if they had been executed.
"""
import json, sys, os
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab")

import MetaTrader5 as mt5
mt5.initialize()

SIGNALS_FILE = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\live_logs\signals.jsonl"

# Read all signals
signals = []
with open(SIGNALS_FILE, "r") as f:
    for line in f:
        line = line.strip()
        if line:
            try:
                signals.append(json.loads(line))
            except:
                pass

print("Total signals in file: %d" % len(signals))

# Filter to only ENTRY signals from the bridge (after 12:24 PM)
bridge_entries = []
for s in signals:
    ts = s.get("timestamp", "")
    if ts >= "2026-06-01T12:24" and s.get("event") == "ENTRY":
        bridge_entries.append(s)

print("Bridge ENTRY signals after 12:24 PM: %d" % len(bridge_entries))

# Show all ENTRY signals with details
for s in bridge_entries:
    print("  %s %s %s @ %.5f SL=%.5f TP=%.5f eng=%s" % (
        ts[:19], s.get("symbol"), s.get("direction"), s.get("entry_price"),
        s.get("sl"), s.get("tp"), s.get("source","?")))

# Now fetch actual price data to determine outcome of each trade
print("\n--- OUTCOME ANALYSIS ---")
wins = 0
losses = 0
total_pnl_pips = 0.0

for s in bridge_entries:
    sym = s.get("symbol")
    direction = s.get("direction")
    entry = s.get("entry_price")
    sl = s.get("sl")
    tp = s.get("tp")
    ts = s.get("timestamp", "")
    
    # Parse entry time
    try:
        from datetime import datetime
        entry_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        entry_ts = int(entry_dt.timestamp())
    except:
        entry_ts = 0
    
    # Fetch M1 bars from entry time to now + 30 min
    bars = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M1, 0, 1000)
    if bars is None:
        # Try from a date range
        from datetime import datetime, timezone
        end_dt = datetime(2026, 6, 1, 23, 59, tzinfo=timezone.utc)
        start_dt = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
        bars = mt5.copy_rates_range(sym, mt5.TIMEFRAME_M1, start_dt, end_dt)
    
    if bars is None or len(bars) == 0:
        print("  %s %s @ %.5f -> NO DATA" % (sym, direction, entry))
        continue
    
    # Find bars after entry time
    outcome = None
    outcome_bar = None
    if entry_ts > 0:
        after_bars = [b for b in bars if b['time'] >= entry_ts]
    else:
        after_bars = bars[-200:]  # Use last 200 bars if no timestamp
    
    if not after_bars:
        print("  %s %s @ %.5f -> NO BARS AFTER ENTRY" % (sym, direction, entry))
        continue
    
    for bar in after_bars:
        if direction == "BUY":
            # SL hit?
            if bar['low'] <= sl:
                outcome = "SL_HIT"
                outcome_bar = bar
                break
            # TP hit?
            if bar['high'] >= tp:
                outcome = "TP_HIT"
                outcome_bar = bar
                break
        else:  # SELL
            # SL hit?
            if bar['high'] >= sl:
                outcome = "SL_HIT"
                outcome_bar = bar
                break
            # TP hit?
            if bar['low'] <= tp:
                outcome = "TP_HIT"
                outcome_bar = bar
                break
    
    if outcome == "TP_HIT":
        wins += 1
        if direction == "BUY":
            pnl = tp - entry
        else:
            pnl = entry - tp
        total_pnl_pnl = pnl  # will sum later
        print("  ✅ %s %s @ %.5f → TP_HIT bar_time=%s pnl=%.1fp" % (
            sym, direction, entry, outcome_bar['time'], pnl * 100000))
    elif outcome == "SL_HIT":
        losses += 1
        if direction == "BUY":
            pnl = entry - sl
        else:
            pnl = sl - entry
        print("  ❌ %s %s @ %.5f → SL_HIT bar_time=%s pnl=%.1fp" % (
            sym, direction, entry, outcome_bar['time'], pnl * 100000))
    else:
        # Still open — check current P&L
        last_close = after_bars[-1]['close']
        if direction == "BUY":
            pnl = last_close - entry
        else:
            pnl = entry - last_close
        print("  ⏳ %s %s @ %.5f → STILL_OPEN last_close=%.5f pnl=%.1fp" % (
            sym, direction, entry, last_close, pnl * 100000))

total = wins + losses
print("\n--- SUMMARY ---")
print("Resolved trades: %d" % total)
print("  Wins: %d" % wins)
print("  Losses: %d" % losses)
if total > 0:
    print("  WR: %.1f%%" % (wins / total * 100))

mt5.shutdown()
