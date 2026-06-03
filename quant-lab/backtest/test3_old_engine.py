"""Test 3: Run EURUSD with OLD engine (git checkout of 5/30 version)."""
import subprocess
import sys
import shutil
from pathlib import Path

engine_path = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\symmetry_trap.py")
backup_path = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\symmetry_trap.py.bak")
old_version_path = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\symmetry_trap_old.py")

# Step 1: Backup current engine
shutil.copy2(engine_path, backup_path)
print(f"Backed up current engine to {backup_path}")

# Step 2: Get old version from git
result = subprocess.run(
    ["git", "show", "21eed3e05:quant-lab/engines/symmetry_trap.py"],
    capture_output=True, text=True, cwd=r"C:\Users\wifik\Desktop\projects\larger-lab"
)
if result.returncode != 0:
    print(f"Git error: {result.stderr}")
    sys.exit(1)

old_version_path.write_text(result.stdout)
print(f"Old engine written to {old_version_path}")

# Step 3: Replace current with old
shutil.copy2(old_version_path, engine_path)
print(f"Replaced engine with old version")

# Step 4: Clear __pycache__
import os
pycache = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\__pycache__")
for f in pycache.glob("symmetry_trap*"):
    f.unlink()
    print(f"Removed {f.name}")

# Step 5: Run backtest
print("\n=== Running EURUSD with OLD engine (5/30 version) ===\n")

# Need to reimport
import importlib
import symmetry_trap
importlib.reload(symmetry_trap)
import symmetry_trap_backtest
importlib.reload(symmetry_trap_backtest)

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest

asset_key = "EURUSD"
config = ASSET_CONFIGS[asset_key]
pip_size = config["pip_value"]
tier_config = config["tiers"]

bt = SymmetryTrapBacktest(
    pip_size=pip_size,
    tier_config=tier_config,
    symbol=asset_key,
    config=config,
)

csv_path = Path(__file__).parent.parent / "data" / f"{asset_key}_M5.csv"
result = bt.run_from_csv(str(csv_path))

print(f"EURUSD (OLD engine):")
print(f"  Trades: {result.total_trades} | WR: {result.win_rate:.1f}% | PnL: {result.total_pnl_pips:+.1f}p | PF: {result.profit_factor:.2f}")
print(f"  Long: {result.long_trades} tr, {result.long_wr:.1f}% WR, {result.long_pnl:+.1f}p")
print(f"  Short: {result.short_trades} tr, {result.short_wr:.1f}% WR, {result.short_pnl:+.1f}p")

from collections import Counter
exits = Counter(t.result for t in result.trades)
for et, cnt in exits.most_common():
    print(f"  {et}: {cnt} ({cnt/result.total_trades*100:.1f}%)")

# Step 6: Restore current engine
shutil.copy2(backup_path, engine_path)
print(f"\nRestored current engine from backup")

# Clear cache again
for f in pycache.glob("symmetry_trap*"):
    f.unlink()
print("Cleared __pycache__")
