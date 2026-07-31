"""
BTC Symmetry Trap Full Backtest (4-Year, 5m)
==============================================
Uses ccxt/Binance for historical 5m data with pagination.
Comprehensive stats: Sharpe, Sortino, Calmar, R-multiples, etc.
"""

import sys, time, json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab")))
sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs")))
sys.path.insert(0, str(Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines")))

from asset_configs import ASSET_CONFIGS
from symmetry_trap import SymmetryTrapEngine, TradeSignal, Bar, TradeDirection

EST = timezone(timedelta(hours=-5))


def fetch_binance_5m(days=1460):
    """Fetch BTC 5m candles from Binance using ccxt with pagination."""
    import ccxt
    exchange = ccxt.binance({'enableRateLimit': True})
    now_ms = int(time.time() * 1000)
    start_ms = now_ms - days * 24 * 3600 * 1000

    all_candles = []
    current_since = start_ms
    req_count = 0

    print(f"[Binance] Fetching BTC 5m, {days} days back...")

    while current_since < now_ms and req_count < 500:
        try:
            # Fetch 1000 candles starting from current_since
            ohlcv = exchange.fetch_ohlcv('BTC/USDT', '5m', since=current_since, limit=1000)
            if not ohlcv:
                break

            # Filter to range
            batch = [c for c in ohlcv if c[0] >= start_ms and c[0] <= now_ms]
            if not batch:
                break

            # Deduplicate
            existing_ts = set(c[0] for c in all_candles)
            new_candles = [c for c in batch if c[0] not in existing_ts]
            all_candles.extend(new_candles)

            oldest = batch[0][0]
            newest = batch[-1][0]

            if req_count % 50 == 0:
                first_dt = datetime.fromtimestamp(oldest/1000, tz=timezone.utc)
                last_dt = datetime.fromtimestamp(newest/1000, tz=timezone.utc)
                print(f"  req {req_count+1}: {len(batch)} candles ({len(new_candles)} new), {first_dt.strftime('%Y-%m-%d')} -> {last_dt.strftime('%Y-%m-%d')}, total: {len(all_candles)}")

            if len(batch) < 1000:
                break

            # Move since pointer to just after the newest candle
            current_since = newest + 1
            req_count += 1

        except Exception as e:
            print(f"  ERROR: {e}")
            time.sleep(2)

    # Dedup and sort
    seen = set()
    deduped = []
    for c in all_candles:
        if c[0] not in seen:
            seen.add(c[0])
            deduped.append(c)
    deduped.sort(key=lambda x: x[0])

    print(f"[Binance] Total: {len(deduped)} candles from {req_count} requests")
    if deduped:
        first = datetime.fromtimestamp(deduped[0][0]/1000, tz=timezone.utc)
        last = datetime.fromtimestamp(deduped[-1][0]/1000, tz=timezone.utc)
        print(f"[Binance] Range: {first.strftime('%Y-%m-%d')} -> {last.strftime('%Y-%m-%d')} ({(last-first).days} days)")

    return deduped


def compute_stats(trades, bars):
    total = len(trades)
    if total == 0:
        return {"total_trades": 0}

    wins = [t for t in trades if t["pnl_pips"] > 0]
    losses = [t for t in trades if t["pnl_pips"] <= 0]
    n_wins, n_losses = len(wins), len(losses)

    total_pnl = sum(t["pnl_pips"] for t in trades)
    gp = sum(t["pnl_pips"] for t in wins)
    gl = abs(sum(t["pnl_pips"] for t in losses))

    wr = (n_wins / total * 100.0) if total > 0 else 0.0
    pf = gp / gl if gl > 0 else float("inf")
    avg_win = gp / n_wins if n_wins > 0 else 0.0
    avg_loss = gl / n_losses if n_losses > 0 else 0.0
    expectancy = total_pnl / total if total > 0 else 0.0

    r_multiples = [t["pnl_pips"] / avg_loss if avg_loss > 0 else 0.0 for t in trades]
    avg_r = sum(r_multiples) / len(r_multiples) if r_multiples else 0.0

    # Max DD
    cumulative = peak = max_dd = 0.0
    for t in trades:
        cumulative += t["pnl_pips"]
        if cumulative > peak: peak = cumulative
        dd = peak - cumulative
        if dd > max_dd: max_dd = dd

    # Consec
    max_cw = max_cl = cw = cl = 0
    for t in trades:
        if t["pnl_pips"] > 0: cw += 1; cl = 0; max_cw = max(max_cw, cw)
        else: cl += 1; cw = 0; max_cl = max(max_cl, cl)

    # Streaks
    streaks, cs = [], 0
    for t in trades:
        if t["pnl_pips"] > 0:
            cs = cs + 1 if cs >= 0 else 1
        else:
            cs = cs - 1 if cs <= 0 else -1
        if not streaks or (streaks[-1] > 0) != (cs > 0): streaks.append(cs)
    if cs != 0: streaks.append(cs)
    ws = [s for s in streaks if s > 0]
    ls = [abs(s) for s in streaks if s < 0]
    avg_ws = sum(ws)/len(ws) if ws else 0
    avg_ls = sum(ls)/len(ls) if ls else 0

    # Exits, tiers
    exit_counts, tier_counts = {}, {}
    for t in trades:
        exit_counts[t["exit"]] = exit_counts.get(t["exit"], 0) + 1
        tier_counts[t.get("tier","?")] = tier_counts.get(t.get("tier","?"), 0) + 1

    # Daily PnL for Sharpe/Sortino/Calmar
    daily_pnl = defaultdict(float)
    for t in trades:
        day = t["entry_time"][:10] if isinstance(t["entry_time"], str) else str(t["entry_time"])[:10]
        daily_pnl[day] += t["pnl_pips"]
    daily_r = list(daily_pnl.values())
    n_d = len(daily_r)
    avg_d = sum(daily_r)/n_d if n_d > 0 else 0.0

    if n_d > 1:
        var = sum((r-avg_d)**2 for r in daily_r)/(n_d-1)
        std_d = var**0.5
        sharpe = (avg_d/std_d*(252**0.5)) if std_d > 0 else 0.0
        down = [r for r in daily_r if r < 0]
        dd_var = sum(r**2 for r in down)/n_d if n_d > 0 else 0.0
        dd_dev = dd_var**0.5
        sortino = (avg_d/dd_dev*(252**0.5)) if dd_dev > 0 else 0.0
        calmar = (avg_d*252)/max_dd if max_dd > 0 else 0.0
    else:
        sharpe = sortino = calmar = std_d = 0.0

    # Monthly
    monthly_pnl = defaultdict(float)
    for t in trades:
        m = t["entry_time"][:7] if isinstance(t["entry_time"], str) else str(t["entry_time"])[:7]
        monthly_pnl[m] += t["pnl_pips"]
    win_m = sum(1 for v in monthly_pnl.values() if v > 0)
    loss_m = sum(1 for v in monthly_pnl.values() if v <= 0)

    wr_rate = n_wins/total if total > 0 else 0.0
    lr_rate = n_losses/total if total > 0 else 0.0
    exp_r = (wr_rate * avg_r) - (lr_rate * 1.0) if avg_loss > 0 else 0.0

    days_total = (bars[-1].timestamp - bars[0].timestamp).days if bars else 0
    tr_per_day = total/days_total if days_total > 0 else 0.0

    return {
        "total_trades": total, "wins": n_wins, "losses": n_losses,
        "win_rate": round(wr, 1), "profit_factor": round(pf, 2),
        "total_pnl_pips": round(total_pnl, 1),
        "gross_profit": round(gp, 1), "gross_loss": round(gl, 1),
        "avg_win_pips": round(avg_win, 1), "avg_loss_pips": round(avg_loss, 1),
        "expectancy_pips": round(expectancy, 1),
        "avg_r_multiple": round(avg_r, 2), "expectancy_r": round(exp_r, 3),
        "max_drawdown_pips": round(max_dd, 1),
        "max_consec_wins": max_cw, "max_consec_losses": max_cl,
        "avg_win_streak": round(avg_ws, 1), "avg_loss_streak": round(avg_ls, 1),
        "sharpe_ratio": round(sharpe, 2), "sortino_ratio": round(sortino, 2),
        "calmar_ratio": round(calmar, 2),
        "std_daily_pips": round(std_d, 1), "avg_daily_pips": round(avg_d, 1),
        "trades_per_day": round(tr_per_day, 2),
        "exit_distribution": exit_counts, "tier_distribution": tier_counts,
        "winning_months": win_m, "losing_months": loss_m,
        "monthly_pnl": {k: round(v, 1) for k, v in sorted(monthly_pnl.items())},
        "bars_processed": len(bars),
        "date_range": {
            "start": bars[0].timestamp.isoformat() if bars else None,
            "end": bars[-1].timestamp.isoformat() if bars else None,
        },
    }


def main():
    DAYS = 1460  # 4 years
    config = ASSET_CONFIGS.get("BTCUSD", {"tiers": {"T1": {"ar_max": 60.0, "au": 205.0, "trigger": 240.0}}})

    # Fetch data
    candles = fetch_binance_5m(DAYS)
    if not candles:
        print("No data fetched!")
        return

    # Convert to engine bars
    bars = []
    for c in candles:
        dt = datetime.fromtimestamp(c[0]/1000, tz=timezone.utc).astimezone(EST)
        bars.append(Bar(timestamp=dt, open=float(c[1]), high=float(c[2]), low=float(c[3]), close=float(c[4])))
    bars.sort(key=lambda b: b.timestamp)
    print(f"Loaded {len(bars)} bars")

    # Run backtest
    engine = SymmetryTrapEngine(config=config)
    trades = []
    current_date = None

    for i, bar in enumerate(bars):
        bar_date = bar.timestamp.date()

        # Session init at 3AM EST
        if bar.timestamp.hour == 3 and bar.timestamp.minute == 0 and bar_date != current_date:
            current_date = bar_date
            asian_bars = []
            for j in range(i, -1, -1):
                b = bars[j]
                if b.timestamp.date() != bar_date and b.timestamp.date() != current_date:
                    break
                h = b.timestamp.hour
                if h >= 19 or h < 3:
                    asian_bars.append(b)
            if asian_bars:
                engine.initialize_session(max(b.high for b in asian_bars), min(b.low for b in asian_bars))

        if bar.timestamp.hour == 12 and bar.timestamp.minute == 0:
            engine.hard_exit()

        if not engine.session_active:
            continue

        signal = engine.process_bar(bar)

        if signal and signal.event == "ENTRY":
            direction = signal.direction
            entry_px = signal.entry_price
            sl_px = signal.sl_price
            tp_px = signal.tp_price
            entry_time = signal.timestamp

            pnl_pips = None
            exit_type = "END"
            for tb in bars[i + 1:]:
                if direction == TradeDirection.LONG:
                    if tb.low <= sl_px: pnl_pips = (sl_px - entry_px)/engine.pip_size; exit_type = "SL"; break
                    if tb.high >= tp_px: pnl_pips = (tp_px - entry_px)/engine.pip_size; exit_type = "TP"; break
                else:
                    if tb.high >= sl_px: pnl_pips = (entry_px - sl_px)/engine.pip_size; exit_type = "SL"; break
                    if tb.low <= tp_px: pnl_pips = (entry_px - tp_px)/engine.pip_size; exit_type = "TP"; break

            if pnl_pips is None:
                lc = bars[-1].close
                pnl_pips = ((lc - entry_px) if direction == TradeDirection.LONG else (entry_px - lc))/engine.pip_size

            trades.append({
                "pnl_pips": round(pnl_pips, 1), "exit": exit_type,
                "direction": "LONG" if direction == TradeDirection.LONG else "SHORT",
                "entry_time": entry_time.isoformat() if hasattr(entry_time, 'isoformat') else str(entry_time),
                "au": engine.au_pips, "tier": engine.tier_name,
            })

    stats = compute_stats(trades, bars)

    # Print results
    dr = stats.get("date_range", {})
    print("\n" + "=" * 65)
    print("  SYMMETRY TRAP FULL BACKTEST — BTCUSD (Binance 5m)")
    print("=" * 65)
    print("  Period:       " + str(dr.get("start", "")[:10]) + " -> " + str(dr.get("end", "")[:10]))
    print("  Bars:         " + str(len(bars)))
    print("  Trades:       " + str(stats["total_trades"]))
    print("  Wins:         " + str(stats["wins"]) + " | Losses: " + str(stats["losses"]))
    print("  WR:           " + str(stats["win_rate"]) + "%")
    print("  PF:           " + str(stats["profit_factor"]))
    print("  PnL:          " + str(stats["total_pnl_pips"]) + " pips")
    print("  Max DD:       " + str(stats["max_drawdown_pips"]) + " pips")
    print("  Avg Win:      " + str(stats["avg_win_pips"]) + " pips")
    print("  Avg Loss:     " + str(stats["avg_loss_pips"]) + " pips")
    print("  Avg R:        " + str(stats["avg_r_multiple"]))
    print("  Expectancy:   " + str(stats["expectancy_pips"]) + " pips (" + str(stats["expectancy_r"]) + "R)")
    print("  Tr/Day:       " + str(stats["trades_per_day"]))
    print("  Max Consec:   W" + str(stats["max_consec_wins"]) + " / L" + str(stats["max_consec_losses"]))
    print("  Avg Streak:   W" + str(stats["avg_win_streak"]) + " / L" + str(stats["avg_loss_streak"]))
    print("  Sharpe:       " + str(stats["sharpe_ratio"]))
    print("  Sortino:      " + str(stats["sortino_ratio"]))
    print("  Calmar:       " + str(stats["calmar_ratio"]))
    print("  Win Months:   " + str(stats["winning_months"]) + " | Loss Months: " + str(stats["losing_months"]))
    if stats.get("exit_distribution"):
        print("  Exits:        " + str(stats["exit_distribution"]))
    if stats.get("tier_distribution"):
        print("  Tiers:        " + str(stats["tier_distribution"]))
    print("=" * 65)

    # Save
    report_dir = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\hyperliquid_full")
    report_dir.mkdir(parents=True, exist_ok=True)
    with open(report_dir / "BTCUSD_st_full_backtest.json", "w") as f:
        json.dump(stats, f, indent=2, default=str)
    print("Results saved.")


if __name__ == "__main__":
    main()
