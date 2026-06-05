"""Check SL distances in backtest for CHFJPY."""
import sys, json
from pathlib import Path

# Load the latest backtest report
reports = list(Path('reports').glob('NAUTILUS_SYMMETRY_TRAP_EURUSD*.json'))
if reports:
    latest = max(reports, key=lambda p: p.stat().st_mtime)
    print(f"Latest report: {latest.name}")

# Check trigger sweep data for CHFJPY
sweep_files = list(Path('reports').glob('*CHFJPY*'))
print(f"\nCHFJPY sweep files: {[f.name for f in sweep_files]}")

# Load floor/ceiling data
for f in sweep_files:
    with open(f) as fh:
        data = json.load(fh)
    print(f"\n{f.name}:")
    if isinstance(data, dict):
        for k in list(data.keys())[:5]:
            print(f"  {k}: {data[k]}")
