"""
DMR USD/CHF Dedicated Backtest Engine
======================================
- Per-hour P90 calibration from CHF's own M5 distribution
- Full statistical suite: Sharpe, Kelly, PF, Max DD, etc.
- Manual k-factor cross-validation (P90 ≈ AU × 0.38-0.52)
- Daily and monthly breakdowns
"""
import sys, json
from datetime import datetime, timedelta
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

import MetaTrader5 as mt5
import numpy as np

SYMBOL = 'USDCHF.PRO'
PIP_MULT = 10000  # CHF: 1 pip = 0.0001

PARAMS = {
    'DeepMult': 2.0,
    'KillMult': 2.2,
    'MinAR': 3,
    'MaxAR': 45,
    'ESTOffset': -5,
    'HardExitHour': 17,
}

def get_est_hour(dt, offset=-5):
    return (dt.hour + offset) % 24

# ── STEP 1: Per-hour P90 Calibration ──
def calibrate_p90(bars):
    """Compute P90 per EST hour from CHF's own M5 data."""
    hourly = defaultdict(list)
    for bar in bars:
        dt = datetime.fromtimestamp(bar['time'])
        est_h = get_est_hour(dt)
        body_pips = abs(bar['close'] - bar['open']) * PIP_MULT
        hourly[est_h].append(body_pips)
    
    hourly_p90 = {}
    print("PER-HOUR P90 CALIBRATION (USD/CHF):")
    print(f"{'Hour':<8} {'Candles':<10} {'P90':<8} {'Mean':<8} {'Median':<8} {'Std':<8}")
    print("-" * 50)
    for h in range(2, 11):
        vals = hourly.get(h, [])
        if len(vals) >= 20:
            p90 = round(np.percentile(vals, 90), 1)
            hourly_p90[h] = p90
            print(f"  {h:02d}:00  {len(vals):<10} {p90:<8.1f} {np.mean(vals):<8.1f} {np.median(vals):<8.1f} {np.std(vals):<8.1f}")
        else:
            hourly_p90[h] = None
            print(f"  {h:02d}:00  {len(vals):<10} {'N/A':<8} (insufficient data)")
    # Overall P90 (2AM-11AM pool)
    all_activation = []
    for h in range(2, 11):
        all_activation.extend(hourly.get(h, []))
    overall_p90 = round(np.percentile(all_activation, 90), 1) if all_activation else 4.2
    print(f"\n  Overall P90 (2AM-11AM): {overall_p90}p")
    print(f"  Manual benchmark: 4.2p")
    if overall_p90 > 0:
        dev = abs(overall_p90 - 4.2) / 4.2 * 100
        status = "OK" if dev < 15 else "CHECK"
        print(f"  Deviation: {dev:.1f}% [{status}]")
    return hourly_p90, overall_p90

