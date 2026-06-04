"""
A/B TEST: Pure Option B vs Current Engine (with Telemetry)
Same data (EURUSD 2022-2026), same triggers, same OCC logic.
Test A: Disable 4h timeout, disable 80% kill switch, flat 20-50% DZ for all loops
Test B: Current engine (all extras active)

Method: Monkey-patch only the specific lines that implement the extras.
All other engine logic (state machine, OCC, TP/SL, loop tracking) stays intact.
"""
import sys, os, types

for key in list(sys.modules.keys()):
    if 'asset_config' in key or 'symmetry_trap' in key:
        del sys.modules[key]

sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')

import symmetry_trap as st
from symmetry_trap_backtest import SymmetryTrapBacktest

csv_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURUSD_M5.csv'

eurusd_tiers = {
    "T1": {"ar_max": 20.0, "trigger": 12.0, "au": 10.0},
    "T2": {"ar_max": 30.0, "trigger": 15.0, "au": 12.0},
    "T3": {"ar_max": 45.0, "trigger": 19.0, "au": 15.0},
}
eurusd_config = {"pip_value": 0.0001, "tiers": eurusd_tiers}

def get_telemetry(engine):
    return {
        "kill_switch_80pct": getattr(engine, 'tel_kill_switch_80pct', 0),
        "timeout_4hr": getattr(engine, 'tel_timeout_4hr', 0),
        "loop1_reject_shallow": getattr(engine, 'tel_loop1_reject_shallow', 0),
        "loop1_reject_deep": getattr(engine, 'tel_loop1_reject_deep', 0),
        "max_loops_exhausted": getattr(engine, 'tel_max_loops_exhausted', 0),
    }

def print_result(label, result, tel):
    td = result.total_trades
    days = result.data_days
    wr = result.win_rate
    pnl = result.total_pnl_pips
    pf = result.profit_factor
    dd = result.max_drawdown_pct
    avg_w = result.avg_win_pips
    avg_l = result.avg_loss_pips
    exp = result.expectancy_pips
    tier = {t: sum(1 for tr in result.trades if getattr(tr, 'tier', '') == t) for t in ['T1','T2','T3']}
    loops = result.loop_stats or {}

    print("\n{}".format("="*60))
    print(label)
    print("="*60)
    print("Trades: {} | Days: {} | {:.3f} tr/day".format(td, days, td/days if days else 0))
    print("WR: {:.1f}% | PnL: {:.1f}p | PF: {:.2f} | MaxDD: {:.1f}%".format(wr, pnl, pf, dd))
    print("Avg Win: {:.1f}p | Avg Loss: {:.1f}p | Expectancy: {:.1f}p".format(avg_w, avg_l, exp))
    print("Tiers: {}".format(tier))
    for i in range(1,6):
        ls = loops.get(i, {})
        if ls:
            print("  Loop {}: {}tr | {:.1f}% WR | {:.1f}p PnL".format(i, ls.get('trades',0), ls.get('wr',0), ls.get('pnl',0)))
    print("TELEMETRY: {}".format(tel))
    return td, days, wr, pnl, pf, dd

# ── TEST B: Current engine (run first with clean engine) ──
print("Running TEST B (Current Engine with telemetry)...")
sys.stdout.flush()
bt_b = SymmetryTrapBacktest(pip_size=0.0001, tier_config=eurusd_tiers, symbol="EURUSD_B", config=eurusd_config)
result_b = bt_b.run_from_csv(csv_path)

# The backtest runner creates the engine internally. We need to access it.
# Check if the runner stores the engine reference
engine_b = None
if hasattr(bt_b, '_engine'):
    engine_b = bt_b._engine
elif hasattr(bt_b, 'engine'):
    engine_b = bt_b.engine

tel_b = get_telemetry(engine_b) if engine_b else {}
td_b, days_b, wr_b, pnl_b, pf_b, dd_b = print_result(
    "TEST B — CURRENT ENGINE (4h timeout, 80% kill, dynamic DZ 32/20)",
    result_b, tel_b)

# ── TEST A: Pure Option B ──
# Patch the engine class to disable extras while keeping all logic intact.
# Strategy: Override __init__ to set _pure_mode flag, then wrap process_bar
# to skip the 3 extra checks when _pure_mode is True.

_original_process_bar = st.SymmetryTrapEngine.process_bar

