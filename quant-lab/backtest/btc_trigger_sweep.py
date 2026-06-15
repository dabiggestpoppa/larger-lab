"""
BTC Trigger Sweep — 4-Year Backtest
====================================
Sweeps T1 trigger values to find optimal WR vs trade frequency balance.
Uses pre-fetched Binance 5m data.
"""

import sys, time, json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab")))
sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs")))
sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines")))
sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data")))

from asset_configs import ASSET_CONFIGS
from symmetry_trap import SymmetryTrapEngine, TradeSignal, Bar, TradeDirection

EST = timezone(timedelta(hours=-5))


def fetch_binance_5m(days=1460):
    import ccxt
    exchange = ccxt.binance({'enableRateLimit': True})
    now_ms = int(time.time() * 1000)
    start_ms = now_ms - days * 24 * 3600 * 1000

    all_candles = []
    current_since = start_ms
    req_count = 0

    print(f"[Binance] Fetching {days} days of BTC 5m...")

    while current_since < now_ms and req_count < 500:
        try:
            ohlcv = exchange.fetch_ohlcv('BTC/USDT', '5m', since=current_since, limit=1000)
            if not ohlcv:
                break
            batch = [c for c in ohlcv if c[0] >= start_ms and c[0] <= now_ms]
            if not batch:
                break
            existing_ts = set(c[0] for c in all_candles)
            new_candles = [c for c in batch if c[0] not in existing_ts]
            all_candles.extend(new_candles)
            newest = batch[-1][0]
            if req_count % 100 == 0:
                print(f"  req {req_count+1}: {len(new_candles)} new, total: {len(all_candles)}")
            if len(batch) < 1000:
                break
            current_since = newest + 1
            req_count += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            time.sleep(2)

    all_candles.sort(key=lambda x: x[0])
    print(f"[Binance] Total: {len(all_candles)} candles")
    return all_candles


def run_backtest(candles, t1_trigger):
    """Run ST backtest with a specific T1 trigger value."""
    config = {
        "tiers": {
            "T1": {"ar_max": 1500.0, "au": t1_trigger * 0.85, "trigger": t1_trigger},
            "T2": {"ar_max": 3000.0, "au": t1_trigger * 1.5, "trigger": t1_trigger * 1.5},
            "T3": {"ar_max": 7000.0, "au": t1_trigger * 2.5, "trigger": t1_trigger * 2.5},
        }
    }

    engine = SymmetryTrapEngine(config=config)
    trades = []
    current_date = None

    for i, c in enumerate(candles):
        dt = datetime.fromtimestamp(c[0]/1000, tz=timezone.utc).astimezone(EST)
        bar = Bar(timestamp=dt, open=float(c[1]), high=float(c[2]), low=float(c[3]), close=float(c[4]))
        bar_date = dt.date()

        if dt.hour == 3 and dt.minute == 0 and bar_date != current_date:
            current_date = bar_date
            asian_bars = []
            for j in range(i, -1, -1):
                b_dt = datetime.fromtimestamp(candles[j][0]/1000, tz=timezone.utc).astimezone(EST)
                if b_dt.date() != bar_date and b_dt.date() != current_date:
                    break
                if b_dt.hour >= 19 or b_dt.hour < 3:
                    asian_bars.append(candles[j])
            if asian_bars:
                ah = max(float(b[2]) for b in asian_bars)
                al = min(float(b[3]) for b in asian_bars)
                engine.initialize_session(ah, al)

        if dt.hour == 12 and dt.minute == 0:
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
                tb_dt = datetime.fromtimestamp(tb[0]/1000, tz=timezone.utc)
                if direction == TradeDirection.LONG:
                    if tb[3] <= sl_px: pnl_pips = (sl_px - entry_px)/engine.pip_size; exit_type = "SL"; break
                    if tb[2] >= tp_px: pnl_pips = (tp_px - entry_px)/engine.pip_size; exit_type = "TP"; break
                else:
                    if tb[2] >= sl_px: pnl_pips = (entry_px - sl_px)/engine.pip_size; exit_type = "SL"; break
                    if tb[3] <= tp_px: pnl_pips = (entry_px - tp_px)/engine.pip_size; exit_type = "TP"; break

            if pnl_pips is None:
                lc = float(candles[-1][4])
                pnl_pips = ((lc - entry_px) if direction == TradeDirection.LONG else (entry_px - lc))/engine.pip_size

            trades.append({"pnl_pips": pnl_pips, "exit": exit_type})

    total = len(trades)
    if total == 0:
        return {"trades": 0, "wr": 0, "pf": 0, "tr_per_day": 0, "pnl": 0, "max_dd": 0}

    wins = sum(1 for t in trades if t["pnl_pips"] > 0)
    losses = total - wins
    wr = wins / total * 100.0
    pnl = sum(t["pnl_pips"] for t in trades)
    gp = sum(t["pnl_pips"] for t in trades if t["pnl_pips"] > 0)
    gl = abs(sum(t["pnl_pips"] for t in trades if t["pnl_pips"] < 0))
    pf = gp / gl if gl > 0 else float("inf")

    cumulative = peak = max_dd = 0.0
    for t in trades:
        cumulative += t["pnl_pips"]
        if cumulative > peak: peak = cumulative
        dd = peak - cumulative
        if dd > max_dd: max_dd = dd

    days = (datetime.fromtimestamp(candles[-1][0]/1000, tz=timezone.utc) -
            datetime.fromtimestamp(candles[0][0]/1000, tz=timezone.utc)).days
    tr_per_day = total / days if days > 0 else 0

    return {
        "trades": total, "wr": round(wr, 1), "pf": round(pf, 2),
        "tr_per_day": round(tr_per_day, 2), "pnl": round(pnl, 1),
        "max_dd": round(max_dd, 1), "wins": wins, "losses": losses,
    }


