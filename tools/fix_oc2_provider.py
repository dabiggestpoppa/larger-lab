"""Fix OC2 model provider config."""
import json

cfg_path = r"C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2\openclaw.json"
with open(cfg_path, encoding="utf-8") as f:
    cfg = json.load(f)

# Set model to inclusionai/ring-2.6-1t
cfg["agents"]["defaults"]["model"] = "inclusionai/ring-2.6-1t"

# Add inclusionai provider with the model
cfg["models"]["providers"]["inclusionai"] = {
    "baseUrl": "https://openrouter.ai/api/v1",
    "apiKey": "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",
    "models": [
        {
            "id": "ring-2.6-1t",
            "name": "inclusionai/ring-2.6-1t"
        }
    ]
}

# Update models alias
cfg["agents"]["defaults"]["models"]["inclusionai/ring-2.6-1t"] = {"alias": "ring"}

with open(cfg_path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2)

print("Fixed: Added inclusionai provider with ring-2.6-1t model")
print("Default model set to: inclusionai/ring-2.6-1t")
