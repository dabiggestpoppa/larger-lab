"""Check if OC2's model is available on OpenRouter."""
import json
import requests

key = "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"
headers = {"Authorization": f"Bearer {key}"}

# Check the specific model
model = "inclusionai/ring-2.6-1t"
r = requests.get(f"https://openrouter.ai/api/v1/models/{model}", headers=headers, timeout=10)
print(f"Model check status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Model: {data.get('id')}")
    print(f"Available: {data.get('available', 'unknown')}")
    print(f"Context length: {data.get('context_length', 'unknown')}")
else:
    print(f"Error: {r.text[:300]}")

# List available models with "ring" in name
r2 = requests.get("https://openrouter.ai/api/v1/models", headers=headers, timeout=10)
if r2.status_code == 200:
    models = r2.json().get("data", [])
    for m in models:
        mid = m.get("id", "")
        if "ring" in mid.lower() or "inclusion" in mid.lower():
            print(f"Found: {mid} available={m.get('available', '?')}")
