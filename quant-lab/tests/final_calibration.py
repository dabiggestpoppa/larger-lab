"""
FINAL CALIBRATION — Gold Standard Configuration
================================================
Per THE BIBLE directive:
- AR gate: ar_max=60 (session filter only, not tier classifier)
- T1 trigger: 10 pips (T2/T3 proportional)
- Session cutoff: 4PM EST
- Tier logic: strictly by impulse size (T1<20p, T2=20-30p, T3>30p), decoupled from AR

Target: 3,500-4,500 trades | PF > 10.0 | WR > 80%
"""
import sys, os

QUANTLAB_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(QUANTLAB_ROOT, 'engines'))

from symmetry_trap_backtest import SymmetryTrapBacktest

CSV_PATH = os.path.join(QUANTLAB_ROOT, 'data', 'EURUSD_M5.csv')

# Final calibration config — matches updated DEFAULT_TIER_CONFIG
FINAL_TIERS = {
    "T1": {"ar_max": 60.0, "au": 8.0, "trigger": 10.0},
    "T2": {"ar_max": 60.0, "au": 10.0, "trigger": 10.0},
    "T3": {"ar_max": 60.0, "au": 12.0, "trigger": 10.0},
}

bt = SymmetryTrapBacktest(
    pip_size=0.0001,
    tier_config=FINAL_TIERS,
    symbol="EURUSD",
    config={"pip_value": 0.0001, "tiers": FINAL_TIERS}
)
bt.session_cutoff = 16  # 4PM EST

result = bt.run_from_csv(CSV_PATH)

td = result.total_trades
days = result.data_days
wr = result.win_rate
pnl = result.total_pnl_pips
pf = result.profit_factor
dd_pct = result.max_drawdown_pct
dd_pips = result.max_drawdown_pips
avg_w = result.avg_win_pips
avg_l = result.avg_loss_pips
exp = result.expectancy_pips
tier_counts = {t: sum(1 for tr in result.trades if getattr(tr, 'tier', '') == t) for t in ['T1', 'T2', 'T3']}
loops = result.loop_stats or {}

# Consecutive wins/losses
max_consec_wins = 0
max_consec_losses = 0
cur_wins = 0
cur_losses = 0
for tr in result.trades:
    if tr.result == "WIN":
        cur_wins += 1
        cur_losses = 0
        max_consec_wins = max(max_consec_wins, cur_wins)
    else:
        cur_losses += 1
        cur_wins = 0
        max_consec_losses = max(max_consec_losses, cur_losses)

print("=" * 65)
print("FINAL CALIBRATION — Gold Standard Configuration")
print("=" * 65)
print("AR gate: ar_max=60 | Trigger: 10p | Cutoff: 4PM EST")
print("Tier: by impulse size (T1<20p, T2=20-30p, T3>30p)")
print("")
print("Trades: {} | Days: {} | {:.3f} tr/day".format(td, days, td/days if days else 0))
print("WR: {:.1f}% | PnL: {:.1f}p | PF: {:.2f}".format(wr, pnl, pf))
print("MaxDD: {:.1f}% ({:.1f}p) | Expectancy: {:.1f}p".format(dd_pct, dd_pips, exp))
print("Avg Win: {:.1f}p | Avg Loss: {:.1f}p".format(avg_w, avg_l))
print("Max Consec Wins: {} | Max Consec Losses: {}".format(max_consec_wins, max_consec_losses))
print("Tiers: {}".format(tier_counts))
print("")
print("--- Loop Stats ---")
for i in range(1, 6):
    ls = loops.get(i, {})
    if ls:
        print("  Loop {}: {}tr | {:.1f}% WR | {:.1f}p PnL".format(
            i, ls.get('trades', 0), ls.get('wr', 0), ls.get('pnl', 0)))
print("")
print("--- Delta vs Baseline (1,125 tr | 84.6% WR | +5,100p | PF 8.18) ---")
print("Trades: {:+d} ({:+.1f}%)".format(td - 1125, (td/1125 - 1)*100))
print("WR: {:+.1f}%".format(wr - 84.6))
print("PnL: {:+.1f}p".format(pnl - 5100.0))
print("PF: {:+.2f}".format(pf - 8.18))
