"""Run EURUSD backtest using OLD engine from git commit 21eed3e05 (5/30/2026).
This script creates a TEMPORARY copy of the old engine, runs the test, then deletes it.
NO files in the real engine directory are touched."""
import subprocess
import sys
import os
import tempfile
import shutil
from pathlib import Path

REPO_ROOT = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
QUANT_LAB = REPO_ROOT / "quant-lab"
DATA_DIR = QUANT_LAB / "data"

# Step 1: Extract old engine from git into a temp directory
tmpdir = Path(tempfile.mkdtemp(prefix="old_engine_"))
old_engine_src = tmpdir / "symmetry_trap.py"

result = subprocess.run(
    ["git", "show", "21eed3e05:quant-lab/engines/symmetry_trap.py"],
    capture_output=True, text=True, cwd=str(REPO_ROOT)
)
if result.returncode != 0:
    print(f"Git error: {result.stderr}")
    sys.exit(1)

old_engine_src.write_text(result.stdout, encoding="utf-8")
print(f"Old engine extracted to temp: {old_engine_src}")

# Step 2: Read backtest source and create a standalone runner
bt_src = QUANT_LAB / "engines" / "symmetry_trap_backtest.py"
bt_code = bt_src.read_text(encoding="utf-8")

# Step 3: Create a standalone script in the temp directory that uses old engine but current backtest
runner = tmpdir / "run_test.py"
runner_code = f'''
import sys, os
sys.path.insert(0, r"{tmpdir}")
sys.path.insert(0, r"{QUANT_LAB / 'engines'}")
sys.path.insert(0, r"{QUANT_LAB / 'configs'}")

# Import OLD engine (has 'from' syntax issue? Let's check)
import symmetry_trap as st_old
from symmetry_trap_backtest import SymmetryTrapBacktest

from pathlib import Path
from configs.asset_configs import ASSET_CONFIGS

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

csv_path = Path(r"{DATA_DIR / 'EURUSD_M5.csv'}")
result = bt.run_from_csv(str(csv_path))

print(f"EURUSD OLD engine: trades={{result.total_trades}}, wr={{result.win_rate:.1f}}%, pnl={{result.total_pnl_pips:+.1f}}p, pf={{result.profit_factor:.2f}}")
print(f"  Long: {{result.long_trades}} tr, {{result.long_wr:.1f}}%")
print(f"  Short: {{result.short_trades}} tr, {{result.short_wr:.1f}}%")

from collections import Counter
exits = Counter(t.result for t in result.trades)
for et, cnt in exits.most_common():
    print(f"  {{et}}: {{cnt}} ({{cnt/result.total_trades*100:.1f}}%)")
'''
runner.write_text(runner_code, encoding="utf-8")

# Step 4: Run it
print("\n=== Running EURUSD with OLD engine (5/30) ===\n")
proc = subprocess.run(
    [sys.executable, str(runner)],
    capture_output=True, text=True, timeout=120,
    cwd=str(tmpdir),
    env={**os.environ, "PYTHONPATH": f"{tmpdir};{QUANT_LAB / 'engines'};{QUANT_LAB / 'configs'}"}
)
print(proc.stdout)
if proc.stderr:
    print("STDERR:", proc.stderr[:500])
print(f"Return code: {proc.returncode}")

# Step 5: Cleanup
shutil.rmtree(tmpdir, ignore_errors=True)
print(f"\nCleaned up temp dir: {tmpdir}")
print("NO engine files were modified.")
