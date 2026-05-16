"""
Dual Discord Bot Runner
blrr city + hermes boa in one process via asyncio.
"""

import discord
from discord import app_commands
import os, re, subprocess, sys, asyncio
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path, override=True)

WORKSPACE = Path(os.getenv("WORKSPACE_PATH", str(Path(__file__).parent.parent)))
PROGRESS_FILE = WORKSPACE / "PROJECT_PROGRESS_CLEAN.md"

active_agent = "hermes"
responded_messages = set()


def read_progress():
    if PROGRESS_FILE.exists():
        return PROGRESS_FILE.read_text(encoding='utf-8')
    return "No progress file found."


def append_progress(entry, agent):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    line = f"\n- [{timestamp}] **{agent}**: {entry}"
    with open(PROGRESS_FILE, 'a', encoding='utf-8') as f:
        f.write(line)
    return line


def get_workspace_summary():
    dirs = sorted([d.name for d in WORKSPACE.iterdir() if d.is_dir() and not d.name.startswith('.')])
    files = sorted([f.name for f in WORKSPACE.iterdir() if f.is_file() and f.suffix in ('.py', '.md', '.json', '.txt')])
    return dirs[:12], files[:12]


def hermes_handle(content):
    c = content.lower().strip()
    if any(w in c for w in ['status', 'progress', 'update', 'how are we', 'ping']):
        lines = [l for l in read_progress().split('\n') if l.strip()][-10:]
        return "HERMES Status\n" + "\n".join(lines)[:1200]
    if any(w in c for w in ['help', 'what can']):
        return "HERMES - Architect & Planner\nstatus | workspace | plan: <text> | decision: <text>"
    if any(w in c for w in ['workspace', 'files', 'structure']):
        dirs, files = get_workspace_summary()
        return f"HERMES Workspace\nDirs: {', '.join(dirs)}\nFiles: {', '.join(files)}"
    if c.startswith('plan ') or c.startswith('plan:'):
        text = re.sub(r'^plan[:\s]*', '', c, flags=re.IGNORECASE).strip()
        return f"HERMES Plan logged: {append_progress('PLAN: ' + text, 'Hermes')}"
    if 'decision:' in c or c.startswith('decide'):
        text = re.sub(r'^decide[:\s]*', '', c.split(':', 1)[-1].strip() if ':' in c else c, flags=re.IGNORECASE).strip()
        return f"HERMES Decision logged: {append_progress('DECISION: ' + text, 'Hermes')}"
    return f'HERMES: "{content[:150]}" -- try status, workspace, plan:, decision:'


def openclaw_handle(content):
    c = content.lower().strip()
    if any(w in c for w in ['status', 'progress', 'what are you doing', 'ping']):
        lines = [l for l in read_progress().split('\n') if l.strip()][-5:]
        return "OPENCLAW Status\n" + "\n".join(lines)[:800]
    if any(w in c for w in ['help', 'what can']):
        return "OPENCLAW - Builder & Executor\nstatus | workspace | run <script> | edit: <text>"
    if any(w in c for w in ['workspace', 'files', 'structure']):
        dirs, files = get_workspace_summary()
        return f"OPENCLAW Workspace\nDirs: {', '.join(dirs)}\nFiles: {', '.join(files)}"
    if c.startswith('run '):
        script = content[4:].strip()
        sp = WORKSPACE / script
        if sp.exists():
            try:
                r = subprocess.run([sys.executable, str(sp)], capture_output=True, text=True, timeout=30, cwd=str(WORKSPACE))
                out = r.stdout[:1200] or r.stderr[:1200] or "(no output)"
                return f"Ran `{script}`:\n```{out}```"
            except subprocess.TimeoutExpired:
                return f"`{script}` timed out (30s)"
            except Exception as e:
                return f"Error: {e}"
        return f"Script not found: `{script}`"
    if c.startswith('edit:') or c.startswith('edit progress:'):
        text = re.sub(r'^edit( progress)?[:\s]*', '', c, flags=re.IGNORECASE).strip()
        return f"Progress updated: {append_progress(text, 'OpenClaw')}"
    return f'OPENCLAW: "{content[:150]}" -- try status, workspace, run <script>, edit: <text>'


def is_dup(msg_id):
    if msg_id in responded_messages:
        return True
    responded_messages.add(msg_id)
    if len(responded_messages) > 3000:
        responded_messages.clear()
    return False


# ── Bot 1: blrr city ──

intents1 = discord.Intents.default()
intents1.message_content = True

blrr = discord.Client(intents=intents1)
blrr_tree = app_commands.CommandTree(blrr)


