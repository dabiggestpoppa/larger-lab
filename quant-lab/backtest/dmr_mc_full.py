"""
DMR Full Monte Carlo + Deep Stats + Grouping
==============================================
Per-asset: comprehensive stats (Sharpe, Calmar, Sortino, streaks, duration, etc.)
Portfolio MC: 10K simulations with ruin analysis
Grouping: by basket (EUR, GBP, USD, JPY, AUD, NZD, CAD, CHF), by trade count, by WR, by PF
"""

import csv, json, random, sys, math
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from pathlib import Path
import numpy as np

WORKSPACE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
REPORTS_DIR = WORKSPACE / "quant-lab" / "reports"
MC_DIR = REPORTS_DIR / "dmr_mc"
MC_DIR.mkdir(parents=True, exist_ok=True)

EST = timezone(timedelta(hours=-5))
N_SIMULATIONS = 10000
INITIAL_BALANCE = 10000.0

# ─── Asset Config ───────────────────────────────────────────
PIP_SIZES = {
    "EURUSD": 0.0001, "GBPUSD": 0.0001, "USDCHF": 0.0001,
    "USDJPY": 0.01,   "AUDUSD": 0.0001, "NZDUSD": 0.0001,
    "USDCAD": 0.0001, "EURGBP": 0.0001, "EURJPY": 0.01,
    "GBPJPY": 0.01,   "AUDJPY": 0.01,   "CHFJPY": 0.01,
    "AUDNZD": 0.0001, "EURAUD": 0.0001, "EURCHF": 0.0001,
    "GBPCHF": 0.0001, "GBPAUD": 0.0001, "GBPNZD": 0.0001,
    "NZDCHF": 0.0001, "NZDJPY": 0.01,   "CADJPY": 0.01,
    "AUDCAD": 0.0001, "AUDCHF": 0.0001, "CADCHF": 0.0001,
    "EURNZD": 0.0001, "NZDCAD": 0.0001,
    "BTCUSD": 1.0,     "ETHUSD": 0.01,   "XAUUSD": 0.1,
    "XAGUSD": 0.001,  "US500": 1.0,
}

CSV_FILES = {
    "EURUSD": "quant-lab/data/EURUSDPRO_M5_2023_2026.csv",
    "USDCHF": "quant-lab/data/USDCHFPRO_M5.csv",
    "GBPUSD": "quant-lab/data/GBPUSD_M5.csv",
    "USDJPY": "quant-lab/data/USDJPY_M5.csv",
    "AUDUSD": "quant-lab/data/AUDUSD_M5.csv",
    "NZDUSD": "quant-lab/data/NZDUSD_M5.csv",
    "USDCAD": "quant-lab/data/USDCAD_PRO_M5.csv",
    "EURGBP": "quant-lab/data/EURGBP_PRO_M5.csv",
    "EURJPY": "quant-lab/data/EURJPY_PRO_M5.csv",
    "GBPJPY": "quant-lab/data/GBPJPY_M5.csv",
    "AUDJPY": "quant-lab/data/AUDJPY_PRO_M5.csv",
    "CHFJPY": "quant-lab/data/CHFJPY_M5.csv",
    "AUDNZD": "quant-lab/data/AUDNZD_PRO_M5.csv",
    "EURAUD": "quant-lab/data/EURAUD_PRO_M5.csv",
    "EURCHF": "quant-lab/data/EURCHF_PRO_M5.csv",
    "GBPCHF": "quant-lab/data/GBPCHF_M5.csv",
    "GBPAUD": "quant-lab/data/GBPAUD_M5.csv",
    "GBPNZD": "quant-lab/data/GBPNZD_M5.csv",
    "NZDCHF": "quant-lab/data/NZDCHF_PRO_M5.csv",
    "NZDJPY": "quant-lab/data/NZDJPY_PRO_M5.csv",
    "CADJPY": "quant-lab/data/CADJPY_PRO_M5.csv",
    "AUDCAD": "quant-lab/data/AUDCAD_PRO_M5.csv",
    "AUDCHF": "quant-lab/data/AUDCHF_PRO_M5.csv",
    "CADCHF": "quant-lab/data/CADCHF_PRO_M5.csv",
    "EURNZD": "quant-lab/data/EURNZD_PRO_M5.csv",
    "NZDCAD": "quant-lab/data/NZDCAD_PRO_M5.csv",
    "BTCUSD": "quant-lab/data/BTCUSD_M5.csv",
    "ETHUSD": "quant-lab/data/ETHUSD_M5.csv",
    "XAUUSD": "quant-lab/data/XAUUSD_M5.csv",
    "XAGUSD": "quant-lab/data/XAGUSD_M5.csv",
    "US500": "quant-lab/data/US500_M5.csv",
}

