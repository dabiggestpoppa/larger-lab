"""
Discord Bot -- blrr city
@mentions respond as the active agent (default: Hermes)
/hermes -> switch to Hermes + respond
/openclaw -> switch to OpenClaw + respond
/agent_status -> show active agent + progress
"""

import discord
from discord import app_commands
from discord.ext import commands
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

# Use commands.Bot instead of discord.Client -- this gives us process_commands()
bot = commands.Bot(command_prefix='!', intents=intents)
tree = bot.tree  # commands.Bot already has a tree

WORKSPACE = Path(os.getenv("WORKSPACE_PATH", str(Path(__file__).parent.parent)))
PROGRESS_FILE = WORKSPACE / "PROJECT_PROGRESS_CLEAN.md"

# State
active_agent = "hermes"
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


def hermes_handle(content: str) -> str:
    c = content.lower().strip()
    if any(w in c for w in ['status', 'progress', 'update', 'how are we']):
        lines = [l for l in read_progress().split('\n') if l.strip()][-10:]
        return f"HERMES Status\n```\n{chr(10).join(lines)[:1200]}\n```"
    if any(w in c for w in ['help', 'what can']):
        return ("HERMES - Architect & Planner\n"
                "status | workspace | plan: <text> | decision: <text>")
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


def openclaw_handle(content: str) -> str:
    c = content.lower().strip()
    if any(w in c for w in ['status', 'progress', 'what are you doing']):
        lines = [l for l in read_progress().split('\n') if l.strip()][-5:]
        return f"OPENCLAW Status\n```\n{chr(10).join(lines)[:800]}\n```\nReady for tasks!"
    if any(w in c for w in ['help', 'what can']):
        return ("OPENCLAW - Builder & Executor\n"
                "status | workspace | run <script> | edit: <text> | create: <file> | <content>")
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
                return f"Ran `{script}`:\n```\n{out}\n```"
            except subprocess.TimeoutExpired:
                return f"`{script}` timed out (30s)"
            except Exception as e:
                return f"Error: {e}"
        return f"Script not found: `{script}`"
    if c.startswith('edit:') or c.startswith('edit progress:'):
        text = re.sub(r'^edit( progress)?[:\s]*', '', c, flags=re.IGNORECASE).strip()
        return f"Progress updated: {append_progress(text, 'OpenClaw')}"
    if c.startswith('create:') or c.startswith('create file:'):
        parts = re.sub(r'^create( file)?[:\s]*', '', c, flags=re.IGNORECASE).strip().split('|', 1)
        fname = parts[0].strip()
        fcontent = parts[1].strip() if len(parts) > 1 else "# Created by OpenClaw\n"
        try:
            (WORKSPACE / fname).write_text(fcontent, encoding='utf-8')
            return f"Created: `{fname}`"
        except Exception as e:
            return f"Error: {e}"
    return f'OPENCLAW: "{content[:150]}" -- try status, workspace, run <script>, edit: <text>'


@bot.event
async def on_ready():
    print(f'[OK] {bot.user} connected (id={bot.user.id})')
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
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, name="@mentions | /hermes | /openclaw"))


@bot.event
async def on_message(message):
    # Skip own messages immediately
    if message.author.id == bot.user.id:
        return

    bot_id = bot.user.id
    mentioned = f"<@{bot_id}>" in message.content or f"<@!{bot_id}>" in message.content

    if mentioned:
        # Prevent duplicate responses
        if message.id in responded_messages:
            return
        responded_messages.add(message.id)
        if len(responded_messages) > 2000:
            responded_messages.clear()

        clean = message.content.replace(f"<@{bot_id}>", "").replace(f"<@!{bot_id}>", "").strip()
        if not clean:
            agent_name = "Hermes" if active_agent == "hermes" else "OpenClaw"
            await message.channel.send(f"Active agent: **{agent_name}**. Use `/hermes` or `/openclaw` to switch.")
            return

        if active_agent == "hermes":
            response = hermes_handle(clean)
        else:
            response = openclaw_handle(clean)

        await message.channel.send(response)

    # ALWAYS process commands at the end -- this is critical for slash commands to work
    await bot.process_commands(message)


# -- Slash commands --
@tree.command(name="hermes", description="Switch to Hermes and get a response")
@app_commands.describe(message="Message for Hermes")
async def hermes_cmd(interaction: discord.Interaction, message: str):
    global active_agent
    active_agent = "hermes"
    response = hermes_handle(message)
    await interaction.response.send_message(response)


@tree.command(name="openclaw", description="Switch to OpenClaw and get a response")
@app_commands.describe(message="Message for OpenClaw")
async def openclaw_cmd(interaction: discord.Interaction, message: str):
    global active_agent
    active_agent = "openclaw"
    response = openclaw_handle(message)
    await interaction.response.send_message(response)


@tree.command(name="agent_status", description="Show which agent is active + recent progress")
async def agent_status(interaction: discord.Interaction):
    global active_agent
    name = "Hermes" if active_agent == "hermes" else "OpenClaw"
    lines = [l for l in read_progress().split('\n') if l.strip()][-5:]
    embed = discord.Embed(title="Agent Status", color=0x2ecc71)
    embed.add_field(name="Active Agent", value=name, inline=True)
    embed.add_field(name="Recent Progress", value='\n'.join(lines)[:1024] or "No entries", inline=False)
    embed.set_footer(text="Use /hermes or /openclaw to switch agents")
    await interaction.response.send_message(embed=embed)


if __name__ == "__main__":
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        print("Error: DISCORD_BOT_TOKEN not set")
        exit(1)
    bot.run(token)
