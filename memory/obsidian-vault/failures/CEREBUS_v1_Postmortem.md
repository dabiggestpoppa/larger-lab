# CEREBUS v1 Live Engine - Postmortem

> 2026-06-01 15:35 UTC

#cerebus #postmortem #v1

Result: 0% WR (0W/30L, -393.1p)

Root Causes
1. 1-state immediate entry (not 4-state)
2. SL = current bar low (5-14p) not impulse extreme (15-40p)
3. Wick-based SL (not close-only)
4. No Goldilocks zone (32-50% pullback)
5. No OCC confirmation
6. P90 INITIAL only (no CASCADE/EWS)
7. NO-GO tier not enforced

Lesson: Backtest-to-live requires EXACT state machine parity
