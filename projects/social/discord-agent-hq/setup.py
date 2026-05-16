"""
Quick setup script for Discord Agent Communication System.
"""

import os
import subprocess
from pathlib import Path


def main():
    """Run the quick setup."""
    print("🚀 Setting up Discord Agent Communication System...")
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True)
    
    # Check for .env configuration
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        print("\n✅ .env file found")
        with open(env_path) as f:
            content = f.read()
            if "DISCORD_BOT_TOKEN" in content and "your_discord_bot_token_here" not in content:
                print("✅ Discord configuration detected")
            else:
                print("⚠️  Please configure Discord credentials in .env")
    else:
        print("⚠️  .env file not found")
    
    print("\n✨ Setup complete!")
    print("\nNext steps:")
    print("1. Configure your Discord bot token in .env")
    print("2. Run: python discord_bot.py")
    print("3. Or with Docker: docker-compose up -d")


if __name__ == "__main__":
    main()