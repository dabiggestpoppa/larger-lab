"""Manually register slash commands via Discord API."""
import os, requests, json
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(r'C:\Users\wifik\Desktop\projects\larger-lab\.env'))
token = os.getenv('DISCORD_BOT_TOKEN')
app_id = os.getenv('DISCORD_APPLICATION_ID')
guild_id = os.getenv('DISCORD_GUILD_ID')
headers = {'Authorization': 'Bot ' + token, 'Content-Type': 'application/json'}

commands = [
    {
        "name": "hermes",
        "description": "Switch to Hermes (Architect & Planner) and get a response",
        "type": 1,
        "options": [{
            "type": 3,
            "name": "message",
            "description": "Your message for Hermes",
            "required": True
        }]
    },
    {
        "name": "openclaw",
        "description": "Switch to OpenClaw (Builder & Executor) and get a response",
        "type": 1,
        "options": [{
            "type": 3,
            "name": "message",
            "description": "Your message for OpenClaw",
            "required": True
        }]
    },
    {
        "name": "agent_status",
        "description": "Show active agent + recent progress",
        "type": 1
    }
]

# Register each command
for cmd in commands:
    r = requests.post(
        f'https://discord.com/api/v10/applications/{app_id}/guilds/{guild_id}/commands',
        headers=headers,
        json=cmd
    )
    print(f'/{cmd["name"]}: {r.status_code}')
    if r.status_code >= 400:
        print(f'  Error: {r.text[:200]}')

# Verify
r = requests.get(f'https://discord.com/api/v10/applications/{app_id}/guilds/{guild_id}/commands', headers=headers)
print(f'\nRegistered commands:')
for cmd in r.json():
    print(f'  /{cmd["name"]} — {cmd["description"]}')
