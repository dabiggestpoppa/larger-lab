"""Debug BTC OCC+Buffer backtest"""
import sys, time
from datetime import datetime, timedelta, timezone
from collections import Counter
sys.path.insert(0, 'quant-lab/engines')
from symmetry_trap import SymmetryTrapEngine, Bar, TradeDirection
import ccxt

exchange = ccxt.binance({'enableRateLimit': True})
now_ms = int(time.time() * 1000)
start_ms = now_ms - 90 * 24 * 3600 * 1000

all_candles = []
current_since = start_ms
for i in range(90):
    ohlcv = exchange.fetch_ohlcv('BTC/USDT', '5m', since=current_since, limit=1000)
    if not ohlcv: break
    all_candles.extend(ohlcv)
    current_since = ohlcv[-1][0] + 1
    if len(ohlcv) < 1000: break
    time.sleep(0.1)

print(f"Fetched {len(all_candles)} candles")

config = {
    "pip_value": 1.0,
    "tiers": {
        "T1": {"ar_max": 3000.0, "au": 200.0, "trigger": 240.0},
        "T2": {"ar_max": 5000.0, "au": 500.0, "trigger": 600.0},
        "T3": {"ar_max": 8000.0, "au": 1000.0, "trigger": 1200.0},
    }
}

SPREAD_BUFFER = 50.0
engine = SymmetryTrapEngine(config=config)
trades = []
current_date = None
EST = timezone(timedelta(hours=-5))
sessions_initialized = 0

for i, c in enumerate(all_candles):
    dt = datetime.fromtimestamp(c[0]/1000, tz=timezone.utc).astimezone(EST)
    bar = Bar(timestamp=dt, open=float(c[1]), high=float(c[2]), low=float(c[3]), close=float(c[4]))
    bar_date = dt.date()

    if dt.hour == 3 and dt.minute == 0 and bar_date != current_date:
        current_date = bar_date
        asian_bars = []
        for j in range(i, -1, -1):
            b_dt = datetime.fromtimestamp(all_candles[j][0]/1000, tz=timezone.utc).astimezone(EST)
            if b_dt.date() != bar_date: break
            if b_dt.hour >= 19 or b_dt.hour < 3: asian_bars.append(all_candles[j])
        if asian_bars:
            ah = max(float(b[2]) for b in asian_bars)
            al = min(float(b[3]) for b in asian_bars)
            ar = ah - al
            engine.initialize_session(ah, al)
            sessions_initialized += 1
            if sessions_initialized <= 3:
                print(f"Session {sessions_initialized}: {bar_date}, AR={ar:.1f}, active={engine.session_active}, tier={engine.tier_name}, state={engine.state}")

    if dt.hour == 12 and dt.minute == 0: engine.hard_exit()
    if not engine.session_active: continue

    signal = engine.process_bar(bar)

    if signal and signal.event == "ENTRY":
        direction = signal.direction
        entry_px = signal.entry_price
        if direction == TradeDirection.LONG:
            sl_px = signal.sl_price - SPREAD_BUFFER
        else:
            sl_px = signal.sl_price + SPREAD_BUFFER
        tp_px = signal.tp_price

        pnl_pips = None
        exit_type = "END"
        for tb in all_candles[i+1:]:
            if direction == TradeDirection.LONG:
                if tb[3] <= sl_px: pnl_pips = (sl_px - entry_px); exit_type = "SL"; break
                if tb[2] >= tp_px: pnl_pips = (tp_px - entry_px); exit_type = "TP"; break
            else:
                if tb[2] >= sl_px: pnl_pips = (entry_px - sl_px); exit_type = "SL"; break
                if tb[3] <= tp_px: pnl_pips = (entry_px - tp_px); exit_type = "TP"; break

        if pnl_pips is None:
            lc = float(all_candles[-1][4])
            pnl_pips = ((lc - entry_px) if direction == TradeDirection.LONG else (entry_px - lc))
        trades.append({"pnl_pips": pnl_pips, "exit": exit_type, "direction": "LONG" if direction == TradeDirection.LONG else "SHORT", "tier": engine.tier_name})

total = len(trades)
wins = sum(1 for t in trades if t["pnl_pips"] > 0)
losses = total - wins
wr = wins/total*100 if total > 0 else 0
pnl = sum(t["pnl_pips"] for t in trades)
tp_hits = sum(1 for t in trades if t["exit"] == "TP")
sl_hits = sum(1 for t in trades if t["exit"] == "SL")
days = (datetime.fromtimestamp(all_candles[-1][0]/1000, tz=timezone.utc) - datetime.fromtimestamp(all_candles[0][0]/1000, tz=timezone.utc)).days
tr_per_day = total/days if days > 0 else 0
tiers = Counter(t["tier"] for t in trades)

print(f"\n=== OCC+Buffer Backtest ({days} days, BTC 5m) ===")
print(f"Sessions initialized: {sessions_initialized}")
print(f"Trades: {total} | WR: {wr:.1f}% | PnL: {pnl:.0f} pips")
print(f"TP: {tp_hits} | SL: {sl_hits} | Tr/Day: {tr_per_day:.1f}")
print(f"Tier dist: {dict(tiers)}")
if wins > 0: print(f"Avg win: {sum(t['pnl_pips'] for t in trades if t['pnl_pips']>0)/wins:.1f} pips")
if losses > 0: print(f"Avg loss: {sum(t['pnl_pips'] for t in trades if t['pnl_pips']<0)/losses:.1f} pips")
