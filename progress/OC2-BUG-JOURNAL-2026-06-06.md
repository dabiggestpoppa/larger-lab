# OC2 Bug Journal — 2026-06-06

> **Key insight from operator:** "OC2 has a lot of little bugs that's just OpenClaw setup. We don't have none of these problems with PO. Which is telling that it's just OpenClaw itself."
>
> **Translation:** PO's custom Python gateway (scripts/telegram_gateway.py) is rock solid. OC2's OpenClaw-based gateway is the source of all these issues. The bugs are in OpenClaw, not in our code.

---

## Bug #6: Session Recovery Sends Stale Responses (DOCUMENTED — NO CODE CHANGE)

**Symptom:** After OC2 restarts, the first message gets a stale response like "No further note from me." instead of actually processing the new message. Sometimes sends TWO responses — one stale, one correct.

**Root Cause:** OpenClaw's session recovery mechanism. When the gateway restarts, it resumes the previous Telegram session and re-sends the last assistant response before processing the new message. Log evidence:
```
22:39:46 [resumed interrupted main session: agent:main:telegram:direct:8258195396]
22:44:10 [telegram sendMessage ok] message=9449   ← stale response
22:44:17 [telegram sendMessage ok] message=9451   ← actual response
```

**Fix:** No code change. Operator confirmed: "I don't wanna touch code OC2 Telegram way too fragile, we will just work with what we got."

**Workaround:** After any OC2 restart, send a `/new` or `/reset` command to start a fresh session, or just ignore the first stale response.

**Why PO doesn't have this:** PO's custom Python gateway (`scripts/telegram_gateway.py`) doesn't have session recovery — each message is processed fresh.

---

## Bug #1: OpenClaw Gateway Restart Loop (CRITICAL)

**Symptom:** OC2 gateway restarts every ~2-5 minutes. Each restart takes 30-90s to come back. During restart, Telegram messages are queued but not processed.

**Root Cause:** The OpenClaw gateway's Telegram long-polling `getUpdates` connection keeps failing with `fetch timeout reached` and `DNS-resolved IP unreachable; trying alternative Telegram API IP`. This causes the gateway process to crash/restart.

**Evidence from logs:**
```
22:24:21 [fetch timeout reached; aborting operation]
22:26:58 [fetch timeout reached; aborting operation]
22:29:03 [loading configuration…]  <-- restart #1
22:29:40 [gateway ready]
22:30:17 [liveness warning: event_loop_delay, event_loop_utilization]
22:31:33 [WARN] Attempting gateway restart...  <-- watchdog triggers restart #2
```

**Pattern:** Gateway starts → Telegram connects → ~2 min later `fetch timeout` → gateway crashes → watchdog detects failure → watchdog restarts gateway → repeat.

**Impact:** OC2 was effectively unavailable for ~7 hours today. Even when "up", it restarts every few minutes, losing context each time.

**Why PO doesn't have this:** PO uses a custom Python polling gateway (`scripts/telegram_gateway.py`) with `requests.get()` and proper timeout handling. OpenClaw uses its own internal Node.js HTTP stack which has DNS resolution issues.

**Possible fixes to investigate:**
1. Increase OpenClaw's internal HTTP timeout for Telegram API calls
2. Set `NODE_OPTIONS=--dns-result-order=ipv4first` to fix DNS resolution
3. Configure OpenClaw to use a specific Telegram API IP instead of DNS resolution
4. Run OpenClaw gateway in foreground to see real-time errors
5. Consider running PO's gateway pattern for OC2 as well (custom Python poller)

---

## Bug #2: Watchdog Aggressive Restart (MEDIUM)

**Symptom:** The watchdog (`tools/openclaw_watchdog.py`) detects a health check failure and immediately restarts the gateway. But the gateway takes 30-90s to start up, and during that time the watchdog keeps failing health checks and may trigger multiple restarts.

