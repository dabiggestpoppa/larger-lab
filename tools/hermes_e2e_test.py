"""Send a test message to Hermes bot and check if it responds."""
import requests
import time

token = "8262820178:AAEIbmGIJNNqTzBxiUAAOC8rsVEJUnTq-28"
chat_id = "8258195396"  # from log

# Send a test message
print("Sending test message...")
r = requests.post(
    f"https://api.telegram.org/bot{token}/sendMessage",
    json={"chat_id": chat_id, "text": "E2E test ping from check script"},
    timeout=10,
)
print(f"  Status: {r.status_code}, ok: {r.json().get('ok')}")

# Wait for bot to process and respond
print()
print("Waiting 20s for bot to process...")
time.sleep(20)

# Check the bot's recent updates (what it sent to us)
print("Checking for bot response...")
r = requests.get(
    f"https://api.telegram.org/bot{token}/getUpdates",
    params={"limit": 10},
    timeout=5,
)
data = r.json()
if data.get("ok"):
    # Find messages from the bot (not from user)
    for u in data.get("result", []):
        msg = u.get("message") or {}
        text = msg.get("text", "")
        from_chat = msg.get("from", {}).get("id", 0)
        from_is_bot = msg.get("from", {}).get("is_bot", False)
        if from_is_bot and chat_id in str(from_chat):
            print(f"  BOT REPLY: {text[:300]}")
else:
    print(f"  Error: {data}")
