"""Fix OC2 config - remove inclusionai alias and set owl-alpha."""
import json

cfg_path = r"C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2\openclaw.json"
with open(cfg_path, encoding="utf-8") as f:
    cfg = json.load(f)

# Remove the inclusionai/ring-2.6-1t alias completely
models = cfg["agents"]["defaults"].get("models", {})
models.pop("inclusionai/ring-2.6-1t", None)
cfg["agents"]["defaults"]["models"] = models

# Set model to openrouter/owl-alpha
cfg["agents"]["defaults"]["model"] = "openrouter/owl-alpha"

with open(cfg_path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2)

# Verify
with open(cfg_path, encoding="utf-8") as f:
    cfg2 = json.load(f)

print(f"Model: {cfg2['agents']['defaults']['model']}")
print(f"Aliases: {list(cfg2['agents']['defaults']['models'].keys())}")