# ── STEP 2: DMR Engine ──
def run_dmr(bars, hourly_p90, fallback_p90):
    def pips_to_price(pips):
        return pips / PIP_MULT
    def price_to_pips(price):
        return price * PIP_MULT
    
    def get_p90_for_hour(est_h):
        if est_h in hourly_p90 and hourly_p90[est_h] is not None:
            return hourly_p90[est_h]
        # nearest fallback
        for d in range(1, 9):
            for c in [est_h - d, est_h + d]:
                if c in hourly_p90 and hourly_p90[c] is not None:
                    return hourly_p90[c]
        return fallback_p90
    
    # Group by EST date
    days = {}
    for bar in bars:
        dt = datetime.fromtimestamp(bar['time'])
        est_dt = dt + timedelta(hours=PARAMS['ESTOffset'])
        dk = est_dt.date()
        eh = get_est_hour(dt)
        if dk not in days:
            days[dk] = []
        days[dk].append({
            'time': bar['time'], 'dt': dt, 'est_h': eh,
            'open': bar['open'], 'high': bar['high'],
            'low': bar['low'], 'close': bar['close'],
        })
    
    trades = []
    skip_ar = skip_p90 = skip_ds = 0
    
    for dk in sorted(days.keys()):
        day_bars = sorted(days[dk], key=lambda b: b['time'])
        if len(day_bars) < 5:
            continue
        
        # Asian Range
        ah, al = 0.0, 99999.0
        ar_lock = False
        skip = False
        ar_p = 0.0
        for b in day_bars:
            if b['est_h'] >= 19 or b['est_h'] < 3:
                ah = max(ah, b['high'])
                al = min(al, b['low'])
            if b['est_h'] == 3 and not ar_lock:
                ar_lock = True
                if ah > 0 and al < 99999:
                    ar_p = price_to_pips(ah - al)
                    if ar_p < PARAMS['MinAR'] or ar_p > PARAMS['MaxAR']:
                        skip = True
                        skip_ar += 1
                break
        if skip:
            continue
        
        # Trading window 2AM-11AM
        tb = [b for b in day_bars if 2 <= b['est_h'] < 11]
        if not tb:
            continue
        
        # P90 scan
        found = False
        p90_dir = act = ds = ks = bp = 0.0
        p90_i = -1
        p90_h = -1
        for i, b in enumerate(tb):
            body = abs(b['close'] - b['open'])
            body_p = price_to_pips(body)
            thresh = get_p90_for_hour(b['est_h'])
            if body_p >= thresh:
                found = True
                p90_dir = 1 if b['close'] > b['open'] else -1
                act = b['close']
                bp = body_p
                ds = act + pips_to_price(body_p * PARAMS['DeepMult']) * p90_dir
                ks = act + pips_to_price(body_p * PARAMS['KillMult']) * p90_dir
                p90_i = i
                p90_h = b['est_h']
                break
        if not found:
            skip_p90 += 1
            continue
        
        # DS touch
        touched = False
        dsb = None
        for b in tb[p90_i + 1:]:
            if b['est_h'] >= 12:
                break
            if p90_dir == 1 and b['low'] <= ds:
                touched = True; dsb = b; break
            if p90_dir == -1 and b['high'] >= ds:
                touched = True; dsb = b; break
        if not touched:
            skip_ds += 1
            continue
        
        is_short = (p90_dir == 1)
        # Entry at deep_state (limit order), NOT bar close
        # Gives full DeepMult=2.0 distance to TP, proper R:R
        entry = ds
        
        # Validate
        if is_short:
            if act >= entry or ks <= entry:
                continue
        else:
            if act <= entry or ks >= entry:
                continue
        
        # Simulate
        pnl = 0.0
        result = 'UNKNOWN'
        for tb2 in tb:
            if tb2['time'] <= dsb['time']:
                continue
            if tb2['est_h'] >= PARAMS['HardExitHour']:
                pnl = price_to_pips(entry - tb2['close']) if is_short else price_to_pips(tb2['close'] - entry)
                result = 'HARD_EXIT'
                break
            if is_short:
                if tb2['high'] >= ks:
                    pnl = price_to_pips(entry - ks); result = 'SL'; break
                if tb2['low'] <= act:
                    pnl = price_to_pips(entry - act); result = 'TP'; break
            else:
                if tb2['low'] <= ks:
                    pnl = price_to_pips(ks - entry); result = 'SL'; break
                if tb2['high'] >= act:
                    pnl = price_to_pips(act - entry); result = 'TP'; break
        else:
            last = tb[-1]
            pnl = price_to_pips(entry - last['close']) if is_short else price_to_pips(last['close'] - entry)
            result = 'EOD'
        
        pnl = round(pnl, 1)
        trades.append({
            'date': str(dk), 'result': result, 'pnl': pnl,
            'dir': 'SHORT' if is_short else 'LONG',
            'body': round(bp, 1), 'est_hour': p90_h,
            'entry': round(entry, 5), 'sl': round(ks, 5), 'tp': round(act, 5),
            'ar': round(ar_p, 1),
        })
    
    return trades, skip_ar, skip_p90, skip_ds