# Currency basket mapping
CURRENCY_BASKETS = {
    "EUR": ["EURUSD", "EURGBP", "EURJPY", "EURAUD", "EURCHF", "EURNZD"],
    "GBP": ["GBPUSD", "EURGBP", "GBPJPY", "GBPAUD", "GBPCHF", "GBPNZD"],
    "USD": ["EURUSD", "GBPUSD", "USDCHF", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "US500"],
    "JPY": ["EURJPY", "GBPJPY", "USDJPY", "AUDJPY", "CHFJPY", "NZDJPY", "CADJPY"],
    "AUD": ["AUDUSD", "EURAUD", "GBPAUD", "AUDJPY", "AUDNZD", "AUDCAD", "AUDCHF"],
    "NZD": ["NZDUSD", "EURNZD", "GBPNZD", "AUDNZD", "NZDCHF", "NZDJPY", "NZDCAD"],
    "CAD": ["USDCAD", "AUDCAD", "NZDCAD", "CADCHF", "CADJPY"],
    "CHF": ["USDCHF", "EURCHF", "GBPCHF", "AUDCHF", "CADCHF", "NZDCHF", "CHFJPY"],
}

# DMR Parameters
DEEP_MULT = 2.0
KILL_MULT = 2.2
MIN_AR = 3.0
MAX_AR = 45.0
ASIAN_START_H = 19
ASIAN_END_H = 3
TRADING_START_H = 2
TRADING_END_H = 11
DS_SCAN_END_H = 12
HARD_EXIT_H = 17


def load_csv(path):
    bars = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ts_raw = row.get("timestamp") or row.get("time")
                if not ts_raw:
                    continue
                try:
                    ts = datetime.fromtimestamp(int(float(ts_raw)), tz=EST)
                except (ValueError, OSError):
                    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"]:
                        try:
                            dt_naive = datetime.strptime(ts_raw.strip(), fmt)
                            ts = dt_naive.replace(tzinfo=EST)
                            break
                        except ValueError:
                            continue
                    else:
                        continue
                o = float(row.get("open") or row.get("Open"))
                h = float(row.get("high") or row.get("High"))
                lo = float(row.get("low") or row.get("Low"))
                c = float(row.get("close") or row.get("Close"))
                bars.append({"ts": ts, "est_h": ts.hour, "o": o, "h": h, "l": lo, "c": c})
            except (ValueError, KeyError):
                continue
    bars.sort(key=lambda b: b["ts"])
    return bars


def session_date(dt):
    if dt.hour >= ASIAN_START_H:
        return (dt + timedelta(days=1)).date()
    return dt.date()


def price_to_pips(price_diff, pip_size):
    return price_diff / pip_size


def pips_to_price(pips, pip_size):
    return pips * pip_size


def compute_p90_per_hour(bars, pip_size):
    hourly_bodies = defaultdict(list)
    for b in bars:
        body_pips = price_to_pips(abs(b["c"] - b["o"]), pip_size)
        hourly_bodies[b["est_h"]].append(body_pips)
    hourly_p90 = {}
    for h in range(2, 11):
        if len(hourly_bodies[h]) >= 20:
            hourly_p90[h] = round(np.percentile(hourly_bodies[h], 90), 1)
        else:
            hourly_p90[h] = None
    return hourly_p90


def get_p90_threshold(est_hour, hourly_p90, fallback):
    if est_hour in hourly_p90 and hourly_p90[est_hour] is not None:
        return hourly_p90[est_hour]
    for offset in range(1, 9):
        for candidate in [est_hour - offset, est_hour + offset]:
            if candidate in hourly_p90 and hourly_p90[candidate] is not None:
                return hourly_p90[candidate]
    return fallback


