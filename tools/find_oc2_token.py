"""Find OC2 telegram token in nested config."""
import os
import json
import requests
from pathlib import Path

cfg_path = Path.home() / ".openclaw-2" / "openclaw.json"
cfg = json.loads(cfg_path.read_text(encoding="utf-8"))

def walk(obj, path=""):
    """Yield (path, value) for every leaf in nested dict/list."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from walk(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from walk(v, f"{path}[{i}]")
    else:
        yield path, obj

# Look for telegram-related tokens
print("=== Looking for telegram tokens ===")
for path, val in walk(cfg):
    pl = path.lower()
    if "telegram" in pl and ("token" in pl or "bot" in pl):
        s = str(val)
        print(f"  {path}: {s[:30]}{'...' if len(s) > 30 else ''}")

# Also try to find any string that looks like a bot token
print("\n=== Looking for bot token patterns ===")
for path, val in walk(cfg):
    s = str(val)
    if ":" in s and len(s) > 30 and s.split(":")[0].isdigit():
        # Looks like a bot token
        print(f"  {path}: {s[:20]}...")
        try:
            r = requests.get(f"https://api.telegram.org/bot{s}/getMe", timeout=5)
            data = r.json()
            if data.get("ok"):
                u = data["result"]["username"]
                i = data["result"]["id"]
                print(f"    [OK] Telegram bot: @{u}  (id={i})")
        except Exception as e:
            pass
