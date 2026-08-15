# CAPITAL ROUTING — PHASE 7 PROGRESS (CR-P7-ROUTING-TRANSLATION-01)

> **Task:** CR-P7-ROUTING-TRANSLATION-01 (Routing Translation / Baseline Strategies)
> **Repo:** dabigestpoppa/larger-lab | branch: `capital-routing`
> **Base:** Phase 6 commit `5726bf02` (ACCEPTED)
> **Last updated:** 2026-08-15

---

## 1. Frozen Relationship Families (from Phase 6 VALIDATED)

| Family | Relationship | Validated horizons | Trade expression | Alpha gate |
|---|---|---|---|---|
| A | EUR ACCUMULATION → JPY relative weakness | 6h/8h/12h | LONG JPY crosses (long EURJPY/USDJPY/GBPJPY/CHFJPY) | **PROMOTED** |
| B | EUR LIQUIDATION → JPY relative strength | 4h/6h/8h/12h | SHORT JPY crosses | **PROMOTED** |
| C | JPY LIQUIDATION → CHF relative strength | ~48h | long CHFJPY, short USDCHF/EURCHF/GBPCHF | **PROMOTED** |

All 6 alpha-promotion criteria PASS for every family:
1. same holdout sign ✅ 2. holdout effect ≥ 50% dev ✅ 3. bootstrap CI excludes zero ✅
4. holdout N ≥ 100 ✅ 5. no collapse under overlap cooldowns (effect recomputed on
6/12/24h non-overlapping subsets, ratio 0.86–0.99) ✅ 6. no single-horizon dependence
(plateau / 36-48-60h sign coherence) ✅

## 2. Execution State

| Item | Status | Notes |
|---|---|---|
| `P7_RELATIONSHIP_FAMILIES.json` | ✅ | 3 families frozen, static gate 1-5 per family |
| `P7_ALPHA_PROMOTION_GATE.json` | ✅ | All 3 families PROMOTED (gate_status PASS) |
| Execution grid (pair × delay 0-4h × hold) | ✅ | A/B: 4 JPY crosses × holds 4-12h; C: CHF pairs × holds 24-72h |
| `P7_PAIR_SPACE_COMPARISON.csv` | ✅ | routing efficiency = E[MFE]/(E[MAE]+cost) |
| `P7_ENTRY_DELAY_SURFACE.csv` | ✅ | plateaus, not isolated optima |
| `P7_EXCURSION_GEOMETRY.csv` | ✅ | MAE/MFE p50/75/90/95, time-to-MFE/MAE |
| Mirrored symmetry (A long vs B short) | ✅ | `P7_MIRRORED_SYMMETRY.csv` |
| `P7_EUR_JPY_BASELINE_RESULTS.csv` | ✅ | families A+B, fixed delay/hold, vol-normalized risk |
| `P7_JPY_CHF_BASELINE_RESULTS.csv` | ✅ | family C, incl. swap/carry + spread |
| `PHASE_7_STRATEGY_STUDY.md` + `PHASE_7_DECISION.json` | ✅ | gate PASS, 3/3 promoted |
| Tests (`tests/test_phase_7_translation.py`) | ✅ | **19/19 passing** (168/168 repo-wide) |
| Determinism | ✅ | two full runs → identical SHA-256 on 8 key outputs |
| Commit | ✅ | **`db9f8c62`** on `capital-routing` (22 files, +3,722) |
| Sync to `Desktop\projects\larger-lab` | ✅ | source/tests/artifacts copied; 19/19 tests pass there |
| Push to GitHub | ✅ | `5726bf02..db9f8c62 capital-routing -> capital-routing` |

## 3. Baseline Results (fixed vol-normalized risk, per split)

| Baseline | Split | Trades | Win | Expect/bps | PF | Sharpe(ann) |
|---|---|---|---|---|---|---|
| A: EUR-acc→JPY weakness (USDJPY, d2h h6h) | inner_sel | 211 | 0.668 | +10.06 | 2.43 | 4.04 |
| A | inner_val | 77 | 0.623 | +7.52 | 1.90 | 2.98 |
| A | **untouched** | 144 | 0.604 | **+10.13** | 2.39 | 3.96 |
| B: EUR-liq→JPY strength (USDJPY, d1h h6h) | inner_sel | 250 | 0.628 | +7.42 | 1.86 | 3.08 |
| B | inner_val | 72 | 0.639 | +10.53 | 2.57 | 4.20 |
| B | **untouched** | 136 | 0.574 | **+6.18** | 1.81 | 2.89 |
| C: JPY-liq→CHF strength (USDCHF, d0h h48h) | inner_sel | 211 | 0.507 | +0.76 | 1.04 | 0.16 |
| C | inner_val | 68 | 0.647 | +34.56 | 3.93 | 6.08 |
| C | **untouched** | 121 | 0.455 | **+1.17** | 1.05 | 0.22 |

EUR→JPY families A/B translate cleanly to pair space and survive untouched
validation (expectancy +6 to +10 bps, PF 1.8-2.4, Sharpe 2.9-4.0). Family C
(JPY→CHF) is promoted on factor-space criteria but its pair-space baseline is
marginal on untouched (+1.2 bps, PF 1.05, 45% win) — honest finding, noted in
the decision.

## 4. Key Engineering Notes

- **Sign conventions verified empirically** from Phase 6 pair returns before
  coding trade directions (EUR acc → JPY crosses rise; EUR liq → JPY crosses
  fall except EURJPY which is flat; JPY liq → CHFJPY up / CHF-quote pairs down).
- **Swap bug found + fixed:** initial formula treated percent as bps (100× too
  large). `swap_bps_per_day = (r_base − r_quote) * 100 / 365`; signed by trade
  direction (short reverses carry).
- **Sharpe annualization fixed:** used actual event frequency (trades/year),
  not a fixed hourly bar count — Sharpe now 2.9-4.2 instead of inflated ~26.
- **Plateau detection:** holds are consecutive in the family hold grid (Family C
  holds 24/36/48/60/72 are 12h apart), not calendar-adjacent.
- **Criterion 5:** recomputes destination effect on non-overlapping subsets via
  Phase 6's `non_overlapping_mask` (6/12/24h cooldowns) — same sign + ≥50%
  magnitude. The Phase 6 overlap CSV's `mean_forward` column is ~1e-20 noise,
  so it is not used numerically.
- **Config selection:** representative (delay, hold) restricted to VALIDATED
  horizons (Family C stays at 48h, not the best-net 24h).
- Validation discipline: untouched (Phase 6 holdout) used ONCE after rules
  frozen on inner_sel/inner_val within dev. No parameter rescue.

## 5. Batches

1. ✅ Batch 1 — plan + families + alpha gate (PASS, 3/3)
2. ✅ Batch 2 — execution engine + costs + nested splits
3. ✅ Batch 3 — pair space / delay surface / excursions / symmetry
4. ✅ Batch 4 — baselines + yearly metrics + decision
5. ✅ Batch 5 — tests (19) + determinism (byte-identical re-run)
6. 🔄 Batch 6 — commit CR-P7 + report back; push/sync pending user decision

## 6. Commit message (if clean)

CR-P7-ROUTING-TRANSLATION-01: translate validated routing relationships into pair-space baselines
