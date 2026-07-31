"""Fix OC2 config - nuclear option.
Remove ALL model aliases and set a single working model.
Write the file as read-only to prevent OpenClaw from modifying it.
"""
import json
import os
import stat

cfg_path = r"C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2\openclaw.json"
with open(cfg_path, encoding="utf-8") as f:
    cfg = json.load(f)

# Set model to openrouter/auto (known working)
cfg["agents"]["defaults"]["model"] = "openrouter/auto"

# Remove ALL model aliases
cfg["agents"]["defaults"]["models"] = {}

# Remove all providers except openrouter
cfg["models"]["providers"] = {
    "openrouter": {
        "baseUrl": "https://openrouter.ai/api/v1",
        "apiKey": cfg["models"]["providers"]["openrouter"]["apiKey"],
        "models": [
            {"id": "openrouter/auto", "name": "openrouter/auto"}
        ]
    }
}

# Remove meta section that might have cached state
cfg.pop("meta", None)

with open(cfg_path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2)

# Make file read-only to prevent OpenClaw from modifying it
os.chmod(cfg_path, stat.S_IRUSR | stat.S_IWUSR)

# Verify
with open(cfg_path, encoding="utf-8") as f:
    cfg2 = json.load(f)

print(f"Model: {cfg2['agents']['defaults']['model']}")
print(f"Aliases: {list(cfg2['agents']['defaults']['models'].keys())}")
print(f"Providers: {list(cfg2['models']['providers'].keys())}")
print(f"OpenRouter models: {[m['id'] for m in cfg2['models']['providers']['openrouter']['models']]}")
print("File set to read-only")
