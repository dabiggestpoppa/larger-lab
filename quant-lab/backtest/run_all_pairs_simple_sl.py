"""
Multi-Pair Symmetry Trap Backtest — Simple Buffer SL
=====================================================
Runs ST with simple buffer SL across all available pairs.
Uses cached Binance 5m data where available.

SL = entry ± AU buffer (no OCC extreme, no profit lock)
TP = 1 AU from entry
"""
import sys, time, json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import Counter, defaultdict

sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab")))
sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs")))
sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines")))

from asset_configs import ASSET_CONFIGS
from symmetry_trap_simple_sl import SymmetryTrapEngineSimpleSL, Bar, TradeDirection, DEFAULT_TIER_CONFIG
import ccxt

EST = timezone(timedelta(hours=-5))

# Map ASSET_CONFIGS keys to Binance symbols
PAIR_MAP = {
    "BTCUSD": "BTC/USDT",
    "ETHUSD": "ETH/USDT",
    "SOLUSD": "SOL/USDT",
    "AVAXUSD": "AVAX/USDT",
    "DOGEUSD": "DOGE/USDT",
    "XRPUSD": "XRP/USDT",
    "LINKUSD": "LINK/USDT",
    "MATICUSD": "MATIC/USDT",
    "BNBUSD": "BNB/USDT",
    "LTCUSD": "LTC/USDT",
    "DOTUSD": "DOT/USDT",
    "UNIUSD": "UNI/USDT",
    "AAVEUSD": "AAVE/USDT",
    "NEARUSD": "NEAR/USDT",
    "APTUSD": "APT/USDT",
    "SUIUSD": "SUI/USDT",
    "TRXUSD": "TRX/USDT",
    "FILUSD": "FIL/USDT",
    "ARBUSD": "ARB/USDT",
    "OPUSD": "OP/USDT",
    "INJUSD": "INJ/USDT",
    "STXUSD": "STX/USDT",
    "CFXUSD": "CFX/USDT",
    "GMXUSD": "GMX/USDT",
    "SNXUSD": "SNX/USDT",
    "RUNEUSD": "RUNE/USDT",
    "SEIUSD": "SEI/USDT",
    "JUPUSD": "JUP/USDT",
    "WIFUSD": "WIF/USDT",
    "ONDOUSD": "ONDO/USDT",
    "ENAUSD": "ENA/USDT",
    "WUSD": "W/USDT",
    "TONUSD": "TON/USDT",
    "BONKUSD": "BONK/USDT",
    "PEPEUSD": "PEPE/USDT",
    "kPEPEUSD": "1000PEPE/USDT",
}

# Buffer size in pips (same as AU for simple SL)
# For FX: 10-20 pips, for Crypto: 200-1000 pips


def fetch_candles(symbol: str, days: int = 1460) -> list:
    """Fetch candles from Binance."""
    cache_path = Path(f"quant-lab/data/{symbol.lower().replace('/', '_')}_{days}d.json")
    # Check for pre-cached 4yr data
    for alt_name in [f"quant-lab/data/{symbol.lower().replace('/', '_')}_5m_4yr.json"]:
        alt = Path(alt_name)
        if not cache_path.exists() and alt.exists():
            cache_path = alt
            break
    if cache_path.exists():
        with open(cache_path) as f:
            return json.load(f)

    exchange = ccxt.binance({'enableRateLimit': True})
    now_ms = int(time.time() * 1000)
    start_ms = now_ms - days * 24 * 3600 * 1000

    all_candles = []
    current_since = start_ms
    for i in range(500):
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, '5m', since=current_since, limit=1000)
        except Exception as e:
            print(f"  Error fetching {symbol}: {e}")
            break
        if not ohlcv:
            break
        batch = [c for c in ohlcv if c[0] >= start_ms and c[0] <= now_ms]
        if not batch:
            break
        existing_ts = set(c[0] for c in all_candles)
        new_candles = [c for c in batch if c[0] not in existing_ts]
        all_candles.extend(new_candles)
        if len(batch) < 1000:
            break
        current_since = batch[-1][0] + 1
        time.sleep(0.1)

    all_candles.sort(key=lambda x: x[0])
    if all_candles:
        with open(cache_path, 'w') as f:
            json.dump(all_candles, f)
    return all_candles


