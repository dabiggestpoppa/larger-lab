"""Fix OC2 config - add inclusionai provider that routes through OpenRouter.
OpenClaw 2026.6.1 requires model prefix to match a provider name.
inclusionai/ring-2.6-1t -> needs 'inclusionai' provider
We'll add it as a separate provider that uses OpenRouter's API.
"""
import json

cfg_path = r"C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2\openclaw.json"
with open(cfg_path, encoding="utf-8") as f:
    cfg = json.load(f)

# Add inclusionai provider that routes through OpenRouter
cfg["models"]["providers"]["inclusionai"] = {
    "baseUrl": "https://openrouter.ai/api/v1",
    "apiKey": cfg["models"]["providers"]["openrouter"]["apiKey"],
    "models": [
        {
            "id": "ring-2.6-1t",
            "name": "inclusionai/ring-2.6-1t"
        }
    ]
}

# Keep the default model as inclusionai/ring-2.6-1t
# (it was working before, the issue is just the provider registration)

with open(cfg_path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2)

print("Added inclusionai provider with ring-2.6-1t model")
print(f"Providers: {list(cfg['models']['providers'].keys())}")
