#!/usr/bin/env python3
"""Test Telegram API connectivity from this machine."""
import requests
import socket

print("=== Telegram API Connectivity Test ===\n")

# Test 1: DNS resolution
try:
    ip = socket.gethostbyname("api.telegram.org")
    print(f"[OK] DNS: api.telegram.org -> {ip}")
except Exception as e:
    print(f"[FAIL] DNS: {e}")

# Test 2: HTTPS connection
try:
    r = requests.get("https://api.telegram.org", timeout=10)
    print(f"[OK] HTTPS: status {r.status_code}")
except Exception as e:
    print(f"[FAIL] HTTPS: {type(e).__name__}: {e}")

# Test 3: Bot API endpoint
token = "8945439460:AAHZT2Xx0jHaApejRJYi-xORG5FkKNAQ5yM"
try:
    r = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10)
    data = r.json()
    if data.get("ok"):
        bot_name = data["result"]["username"]
        print(f"[OK] Bot API: @{bot_name} reachable")
    else:
        print(f"[FAIL] Bot API: {data}")
except Exception as e:
    print(f"[FAIL] Bot API: {type(e).__name__}: {e}")

# Test 4: getUpdates (what OpenClaw polling uses)
try:
    r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=15, params={"timeout": 5, "limit": 1})
    data = r.json()
    if data.get("ok"):
        updates = data.get("result", [])
        print(f"[OK] getUpdates: working ({len(updates)} pending)")
    else:
        print(f"[FAIL] getUpdates: {data}")
except Exception as e:
    print(f"[FAIL] getUpdates: {type(e).__name__}: {e}")

# Test 5: Check proxy / firewall
import os
http_proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
https_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
print(f"\nProxy settings: HTTP_PROXY={http_proxy}, HTTPS_PROXY={https_proxy}")

# Test 6: Try alternative Telegram IPs
alt_hosts = ["149.154.167.99", "149.154.167.100", "149.154.167.200"]
for host in alt_hosts:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, 443))
        sock.close()
        if result == 0:
            print(f"[OK] TCP connect to {host}:443 — reachable")
        else:
            print(f"[FAIL] TCP connect to {host}:443 — blocked (error {result})")
    except Exception as e:
        print(f"[FAIL] TCP connect to {host}:443 — {e}")

print("\n=== Done ===")
