# OC2 Debugging Notes — 2026-06-06

## Problem
OC2 Telegram bot (`@OC2BLRBOT`) not responding to messages. Shows "typing" but never delivers a reply. Every new session immediately fails with "⚠️ Something went wrong while processing your request."

## Root Cause (IDENTIFIED)
The OpenClaw gateway's agent loop is failing before it gets to the actual LLM model call. The error is:
```
FailoverError: Unknown model: inclusionai/ring-2.6-1t
Found agents.defaults.models["inclusionai/ring-2.6-1t"], but no matching models.providers["inclusionai"].models[] entry.
```

The model `inclusionai/ring-2.6-1t` is configured under `openrouter` provider, but OpenClaw's model resolver expects a provider named `inclusionai` (matching the model prefix). Since there's no `inclusionai` provider — only `openrouter` — it fails.

## What Was Working
- OC2 was working at 10:21 AM on 2026-06-06
- The config file (`.openclaw-2/openclaw.json`) was last changed in commit `8f6bf3ed6` at 10:49 PM on June 5
- The config has `inclusionai/ring-2.6-1t` under `openrouter` provider's models list
- The `agents.defaults.model` is set to `inclusionai/ring-2.6-1t`

## All Attempts Made (Chronological)

### 1. Killed and restarted OC2 gateway multiple times
- Result: Same error. New sessions always fail immediately.

### 2. Changed model from `inclusionai/ring-2.6-1t` to `openrouter/auto`
- Result: Same error. The `agents.defaults.models` alias still referenced `inclusionai/ring-2.6-1t`.

### 3. Clean reinstall of OpenClaw (`npm uninstall -g openclaw && npm install -g openclaw`)
- Result: Same error. The config file was not changed by the reinstall.

### 4. Ran `openclaw doctor --fix`
- Result: Fixed plugin registry, installed missing discord plugin, repaired 7 stale session paths. But the model config issue remained.

### 5. Deleted all session state files (`sessions.json`, `openclaw.sqlite`, `*.jsonl`)
- Result: Same error. New sessions still fail.

### 6. Tried changing `tools.profile` from `coding` to `minimal`
- Result: No effect.

### 7. Tried adding `env` config for UTF-8
- Result: No effect.

### 8. Checked for duplicate bot instances (409 Conflict)
- Found `OpenClaw-1-Gateway` and `OpenClaw-2-Gateway` scheduled tasks
- Disabled `OpenClaw-1-Gateway` but couldn't delete it (access denied)
- Result: 409 Conflict errors stopped, but the model error persisted.

### 9. Checked VTuber integration for conflicts
- VTuber uses different Telegram token — no conflict.

### 10. Verified the model works via direct API call
- `inclusionai/ring-2.6-1t` responds correctly when called directly via OpenRouter API.
- Result: The model itself works. The issue is OpenClaw's model resolution.

## What Has NOT Been Tried
1. **Adding an `inclusionai` provider** to `models.providers` with the model registered
2. **Changing the model to `openrouter/auto`** AND removing the `inclusionai/ring-2.6-1t` alias from `agents.defaults.models`
3. **Restoring the config from git** (`git checkout 8f6bf3ed6 -- .openclaw-2/openclaw.json`) — the config was the same then, so this won't help
4. **Checking if OpenClaw version 2026.6.1 changed model resolution behavior** — the reinstall may have introduced a new model resolution requirement

## Key Insight
The config was working before (at 10:21 AM today). Something changed between then and now. The most likely cause is:
- The OpenClaw reinstall (version 2026.6.1) changed how model resolution works
- OR the `openclaw doctor --fix` changed something in the config that broke model resolution

## Recommended Next Steps
1. Check what the config looked like when it was working (compare with git history)
2. Add an `inclusionai` provider to `models.providers` with the model registered
3. Or change the default model to `openrouter/auto` and remove all references to `inclusionai/ring-2.6-1t`
4. Check OpenClaw changelog for version 2026.6.1 to see if model resolution changed
