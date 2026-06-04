"""
TEST C + TEST D — Isolate the real bottlenecks
================================================

TEST C: AR Gate Bypass
  - Remove the Asian Range max filter (ar_max)
  - All days trade regardless of Asian session volatility
  - Isolates the AR regime filter as a trade suppressor

TEST D: Trigger Lowering + Session Extension
  - Lower T1 trigger from 12p to 8p (T2: 15p->10p, T3: 19p->13p)
  - Extend session cutoff from 12PM to 4PM EST
  - Captures micro-impulses and afternoon sessions

TEST C+D: Both combined
  - AR gate removed + lower triggers + extended session
  - Maximum trade frequency test

Baseline: Current cleaned engine (extras removed) with original config
"""
import sys, os

QUANTLAB_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(QUANTLAB_ROOT, 'engines'))
sys.path.insert(0, os.path.join(QUANTLAB_ROOT, 'configs'))

import importlib

# Clear any cached engine modules
for key in list(sys.modules.keys()):
    if 'symmetry_trap' in key:
        del sys.modules[key]

from symmetry_trap import SymmetryTrapEngine, DEFAULT_TIER_CONFIG
from symmetry_trap_backtest import SymmetryTrapBacktest

CSV_PATH = os.path.join(QUANTLAB_ROOT, 'data', 'EURUSD_M5.csv')

# ── CONFIGS ──────────────────────────────────────────────────────────────

ORIGINAL_TIERS = {
    "T1": {"ar_max": 20.0, "trigger": 12.0, "au": 10.0},
    "T2": {"ar_max": 30.0, "trigger": 15.0, "au": 12.0},
    "T3": {"ar_max": 45.0, "trigger": 19.0, "au": 15.0},
}

LOW_TRIGGER_TIERS = {
    "T1": {"ar_max": 20.0, "trigger": 8.0, "au": 6.0},
    "T2": {"ar_max": 30.0, "trigger": 10.0, "au": 8.0},
    "T3": {"ar_max": 45.0, "trigger": 13.0, "au": 10.0},
}

# AR gate removed — set ar_max very high so all days pass
NO_AR_GATE_TIERS = {
    "T1": {"ar_max": 999.0, "trigger": 12.0, "au": 10.0},
    "T2": {"ar_max": 999.0, "trigger": 15.0, "au": 12.0},
    "T3": {"ar_max": 999.0, "trigger": 19.0, "au": 15.0},
}

# Combined: no AR gate + low triggers
COMBINED_TIERS = {
    "T1": {"ar_max": 999.0, "trigger": 8.0, "au": 6.0},
    "T2": {"ar_max": 999.0, "trigger": 10.0, "au": 8.0},
    "T3": {"ar_max": 999.0, "trigger": 13.0, "au": 10.0},
}


