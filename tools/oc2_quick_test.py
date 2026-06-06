import json, requests, time
with open(r"C:\Users\wifik\.openclaw-2\openclaw.json", encoding="utf-8") as f:
    cfg = json.load(f)
token = cfg["channels"]["telegram"]["botToken"]
r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
    json={"chat_id": "8258195396", "text": "OC2 quick test"}, timeout=10)
print("Sent:", r.json().get("ok"))
time.sleep(50)
r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates",
    params={"limit": 5, "timeout": 5}, timeout=10)
data = r.json()
pending = len(data.get("result", []))
print(f"Pending after 50s: {pending}")
