"""
Discord Bot -- blrr city (OC2 / OWL)
@mentions respond as OWL (OC2)
/status -> show agent status + progress
/help -> show available commands
"""

import discord
from discord import app_commands
import os, re, subprocess, sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

WORKSPACE = Path(os.getenv("WORKSPACE_PATH", str(Path(__file__).parent.parent)))
PROGRESS_FILE = WORKSPACE / "PROJECT_PROGRESS_CLEAN.md"

# State
responded_messages = set()


def read_progress():
    if PROGRESS_FILE.exists():
        return PROGRESS_FILE.read_text(encoding='utf-8')
    return "No progress file found."


def append_progress(entry: str, agent: str):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    line = f"\n- [{timestamp}] **{agent}**: {entry}"
    with open(PROGRESS_FILE, 'a', encoding='utf-8') as f:
        f.write(line)
    return line


def get_workspace_summary():
    dirs = sorted([d.name for d in WORKSPACE.iterdir() if d.is_dir() and not d.name.startswith('.')])
    files = sorted([f.name for f in WORKSPACE.iterdir() if f.is_file() and f.suffix in ('.py', '.md', '.json', '.txt')])
    return dirs[:12], files[:12]


def owl_handle(content: str) -> str:
    c = content.lower().strip()
    if any(w in c for w in ['status', 'progress', 'update', 'how are we', 'ping']):
        lines = [l for l in read_progress().split('\n') if l.strip()][-10:]
        return f"🦉 OWL (OC2) Status\n```\n{chr(10).join(lines)[:1200]}\n```"
    if any(w in c for w in ['help', 'what can']):
        return ("🦉 OWL (OC2) — Operator Shell\n"
                "status | workspace | run <script> | edit: <text> | create: <file>")
    if any(w in c for w in ['workspace', 'files', 'structure']):
        dirs, files = get_workspace_summary()
        return f"🦉 Workspace\n📁 {', '.join(dirs)}\n📄 {', '.join(files)}"
    if c.startswith('run '):
        script = content[4:].strip()
        sp = WORKSPACE / script
        if sp.exists():
            try:
                r = subprocess.run([sys.executable, str(sp)], capture_output=True, text=True, timeout=30, cwd=str(WORKSPACE))
                out = r.stdout[:1200] or r.stderr[:1200] or "(no output)"
                return f"Ran `{script}`:\n```\n{out}\n```"
            except subprocess.TimeoutExpired:
                return f"`{script}` timed out (30s)"
            except Exception as e:
                return f"Error: {e}"
        return f"Script not found: `{script}`"
    if c.startswith('edit:') or c.startswith('edit progress:'):
        text = re.sub(r'^edit( progress)?[:\s]*', '', c, flags=re.IGNORECASE).strip()
        return f"Progress updated: {append_progress(text, 'OC2')}"
    if c.startswith('create:') or c.startswith('create file:'):
        parts = re.sub(r'^create( file)?[:\s]*', '', c, flags=re.IGNORECASE).strip().split('|', 1)
        fname = parts[0].strip()
        fcontent = parts[1].strip() if len(parts) > 1 else "# Created by OC2\n"
        try:
            (WORKSPACE / fname).write_text(fcontent, encoding='utf-8')
            return f"Created: `{fname}`"
        except Exception as e:
            return f"Error: {e}"
    return f'🦉 OWL: "{content[:150]}" — try status, workspace, run <script>, edit: <text>'


@client.event
async def on_ready():
    print(f'[OK] blrr city (OC2): {client.user} connected (id={client.user.id})')
    try:
        gid = os.getenv("DISCORD_GUILD_ID")
        if gid:
            guild = discord.Object(id=int(gid))
            tree.copy_global_to(guild=guild)
            synced = await tree.sync(guild=guild)
            print(f"Synced {len(synced)} commands to guild")
        else:
            synced = await tree.sync()
            print(f"Synced {len(synced)} global commands")
    except Exception as e:
        print(f"Sync error: {e}")
    await client.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, name="@mentions | /status | /help"))


@client.event
async def on_message(message):
    print(f"[DEBUG] on_message: {message.author} ({message.author.id}): {message.content[:80]}")

    if message.author.id == client.user.id:
        print("  -> SKIP (self)")
        return

    bot_id = client.user.id
    mentioned = f"<@{bot_id}>" in message.content or f"<@!{bot_id}>" in message.content

    if mentioned:
        if message.id in responded_messages:
            print("  -> SKIP (duplicate)")
            return
        responded_messages.add(message.id)
        if len(responded_messages) > 2000:
            responded_messages.clear()

        clean = message.content.replace(f"<@{bot_id}>", "").replace(f"<@!{bot_id}>", "").strip()
        print(f"  -> mentioned, clean='{clean}'")
        if not clean:
            await message.channel.send("🦉 OWL (OC2) here. Use `/status` or just ask me anything.")
            return

        response = owl_handle(clean)
        print(f"  -> responding: {response[:80]}")
        await message.channel.send(response)


# -- Slash commands --
@tree.command(name="status", description="Show OWL (OC2) status + recent progress")
async def status_cmd(interaction: discord.Interaction):
    lines = [l for l in read_progress().split('\n') if l.strip()][-5:]
    embed = discord.Embed(title="🦉 OWL (OC2) Status", color=0x2ecc71)
    embed.add_field(name="Agent", value="OC2 / OWL", inline=True)
    embed.add_field(name="Recent Progress", value='\n'.join(lines)[:1024] or "No entries", inline=False)
    await interaction.response.send_message(embed=embed)


@tree.command(name="help", description="Show available commands")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(title="🦉 OWL (OC2) Commands", color=0x3498db)
    embed.add_field(name="Mention me", value="@blrr city + your message", inline=False)
    embed.add_field(name="/status", value="Show status + progress", inline=False)
    embed.add_field(name="/help", value="This message", inline=False)
    embed.add_field(name="Text commands", value="`status` `workspace` `run <script>` `edit: <text>` `create: <file> | <content>`", inline=False)
    await interaction.response.send_message(embed=embed)


if __name__ == "__main__":
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        print("Error: DISCORD_BOT_TOKEN not set")
        exit(1)
    client.run(token)
