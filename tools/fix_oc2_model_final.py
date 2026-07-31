"""Fix OC2 model config - remove broken inclusionai model reference."""
import json

cfg_path = r"C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2\openclaw.json"
with open(cfg_path, encoding="utf-8") as f:
    cfg = json.load(f)

# Remove the broken model alias
models = cfg["agents"]["defaults"].get("models", {})
if "inclusionai/ring-2.6-1t" in models:
    del models["inclusionai/ring-2.6-1t"]
    print("Removed broken inclusionai/ring-2.6-1t alias")

# Ensure openrouter/auto is in the aliases
models["openrouter/auto"] = {"alias": "auto"}
cfg["agents"]["defaults"]["models"] = models

# Also remove inclusionai/ring-2.6-1t from openrouter provider models list
# since it's not a valid openrouter model ID
providers = cfg["models"]["providers"]
if "openrouter" in providers:
    openrouter_models = providers["openrouter"].get("models", [])
    original_count = len(openrouter_models)
    openrouter_models = [m for m in openrouter_models if m.get("id") != "inclusionai/ring-2.6-1t"]
    providers["openrouter"]["models"] = openrouter_models
    removed = original_count - len(openrouter_models)
    if removed:
        print(f"Removed {removed} broken model(s) from openrouter provider")

with open(cfg_path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2)

print("Fixed openclaw.json")
