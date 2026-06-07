"""Quick EURUSD test — verify engine fix produces same results as original."""
import sys, time
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs")
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines")
from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest, load_m5_csv

pair = "EURUSD"
cfg = ASSET_CONFIGS[pair]
pip_value = cfg.get("pip_value", 0.0001)

bars, _ = load_m5_csv(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURUSD_M5.csv", pip_size=pip_value)
print(f"EURUSD: {len(bars)} bars, pip={pip_value}")

# Test 1: mult=1.0 (baseline) — tier_config from scaled, config for session params
tiers = {}
for tn in ["T1", "T2", "T3"]:
    t = cfg["tiers"][tn]
    tiers[tn] = {"ar_max": t["ar_max"], "au": t["au"], "trigger": t["trigger"]}

t0 = time.time()
bt = SymmetryTrapBacktest(pip_size=pip_value, tier_config=tiers, config=cfg, symbol=pair)
result = bt.run(bars)
elapsed = time.time() - t0

print(f"\nTest 1 — tier_config=original, config=cfg:")
print(f"  Trades={result.total_trades} | WR={result.win_rate:.1f}% | PF={result.profit_factor:.2f} | PnL={result.total_pnl_pips:.1f} | {elapsed:.1f}s")

# Test 2: Like the original sweep — only config, no tier_config override
t0 = time.time()
bt2 = SymmetryTrapBacktest(pip_size=pip_value, config=cfg, symbol=pair)
result2 = bt2.run(bars)
elapsed2 = time.time() - t0

print(f"\nTest 2 — config=cfg only (original method):")
print(f"  Trades={result2.total_trades} | WR={result2.win_rate:.1f}% | PF={result2.profit_factor:.2f} | PnL={result2.total_pnl_pips:.1f} | {elapsed2:.1f}s")

# Test 3: config=None, tier_config=scaled (the broken method from v1)
t0 = time.time()
bt3 = SymmetryTrapBacktest(pip_size=0.10, tier_config=tiers, symbol=pair, config=None)
result3 = bt3.run(bars)
elapsed3 = time.time() - t0

print(f"\nTest 3 — pip_size=0.10, config=None (BROKEN — wrong pip):")
print(f"  Trades={result3.total_trades} | WR={result3.win_rate:.1f}% | PF={result3.profit_factor:.2f} | PnL={result3.total_pnl_pips:.1f} | {elapsed3:.1f}s")

# Original June 4th at t1=12: 5593 trades, 82.9% WR, PF=12.48
print(f"\n--- Original June 4th at t1=12.0: 5593 trades, 82.9% WR, PF=12.48 ---")
print(f"Test 1 matches: {abs(result.total_trades - 5593) < 200}")
print(f"Test 2 matches: {abs(result2.total_trades - 5593) < 200}")
