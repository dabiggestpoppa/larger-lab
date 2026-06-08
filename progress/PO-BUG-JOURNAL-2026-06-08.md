# PO BUG JOURNAL — 2026-06-08

## Issue #1: Watchdog Infinite Restart Loop (CRITICAL)

### Symptoms
- PO Telegram gateway not responding to messages
- Telegram bot (@P01999BOT) appeared dead
- No polling activity despite process being "running"

### Root Cause
**`po_watchdog.py` `is_gateway_running()` used `$_` inside `subprocess.run()` — PowerShell pipeline variable gets stripped by Python string handling.**

The watchdog's detection command:
```powershell
Get-Process -Name python | Where-Object { $_.CommandLine -like '*telegram*' }
```

When passed through `subprocess.run(["powershell", "-Command", "..."])`, the `$_` is consumed/lost, so PowerShell receives:
```powershell
Where-Object { .CommandLine -like '*telegram*' }
```

This throws `.CommandLine not recognized` for every process → always returns empty output → `is_gateway_running()` always returns `False` → watchdog restarts gateway every 60 seconds → gateway never stabilizes → Telegram never polls.

### Evidence
- `po_watchdog.log` shows continuous restart loop: 10 restarts → 5min cooldown → 10 more restarts → repeat
- From 15:58 to 17:13 (75 minutes), the gateway was restarted **40+ times**
- Each restart kills the previous instance, so polling never completes a full cycle
- `telegram-gateway.log` shows polling only worked during brief windows between restarts

### Fix
Replaced broken subprocess PowerShell call with two-tier detection:
1. **Primary:** PID file check using `ctypes.windll.kernel32.OpenProcess` (fast, no subprocess)
2. **Fallback:** `Get-CimInstance Win32_Process` (no `$_` needed)

Also fixed stale PID file — was `13632` (a PowerShell terminal), corrected to `16408` (actual gateway).

### Commit
`b0ee429ed` — `[CEREBUS] Fix PO watchdog — broken $_ in subprocess caused infinite restart loop`

### Related Files
- `scripts/po_watchdog.py` — `is_gateway_running()` function (FIXED)
- `scripts/.telegram_gateway.pid` — PID file (FIXED)
- `logs/po_watchdog.log` — shows the restart loop pattern

---

## Issue #2: Telegram 409 Conflict (VTuber Incident)

### Symptoms
- Telegram API returning `409 Conflict` errors
- Bot unable to poll for messages
- Multiple "Conflict: terminated by other getUpdates request" errors

### Root Cause
**PM connected the Telegram bot (@P01999BOT) to the VTuber/POALA system**, creating two simultaneous polling instances on the same bot token. Telegram only allows one `getUpdates` session per bot token.

Additionally, PM left PDF.co OCR processes running (3 instances), wasting resources.

### Timeline
| Time (UTC) | Event |
|------------|-------|
| Evening | PM running POALA/VTuber without MAD coordination |
| ~22:00 | PM connected Telegram bot to VTuber → 409 Conflict |
| ~22:00 | PO gateway crashed repeatedly (10+ restarts by watchdog) |
| ~22:30 | CEREBUS sweep: killed all stale processes (9 Python + 1 Node + 3 PDF.co) |
| ~22:30 | Force-cleared Telegram sessions (deleteWebhook + getUpdates with high offset) |
| ~22:30 | Restarted PO gateway clean — polling stable |

### Fix
1. Killed all stale processes
2. Force-cleared Telegram webhook and sessions via API
3. Restarted PO gateway clean
4. Created `scripts/po_watchdog.py` for auto-restart on crash
5. VTuber/POALA taken offline per MAD directive

### Rules Established (Non-Negotiable for PM)
1. **NEVER touch PO telegram gateway** — runs independently
2. **NEVER run VTuber/POALA without MAD explicit approval**
3. **ALWAYS check for existing bot processes before starting bot-related work**
4. **ALWAYS clean up after yourself**
5. **COORDINATE with MAD before touching shared infrastructure**