def main():
    # Fetch data once
    candles = fetch_binance_5m(1460)
    if not candles:
        print("No data!")
        return

    print(f"\nData: {len(candles)} candles, "
          f"{datetime.fromtimestamp(candles[0][0]/1000, tz=timezone.utc).strftime('%Y-%m-%d')} -> "
          f"{datetime.fromtimestamp(candles[-1][0]/1000, tz=timezone.utc).strftime('%Y-%m-%d')}")

    # Sweep trigger values
    triggers = [50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200,
                210, 220, 230, 240, 250, 260, 270, 280, 290, 300, 320, 340, 360, 380, 400,
                450, 500, 550, 600, 700, 800]

    results = []
    print(f"\nSweeping {len(triggers)} trigger values...")
    print("-" * 80)

    for trigger in triggers:
        stats = run_backtest(candles, trigger)
        stats["trigger"] = trigger
        results.append(stats)
        print(f"  trigger={trigger:>4d}: trades={stats['trades']:>5d}  wr={stats['wr']:>5.1f}%  "
              f"pf={stats['pf']:>5.1f}  tr/day={stats['tr_per_day']:>4.1f}  "
              f"pnl={stats['pnl']:>10.1f}  max_dd={stats['max_dd']:>8.1f}")

    # Find best configs
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    # Best WR with >= 2 tr/day
    high_freq = [r for r in results if r["tr_per_day"] >= 2.0]
    if high_freq:
        best_wr = max(high_freq, key=lambda x: x["wr"])
        print(f"\nBest WR with >= 2 tr/day: trigger={best_wr['trigger']}, "
              f"wr={best_wr['wr']}%, tr/day={best_wr['tr_per_day']}, "
              f"trades={best_wr['trades']}, pf={best_wr['pf']}")

    # Best WR with >= 3 tr/day
    med_freq = [r for r in results if r["tr_per_day"] >= 3.0]
    if med_freq:
        best_wr3 = max(med_freq, key=lambda x: x["wr"])
        print(f"Best WR with >= 3 tr/day: trigger={best_wr3['trigger']}, "
              f"wr={best_wr3['wr']}%, tr/day={best_wr3['tr_per_day']}, "
              f"trades={best_wr3['trades']}, pf={best_wr3['pf']}")

    # Best PF with >= 2 tr/day
    if high_freq:
        best_pf = max(high_freq, key=lambda x: x["pf"])
        print(f"Best PF with >= 2 tr/day:  trigger={best_pf['trigger']}, "
              f"pf={best_pf['pf']}, wr={best_pf['wr']}%, tr/day={best_pf['tr_per_day']}")

    # Best overall (highest pnl with >= 2 tr/day)
    if high_freq:
        best_pnl = max(high_freq, key=lambda x: x["pnl"])
        print(f"Best PnL with >= 2 tr/day: trigger={best_pnl['trigger']}, "
              f"pnl={best_pnl['pnl']}, wr={best_pnl['wr']}%, tr/day={best_pnl['tr_per_day']}")

    # Print table
    print("\n" + "-" * 80)
    print(f"{'Trigger':>8} {'Trades':>8} {'WR%':>8} {'PF':>8} {'Tr/Day':>8} {'PnL':>12} {'MaxDD':>10}")
    print("-" * 80)
    for r in results:
        print(f"{r['trigger']:>8d} {r['trades']:>8d} {r['wr']:>7.1f}% {r['pf']:>7.1f} "
              f"{r['tr_per_day']:>7.1f} {r['pnl']:>10.1f} {r['max_dd']:>9.1f}")

    # Save results
    report_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\hyperliquid_full")
    report_dir.mkdir(parents=True, exist_ok=True)
    with open(report_dir / "btc_trigger_sweep.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {report_dir / 'btc_trigger_sweep.json'}")


if __name__ == "__main__":
    main()
