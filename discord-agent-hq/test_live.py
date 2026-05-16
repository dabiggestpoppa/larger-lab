import os, requests, json, time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(r'C:\Users\wifik\Desktop\projects\larger-lab\.env'))
token = os.getenv('DISCORD_BOT_TOKEN')
channel_id = os.getenv('DISCORD_CHANNEL_ID')
headers = {'Authorization': 'Bot ' + token}

r = requests.get('https://discord.com/api/v10/users/@me', headers=headers)
bot_id = r.json()['id']

# Send a fresh test
r2 = requests.post(f'https://discord.com/api/v10/channels/{channel_id}/messages', headers=headers,
    json={'content': f'<@{bot_id}> ping'})
print(f'Sent: {r2.status_code}')

time.sleep(5)

# Get last 10 messages
r3 = requests.get(f'https://discord.com/api/v10/channels/{channel_id}/messages?limit=10', headers=headers)
if r3.status_code == 200:
    for msg in r3.json():
        author = msg.get('author', {})
        uname = author.get('username', '?')
        mid = author.get('id', '?')
        content = msg.get('content', '')[:200]
        ts = msg.get('timestamp', '')
        safe_u = uname.encode('ascii', 'replace').decode()
        safe_c = content.encode('ascii', 'replace').decode()
        is_bot = ' [BOT]' if mid == bot_id else ''
        print(f'{safe_u}{is_bot}: {safe_c}')
        print(f'  ({ts})')
        print()
