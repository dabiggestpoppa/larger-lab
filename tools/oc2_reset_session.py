"""Reset OC2 session state to force resumption of old working session."""
import json
from pathlib import Path

sessions_file = Path(r"C:\Users\wifik\.openclaw-2\.openclaw\agents\main\sessions\sessions.json")
data = json.loads(sessions_file.read_text(encoding="utf-8"))

# Remove the stale telegram direct session that keeps creating new failing sessions
telegram_key = "agent:main:telegram:direct:8258195396"
if telegram_key in data:
    print(f"Removing stale session: {telegram_key}")
    print(f"  sessionId was: {data[telegram_key].get('sessionId', '?')[:30]}")
    del data[telegram_key]

# Also remove any subagent sessions that might be stale
keys_to_remove = [k for k in data if "subagent" in k]
for k in keys_to_remove:
    print(f"Removing subagent session: {k[:40]}")
    del data[k]

# Save
sessions_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
print(f"\nSaved sessions.json. Remaining keys: {list(data.keys())}")

# Also delete the failing session file
failing_file = Path(r"C:\Users\wifik\.openclaw-2\.openclaw\agents\main\sessions\1d7c86dc-7fe9-4b08-bba7-71a51c090bb2.jsonl")
if failing_file.exists():
    failing_file.unlink()
    print(f"Deleted failing session file: {failing_file.name}")
