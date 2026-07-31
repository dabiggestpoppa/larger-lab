"""Check OC2 / OpenClaw Telegram bot via getMe API."""
import os
import json
import requests
from pathlib import Path

cfg_path = Path.home() / ".openclaw-2" / "openclaw.json"
print(f"Reading {cfg_path}")
if not cfg_path.exists():
    print(f"  [FAIL] Config not found")
    raise SystemExit(1)

cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
print(f"Config keys: {list(cfg.keys())[:15]}")

# Try common token keys
for key in ("telegram_token", "bot_token", "token", "TELEGRAM_BOT_TOKEN"):
    if key in cfg:
        token = cfg[key]
        print(f"Found token via key '{key}': {token[:10]}...")
        try:
            r = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5)
            data = r.json()
            if data.get("ok"):
                u = data["result"]["username"]
                i = data["result"]["id"]
                print(f"  [OK]   OC2: @{u}  (id={i})")
            else:
                print(f"  [ERR]  OC2: {data}")
        except Exception as e:
            print(f"  [FAIL] OC2: {e}")
        break
else:
    print("  [WARN] No telegram token key found in config")
    # Print first 20 keys for debug
    print(f"Available keys: {list(cfg.keys())}")
