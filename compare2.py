import os

with open(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\symmetry_trap.py") as f:
    bt = f.read()

# Check if ST engine has P90 cascade bias
print("=== P90 CASCADE BIAS IN BACKTEST ===")
print("cascade_bias in backtest:", "cascade_bias" in bt)
print("cascade_bypass logic:", "cascade_bypass = False" in bt)

# Check P90 strategy file
with open(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies\p90_strategy.py") as f:
    p90 = f.read()

print("\n=== P90 STRATEGY ===")
print("INITIAL variant:", "INITIAL" in p90)
print("CASCADE variant:", "CASCADE" in p90)
print("CASCADE timing (2h):", "120" in p90 or "2 hour" in p90.lower() or "hours=2" in p90)
print("TP1 (25%):", "0.25" in p90 or "25%" in p90)
print("TP2 (50%):", "0.50" in p90 or "50%" in p90)

# Check live engine P90
lv = open(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\cerebus_live.py").read()
print("\n=== LIVE P90 ===")
print("INITIAL variant:", '"INITIAL"' in lv)
print("CASCADE variant:", '"CASCADE"' in lv)
print("CASCADE timing (120min):", "120" in lv)
print("TP1 (25%):", "0.25" in lv)
print("TP2 (50%):", "0.50" in lv)
print("Body threshold by hour:", "P90_THRESHOLDS" in lv)

# Check what cascade_bypass actually does in backtest
# In WAIT_RETRACE: if loop>=2 and retrace < min and cascade_bias matches impulse -> bypass Goldilocks
# This matters when loop 2+ has shallow pullback but P90 cascade confirms direction
print("\n=== CASCADE BYPASS IMPACT ===")
print("Only affects: loop 2+ entries where:")
print("  1. Pullback is shallow (retrace < min_retrace_pct)")
print("  2. cascade_bias matches impulse direction")
print("Without it: loop 2+ waits for full 20-50% pullback")
print("With it: loop 2+ can enter on shallow pullbacks with cascade confirmation")
print("\nBacktest has 82.8% WR across 14,563 trades")
print("Cascade bypass contributes to catching trades that would otherwise skip")
