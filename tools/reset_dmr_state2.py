import json
from pathlib import Path
from datetime import datetime, timezone

state_file = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live_state.json")

with open(state_file) as f:
    state = json.load(f)

today = datetime.now(timezone.utc).date().isoformat()
state['today'] = today

# Reset ALL symbols — clear false positive P90s
for sym in state.get('symbols', {}):
    old_count = state['symbols'][sym].get('p90_count', 0)
    state['symbols'][sym]['known_p90s'] = []
    state['symbols'][sym]['p90_count'] = 0
    state['symbols'][sym]['last_p90_time'] = None
    # Keep trade state if there's an active position
    print(f"Reset {sym}: cleared {old_count} P90s (active_trade={state['symbols'][sym].get('active_trade')}, ticket={state['symbols'][sym].get('current_ticket')})")

with open(state_file, 'w') as f:
    json.dump(state, f, indent=2, default=str)

print("\nState reset complete — P90s will be re-detected with Asian range filter")
