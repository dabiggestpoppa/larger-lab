"""
Symmetry Trap v4 - AU-Based Structural Engine
=============================================
State Machine: SEARCH -> WAIT_RETRACE -> WAIT_OCC -> IN_TRADE
Fib Confluence: 38.2%-50% zone + exact AU retracement
Gear Shift Override: intraday tier reclassification
"""
import json, math
from datetime import datetime, timedelta
import numpy as np

ASSET_CONFIG = {
    'EURUSD.PRO': {
        'pip_mult': 10000, 'pip_size': 0.0001,
        't1_trigger': 12, 't2_trigger': 15, 't3_trigger': 19,
        't1_au': 10, 't2_au': 12, 't3_au': 15, 'mt25_au': 25,
        'gear_t1_t2': 15, 'gear_t1_t3': 19, 'gear_t2_t3': 19, 'gear_t3_mt25': 25,
        'min_ar': 3, 'max_ar': 45,
    },
    'USDCHF.PRO': {
        'pip_mult': 10000, 'pip_size': 0.0001,
        't1_trigger': 13, 't2_trigger': 18, 't3_trigger': 24,
        't1_au': 11, 't2_au': 15, 't3_au': 18, 'mt25_au': 25,
        'gear_t1_t2': 13, 'gear_t1_t3': 24, 'gear_t2_t3': 24, 'gear_t3_mt25': 25,
        'min_ar': 3, 'max_ar': 45,
    },
}

EST_OFFSET = -5
HARD_EXIT_HOUR = 17

def pips_to_price(pips, pip_mult):
    return pips / pip_mult

def price_to_pips(price, pip_mult):
    return price * pip_mult

def get_est_hour(dt_utc):
    return (dt_utc.hour + EST_OFFSET) % 24


