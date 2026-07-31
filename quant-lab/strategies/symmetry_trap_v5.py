"""
Symmetry Trap v5 - Direct 3-Layer Implementation from Manual
=============================================================
Layer 1: Bias Lock - first M5 close outside Asian Range
Layer 2: Atomic Entry - impulse (body >= AU*0.5) in bias dir + OCC pullback
Layer 3: Distribution Targets - -25%, -50%, -100% of AR from band edge

SL: M5 close back inside Asian band (81.2% rule)
TP1: -25% AR | TP2: -50% AR | TP3: -100% AR
Hard Exit: 5PM EST

Uses AU (Atomic Unit) from P90 body distribution, not DZ approximation.
AU values per tier from manual.
"""
import json, math, sys
from datetime import datetime, timedelta
import numpy as np

ASSET_CONFIG = {
    'USDCHF.PRO': {
        'pip_mult': 10000,
        't1_trigger': 13, 't2_trigger': 18, 't3_trigger': 24,
        't1_au': 11, 't2_au': 15, 't3_au': 18, 'mt25_au': 25,
        'min_ar': 5, 'max_ar': 60,
    },
    'EURUSD.PRO': {
        'pip_mult': 10000,
        't1_trigger': 12, 't2_trigger': 15, 't3_trigger': 19,
        't1_au': 10, 't2_au': 12, 't3_au': 15, 'mt25_au': 25,
        'min_ar': 3, 'max_ar': 45,
    },
}

EST_OFFSET = -5
HARD_EXIT_HOUR = 17

def pt(pips, pm): return pips / pm
def pp(price, pm): return price * pm
def est_hour(dt): return (dt.hour + EST_OFFSET) % 24


