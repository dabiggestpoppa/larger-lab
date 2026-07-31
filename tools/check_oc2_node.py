"""Check OC2 node process and what it's been sending."""
import json
import time
import requests
import psutil

# Find OC2 process
print("=== OC2 processes ===")
for p in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
    try:
        cmd = ' '.join(p.info.get('cmdline') or [])
        if 'openclaw.mjs' in cmd:
            print(f"PID {p.info['pid']} {p.info['name']} create_t={p.info['create_time']:.2f}")
            print(f"  cmd: {cmd[:200]}")
            try:
                ppid = p.info.get('ppid') or 0
                parent = psutil.Process(ppid) if ppid else None
                if parent:
                    print(f"  parent: PID {parent.pid} {parent.name()}")
                    print(f"  parent cmd: {' '.join(parent.cmdline() or [])[:150]}")
            except Exception as e:
                print(f"  parent lookup failed: {e}")
    except Exception:
        pass

# Get all messages TO the user (bot's outgoing)
print()
print("=== Messages FROM OC2 to user (last 20) ===")
with open(r"C:\Users\wifik\.openclaw-2\openclaw.json", encoding="utf-8") as f:
    cfg = json.load(f)
token = cfg["channels"]["telegram"]["botToken"]
chat_id = "8258195396"

# Get recent updates
r = requests.get(
    f"https://api.telegram.org/bot{token}/getUpdates",
    params={"limit": 30, "timeout": 5},
    timeout=10,
)
data = r.json()
print(f"ok={data.get('ok')}, total={len(data.get('result', []))}")
for u in data.get("result", []):
    msg = u.get("message") or {}
    text = msg.get("text", "")
    from_id = msg.get("from", {}).get("id", 0)
    is_bot = msg.get("from", {}).get("is_bot", False)
    update_id = u.get("update_id")
    sender = "BOT" if is_bot else "USER"
    print(f"  [{sender}] update_id={update_id} text={text[:100]!r}")
