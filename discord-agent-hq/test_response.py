import os, requests, time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(r'C:\Users\wifik\Desktop\projects\larger-lab\.env'), override=True)
token = os.getenv('DISCORD_BOT_TOKEN')
channel_id = os.getenv('DISCORD_CHANNEL_ID')
bot_id = '1504901841614274671'
headers = {'Authorization': 'Bot' + token, 'Content-Type': 'application/json'}

# Send test
r = requests.post(f'https://discord.com/api/v10/channels/{channel_id}/messages',
    headers=headers, json={'content': f'<@{bot_id}> ping from API test'})
print(f'Sent: {r.status_code}')

time.sleep(5)

# Check responses
r2 = requests.get(f'https://discord.com/api/v10/channels/{channel_id}/messages?limit=5', headers=headers)
for msg in r2.json():
    u = msg.get('author', {}).get('username', '?')
    c = msg.get('content', '')[:150]
    mid = msg.get('author', {}).get('id', '')
    tag = ' [BOT]' if mid == bot_id else ''
    safe_u = u.encode('ascii', 'replace').decode()
    safe_c = c.encode('ascii', 'replace').decode()
    print(f'{safe_u}{tag}: {safe_c}')