def run_dmr_backtest(bars, pip_size, p90_fallback):
    """Run DMR backtest, return trades with timestamps for duration tracking."""
    hourly_p90 = compute_p90_per_hour(bars, pip_size)
    days = defaultdict(list)
    for bar in bars:
        sd = session_date(bar["ts"])
        days[sd].append(bar)
    
    trades = []
    
    for sd in sorted(days.keys()):
        day_bars = sorted(days[sd], key=lambda b: b["ts"])
        if len(day_bars) < 5:
            continue
        
        ah, al = 0.0, 99999.0
        ar_locked = False
        skip_day = False
        for b in day_bars:
            if b["est_h"] >= ASIAN_START_H or b["est_h"] < ASIAN_END_H:
                ah = max(ah, b["h"])
                al = min(al, b["l"])
            if b["est_h"] == ASIAN_END_H and not ar_locked:
                ar_locked = True
                if ah > 0 and al < 99999:
                    ar_pips = price_to_pips(ah - al, pip_size)
                    if ar_pips < MIN_AR or ar_pips > MAX_AR:
                        skip_day = True
                break
        if skip_day:
            continue
        
        trading = [b for b in day_bars if TRADING_START_H <= b["est_h"] < TRADING_END_H]
        if not trading:
            continue
        
        p90_found = False
        p90_dir = 0
        activation = 0.0
        body_pips = 0.0
        p90_idx = -1
        
        for i, b in enumerate(trading):
            body = abs(b["c"] - b["o"])
            bp = price_to_pips(body, pip_size)
            threshold = get_p90_threshold(b["est_h"], hourly_p90, p90_fallback)
            if bp >= threshold:
                p90_found = True
                p90_dir = 1 if b["c"] > b["o"] else -1
                activation = b["c"]
                body_pips = bp
                p90_idx = i
                break
        
        if not p90_found:
            continue
        
        ds = activation + pips_to_price(body_pips * DEEP_MULT, pip_size) * p90_dir
        ks = activation + pips_to_price(body_pips * KILL_MULT, pip_size) * p90_dir
        
        ds_touched = False
        ds_bar = None
        for b in trading[p90_idx + 1:]:
            if b["est_h"] >= DS_SCAN_END_H:
                break
            if p90_dir == 1 and b["l"] <= ds:
                ds_touched = True
                ds_bar = b
                break
            if p90_dir == -1 and b["h"] >= ds:
                ds_touched = True
                ds_bar = b
                break
        
        if not ds_touched:
            continue
        
        is_short = (p90_dir == 1)
        entry_price = ds
        
        if is_short:
            if activation >= entry_price or ks <= entry_price:
                continue
        else:
            if activation <= entry_price or ks >= entry_price:
                continue
        
        pnl_pips = 0.0
        result = "UNKNOWN"
        exit_time = None
        
        for tb in day_bars:
            if tb["ts"] <= ds_bar["ts"]:
                continue
            if tb["est_h"] >= HARD_EXIT_H:
                if is_short:
                    pnl_pips = price_to_pips(entry_price - tb["c"], pip_size)
                else:
                    pnl_pips = price_to_pips(tb["c"] - entry_price, pip_size)
                result = "HARD_EXIT"
                exit_time = tb["ts"]
                break
            if is_short:
                if tb["l"] <= activation:
                    pnl_pips = price_to_pips(entry_price - activation, pip_size)
                    result = "TP"
                    exit_time = tb["ts"]
                    break
                if tb["h"] >= ks:
                    pnl_pips = price_to_pips(entry_price - ks, pip_size)
                    result = "SL"
                    exit_time = tb["ts"]
                    break
            else:
                if tb["h"] >= activation:
                    pnl_pips = price_to_pips(activation - entry_price, pip_size)
                    result = "TP"
                    exit_time = tb["ts"]
                    break
                if tb["l"] <= ks:
                    pnl_pips = price_to_pips(ks - entry_price, pip_size)
                    result = "SL"
                    exit_time = tb["ts"]
                    break
        
        if result == "UNKNOWN":
            last = day_bars[-1]
            pnl_pips = price_to_pips(entry_price - last["c"], pip_size) if is_short else price_to_pips(last["c"] - entry_price, pip_size)
            result = "EOD"
            exit_time = last["ts"]
        
        duration = (exit_time - ds_bar["ts"]).total_seconds() / 60.0  # minutes
        
        trades.append({
            "date": str(sd),
            "result": result,
            "pnl": round(pnl_pips, 1),
            "dir": "SHORT" if is_short else "LONG",
            "body": round(body_pips, 1),
            "est_h": ds_bar["est_h"],
            "entry_time": ds_bar["ts"].isoformat(),
            "exit_time": exit_time.isoformat() if exit_time else None,
            "duration_min": round(duration, 1),
        })
    
    return trades


