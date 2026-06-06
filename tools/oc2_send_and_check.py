"""Send message to OC2 and check response."""
import json
import time
import requests

with open(r"C:\Users\wifik\.openclaw-2\openclaw.json", encoding="utf-8") as f:
    cfg = json.load(f)
token = cfg["channels"]["telegram"]["botToken"]

# Send test message
r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
    json={"chat_id": "8258195396", "text": "OC2 test after fix"}, timeout=10)
print(f"Sent: {r.json().get('ok')}")

# Wait 60s for OC2 to process
print("Waiting 60s...")
time.sleep(60)

# Check pending
r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates",
    params={"limit": 10, "timeout": 5}, timeout=10)
data = r.json()
pending = len(data.get("result", []))
print(f"Pending after 60s: {pending}")

# Check for bot replies
for u in data.get("result", []):
    msg = u.get("message") or {}
    is_bot = msg.get("from", {}).get("is_bot", False)
    text = msg.get("text", "")
    if is_bot:
        print(f"  BOT REPLY: {text[:200]!r}")
    else:
        print(f"  USER: {text[:100]!r}")

# Also check session files
from pathlib import Path
sessions_dir = Path(r"C:\Users\wifik\.openclaw-2\.openclaw\agents\main\sessions")
files = sorted(sessions_dir.glob("*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)
print(f"\nLatest session files:")
for f in files[:3]:
    lines = f.read_text(encoding="utf-8").strip().splitlines()
    print(f"  {f.name[:20]}... lines={len(lines)} mtime={f.stat().st_mtime}")
