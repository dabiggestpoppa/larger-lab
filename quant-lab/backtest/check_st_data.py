import json
from pathlib import Path

REPORTS = Path(__file__).parent.parent / "reports" / "per-asset"

for sym in ["EURUSD", "USDCHF", "NZDUSD"]:
    p = REPORTS / f"{sym}_mc_results.json"
    if not p.exists():
        print(f"{sym}: MISSING")
        continue
    d = json.loads(p.read_text())
    keys = list(d.keys())
    print(f"{sym}: keys={keys[:8]}")
    print(f"  has per_trade_pnl: {'per_trade_pnl' in d}")
    print(f"  has backtest: {'backtest' in d}")
    print(f"  has n_iterations: {'n_iterations' in d}")
    # Check for any list that could be trade data
    for k, v in d.items():
        if isinstance(v, list) and len(v) > 0:
            print(f"  list key '{k}': len={len(v)}, sample={v[:3]}")
    print()
