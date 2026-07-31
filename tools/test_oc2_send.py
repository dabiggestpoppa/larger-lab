"""Test OC2 bot end-to-end."""
import json
import time
import requests

# Load OC2 token
with open(r"C:\Users\wifik\.openclaw-2\openclaw.json", encoding="utf-8") as f:
    cfg = json.load(f)
token = cfg["channels"]["telegram"]["botToken"]
chat_id = "8258195396"

print(f"OC2 token prefix: {token[:15]}...")
print()

# Send a test message
print("=== Sending test message to OC2 ===")
r = requests.post(
    f"https://api.telegram.org/bot{token}/sendMessage",
    json={"chat_id": chat_id, "text": "OC2 test ping"},
    timeout=10,
)
print(f"  Status: {r.status_code}, ok: {r.json().get('ok')}")

# Wait 35s for long-poll to pick it up
print()
print("Waiting 35s for OC2 long-poll to pick up...")
time.sleep(35)

# Check pending updates (would show if OC2 didn't acknowledge)
print()
print("=== Checking getUpdates for OC2 (should be empty if OC2 acked) ===")
r = requests.get(
    f"https://api.telegram.org/bot{token}/getUpdates",
    params={"limit": 5, "timeout": 5},
    timeout=10,
)
data = r.json()
print(f"  ok: {data.get('ok')}, pending: {len(data.get('result', []))}")
for u in data.get("result", []):
    msg = u.get("message") or {}
    text = msg.get("text", "")
    update_id = u.get("update_id")
    print(f"    update_id={update_id} text={text[:50]!r}")
