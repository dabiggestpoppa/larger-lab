"""Test send to Hermes bot to debug delivery."""
import os
import json
import requests
from pathlib import Path

# Read Hermes token
env_path = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\.env")
token = None
chat_id = "8258195396"  # from log

if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("HERMES_TELEGRAM_TOKEN="):
            token = line.split("=", 1)[1].strip()
            break

print(f"Token: {token[:10] if token else 'NOT FOUND'}...")
print(f"Chat ID: {chat_id}")
print()

if not token:
    raise SystemExit("No token")

# Test 1: Plain text (no markdown)
print("=== Test 1: Plain text ===")
r = requests.post(
    f"https://api.telegram.org/bot{token}/sendMessage",
    json={"chat_id": chat_id, "text": "Test from outside: plain text works"},
    timeout=10
)
print(f"  Status: {r.status_code}")
print(f"  Response: {r.json()}")

# Test 2: Markdown
print()
print("=== Test 2: Markdown ===")
r = requests.post(
    f"https://api.telegram.org/bot{token}/sendMessage",
    json={
        "chat_id": chat_id,
        "text": "*Bold* and _italic_ `code`",
        "parse_mode": "Markdown",
    },
    timeout=10
)
print(f"  Status: {r.status_code}")
print(f"  Response: {r.json()}")

# Test 3: Markdown with potentially-broken characters
print()
print("=== Test 3: Markdown with special chars ===")
r = requests.post(
    f"https://api.telegram.org/bot{token}/sendMessage",
    json={
        "chat_id": chat_id,
        "text": "Reply with * asterisk and _ underscore.",
        "parse_mode": "Markdown",
    },
    timeout=10
)
print(f"  Status: {r.status_code}")
print(f"  Response: {r.json()}")
