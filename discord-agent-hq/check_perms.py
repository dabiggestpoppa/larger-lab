import os, requests, json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(r'C:\Users\wifik\Desktop\projects\larger-lab\.env'))
token = os.getenv('DISCORD_BOT_TOKEN')
guild_id = os.getenv('DISCORD_GUILD_ID')
channel_id = os.getenv('DISCORD_CHANNEL_ID')
headers = {'Authorization': 'Bot ' + token}

# 1. Check bot user info
r = requests.get('https://discord.com/api/v10/users/@me', headers=headers)
print('=== BOT USER ===')
print(json.dumps(r.json(), indent=2)[:500])
print()

# 2. Check bot's guild member info (roles, permissions)
r2 = requests.get(f'https://discord.com/api/v10/guilds/{guild_id}/members/{r.json()["id"]}', headers=headers)
print('=== BOT GUILD MEMBER ===')
if r2.status_code == 200:
    data = r2.json()
    print(f'Roles: {data.get("roles", [])}')
    print(f'Nickname: {data.get("nick")}')
else:
    print(f'Error: {r2.status_code} - {r2.text[:200]}')
print()

# 3. Check guild roles
r3 = requests.get(f'https://discord.com/api/v10/guilds/{guild_id}/roles', headers=headers)
print('=== GUILD ROLES ===')
if r3.status_code == 200:
    for role in r3.json():
        name = role.get('name', '?')
        if name in ['@everyone', 'blrr city', 'Bot'] or 'bot' in name.lower():
            print(f'  {name} (id={role["id"]}, permissions={role["permissions"]}, position={role.get("position", "?")})')
else:
    print(f'Error: {r3.status_code}')
print()

# 4. Check channel
r4 = requests.get(f'https://discord.com/api/v10/channels/{channel_id}', headers=headers)
print('=== CHANNEL ===')
if r4.status_code == 200:
    ch = r4.json()
    print(f'Name: #{ch.get("name")}')
    print(f'Type: {ch.get("type")}')
    print(f'Permission overwrites: {json.dumps(ch.get("permission_overwrites", []), indent=2)[:500]}')
else:
    print(f'Error: {r4.status_code} - {r4.text[:200]}')
print()

# 5. Check bot's effective permissions in the channel
r5 = requests.get(f'https://discord.com/api/v10/channels/{channel_id}', headers=headers)
print('=== BOT PERMISSIONS IN CHANNEL ===')
if r5.status_code == 200:
    ch = r5.json()
    overwrites = ch.get('permission_overwrites', [])
    bot_id = r.json()['id']
    bot_member_roles = r2.json().get('roles', []) if r2.status_code == 200 else []
    
    # Calculate effective permissions
    guild_roles = {r['id']: r for r in r3.json()} if r3.status_code == 200 else {}
    
    # Start with @everyone permissions
    everyone_id = guild_id  # @everyone role ID = guild ID
    effective_perms = int(guild_roles.get(everyone_id, {}).get('permissions', '0'))
    
    # Apply role permissions (OR them together)
    for role_id in bot_member_roles:
        if role_id in guild_roles:
            effective_perms |= int(guild_roles[role_id].get('permissions', '0'))
    
    # Apply channel overwrites
    for ow in overwrites:
        ow_type = ow.get('type')  # 0=role, 1=member
        ow_id = ow.get('id')
        allow = int(ow.get('allow', '0'))
        deny = int(ow.get('deny', '0'))
        
        if ow_type == 1 and ow_id == bot_id:
            effective_perms &= ~deny
            effective_perms |= allow
        elif ow_type == 0 and ow_id in bot_member_roles:
            effective_perms &= ~deny
            effective_perms |= allow
        elif ow_type == 0 and ow_id == everyone_id:
            effective_perms &= ~deny
            effective_perms |= allow
    
    # Check key permissions
    SEND_MESSAGES = 1 << 11
    READ_MESSAGES = 1 << 10
    USE_APPLICATION_COMMANDS = 1 << 31
    VIEW_CHANNEL = 1 << 10
    READ_MESSAGE_HISTORY = 1 << 16
    EMBED_LINKS = 1 << 14
    ATTACH_FILES = 1 << 15
    
    print(f'Effective permissions: {effective_perms}')
    print(f'  VIEW_CHANNEL: {bool(effective_perms & VIEW_CHANNEL)}')
    print(f'  SEND_MESSAGES: {bool(effective_perms & SEND_MESSAGES)}')
    print(f'  READ_MESSAGE_HISTORY: {bool(effective_perms & READ_MESSAGE_HISTORY)}')
    print(f'  EMBED_LINKS: {bool(effective_perms & EMBED_LINKS)}')
    print(f'  ATTACH_FILES: {bool(effective_perms & ATTACH_FILES)}')
    print(f'  USE_APPLICATION_COMMANDS: {bool(effective_perms & USE_APPLICATION_COMMANDS)}')
