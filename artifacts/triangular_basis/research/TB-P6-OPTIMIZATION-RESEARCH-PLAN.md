# TB-P6 — OPTIMIZATION RESEARCH PLAN (INVENTORY ONLY — NO TESTING)

Validation cleared optimization for at least one neutral model. This document only
INVENTORIES dimensions for human review. Nothing here has been tested or selected.

## Candidate optimization dimensions (do not test until human approval)
1. Basis-dislocation entry threshold (z) — currently frozen at 2.5.
2. Entry timing within London session / time-of-day.
3. Further-extension behavior (add to position vs wait).
4. Convergence target (exit z) — currently 0.0.
5. Maximum holding period / hard-exit hour.
6. Stop / invalidation level (z) — currently 6.0.
7. Session (London-only) — verify vs other sessions with neutral sizing.
8. Weekday effects (see TB_P5_DISLOCATION_ANATOMY.csv).
9. Volatility-regime conditioning (entry vol tercile).
10. Spread / liquidity regime gating.
11. Offending/leading-leg conditioning (which leg created the dislocation).
12. Re-entry / cooldown after exit.
13. TB-B (exact) vs practical TB-C residual ceiling (2.5-10%).
14. Basket notional / executable lot precision (min viable scale).
15. CEREBUS basis geometry (multi-triangle families).
16. P90/rekey behavior on the synthetic basis series.

## Rules for the next phase
- One dimension at a time; every variant validated on the frozen evaluation protocol.
- No dimension may touch the signal's causal construction.
- Any accepted change re-runs TB-P5 sections 1-12 before adoption.
