# Context Monitor Skill

> **Purpose:** Monitor session context usage and alert when approaching limit.
> **Trigger:** Check context after every response. Alert at 75% threshold.

## Context Limits by Model

| Model | Max Tokens | 75% Warning | 90% Critical |
|-------|-----------|-------------|--------------|
| openrouter/owl-alpha | 1,000,000 | 750,000 | 900,000 |
| openrouter/anthropic/claude-sonnet-4 | 200,000 | 150,000 | 180,000 |
| deepseek/deepseek-v4-flash:free | 128,000 | 96,000 | 115,200 |
| nvidia/nemotron-3-nano-omni | 128,000 | 96,000 | 115,200 |
| poolside/laguna-m.1:free | 32,000 | 24,000 | 28,800 |

## Behavior

### After Every Response
1. Check `contextTokens` from session state
2. Calculate percentage of model's max context
3. If ≥ 75%: Send warning message to user
4. If ≥ 90%: Send critical alert + suggest new session

### Warning Message (75%)
```
⚠️ Context Warning: {model} session at {used}/{max} tokens ({pct}%)

Session: {session_key}
Model: {model}

Recommendation: Start a new session soon to avoid context overflow.
Reply /new to start a fresh session.
```

### Critical Message (90%)
```
🚨 Context Critical: {model} session at {used}/{max} tokens ({pct}%)

Session will be truncated soon. Start a new session NOW.
Reply /new to start a fresh session.
```

### Auto-Compaction (95%)
At 95%, automatically:
1. Summarize the session so far
2. Save summary to `logs/session-summaries/`
3. Start a new session with the summary as context
4. Notify user of the transition

## Session State Location
- Sessions file: `.openclaw-2/.openclaw/agents/main/sessions/sessions.json`
- Each session has: `contextTokens`, `model`, `status`

## Implementation
This skill runs as part of the agent's post-response hook.
It reads the session state file and sends alerts via Telegram DM.