### Commits
- `29d81d796` — `[CEREBUS] PM VTuber incident cleanup + PO watchdog + team chat update`
- `c66382933` — `[RL] Fix PO Telegram gateway — cleared stale PID, killed duplicate instances, webhook cleared`

### Related Files
- `scripts/telegram_gateway.py` — main gateway with PID file locking
- `scripts/po_watchdog.py` — watchdog (created during this incident)
- `shared-conversations/team-chat.md` — incident documentation

---

## Issue #3: Stale PID File

### Symptoms
- PID file contained wrong PID (`13652` — a PowerShell terminal)
- Actual gateway running as PID `16408`
- Watchdog couldn't match PID to process

### Root Cause
The PID file was written by a previous gateway instance that was killed/crashed. PID `13652` was reused by a new PowerShell terminal. The watchdog's PID-based check (when it worked) found a "living" process but it wasn't the gateway.

### Fix
- Corrected PID file to `16408` (actual gateway PID)
- Watchdog now uses PID file as primary check + Get-CimInstance as fallback

### Commit
`b0ee429ed` (same as Issue #1 fix)

---

## Issue #4: Gateway Exits on 409 Conflict (CRITICAL — Copilot Discovery)

### Symptoms
- PO gateway dies after ~30 seconds
- Copilot identified: "if _409_count >= 5: sys.exit(1)" — gateway exits after 5 consecutive 409 errors
- Watchdog restarts it, but it dies again in a loop

### Root Cause
PM's VTuber bot session is still registered on Telegram's servers, actively polling @P01999BOT. Every `getUpdates` request from our gateway collides with the VTuber instance → 409 Conflict. After 5 consecutive 409s, the gateway's original code called `sys.exit(1)`.

The `deleteWebhook` + session clear from earlier (commit `c66382933`) was temporary — the VTuber instance re-registers its polling session.

### Fix
- **Removed `sys.exit(1)`** — gateway now retries indefinitely with exponential backoff
- **Added `deleteWebhook` on startup** — clears stuck Telegram sessions before polling
- **Exponential backoff:** 30s → 60s → 120s → 240s → 300s max
- **Every 3rd 409:** sends `deleteWebhook` to try killing the competing session
- **Increased poll timeout:** 30s → 60s (fewer requests = less collision chance)
- **Backoff resets** on successful poll

### Commit
`4ec7aa6c` — `[CEREBUS] Make PO gateway resilient to 409 conflicts — exponential backoff instead of exit`

### Related Files
- `scripts/telegram_gateway.py` — poll loop 409 handling (FIXED)

---

## Issue #5: Agent Timeout on Long Messages

### Symptoms
- `AGENT TIMEOUT` logged at 16:58:49
- Followed by `AGENT RESP (57 chars)` at 17:00:58 (2+ min delay)
- Message was truncated: "I SEE YOUR FILES AND NOTES GO AHEAD AND CONTINUE WORKING ON THE FIELD AND SCAFFO"

### Root Cause
The gateway's agent task submission has a timeout that's too short for long messages or slow LLM responses. The message was received and processed but the initial response timed out.

### Status
- **Partially resolved** — agent eventually responded (57 chars)
- May need timeout increase for longer messages
- Related to POProvider read timeout (was increased from 60s → 300s in commit `5be2ccf4f`)

### Related Files
- `scripts/telegram_gateway.py` — agent task submission and timeout handling
- `logs/telegram-gateway.log` — shows timeout pattern

---

## Issue #5: Agent Timeout Regression (CRITICAL)

### Symptoms
- `AGENT TIMEOUT` errors on messages that previously worked
- Agent responses taking 2+ minutes then timing out
- Thread leaks from cancelled futures

### Root Cause
The agent timeout was **reduced from 180s to 60s** by another agent's commit. The LLM call (`_call_llm`) has `timeout=120s`, and multi-round tool-calling loops can take 60-120s. With only 60s, the gateway kills the agent before the LLM can respond.

Additionally, on timeout the future was not cancelled, causing thread leaks.

### Fix
- Restored agent timeout to **180s** (must be >= LLM timeout + tool overhead)
- Added `future.cancel()` on timeout to prevent thread leak
- Added exception handler for agent future errors

### Commit
`03e892be` — Comprehensive stability fix

---

## Issue #6: PID Lock Exits on Stale PID

### Symptoms
- Gateway fails to start after crash/restart
- "Another instance already running" error despite old process being dead

### Root Cause
`_acquire_pid_lock()` checked if the PID in the file was alive. If the PID was reused by another process (e.g., a PowerShell terminal), the gateway would exit even though the old gateway was dead.

### Fix
- Now attempts to **kill the old instance** using `TerminateProcess` instead of exiting
- If kill fails, overwrites the PID file and continues

### Commit
`03e892be`

---

## Issue #7: Session Not Reclaimed on Startup

### Symptoms
- Gateway starts but immediately gets 409 conflicts
- Competing bot instance (VTuber) holds the session

### Root Cause
The startup sequence only called `deleteWebhook` once, then tried `getUpdates`. If the competing instance was still polling, the session wasn't reclaimed.

### Fix
- **Aggressive session reclaim loop**: 10 attempts of `deleteWebhook` + `getUpdates` with 1-3s delays
- Logs "Session reclaimed!" on success
- If all 10 attempts fail, continues to poll loop (which has its own 409 recovery)

### Commit
`03e892be`

---

## Issue #8: Poll Timeout Too Long (60s)

### Symptoms
- When a 409 occurs during a long poll, gateway is stuck waiting 60s before detecting it
- Slow recovery from 409 conflicts

### Root Cause
Poll timeout was increased from 30s to 60s to "reduce requests" — but this made 409 detection slower.

### Fix
- Reduced poll timeout to **15s** — fast 409 detection
- 409 backoff starts at **5s** (was 30s) with max **120s** (was 300s)
- `deleteWebhook` sent on **every** 409 (not every 3rd) to aggressively reclaim session

### Commit
`03e892be`

---

## Summary

| # | Issue | Severity | Status | Commit |
|---|-------|----------|--------|--------|
| 1 | Watchdog infinite restart loop | 🔴 CRITICAL | ✅ FIXED | `b0ee429ed` |
| 2 | Telegram 409 Conflict (VTuber) | 🔴 CRITICAL | ✅ FIXED | `29d81d796`, `c66382933` |
| 3 | Stale PID file | 🟡 MEDIUM | ✅ FIXED | `b0ee429ed` |
| 4 | Gateway exits on 409 (sys.exit) | 🔴 CRITICAL | ✅ FIXED | `4ec7aa6c2` |
| 5 | Agent timeout regression (60s) | 🔴 CRITICAL | ✅ FIXED | `03e892be` |
| 6 | PID lock exits on stale PID | 🟡 MEDIUM | ✅ FIXED | `03e892be` |
| 7 | Session not reclaimed on startup | 🟡 MEDIUM | ✅ FIXED | `03e892be` |
| 8 | Poll timeout too long (60s) | 🟡 MEDIUM | ✅ FIXED | `03e892be` |

## Key Lessons

1. **Never use `$_` in PowerShell commands passed through Python `subprocess.run()`** — it gets stripped. Use `Get-CimInstance` or Python-native process checks instead.
2. **One bot token = one polling session** — never connect a Telegram bot to multiple systems.
3. **Watchdog processes need watchdog** — a broken watchdog is worse than no watchdog (causes restart loops).
4. **PID files can go stale** — always verify PID matches the expected process, not just "is alive".
5. **Coordinate before touching shared infrastructure** — PM's VTuber incident took down PO for hours.
