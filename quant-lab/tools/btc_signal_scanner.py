"""
BTC Signal Scanner — Symmetry Trap
===================================
Fetches recent BTC 5m data from Binance, runs through ST engine,
outputs live signals with entry/SL/TP/direction.

Usage:
    python quant-lab/tools/btc_signal_scanner.py
    python quant-lab/tools/btc_signal_scanner.py --lookback 500
"""

import sys, time, json
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab")))
sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs")))
sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines")))

from asset_configs import ASSET_CONFIGS
from symmetry_trap import SymmetryTrapEngine, TradeSignal, Bar, TradeDirection

EST = timezone(timedelta(hours=-5))


def fetch_recent_candles(lookback=500):
    """Fetch recent BTC 5m candles from Binance."""
    import ccxt
    exchange = ccxt.binance({'enableRateLimit': True})
    ohlcv = exchange.fetch_ohlcv('BTC/USDT', '5m', limit=lookback)
    candles = []
    for c in ohlcv:
        dt = datetime.fromtimestamp(c[0]/1000, tz=timezone.utc).astimezone(EST)
        candles.append({
            't': c[0], 'dt': dt,
            'o': float(c[1]), 'h': float(c[2]), 'l': float(c[3]), 'c': float(c[4]),
        })
    return candles


def run_scanner(lookback=500):
    """Run ST scanner on recent data and output signals."""
    config = ASSET_CONFIGS.get("BTCUSD", {
        "tiers": {"T1": {"ar_max": 1500.0, "au": 120.0, "trigger": 140.0}}
    })

    print(f"[Scanner] Fetching {lookback} recent BTC 5m candles...")
    candles = fetch_recent_candles(lookback)
    if not candles:
        print("[Scanner] No data!")
        return

    print(f"[Scanner] Got {len(candles)} candles, "
          f"{candles[0]['dt'].strftime('%Y-%m-%d %H:%M')} -> {candles[-1]['dt'].strftime('%Y-%m-%d %H:%M')}")

    engine = SymmetryTrapEngine(config=config)
    signals = []
    current_date = None

    for i, c in enumerate(candles):
        bar = Bar(timestamp=c['dt'], open=c['o'], high=c['h'], low=c['l'], close=c['c'])
        bar_date = c['dt'].date()

        # Session init at 3AM EST
        if c['dt'].hour == 3 and c['dt'].minute == 0 and bar_date != current_date:
            current_date = bar_date
            asian_bars = []
            for j in range(i, -1, -1):
                if candles[j]['dt'].date() != bar_date and candles[j]['dt'].date() != current_date:
                    break
                if candles[j]['dt'].hour >= 19 or candles[j]['dt'].hour < 3:
                    asian_bars.append(candles[j])
            if asian_bars:
                ah = max(b['h'] for b in asian_bars)
                al = min(b['l'] for b in asian_bars)
                engine.initialize_session(ah, al)

        if c['dt'].hour == 12 and c['dt'].minute == 0:
            engine.hard_exit()

        if not engine.session_active:
            continue

        signal = engine.process_bar(bar)

        if signal:
            sig = {
                "time": c['dt'].strftime('%Y-%m-%d %H:%M'),
                "event": signal.event,
                "direction": "LONG" if signal.direction == TradeDirection.LONG else "SHORT" if signal.direction == TradeDirection.SHORT else "FLAT",
                "entry": signal.entry_price,
                "sl": signal.sl_price,
                "tp": signal.tp_price,
                "au": signal.au_used,
                "tier": engine.tier_name,
                "price": c['c'],
            }
            signals.append(sig)

            # Print signal
            if signal.event == "ENTRY":
                print(f"\n  *** ENTRY SIGNAL ***")
                print(f"  Time:     {sig['time']}")
                print(f"  Direction: {sig['direction']}")
                print(f"  Entry:    {sig['entry']:.1f}")
                print(f"  SL:       {sig['sl']:.1f}")
                print(f"  TP:       {sig['tp']:.1f}")
                print(f"  AU:       {sig['au']:.1f}")
                print(f"  Tier:     {sig['tier']}")
                print(f"  Price:    {sig['price']:.1f}")
            elif signal.event in ("TP_HIT", "SL_HIT", "KILL_SWITCH"):
                print(f"\n  <<< EXIT: {signal.event} at {sig['time']} >>>")

    # Summary
    entries = [s for s in signals if s['event'] == 'ENTRY']
    print(f"\n[Scanner] Complete. {len(entries)} entry signals found in {len(candles)} bars.")

    if entries:
        print(f"\n  Latest signals:")
        for sig in entries[-5:]:
            print(f"    {sig['time']} | {sig['direction']:>5s} | entry={sig['entry']:.1f} | sl={sig['sl']:.1f} | tp={sig['tp']:.1f} | {sig['tier']}")

    # Check if we're currently in a session
    if engine.session_active:
        print(f"\n  [ACTIVE SESSION] Tier={engine.tier_name}, State={engine.state}")
        if engine.state == "IN_TRADE":
            print(f"  Direction: {'LONG' if engine.impulse_direction == TradeDirection.LONG else 'SHORT'}")
            print(f"  Entry: {engine.entry_price:.1f}, SL: {engine.sl_price:.1f}, TP: {engine.tp_price:.1f}")
    else:
        print(f"\n  [NO ACTIVE SESSION] Last state: {engine.state}")

    return signals


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--lookback", type=int, default=500, help="Number of 5m candles to scan")
    args = parser.parse_args()

    print("=" * 60)
    print("  BTC SIGNAL SCANNER — Symmetry Trap")
    print("=" * 60)
    signals = run_scanner(args.lookback)
