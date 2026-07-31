"""Check Telegram bot status via getMe API."""
import requests

bots = [
    ("Hermes", "8262820178:AAEIbmGIJNNqTzBxiUAAOC8rsVEJUnTq-28"),
    ("PO Bot",  "8951584547:AAEzC-suY_uS9bOvD9kAfhpnwHVw8hvbs9I"),
]
for name, token in bots:
    try:
        r = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5)
        data = r.json()
        if data.get("ok"):
            u = data["result"]["username"]
            i = data["result"]["id"]
            print(f"  [OK]   {name}: @{u}  (id={i})")
        else:
            print(f"  [ERR]  {name}: {data}")
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")
