"""
Discord Bot for Agent Communication.
Provides slash commands for task management and agent coordination.
"""

import discord
from discord import app_commands
import os
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import AgentTeamOrchestrator


# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)
orchestrator = AgentTeamOrchestrator()


@bot.event
async def on_ready():
    """Called when the bot is ready."""
    print(f'{bot.user} has connected to Discord!')
    
    # Sync slash commands
    try:
        guild_id = os.getenv("DISCORD_GUILD_ID")
        if guild_id:
            guild = discord.Object(id=int(guild_id))
            tree.copy_global_to(guild=guild)
            await tree.sync(guild=guild)
            print(f"Synced commands to guild {guild_id}")
        else:
            await tree.sync()
            print("Synced global commands")
    except Exception as e:
        print(f"Error syncing commands: {e}")
    
    # Set bot activity
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="the agent team"
        )
    )


@tree.command(name="agent_status", description="Get status of all agents")
async def agent_status(interaction: discord.Interaction):
    """Get the current status of all agents."""
    status = orchestrator.get_team_status()
    
    embed = discord.Embed(
        title="🏢 Agent Team Status",
        color=0x2ecc71
    )
    embed.add_field(name="Hermes", value=status["hermes"]["status"], inline=True)
    embed.add_field(name="OpenClaw", value=status["openclaw"]["status"], inline=True)
    embed.add_field(name="Active Tasks", value=str(status["active_tasks"]), inline=False)
    
    await interaction.response.send_message(embed=embed)


@tree.command(name="assign_task", description="Assign a task to an agent")
@app_commands.describe(agent="Agent name (hermes or openclaw)", task="Task description")
async def assign_task(interaction: discord.Interaction, agent: str, task: str):
    """Assign a task to an agent."""
    agent = agent.lower()
    if agent not in ["hermes", "openclaw"]:
        await interaction.response.send_message("Invalid agent. Use 'hermes' or 'openclaw'.")
        return
    
    task_id = orchestrator.assign_task(agent, task)
    await interaction.response.send_message(f"✅ Task assigned: `{task_id}` to **{agent.title()}**")


@tree.command(name="workspace_update", description="Post a workspace update")
@app_commands.describe(filename="File name", message="Update message")
async def workspace_update(interaction: discord.Interaction, filename: str, message: str = ""):
    """Post a workspace update to Discord."""
    workspace_path = Path(os.getenv("WORKSPACE_PATH", "."))
    file_path = workspace_path / filename
    
    if not file_path.exists():
        await interaction.response.send_message(f"File `{filename}` not found in workspace.")
        return
    
    embed = discord.Embed(
        title=f"📂 Workspace Update: {filename}",
        description=message or f"Updated {filename}",
        color=0x3498db
    )
    
    await interaction.response.send_message(embed=embed)


@tree.command(name="standup", description="Run daily standup")
async def standup(interaction: discord.Interaction):
    """Run a daily standup with all agents."""
    await orchestrator.run_daily_standup()
    await interaction.response.send_message("📋 Daily standup initiated! Check the channel for updates.")


@tree.command(name="task_progress", description="Check task progress")
@app_commands.describe(task_id="Task ID (e.g., task-202401151230)")
async def task_progress(interaction: discord.Interaction, task_id: str):
    """Check the progress of a specific task."""
    if task_id not in orchestrator.tasks:
        await interaction.response.send_message(f"Task `{task_id}` not found.")
        return
    
    task = orchestrator.tasks[task_id]
    embed = discord.Embed(
        title=f"📊 Task Progress: {task_id}",
        color=0x9b59b6
    )
    embed.add_field(name="Agent", value=task["agent"].title(), inline=True)
    embed.add_field(name="Status", value=task["status"], inline=True)
    embed.add_field(name="Task", value=task["task"], inline=False)
    
    if "result" in task:
        embed.add_field(name="Result", value=task["result"][:1000], inline=False)
    
    await interaction.response.send_message(embed=embed)


# Run the bot
if __name__ == "__main__":
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        print("Error: DISCORD_BOT_TOKEN not set in environment")
        exit(1)
    
    bot.run(token)