@blrr.event
async def on_ready():
    print(f'[OK] blrr city: {blrr.user} (id={blrr.user.id})', flush=True)
    try:
        gid = os.getenv("DISCORD_GUILD_ID")
        if gid:
            guild = discord.Object(id=int(gid))
            blrr_tree.copy_global_to(guild=guild)
            synced = await blrr_tree.sync(guild=guild)
            print(f'  Synced {len(synced)} commands', flush=True)
    except Exception as e:
        print(f'  Sync error: {e}', flush=True)
    await blrr.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, name='@mentions | /hermes | /openclaw'))


@blrr.event
async def on_message(message):
    if message.author.id == blrr.user.id:
        return
    if is_dup(message.id):
        return
    bot_id = blrr.user.id
    mentioned = f'<@{bot_id}>' in message.content or f'<@!{bot_id}>' in message.content
    if not mentioned:
        return
    print(f'[blrr] {message.author}: {message.content[:80]}', flush=True)
    clean = message.content.replace(f'<@{bot_id}>', '').replace(f'<@!{bot_id}>', '').strip()
    if not clean:
        name = 'Hermes' if active_agent == 'hermes' else 'OpenClaw'
        await message.channel.send(f'Active: **{name}**. Use /hermes or /openclaw to switch.')
        return
    response = hermes_handle(clean) if active_agent == 'hermes' else openclaw_handle(clean)
    await message.channel.send(response)


@blrr_tree.command(name='hermes', description='Switch to Hermes (Architect & Planner)')
@app_commands.describe(message='Message for Hermes')
async def blrr_hermes(interaction: discord.Interaction, message: str):
    global active_agent
    active_agent = 'hermes'
    await interaction.response.send_message(hermes_handle(message))


@blrr_tree.command(name='openclaw', description='Switch to OpenClaw (Builder & Executor)')
@app_commands.describe(message='Message for OpenClaw')
async def blrr_openclaw(interaction: discord.Interaction, message: str):
    global active_agent
    active_agent = 'openclaw'
    await interaction.response.send_message(openclaw_handle(message))


@blrr_tree.command(name='agent_status', description='Show active agent + recent progress')
async def blrr_status(interaction: discord.Interaction):
    global active_agent
    name = 'Hermes' if active_agent == 'hermes' else 'OpenClaw'
    lines = [l for l in read_progress().split('\n') if l.strip()][-5:]
    embed = discord.Embed(title='Agent Status', color=0x2ecc71)
    embed.add_field(name='Active Agent', value=name, inline=True)
    embed.add_field(name='Recent Progress', value='\n'.join(lines)[:1024] or 'No entries', inline=False)
    await interaction.response.send_message(embed=embed)


# ── Bot 2: hermes boa ──

intents2 = discord.Intents.default()
intents2.message_content = True

hermes_bot = discord.Client(intents=intents2)
hermes_tree = app_commands.CommandTree(hermes_bot)


@hermes_bot.event
async def on_ready():
    print(f'[OK] hermes boa: {hermes_bot.user} (id={hermes_bot.user.id})', flush=True)
    try:
        gid = os.getenv("DISCORD_GUILD_ID")
        if gid:
            guild = discord.Object(id=int(gid))
            hermes_tree.copy_global_to(guild=guild)
            synced = await hermes_tree.sync(guild=guild)
            print(f'  Synced {len(synced)} commands', flush=True)
    except Exception as e:
        print(f'  Sync error: {e}', flush=True)
    await hermes_bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.listening, name='architecture'))


@hermes_bot.event
async def on_message(message):
    if message.author.id == hermes_bot.user.id:
        return
    if is_dup(message.id):
        return
    bot_id = hermes_bot.user.id
    mentioned = f'<@{bot_id}>' in message.content or f'<@!{bot_id}>' in message.content
    if not mentioned:
        return
    print(f'[hermes] {message.author}: {message.content[:80]}', flush=True)
    clean = message.content.replace(f'<@{bot_id}>', '').replace(f'<@!{bot_id}>', '').strip()
    if not clean:
        await message.channel.send('HERMES - Architect & Planner. Ask about status, workspace, plans, or decisions.')
        return
    await message.channel.send(hermes_handle(clean))


@hermes_tree.command(name='hermes', description='Talk to Hermes (Architect & Planner)')
@app_commands.describe(message='Your message')
async def hermes_cmd(interaction: discord.Interaction, message: str):
    await interaction.response.send_message(hermes_handle(message))


@hermes_tree.command(name='status', description='Get project status')
async def hermes_status(interaction: discord.Interaction):
    await interaction.response.send_message(hermes_handle('status'))


# ── Main ──

async def main():
    t1 = os.getenv('DISCORD_BOT_TOKEN')
    t2 = os.getenv('DISCORD_HERMES_TOKEN')
    print(f'Starting dual bot...', flush=True)
    print(f'  blrr city token: {len(t1)} chars', flush=True)
    print(f'  hermes token: {len(t2)} chars', flush=True)
    await asyncio.gather(
        blrr.start(t1),
        hermes_bot.start(t2),
    )


if __name__ == '__main__':
    asyncio.run(main())
