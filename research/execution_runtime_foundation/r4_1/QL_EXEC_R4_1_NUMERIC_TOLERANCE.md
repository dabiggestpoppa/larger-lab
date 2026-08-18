# QL-EXEC-R4.1 — Numeric Tolerances (frozen before observation)

These tolerances are frozen BEFORE live observation, derived from the R4
offline/replay parity evidence (EXACT tier). They are NOT widened after a
mismatch. A value outside tolerance => MISMATCH alert (shadow remains
orderless).

| Quantity | Parity basis | Frozen tolerance |
|----------|--------------|------------------|
| common-bar key / source timestamp | deterministic string | EXACT equality |
| basis `ln(GA)-ln(GN)+ln(AN)` | identical frozen formula + inputs | relative `1e-12` |
| z-score (rolling 200, ddof=0, bar excluded) | identical frozen formula + inputs | absolute `1e-9` |
| model weights (TB-B exact neutral, sum|s|=3) | deterministic | EXACT |
| direction / decision / session eligibility | deterministic enum | EXACT |
| target lots (0.07/0.07/0.13 or current canonical) | deterministic 2dp rounding | EXACT string equality; float `1e-9` |
| basket state / blocker | deterministic enum | EXACT |
| clock calibration / freshness flags | frozen config | EXACT boolean |

## Notes

- Floating-point quantities are compared at the frozen epsilon only. Where a
  value is deterministic (weights, lots, direction), exact string/enum equality
  is used.
- If the canonical translation later changes target-lot mechanics (it is frozen
  at TB authority b48fd35255b41865026a3cba333ae2a2a0d6a004), the tolerance is
  re-frozen against the new authority BEFORE any new comparison run — never
  after observing a mismatch.
