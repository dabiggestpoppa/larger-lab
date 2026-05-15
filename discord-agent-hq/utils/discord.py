"""
Discord utility module for agent communication.
Provides helpers for posting messages and embeds to Discord channels.
"""

import os
import json
import requests
from typing import Optional, Dict, Any
from pathlib import Path


# Configuration - loaded from environment
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")


def post_text(
    content: str,
    username: Optional[str] = None,
    avatar_url: Optional[str] = None,
    webhook_url: Optional[str] = None
) -> None:
    """
    Send a plain text message to Discord via webhook.
    
    Args:
        content: The message content to send
        username: Optional custom username for the webhook
        avatar_url: Optional custom avatar URL for the webhook
        webhook_url: Optional override webhook URL (uses env var if not provided)
    """
    url = webhook_url or WEBHOOK_URL
    if not url:
        raise ValueError("DISCORD_WEBHOOK_URL not set and no webhook_url provided")
    
    payload = {"content": content}
    if username:
        payload["username"] = username
    if avatar_url:
        payload["avatar_url"] = avatar_url
    
    response = requests.post(url, json=payload)
    response.raise_for_status()


def post_embed(
    title: str,
    description: str,
    color: int = 0x0099ff,
    fields: Optional[Dict[str, Any]] = None,
    image_url: Optional[str] = None,
    webhook_url: Optional[str] = None
) -> None:
    """
    Send an embed message to Discord via webhook.
    
    Args:
        title: Embed title
        description: Embed description
        color: Embed color (hex as int, default blue)
        fields: Optional dict of field name -> value mappings
        image_url: Optional image URL to include
        webhook_url: Optional override webhook URL
    """
    url = webhook_url or WEBHOOK_URL
    if not url:
        raise ValueError("DISCORD_WEBHOOK_URL not set and no webhook_url provided")
    
    embed = {
        "title": title,
        "description": description,
        "color": color,
        "timestamp": __import__('datetime').datetime.utcnow().isoformat() + "Z"
    }
    
    if fields:
        embed["fields"] = [
            {"name": k, "value": v, "inline": True}
            for k, v in fields.items()
        ]
    
    if image_url:
        embed["image"] = {"url": image_url}
    
    payload = {"embeds": [embed]}
    response = requests.post(url, json=payload)
    response.raise_for_status()


def post_file(
    content: str,
    file_path: Path,
    filename: Optional[str] = None,
    webhook_url: Optional[str] = None
) -> None:
    """
    Send a message with a file attachment to Discord.
    
    Args:
        content: Message content
        file_path: Path to the file to attach
        filename: Optional custom filename (uses file_path.name if not provided)
        webhook_url: Optional override webhook URL
    """
    url = webhook_url or WEBHOOK_URL
    if not url:
        raise ValueError("DISCORD_WEBHOOK_URL not set and no webhook_url provided")
    
    filename = filename or file_path.name
    
    with open(file_path, 'rb') as f:
        files = {'file': (filename, f)}
        data = {'payload_json': json.dumps({"content": content})}
        response = requests.post(url, data=data, files=files)
    
    response.raise_for_status()


def get_agent_webhook(agent_name: str) -> Optional[str]:
    """
    Get the webhook URL for a specific agent from environment.
    
    Args:
        agent_name: Name of the agent (e.g., 'HERMES', 'OPENCLAW')
    
    Returns:
        Webhook URL or None if not configured
    """
    return os.getenv(f"DISCORD_WEBHOOK_{agent_name.upper()}")