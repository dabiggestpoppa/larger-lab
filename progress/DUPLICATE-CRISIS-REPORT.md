# DUPLICATE PROCESS CRISIS — Full Report & Handoff
> **Date:** 2026-06-08
> **Author:** PM2 (OWL)
> **Status:** UNRESOLVED — escalating to full team
> **Severity:** CRITICAL — has blocked all trading operations for 4+ days

---

## 🔥 THE PROBLEM

Every time we start the trading engines (bridge, signal bot, telegram gateway), DUPLICATE processes spawn immediately. We've been fighting this for 4 days. Every agent says "I fixed it" but it keeps coming back.

**Current state:** 29 Python processes running, many duplicates. Engines keep dying and respawning.

---

## 🔍 ROOT CAUSE ANALYSIS

### What I Found:

1. **Two Python interpreters running simultaneously:**
   - `C:\...\venv\Scripts\python.exe` (correct — our venv)
   - `C:\...\uv\python\cpython-3.12-windows-x86_64-none\python.exe` (UV Python — the duplicate spawner)

2. **UV Python instances are spawned as CHILD PROCESSES of the venv bridge:**
   - VENV bridge PID 7176 → Parent: 31720 (cmd.exe)
   - UV bridge PID 13336 → Parent: **7176** (the venv bridge itself!)
   - This means the bridge script is somehow launching a second instance through UV Python

3. **The `pyproject.toml` has `requires-python = ">=3.12"`** — this matches the UV Python version (3.12). UV auto-detects the workspace via pyproject.toml and may be intercepting subprocess calls.

4. **Bridge auto-restart feature (line 863):** `cerebus_live_bridge.py` has `except Exception` → "Auto-restarting in 10 seconds..." → calls `run_live()` again. If the bridge crashes, it restarts itself, creating a duplicate.

5. **Scheduled task `twin_bridge`:** Found `schtasks` entry running `shared-twin\twin_bridge.py heartbeat oc3 18791 poolside/laguna-m.1:free`. This was DISABLED but may have been spawning processes before.

### What I Tried (ALL FAILED):

| Attempt | Result |
|---------|--------|
| `process_registry.py --clean` then `--start` | Duplicates appear within seconds of starting |
| Killing UV Python processes | They respawn immediately as children of the venv bridge |
| Disabling `twin_bridge` scheduled task | No effect — UV duplicates still appear |
| Bridge auto-restart disable (line 863) | Code change made but duplicates are NOT from auto-restart — they appear immediately on startup |
| `Start-Process -WindowStyle Hidden` | Processes die when terminal session ends |
| `cmd /c "start /B ..."` | Same issue — processes die with terminal |
| `Start-Process` with `.NET ProcessStartInfo` | Failed silently |
| Killing ALL Python processes then starting fresh | Duplicates appear within 5 seconds of starting bridge |
| Using only venv Python (not UV) | UV instances still spawn as children |

### The Smoking Gun:

When I started the bridge with venv Python, then checked parent PIDs:
```
PID 7176 (VENV bridge)  → Parent: 31720 (cmd.exe that started it)
PID 13336 (UV bridge)   → Parent: 7176 (the VENV bridge itself!)
```

**The bridge is spawning a UV Python child process.** I don't know why. The bridge code has no `subprocess`, `multiprocessing`, `threading`, or `uv` references. The only explanation is that something in the MT5 Python library or the `pyproject.toml` workspace detection is causing UV to intercept.

---

## 📋 HANDOFF TO TEAM

### Immediate Actions Needed:

1. **Find what's spawning UV Python as a child of the bridge**
   - Check if `mt5.initialize()` or any MT5 library call spawns subprocesses
   - Check if `pyproject.toml` workspace detection is causing UV interception
   - Check if there's a `.pth` file or sitecustomize.py that hooks into Python startup

2. **Fix the process startup method**
   - Current: `Start-Process` / `cmd /c` — processes die with terminal
   - Need: True detached processes that survive terminal closure
   - Options: Windows Service, Task Scheduler, or `CREATE_NEW_PROCESS_GROUP` flag

3. **Add FR40 to the live engine config**
   - MAD added FR40 manually — needs to be in `deploy_config.py`
   - Bridge currently runs: EURJPY, EURNZD, GBPNZD, EURAUD, GBPAUD, GBPCAD
   - Add: FR40.PRO

4. **Set up proper watchdog**
   - PO's `po_watchdog.py` exists but doesn't prevent duplicates
   - Need: Watchdog that checks for AND kills duplicates, not just restarts dead processes

### Files to Review:
- `quant-lab/mt5/cerebus_live_bridge.py` — line 863 (auto-restart), MT5 init code
- `pyproject.toml` — `requires-python = ">=3.12"` may trigger UV
- `scripts/process_registry.py` — exists but doesn't prevent spawning
- `scripts/po_watchdog.py` — exists but only restarts, doesn't prevent duplicates
- `scripts/telegram_gateway.py` — has mutex singleton (PO's fix) but still gets duplicates

### Current Process State:
- Bridge: scanning but with duplicates
- Signal bot: running but with duplicates  
- Telegram: running (PO restarted it)
- 29 Python processes total, many duplicates

---

## ⚠️ CRITICAL LESSON

**Every agent has been "fixing" duplicates by killing and restarting. But the RESTART is what CREATES the duplicate.** We need to prevent the spawning, not just kill after the fact.

The duplicate spawner is NOT the watchdog, NOT the registry, NOT the scheduled task. It's something in the Python/UV/workspace setup that causes the bridge to spawn a UV Python child process.

**This needs a fresh pair of eyes. I've spent hours going in circles.**
