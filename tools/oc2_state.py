"""Check OC2 state for issues."""
import json
from pathlib import Path

sessions_file = Path(r"C:\Users\wifik\.openclaw-2\.openclaw\agents\main\sessions\sessions.json")
data = json.loads(sessions_file.read_text(encoding="utf-8"))

print(f"Total session keys: {len(data)}")
print()

# Find the main session
main_key = "agent:main:main"
if main_key in data:
    main = data[main_key]
    print(f"=== Main session ===")
    print(f"  sessionId: {main.get('sessionId', '?')[:30]}")
    print(f"  model: {main.get('model', '?')}")
    print(f"  modelProvider: {main.get('modelProvider', '?')}")
    print(f"  abortedLastRun: {main.get('abortedLastRun', '?')}")
    print(f"  compactionCount: {main.get('compactionCount', '?')}")
    print(f"  systemSent: {main.get('systemSent', '?')}")
    print(f"  chatType: {main.get('chatType', '?')}")
    print(f"  origin: {str(main.get('origin', {}))[:200]}")
    print(f"  usageFamilyKey: {main.get('usageFamilyKey', '?')}")
    print(f"  usageFamilySessionIds: {main.get('usageFamilySessionIds', [])}")
else:
    print("No main session found")

# Check for telegram direct session
telegram_key = "agent:main:telegram:direct:8258195396"
if telegram_key in data:
    tg = data[telegram_key]
    print(f"\n=== Telegram direct session ===")
    print(f"  sessionId: {tg.get('sessionId', '?')[:30]}")
    print(f"  model: {tg.get('model', '?')}")
    print(f"  modelProvider: {tg.get('modelProvider', '?')}")
    print(f"  abortedLastRun: {tg.get('abortedLastRun', '?')}")
    print(f"  systemSent: {tg.get('systemSent', '?')}")
