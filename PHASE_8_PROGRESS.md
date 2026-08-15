# CAPITAL ROUTING — PHASE 8 PROGRESS (CR-P8-CEREBUS-ROUTING-OVERLAY-DISCOVERY-01)

> **Base:** Phase 7.5 sealed baseline `7bc1c024` (ACCEPTED — A/B STRONG, C WATCHLIST)
> **Branch:** `capital-routing` | **Status:** ✅ DISCOVERY COMPLETE — STOPPED per brief §27
> **Last updated:** 2026-08-15

## Status

| Item | Status |
|------|--------|
| Canonical CEREBUS primitives located & frozen | ✅ Pine `get_tier` / P90 signal / `violation_long-short` (132% rekey), cascade config thresholds, `asian_range.py` session rule, `mlr_test.py` midpoint |
| USDJPY M5 data (canonical, 2022-01→2026-05) | ✅ copied to `data/USDJPY_M5.parquet`, sha256 `719353ad...` frozen |
| Primitive extraction (120m causal window) | ✅ `phase_8_primitives.py` |
| Event fingerprint + long stream | ✅ `P8_EVENT_FINGERPRINT.csv`, `P8_PRIMITIVE_STREAM_LONG.csv` (900 events, 1 row/event) |
| All 14 study tables (discovery-only) | ✅ all `P8_*.csv` written |
| Candidate protocol (discovery→confirmation→OOS once) | ✅ 38 candidates, BH-FDR per family, subperiod stability |
| Decision | ✅ `CR_P8_DECISION.json` — **phase_9_optimization_cleared = FALSE** |
| Tests | ✅ 19 new (`test_phase_8_overlay.py`) — **207/207 repo-wide** |
| Determinism | ✅ byte-identical re-run (6 sampled outputs) |
| Commit | ⏳ (pending push) |

## Key results

- **Baseline reproduced exactly:** A inner_sel +10.06 / untouched +10.13; B inner_sel +7.42 / untouched +6.18 bps (vol-normalized) — matches sealed Phase 7/7.5 to 3 decimals.
- **NO primitive clears the materiality gate.** 0 class-A, 5 conditional (B), 33 rejected.
- **Strongest signals (under-powered, NOT promoted):**
  - `A_rekey_present` (132% violation in window): expectancy −11.6 bps vs base, p=0.08, n=21, cov 10% → VETO/EXIT candidate.
  - `B_tier_t3` (wide Asian range): −9.2 bps, p=0.09, n=36 → REGIME candidate ("T3 = exhausted variance" directionally supported).
  - Aligned P90 / commitment ratio: +2.7 to +6.1 bps, p=0.24–0.48 → ACTIVATION direction, not significant.
- **Equal-weight primitive score is monotonically increasing** (Spearman 0.40 A / 0.45 B): score 2 cells A +15.8 (89% win) / B +20.3 (100% win) vs score 0 (+8.9/+7.3). Per §20, marked as Phase-9 optimization candidate — weights untouched.
- **T1 is structurally absent** (16/890 events); NO-GO is modal (58%). P90 prints only exist 2–11 AM EST — 61% of routing events fall in-window; among those, 81% have ≥1 P90 print.
- **P90 adds no incremental info beyond tier impulse** (tier impulse = P90 body + band breach by definition).
- **Sequence grammar** is midpoint-dominated, no cell with N ≥ 30; repeated opposed rekey (RO-RO-RO-RO) shows 40% win.

## Decision (CR_P8_DECISION.json)

`phase_9_optimization_cleared: false` — no primitive/pattern materially improves
expectancy with coverage + confirmation + OOS agreement. Eligible for human
review as Phase-9 optimization candidates: `A_rekey_present` (VETO/EXIT),
`B_tier_t3` (REGIME), aligned-P90 / commitment (ACTIVATION), equal-weight score
(SIZING/ACTIVATION).

## Timeline

| Date | Milestone |
|------|-----------|
| 2026-08-15 | Phase 8 received; located canonical CEREBUS (Pine V5, cascade config, asian_range, label_generator, dual-engine ontology) |
| 2026-08-15 | Primitives/fingerprint/studies built; baseline fixed to vol-normalized (sealed P7 convention); dup-event bug fixed; materiality gate added |
| 2026-08-15 | 19 tests + 207/207 full suite; determinism verified; discovery complete |

## Next steps (await human review)

1. Decide which candidates proceed to Phase 9 (exact threshold optimization is FORBIDDEN until then).
2. Recommended review focus: rekey VETO logic, T3 regime conditioning, equal-weight score monotonicity.
