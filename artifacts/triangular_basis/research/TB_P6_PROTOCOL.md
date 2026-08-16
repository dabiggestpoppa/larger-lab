# TB-P6 — ENTRY ANATOMY PROTOCOL (PRE-REGISTERED)

**Phase:** TB-P6-ENTRY-ANATOMY-01 — ENTRY RESEARCH ONLY.
**Base commit:** `7868a67d624931d3afc56910de8b805510eabcc7` (TB-P5 accepted: TB-A VALIDATED control, TB-B STRONG, TB-C 2.5/5/7.5/10% STRONG, `optimization_cleared = true`, forward OOS pending).
**Status of this document:** written and committed BEFORE any P6.1 outcome is viewed. The split, grid, metrics, plateau rule, candidate gates, and multiple-testing controls below are fixed; they are not adjusted after seeing results.

## 0. Scope

Study ENTRY QUALITY only. Everything else is frozen (triangular identity, basis construction, rolling normalization, neutralization logic, TB-A/B/C model definitions, exit target z=0, stop z=6, max hold = London session end, hard exit 12:00 EST, cost methodology = flat 10.2 pips round-trip, lot-translation methodology, causal weighting). No exit/hold/stop/pyramiding/scaling/risk sizing work. No new instruments. No CEREBUS/P90/rekey.

Frozen entry reference: z = 2.5, London session 3–12 EST (UTC−5), minimum 120 minutes to session end, direction SHORT when z > 0 else LONG.

## 1. Models

- **TB-A** — canonical inverse-ATR control (reported for reference only; never used to choose neutral parameters).
- **TB-B** — exact-neutral (eps = 0) three-leg basket.
- **TB-C-2.5% / 5% / 7.5% / 10%** — constrained-neutral baskets.
- Primary optimization target: **TB-B**. Secondary: TB-C variants (2.5% and 5% are the practical pair).

Weights are computed exactly as in TB-P5 (`project_basket(q_alpha, E, eps)` on entry-time closes + entry-time ATR shares + frozen seal rates; hard residual guard enforced; PnL = `basket_pnl − 10.2` pips).

## 2. Data + integrity gates (fail-closed)

Same frozen feed as TB-P5: `load_research_pairs()` (GBPAUD/GBPNZD/AUDNZD research M5, inner-joined, OHLC). Gates asserted before any analysis:

1. synchronized series ≡ `bar_parity.csv` (max close diff < 1e-9),
2. bar count ≈ 265,809,
3. causal re-simulation at z = 2.5 reproduces the canonical 405-trade log **exactly** (entry/exit times, direction, result, z-scores, sizes, PnL to 1e-9),
4. TB-B per-trade PnL at z = 2.5 equals the TB-P5 per-trade weights CSV (independent cross-check of the two implementations).

If any gate fails, the run stops (no partial outputs used).

## 3. Entry-threshold grid (P6.1) — predeclared, not extended

z ∈ {1.50, 1.75, 2.00, 2.25, **2.50**, 2.75, 3.00, 3.25, 3.50, 3.75, 4.00}. If frequency collapses above a threshold we REPORT that, we do not chase with a finer/extended grid.

Per (threshold × model): N trades, coverage vs z=2.5 baseline (same model), win rate, EV/trade, PF, net pips, median trade, avg win, avg loss, payoff ratio, max DD, Sharpe, Sortino, MFE, MAE, time-to-MFE, time-to-MAE, median convergence time (TP trades), failure rate (non-TP share), transaction-cost share of gross edge (= costs / (net+costs)).

## 4. Chronological protocol (PRE-REGISTERED) — applies to every threshold's own trade set

Trades sorted by entry time; each threshold's trade set is split by **count**:

| Block | Share | Purpose |
|---|---|---|
| DISCOVERY | earliest 60% | hypothesis generation (never select from holdout) |
| CONFIRMATION | next 20% (60–80%) | same-direction check |
| HOLDOUT | latest 20% | frozen test; probed once per threshold |

Secondary frozen check where sample permits: the TB-P5 date holdout (exit ≥ 2025-07-01, 94 baseline trades) — the same trade-set condition is applied to candidate thresholds' own trades.

A candidate threshold's EV is compared against the same model's z=2.5 EV computed on the baseline's own trades in the corresponding block. No repeated probing of the holdout.

## 5. Plateau rule (P6.1)

For each neutral model, scan the 11-point grid for contiguous runs of ≥ 3 thresholds where EV spread within the run ≤ 15% of the run max AND run max EV ≥ baseline (z=2.5) EV. Report: broad plateaus, cliffs (adjacent drop > 40% from a local peak), monotonic regions, saturation point (first threshold beyond which EV stops improving by > 10%). A plateau member must also be chronologically stable: EV > 0 in ≥ 4 of 5 calendar years and no year with N ≥ 10 has PF ≤ 1.

## 6. Multiple-testing control

Per model family (10 threshold-vs-baseline EV-uplift tests): two-sample bootstrap 95% CI on ΔEV (seeded), BH-FDR q-values, minimum support N ≥ 30. Promote only cells with q < 0.10, CI excluding 0, and coverage ≥ 25% (band below = exploratory unless exceptional + stable).

## 7. P6.2 further-extension anatomy (measurement only)

