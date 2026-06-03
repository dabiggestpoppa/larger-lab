"""Compare MC-pooled results vs actual backtest results for portfolios we already have."""
import sys, json, random
from pathlib import Path

QUANT_LAB = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab")
MC_DIR = QUANT_LAB / "reports" / "per-asset"

# Load per-asset PnLs
ASSET_PNL = {}
for f in sorted(MC_DIR.glob("*_mc_results.json")):
    sym = f.stem.replace("_mc_results", "")
    d = json.load(open(f))
    pnls = d.get("per_trade_pnl", [])
    if len(pnls) >= 10:
        ASSET_PNL[sym] = pnll

# ── 5-asset portfolio we already ran ──
portfolio_5 = ["GBPJPY", "CHFJPY", "GBPAUD", "GBPNZD", "NZDUSD"]

# MC pooled approach
pooled = []
for sym in portfolio_5:
    if sym in ASSET_PNL:
        pooled.extend(ASSET_PNL[sym])

n_trades = len(pooled)
wins = [p for p in pooled if p > 0]
losses = [p for p in pooled if p <= 0]
mc_wr = len(wins) / n_trades * 100
mc_pf = sum(wins) / abs(sum(losses)) if losses else 999
mc_pnl = sum(pooled)

random.seed(42)
terminal_pnls = []
max_dds = []
for _ in range(10000):
    shuffled = random.sample(pooled, n_trades)
    terminal_pnls.append(sum(shuffled))
    cumulative = 0; peak = 0; max_dd = 0
    for p in shuffled:
        cumulative += p
        if cumulative > peak: peak = cumulative
        dd = peak - cumulative
        if dd > max_dd: max_dd = dd
    max_dds.append(max_dd)
terminal_pnls.sort()
max_dds.sort()
n = len(terminal_pnls)

print("=== MC-POOLED vs ACTUAL BACKTEST COMPARISON ===")
print(f"\nPortfolio: {portfolio_5}")
print(f"\nMC-POOLED (what the matrix generator does):")
print(f"  Pooled trades: {n_trades}")
print(f"  WR: {mc_wr:.1f}%")
print(f"  PF: {mc_pf:.2f}")
print(f"  Total PnL: {mc_pnl:+.1f}p")
print(f"  Terminal PnL median: {terminal_pnls[n//2]:.1f}p")
print(f"  MaxDD 95th: {max_dds[int(n*0.95)]:.1f}p")
print(f"  MaxDD 99th: {max_dds[int(n*0.99)]:.1f}p")

# Now compare to the actual backtest results from portfolio_mc_5assets.json
import json as j
actual_path = QUANT_LAB / "reports" / "portfolio_mc" / "portfolio_mc_5assets.json"
if actual_path.exists():
    actual = j.load(open(actual_path))
    a = actual["pooled_stats"]
    mc_section = actual["monte_carlo"]
    print(f"\nACTUAL BACKTEST (run_portfolio_mc_no_eu_uchf.py):")
    print(f"  Pooled trades: {a['total_trades']}")
    print(f"  WR: {a['win_rate']:.1f}%")
    print(f"  PF: {a['profit_factor']:.2f}")
    print(f"  Total PnL: {a['total_pnl_pips']:+.1f}p")
    print(f"  MaxDD 95th: {mc_section['max_dd_95th']}p")
    print(f"  MaxDD 99th: {mc_section['max_dd_99th']}p")

    print(f"\nDELTA (MC-pooled vs Actual):")
    print(f"  WR delta: {mc_wr - a['win_rate']:+.1f}%")
    print(f"  PF delta: {mc_pf - a['profit_factor']:+.2f}")
    print(f"  PnL delta: {mc_pnl - a['total_pnl_pips']:+.1f}p")
    print(f"  MaxDD 95th delta: {max_dds[int(n*0.95)] - mc_section['max_dd_95th']:+.1f}p")
else:
    print(f"\nNo actual backtest file found at {actual_path}")

# ── Per-asset MC vs backtest comparison ──
print(f"\n\n=== PER-ASSET: MC backtest WR vs stored backtest WR ===")
for sym in sorted(ASSET_PNL.keys()):
    pnls = ASSET_PNL[sym]
    mc_wins = sum(1 for p in pnls if p > 0)
    mc_wr = mc_wins / len(pnls) * 100
    
    # Get stored backtest WR
    d = json.load(open(MC_DIR / (sym + "_mc_results.json")))
    bt = d.get("backtest", {})
    bt_wr = bt.get("win_rate", 0)
    bt_trades = bt.get("trades", 0)
    
    # Some store WR as fraction, some as percent
    if bt_wr < 1.0:
        bt_wr_display = bt_wr * 100
    else:
        bt_wr_display = bt_wr
    
    delta = mc_wr - bt_wr_display
    flag = " ⚠️" if abs(delta) > 1 else ""
    print(f"  {sym:10s}: MC_WR={mc_wr:.1f}% | BT_WR={bt_wr_display:.1f}% | delta={delta:+.1f}%{flag}")
