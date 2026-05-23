# Phase 11.2 — 20X Chaos Amplification Test v2

## Test Parameters
- **Started:** 2026-05-23 00:06 UTC
- **Duration:** 5 hours (ends ~05:06 UTC)
- **Amplification:** 0.5% per PASS cycle
- **Max amplification:** 20x
- **Cooldown:** 5 minutes between cycles
- **Script:** `tools/testing/chaos/chaos_20x_test.py`
- **Trace log:** `stability/chaos_20x_trace.log` (workspace root)

## What's Fixed in v2
- Amplification now **actually scales** chaos parameters:
  - Durations multiply by amp (observer_kill: 30s × amp, event_flood: 120s × amp, etc.)
  - Severity/corruption rates multiply by amp (capped at 1.0)
  - More targets get hit at higher amp thresholds (1.5x, 2x, 3x, 5x, 8x, 10x)
  - New `extreme_chaos` scenario unlocks at 10x
  - Recovery timeout scales with amp (5min base + 60s per amp, max 15min)
  - Stagger between injections decreases at higher amp

## Progress

| Cycle | Amplification | Status | Recovery Time | Events |
|-------|--------------|--------|---------------|--------|
| 1 | 1.005x | ✅ PASS | 302.9s | 4 |
| 2 | 1.010x | 🔄 Cooldown | — | — |

## Notes
- Killed old test (cycle 2, same durations every cycle — broken amplification)
- Rewrote chaos_engine.py: all methods accept `amplification` param
- Rewrote chaos_20x_test.py: passes `self.amplification` to engine
- Background monitor running (checks trace every 30s, PID 7660)
