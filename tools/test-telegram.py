"""Quick Telegram API connectivity test."""
import urllib.request, json, time, sys

token = "8945439460:AAHZT2Xx0jHaApejRJYi-xORG5FkKNAQ5yM"
base = f"https://api.telegram.org/bot{token}"

# Test 1: getMe
try:
    start = time.time()
    req = urllib.request.Request(f"{base}/getMe")
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
        elapsed = time.time() - start
        print(f"getMe: OK ({elapsed:.2f}s) - @{data['result']['username']}")
except Exception as e:
    elapsed = time.time() - start
    print(f"getMe: FAIL ({elapsed:.2f}s) - {e}")

# Test 2: sendMessage
try:
    start = time.time()
    payload = json.dumps({"chat_id": 8258195396, "text": "OC2 heartbeat test"}).encode()
    req = urllib.request.Request(f"{base}/sendMessage", data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
        elapsed = time.time() - start
        print(f"sendMessage: OK ({elapsed:.2f}s) - msg_id={data['result']['message_id']}")
except Exception as e:
    elapsed = time.time() - start
    print(f"sendMessage: FAIL ({elapsed:.2f}s) - {e}")

# Test 3: setMyCommands
try:
    start = time.time()
    payload = json.dumps({"commands": []}).encode()
    req = urllib.request.Request(f"{base}/setMyCommands", data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
        elapsed = time.time() - start
        print(f"setMyCommands: OK ({elapsed:.2f}s)")
except Exception as e:
    elapsed = time.time() - start
    print(f"setMyCommands: FAIL ({elapsed:.2f}s) - {e}")
