# OC2 Debugging Notes — 2026-06-06 (FINAL)

## Problem
OC2 Telegram bot not responding. "Something went wrong" on every new session.

## Root Cause
OpenClaw 2026.6.1 changed model resolution. Model `inclusionai/ring-2.6-1t` is under `openrouter` provider but OpenClaw now expects provider name `inclusionai`. Also, OpenClaw overwrites config on startup reverting any model changes.

## All 11 Attempts (ALL FAILED)
1. Kill/restart gateway — same error
2. Change model to openrouter/auto — config reverted
3. Clean reinstall — same error (new version broke model resolution)
4. openclaw doctor --fix — fixed plugins only
5. Delete session state — same error
6. Change tools.profile — no effect
7. Add inclusionai provider — stripped by OpenClaw
8. Set model to owl-alpha — config reverted
9. Read-only config — OpenClaw couldn't start
10. Disable duplicate scheduled tasks — helped but didn't fix model
11. Remove alias from models — config reverted

## Key Discovery
OpenClaw 2026.6.1 overwrites config on ANY startup. Model always reverts to inclusionai/ring-2.6.1t.

## NOT YET TRIED
- openclaw config set CLI command
- Add inclusionai provider with baseUrl pointing to OpenRouter
- Downgrade OpenClaw

## Status 7:20 PM
- PO Bot: OK
- Hermes Bot: OK
- OC2 Bot: Online but not responding

## Lessons
- Don't change models without asking
- Don't kill/restart repeatedly
- OpenClaw 2026.6.1 has config overwrite bug
- Persistent debug log is critical
