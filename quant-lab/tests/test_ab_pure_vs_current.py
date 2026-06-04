"""
A/B TEST: Pure Option B vs Current Engine
Same data (EURUSD), same trigger, same window.
Only difference: the 3 extras Arch flagged.
"""
import sys, os
for key in list(sys.modules.keys()):
    if 'asset_configs' in key or 'symmetry_trap' in key:
        del sys.modules[key]

sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')

from symmetry_trap_backtest import SymmetryTrapBacktest

csv_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURUSD_M5.csv'

# EURUSD config (same for both tests)
eurusd_tiers = {
    "T1": {"ar_max": 20.0, "trigger": 12.0, "au": 10.0},
    "T2": {"ar_max": 30.0, "trigger": 15.0, "au": 12.0},
    "T3": {"ar_max": 45.0, "trigger": 19.0, "au": 15.0},
}
eurusd_config = {"pip_value": 0.0001, "tiers": eurusd_tiers}

# ── TEST B: Current engine (with extras) ──
print("=" * 60)
print("TEST B — CURRENT ENGINE (with 4h timeout, 80% kill, dynamic DZ)")
print("=" * 60)
sys.stdout.flush()
bt_b = SymmetryTrapBacktest(pip_size=0.0001, tier_config=eurusd_tiers, symbol="EURUSD_B", config=eurusd_config)
result_b = bt_b.run_from_csv(csv_path)
td_b = result_b.total_trades
days_b = result_b.data_days
wr_b = result_b.win_rate
pnl_b = result_b.total_pnl_pips
pf_b = result_b.profit_factor
dd_b = result_b.max_drawdown_pct
avg_win_b = result_b.avg_win_pips
avg_loss_b = result_b.avg_loss_pips
exp_b = result_b.expectancy_pips
tier_b = {t: sum(1 for tr in result_b.trades if getattr(tr, 'tier', '') == t) for t in ['T1','T2','T3']}
loops_b = result_b.loop_stats or {}

print("Trades: {} | Days: {} | {:.3f} tr/day".format(td_b, days_b, td_b/days_b if days_b else 0))
print("WR: {:.1f}% | PnL: {:.1f}p | PF: {:.2f} | MaxDD: {:.1f}%".format(wr_b, pnl_b, pf_b, dd_b))
print("Avg Win: {:.1f}p | Avg Loss: {:.1f}p | Expectancy: {:.1f}p".format(avg_win_b, avg_loss_b, exp_b))
print("Tiers: {}".format(tier_b))
for i in range(1,6):
    ls = loops_b.get(i, {})
    if ls:
        print("  Loop {}: {}tr | {:.1f}% WR | {:.1f}p PnL".format(i, ls.get('trades',0), ls.get('wr',0), ls.get('pnl',0)))
sys.stdout.flush()

# ── TEST A: Pure Option B (no extras) ──
# We need to temporarily patch the engine to disable:
# 1. 4-hour loop timeout
# 2. 80% kill switch
# 3. Dynamic DZ (use flat 20-50% for all loops)
# We do this by monkey-patching the engine class
import symmetry_trap as st

# Save originals
original_process_bar = st.SymmetryTrapEngine.process_bar

def pure_option_b_process_bar(self, bar):
    """Patched process_bar with extras disabled."""
    if not self.session_active:
        return None

    if self.swing_origin is None:
        self.swing_origin = bar.close

    # EXTRA #1 DISABLED: No 4-hour timeout
    # (removed entirely)

    active_trig = self.trigger_pips * self.pip_size
    up_move = bar.high - self.swing_origin
    dn_move = self.swing_origin - bar.low

    KILL_SWITCH_PCT = 0.80

    # ── STATE: SEARCH ──
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

    # ── STATE: WAIT_RETRACE ──
    elif self.state == st.EngineState.WAIT_RETRACE:
        # EXTRA #2 DISABLED: No 80% kill switch
        # (kill switch check removed)

        # EXTRA #3 DISABLED: Flat 20-50% DZ for ALL loops
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

        if au_penetrated and fib_penetrated:
            self.state = st.EngineState.WAIT_OCC
        elif au_penetrated and not fib_penetrated:
            # DZ failed — reset to next loop
            _loop = self.loop_count
            self._reset_state_keep_loop(bar.close)
            self.loop_count = min(_loop + 1, self.max_loops)
            self.loop_start_time = bar.timestamp
            if self.loop_count >= self.max_loops:
                self.session_active = False
            return st.TradeSignal(
                event="NO_GO", direction=None, entry_price=None,
                sl_price=None, tp_price=None, au_used=self.au_pips,
                timestamp=bar.timestamp,
                reason="DZ failed (AU hit, fib missed) — loop {} -> {}".format(_loop, self.loop_count),
                loop_count=_loop,
            )

    # ── STATE: WAIT_OCC ──
    elif self.state == st.EngineState.WAIT_OCC:
        # EXTRA #2 DISABLED: No kill switch in WAIT_OCC either
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

    # ── STATE: IN_TRADE ──
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
                sig = st.TradeSignal(event="SL_HIT", direction=_dir, entry_price=_entry,
                    sl_price=_sl, tp_price=_tp, au_used=self.au_pips,
                    timestamp=bar.timestamp, reason="SL hit loop {}".format(_loop),
                    loop_count=_loop)
                self.signal_log.append(sig)
                return sig

    return None

