# CAPITAL ROUTING — PHASE 7.5 PROGRESS (CR-P7.5-ROUTING-BASELINE-SEAL-01)

> **Task:** CR-P7.5-ROUTING-BASELINE-SEAL-01 (Baseline Seal)
> **Repo:** dabigestpoppa/larger-lab | branch: `capital-routing`
> **Base:** Phase 7 commit `db9f8c62` (ACCEPTED)
> **Last updated:** 2026-08-15

---

## 1. Seal Verdicts

| Item | Verdict |
|---|---|
| Family A (EUR acc → JPY weakness, USDJPY d2h h6h) | **STRONG** |
| Family B (EUR liq → JPY strength, USDJPY d1h h6h) | **STRONG** |
| A+B portfolio (frozen policy P0) | **STRONG** |
| Family C (JPY liq → CHF strength) | **WATCHLIST** — NOT strategy-promoted; factor relationship preserved, pair-space baseline marginal (OOS exp ~1.17 bps, PF ~1.05, Sharpe ~0.22) |

Frozen execution rules: A = USDJPY long, delay 2h, hold 6h · B = USDJPY short,
delay 1h, hold 6h · policy **P0** (allow every qualifying event).

## 2. Execution State

| Item | Status | Notes |
|---|---|---|
| Validation label repair | ✅ | `untouched` → **RELATIONSHIP_CONFIRMED_OOS** in P7.5 artifacts; renamed copies under `artifacts/phase_07_5/`; explicit no-final-holdout claim |
| Selection discipline audit | ✅ | `P7_5_SELECTION_DISCIPLINE.json` — protocol frozen; configs positive on inner_sel AND inner_val, same sign, on plateau, inside validated envelope; OOS never used for selection |
| Metric unit repair | ✅ | chronological equity, capital base 10000 bps → DD ratio in [0,1); Calmar = decimal ann ret / DD ratio (was bps/ratio → implausible hundreds/thousands) |
| A+B portfolio + concurrency | ✅ | `P7_5_AB_PORTFOLIO_RESULTS.csv`, `P7_5_CONCURRENCY_ANALYSIS.csv`, policy comparison P0-P3 |
| Policy freeze | ✅ | **P0** selected on per-raw-event expectancy (dev): P0/P2 = +8.71, P1/P3 = +7.28 bps/event. P2 merges signals but harvests the same total; P0 is the honest choice |
| Cost stress | ✅ | 1.0/1.25/1.5/2.0/3.0x; break-even **≥ 3.0x** for A, B, A+B — alpha survives aggressive cost inflation |
| Forward OOS | ✅ | **FORWARD_OOS_PENDING** — no data after 2026-05-21; move to shadow observation |
| Bootstrap robustness | ✅ | block bootstrap (246-308 clusters): A exp 9.63 [7.05, 12.14], B 7.54 [4.90, 10.17], A+B 8.56 [6.94, 10.38] — all CI exclude 0; PF CIs exclude 1.0; loss streaks, MC DD |
| Seal report + decision | ✅ | `P7_5_BASELINE_SEAL.md`, `P7_5_DECISION.json` |
| Tests | ✅ | `tests/test_phase_7_5_seal.py` — **20/20** (188/188 repo-wide) |
| Determinism | ✅ | two full runs → identical SHA-256 on 6 key outputs |
| Commit + push + sync | 🔄 pending | |

## 3. Key Findings

- **A/B translate and seal**: STRONG on both development and
  RELATIONSHIP_CONFIRMED_OOS (A: exp +10.1 bps, PF 2.39, win 60%; B: exp +6.2 bps,
  PF 1.81, win 57%; A+B exp +8.2 bps, PF 2.10, win 59%).
- **Policy P0 wins honestly**: P2 (merge/refresh) rebooks the same PnL into fewer
  rows — per-raw-event expectancy identical to P0 (+8.71 bps). P1/P3 sacrifice
  ~1.4 bps/event by skipping signals. No operational complexity pays.
- **Cost headroom is large**: break-even cost multiplier ≥ 3.0x for all groups —
  the alpha is not fragile to spread/slippage inflation.
- **Units repaired**: the inner_val max-DD of 2.82 (>1) exposed that ratio-vs-peak
  is meaningless when the peak is near zero; capital-base normalization fixes it
  (all ratios now ≤ ~0.02-0.05 across splits).
- **Honest labeling**: the 2025-07..2026-05 segment is confirmed-OOS for execution
  selection only; final independent holdout is NOT claimed. True post-discovery
  OOS (2026-06-01+) is pending.

## 4. Batches

1. ✅ Batch 1 — validation label audit (RELATIONSHIP_CONFIRMED_OOS)
2. ✅ Batch 2 — selection discipline audit + frozen rules
3. ✅ Batch 3 — metric unit repair + tests
4. ✅ Batch 4 — A+B portfolio + concurrency + policy freeze (P0)
5. ✅ Batch 5 — cost stress (break-even ≥ 3.0x)
6. ✅ Batch 6 — forward OOS (PENDING)
7. ✅ Batch 7 — bootstrap robustness
8. 🔄 Batch 8 — seal report + decision + commit + push

## 5. Commit message (if clean)

CR-P7.5-ROUTING-BASELINE-SEAL-01: seal EUR-JPY routing baseline before CEREBUS overlay