class SymmetryTrapEngine:
    def __init__(self, symbol='USDCHF.PRO'):
        self.symbol = symbol
        self.cfg = ASSET_CONFIG.get(symbol, ASSET_CONFIG['USDCHF.PRO'])
        self.reset_session()

    def reset_session(self):
        self.state = 'SEARCH'
        self.swing_origin = None
        self.impulse_extreme = None
        self.impulse_direction = 0
        self.kill_switch_level = None
        self.base_tier = None
        self.shifted_tier = None
        self.au_target = 0
        self.fib_zone_low = None
        self.fib_zone_high = None
        self.entry_price = None
        self.sl_price = None
        self.tp_price = None
        self.trade_direction = None
        self.loop_count = 0

    def classify_tier(self, ar_pips):
        cfg = self.cfg
        if ar_pips < cfg['t1_trigger']:
            return None
        if ar_pips < cfg['t2_trigger']:
            return 'T1'
        if ar_pips < cfg['t3_trigger']:
            return 'T2'
        if ar_pips <= cfg['t3_trigger'] * 1.5:
            return 'T3'
        return None

    def get_au_for_tier(self, tier):
        cfg = self.cfg
        return {'T1': cfg['t1_au'], 'T2': cfg['t2_au'], 'T3': cfg['t3_au'], 'MT25': cfg['mt25_au']}.get(tier, cfg['t1_au'])

    def detect_gear_shift(self, impulse_pips, base_tier):
        cfg = self.cfg
        if base_tier == 'T1':
            if impulse_pips >= cfg['gear_t1_t3']: return 'T3'
            if impulse_pips >= cfg['gear_t1_t2']: return 'T2'
        elif base_tier == 'T2':
            if impulse_pips >= cfg['gear_t2_t3']: return 'T3'
        elif base_tier == 'T3':
            if impulse_pips >= cfg['gear_t3_mt25']: return 'MT25'
        return base_tier

    def in_fib_zone(self, price):
        if self.fib_zone_low is None or self.fib_zone_high is None:
            return False
        return self.fib_zone_low <= price <= self.fib_zone_high

    def price_in_zone(self, bar):
        if self.fib_zone_low is None:
            return False
        return bar['low'] <= self.fib_zone_high and bar['high'] >= self.fib_zone_low

    def run_on_bars(self, bars):
        completed_trades = []
        cfg = self.cfg
        pm = cfg['pip_mult']
        self.reset_session()

        # Asian Range (7PM-3AM EST)
        asian_bars = [b for b in bars if b['est_h'] >= 19 or b['est_h'] < 3]
        if len(asian_bars) < 2:
            return completed_trades

        asian_high = max(b['high'] for b in asian_bars)
        asian_low = min(b['low'] for b in asian_bars)
        ar_pips = price_to_pips(asian_high - asian_low, pm)

        base_tier = self.classify_tier(ar_pips)
        if base_tier is None:
            return completed_trades
        self.base_tier = base_tier

        # Bias Lock: first M5 close outside Asian band (3AM-11AM)
        bias_window = [b for b in bars if 3 <= b['est_h'] < 11]
        bias = 0
        bias_locked_idx = -1
        for i, b in enumerate(bias_window):
            if b['close'] > asian_high:
                bias = 1; bias_locked_idx = i; break
            elif b['close'] < asian_low:
                bias = -1; bias_locked_idx = i; break

        if bias == 0:
            return completed_trades

        post_bias = bias_window[bias_locked_idx + 1:]
        if not post_bias:
            return completed_trades

        self.state = 'SEARCH'
        self.swing_origin = post_bias[0]['close']

        i = 0
        while i < len(post_bias) and self.loop_count < 50:
            b = post_bias[i]

            if b['est_h'] >= HARD_EXIT_HOUR:
                if self.state == 'IN_TRADE':
                    pnl = self._compute_pnl(b['close'])
                    completed_trades.append(self._make_trade_record(b['close'], 'HARD_EXIT', pnl))
                break

            if self.state == 'SEARCH':
                result = self._state_search(b, i, post_bias)
                if result == 'killed':
                    self.state = 'SEARCH'
                    self.swing_origin = b['close']
                    self.loop_count += 1
            elif self.state == 'WAIT_RETRACE':
                result = self._state_wait_retrace(b)
                if result == 'killed':
                    self.state = 'SEARCH'
                    self.swing_origin = b['close']
                    self.loop_count += 1
            elif self.state == 'WAIT_OCC':
                self._state_wait_occ(b)
            elif self.state == 'IN_TRADE':
                result = self._state_in_trade(b, completed_trades)
                if result == 'exited':
                    self.state = 'SEARCH'
                    self.swing_origin = b['close']
                    self.loop_count += 1
            i += 1

        return completed_trades

    def _state_search(self, bar, idx, all_bars):
        cfg = self.cfg
        pm = cfg['pip_mult']
        if self.swing_origin is None:
            self.swing_origin = bar['close']

        move_up = price_to_pips(bar['high'] - self.swing_origin, pm)
        move_dn = price_to_pips(self.swing_origin - bar['low'], pm)
        trigger = cfg[self.base_tier.lower() + '_trigger']

        if self.impulse_direction == 0:
            if move_up >= trigger:
                self.impulse_direction = 1
                self.impulse_extreme = bar['high']
            elif move_dn >= trigger:
                self.impulse_direction = -1
                self.impulse_extreme = bar['low']
            else:
                return 'continue'

        # Update extreme
        if self.impulse_direction == 1 and bar['high'] > self.impulse_extreme:
            self.impulse_extreme = bar['high']
        elif self.impulse_direction == -1 and bar['low'] < self.impulse_extreme:
            self.impulse_extreme = bar['low']

        impulse_range = abs(self.impulse_extreme - self.swing_origin)
        if self.impulse_direction == 1:
            self.kill_switch_level = self.swing_origin + impulse_range * 0.80
        else:
            self.kill_switch_level = self.swing_origin - impulse_range * 0.80

        fib_low = min(self.swing_origin, self.fib_zone_low if self.fib_zone_low else self.swing_origin)
        fib_high = max(self.swing_origin, self.impulse_extreme)
        fib_range = fib_high - fib_low
        self.fib_zone_low = fib_low + fib_range * 0.382
        self.fib_zone_high = fib_low + fib_range * 0.50
        if self.fib_zone_low > self.fib_zone_high:
            self.fib_zone_low, self.fib_zone_high = self.fib_zone_high, self.fib_zone_low

        self.state = 'WAIT_RETRACE'
        current_move = price_to_pips(impulse_range, pm)
        shifted = self.detect_gear_shift(current_move, self.base_tier)
        self.shifted_tier = shifted if shifted != self.base_tier else None
        self.au_target = self.get_au_for_tier(shifted)
        return 'continue'

    def _state_wait_retrace(self, bar):
        if self.impulse_direction == 1:
            if bar['close'] < self.kill_switch_level:
                return 'killed'
        else:
            if bar['close'] > self.kill_switch_level:
                return 'killed'

        retrace_valid = False
        if self.impulse_direction == 1:
            retrace_pips = price_to_pips(self.impulse_extreme - bar['low'], self.cfg['pip_mult'])
        else:
            retrace_pips = price_to_pips(bar['high'] - self.impulse_extreme, self.cfg['pip_mult'])

        if retrace_pips >= self.au_target * 0.8:
            retrace_valid = True
        if self.in_fib_zone(bar['close']) or self.price_in_zone(bar):
            retrace_valid = True

        if retrace_valid:
            self.state = 'WAIT_OCC'
        return 'continue'

    def _state_wait_occ(self, bar):
        is_bull = bar['close'] > bar['open']
        is_bear = bar['close'] < bar['open']
        entry = None

        if self.impulse_direction == 1 and is_bear:
            entry = bar['close']; self.trade_direction = 'SHORT'
        elif self.impulse_direction == -1 and is_bull:
            entry = bar['close']; self.trade_direction = 'LONG'
        elif self.impulse_direction == 1 and is_bull:
            entry = bar['close']; self.trade_direction = 'LONG'
        elif self.impulse_direction == -1 and is_bear:
            entry = bar['close']; self.trade_direction = 'SHORT'

        if entry is not None:
            self.entry_price = entry
            au_price = pips_to_price(self.au_target, self.cfg['pip_mult'])
            self.sl_price = self.impulse_extreme
            if self.trade_direction == 'LONG':
                self.tp_price = entry + au_price
            else:
                self.tp_price = entry - au_price
            self.state = 'IN_TRADE'
        return 'continue'

    def _state_in_trade(self, bar, completed_trades):
        exit_price = None
        exit_reason = None
        if self.trade_direction == 'LONG':
            if bar['high'] >= self.tp_price:
                exit_price = self.tp_price; exit_reason = 'TP'
            elif bar['close'] <= self.sl_price:
                exit_price = bar['close']; exit_reason = 'SL'
        else:
            if bar['low'] <= self.tp_price:
                exit_price = self.tp_price; exit_reason = 'TP'
            elif bar['close'] >= self.sl_price:
                exit_price = bar['close']; exit_reason = 'SL'

        if exit_price is not None:
            pnl = self._compute_pnl(exit_price)
            completed_trades.append(self._make_trade_record(exit_price, exit_reason, pnl))
            return 'exited'
        return 'continue'

    def _compute_pnl(self, exit_price):
        if self.trade_direction == 'LONG':
            return (exit_price - self.entry_price) * self.cfg['pip_mult']
        return (self.entry_price - exit_price) * self.cfg['pip_mult']

    def _make_trade_record(self, exit_price, reason, pnl):
        return {
            'direction': self.trade_direction,
            'entry': round(self.entry_price, 5),
            'exit': round(exit_price, 5),
            'sl': round(self.sl_price, 5),
            'tp': round(self.tp_price, 5),
            'pnl_pips': round(pnl, 1),
            'exit_reason': reason,
            'tier': self.base_tier,
            'shifted_tier': self.shifted_tier,
            'au': self.au_target,
            'loop': self.loop_count + 1,
        }