For every baseline (z=2.5) trade: z-at-first-signal, max further extension of |z| after entry, time to max extension, whether |z| reached {2.75, 3.00, 3.25, 3.50, 4.00, 4.50, 5.00, 6.00}, eventual outcome (TP/SL/TIMEOUT), per-model PnL (TB-A, TB-B, TB-C-5%), MFE/MAE, convergence time. Estimates:

- P(convergence | max |z| bin) and E[PnL | max |z| bin] — bins aligned to the level grid,
- P(convergence | current z bucket, time-since-entry bucket) — hazard-style 2D surface (coarse bins).

Path classes (empirical, descriptive): IMMEDIATE_CONVERGENCE (no material extension, TP), SHALLOW/DEEP × CONVERGED/FAILED with extension < 1.0 z / ≥ 1.0 z. Hypotheses A (extension → higher expectancy), B (inverted-U with structural failure zone), C (extreme extension = regime break → eventual veto potential), D (differs by vol regime / session timing) are each tested quantitatively and reported — none is assumed true, none becomes a rule.

## 8. P6.3 session clock

Baseline trades conditioned by: entry EST hour, 30-min bucket, minutes since London start, early/mid/late thirds, proximity to 5 EST (Tokyo overlap) / 8 EST (NY open) within ±30 min. Spread is NOT available in the frozen OHLC feed — recorded as NA; realized 5-min basis vol used as the liquidity-adjacent state variable.

## 9. P6.4 dislocation-quality fingerprint (causal)

Per baseline trade, entry-time features: |z|, basis velocity (1/3/5-bar), acceleration, duration above threshold, threshold touches in prior 20 bars, time since prior signal, 5-min basis realized vol, leg ATRs + relative vol, causal expanding vol tercile (quantiles of prior trades only), leg contribution to the entry-bar and 5-bar basis change (primary/secondary leg, dominance = max|c|/Σ|c|, dispersion), session third, weekday, month. No future information enters any feature (tested deterministically). Quality conditionals on coarse bins of velocity / persistence / vol / dominance / session / weekday.

## 10. Cost stress + execution translation

- **Cost stress:** every threshold × model re-evaluated at 1.0 / 1.25 / 1.5 / 2.0 / 2.5 / 3.0 × modeled costs; break-even multiplier interpolated to EV = 0. Candidate must not derive its edge from a selected cheaper-cost era (no cost-era selection is performed at all).
- **Execution translation:** TB-B and TB-C-5% at every threshold, notionals $5k/$10k/$25k/$50k/$100k: executable residual (median), weight distortion (median), rejection rate, PnL ratio vs theoretical model (median). Same broker math as TB-P5 (0.01 lot step, 0.01 min lot, contract 100k, seal USD conversion).

## 11. Candidate gates (A/B classification) — sealed before outcomes

For every (neutral model, threshold ≠ 2.5):

1. full-sample EV uplift vs baseline (same model) with bootstrap CI excluding 0 and q < 0.10,
2. same-direction EV uplift in DISCOVERY, CONFIRMATION, and HOLDOUT (min support N ≥ 20 per block),
3. P5 date holdout agrees (where sample permits, N ≥ 20),
4. threshold lies on a plateau for its model (or within 15% of plateau max EV),
5. coverage band ≥ 25% (band ≥ 40% for anything above EXPLORATORY),
6. break-even cost multiplier ≥ 1.5×,
7. uplift survives dropping top-5% |PnL| trades (per-model),
8. basis reversion share of gross PnL ≥ 60% for the candidate set,
9. candidate does not depend on a handful of trades (top-5% independence, #7).

Grades: **A STRONG** (all gates) / **B CONDITIONAL** (promising, ≥ 4 gates incl. 1–3) / **C EXPLORATORY** (uplift but low N or unstable blocks) / **D REJECT** (no robust benefit). A/B candidates reported with hypothesis, model, parameter range, N, coverage, EV uplift, PF change, MAE change, DD change, convergence-time change, cost survival, chronological stability, lot impact.

## 12. Decision

`p7_convergence_optimization_cleared = true` only if ≥ 1 entry modification grades A or B AND preserves basis-reversion attribution AND remains executable. Otherwise `false`, retain z = 2.5.

## 13. Deterministic tests

`tb_p6_tests.py`: integrity gates (1–4 above), N monotone non-increasing in threshold, coverage(2.5) = 100%, weight causality (exit-price perturbation leaves weights bit-identical; entry-price perturbation changes them), residual caps for every basket, attribution identity (basis + rotation + cost = PnL to 1e-6) per model, extension-surface structural invariants, fingerprint future-bar invariance, cost-stress monotonicity, determinism (two runs hash-identical), surface-table completeness (11 × 6 rows).

## 14. Git cadence + human gate

Four phase commits (`TB-P6.1-ENTRY-THRESHOLD-SURFACE`, `TB-P6.2-FURTHER-EXTENSION-ANATOMY`, `TB-P6.3-SESSION-TIMING`, `TB-P6.4-DISLOCATION-QUALITY`) then the final seal `TB-P6-ENTRY-ANATOMY-SEAL` on branch `tb-research-verify-04a`. No push, no P7 work before human review. Reproduction: `python quant-lab/engines/tb_p6_anatomy.py --phase all` + `python quant-lab/engines/tb_p6_tests.py`.
