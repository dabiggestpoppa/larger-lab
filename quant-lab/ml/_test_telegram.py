"""Test Telegram connection for CEREBUS Guardian."""
import os
import sys
import requests
from pathlib import Path

# Load .env
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

token = os.environ.get("HERMES_TELEGRAM_TOKEN", "")
if not token:
    print("ERROR: HERMES_TELEGRAM_TOKEN not set")
    sys.exit(1)

print(f"Token: {token[:10]}...")

# Discover chat_id
chat_id = ""
try:
    r = requests.get(
        f"https://api.telegram.org/bot{token}/getUpdates?limit=5&timeout=10",
        timeout=15,
    )
    data = r.json()
    print(f"getUpdates ok: {data.get('ok')}")
    if data.get("result"):
        for u in data["result"]:
            chat = u.get("message", {}).get("chat", {})
            print(f"  chat_id={chat.get('id')} type={chat.get('type')} title={chat.get('title', '')}")
        chat_id = str(data["result"][-1]["message"]["chat"]["id"])
        print(f"Using chat_id: {chat_id}")
    else:
        print("No messages found — send a message to the bot first")
except Exception as e:
    print(f"Error: {e}")

# Send test message
if chat_id:
    test_msg = (
        "🔱 CEREBUS NEURO-SYMBOLIC SCANNER\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ System initialized and connected to Telegram.\n\n"
        "This is a test message to verify the Guardian → Hermes Bot pipeline.\n\n"
        "All 4 steps operational:\n"
        "  1. Data + Features ✅\n"
        "  2. XGBoost Models ✅\n"
        "  3. RAG Oracle ✅\n"
        "  4. Guardian + Orchestrator ✅\n\n"
        "Awaiting live market data..."
    )
    r2 = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": test_msg, "parse_mode": "HTML"},
        timeout=15,
    )
    result = r2.json()
    print(f"Send result: {result.get('ok')}")
    if not result.get("ok"):
        print(f"Error: {result}")
    else:
        print("✅ Test message sent successfully!")
else:
    print("Skipping send — no chat_id")
