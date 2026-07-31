import json, requests
with open(r"C:\Users\wifik\.openclaw-2\openclaw.json", encoding="utf-8") as f:
    cfg = json.load(f)
token = cfg["channels"]["telegram"]["botToken"]
r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", params={"limit": 50, "timeout": 5}, timeout=10)
data = r.json()
print(f"Total pending: {len(data.get('result', []))}")
for u in data.get("result", []):
    msg = u.get("message") or {}
    text = msg.get("text", "")
    is_bot = msg.get("from", {}).get("is_bot", False)
    sender = "BOT" if is_bot else "USER"
    print(f"  [{sender}] {text[:100]!r}")
