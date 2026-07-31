import requests
r = requests.get(
    "https://api.telegram.org/bot8262820178:AAEIbmGIJNNqTzBxiUAAOC8rsVEJUnTq-28/getUpdates",
    params={"limit": 10, "timeout": 5},
    timeout=10,
)
data = r.json()
print("Pending updates:", len(data.get("result", [])))
for u in data.get("result", []):
    msg = u.get("message") or {}
    print(f"  update_id={u['update_id']} text={msg.get('text')!r}")
