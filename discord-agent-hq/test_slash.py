"""Test slash command interaction directly."""
import os, requests, json
from pathlib import Path
from dotenv import load_dotenv
import time

load_dotenv(Path(r'C:\Users\wifik\Desktop\projects\larger-lab\.env'))
token = os.getenv('DISCORD_BOT_TOKEN')
app_id = os.getenv('DISCORD_APPLICATION_ID')
channel_id = os.getenv('DISCORD_CHANNEL_ID')
guild_id = os.getenv('DISCORD_GUILD_ID')
headers = {'Authorization': 'Bot ' + token, 'Content-Type': 'application/json'}

# Get command ID
r = requests.get(f'https://discord.com/api/v10/applications/{app_id}/guilds/{guild_id}/commands', headers=headers)
cmds = r.json()
openclaw_id = None
for cmd in cmds:
    if cmd['name'] == 'openclaw':
        openclaw_id = cmd['id']
        break

print(f"OpenClaw command ID: {openclaw_id}")

# Simulate an interaction
interaction_data = {
    "type": 2,  # APPLICATION_COMMAND
    "application_id": app_id,
    "guild_id": guild_id,
    "channel_id": channel_id,
    "data": {
        "id": openclaw_id,
        "name": "openclaw",
        "type": 1,
        "options": [{
            "type": 3,
            "name": "message",
            "value": "status"
        }]
    },
    "user": {
        "id": "123456",
        "username": "test"
    }
}

# We can't actually trigger interactions via REST API — they need Discord's gateway
# Instead let's just verify the bot is responding to messages
print("\nBot should be running. Testing @mention...")

# Send a test message with @mention
r2 = requests.get('https://discord.com/api/v10/users/@me', headers=headers)
bot_id = r2.json()['id']

r3 = requests.post(f'https://discord.com/api/v10/channels/{channel_id}/messages', headers=headers, json={
    'content': f'<@{bot_id}> openclaw status'
})
print(f"Sent test message: {r3.status_code}")

time.sleep(3)

# Check for response
r4 = requests.get(f'https://discord.com/api/v10/channels/{channel_id}/messages?limit=5', headers=headers)
if r4.status_code == 200:
    for msg in r4.json():
        author = msg.get('author', {})
        print(f"  {author.get('username', '?')}: {msg.get('content', '')[:150]}")
