"""Fix OC2 session state - ensure new sessions get the model config."""
import json
from pathlib import Path

sessions_file = Path(r"C:\Users\wifik\.openclaw-2\.openclaw\agents\main\sessions\sessions.json")
data = json.loads(sessions_file.read_text(encoding="utf-8"))

# Find the telegram direct session and ensure it has the model
telegram_key = "agent:main:telegram:direct:8258195396"
if telegram_key in data:
    tg = data[telegram_key]
    print(f"Before fix:")
    print(f"  sessionId: {tg.get('sessionId', '?')[:30]}")
    print(f"  model: {tg.get('model', 'NOT SET')}")
    print(f"  modelProvider: {tg.get('modelProvider', 'NOT SET')}")

    # Set the model from defaults
    if not tg.get("model"):
        tg["model"] = "inclusionai/ring-2.6-1t"
        tg["modelProvider"] = "openrouter"
        print(f"\nFixed: set model to inclusionai/ring-2.6-1t")

    # Save
    sessions_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Saved sessions.json")
else:
    print("Telegram direct session not found")
