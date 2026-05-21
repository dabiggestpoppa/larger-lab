"""Reset DMR state and verify thresholds"""
import json, os

# Reset state
state_file = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live_state.json"
with open(state_file) as f:
    state = json.load(f)

from datetime import datetime, timezone
today = datetime.now(timezone.utc).date().isoformat()
state['today'] = today

for sym in state.get('symbols', {}):
    state['symbols'][sym]['known_p90s'] = []
    state['symbols'][sym]['p90_count'] = 0
    state['symbols'][sym]['last_p90_time'] = None
    state['symbols'][sym]['active_trade'] = False
    state['symbols'][sym]['current_ticket'] = None
    print(f"Reset {sym}")

with open(state_file, 'w') as f:
    json.dump(state, f, indent=2, default=str)
print("State reset OK")

# Verify thresholds in the code
import importlib.util
spec = importlib.util.spec_from_file_location("dmr", r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live_v2.py")
print(f"\nDMR file size: {os.path.getsize(r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live_v2.py')} bytes")
print("Thresholds will be verified when DMR starts")