def load_bars_mt5(symbol, count=250000):
    import MetaTrader5 as mt5
    if not mt5.initialize():
        return None
    bars = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, count)
    mt5.shutdown()
    if bars is None or len(bars) == 0:
        return None
    result = []
    for bar in bars:
        dt = datetime.fromtimestamp(bar['time'])
        result.append({
            'time': bar['time'], 'dt': dt,
            'est_h': get_est_hour(dt),
            'open': bar['open'], 'high': bar['high'],
            'low': bar['low'], 'close': bar['close'],
        })
    return result


def group_sessions(bars):
    sessions = {}
    for bar in bars:
        est_h = bar['est_h']
        d = bar['dt'].date()
        from datetime import timedelta as td
        if est_h < 3:
            d = (bar['dt'] + td(hours=EST_OFFSET)).date()
        key = str(d)
        sessions.setdefault(key, []).append(bar)
    return sessions


def run_backtest(symbol='USDCHF.PRO', max_sessions=None):
    print('=' * 60)
    print('SYMMETRY TRAP v4 - AU-Based Structural State Machine')
    print('States: SEARCH | WAIT_RETRACE | WAIT_OCC | IN_TRADE')
    print(f'Symbol: {symbol}')
    print('=' * 60)

    bars = load_bars_mt5(symbol, 250000)
    if not bars:
        print('ERROR: No MT5 data'); return []

    print(f'Bars loaded: {len(bars):,}')
    sessions = group_sessions(bars)
    dates = sorted(sessions.keys())
    if max_sessions:
        dates = dates[:max_sessions]
    print(f'Sessions: {len(dates)}')

    engine = SymmetryTrapEngine(symbol)
    all_trades = []

    for i, d in enumerate(dates):
        trades = engine.run_on_bars(sessions[d])
        all_trades.extend(trades)
        if (i + 1) % 100 == 0:
            wr, pnl, n = _stats(all_trades)
            print(f'  [{i+1}/{len(dates)}] {n} tr, {wr:.1f}% WR, {pnl:+.0f}p')

    _print_results(all_trades, symbol)
    return all_trades