# ── STEP 3: Full Stats ──
def compute_stats(trades, initial_balance=289.17):
    if not trades:
        return {'error': 'no trades'}
    pnls = [t['pnl'] for t in trades]
    n = len(pnls)
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    total = sum(pnls)
    
    # Daily PnL for drawdown
    daily = defaultdict(float)
    for t in trades:
        daily[t['date']] += t['pnl']
    daily_dates = sorted(daily.keys())
    daily_pnls = [daily[d] for d in daily_dates]
    
    # Max DD from daily equity
    eq = initial_balance
    peak = eq
    max_dd = 0
    dd_start = dd_end = None
    cum = 0
    for i, p in enumerate(daily_pnls):
        cum += p * 0.01
        eq = initial_balance + cum
        if eq > peak:
            peak = eq
        dd = peak - eq
        if dd > max_dd:
            max_dd = dd
            dd_end = daily_dates[i]
    
    equity_curve = []
    cum = 0
    for p in daily_pnls:
        cum += p * 0.01
        equity_curve.append(initial_balance + cum)
    
    max_dd_pct = max_dd / initial_balance * 100 if initial_balance > 0 else 0
    
    # Sharpe from daily returns
    daily_rets = daily_pnls
    mean_d = np.mean(daily_rets)
    std_d = np.std(daily_rets)
    sharpe = (mean_d / std_d * np.sqrt(252)) if std_d > 0 else 0
    
    # Sortino (downside deviation)
    downside = [r for r in daily_rets if r < 0]
    std_down = np.std(downside) if downside else 0.001
    sortino = (mean_d / std_down * np.sqrt(252)) if std_down > 0 else 0
    
    # Calmar (annual return / max dd)
    annual_return = sum(daily_pnls) * (252 / len(daily_pnls)) * 0.01 if daily_pnls else 0
    calmar = annual_return / max_dd if max_dd > 0 else 0
    
    # Kelly
    w = len(wins) / n
    avg_w = sum(wins) / len(wins) if wins else 0
    avg_l = sum(losses) / len(losses) if losses else -0.001
    r = avg_w / abs(avg_l) if avg_l != 0 else 1
    kelly = (w * r - (1 - w)) / r if r > 0 else 0
    
    # Monthly breakdown
    monthly = defaultdict(list)
    for t in trades:
        mo = t['date'][:7]  # YYYY-MM
        monthly[mo].append(t['pnl'])
    
    monthly_stats = {}
    for mo in sorted(monthly.keys()):
        mp = monthly[mo]
        mw = sum(1 for p in mp if p > 0)
        monthly_stats[mo] = {
            'trades': len(mp), 'pnl': round(sum(mp), 1),
            'wr': round(mw / len(mp) * 100, 1) if mp else 0,
        }
    
    # Hourly breakdown
    hourly = defaultdict(list)
    for t in trades:
        hourly[t['est_hour']].append(t['pnl'])
    
    hourly_stats = {}
    for h in sorted(hourly.keys()):
        hp = hourly[h]
        hw = sum(1 for p in hp if p > 0)
        hourly_stats[str(h)] = {
            'trades': len(hp), 'pnl': round(sum(hp), 1),
            'wr': round(hw / len(hp) * 100, 1) if hp else 0,
        }
    
    # Result type breakdown
    results = defaultdict(lambda: {'count': 0, 'pnl': 0})
    for t in trades:
        results[t['result']]['count'] += 1
        results[t['result']]['pnl'] += t['pnl']
    
    # Consecutive
    max_cw = max_cl = cw = cl = 0
    for p in pnls:
        if p > 0: cw += 1; cl = 0; max_cw = max(max_cw, cw)
        elif p < 0: cl += 1; cw = 0; max_cl = max(max_cl, cl)
        else: cw = cl = 0
    
    # Long/Short
    lt = [t for t in trades if t['dir'] == 'LONG']
    st = [t for t in trades if t['dir'] == 'SHORT']
    lp = sum(t['pnl'] for t in lt)
    sp = sum(t['pnl'] for t in st)
    
    return {
        'total_trades': n, 'wins': len(wins), 'losses': len(losses),
        'win_rate': round(len(wins)/n*100, 1),
        'total_pnl_pips': round(total, 1),
        'gross_profit': round(sum(wins), 1),
        'gross_loss': round(-sum(losses), 1) if losses else 0,
        'profit_factor': round(sum(wins)/abs(sum(losses)), 2) if losses else float('inf'),
        'expectancy_pips': round(total/n, 2),
        'avg_win_pips': round(avg_w, 1),
        'avg_loss_pips': round(avg_l, 1),
        'avg_trade_pips': round(total/n, 2),
        'sharpe_daily': round(sharpe, 2),
        'sortino_daily': round(sortino, 2),
        'calmar_ratio': round(calmar, 2),
        'max_drawdown_$': round(max_dd, 2),
        'max_drawdown_%': round(max_dd_pct, 2),
        'max_dd_date': dd_end,
        'kelly': round(kelly, 3),
        'half_kelly': round(kelly/2, 3),
        'max_consec_wins': max_cw, 'max_consec_losses': max_cl,
        'long': {'trades': len(lt), 'wr': round(sum(1 for t in lt if t['pnl']>0)/len(lt)*100,1) if lt else 0, 'pnl': round(lp,1)},
        'short': {'trades': len(st), 'wr': round(sum(1 for t in st if t['pnl']>0)/len(st)*100,1) if st else 0, 'pnl': round(sp,1)},
        'result_types': {k: {'count': v['count'], 'pnl': round(v['pnl'],1)} for k, v in results.items()},
        'hourly': hourly_stats,
        'monthly': monthly_stats,
        'trading_days': len(daily),
        'trades_per_day': round(n / len(daily), 2) if daily else 0,
    }

