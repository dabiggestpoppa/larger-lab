"""Send test ping to Hermes bot."""
import requests
import json

token = "8262820178:AAEIbmGIJNNqTzBxiUAAOC8rsVEJUnTq-28"
# Get the most recent chat
r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=5, params={"limit": 5})
data = r.json()
if data.get("result"):
    chat_id = data["result"][-1].get("message", {}).get("chat", {}).get("id")
    print(f"Most recent chat: {chat_id}")
    r2 = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": "Hermes bot restarted with send-fix. Ready for new messages."},
        timeout=10,
    )
    ok = r2.json().get("ok")
    print(f"Send status: {r2.status_code}, ok={ok}")
else:
    print("No recent messages")