def run_session(day_bars, symbol='USDCHF.PRO'):
    """Run one session through the 3-layer Symmetry Trap engine."""
    cfg = ASSET_CONFIG.get(symbol, ASSET_CONFIG['USDCHF.PRO'])
    pm = cfg['pip_mult']
    trades = []

    # === LAYER 1: Asian Range (7PM-3AM EST) ===
    asian_bars = [b for b in day_bars if b['est_h'] >= 19 or b['est_h'] < 3]
    if len(asian_bars) < 2:
        return trades

    asian_high = max(b['high'] for b in asian_bars)
    asian_low = min(b['low'] for b in asian_bars)
    ar_pips = pp(asian_high - asian_low, pm)

    # Classify tier
    if ar_pips < cfg['min_ar'] or ar_pips > cfg['max_ar']:
        return trades

    if ar_pips < cfg['t1_trigger']:
        return trades
    elif ar_pips < cfg['t2_trigger']:
        tier = 'T1'; au = cfg['t1_au']
    elif ar_pips < cfg['t3_trigger']:
        tier = 'T2'; au = cfg['t2_au']
    elif ar_pips <= cfg['t3_trigger'] * 1.5:
        tier = 'T3'; au = cfg['t3_au']
    else:
        return trades

    # === LAYER 1: Bias Lock (first M5 close outside Asian band) ===
    bias_window = [b for b in day_bars if 3 <= b['est_h'] < 11]
    bias = 0
    bias_idx = -1
    for i, b in enumerate(bias_window):
        if b['close'] > asian_high:
            bias = 1; bias_idx = i; break   # BULL bias (broke above)
        if b['close'] < asian_low:
            bias = -1; bias_idx = i; break   # BEAR bias (broke below)

    if bias == 0:
        return trades

    asian_edge = asian_high if bias == 1 else asian_low
    post_bias = bias_window[bias_idx:]

    # === LAYER 2: Atomic Entry ===
    # Scan for impulse candle (body >= AU*0.5) in bias direction
    # followed by opposite candle close (OCC pullback)
    i = 0
    while i < len(post_bias) - 1:
        b = post_bias[i]
        body = abs(b['close'] - b['open'])
        body_pips = pp(body, pm)
        is_bull = b['close'] > b['open']
        is_bear = b['close'] < b['open']

        # Impulse in bias direction?
        impulse_found = False
        if bias == 1 and is_bull and body_pips >= au * 0.5:
            impulse_found = True
        elif bias == -1 and is_bear and body_pips >= au * 0.5:
            impulse_found = True

        if impulse_found:
            # Check next candle for OCC (opposite close)
            next_b = post_bias[i + 1]
            occ = False
            if bias == 1 and next_b['close'] < next_b['open']:
                occ = True  # Bull bias, bear pullback candle
            elif bias == -1 and next_b['close'] > next_b['open']:
                occ = True  # Bear bias, bull pullback candle

            if occ:
                # Entry at OCC close
                entry = next_b['close']
                trade_dir = 'SHORT' if bias == 1 else 'LONG'  # fade the bias

                # SL: close back inside Asian band
                if bias == 1:
                    sl = asian_high  # close above Asian high = invalidation
                else:
                    sl = asian_low   # close below Asian low = invalidation

                # === LAYER 3: Distribution Targets ===
                t25 = asian_edge + ar_pips * 0.25 * (1 if bias == 1 else -1) / pm * pm / pm
                # Actually compute distribution targets properly
                # -25% of AR from band edge in trade direction
                if trade_dir == 'SHORT':
                    t25_price = asian_edge + pt(ar_pips * -0.25, pm)
                    t50_price = asian_edge + pt(ar_pips * -0.50, pm)
                    t100_price = asian_edge + pt(ar_pips * -1.00, pm)
                else:
                    t25_price = asian_edge + pt(ar_pips * 0.25, pm)
                    t50_price = asian_edge + pt(ar_pips * 0.50, pm)
                    t100_price = asian_edge + pt(ar_pips * 1.00, pm)

                # === LAYER 4: Trade Management ===
                # Use TP1 (-25% AR) as primary, let runners to -100%
                # Exit logic: TP (wick hit), SL (close inside band), or EOD
                tp1 = t25_price
                tp2 = t50_price
                tp_star = t100_price  # use TP2 as the main target for now

                # Scan remaining bars for exit
                entry_idx = day_bars.index(next_b) if next_b in day_bars else -1
                remaining = day_bars[entry_idx + 1:] if entry_idx > 0 else []

                exited = False
                for rb in remaining:
                    if rb['est_h'] >= HARD_EXIT_HOUR:
                        # Hard exit at bar close
                        exit_price = rb['close']
                        if trade_dir == 'SHORT':
                            pnl = pp(entry - exit_price, pm)
                        else:
                            pnl = pp(exit_price - entry, pm)
                        trades.append({
                            'dir': trade_dir, 'entry': round(entry, 5),
                            'exit': round(exit_price, 5), 'sl': round(sl, 5),
                            'tp1': round(tp1, 5), 'tp2': round(tp2, 5),
                            'pnl_pips': round(pnl, 1), 'reason': 'EOD',
                            'tier': tier, 'au': au, 'loop': i
                        })
                        exited = True
                        break

                    if trade_dir == 'SHORT':
                        # TP hit (wick)
                        if rb['high'] >= tp1 and rb['low'] <= tp1:
                            exit_price = tp1
                            pnl = pp(entry - exit_price, pm)
                            trades.append({
                                'dir': trade_dir, 'entry': round(entry, 5),
                                'exit': round(exit_price, 5), 'sl': round(sl, 5),
                                'tp1': round(tp1, 5), 'pnl_pips': round(pnl, 1),
                                'reason': 'TP25', 'tier': tier, 'au': au, 'loop': i
                            })
                            exited = True
                            break
                        if rb['low'] <= tp2:
                            exit_price = tp2
                            pnl = pp(entry - exit_price, pm)
                            trades.append({
                                'dir': trade_dir, 'entry': round(entry, 5),
                                'exit': round(exit_price, 5), 'sl': round(sl, 5),
                                'tp2': round(tp2, 5), 'pnl_pips': round(pnl, 1),
                                'reason': 'TP50', 'tier': tier, 'au': au, 'loop': i
                            })
                            exited = True
                            break
                        if rb['close'] >= sl:  # SL = close back inside band
                            exit_price = rb['close']
                            pnl = pp(entry - exit_price, pm)
                            trades.append({
                                'dir': trade_dir, 'entry': round(entry, 5),
                                'exit': round(exit_price, 5), 'sl': round(sl, 5),
                                'pnl_pips': round(pnl, 1), 'reason': 'SL',
                                'tier': tier, 'au': au, 'loop': i
                            })
                            exited = True
                            break
                    else:  # LONG
                        if rb['low'] <= tp1 and rb['high'] >= tp1:
                            exit_price = tp1; pnl = pp(exit_price - entry, pm)
                            trades.append({
                                'dir': trade_dir, 'entry': round(entry, 5),
                                'exit': round(exit_price, 5), 'pnl_pips': round(pnl, 1),
                                'reason': 'TP25', 'tier': tier, 'au': au, 'loop': i
                            })
                            exited = True
                            break
                        if rb['high'] >= tp2:
                            exit_price = tp2; pnl = pp(exit_price - entry, pm)
                            trades.append({
                                'dir': trade_dir, 'entry': round(entry, 5),
                                'exit': round(exit_price, 5), 'pnl_pips': round(pnl, 1),
                                'reason': 'TP50', 'tier': tier, 'au': au, 'loop': i
                            })
                            exited = True
                            break
                        if rb['close'] <= sl:
                            exit_price = rb['close']
                            pnl = pp(exit_price - entry, pm)
                            trades.append({
                                'dir': trade_dir, 'entry': round(entry, 5),
                                'exit': round(exit_price, 5), 'pnl_pips': round(pnl, 1),
                                'reason': 'SL', 'tier': tier, 'au': au, 'loop': i
                            })
                            exited = True
                            break

                if exited:
                    # Continue scanning for next trade in same session
                    i += 2
                    continue
                else:
                    # Trade still open at end of data
                    pass

        i += 1

    return trades


