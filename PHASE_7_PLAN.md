# CAPITAL ROUTING — PHASE 7 PLAN (CR-P7-ROUTING-TRANSLATION-01)

> **Base:** Phase 6 commit `5726bf02` (ACCEPTED — empirical routing study)
> **Repo:** dabiggestpoppa/larger-lab | branch: `capital-routing`
> **Last updated:** 2026-08-15
> **Scope:** Translate holdout-validated Phase 6 routing relationships into executable
> pair-space expressions and baseline strategies. STOP after baseline evaluation.
> No CEREBUS filters, no deployment, no MT5 execution.

---

## 1. Frozen Relationship Families (from Phase 6 VALIDATED candidates)

| Family | Relationship | Validated horizons | Direction (trade expression) |
|---|---|---|---|
| A | EUR ACCUMULATION → JPY relative WEAKNESS | 6h, 8h, 12h | LONG JPY crosses (JPY weakens): long EURJPY / USDJPY / GBPJPY / CHFJPY |
| B | EUR LIQUIDATION → JPY relative STRENGTH | 4h, 6h, 8h, 12h | SHORT JPY crosses (JPY strengthens): short EURJPY / USDJPY / GBPJPY / CHFJPY |
| C | JPY LIQUIDATION → CHF relative STRENGTH | ~48h | CHF strong: long CHFJPY; short USDCHF / EURCHF / GBPCHF |

Sign conventions verified empirically from Phase 6 pair returns (e.g., EUR liq → USDJPY/GBPJPY/CHFJPY fall,
EUR acc → JPY crosses rise, JPY liq → CHFJPY rises at 48h while EURCHF/GBPCHF/USDCHF fall).

**Hard constraints:**
- Do NOT reopen Phase 5 thresholds. Do NOT discover new routing relationships.
- Adjacent validated horizons from same origin/destination/direction = ONE relationship family.
- Do NOT treat adjacent validated horizons as independent alphas.

## 2. Research Gate vs Alpha Promotion Gate

- Phase 6 `phase_6_gate.json` stays as **RESEARCH_GATE** (untouched).
- New **ALPHA_PROMOTION_GATE** (`P7_ALPHA_PROMOTION_GATE.json`) requires ALL:
  1. same holdout sign as development
  2. holdout effect >= 50% of development effect
  3. holdout bootstrap CI excludes zero
  4. adequate holdout N (>= 100)
  5. no material collapse under overlap cooldowns (6h/12h/24h)
  6. no dependence on one exact horizon (family-level clustering; plateaus, not isolated peaks)

## 3. Execution Studies

- **Pair-space translation** (`P7_PAIR_SPACE_COMPARISON.csv`): for each family, evaluate
  EURJPY, USDJPY, GBPJPY, CHFJPY (A/B) and CHFJPY, USDCHF, EURCHF, GBPCHF (C) +
  equal-risk JPY basket. Metrics: mean/median return, MFE, MAE, win prob, spread/commission,
  **RoutingEfficiency = E[MFE] / (E[MAE] + transaction cost)**.
- **Entry delay study** (`P7_ENTRY_DELAY_SURFACE.csv`): delays 0/1/2/3/4h × holds 4/6/8/12h
  (EUR→JPY). Look for stable plateaus, not isolated optima.
- **Excursion geometry** (`P7_EXCURSION_GEOMETRY.csv`): MAE/MFE p50/p75/p90/p95, time-to-MFE,
  time-to-MAE. No stop-loss optimization yet.
- **Mirrored EUR routing model**: long (A) vs short (B) evaluated separately; report whether
  symmetry actually holds (effect size, timing, MFE, MAE, cost-adjusted expectancy).

## 4. Baseline Strategy Test (no CEREBUS filters)

Event-driven baseline: entry at frozen delay, fixed holding-period exit, fixed
volatility-normalized risk. Metrics per baseline CSV:
trades, win rate, expectancy, profit factor, Sharpe, Sortino, max drawdown, Calmar,
MFE/MAE, turnover, cost drag, yearly results. No Kelly, no pyramiding, no parameter rescue.

- `P7_EUR_JPY_BASELINE_RESULTS.csv` (Families A+B, 4-12h holds)
- `P7_JPY_CHF_BASELINE_RESULTS.csv` (Family C, 24/36/48/60/72h holds, incl. swap/carry + spread)

## 5. Validation Discipline (brief §8)

- Phase 6 holdout is EVIDENCE only — never used to optimize Phase 7 parameters.
- Execution-rule selection uses **nested chronological development within the existing dev
  period** (dev 2023-07-01..2025-06-30): inner-sel 2023-07..2024-12, inner-val 2025-01..2025-06.
- Final validation on the **untouched latest period** (Phase 6 holdout 2025-07..2026-05) ONCE,
  after rules frozen. Labeled accordingly.
- Walk-forward/purged fallback noted if no untouched period exists (not needed here).

## 6. Outputs (artifacts/phase_07/)

- PHASE_7_PLAN.md, P7_ALPHA_PROMOTION_GATE.json, P7_RELATIONSHIP_FAMILIES.json
- P7_PAIR_SPACE_COMPARISON.csv, P7_ENTRY_DELAY_SURFACE.csv, P7_EXCURSION_GEOMETRY.csv
- P7_EUR_JPY_BASELINE_RESULTS.csv, P7_JPY_CHF_BASELINE_RESULTS.csv
- PHASE_7_STRATEGY_STUDY.md, PHASE_7_DECISION.json

## 7. Tests

`tests/test_phase_7_translation.py` — delay/hold window indexing, causal entry (no look-ahead),
cost application (spread + swap), basket weights, routing-efficiency formula, nested split
assignment, holdout untouched during selection, plateau detection, symmetry handling,
determinism (fixed seeds).

## 8. Batches

1. Batch 1 — plan + families freeze + alpha promotion gate
2. Batch 2 — execution engine (pair/delay/hold grid, costs, nested splits)
3. Batch 3 — pair-space, entry-delay surface, excursion geometry, mirrored symmetry
4. Batch 4 — baseline engines (EUR→JPY, JPY→CHF) + yearly metrics
5. Batch 5 — tests + full run + determinism
6. Batch 6 — commit CR-P7-ROUTING-TRANSLATION-01 + report back

## 9. Commit message (if clean)

CR-P7-ROUTING-TRANSLATION-01: translate validated routing relationships into pair-space baselines