def run_pair_backtest(symbol: str, candles: list, config: dict) -> dict:
    """Run ST Simple SL backtest for a single pair."""
    engine = SymmetryTrapEngineSimpleSL(
        pip_size=config.get("pip_value", 0.0001),
        tier_config=config.get("tiers", DEFAULT_TIER_CONFIG),
        symbol=symbol,
        config=config,
    )

    current_date = None
    trades = []

    for i, c in enumerate(candles):
        dt_utc = datetime.fromtimestamp(c[0] / 1000, tz=timezone.utc)
        dt_est = dt_utc.astimezone(EST)
        # Bar timestamp must be UTC (engine's _est_hour converts UTC->EST)
        bar = Bar(timestamp=dt_utc, open=float(c[1]), high=float(c[2]), low=float(c[3]), close=float(c[4]))
        bar_date = dt_est.date()

        # Session init at 3AM EST
        if dt_est.hour == 3 and dt_est.minute == 0 and bar_date != current_date:
            current_date = bar_date
            asian_bars = []
            for j in range(i, -1, -1):
                b_dt = datetime.fromtimestamp(candles[j][0] / 1000, tz=timezone.utc).astimezone(EST)
                if b_dt.date() != bar_date:
                    break
                if b_dt.hour >= 19 or b_dt.hour < 3:
                    asian_bars.append(candles[j])
            if asian_bars:
                ah = max(float(b[2]) for b in asian_bars)
                al = min(float(b[3]) for b in asian_bars)
                engine.initialize_session(ah, al)

        if dt_est.hour == 12 and dt_est.minute == 0:
            engine.hard_exit()

        if not engine.session_active:
            continue

        signal = engine.process_bar(bar)

        if signal and signal.event == "ENTRY":
            direction = signal.direction
            entry_px = signal.entry_price
            sl_px = signal.sl_price
            tp_px = signal.tp_price

            pnl_pips = None
            exit_type = "END"
            for tb in candles[i + 1:]:
                if direction == TradeDirection.LONG:
                    if tb[2] >= tp_px:
                        pnl_pips = (tp_px - entry_px) / engine.pip_size
                        exit_type = "TP"
                        break
                    if tb[3] <= sl_px:
                        pnl_pips = (sl_px - entry_px) / engine.pip_size
                        exit_type = "SL"
                        break
                else:
                    if tb[3] <= tp_px:
                        pnl_pips = (entry_px - tp_px) / engine.pip_size
                        exit_type = "TP"
                        break
                    if tb[2] >= sl_px:
                        pnl_pips = (entry_px - sl_px) / engine.pip_size
                        exit_type = "SL"
                        break

            if pnl_pips is None:
                lc = float(candles[-1][4])
                pnl_pips = ((lc - entry_px) if direction == TradeDirection.LONG else (entry_px - lc)) / engine.pip_size

            trades.append({
                "pnl_pips": pnl_pips,
                "exit": exit_type,
                "direction": "LONG" if direction == TradeDirection.LONG else "SHORT",
                "tier": engine.tier_name,
            })

    total = len(trades)
    if total == 0:
        return {"trades": 0}

    wins = sum(1 for t in trades if t["pnl_pips"] > 0)
    losses = total - wins
    wr = wins / total * 100.0
    pnl = sum(t["pnl_pips"] for t in trades)
    tp_hits = sum(1 for t in trades if t["exit"] == "TP")
    sl_hits = sum(1 for t in trades if t["exit"] == "SL")
    days = (datetime.fromtimestamp(candles[-1][0] / 1000, tz=timezone.utc) -
            datetime.fromtimestamp(candles[0][0] / 1000, tz=timezone.utc)).days
    tr_per_day = total / days if days > 0 else 0
    tiers = Counter(t["tier"] for t in trades)
    avg_win = sum(t["pnl_pips"] for t in trades if t["pnl_pips"] > 0) / wins if wins > 0 else 0
    avg_loss = sum(t["pnl_pips"] for t in trades if t["pnl_pips"] < 0) / losses if losses > 0 else 0

    return {
        "trades": total, "wins": wins, "losses": losses,
        "win_rate": round(wr, 1), "pnl_pips": round(pnl, 1),
        "tp_hits": tp_hits, "sl_hits": sl_hits,
        "tr_per_day": round(tr_per_day, 1), "days": days,
        "avg_win": round(avg_win, 1), "avg_loss": round(avg_loss, 1),
        "tier_dist": dict(tiers),
        "pf": round(abs(avg_win * wins) / abs(avg_loss * losses), 2) if losses > 0 and avg_loss != 0 else float("inf"),
    }


def main():
    report_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\hyperliquid_full")
    report_dir.mkdir(parents=True, exist_ok=True)

    all_results = {}

    for asset_key, binance_symbol in PAIR_MAP.items():
        print(f"\n{'='*60}")
        print(f"  {asset_key} ({binance_symbol})")
        print(f"{'='*60}")

        config = ASSET_CONFIGS.get(asset_key)
        if not config:
            print(f"  No config for {asset_key}, skipping")
            continue

        print(f"  Fetching data...")
        candles = fetch_candles(binance_symbol, 1460)
        if not candles:
            print(f"  No data for {binance_symbol}, skipping")
            continue

        print(f"  {len(candles)} candles loaded")
        result = run_pair_backtest(asset_key, candles, config)
        all_results[asset_key] = result

        if result["trades"] > 0:
            print(f"  Trades: {result['trades']} | WR: {result['win_rate']}% | PnL: {result['pnl_pips']:.0f}")
            print(f"  TP: {result['tp_hits']} | SL: {result['sl_hits']} | Tr/Day: {result['tr_per_day']}")
            print(f"  Avg Win: {result['avg_win']} | Avg Loss: {result['avg_loss']} | PF: {result['pf']}")
            print(f"  Tiers: {result['tier_dist']}")
        else:
            print(f"  No trades generated")

    # Summary table
    print(f"\n\n{'='*90}")
    print(f"  MULTI-PAIR SIMPLE SL BACKTEST SUMMARY")
    print(f"{'='*90}")
    h = f"{'Pair':<10} {'Trades':>8} {'WR%':>8} {'PnL':>12} {'TP':>6} {'SL':>6} {'Tr/D':>6} {'PF':>6}"
    print(h)
    print("-" * 70)
    for sym, r in sorted(all_results.items(), key=lambda x: x[1].get("pnl_pips", 0), reverse=True):
        if r["trades"] > 0:
            print(f"{sym:<10} {r['trades']:>8} {r['win_rate']:>7.1f}% {r['pnl_pips']:>10.0f} {r['tp_hits']:>6} {r['sl_hits']:>6} {r['tr_per_day']:>5.1f} {r['pf']:>5.2f}")

    # Save all results
    with open(report_dir / "multi_pair_simple_sl.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to {report_dir / 'multi_pair_simple_sl.json'}")


if __name__ == "__main__":
    main()
