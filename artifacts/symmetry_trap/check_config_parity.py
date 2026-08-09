import json
import sys
import os

# Add both engines and quant-lab root to path
quant_lab = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "quant-lab")
sys.path.insert(0, os.path.join(quant_lab, "engines"))
sys.path.insert(0, quant_lab)

from symmetry_trap_backtest import SymmetryTrapBacktest
from symmetry_trap_live import SymmetryTrapLiveEngine
from symmetry_trap import SymmetryTrapEngine

# Test config (same as parity replay)
test_config = {
    "pip_value": 0.0001,
    "est_offset": -5,
    "entry_window_start": 2,
    "entry_window_end": 11,
    "hard_exit_hour": 17,
    "lot_size": 0.01,
    "name": "EURUSD",
    "tiers": {
        "T1": {"ar_max": 60.0, "au": 10.0, "trigger": 12.0},
        "T2": {"ar_max": 60.0, "au": 12.0, "trigger": 15.0},
        "T3": {"ar_max": 60.0, "au": 15.0, "trigger": 19.0},
    },
}

# Canonical backtest engine
bt = SymmetryTrapBacktest(config=test_config)
bt_engine = SymmetryTrapEngine(
    pip_size=bt.pip_size,
    tier_config=bt.tier_config,
    symbol=bt.symbol,
    config=bt.config,
)

# Live engine with config override
live = SymmetryTrapLiveEngine("EURUSD", config_override=test_config)

# Compare all config values
diff = {
    "canonical": {
        "pip_size": bt_engine.pip_size,
        "tier_config": bt_engine.tier_config,
        "symbol": bt_engine.symbol,
        "min_sl_buffer": bt_engine.min_sl_buffer,
        "spread_buffer": bt_engine.spread_buffer,
        "max_loops": bt_engine.max_loops,
    },
    "live": {
        "pip_size": live.engine.pip_size,
        "tier_config": live.engine.tier_config,
        "symbol": live.engine.symbol,
        "min_sl_buffer": live.engine.min_sl_buffer,
        "spread_buffer": live.engine.spread_buffer,
        "max_loops": live.engine.max_loops,
    },
}

# Find differences
diffs = []
for key in diff["canonical"]:
    if diff["canonical"][key] != diff["live"][key]:
        diffs.append({
            "field": key,
            "canonical": str(diff["canonical"][key]),
            "live": str(diff["live"][key]),
        })

result = {
    "diff_count": len(diffs),
    "diffs": diffs,
    "canonical_config": diff["canonical"],
    "live_config": diff["live"],
    "parity": len(diffs) == 0,
}

output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config_parity.json")
with open(output_path, 'w') as f:
    json.dump(result, f, indent=2, default=str)

print(f"Config parity: {len(diffs)} differences")
print(f"Parity achieved: {len(diffs) == 0}")
if diffs:
    print("Differences:")
    for d in diffs:
        print(f"  {d['field']}: canonical={d['canonical']}, live={d['live']}")
print(f"Written to: {output_path}")