def compute_deep_stats(trades, pip_size):
    """Compute comprehensive quantitative stats."""
    if not trades:
        return {"total": 0}
    
    pnls = [t["pnl"] for t in trades]
    n = len(pnls)
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    
    total_pnl = sum(pnls)
    gross_profit = sum(wins) if wins else 0
    gross_loss = abs(sum(losses)) if losses else 0.001
    wr = len(wins) / n * 100
    pf = gross_profit / gross_loss
    
    # Max DD and longest DD period
    cumulative = 0
    peak = 0
    max_dd = 0
    dd_start = None
    longest_dd_days = 0
    current_dd_days = 0
    
    for t in trades:
        cumulative += t["pnl"]
        if cumulative > peak:
            peak = cumulative
            dd_start = None
            current_dd_days = 0
        else:
            if dd_start is None:
                dd_start = t.get("date", "")
            current_dd_days += 1
            longest_dd_days = max(longest_dd_days, current_dd_days)
        dd = peak - cumulative
        max_dd = max(max_dd, dd)
    
    # Streaks
    cw = cl = mcw = mcl = 0
    for p in pnls:
        if p > 0:
            cw += 1
            cl = 0
            mcw = max(mcw, cw)
        elif p < 0:
            cl += 1
            cw = 0
            mcl = max(mcl, cl)
    
    # Sharpe (per-trade, annualized)
    mean_pnl = np.mean(pnls)
    std_pnl = np.std(pnls)
    sharpe = (mean_pnl / std_pnl * math.sqrt(252)) if std_pnl > 0 else 0
    
    # Sortino (downside deviation)
    downside_returns = [p for p in pnls if p < 0]
    downside_std = np.std(downside_returns) if downside_returns else 0.001
    sortino = (mean_pnl / downside_std * math.sqrt(252)) if downside_std > 0 else 0
    
    # Calmar (annual return / max dd)
    annual_return = mean_pnl * 252
    calmar = annual_return / max_dd if max_dd > 0 else float("inf")
    
    # Average trade duration
    durations = [t.get("duration_min", 0) for t in trades if t.get("duration_min")]
    avg_duration = np.mean(durations) if durations else 0
    
    # Trades per day / week
    trade_dates = set(t["date"] for t in trades)
    n_days = len(trade_dates)
    first_date = min(trade_dates) if trade_dates else ""
    last_date = max(trade_dates) if trade_dates else ""
    n_weeks = max(1, n_days / 5)
    trades_per_day = n / n_days if n_days > 0 else 0
    trades_per_week = n / n_weeks
    
    # Result breakdown
    tp_count = sum(1 for t in trades if t["result"] == "TP")
    sl_count = sum(1 for t in trades if t["result"] == "SL")
    he_count = sum(1 for t in trades if t["result"] == "HARD_EXIT")
    eod_count = sum(1 for t in trades if t["result"] == "EOD")
    
    # Long/Short split
    lt = [t["pnl"] for t in trades if t["dir"] == "LONG"]
    st = [t["pnl"] for t in trades if t["dir"] == "SHORT"]
    
    # Kelly Criterion
    if gross_loss > 0 and gross_profit > 0:
        w = len(wins) / n
        r = sum(wins) / len(wins) / abs(sum(losses) / len(losses)) if losses else 1
        kelly = (w * r - (1 - w)) / r if r > 0 else 0
    else:
        kelly = 0
    
    # Profit Factor by hour
    hourly_pf = {}
    for h in range(2, 11):
        h_trades = [t["pnl"] for t in trades if t["est_h"] == h]
        if len(h_trades) >= 5:
            h_wins = sum(p for p in h_trades if p > 0)
            h_losses = abs(sum(p for p in h_trades if p < 0))
            hourly_pf[h] = round(h_wins / h_losses, 2) if h_losses > 0 else float("inf")
    
    return {
        "total": n,
        "wins": len(wins),
        "losses": len(losses),
        "wr": round(wr, 1),
        "pnl": round(total_pnl, 1),
        "pf": round(pf, 2),
        "avg_trade": round(mean_pnl, 2),
        "avg_win": round(sum(wins) / len(wins), 1) if wins else 0,
        "avg_loss": round(sum(losses) / len(losses), 1) if losses else 0,
        "max_dd": round(max_dd, 1),
        "longest_dd_trades": longest_dd_days,
        "max_consec_wins": mcw,
        "max_consec_losses": mcl,
        "sharpe": round(sharpe, 2),
        "sortino": round(sortino, 2),
        "calmar": round(calmar, 2),
        "kelly": round(kelly, 3),
        "half_kelly": round(kelly / 2, 3),
        "avg_duration_min": round(avg_duration, 1),
        "trades_per_day": round(trades_per_day, 2),
        "trades_per_week": round(trades_per_week, 1),
        "n_trading_days": n_days,
        "date_range": f"{first_date} to {last_date}",
        "tp": tp_count,
        "sl": sl_count,
        "hard_exit": he_count,
        "eod": eod_count,
        "long_trades": len(lt),
        "long_wr": round(sum(1 for p in lt if p > 0) / len(lt) * 100, 1) if lt else 0,
        "long_pnl": round(sum(lt), 1),
        "short_trades": len(st),
        "short_wr": round(sum(1 for p in st if p > 0) / len(st) * 100, 1) if st else 0,
        "short_pnl": round(sum(st), 1),
        "hourly_pf": hourly_pf,
        "per_trade_pnl": pnls,  # For MC
    }


