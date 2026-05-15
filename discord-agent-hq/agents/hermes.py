"""
Hermes Discord Agent - The Architect/Planner agent for Discord communication.
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


class HermesDiscordAgent:
    """
    Hermes agent wrapper that communicates via Discord.
    Handles planning, architecture decisions, and coordination.
    """
    
    def __init__(self, workspace_path: str = None):
        self.workspace_path = Path(workspace_path or os.getenv("WORKSPACE_PATH", "."))
        self.agent_name = "Hermes"
        self.webhook_url = get_agent_webhook("HERMES") or os.getenv("DISCORD_WEBHOOK_URL")
    
    def run_hermes(self, prompt: str) -> str:
        """
        Execute Hermes with the given prompt.
        This is a placeholder - replace with actual Hermes execution.
        """
        # Placeholder for actual Hermes execution
        # In production, this would call the actual Hermes agent
        result = f"Hermes processed: {prompt[:100]}..."
        return result
    
    def post_status(self, status: str, details: dict = None):
        """Post a status update to Discord."""
        fields = None
        if details:
            fields = {k: str(v) for k, v in details.items()}
        
        post_embed(
            title=f"🔱 {self.agent_name} Status Update",
            description=status,
            color=0x3498db,  # Blue
            fields=fields,
            webhook_url=self.webhook_url
        )
    
    def post_plan(self, plan: str, tasks: list = None):
        """Post a plan to Discord."""
        fields = None
        if tasks:
            fields = {"Tasks": "\n".join(f"• {t}" for t in tasks[:10])}
        
        post_embed(
            title=f"📋 {self.agent_name} - New Plan",
            description=plan[:4000],  # Discord limit
            color=0x9b59b6,  # Purple
            fields=fields,
            webhook_url=self.webhook_url
        )
    
    def post_architecture_decision(self, decision: str, rationale: str):
        """Post an architecture decision to Discord."""
        post_embed(
            title=f"🏛️ {self.agent_name} - Architecture Decision",
            description=f"**Decision:** {decision}\n\n**Rationale:** {rationale}",
            color=0xe74c3c,  # Red
            webhook_url=self.webhook_url
        )
    
    def post_question(self, question: str, context: str = None):
        """Post a question to Discord for team input."""
        description = question
        if context:
            description += f"\n\n**Context:** {context}"
        
        post_embed(
            title=f"❓ {self.agent_name} - Question",
            description=description,
            color=0xf39c12,  # Orange
            webhook_url=self.webhook_url
        )


def main():
    """Main entry point for Hermes Discord agent."""
    agent = HermesDiscordAgent()
    
    # Example usage
    agent.post_status(
        "Hermes agent initialized and ready",
        {"Workspace": str(agent.workspace_path), "Status": "Online"}
    )


if __name__ == "__main__":
    main()