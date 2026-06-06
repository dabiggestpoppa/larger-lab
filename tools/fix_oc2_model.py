"""Fix OC2 model config - change to openrouter/auto."""
import json

cfg_path = r"C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2\openclaw.json"
with open(cfg_path, encoding="utf-8") as f:
    cfg = json.load(f)

old_model = cfg["agents"]["defaults"]["model"]
cfg["agents"]["defaults"]["model"] = "openrouter/auto"

# Also update the models alias
models = cfg["agents"]["defaults"].get("models", {})
if "inclusionai/ring-2.6-1t" in models:
    del models["inclusionai/ring-2.6-1t"]
models["openrouter/auto"] = {"alias": "auto"}
cfg["agents"]["defaults"]["models"] = models

with open(cfg_path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2)

print(f"Changed model from {old_model} to openrouter/auto")
