"""Quick verification of the cost fix."""
import sys
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\backtest')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\configs')
sys.path.insert(0, r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines')

from apply_costs import get_pip_value_per_lot, COST_TABLE

print("=== PIP VALUES ===")
test_cases = [
    ("EURUSD", 0.0001),
    ("USDJPY", 0.01),
    ("XAUUSD", 0.01),
    ("BTCUSD", 1.0),
    ("ETHUSD", 0.01),
    ("US500", 0.1),
    ("DE30", 0.1),
]
for sym, ps in test_cases:
    pv = get_pip_value_per_lot(sym, ps)
    print(f"  {sym} (pip_size={ps}): ${pv:.2f}/pip/lot")

print()
print("=== COMMISSION PER TRADE (lot_size=0.01, $7/lot) ===")
for sym, ps in test_cases:
    pv = get_pip_value_per_lot(sym, ps)
    comm_usd = 7.0 * 0.01
    comm_pips = comm_usd / pv
    spread = COST_TABLE.get(sym, {}).get("spread_pips", 0.5)
    total = spread + comm_pips
    print(f"  {sym}: spread={spread}p + comm={comm_pips:.4f}p = {total:.4f}p total")

print()
print("=== COMPARISON: OLD vs NEW commission ===")
print(f"  {'Asset':<10} {'Old comm':>10} {'New comm':>10} {'Ratio':>8}")
for sym, ps in test_cases:
    pv_old = ps * 100000.0 if not any(x in sym for x in ["XAU","XAG","BTC","ETH","US500","DE30","FR40","HK0"]) else get_pip_value_per_lot(sym, ps)
    pv_new = get_pip_value_per_lot(sym, ps)
    comm_old = 0.07 / (pv_old * 0.01) if pv_old > 0 else 0
    comm_new = 0.07 / pv_new if pv_new > 0 else 0
    ratio = comm_old / comm_new if comm_new > 0 else 0
    print(f"  {sym:<10} {comm_old:>10.4f} {comm_new:>10.4f} {ratio:>8.1f}x")
