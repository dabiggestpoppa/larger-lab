# OC2 Debugging — 2026-06-06

## Problem
OC2 Telegram bot not responding. "Something went wrong" error on every new session.

## Root Cause
`FailoverError: Unknown model: inclusionai/ring-2.6-1t` — model listed under `openrouter` provider but OpenClaw expects provider named `inclusionai`.

## What Didn't Work
- Killing/restarting gateway repeatedly
- Changing model to openrouter/auto
- Clean reinstall of OpenClaw
- Running openclaw doctor --fix
- Deleting session state files
- Disabling duplicate scheduled tasks

## What Needs To Be Tried
1. Add `inclusionai` provider to models.providers with model registered
2. Or change default model to openrouter/auto AND remove inclusionai alias
3. Check if OpenClaw 2026.6.1 changed model resolution

## Lessons Learned
- Don't change models without asking user
- Don't kill/restart gateway repeatedly
- Config was working at 10:21 AM — reinstall likely changed model resolution
