import json
from datetime import datetime, timezone

state_file = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live_state.json"
with open(state_file) as f:
    state = json.load(f)

today = datetime.now(timezone.utc).date().isoformat()
state['today'] = today

for sym in state.get('symbols', {}):
    state['symbols'][sym]['known_p90s'] = []
    state['symbols'][sym]['p90_count'] = 0
    state['symbols'][sym]['last_p90_time'] = None
    state['symbols'][sym]['active_trade'] = False
    state['symbols'][sym]['current_ticket'] = None
    print("Reset " + sym)

with open(state_file, 'w') as f:
    json.dump(state, f, indent=2, default=str)
print("State reset OK")
