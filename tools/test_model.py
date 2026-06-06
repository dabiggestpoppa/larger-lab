import requests
import json

key = "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"
headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
payload = {
    "model": "inclusionai/ring-2.6-1t",
    "messages": [{"role": "user", "content": "Hello, are you there?"}],
    "max_tokens": 100
}
r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    content = data["choices"][0]["message"]["content"]
    print(f"Response: {content[:200]}")
else:
    print(f"Error: {r.text[:300]}")