def _stats(trades):
    if not trades: return 0, 0, 0
    wins = sum(1 for t in trades if t['pnl_pips'] > 0)
    pnl = sum(t['pnl_pips'] for t in trades)
    return wins / len(trades) * 100, pnl, len(trades)


def _print_results(trades, symbol):
    if not trades:
        print('No trades'); return
    wins = [t for t in trades if t['pnl_pips'] > 0]
    losses = [t for t in trades if t['pnl_pips'] <= 0]
    total = sum(t['pnl_pips'] for t in trades)
    wr = len(wins) / len(trades) * 100
    avg_w = np.mean([t['pnl_pips'] for t in wins]) if wins else 0
    avg_l = np.mean([t['pnl_pips'] for t in losses]) if losses else 0
    pf = abs(sum(t['pnl_pips'] for t in wins) / sum(t['pnl_pips'] for t in losses)) if losses and sum(t['pnl_pips'] for t in losses) != 0 else float('inf')
    exp = total / len(trades)
    tp_t = [t for t in trades if t['exit_reason'] == 'TP']
    sl_t = [t for t in trades if t['exit_reason'] == 'SL']
    eod_t = [t for t in trades if t['exit_reason'] == 'HARD_EXIT']
    long_t = [t for t in trades if t['direction'] == 'LONG']
    short_t = [t for t in trades if t['direction'] == 'SHORT']

    # Loop breakdown
    loops = {}
    for t in trades:
        l = t['loop']
        loops.setdefault(l, []).append(t)

    print()
    print('=' * 60)
    print('RESULTS')
    print('=' * 60)
    print(f'  Trades:        {len(trades)} ({len(wins)}W / {len(losses)}L)')
    print(f'  Win Rate:      {wr:.1f}%')
    print(f'  Total PnL:     {total:+.1f} pips')
    print(f'  Avg Win:       {avg_w:+.1f}p  |  Avg Loss: {avg_l:+.1f}p')
    print(f'  Payoff Ratio:  {abs(avg_w/avg_l):.2f}' if avg_l else '  Payoff: N/A')
    print(f'  Profit Factor: {pf:.2f}')
    print(f'  Expectancy:    {exp:+.2f} pips/trade')
    print(f'  ---')
    print(f'  TP:  {len(tp_t)} ({len(tp_t)/len(trades)*100:.1f}%)  PnL={sum(t["pnl_pips"] for t in tp_t):+.0f}p')
    print(f'  SL:  {len(sl_t)} ({len(sl_t)/len(trades)*100:.1f}%)  PnL={sum(t["pnl_pips"] for t in sl_t):+.0f}p')
    print(f'  EOD: {len(eod_t)} ({len(eod_t)/len(trades)*100:.1f}%)  PnL={sum(t["pnl_pips"] for t in eod_t):+.0f}p')
    print(f'  ---')
    print(f'  Long:  {len(long_t)} tr  WR={sum(1 for t in long_t if t["pnl_pips"]>0)/max(len(long_t),1)*100:.1f}%')
    print(f'  Short: {len(short_t)} tr  WR={sum(1 for t in short_t if t["pnl_pips"]>0)/max(len(short_t),1)*100:.1f}%')
    print(f'  ---')
    print(f'  Loop Breakdown:')
    for lo in sorted(loops.keys()):
        lt = loops[lo]
        lw = sum(1 for t in lt if t['pnl_pips'] > 0)
        lp = sum(t['pnl_pips'] for t in lt)
        print(f'    Loop {lo}: {len(lt)} tr  WR={lw/len(lt)*100:.1f}%  PnL={lp:+.0f}p')


if __name__ == '__main__':
    import sys
    sym = sys.argv[1] if len(sys.argv) > 1 else 'USDCHF.PRO'
    run_backtest(sym)
