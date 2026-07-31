"""Check messages sent by all 3 bots recently."""
import json
import time
import requests
import os
from pathlib import Path

# Load tokens
b = {}
env = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\.env")
if env.exists():
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

b["PO"] = os.environ.get("TELEGRAM_TOKEN")
b["Hermes"] = os.environ.get("HERMES_TELEGRAM_TOKEN")

oc2_cfg = Path.home() / ".openclaw-2" / "openclaw.json"
if oc2_cfg.exists():
    cfg = json.loads(oc2_cfg.read_text(encoding="utf-8"))
    b["OC2"] = cfg.get("channels", {}).get("telegram", {}).get("botToken")

print("=== Checking getUpdates for each bot (sees incoming only) ===")
for name, token in b.items():
    if not token:
        print(f"  {name}: no token")
        continue
    r = requests.get(
        f"https://api.telegram.org/bot{token}/getUpdates",
        params={"limit": 30, "timeout": 5},
        timeout=10,
    )
    data = r.json()
    pending = data.get("result", [])
    print(f"  {name}: {len(pending)} pending incoming")

# Now: check whether OC2 is currently running. If it's been up for hours
# and the user says it's still sending the same message, then it's likely
# a problem with one of the OTHER bots. Let's check process uptime.
import psutil
import datetime
print()
print("=== Process uptime ===")
for name, cmd_substr in [("Hermes", "hermes_telegram"), ("PO", "telegram_gateway"), ("OC2", "openclaw.mjs")]:
    for p in psutil.process_iter(['pid', 'create_time', 'name', 'cmdline']):
        try:
            cmd = ' '.join(p.info.get('cmdline') or [])
            if cmd_substr in cmd and 'python' in cmd.lower() or (name == "OC2" and 'node' in p.info.get('name', '').lower()):
                ct = p.info['create_time']
                uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(ct)
                print(f"  {name}: PID {p.info['pid']} uptime {uptime}")
                break
        except Exception:
            pass