def load_bars_mt5(symbol, count=250000):
    import MetaTrader5 as mt5
    if not mt5.initialize(): return None
    bars = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, count)
    mt5.shutdown()
    if bars is None or len(bars) == 0: return None
    result = []
    for bar in bars:
        dt = datetime.fromtimestamp(bar['time'])
        result.append({
            'time': bar['time'], 'dt': dt, 'est_h': est_hour(dt),
            'open': bar['open'], 'high': bar['high'],
            'low': bar['low'], 'close': bar['close'],
        })
    return result


def group_sessions(bars):
    sessions = {}
    for bar in bars:
        est_h = bar['est_h']
        d = bar['dt'].date()
        if est_h < 3:
            d = (bar['dt'] + timedelta(hours=EST_OFFSET)).date()
        key = str(d)
        sessions.setdefault(key, []).append(bar)
    return sessions


def run_backtest(symbol='USDCHF.PRO'):
    print('=' * 60)
    print('SYMMETRY TRAP v5 - 3-Layer Direct Implementation')
    print('Layer 1: Bias Lock | Layer 2: Atomic Entry | Layer 3: Distribution')
    print(f'Symbol: {symbol}')
    print('=' * 60)

    bars = load_bars_mt5(symbol, 250000)
    if not bars:
        print('No data'); return []

    print(f'Bars: {len(bars):,}')
    sessions = group_sessions(bars)
    dates = sorted(sessions.keys())
    print(f'Sessions: {len(dates)}')

    all_trades = []
    for i, d in enumerate(dates):
        trades = run_session(sessions[d], symbol)
        all_trades.extend(trades)
        if (i+1) % 100 == 0:
            wr, pnl, n = _stats(all_trades)
            print(f'  [{i+1}/{len(dates)}] {n} tr, {wr:.1f}% WR, {pnl:+.0f}p')

    _print_results(all_trades, symbol)
    return all_trades


