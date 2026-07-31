"""Check ALL Telegram bot statuses via getMe API.

Includes:
- PO Bot (.env TELEGRAM_TOKEN)
- Hermes Bot (.env HERMES_TELEGRAM_TOKEN)
- OC2 / OpenClaw Bot (~/.openclaw-2/openclaw.json)
"""
import os
import json
import requests
from pathlib import Path


def check_bot(name: str, token: str) -> None:
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{token}/getMe", timeout=5
        )
        data = r.json()
        if data.get("ok"):
            u = data["result"]["username"]
            i = data["result"]["id"]
            print(f"  [OK]   {name:<10} @{u:<20}  (id={i})")
        else:
            print(f"  [ERR]  {name:<10} {data}")
    except Exception as e:
        print(f"  [FAIL] {name:<10} {e}")


# PO Bot — from .env
env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

po_token = os.environ.get("TELEGRAM_TOKEN")
hermes_token = os.environ.get("HERMES_TELEGRAM_TOKEN")

# OC2 — from nested openclaw config
oc2_token = None
oc2_cfg = Path.home() / ".openclaw-2" / "openclaw.json"
if oc2_cfg.exists():
    try:
        cfg = json.loads(oc2_cfg.read_text(encoding="utf-8"))
        # Walk and find channels.telegram.botToken
        tg = cfg.get("channels", {}).get("telegram", {})
        if isinstance(tg, dict):
            oc2_token = tg.get("botToken") or tg.get("token") or tg.get("bot_token")
    except Exception as e:
        print(f"  [WARN] Could not read {oc2_cfg}: {e}")

print("=== Telegram Bot Status ===")
if po_token:
    check_bot("PO Bot", po_token)
else:
    print("  [SKIP] PO Bot — no TELEGRAM_TOKEN in .env")

if hermes_token:
    check_bot("Hermes", hermes_token)
else:
    print("  [SKIP] Hermes — no HERMES_TELEGRAM_TOKEN in .env")

if oc2_token:
    check_bot("OC2", oc2_token)
else:
    print("  [SKIP] OC2 — no channels.telegram.botToken in ~/.openclaw-2/openclaw.json")
