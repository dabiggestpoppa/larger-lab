"""Compare MC-pooled results vs actual backtest results."""
import json, random
from pathlib import Path

QUANT_LAB = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab")
MC_DIR = QUANT_LAB / "reports" / "per-asset"

ASSET_PNL = {}
for f in sorted(MC_DIR.glob("*_mc_results.json")):
    sym = f.stem.replace("_mc_results", "")
    d = json.load(open(f))
    pnls = d.get("per_trade_pnl", [])
    if len(pnls) >= 10:
        ASSET_PNL[sym] = pnls

portfolio_5 = ["GBPJPY", "CHFJPY", "GBPAUD", "GBPNZD", "NZDUSD"]

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

print("=== MC-POOLED vs ACTUAL BACKTEST ===")
print(f"Portfolio: {portfolio_5}")
print(f"\nMC-POOLED:")
print(f"  Trades: {n_trades} | WR: {mc_wr:.1f}% | PF: {mc_pf:.2f} | PnL: {mc_pnl:+.1f}p")
print(f"  Term PnL median: {terminal_pnls[n//2]:.1f}p")
print(f"  MaxDD 95th: {max_dds[int(n*0.95)]:.1f}p | 99th: {max_dds[int(n*0.99)]:.1f}p")

actual_path = QUANT_LAB / "reports" / "portfolio_mc" / "portfolio_mc_5assets.json"
if actual_path.exists():
    actual = json.load(open(actual_path))
    a = actual["pooled_stats"]
    mc_sec = actual["monte_carlo"]
    print(f"\nACTUAL BACKTEST:")
    print(f"  Trades: {a['total_trades']} | WR: {a['win_rate']:.1f}% | PF: {a['profit_factor']:.2f} | PnL: {a['total_pnl_pips']:+.1f}p")
    print(f"  MaxDD 95th: {mc_sec['max_dd_95th']}p | 99th: {mc_sec['max_dd_99th']}p")
    print(f"\nDELTA:")
    print(f"  WR: {mc_wr - a['win_rate']:+.1f}% | PF: {mc_pf - a['profit_factor']:+.2f} | PnL: {mc_pnl - a['total_pnl_pips']:+.1f}p")
    print(f"  MaxDD 95th: {max_dds[int(n*0.95)] - mc_sec['max_dd_95th']:+.1f}p")
else:
    print("No actual backtest file found")

print(f"\n=== PER-ASSET: stored BT_WR vs recomputed from per_trade_pnl ===")
for sym in sorted(ASSET_PNL.keys()):
    pnls = ASSET_PNL[sym]
    recomputed_wr = sum(1 for p in pnls if p > 0) / len(pnls) * 100
    d = json.load(open(MC_DIR / (sym + "_mc_results.json")))
    bt = d.get("backtest", {})
    stored_wr = bt.get("win_rate", 0)
    if stored_wr < 1.0:
        stored_wr = stored_wr * 100
    delta = recomputed_wr - stored_wr
    flag = " MISMATCH" if abs(delta) > 0.5 else ""
    print(f"  {sym:10s}: recomputed={recomputed_wr:.1f}% stored={stored_wr:.1f}% delta={delta:+.2f}%{flag}")
