"""Fix OC2 config cleanly - use openrouter/owl-alpha."""
import json

cfg_path = r"C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2\openclaw.json"
with open(cfg_path, encoding="utf-8") as f:
    cfg = json.load(f)

# Set model to openrouter/owl-alpha
cfg["agents"]["defaults"]["model"] = "openrouter/owl-alpha"

# Remove inclusionai/ring-2.6-1t alias if present
models = cfg["agents"]["defaults"].get("models", {})
if "inclusionai/ring-2.6-1t" in models:
    del models["inclusionai/ring-2.6-1t"]
if "openrouter/auto" in models:
    del models["openrouter/auto"]
# Keep only owl-alpha and other safe aliases
cfg["agents"]["defaults"]["models"] = {
    "openrouter/owl-alpha": {"alias": "owl"},
    "minimax/minimax-m3": {"alias": "minimax"},
    "nvidia/nemotron-3-ultra-550b-a55b": {"alias": "nemotron"}
}

# Make sure openrouter provider has owl-alpha model
openrouter_models = cfg["models"]["providers"]["openrouter"]["models"]
has_owl = any(m.get("id") == "openrouter/owl-alpha" for m in openrouter_models)
if not has_owl:
    openrouter_models.append({"id": "openrouter/owl-alpha", "name": "openrouter/owl-alpha"})

# Remove inclusionai provider if it was added earlier
if "inclusionai" in cfg["models"]["providers"]:
    del cfg["models"]["providers"]["inclusionai"]

with open(cfg_path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2)

print("Config cleaned:")
print(f"  Model: {cfg['agents']['defaults']['model']}")
print(f"  Aliases: {list(cfg['agents']['defaults']['models'].keys())}")
print(f"  OpenRouter models: {[m['id'] for m in cfg['models']['providers']['openrouter']['models']]}")
print(f"  Providers: {list(cfg['models']['providers'].keys())}")
