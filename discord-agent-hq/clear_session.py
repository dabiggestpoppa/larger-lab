import os, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(r'C:\Users\wifik\Desktop\projects\larger-lab\.env'), override=True)
token = os.getenv('TELEGRAM_HERMES_TOKEN')

# Delete webhook (clears any existing session)
r = requests.post(f'https://api.telegram.org/bot{token}/deleteWebhook', json={'drop_pending_updates': True})
print(f"deleteWebhook: {r.status_code} - {r.text[:200]}")

# Also try getUpdates with timeout=0 to clear
r2 = requests.post(f'https://api.telegram.org/bot{token}/getUpdates', json={'timeout': 0, 'offset': -1})
print(f"getUpdates: {r2.status_code} - {r2.text[:200]}")
