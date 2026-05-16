"""
Setup separate Hermes and OpenClaw webhooks via Discord API.
Requires bot to have 'Manage Webhooks' permission.
"""
import requests, json, os, sys
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(r'C:\Users\wifik\Desktop\projects\larger-lab\.env')
load_dotenv(env_path)
token = os.getenv('DISCORD_BOT_TOKEN')
guild_id = os.getenv('DISCORD_GUILD_ID')

if not token:
    print('ERROR: DISCORD_BOT_TOKEN not set')
    sys.exit(1)

headers = {'Authorization': 'Bot ' + token, 'Content-Type': 'application/json'}

# Get channels
r = requests.get(f'https://discord.com/api/v10/guilds/{guild_id}/channels', headers=headers)
if r.status_code != 200:
    print(f'ERROR getting channels: {r.status_code} - {r.text}')
    sys.exit(1)

channels = r.json()
text_channels = [c for c in channels if c.get('type') == 0]

print('Available text channels:')
for c in text_channels:
    print(f'  {c["id"]} - #{c["name"]}')

# Use #general channel
target_channel = None
for c in text_channels:
    if 'general' in c['name'].lower():
        target_channel = c
        break

if not target_channel:
    target_channel = text_channels[0]

channel_id = target_channel['id']
print(f'\nUsing channel: #{target_channel["name"]} ({channel_id})')

# Create Hermes webhook
print('\nCreating Hermes webhook...')
r_hermes = requests.post(
    f'https://discord.com/api/v10/channels/{channel_id}/webhooks',
    headers=headers,
    json={
        'name': 'Hermes Agent',
        'avatar': None  # Will use default
    }
)
print(f'Hermes webhook status: {r_hermes.status_code}')
if r_hermes.status_code == 200:
    hw = r_hermes.json()
    hermes_webhook_url = f"https://discord.com/api/webhooks/{hw['id']}/{hw['token']}"
    print(f'Hermes webhook URL: {hermes_webhook_url}')
else:
    print(f'Error: {r_hermes.text}')
    hermes_webhook_url = None

# Create OpenClaw webhook
print('\nCreating OpenClaw webhook...')
r_openclaw = requests.post(
    f'https://discord.com/api/v10/channels/{channel_id}/webhooks',
    headers=headers,
    json={
        'name': 'OpenClaw Agent',
        'avatar': None
    }
)
print(f'OpenClaw webhook status: {r_openclaw.status_code}')
if r_openclaw.status_code == 200:
    ow = r_openclaw.json()
    openclaw_webhook_url = f"https://discord.com/api/webhooks/{ow['id']}/{ow['token']}"
    print(f'OpenClaw webhook URL: {openclaw_webhook_url}')
else:
    print(f'Error: {r_openclaw.text}')
    openclaw_webhook_url = None

# Test Hermes webhook
if hermes_webhook_url:
    print('\n--- Testing Hermes webhook ---')
    r_test = requests.post(hermes_webhook_url, json={
        'username': 'Hermes Agent',
        'embeds': [{
            'title': '🔱 Hermes Online',
            'description': 'Hermes agent is now online and ready to coordinate!',
            'color': 0x3498db,
            'fields': [
                {'name': 'Role', 'value': 'Architect & Planner', 'inline': True},
                {'name': 'Status', 'value': 'Active', 'inline': True}
            ]
        }]
    })
    print(f'Hermes test: {r_test.status_code}')

# Test OpenClaw webhook
if openclaw_webhook_url:
    print('\n--- Testing OpenClaw webhook ---')
    r_test2 = requests.post(openclaw_webhook_url, json={
        'username': 'OpenClaw Agent',
        'embeds': [{
            'title': '🦀 OpenClaw Online',
            'description': 'OpenClaw agent is now online and ready to build!',
            'color': 0x2ecc71,
            'fields': [
                {'name': 'Role', 'value': 'Builder & Executor', 'inline': True},
                {'name': 'Status', 'value': 'Active', 'inline': True}
            ]
        }]
    })
    print(f'OpenClaw test: {r_test2.status_code}')

# Save to .env
if hermes_webhook_url or openclaw_webhook_url:
    print('\n--- Updating .env ---')
    with open(env_path, 'r') as f:
        env_content = f.read()
    
    # Update or add webhook URLs
    lines = env_content.split('\n')
    new_lines = []
    hermes_added = False
    openclaw_added = False
    
    for line in lines:
        if line.startswith('DISCORD_WEBHOOK_HERMES=') and hermes_webhook_url:
            new_lines.append(f'DISCORD_WEBHOOK_HERMES={hermes_webhook_url}')
            hermes_added = True
        elif line.startswith('DISCORD_WEBHOOK_OPENCLAW=') and openclaw_webhook_url:
            new_lines.append(f'DISCORD_WEBHOOK_OPENCLAW={openclaw_webhook_url}')
            openclaw_added = True
        else:
            new_lines.append(line)
    
    if not hermes_added and hermes_webhook_url:
        new_lines.append(f'\nDISCORD_WEBHOOK_HERMES={hermes_webhook_url}')
    if not openclaw_added and openclaw_webhook_url:
        new_lines.append(f'DISCORD_WEBHOOK_OPENCLAW={openclaw_webhook_url}')
    
    with open(env_path, 'w') as f:
        f.write('\n'.join(new_lines))
    
    print('Updated .env with new webhook URLs')

print('\n✅ Setup complete!')
