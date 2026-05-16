"""
Quick setup script for separate Discord bots.
"""

import os
import subprocess
from pathlib import Path


def main():
    """Run the quick setup."""
    print("🚀 Setting up Separate Discord Bots for Hermes & OpenClaw...")
    
    # Check for .env
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        print("❌ .env file not found")
        return
    
    # Check for bot tokens
    with open(env_path) as f:
        content = f.read()
    
    has_hermes = "DISCORD_HERMES_TOKEN" in content and "your_hermes_bot_token_here" not in content
    has_openclaw = "DISCORD_OPENCLAW_TOKEN" in content and "your_openclaw_bot_token_here" not in content
    
    print("\n📋 Bot Token Status:")
    print(f"  Hermes Bot: {'✅ Configured' if has_hermes else '⚠️  Not configured'}")
    print(f"  OpenClaw Bot: {'✅ Configured' if has_openclaw else '⚠️  Not configured'}")
    
    if not has_hermes or not has_openclaw:
        print("\n📝 To configure:")
        print("  1. Go to https://discord.com/developers/applications")
        print("  2. Create two bot applications (Hermes & OpenClaw)")
        print("  3. Copy tokens to .env:")
        print("     DISCORD_HERMES_TOKEN=your_hermes_token")
        print("     DISCORD_OPENCLAW_TOKEN=your_openclaw_token")
    
    print("\n📦 Installing dependencies...")
    subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True)
    
    print("\n✅ Setup complete!")
    print("\nTo run the bots:")
    print("  python hermes_bot.py     # Terminal 1")
    print("  python openclaw_bot.py   # Terminal 2")


if __name__ == "__main__":
    main()