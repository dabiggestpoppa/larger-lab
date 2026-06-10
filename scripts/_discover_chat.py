import os, requests, json
from pathlib import Path

env = Path(__file__).resolve().parent.parent / ".env"
if env.exists():
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

token = os.environ.get("HERMES_TELEGRAM_TOKEN", "")
if not token:
    print("No token")
    exit(1)

r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates?limit=5&timeout=10")
data = r.json()
print("ok:", data.get("ok"))
if data.get("result"):
    for u in data["result"]:
        msg = u.get("message", {})
        chat = msg.get("chat", {})
        print(f"chat_id: {chat.get('id')} user: {chat.get('username')} text: {msg.get('text','')[:50]}")
else:
    print("No updates - message the bot first")
