"""Fix OC2 model - use openrouter/owl-alpha as fallback."""
import json

cfg_path = r"C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2\openclaw.json"
with open(cfg_path, encoding="utf-8") as f:
    cfg = json.load(f)

# Set model to openrouter/owl-alpha (known working)
cfg["agents"]["defaults"]["model"] = "openrouter/owl-alpha"

# Update models alias
cfg["agents"]["defaults"]["models"]["openrouter/owl-alpha"] = {"alias": "owl"}

with open(cfg_path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2)

print("Changed default model to: openrouter/owl-alpha")