# Apply monkey patch
st.SymmetryTrapEngine.process_bar = pure_option_b_process_bar

print("\n" + "=" * 60)
print("TEST A — PURE OPTION B (no timeout, no kill switch, flat 20-50% DZ)")
print("=" * 60)
sys.stdout.flush()
bt_a = SymmetryTrapBacktest(pip_size=0.0001, tier_config=eurusd_tiers, symbol="EURUSD_A", config=eurusd_config)
result_a = bt_a.run_from_csv(csv_path)
td_a = result_a.total_trades
days_a = result_a.data_days
wr_a = result_a.win_rate
pnl_a = result_a.total_pnl_pips
pf_a = result_a.profit_factor
dd_a = result_a.max_drawdown_pct
avg_win_a = result_a.avg_win_pips
avg_loss_a = result_a.avg_loss_pips
exp_a = result_a.expectancy_pips
tier_a = {t: sum(1 for tr in result_a.trades if getattr(tr, 'tier', '') == t) for t in ['T1','T2','T3']}
loops_a = result_a.loop_stats or {}

print("Trades: {} | Days: {} | {:.3f} tr/day".format(td_a, days_a, td_a/days_a if days_a else 0))
print("WR: {:.1f}% | PnL: {:.1f}p | PF: {:.2f} | MaxDD: {:.1f}%".format(wr_a, pnl_a, pf_a, dd_a))
print("Avg Win: {:.1f}p | Avg Loss: {:.1f}p | Expectancy: {:.1f}p".format(avg_win_a, avg_loss_a, exp_a))
print("Tiers: {}".format(tier_a))
for i in range(1,6):
    ls = loops_a.get(i, {})
    if ls:
        print("  Loop {}: {}tr | {:.1f}% WR | {:.1f}p PnL".format(i, ls.get('trades',0), ls.get('wr',0), ls.get('pnl',0)))

# Restore original
st.SymmetryTrapEngine.process_bar = original_process_bar

# ── COMPARISON ──
print("\n" + "=" * 60)
print("A/B COMPARISON")
print("=" * 60)
print("{:<20} {:>10} {:>10}".format("Metric", "Test A", "Test B"))
print("{:<20} {:>10} {:>10}".format("------", "-------", "-------"))
print("{:<20} {:>10} {:>10}".format("Trades", td_a, td_b))
print("{:<20} {:>10.3f} {:>10.3f}".format("Tr/day", td_a/days_a if days_a else 0, td_b/days_b if days_b else 0))
print("{:<20} {:>9.1f}% {:>9.1f}%".format("WR", wr_a, wr_b))
print("{:<20} {:>10.1f} {:>10.1f}".format("PnL (pips)", pnl_a, pnl_b))
print("{:<20} {:>10.2f} {:>10.2f}".format("Profit Factor", pf_a, pf_b))
print("{:<20} {:>9.1f}% {:>9.1f}%".format("Max DD", dd_a, dd_b))
print("{:<20} {:>10.1f} {:>10.1f}".format("Avg Win", avg_win_a, avg_win_b))
print("{:<20} {:>10.1f} {:>10.1f}".format("Avg Loss", avg_loss_a, avg_loss_b))
print("{:<20} {:>10.1f} {:>10.1f}".format("Expectancy", exp_a, exp_b))
print("{:<20} {:>10} {:>10}".format("T1/T2/T3", str(tier_a), str(tier_b)))
diff = td_a - td_b
pct = (td_a/td_b - 1)*100 if td_b else 0
print("\nTrade count delta: {} ({:+.1f}%)".format(diff, pct))
if diff > 0:
    print(">>> Pure Option B produces MORE trades")
elif diff < 0:
    print(">>> Current engine produces MORE trades")
else:
    print(">>> IDENTICAL trade count")