def run_test(label, tiers, csv_path, session_cutoff=12):
    """Run a backtest with given config. session_cutoff=12 means 12PM, 16 means 4PM."""
    # We need to patch the backtest runner's session cutoff
    # The cutoff is hardcoded at line 435: if bar_est_h >= 12 and engine.state == EngineState.SEARCH: break
    # We'll monkey-patch the run method's cutoff check by subclassing
    
    import symmetry_trap_backtest as stb
    
    # Create a modified backtest class with configurable cutoff
    class CustomBacktest(stb.SymmetryTrapBacktest):
        def run(self, bars):
            if not bars:
                return stb.BacktestResult(symbol=self.symbol)
            
            days = {}
            for bar in bars:
                est_dt = bar.timestamp + timedelta(hours=self.est_offset)
                dk = est_dt.strftime("%Y-%m-%d")
                if dk not in days:
                    days[dk] = []
                days[dk].append(bar)
            
            engine = SymmetryTrapEngine(
                pip_size=self.pip_size, tier_config=self.tier_config,
                symbol=self.symbol, config=self.config
            )
            all_trades = []
            
            for dk in sorted(days.keys()):
                day_bars = sorted(days[dk], key=lambda b: b.timestamp)
                ah, al = self._find_asian_range(day_bars)
                if ah <= 0 or al >= 99999:
                    continue
                
                engine.initialize_session(ah, al)
                if not engine.session_active:
                    continue
                
                active_trade = None
                
                for bar in day_bars:
                    bar_est_h = self._get_est_hour(bar.timestamp)
                    
                    if bar_est_h >= 19 or bar_est_h < 3:
                        continue
                    
                    # CUSTOM CUTOFF
                    if bar_est_h >= session_cutoff and engine.state == stb.EngineState.SEARCH:
                        break
                    
                    signal = engine.process_bar(bar)
                    
                    if signal is None:
                        if active_trade is not None:
                            if engine.state == stb.EngineState.IN_TRADE:
                                pass
                            elif engine.state == stb.EngineState.SEARCH:
                                active_trade = None
                        continue
                    
                    if signal.event == "ENTRY":
                        active_trade = stb.TradeRecord(
                            entry_price=signal.entry_price,
                            sl_price=signal.sl_price,
                            tp_price=signal.tp_price,
                            direction=signal.direction,
                            entry_time=signal.timestamp,
                            tier=engine.tier_name,
                            au_used=signal.au_used,
                            est_hour=bar_est_h,
                        )
                    elif signal.event in ("TP_HIT", "SL_HIT"):
                        if active_trade is not None:
                            active_trade.exit_price = signal.entry_price if signal.event == "TP_HIT" else signal.sl_price
                            active_trade.exit_time = signal.timestamp
                            active_trade.pnl_pips = (
                                (active_trade.exit_price - active_trade.entry_price) / self.pip_size
                                if active_trade.direction == stb.TradeDirection.LONG
                                else (active_trade.entry_price - active_trade.exit_price) / self.pip_size
                            )
                            active_trade.result = "WIN" if active_trade.pnl_pips > 0 else "LOSS"
                            all_trades.append(active_trade)
                            active_trade = None
            
            result = stb.BacktestResult(symbol=self.symbol)
            result.trades = all_trades
            result.total_trades = len(all_trades)
            result.data_days = len(days)
            
            if all_trades:
                wins = [t for t in all_trades if t.result == "WIN"]
                losses = [t for t in all_trades if t.result == "LOSS"]
                result.win_rate = len(wins) / len(all_trades) * 100
                result.total_pnl_pips = sum(t.pnl_pips for t in all_trades)
                result.avg_win_pips = sum(t.pnl_pips for t in wins) / len(wins) if wins else 0
                result.avg_loss_pips = sum(t.pnl_pips for t in losses) / len(losses) if losses else 0
                gross_profit = sum(t.pnl_pips for t in wins)
                gross_loss = abs(sum(t.pnl_pips for t in losses))
                result.profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
                result.expectancy_pips = result.total_pnl_pips / len(all_trades)
                
                # Max DD
                cumulative = 0
                peak = 0
                max_dd = 0
                for t in all_trades:
                    cumulative += t.pnl_pips
                    peak = max(peak, cumulative)
                    max_dd = max(max_dd, peak - cumulative)
                result.max_drawdown_pips = max_dd
                result.max_drawdown_pct = max_dd / 10000  # rough
            
            return result
    
    from datetime import timedelta
    from symmetry_trap import EngineState, TradeDirection
    
    bt = CustomBacktest(
        pip_size=0.0001,
        tier_config=tiers,
        symbol="EURUSD",
        config={"pip_value": 0.0001, "tiers": tiers}
    )
    
    # Load bars from CSV
    bars = stb.SymmetryTrapBacktest._load_bars_from_csv(bt, CSV_PATH) if hasattr(bt, '_load_bars_from_csv') else None
    
    # If _load_bars_from_csv doesn't exist, use the public interface
    if bars is None:
        # Use run_from_csv which handles loading internally
        # We need a different approach — use the standard backtest but with our custom class
        result = bt.run_from_csv(CSV_PATH)
    else:
        result = bt.run(bars)
    
    td = result.total_trades
    days = result.data_days
    wr = result.win_rate
    pnl = result.total_pnl_pips
    pf = result.profit_factor
    dd = result.max_drawdown_pct
    avg_w = result.avg_win_pips
    avg_l = result.avg_loss_pips
    exp = result.expectancy_pips
    
    print("{}".format("=" * 60))
    print(label)
    print("=" * 60)
    print("Trades: {} | Days: {} | {:.3f} tr/day".format(td, days, td/days if days else 0))
    print("WR: {:.1f}% | PnL: {:.1f}p | PF: {:.2f} | MaxDD: {:.1f}%".format(wr, pnl, pf, dd))
    print("Avg Win: {:.1f}p | Avg Loss: {:.1f}p | Expectancy: {:.1f}p".format(avg_w, avg_l, exp))
    sys.stdout.flush()
    
    return {'td': td, 'days': days, 'wr': wr, 'pnl': pnl, 'pf': pf, 'dd': dd,
            'avg_w': avg_w, 'avg_l': avg_l, 'exp': exp}


