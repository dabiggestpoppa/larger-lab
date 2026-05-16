"""
OpenClaw Discord Agent - The Builder/Executor agent for Discord communication.
"""

import subprocess
import json
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.discord import post_text, post_embed, get_agent_webhook


class OpenClawDiscordAgent:
    """
    OpenClaw agent wrapper that communicates via Discord.
    Handles building, executing, and implementing tasks.
    """
    
    def __init__(self, workspace_path: str = None):
        self.workspace_path = Path(workspace_path or os.getenv("WORKSPACE_PATH", "."))
        self.agent_name = "OpenClaw"
        self.webhook_url = get_agent_webhook("OPENCLAW") or os.getenv("DISCORD_WEBHOOK_URL")
    
    def run_openclaw(self, command: str) -> str:
        """
        Execute OpenClaw with the given command.
        This is a placeholder - replace with actual OpenClaw execution.
        """
        # Placeholder for actual OpenClaw execution
        result = f"OpenClaw executed: {command[:100]}..."
        return result
    
    def post_status(self, status: str, details: dict = None):
        """Post a status update to Discord."""
        fields = None
        if details:
            fields = {k: str(v) for k, v in details.items()}
        
        post_embed(
            title=f"🦀 {self.agent_name} Status Update",
            description=status,
            color=0x2ecc71,  # Green
            fields=fields,
            webhook_url=self.webhook_url
        )
    
    def post_build_progress(self, task: str, progress: int, total: int = 100):
        """Post build progress to Discord."""
        percentage = (progress / total) * 100
        bar_length = 20
        filled = int(bar_length * progress / total)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        post_embed(
            title=f"🛠️ {self.agent_name} - Build Progress",
            description=f"**Task:** {task}\n\n`{bar}` {percentage:.0f}%",
            color=0x1abc9c,  # Teal
            webhook_url=self.webhook_url
        )
    
    def post_completion(self, task: str, result: str, files: list = None):
        """Post task completion to Discord."""
        fields = None
        if files:
            fields = {"Files Created/Modified": "\n".join(f"• `{f}`" for f in files[:10])}
        
        post_embed(
            title=f"✅ {self.agent_name} - Task Complete",
            description=f"**Task:** {task}\n\n**Result:** {result[:2000]}",
            color=0x27ae60,  # Green
            fields=fields,
            webhook_url=self.webhook_url
        )
    
    def post_error(self, task: str, error: str):
        """Post an error to Discord."""
        post_embed(
            title=f"❌ {self.agent_name} - Error",
            description=f"**Task:** {task}\n\n**Error:** ```\n{error[:2000]}\n```",
            color=0xe74c3c,  # Red
            webhook_url=self.webhook_url
        )
    
    def post_implementation(self, component: str, details: str):
        """Post implementation details to Discord."""
        post_embed(
            title=f"🔧 {self.agent_name} - Implementation",
            description=f"**Component:** {component}\n\n{details[:3000]}",
            color=0x3498db,  # Blue
            webhook_url=self.webhook_url
        )


def main():
    """Main entry point for OpenClaw Discord agent."""
    agent = OpenClawDiscordAgent()
    
    # Example usage
    agent.post_status(
        "OpenClaw agent initialized and ready",
        {"Workspace": str(agent.workspace_path), "Status": "Online"}
    )


if __name__ == "__main__":
    main()