def _pure_process_bar(self, bar):
    """Wrapped process_bar that disables the 3 extras when _pure_mode is set."""
    if not self.session_active:
        return None

    if self.swing_origin is None:
        self.swing_origin = bar.close

    # EXTRA #1 DISABLED: Skip 4-hour timeout check
    # (original code checks: if loop_start_time and loop_count > 1 and > 4h → deactivate)
    # We simply skip this block.

    KILL_SWITCH_PCT = 0.80
    active_trig = self.trigger_pips * self.pip_size
    up_move = bar.high - self.swing_origin
    dn_move = self.swing_origin - bar.low

    # ── STATE: SEARCH (identical to original) ──
    if self.state == st.EngineState.SEARCH:
        if up_move >= active_trig:
            self.impulse_direction = st.TradeDirection.LONG
            self.impulse_extreme = bar.high
            self.impulse_size_pips = up_move / self.pip_size
            self.kill_switch_level = self.impulse_extreme - up_move * KILL_SWITCH_PCT
            self.state = st.EngineState.WAIT_RETRACE
        elif dn_move >= active_trig:
            self.impulse_direction = st.TradeDirection.SHORT
            self.impulse_extreme = bar.low
            self.impulse_size_pips = dn_move / self.pip_size
            self.kill_switch_level = self.impulse_extreme + dn_move * KILL_SWITCH_PCT
            self.state = st.EngineState.WAIT_RETRACE

    # ── STATE: WAIT_RETRACE (with extras disabled) ──
    elif self.state == st.EngineState.WAIT_RETRACE:
        # EXTRA #2 DISABLED: No 80% kill switch
        # Skip the entire kill switch check block

        # EXTRA #3 DISABLED: Flat 20-50% DZ for ALL loops (not 32% for Loop 1)
        min_retrace_pct = 0.20
        max_retrace_pct = 0.50

        if self.impulse_direction == st.TradeDirection.LONG:
            pullback_px = self.impulse_extreme - bar.low
        else:
            pullback_px = bar.high - self.impulse_extreme

        pullback_pips = pullback_px / self.pip_size
        retrace_pct = pullback_pips / self.impulse_size_pips if self.impulse_size_pips > 0 else 0

        au_penetrated = pullback_pips >= self.au_pips
        fib_penetrated = min_retrace_pct <= retrace_pct <= max_retrace_pct

        # TELEMETRY: Track what Loop 1 would have rejected with strict 32% floor
        if self.loop_count == 1 and au_penetrated and not fib_penetrated:
            if retrace_pct < 0.32:
                self.tel_loop1_reject_shallow += 1
            elif retrace_pct > 0.50:
                self.tel_loop1_reject_deep += 1

        # Cascade P90 bypass (Loop 2+ only) — keep original logic
        cascade_bypass = False
        if (self.loop_count >= 2 and retrace_pct < min_retrace_pct
                and self.cascade_bias is not None
                and self.cascade_bias == self.impulse_direction):
            cascade_bypass = True

        if au_penetrated or fib_penetrated or cascade_bypass:
            self.state = st.EngineState.WAIT_OCC

    # ── STATE: WAIT_OCC (with kill switch disabled) ──
    elif self.state == st.EngineState.WAIT_OCC:
        # EXTRA #2 DISABLED: No kill switch in WAIT_OCC
        occ_confirmed = (
            (self.impulse_direction == st.TradeDirection.LONG and bar.is_bullish) or
            (self.impulse_direction == st.TradeDirection.SHORT and bar.is_bearish)
        )
        if occ_confirmed:
            self.entry_price = bar.close
            self.sl_price = self.impulse_extreme
            self.tp_price = bar.close + self.active_au * self.impulse_direction.value
            self.state = st.EngineState.IN_TRADE
            self._just_entered = True
            sig = st.TradeSignal(
                event="ENTRY", direction=self.impulse_direction,
                entry_price=self.entry_price, sl_price=self.sl_price,
                tp_price=self.tp_price, au_used=self.au_pips,
                timestamp=bar.timestamp,
                reason="OCC confirmed — entry (loop {})".format(self.loop_count),
                loop_count=self.loop_count,
            )
            self.signal_log.append(sig)
            return sig

    # ── STATE: IN_TRADE (identical to original) ──
    elif self.state == st.EngineState.IN_TRADE:
        if self._just_entered:
            self._just_entered = False
            return None

        if self.impulse_direction == st.TradeDirection.LONG:
            if bar.high >= self.tp_price:
                _entry = self.entry_price; _sl = self.sl_price; _tp = self.tp_price
                _dir = self.impulse_direction; _loop = self.loop_count
                self._reset_state_keep_loop(self.tp_price)
                self.loop_count = min(_loop + 1, self.max_loops)
                self.loop_start_time = bar.timestamp
                self._check_max_loops()
                sig = st.TradeSignal(event="TP_HIT", direction=_dir, entry_price=_entry,
                    sl_price=_sl, tp_price=_tp, au_used=self.au_pips,
                    timestamp=bar.timestamp, reason="TP hit loop {}".format(_loop),
                    loop_count=_loop)
                self.signal_log.append(sig)
                return sig
            if bar.close <= self.sl_price:
                _entry = self.entry_price; _sl = self.sl_price; _tp = self.tp_price
                _dir = self.impulse_direction; _loop = self.loop_count
                self._reset_state_keep_loop(self.sl_price)
                self.loop_count = min(_loop + 1, self.max_loops)
                self.loop_start_time = bar.timestamp
                self._check_max_loops()
                sig = st.TradeSignal(event="SL_HIT", direction=_dir, entry_price=_entry,
                    sl_price=_sl, tp_price=_tp, au_used=self.au_pips,
                    timestamp=bar.timestamp, reason="SL hit loop {}".format(_loop),
                    loop_count=_loop)
                self.signal_log.append(sig)
                return sig
        else:  # SHORT
            if bar.low <= self.tp_price:
                _entry = self.entry_price; _sl = self.sl_price; _tp = self.tp_price
                _dir = self.impulse_direction; _loop = self.loop_count
                self._reset_state_keep_loop(self.tp_price)
                self.loop_count = min(_loop + 1, self.max_loops)
                self.loop_start_time = bar.timestamp
                self._check_max_loops()
                sig = st.TradeSignal(event="TP_HIT", direction=_dir, entry_price=_entry,
                    sl_price=_sl, tp_price=_tp, au_used=self.au_pips,
                    timestamp=bar.timestamp, reason="TP hit loop {}".format(_loop),
                    loop_count=_loop)
                self.signal_log.append(sig)
                return sig
            if bar.close >= self.sl_price:
                _entry = self.entry_price; _sl = self.sl_price; _tp = self.tp_price
                _dir = self.impulse_direction; _loop = self.loop_count
                self._reset_state_keep_loop(self.sl_price)
                self.loop_count = min(_loop + 1, self.max_loops)
                self.loop_start_time = bar.timestamp
                self._check_max_loops()
                sig = st.TradeSignal(event="SL_HIT", direction=_dir, entry_price=_entry,
                    sl_price=_sl, tp_price=_tp, au_used=self.au_pips,
                    timestamp=bar.timestamp, reason="SL hit loop {}".format(_loop),
                    loop_count=_loop)
                self.signal_log.append(sig)
                return sig

    return None

