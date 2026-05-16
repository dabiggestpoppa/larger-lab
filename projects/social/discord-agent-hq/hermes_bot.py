"""
Hermes Discord Bot — Architect & Planner
Run with: python hermes_bot.py
Needs: DISCORD_HERMES_TOKEN in .env
"""

import discord
from discord import app_commands
import os, re, subprocess, sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

WORKSPACE = Path(os.getenv("WORKSPACE_PATH", str(Path(__file__).parent.parent)))
PROGRESS_FILE = WORKSPACE / "PROJECT_PROGRESS_CLEAN.md"


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
    dirs = [d.name for d in WORKSPACE.iterdir() if d.is_dir() and not d.name.startswith('.')]
    files = [f.name for f in WORKSPACE.iterdir() if f.is_file() and f.suffix in ('.py', '.md', '.json', '.txt')]
    return dirs[:15], files[:15]


async def handle_hermes(content: str) -> str:
    content_lower = content.lower().strip()

    if any(w in content_lower for w in ['status', 'progress', 'how are we', 'update']):
        progress = read_progress()
        lines = [l for l in progress.split('\n') if l.strip()][-10:]
        return f"🔱 **Hermes Status Report**\n```\n{chr(10).join(lines)[:1500]}\n```"

    if any(w in content_lower for w in ['help', 'what can you do']):
        return (
            "🔱 **Hermes — Architect & Planner**\n"
            "Commands:\n"
            "• `status` — project progress\n"
            "• `workspace` — list files/dirs\n"
            "• `plan: <idea>` — log a plan\n"
            "• `decision: <text>` — log architecture decision\n"
            "• Or ask me anything!"
        )

    if any(w in content_lower for w in ['workspace', 'files', 'structure']):
        dirs, files = get_workspace_summary()
        return f"🔱 **Workspace**\n📁 {', '.join(dirs)}\n📄 {', '.join(files)}"

    if content_lower.startswith('plan ') or content_lower.startswith('plan:'):
        text = content.split(' ', 1)[1].strip() if ' ' in content else content.split(':', 1)[1].strip()
        entry = append_progress(f"PLAN: {text}", "Hermes")
        return f"🔱 Plan logged: {entry}"

    if 'decision:' in content_lower or content_lower.startswith('decide'):
        text = content.split(':', 1)[-1].strip() if ':' in content else content
        entry = append_progress(f"DECISION: {text}", "Hermes")
        return f"🔱 Decision logged: {entry}"

    return f"🔱 Hermes here. \"{content[:200]}\" — ask me about status, workspace, plans, or decisions."


@bot.event
async def on_ready():
    print(f'🔱 {bot.user} has connected to Discord!')
    try:
        guild_id = os.getenv("DISCORD_GUILD_ID")
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            tree.copy_global_to(guild=guild)
            await tree.sync(guild=guild)
        else:
            await tree.sync()
    except Exception as e:
        print(f"Error syncing: {e}")
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="architecture")
    )


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    bot_id = bot.user.id
    if f"<@{bot_id}>" not in message.content and f"<@!{bot_id}>" not in message.content:
        return

    clean = message.content.replace(f"<@{bot_id}>", "").replace(f"<@!{bot_id}>", "").strip()
    if not clean:
        await message.channel.send("🔱 Hi! I'm Hermes, the Architect & Planner. Ask me about status, workspace, plans, or decisions.")
        return

    response = await handle_hermes(clean)
    await message.channel.send(response)


@tree.command(name="hermes", description="Talk to Hermes (Architect & Planner)")
@app_commands.describe(message="Your message")
async def hermes_cmd(interaction: discord.Interaction, message: str):
    response = await handle_hermes(message)
    await interaction.response.send_message(response)


@tree.command(name="status", description="Get project status")
async def status_cmd(interaction: discord.Interaction):
    response = await handle_hermes("status")
    await interaction.response.send_message(response)


if __name__ == "__main__":
    token = os.getenv("DISCORD_HERMES_TOKEN")
    if not token:
        print("Error: DISCORD_HERMES_TOKEN not set in .env")
        print("Create a bot at https://discord.com/developers/applications and add the token.")
        exit(1)
    bot.run(token)