# ── MAIN ──
def main():
    if not mt5.initialize():
        print("MT5 init failed"); return
    
    # Full available history
    to_dt = datetime.utcnow()
    # Go back to earliest available
    from_dt = datetime(2023, 1, 1)
    
    bars = mt5.copy_rates_range(SYMBOL, mt5.TIMEFRAME_M5, from_dt, to_dt)
    if bars is None or len(bars) == 0:
        print("No data"); mt5.shutdown(); return
    
    span_days = (bars[-1]['time'] - bars[0]['time']) / 86400
    
    print("=" * 60)
    print("DMR USD/CHF — Dedicated Backtest Engine")
    print(f"Symbol: {SYMBOL} | Bars: {len(bars):,} | Span: {span_days:.0f} days")
    print(f"Period: {datetime.fromtimestamp(bars[0]['time']).date()} to {datetime.fromtimestamp(bars[-1]['time']).date()}")
    print(f"Params: DeepMult={PARAMS['DeepMult']} KillMult={PARAMS['KillMult']} AR={PARAMS['MinAR']}-{PARAMS['MaxAR']}p")
    print("=" * 60)
    
    # Step 1: Calibrate P90
    hourly_p90, overall_p90 = calibrate_p90(bars)
    
    # Step 2: Run DMR
    print(f"\nRunning DMR engine...")
    trades, skip_ar, skip_p90, skip_ds = run_dmr(bars, hourly_p90, overall_p90)
    
    print(f"\n  Skip reasons: AR={skip_ar} P90={skip_p90} DS={skip_ds}")
    print(f"  Trades generated: {len(trades)}")
    
    if not trades:
        print("  NO TRADES — calibrate parameters")
        mt5.shutdown(); return
    
    # Step 3: Full stats
    stats = compute_stats(trades)
    
    print("\n" + "=" * 60)
    print("USD/CHF DMR RESULTS")
    print("=" * 60)
    print(f"  Trades:          {stats['total_trades']} ({stats['trading_days']} days)")
    print(f"  Win Rate:        {stats['win_rate']}%  ({stats['wins']}W / {stats['losses']}L)")
    print(f"  Total PnL:       {stats['total_pnl_pips']:+.1f} pips")
    print(f"  Profit Factor:   {stats['profit_factor']}")
    print(f"  Expectancy:      {stats['expectancy_pips']:+.2f} pips/trade")
    print(f"  Avg Win:         {stats['avg_win_pips']:+.1f}p  |  Avg Loss: {stats['avg_loss_pips']:+.1f}p")
    print(f"  Payoff Ratio:    {abs(stats['avg_win_pips']/stats['avg_loss_pips']):.2f}")
    print(f"  ---")
    print(f"  Sharpe (daily):  {stats['sharpe_daily']}")
    print(f"  Sortino (daily): {stats['sortino_daily']}")
    print(f"  Calmar Ratio:    {stats['calmar_ratio']}")
    print(f"  Max Drawdown:    ${stats['max_drawdown_$']:.2f} ({stats['max_drawdown_%']:.2f}%)")
    print(f"  Max DD Date:     {stats['max_dd_date']}")
    print(f"  Kelly:           {stats['kelly']}  (Half-Kelly: {stats['half_kelly']})")
    print(f"  Max Cons W/L:    {stats['max_consec_wins']} / {stats['max_consec_losses']}")
    print(f"  ---")
    print(f"  Long:  {stats['long']['trades']} trades | {stats['long']['wr']}% WR | {stats['long']['pnl']:+.1f}p")
    print(f"  Short: {stats['short']['trades']} trades | {stats['short']['wr']}% WR | {stats['short']['pnl']:+.1f}p")
    print(f"  ---")
    print(f"  Result Types:")
    for rt, rv in stats['result_types'].items():
        print(f"    {rt}: {rv['count']} trades, {rv['pnl']:+.1f}p")
    print(f"  ---")
    print(f"  Hourly Breakdown:")
    for h, hv in stats['hourly'].items():
        print(f"    {int(h):02d}:00  {hv['trades']} tr  WR={hv['wr']}%  PnL={hv['pnl']:+.1f}p")
    print(f"  ---")
    print(f"  Monthly Breakdown:")
    for mo, mv in stats['monthly'].items():
        print(f"    {mo}:  {mv['trades']} tr  WR={mv['wr']}%  PnL={mv['pnl']:+.1f}p")
    
    # Save
    out = {
        'stats': {k: v for k, v in stats.items() if k not in ('monthly', 'hourly', 'result_types', 'long', 'short')},
        'long': stats['long'], 'short': stats['short'],
        'result_types': stats['result_types'],
        'hourly': stats['hourly'], 'monthly': stats['monthly'],
        'hourly_p90': {str(k): v for k, v in hourly_p90.items()},
        'overall_p90': overall_p90,
        'params': PARAMS,
        'symbol': SYMBOL,
        'data_span_days': int(span_days),
    }
    outpath = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\dmr_usdchf.json"
    # Save trades separately (big file)
    trades_path = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\dmr_usdchf_trades.json"
    with open(outpath, 'w') as f:
        json.dump(out, f, indent=2, default=str)
    with open(trades_path, 'w') as f:
        json.dump(trades, f, indent=2, default=str)
    print(f"\nSaved: {outpath}")
    print(f"Trades: {trades_path}")
    
    mt5.shutdown()

if __name__ == '__main__':
    main()
