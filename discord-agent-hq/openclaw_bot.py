"""
OpenClaw Discord Bot — Builder & Executor
Run with: python openclaw_bot.py
Needs: DISCORD_OPENCLAW_TOKEN in .env
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


async def handle_openclaw(content: str) -> str:
    content_lower = content.lower().strip()

    if any(w in content_lower for w in ['status', 'progress', 'what are you doing']):
        progress = read_progress()
        lines = [l for l in progress.split('\n') if l.strip()][-5:]
        return f"🦀 **OpenClaw Status**\n```\n{chr(10).join(lines)[:1000]}\n```\nReady for tasks!"

    if any(w in content_lower for w in ['help', 'what can you do']):
        return (
            "🦀 **OpenClaw — Builder & Executor**\n"
            "Commands:\n"
            "• `status` — check progress\n"
            "• `workspace` — list files/dirs\n"
            "• `edit progress: <text>` — add to progress file\n"
            "• `run <script.py>` — run a Python script\n"
            "• `create file: <name> | <content>` — create a file\n"
            "• Or give me any task!"
        )

    if any(w in content_lower for w in ['workspace', 'files', 'structure']):
        dirs, files = get_workspace_summary()
        return f"🦀 **Workspace**\n📁 {', '.join(dirs)}\n📄 {', '.join(files)}"

    if content_lower.startswith('edit progress:') or content_lower.startswith('progress:'):
        text = content.split(':', 1)[1].strip()
        entry = append_progress(text, "OpenClaw")
        return f"🦀 Progress updated: {entry}"

    if content_lower.startswith('create file:') or content_lower.startswith('create:'):
        parts = content.split(':', 1)[1].strip().split('|', 1)
        filename = parts[0].strip()
        file_content = parts[1].strip() if len(parts) > 1 else "# Created by OpenClaw\n"
        target = WORKSPACE / filename
        try:
            target.write_text(file_content, encoding='utf-8')
            return f"🦀 File created: `{filename}`"
        except Exception as e:
            return f"🦀 Error creating file: {e}"

    if content_lower.startswith('run '):
        script = content[4:].strip()
        script_path = WORKSPACE / script
        if script_path.exists():
            try:
                result = subprocess.run(
                    [sys.executable, str(script_path)],
                    capture_output=True, text=True, timeout=30,
                    cwd=str(WORKSPACE)
                )
                output = result.stdout[:1500] or result.stderr[:1500] or "(no output)"
                return f"🦀 Ran `{script}`:\n```\n{output}\n```"
            except subprocess.TimeoutExpired:
                return f"🦀 Script `{script}` timed out after 30s"
            except Exception as e:
                return f"🦀 Error running `{script}`: {e}"
        else:
            return f"🦀 Script not found: `{script}`"

    return f"🦀 OpenClaw here. \"{content[:200]}\" — give me a task!"


@bot.event
async def on_ready():
    print(f'🦀 {bot.user} has connected to Discord!')
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
        activity=discord.Activity(type=discord.ActivityType.watching, name="for tasks")
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
        await message.channel.send("🦀 Hi! I'm OpenClaw, the Builder & Executor. Give me tasks — edit progress, create files, run scripts.")
        return

    response = await handle_openclaw(clean)
    await message.channel.send(response)


@tree.command(name="openclaw", description="Talk to OpenClaw (Builder & Executor)")
@app_commands.describe(message="Your message")
async def openclaw_cmd(interaction: discord.Interaction, message: str):
    response = await handle_openclaw(message)
    await interaction.response.send_message(response)


@tree.command(name="status", description="Get project status")
async def status_cmd(interaction: discord.Interaction):
    response = await handle_openclaw("status")
    await interaction.response.send_message(response)


if __name__ == "__main__":
    token = os.getenv("DISCORD_OPENCLAW_TOKEN")
    if not token:
        print("Error: DISCORD_OPENCLAW_TOKEN not set in .env")
        print("Create a bot at https://discord.com/developers/applications and add the token.")
        exit(1)
    bot.run(token)