**Evidence:**
```
22:06:57 [WARN] Failure #1 → Attempting gateway restart...
22:08:49 [WARN] Failure #2  (gateway still starting)
22:10:01 [WARN] Failure #3  (gateway still starting)
...
22:19:10 [WARN] Failure #11
22:21:24 [INFO] Recovered after 12 failures
```

**Problem:** The watchdog's 60s check interval is too aggressive during gateway startup. The gateway takes 30-90s to start, but the watchdog treats each failed check as a new failure and may restart again.

**Fix needed:** Add a "startup grace period" to the watchdog — after a restart, wait 120s before checking health again.

---

## Bug #3: Plugin Skill Symlink EPERM (LOW)

**Symptom:** Repeated `failed to create plugin skill symlink` errors in logs.

**Root Cause:** Windows doesn't allow symlinks without elevated privileges. OpenClaw tries to create symlinks for browser-automation skills.

**Impact:** Non-fatal. Browser control still works (port 18792).

**Fix:** Run OpenClaw as Administrator, or configure Windows to allow symlinks.

---

## Bug #4: Two-File Config Trap (DOCUMENTED)

**Symptom:** All 14 initial fix attempts failed because there are TWO config files and the CLI edits the wrong one.

**Files:**
- `C:\Users\wifik\.openclaw-2\openclaw.json` (primary/CLI)
- `C:\Users\wifik\.openclaw-2\.openclaw\openclaw.json` (gateway runtime)

**Fix:** Always edit BOTH files. Documented in `tools/OPENCLAW-RUNBOOK.md`.

---

## Bug #5: sovereign_health_monitor.py Truncated (FIXED)

**Symptom:** `field/sovereign_health_monitor.py` was truncated at line 190 — `def generate_report(self) -> HealthReport:\n    now =` with no body.

**Fix:** PM2 added a minimal stub returning empty HealthReport. PO needs to restore real logic.

---

## Summary: OpenClaw vs PO Gateway

| Aspect | PO Gateway (Python) | OC2 Gateway (OpenClaw) |
|--------|--------------------|-----------------------|
| Uptime | Stable, no restarts | Restarts every 2-5 min |
| Telegram connection | Rock solid | DNS/timeout issues |
| Tool calling | 36 rounds, 8K results | N/A (different arch) |
| Config | Single `.env` file | Two JSON files, CLI lies |
| Watchdog needed | No | Yes, and it's aggressive |
| **Verdict** | **Production ready** | **Needs work** |

**Recommendation:** Consider migrating OC2 to use PO's gateway pattern (custom Python Telegram poller) instead of OpenClaw's built-in Telegram channel. This would eliminate bugs #1 and #2 entirely.

---

## Bug #7: Watchdog Clipping OC2 Mid-Response (FIXED — REMOVED)

**Symptom:** OC2 starts working on a large response/task, takes time to think, watchdog health check fails during thinking, watchdog restarts OC2 mid-response. Result: OC2 never finishes anything.

**Root Cause:** The watchdog (`tools/openclaw_watchdog.py`) was designed with a 60s check interval and auto-restart on any failure. But OC2's LLM can take 30-90s+ to process complex requests. The health check times out during thinking → watchdog thinks OC2 is down → restarts it → kills the in-progress response.

**Operator feedback:** "U BUILT A USELESS ASS GUARD DOG, JUST MAKE A SIMPLE STATE TRACKER WITH A LOG SO WE CAN SEE IF AND WHEN AND WHY OC2 STOP RESPONDING FOR GOING DOWN, NO FUCKING SCRIPT AUTO RESTARTING ON NONE OF THE SHIT COOKING PROGRESS AINT NUN BE WRONG AND ITS RESTARTING THE DAMN AGENT EVERY 2/4 RESPONSES"

**Fix:** 
- DELETED `tools/openclaw_watchdog.py` entirely
- Created `tools/oc2_state_tracker.py` — simple monitor, NO auto-restart
- Checks every 120s, only logs state changes (UP/DOWN/DEGRADED)
- Logs last 5 gateway lines when OC2 goes down for context
- Tracks downtime count and timestamps

**Lesson learned:** Never auto-restart an agent that's mid-task. Just log and alert.
