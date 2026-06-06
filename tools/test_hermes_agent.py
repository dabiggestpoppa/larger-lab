"""Test Hermes agent directly to see if it actually returns."""
import os
import sys
import time

# Setup paths
sys.path.insert(0, r"C:\Users\wifik\AppData\Local\hermes\hermes-agent")
sys.path.insert(0, r"C:\Users\wifik\Desktop\projects\larger-lab\.venv\Lib\site-packages")

# Load .env
env_path = r"C:\Users\wifik\Desktop\projects\larger-lab\.env"
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

print("=== Test 1: Check OpenRouter key ===")
key = os.environ.get("OPENROUTER_API_KEY", "")
print(f"  Key set: {bool(key)}, length: {len(key)}, prefix: {key[:8] if key else 'NONE'}")

print()
print("=== Test 2: Quick OpenRouter API call ===")
import requests
try:
    r = requests.get(
        "https://openrouter.ai/api/v1/models",
        headers={"Authorization": f"Bearer {key}"} if key else {},
        timeout=10,
    )
    print(f"  Status: {r.status_code}")
    if r.status_code == 200:
        models = r.json().get("data", [])
        print(f"  Available models: {len(models)}")
    else:
        print(f"  Error: {r.text[:300]}")
except Exception as e:
    print(f"  Error: {e}")

print()
print("=== Test 3: AIAgent direct call (with timeout) ===")
import concurrent.futures
from run_agent import AIAgent

agent = AIAgent(
    model="openrouter/owl-alpha",
    provider="openrouter",
    api_key=key,
    base_url="https://openrouter.ai/api/v1",
    platform="telegram",
    user_id="test",
    chat_id="test",
    chat_type="private",
    max_iterations=10,
    tool_delay=0.5,
    quiet_mode=True,
    save_trajectories=False,
    enabled_toolsets=[],
    ephemeral_system_prompt="You are a helpful assistant. Be brief.",
)

messages = [{"role": "user", "content": "YOO"}]

print(f"  Calling agent.run_conversation with 30s timeout...")
start = time.time()
with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
    future = ex.submit(agent.run_conversation, messages)
    try:
        response = future.result(timeout=30)
        elapsed = time.time() - start
        print(f"  Response ({elapsed:.1f}s, {len(response)} chars): {response[:200]}")
    except concurrent.futures.TimeoutError:
        elapsed = time.time() - start
        print(f"  TIMEOUT after {elapsed:.1f}s — agent stuck on OpenRouter call")
    except Exception as e:
        elapsed = time.time() - start
        print(f"  ERROR after {elapsed:.1f}s: {e}")
