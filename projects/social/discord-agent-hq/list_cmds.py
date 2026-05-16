import os, requests, json
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(r'C:\Users\wifik\Desktop\projects\larger-lab\.env'))
token = os.getenv('DISCORD_BOT_TOKEN')
app_id = os.getenv('DISCORD_APPLICATION_ID')
guild_id = os.getenv('DISCORD_GUILD_ID')
headers = {'Authorization': 'Bot ' + token}

r = requests.get(f'https://discord.com/api/v10/applications/{app_id}/guilds/{guild_id}/commands', headers=headers)
print(f'Guild commands ({r.status_code}):')
for cmd in r.json():
    print(f'  /{cmd["name"]} — {cmd["description"]}')
