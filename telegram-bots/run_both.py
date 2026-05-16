"""
Run both Hermes and OpenClaw Telegram bots simultaneously.
"""

import subprocess, sys
from pathlib import Path

bot_dir = Path(__file__).parent

print("🔱 Starting Hermes bot...")
print("🦀 Starting OpenClaw bot...")

p1 = subprocess.Popen([sys.executable, str(bot_dir / "hermes_bot.py")])
p2 = subprocess.Popen([sys.executable, str(bot_dir / "openclaw_bot.py")])

print("\n✅ Both bots running! Press Ctrl+C to stop.")
print("   Hermes:  @hermesbebblrbot")
print("   OpenClaw: @goatclaw999")
try:
    p1.wait()
    p2.wait()
except KeyboardInterrupt:
    print("\n🛑 Stopping bots...")
    p1.terminate()
    p2.terminate()
    print("✅ Bots stopped.")
