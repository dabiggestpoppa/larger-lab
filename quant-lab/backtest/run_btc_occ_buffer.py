"""BTC OCC+Buffer Full Backtest (4-Year, 5m)"""
import sys, time, json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import Counter
sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab")))
sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs")))
sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines")))
from asset_configs import ASSET_CONFIGS
from symmetry_trap import SymmetryTrapEngine, TradeSignal, Bar, TradeDirection
import ccxt

exchange = ccxt.binance({'enableRateLimit': True})
now_ms = int(time.time() * 1000)
start_ms = now_ms - 1460 * 24 * 3600 * 1000

all_candles = []
current_since = start_ms
req_count = 0
print("[Binance] Fetching 4 years of BTC 5m...")
while current_since < now_ms and req_count < 500:
    ohlcv = exchange.fetch_ohlcv('BTC/USDT', '5m', since=current_since, limit=1000)
    if not ohlcv: break
    batch = [c for c in ohlcv if c[0] >= start_ms and c[0] <= now_ms]
    if not batch: break
    existing_ts = set(c[0] for c in all_candles)
    new_candles = [c for c in batch if c[0] not in existing_ts]
    all_candles.extend(new_candles)
    if req_count % 100 == 0:
        print(f"  req {req_count+1}: {len(new_candles)} new, total: {len(all_candles)}")
    if len(batch) < 1000: break
    current_since = batch[-1][0] + 1
    req_count += 1
    time.sleep(0.1)
all_candles.sort(key=lambda x: x[0])
print(f"[Binance] Total: {len(all_candles)} candles")

config = ASSET_CONFIGS["BTCUSD"]
SPREAD_BUFFER = config.get("sl_buffer", 50.0)
print(f"Config: pip_value={config['pip_value']}, sl_buffer={SPREAD_BUFFER}")
print(f"Tiers: { {k: v['ar_max'] for k,v in config['tiers'].items()} }")

engine = SymmetryTrapEngine(config=config)
trades = []
current_date = None
EST = timezone(timedelta(hours=-5))

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
            engine.initialize_session(ah, al)

    if dt.hour == 12 and dt.minute == 0: engine.hard_exit()
    if not engine.session_active: continue

    signal = engine.process_bar(bar)

    if signal and signal.event == "ENTRY":
        direction = signal.direction
        entry_px = signal.entry_price
        # OCC+Buffer SL
        if direction == TradeDirection.LONG:
            sl_px = signal.sl_price - SPREAD_BUFFER
        else:
            sl_px = signal.sl_price + SPREAD_BUFFER
        tp_px = signal.tp_price

        pnl_pips = None; exit_type = "END"
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
wr = wins/total*100 if total > 0 else 0
pnl = sum(t["pnl_pips"] for t in trades)
tp_hits = sum(1 for t in trades if t["exit"] == "TP")
sl_hits = sum(1 for t in trades if t["exit"] == "SL")
days = (datetime.fromtimestamp(all_candles[-1][0]/1000, tz=timezone.utc) - datetime.fromtimestamp(all_candles[0][0]/1000, tz=timezone.utc)).days
tr_per_day = total/days if days > 0 else 0
tiers = Counter(t["tier"] for t in trades)

print(f"\n{'='*65}")
print(f"  OCC+Buffer Full Backtest — BTCUSD ({days} days, 5m)")
print(f"{'='*65}")
print(f"Trades: {total} | WR: {wr:.1f}% | PnL: {pnl:.0f} pips")
print(f"TP: {tp_hits} | SL: {sl_hits} | Tr/Day: {tr_per_day:.1f}")
print(f"Tier dist: {dict(tiers)}")
if wins > 0: print(f"Avg win: {sum(t['pnl_pips'] for t in trades if t['pnl_pips']>0)/wins:.1f} pips")
if losses > 0: print(f"Avg loss: {sum(t['pnl_pips'] for t in trades if t['pnl_pips']<0)/losses:.1f} pips")

# Save
report_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\hyperliquid_full")
report_dir.mkdir(parents=True, exist_ok=True)
result = {"total_trades": total, "wins": wins, "losses": losses, "win_rate": round(wr,1), "total_pnl_pips": round(pnl,1), "tp_hits": tp_hits, "sl_hits": sl_hits, "tr_per_day": round(tr_per_day,1), "tier_dist": dict(tiers), "days": days}
with open(report_dir / "btc_occ_buffer_4yr.json", "w") as f:
    json.dump(result, f, indent=2)
print(f"Results saved.")
