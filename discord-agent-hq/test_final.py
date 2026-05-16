import os, requests, time, json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(r'C:\Users\wifik\Desktop\projects\larger-lab\.env'))
token = os.getenv('DISCORD_BOT_TOKEN')
channel_id = os.getenv('DISCORD_CHANNEL_ID')
bot_id = '1504901841614274671'
headers = {'Authorization': 'Bot ' + token, 'Content-Type': 'application/json'}

# Clear old test messages first - just send a marker
print("Sending mention test...")
r = requests.post(f'https://discord.com/api/v10/channels/{channel_id}/messages',
    headers=headers, json={'content': f'<@{bot_id}> ping'})
print(f"Sent: {r.status_code}")

time.sleep(4)

r2 = requests.get(f'https://discord.com/api/v10/channels/{channel_id}/messages?limit=5', headers=headers)
msgs = r2.json()
print("\nLast 5 messages:")
for msg in msgs[:5]:
    u = msg.get('author', {}).get('username', '?')
    c = msg.get('content', '')[:150]
    mid = msg.get('id', '')
    safe_u = u.encode('ascii', 'replace').decode()
    safe_c = c.encode('ascii', 'replace').decode()
    tag = ' [BOT]' if msg.get('author', {}).get('id') == bot_id else ''
    print(f"  {safe_u}{tag}: {safe_c}")