# Apply patch
st.SymmetryTrapEngine.process_bar = _pure_process_bar

print("\nRunning TEST A (Pure Option B — patched engine)...")
sys.stdout.flush()
bt_a = SymmetryTrapBacktest(pip_size=0.0001, tier_config=eurusd_tiers, symbol="EURUSD_A", config=eurusd_config)
result_a = bt_a.run_from_csv(csv_path)

engine_a = None
if hasattr(bt_a, '_engine'):
    engine_a = bt_a._engine
elif hasattr(bt_a, 'engine'):
    engine_a = bt_a.engine

tel_a = get_telemetry(engine_a) if engine_a else {}
td_a, days_a, wr_a, pnl_a, pf_a, dd_a = print_result(
    "TEST A — PURE OPTION B (no timeout, no kill, flat 20-50% DZ)",
    result_a, tel_a)

# Restore original
st.SymmetryTrapEngine.process_bar = _original_process_bar

# ── COMPARISON ──
print("\n{}".format("="*60))
print("A/B COMPARISON")
print("="*60)
print("{:<25} {:>12} {:>12}".format("Metric", "Pure B", "Current"))
print("{:<25} {:>12} {:>12}".format("------", "-------", "-------"))
print("{:<25} {:>12} {:>12}".format("Trades", td_a, td_b))
print("{:<25} {:>12.3f} {:>12.3f}".format("Tr/day", td_a/days_a if days_a else 0, td_b/days_b if days_b else 0))
print("{:<25} {:>11.1f}% {:>11.1f}%".format("WR", wr_a, wr_b))
print("{:<25} {:>12.1f} {:>12.1f}".format("PnL (pips)", pnl_a, pnl_b))
print("{:<25} {:>12.2f} {:>12.2f}".format("Profit Factor", pf_a, pf_b))
print("{:<25} {:>11.1f}% {:>11.1f}%".format("Max DD", dd_a, dd_b))
print("{:<25} {:>12} {:>12}".format("Kill Switch", tel_a.get('kill_switch_80pct',0), tel_b.get('kill_switch_80pct',0)))
print("{:<25} {:>12} {:>12}".format("4H Timeout", tel_a.get('timeout_4hr',0), tel_b.get('timeout_4hr',0)))
print("{:<25} {:>12} {:>12}".format("L1 Reject Shallow", tel_a.get('loop1_reject_shallow',0), tel_b.get('loop1_reject_shallow',0)))
print("{:<25} {:>12} {:>12}".format("L1 Reject Deep", tel_a.get('loop1_reject_deep',0), tel_b.get('loop1_reject_deep',0)))
print("{:<25} {:>12} {:>12}".format("Max Loops Exhausted", tel_a.get('max_loops_exhausted',0), tel_b.get('max_loops_exhausted',0)))

diff = td_a - td_b
pct = (td_a/td_b - 1)*100 if td_b else 0
print("\nTrade count delta: {} ({:+.1f}%)".format(diff, pct))
if diff > 50:
    print(">>> Pure Option B produces SIGNIFICANTLY MORE trades")
    print(">>> The 3 extras ARE suppressing trade frequency")
elif diff > 0:
    print(">>> Pure Option B produces slightly more trades")
    print(">>> Extras have a mild suppressive effect")
elif diff < -50:
    print(">>> Current engine produces SIGNIFICANTLY MORE trades")
    print(">>> The extras are NOT the bottleneck — something else is")
elif diff < 0:
    print(">>> Current engine produces slightly more trades")
    print(">>> Extras are NOT suppressing frequency")
else:
    print(">>> IDENTICAL trade count — extras have zero impact")