def _stats(trades):
    if not trades: return 0, 0, 0
    wins = sum(1 for t in trades if t['pnl_pips'] > 0)
    return wins/len(trades)*100, sum(t['pnl_pips'] for t in trades), len(trades)


def _print_results(trades, symbol):
    if not trades:
        print('No trades'); return
    wins = [t for t in trades if t['pnl_pips'] > 0]
    losses = [t for t in trades if t['pnl_pips'] <= 0]
    total = sum(t['pnl_pips'] for t in trades)
    wr = len(wins)/len(trades)*100
    avg_w = np.mean([t['pnl_pips'] for t in wins]) if wins else 0
    avg_l = np.mean([t['pnl_pips'] for t in losses]) if losses else 0
    pf = abs(sum(t['pnl_pips'] for t in wins)/sum(t['pnl_pips'] for t in losses)) if losses and sum(t['pnl_pips'] for t in losses) != 0 else 0
    exp = total/len(trades)

    tp25 = [t for t in trades if t['reason'] == 'TP25']
    tp50 = [t for t in trades if t['reason'] == 'TP50']
    sl_t = [t for t in trades if t['reason'] == 'SL']
    eod = [t for t in trades if t['reason'] == 'EOD']
    longs = [t for t in trades if t['dir'] == 'LONG']
    shorts = [t for t in trades if t['dir'] == 'SHORT']

    # Tier breakdown
    tiers = {}
    for t in trades:
        tiers.setdefault(t['tier'], []).append(t)

    # Loop breakdown
    loops = {}
    for t in trades:
        l = t.get('loop', 0)
        loops.setdefault(l, []).append(t)

    print()
    print('=' * 60)
    print('RESULTS')
    print('=' * 60)
    print(f'  Trades:        {len(trades)} ({len(wins)}W / {len(losses)}L)')
    print(f'  Win Rate:      {wr:.1f}%')
    print(f'  Total PnL:     {total:+.1f} pips')
    print(f'  Avg Win:       {avg_w:+.1f}p  |  Avg Loss: {avg_l:+.1f}p')
    print(f'  Payoff:        {abs(avg_w/max(avg_l,0.01)):.2f}')
    print(f'  Profit Factor: {pf:.2f}')
    print(f'  Expectancy:    {exp:+.2f} pips/trade')
    print(f'  ---')
    print(f'  TP25: {len(tp25)} ({len(tp25)/len(trades)*100:.1f}%)  PnL={sum(t["pnl_pips"] for t in tp25):+.0f}p')
    print(f'  TP50: {len(tp50)} ({len(tp50)/len(trades)*100:.1f}%)  PnL={sum(t["pnl_pips"] for t in tp50):+.0f}p')
    print(f'  SL:   {len(sl_t)} ({len(sl_t)/len(trades)*100:.1f}%)  PnL={sum(t["pnl_pips"] for t in sl_t):+.0f}p')
    print(f'  EOD:  {len(eod)} ({len(eod)/len(trades)*100:.1f}%)  PnL={sum(t["pnl_pips"] for t in eod):+.0f}p')
    print(f'  ---')
    print(f'  Long:  {len(longs)} tr  WR={sum(1 for t in longs if t["pnl_pips"]>0)/max(len(longs),1)*100:.1f}%')
    print(f'  Short: {len(shorts)} tr  WR={sum(1 for t in shorts if t["pnl_pips"]>0)/max(len(shorts),1)*100:.1f}%')
    print(f'  ---')
    print(f'  Tier Breakdown:')
    for ti in sorted(tiers.keys()):
        tt = tiers[ti]
        tw = sum(1 for t in tt if t['pnl_pips'] > 0)
        tp = sum(t['pnl_pips'] for t in tt)
        print(f'    {ti}: {len(tt)} tr  WR={tw/len(tt)*100:.1f}%  PnL={tp:+.0f}p')


if __name__ == '__main__':
    sym = sys.argv[1] if len(sys.argv) > 1 else 'USDCHF.PRO'
    run_backtest(sym)
