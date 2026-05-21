"""Reset DMR state — clear false positive P90s, keep trade history"""
import json
from pathlib import Path
from datetime import datetime, timezone

state_file = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live_state.json")
with open(state_file) as f:
    state = json.load(f)

today = datetime.now(timezone.utc).date().isoformat()
state['today'] = today

for sym in state.get('symbols', {}):
    old = state['symbols'][sym].get('p90_count', 0)
    state['symbols'][sym]['known_p90s'] = []
    state['symbols'][sym]['p90_count'] = 0
    state['symbols'][sym]['last_p90_time'] = None
    print(f"Cleared {sym}: {old} -> 0 P90s")

with open(state_file, 'w') as f:
    json.dump(state, f, indent=2, default=str)
print("State reset.")