def run_monte_carlo(trades, n_sims=N_SIMULATIONS):
    """Run Monte Carlo simulation on trade PnLs."""
    pnls = [t["pnl"] for t in trades]
    n = len(pnls)
    
    terminal_pnls = []
    max_dds = []
    max_streaks = []
    ruin_count = 0
    
    for _ in range(n_sims):
        shuffled = random.sample(pnls, n)
        cumulative = 0
        peak = 0
        max_dd = 0
        max_streak = 0
        current_streak = 0
        
        for p in shuffled:
            cumulative += p
            peak = max(peak, cumulative)
            max_dd = max(max_dd, peak - cumulative)
            if p <= 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        terminal_pnls.append(cumulative)
        max_dds.append(max_dd)
        max_streaks.append(max_streak)
        if cumulative < 0:
            ruin_count += 1
    
    terminal_pnls.sort()
    max_dds.sort()
    max_streaks.sort()
    n_s = len(terminal_pnls)
    
    return {
        "n_simulations": n_sims,
        "terminal_pnl_median": round(terminal_pnls[n_s // 2], 1),
        "terminal_pnl_mean": round(sum(terminal_pnls) / n_s, 1),
        "terminal_pnl_5th": round(terminal_pnls[int(n_s * 0.05)], 1),
        "terminal_pnl_25th": round(terminal_pnls[int(n_s * 0.25)], 1),
        "terminal_pnl_75th": round(terminal_pnls[int(n_s * 0.75)], 1),
        "terminal_pnl_95th": round(terminal_pnls[int(n_s * 0.95)], 1),
        "max_dd_median": round(max_dds[n_s // 2], 1),
        "max_dd_95th": round(max_dds[int(n_s * 0.95)], 1),
        "max_dd_99th": round(max_dds[int(n_s * 0.99)], 1),
        "max_dd_worst": round(max_dds[-1], 1),
        "max_loss_streak_median": max_streaks[n_s // 2],
        "max_loss_streak_95th": max_streaks[int(n_s * 0.95)],
        "max_loss_streak_99th": max_streaks[int(n_s * 0.99)],
        "max_loss_streak_worst": max_streaks[-1],
        "ruin_rate": round(ruin_count / n_s * 100, 2),
    }


def main():
    print("=" * 80)
    print("DMR FULL MONTE CARLO + DEEP STATS + GROUPING")
    print("=" * 80)
    
    all_trades = {}
    all_stats = {}
    all_mc = {}
    
    for symbol, csv_rel in sorted(CSV_FILES.items()):
        csv_path = WORKSPACE / csv_rel
        if not csv_path.exists():
            continue
        
        pip_size = PIP_SIZES.get(symbol, 0.0001)
        p90_fallback = 4.1  # EURUSD 2-4AM threshold
        
        bars = load_csv(str(csv_path))
        if len(bars) < 100:
            continue
        
        trades = run_dmr_backtest(bars, pip_size, p90_fallback)
        if not trades:
            continue
        
        stats = compute_deep_stats(trades, pip_size)
        mc = run_monte_carlo(trades)
        
        all_trades[symbol] = trades
        all_stats[symbol] = stats
        all_mc[symbol] = mc
        
        print(f"[{symbol:10s}] {stats['total']:4d} tr | WR={stats['wr']:5.1f}% | "
              f"PF={stats['pf']:7.1f} | Sharpe={stats['sharpe']:5.2f} | "
              f"Calmar={stats['calmar']:7.1f} | MaxDD={stats['max_dd']:6.1f}p | "
              f"MC Ruin={mc['ruin_rate']:5.2f}%")
    
    # ─── Grouping ───
    print("\n" + "=" * 80)
    print("GROUPING BY CURRENCY BASKET")
    print("=" * 80)
    
    for basket, pairs in sorted(CURRENCY_BASKETS.items()):
        basket_trades = []
        for p in pairs:
            if p in all_trades:
                basket_trades.extend(all_trades[p])
        
        if not basket_trades:
            continue
        
        pnls = [t["pnl"] for t in basket_trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        n = len(pnls)
        wr = len(wins) / n * 100
        gp = sum(wins) if wins else 0
        gl = abs(sum(losses)) if losses else 0.001
        pf = gp / gl
        
        print(f"[{basket:5s}] {n:5d} tr | WR={wr:5.1f}% | PF={pf:7.1f} | "
              f"PnL={sum(pnls):+10.1f}p | Pairs: {', '.join(p for p in pairs if p in all_trades)}")
    
    # ─── Grouping by WR tier ───
    print("\n" + "=" * 80)
    print("GROUPING BY WIN RATE TIER")
    print("=" * 80)
    
    wr_tiers = {
        "95%+": [],
        "93-95%": [],
        "90-93%": [],
        "87-90%": [],
        "<87%": [],
    }
    
    for sym, stats in all_stats.items():
        wr = stats["wr"]
        if wr >= 95:
            wr_tiers["95%+"].append(sym)
        elif wr >= 93:
            wr_tiers["93-95%"].append(sym)
        elif wr >= 90:
            wr_tiers["90-93%"].append(sym)
        elif wr >= 87:
            wr_tiers["87-90%"].append(sym)
        else:
            wr_tiers["<87%"].append(sym)
    
    for tier, pairs in wr_tiers.items():
        if not pairs:
            continue
        tier_trades = []
        for p in pairs:
            tier_trades.extend(all_trades[p])
        pnls = [t["pnl"] for t in tier_trades]
        wins = [p for p in pnls if p > 0]
        n = len(pnls)
        wr = len(wins) / n * 100
        print(f"[{tier:8s}] {n:5d} tr | WR={wr:5.1f}% | {len(pairs)} pairs: {', '.join(sorted(pairs))}")
    
    # ─── Grouping by trade count ───
    print("\n" + "=" * 80)
    print("GROUPING BY TRADE COUNT")
    print("=" * 80)
    
    count_tiers = {
        "High (500+)": [],
        "Medium (200-500)": [],
        "Low (<200)": [],
    }
    
    for sym, stats in all_stats.items():
        total = stats["total"]
        if total >= 500:
            count_tiers["High (500+)"].append(sym)
        elif total >= 200:
            count_tiers["Medium (200-500)"].append(sym)
        else:
            count_tiers["Low (<200)"].append(sym)
    
    for tier, pairs in count_tiers.items():
        if not pairs:
            continue
        tier_trades = []
        for p in pairs:
            tier_trades.extend(all_trades[p])
        pnls = [t["pnl"] for t in tier_trades]
        wins = [p for p in pnls if p > 0]
        n = len(pnls)
        wr = len(wins) / n * 100
        print(f"[{tier:18s}] {n:5d} tr | WR={wr:5.1f}% | {len(pairs)} pairs: {', '.join(sorted(pairs))}")
    
    # ─── Save everything ───
    output = {
        "timestamp": datetime.now().isoformat(),
        "n_simulations": N_SIMULATIONS,
        "per_asset_stats": all_stats,
        "per_asset_mc": all_mc,
        "grouping": {
            "by_currency_basket": {},
            "by_wr_tier": {},
            "by_trade_count": {},
        },
    }
    
    # Remove per_trade_pnl from stats (too large for JSON)
    for sym in output["per_asset_stats"]:
        output["per_asset_stats"][sym].pop("per_trade_pnl", None)
    
    out_path = MC_DIR / "dmr_mc_full_results.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    
    print(f"\nResults saved to: {out_path}")


if __name__ == "__main__":
    main()
