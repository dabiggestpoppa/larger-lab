import json
from pathlib import Path

state_file = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live_state.json")

with open(state_file) as f:
    state = json.load(f)

# Reset known_p90s for all symbols — they were false positives without Asian range filter
for sym in state.get('symbols', {}):
    state['symbols'][sym]['known_p90s'] = []
    state['symbols'][sym]['p90_count'] = 0
    state['symbols'][sym]['last_p90_time'] = None
    print(f"Reset {sym}: cleared {state['symbols'][sym].get('p90_count', 0)} false P90s")

with open(state_file, 'w') as f:
    json.dump(state, f, indent=2, default=str)

print("State reset complete")
