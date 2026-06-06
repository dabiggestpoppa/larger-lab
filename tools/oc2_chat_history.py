"""Get full chat history for OC2 bot to see what it's sending."""
import json
import requests

with open(r"C:\Users\wifik\.openclaw-2\openclaw.json", encoding="utf-8") as f:
    cfg = json.load(f)
token = cfg["channels"]["telegram"]["botToken"]

# Get updates with a long timeout to see all messages
r = requests.get(
    f"https://api.telegram.org/bot{token}/getUpdates",
    params={"limit": 50, "timeout": 0},
    timeout=10,
)
data = r.json()
updates = data.get("result", [])
print(f"Total updates: {len(updates)}")
for u in updates:
    msg = u.get("message") or {}
    text = msg.get("text", "")
    from_info = msg.get("from", {})
    is_bot = from_info.get("is_bot", False)
    sender = "BOT" if is_bot else "USER"
    chat_id = msg.get("chat", {}).get("id", 0)
    date = msg.get("date", 0)
    print(f"  [{sender}] chat={chat_id} text={text[:120]!r}")
