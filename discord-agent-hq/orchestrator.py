"""
Agent Team Orchestrator - Coordinates Hermes and OpenClaw agents via Discord.
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

from agents.hermes import HermesDiscordAgent
from agents.openclaw import OpenClawDiscordAgent
from utils.discord import post_text, post_embed


class AgentTeamOrchestrator:
    """
    Orchestrates communication between Hermes and OpenClaw agents.
    Manages task delegation and status reporting via Discord.
    """
    
    def __init__(self, workspace_path: str = None):
        self.workspace_path = Path(workspace_path or os.getenv("WORKSPACE_PATH", "."))
        self.hermes = HermesDiscordAgent(str(self.workspace_path))
        self.openclaw = OpenClawDiscordAgent(str(self.workspace_path))
        self.tasks: Dict[str, dict] = {}
        self.webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    def assign_task(self, agent: str, task: str, details: dict = None) -> str:
        """
        Assign a task to an agent.
        
        Args:
            agent: Agent name ('hermes' or 'openclaw')
            task: Task description
            details: Optional task details
        
        Returns:
            Task ID
        """
        task_id = f"task-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        self.tasks[task_id] = {
            "agent": agent,
            "task": task,
            "details": details or {},
            "status": "assigned",
            "created_at": datetime.now().isoformat()
        }
        
        # Post to Discord
        post_embed(
            title=f"📋 Task Assigned to {agent.title()}",
            description=f"**Task:** {task}",
            color=0x9b59b6,  # Purple
            fields=details,
            webhook_url=self.webhook_url
        )
        
        return task_id
    
    def update_task_status(self, task_id: str, status: str, result: str = None):
        """Update the status of a task."""
        if task_id not in self.tasks:
            return
        
        self.tasks[task_id]["status"] = status
        self.tasks[task_id]["updated_at"] = datetime.now().isoformat()
        if result:
            self.tasks[task_id]["result"] = result
        
        post_embed(
            title=f"📊 Task Update: {task_id}",
            description=f"**Status:** {status}\n\n**Result:** {result or 'N/A'}",
            color=0x3498db,  # Blue
            webhook_url=self.webhook_url
        )
    
    def get_team_status(self) -> dict:
        """Get the current status of all agents."""
        return {
            "hermes": {
                "status": "online",
                "last_update": datetime.now().isoformat()
            },
            "openclaw": {
                "status": "online",
                "last_update": datetime.now().isoformat()
            },
            "active_tasks": len([t for t in self.tasks.values() if t["status"] != "completed"])
        }
    
    def post_team_status(self):
        """Post team status to Discord."""
        status = self.get_team_status()
        
        post_embed(
            title="🏢 Agent Team Status",
            description="Current status of all agents",
            color=0x2ecc71,  # Green
            fields={
                "Hermes": status["hermes"]["status"],
                "OpenClaw": status["openclaw"]["status"],
                "Active Tasks": str(status["active_tasks"])
            },
            webhook_url=self.webhook_url
        )
    
    async def run_daily_standup(self):
        """Run a daily standup with all agents."""
        post_embed(
            title="📋 Daily Standup",
            description="Time for our daily agent standup!",
            color=0xf39c12,  # Orange
            webhook_url=self.webhook_url
        )
        
        # Hermes standup
        self.hermes.post_status(
            "Planning today's architecture decisions",
            {"Focus": "System design and coordination"}
        )
        
        # OpenClaw standup
        self.openclaw.post_status(
            "Ready to implement today's tasks",
            {"Focus": "Building and execution"}
        )


def main():
    """Main entry point for the orchestrator."""
    orchestrator = AgentTeamOrchestrator()
    
    # Example task assignment
    task_id = orchestrator.assign_task(
        "openclaw",
        "Set up Discord agent communication system",
        {"Priority": "High", "Deadline": "Today"}
    )
    
    print(f"Task assigned: {task_id}")


if __name__ == "__main__":
    main()