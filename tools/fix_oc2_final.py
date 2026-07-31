"""Fix OC2 config - final attempt.
The issue: OpenClaw 2026.6.1 changed model resolution.
Model prefix must match a provider name.
inclusionai/ring-2.6-1t -> needs 'inclusionai' provider (doesn't exist)
openrouter/owl-alpha -> needs 'openrouter' provider (exists)

Fix: Change default model to openrouter/owl-alpha
"""
import json

cfg_path = r"C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2\openclaw.json"
with open(cfg_path, encoding="utf-8") as f:
    cfg = json.load(f)

# Change default model to openrouter/owl-alpha
cfg["agents"]["defaults"]["model"] = "openrouter/owl-alpha"

# Clean up models aliases - remove inclusionai reference
models = cfg["agents"]["defaults"].get("models", {})
models.pop("inclusionai/ring-2.6-1t", None)
models.pop("openrouter/auto", None)
models.pop("google/gemini-2.5-flash", None)
cfg["agents"]["defaults"]["models"] = models

# Make sure openrouter provider has owl-alpha
or_models = cfg["models"]["providers"]["openrouter"]["models"]
has_owl = any(m.get("id") == "openrouter/owl-alpha" for m in or_models)
if not has_owl:
    or_models.append({"id": "openrouter/owl-alpha", "name": "openrouter/owl-alpha"})

# Remove inclusionai from openrouter models list (it was never a real openrouter model)
or_models = [m for m in or_models if m.get("id") != "inclusionai/ring-2.6-1t"]
cfg["models"]["providers"]["openrouter"]["models"] = or_models

with open(cfg_path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2)

print("Config fixed:")
print(f"  Model: {cfg['agents']['defaults']['model']}")
print(f"  Aliases: {list(cfg['agents']['defaults']['models'].keys())}")
print(f"  OpenRouter models: {[m['id'] for m in cfg['models']['providers']['openrouter']['models']]}")
