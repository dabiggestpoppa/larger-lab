# Team Notes — Persistent Errors, Observations, and Troubleshooting

> **Purpose:** Shared knowledge base for errors that persist or caused trouble during building. All agents contribute here.
> **Format:** Date | Agent | Issue | Root Cause | Resolution

---

## Chaos Test Crashes

**2026-05-23 | OWL | Chaos test keeps crashing at higher amplification**
- **Symptom:** Process exits with code 1 during full_chaos scenario at amp ~3.0x
- **Root Cause:** Recovery timeout exceeded. At amp 3.0, event_flood duration = 360s, combined with router_failure (103s) and websocket_loss (90s) — too many concurrent long-running chaos events.
- **Resolution:** Internal auto-restart with consecutive crash limit (5) added. Test completes 4/5 cycles.
- **Lesson:** Recovery timeout must scale with number of concurrent injections, not just amplification.

**2026-05-23 | OWL | Duplicate chaos test instances running simultaneously**
- **Symptom:** Two chaos test processes writing to same trace log, causing interleaved entries
- **Root Cause:** Auto-restart wrapper spawned new subprocess before old one fully cleaned up its daemon threads
- **Resolution:** Kill all chaos-related processes before restarting. Use PID whitelist.
- **Lesson:** Always check for existing processes before spawning new ones. Use `Get-Process | Where-Object { $_.CommandLine -like '*chaos*' }`.

**2026-05-23 | OWL | Trace log FileNotFoundError**
- **Symptom:** `log_trace` fails with FileNotFoundError for stability/chaos_20x_trace.log
- **Root Cause:** Relative path `Path("stability/...")` depends on CWD. When CWD changes, the path breaks.
- **Resolution:** Changed to absolute paths based on `Path(__file__).parent`. Also added `mkdir(parents=True, exist_ok=True)` before every write.
- **Lesson:** Always use absolute paths based on script location, never relative paths for file I/O.

---

## Singleton Data Persistence

**2026-05-24 | OWL | Tufte renderers show empty data despite feeding data to singleton**
- **Symptom:** `render_observer_density.py` shows "No observer data available" even after feeding data to the singleton
- **Root Cause:** Each Python process gets its own singleton instance. Data fed in one process is not visible in another.
- **Resolution:** Export data to disk (JSON), have renderers load from disk instead of singleton.
- **Lesson:** Singletons don't persist across processes. For cross-process data sharing, use disk (JSON/parquet) or a database.

---

## Unicode Encoding on Windows

**2026-05-23 | AS/OWL | UnicodeEncodeError with emoji characters**
- **Symptom:** `UnicodeEncodeError: 'charmap' codec can't encode character '\u2705'` when printing test results
- **Root Cause:** Windows console uses cp1252 encoding by default, which doesn't support emoji
- **Resolution:** Set `$env:PYTHONIOENCODING="utf-8"` before running Python scripts
- **Lesson:** Always use UTF-8 encoding on Windows for any output containing emoji or special characters.

---

## Progress File Corruption

**2026-05-24 | OWL | Progress files being cleared or corrupted**
- **Symptom:** `phase-11-status.md` found empty after being written
- **Root Cause:** Unknown — possibly user cleanup or formatter tool
- **Resolution:** Recreate with verified data. Keep backups.
- **Lesson:** Don't trust progress files blindly. Verify contents before referencing.

---

## General Observations

**From User Feedback:**
1. "Don't make things harder than they need" — tendency to over-engineer
2. "Test before you update" — tendency to update progress before verifying
3. "Don't make a plan until you feel fully aligned" — tendency to plan before understanding
4. "Take your time, don't rush execution" — tendency to rush through steps

**From Build Files:**
1. The architecture is ONE system (SRRA+OPH runtime + OCE interface), not many separate systems
2. Phases 1-5 are runtime substrate, Phases 6-7 are research horizon
3. Current priority: Phase 11 testing + OCE visualization + runtime instrumentation
4. Delay advanced cognition (Phases 6-7) until runtime stability is proven