if __name__ == '__main__':
    from datetime import timedelta
    from symmetry_trap import EngineState, TradeDirection
    
    print("TEST C+D — Isolating Real Bottlenecks")
    print("Baseline: 1,125 tr | 84.6% WR | +5,100p | PF 8.18")
    print("")
    
    # Reload clean engine
    for key in list(sys.modules.keys()):
        if 'symmetry_trap' in key:
            del sys.modules[key]
    import symmetry_trap
    importlib.reload(symmetry_trap)
    import symmetry_trap_backtest
    importlib.reload(symmetry_trap_backtest)
    
    # TEST C: AR gate removed
    results_c = run_test(
        "TEST C — AR Gate Removed (no ar_max filter, original triggers)",
        NO_AR_GATE_TIERS, CSV_PATH, session_cutoff=12
    )
    
    # TEST D: Low triggers + extended session
    results_d = run_test(
        "TEST D — Low Triggers (8/10/13p) + 4PM Cutoff",
        LOW_TRIGGER_TIERS, CSV_PATH, session_cutoff=16
    )
    
    # TEST C+D: Combined
    results_cd = run_test(
        "TEST C+D — AR Gate Removed + Low Triggers + 4PM Cutoff",
        COMBINED_TIERS, CSV_PATH, session_cutoff=16
    )
    
    # ── COMPARISON ──
    baseline = {'td': 1125, 'wr': 84.6, 'pnl': 5100.0, 'pf': 8.18}
    
    print("\n{}".format("=" * 70))
    print("COMPARISON vs BASELINE (1,125 tr | 84.6% WR | +5,100p | PF 8.18)")
    print("=" * 70)
    print("{:<30} {:>8} {:>8} {:>8} {:>8}".format("Test", "Trades", "WR%", "PnL", "PF"))
    print("{:<30} {:>8} {:>8} {:>8} {:>8}".format("------", "-------", "----", "---", "--"))
    print("{:<30} {:>8} {:>8.1f} {:>8.1f} {:>8.2f}".format(
        "Baseline", baseline['td'], baseline['wr'], baseline['pnl'], baseline['pf']))
    print("{:<30} {:>8} {:>8.1f} {:>8.1f} {:>8.2f}".format(
        "C: No AR gate", results_c['td'], results_c['wr'], results_c['pnl'], results_c['pf']))
    print("{:<30} {:>8} {:>8.1f} {:>8.1f} {:>8.2f}".format(
        "D: Low trig + 4PM", results_d['td'], results_d['wr'], results_d['pnl'], results_d['pf']))
    print("{:<30} {:>8} {:>8.1f} {:>8.1f} {:>8.2f}".format(
        "C+D: Combined", results_cd['td'], results_cd['wr'], results_cd['pnl'], results_cd['pf']))
    
    print("\n--- Delta vs Baseline ---")
    for label, r in [("C: No AR gate", results_c), ("D: Low trig + 4PM", results_d), ("C+D: Combined", results_cd)]:
        d_tr = r['td'] - baseline['td']
        d_pnl = r['pnl'] - baseline['pnl']
        print("{}: {:+d} trades | {:+.1f}p PnL | PF {:+.2f}".format(label, d_tr, d_pnl, r['pf'] - baseline['pf']))
