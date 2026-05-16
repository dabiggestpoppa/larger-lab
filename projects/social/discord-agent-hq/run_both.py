"""
Run both Hermes and OpenClaw bots simultaneously.
Needs: DISCORD_HERMES_TOKEN and DISCORD_OPENCLAW_TOKEN in .env
"""

import subprocess, sys, os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

hermes_token = os.getenv("DISCORD_HERMES_TOKEN")
openclaw_token = os.getenv("DISCORD_OPENCLAW_TOKEN")

if not hermes_token or "your_hermes" in hermes_token:
    print("❌ DISCORD_HERMES_TOKEN not configured in .env")
    print("   Create a bot at https://discord.com/developers/applications")
    sys.exit(1)

if not openclaw_token or "your_openclaw" in openclaw_token:
    print("❌ DISCORD_OPENCLAW_TOKEN not configured in .env")
    print("   Create a bot at https://discord.com/developers/applications")
    sys.exit(1)

print("🔱 Starting Hermes bot...")
print("🦀 Starting OpenClaw bot...")

# Start both bots as separate processes
p1 = subprocess.Popen([sys.executable, str(Path(__file__).parent / "hermes_bot.py")])
p2 = subprocess.Popen([sys.executable, str(Path(__file__).parent / "openclaw_bot.py")])

print("\n✅ Both bots running! Press Ctrl+C to stop.")
try:
    p1.wait()
    p2.wait()
except KeyboardInterrupt:
    print("\n🛑 Stopping bots...")
    p1.terminate()
    p2.terminate()
    print("✅ Bots stopped.")
