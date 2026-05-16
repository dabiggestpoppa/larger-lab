import os, requests, time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(r'C:\Users\wifik\Desktop\projects\larger-lab\.env'), override=True)
token = os.getenv('TELEGRAM_HERMES_TOKEN')
headers = {'Content-Type': 'application/json'}

# Send test message as if from MAD
chat_id = '8258195396'
r = requests.post(f'https://api.telegram.org/bot{token}/sendMessage',
    headers=headers, json={'chat_id': chat_id, 'text': 'HERMES ARE YOU READY TO BUILD?'})
print(f'Sent: {r.status_code}')
print(r.text[:200])
