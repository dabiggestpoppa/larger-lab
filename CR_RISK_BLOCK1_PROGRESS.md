# CR-RISK-BLOCK1 — RISK-ENGINEERING FOUNDATION (Progress)

> **Repo:** dabiggestpoppa/larger-lab · branch `capital-routing`
> **Frozen alpha base:** `7bc1c024` (P7.5 seal) · Phase-8 negative overlay: `95fb6f20`
> **Block:** R1 Exposure Truth → R2 Loss Anatomy → R3 Profit Anatomy → R4 Static Frontier → Block-I Seal
> **Last updated:** 2026-08-15

## Mission

Build the first complete risk-engineering foundation for the sealed EUR→JPY routing strategy.
Output of Block I is a **map, not a single answer**: expose the full risk surface (conservative
through full-press) so the user can deliberately choose a risk-return regime. Alpha is immutable.

## Cadence (per brief)

| Commit | Scope | Status |
|--------|-------|--------|
| `CR-RISK-R1-EXPOSURE-TRUTH` | R1: event-risk ledger, concurrency map, portfolio heat, episode clustering | ✅ Complete (`32374cc0`) |
| `CR-RISK-R1.1-EPISODE-METRIC-REPAIR` | R1.1: fix multi_event_share (was 1.0 everywhere) | ✅ Complete (`413a05fe`) — R1_CONCLUSIONS_UNCHANGED |
| `CR-RISK-R2-LOSS-ANATOMY` | R2: winner/loser MAE, failure speed, recovery surface, tail attribution | ✅ Complete — 248/248 tests |
| `CR-RISK-R3-PROFIT-ANATOMY` | R3: MFE distributions, time-to-MFE, giveback, remaining expectancy | ✅ Complete — 267/267 tests |
| `CR-RISK-R3.1-TIME-TO-PROFIT-METRIC-REPAIR` | R3.1: fix share_of_winners > 1.0 in R3_TIME_TO_PROFIT | ✅ Complete — R3_CONCLUSIONS_UNCHANGED |
| `CR-RISK-R4-STATIC-FRONTIER` | R4: fixed-fractional ladder, DD probability map, ruin defs, full-press envelopes | ✅ Complete — 286/286 tests |
| `CR-RISK-BLOCK1-FOUNDATION-SEAL` | Master report + RM-S0..S4 profile library | ⏳ (R4 stop condition — awaits human review) |

`block_2_cleared = false` until human review after the Block-I seal. No R5-R9, Kelly, hybrid sizing,
deploy, or MT5.

## R4 — Static Risk Frontier ✅ COMPLETE

**Commit:** `CR-RISK-R4-STATIC-FRONTIER` (pushed) · Tests: 15 new (`tests/test_risk_r4.py`) · **286/286 repo-wide** (207 main + 23 R1 + 18 R2 + 23 R3 + 15 R4) · deterministic (byte-identical) · inputs hash-frozen (`R4_INPUT_HASH_MANIFEST.json`)

### The map (research ladder, NOT recommendations)

| f% | CAGR | max DD | Calmar | worst day | P(DD>=20%) | P(DD>=40%) | P(tech) |
|---|---|---|---|---|---|---|---|
| 0.25 | +31% | 2.6% | 11.8 | -1.4% | 0% | 0% | 0 |
| 0.50 | +71% | 5.2% | 13.7 | -2.8% | 0% | 0% | 0 |
| 1.00 | +190% | 10.2% | 18.7 | -5.6% | 0% | 0% | 0 |
| 2.00 | +711% | 19.7% | 36.0 | -10.9% | 1% | 0% | 0 |
| 3.00 | +2080% | 28.7% | 72.5 | -16.1% | 4% | 0.1% | 0 |
| 5.00 | +13950% | 44.6% | 313 | -25.8% | 12% | 1.4% | 0 |

(Historical max DD is the peak-to-trough of the overlap-exact hourly equity path; ruin/DD probabilities are 10k-path chronological block bootstrap. `block1_static_risk_complete = true`, `block_2_cleared = false`.)

### Key findings

- **Risk-unit truth (Q1):** f maps DIRECTLY into equity — a -3R trade at f=1% costs ~-3%. 1R = 24.49 bps is the expected-move unit, NOT a stop; A worst -3.66R, B worst -3.31R. Historical max DD is **near-linear in f** (7.6-10.5% per 1% f); the nonlinearity lives in the **tail**: block-bootstrap p95 max DD at f=5% is 59.4% vs 44.6% historical.
- **Overlap-exact hourly compounding** preserves real overlap (max 3 concurrent): worst day at f=1% is -5.6% (vs -3.7% sequential) — overlap is a real cost driver on the downside. Sequential CAGR tracks hourly within 5% up to f=1.5%.
- **Ruin map (block bootstrap):** P(DD>=40%) stays under 1% up to f=2%; at f=5% it is 1.4% and P(DD>=50%) 0.3%; technical ruin = 0 across the whole ladder (the edge dominates resampled sequences).
- **Edge degradation:** at f=1%, expected CAGR falls 190% -> 75% -> 5% -> -37% as edge drops 100/75/50/25%; p95 max DD balloons 15% -> 20% -> 43% -> 83%. **The strategy is not viable below ~50% of its historical edge at any static fraction.**
- **Tail stress:** amplifying the worst 5% of losses 2x raises max DD 10.2% -> 16.0% at f=1%; inserting a 5-trade p99-loss cluster raises it to 17.6% (terminal 20.8x -> 17.9x).
- **Loss streaks:** 10 median-loser streak at f=1% = 6.3% DD (13-streak 8.1%, 15-streak 9.2%); at f=5% a 10-streak of median losers = 27.2% DD.
- **Family:** B is the capital-limiting family at every f (higher solo max DD at every fraction: e.g. f=1% A 10.3% vs B 11.1%; f=5% A 43.4% vs B 45.7%).
- **Heat:** 3-position overlap exists only 20h (0.1% of in-market time); gross R max 2.39R at 3 positions (heat decays 10x sqrt(rem)). Worst portfolio CAE 3.06R -> at f=1% that is a -3.1% account event.
- **Zones (data-driven, block-bootstrap; the frontier is steep):** RM-S0 f=1.5% (CAGR 392%, p95 DD 22%), RM-S1 f=3.0% (2080%, 40%), RM-S2/S3/S4 all collapse to f=5.0% (P(DD>=30%) 5.4% and P(DD>=40%) 1.4% at 5% - the edge is so strong that even 5% per event stays inside every full-press band). Reported as-is per the brief; no 'best size' selected.
- **Envelopes:** SURVIVAL (P50DD<=5%) allows 5% at 100%/75% edge and 1.5% at 50% edge; PROP (P10DD<=5%) allows 1.5%/1.0%/0.3% at 100/75/50% edge.

### Bugs caught during R4 build

- `worst_cluster_pct` returned 0 everywhere (init `max(-inf, ...)` locked 0 once a positive cluster iterated first) — now `min(...)`; worst 12h-cluster at f=1% is -6.0%.
- `worst_seq_pct` measured min-absolute-equity below start instead of peak-to-trough DD (equity never dips below 1.0 after trade 2) — now relative max DD (10.0% at f=1%, matching the hourly 10.2%).

### STOP condition

`block1_static_risk_complete = true` — but **Block II (compounding families, allocation, episode sizing, heat management, DD-adaptive, Kelly, hybrid) does NOT start** until human review. No 'best size' selected; no alpha, entry, exit, or trade-management change.

## R3.1 — Time-to-Profit Metric Repair ✅ COMPLETE

**Commit:** `CR-RISK-R3.1-TIME-TO-PROFIT-METRIC-REPAIR` · **Defect:** `share_of_winners`
was `N_reached_all / N_winners` (all reaching trades over the winners population) → values
>1.0 (e.g. **1.1544** pooled at +0.25R). **Fix:** separate `N_reached_all` /
`N_winners_reached` / `N_losers_reached` with own-population denominators; winner-only /
loser-only first-passage timing added; timestamps untouched. Corrected pooled shares:
+0.25R → 72.2% all / **96.6% winners** / 31.5% losers; +0.5R → 62.5% / 90.1% / 16.2%;
+1R → 34.4% / 54.9% / 0%. Verdict: **R3_CONCLUSIONS_UNCHANGED** (the corrected reading
strengthens the same story: ~90% of winners deliver +0.5R by median 2h; +1R is a minority
with 0% failure). 4 regression tests added (shares in [0,1], numerator populations,
N reconciliation pooled=A+B, timestamps unchanged); unaffected R3 artifacts verified
byte-identical. Also carried a commit fixup: `phase_r2_common.first_passage_positive` /
`time_to_mfe` (R3 prerequisites) were never staged by the R3 commit (first `git add`
failed on a pathspec and aborted the whole stage) — now committed.
`r3_repair_pass = true` · `r4_static_frontier_cleared = true` → proceed to R4.

## R3 — Profit Anatomy ✅ COMPLETE

**Commit:** `CR-RISK-R3-PROFIT-ANATOMY` (pushed) · Tests: 19 new (`tests/test_risk_r3.py`) · **267/267 repo-wide** (207 main + 23 R1 + 18 R2 + 19 R3) · deterministic (byte-identical) · inputs hash-frozen (`R3_INPUT_HASH_MANIFEST.json`)

### Key findings

- **Winner MFE is large and late:** winners' median MFE **+1.07R** (p90 +2.15R); losers' median +0.03R (half of losers still touch +0.5R and then fail). Winners peak at median **hour 5** (p75 6); losers peak at hour 2 — the strategy's winners are late-delivery, losers are early-impulse.
- **Time to first profit:** +0.25R median 2h, +0.5R median 2h (p75 3h), +1R median 3h (p75 4h). After reaching +1R, **0% finish negative** (n=306); after +0.5R, 9.7% finish negative; after +0.25R, 16.3%.
- **Capture/giveback:** winners retain a median **92%** of peak MFE (p25 64%, p75 100%; 65% keep ≥75%); winners give back a median 0.086R (8% of peak). Giveback by MFE hour: hour-1 peaks give back 1.04R (losers masquerading as early winners); hour-6 peaks give back 0.00R.
- **Remaining expectancy:** N-weighted remaining at 1/2/3/4/5h = **+0.29 / +0.11 / +0.04 / +0.03 / +0.00R**. Deep states at any age: at −0.75R or worse, remaining expectancy is negative by hour 2 (−0.24R) — matches the R2 cliff. States above +1R keep +0.25..+0.42R of remaining edge.
- **Delivery curve:** by hour 3, **69%** of total final PnL is on the book; by hour 4, 88%; by hour 6, 92% (hour 6 is the frozen exit; 48 truncated events cap the ratio below 1). ~40% of winners are past their MFE by hour 5.
- **Maturity classes (quantile-declared):** LATE_DELIVERY n=303, win 98.3%, +1.42R — the core money-maker; NOT_YET_DELIVERED n=247, win 7.7%, −0.95R — the core loser; PEAKED_AND_GIVING_BACK n=141, win 61.7%, +0.06R — capital parked near breakeven after early peaks; EARLY_DELIVERY n=42, −0.10R (early peaks don't persist).
- **Family:** A and B deliver similarly in size (median MFE 0.73 vs 0.70R, capture 91% vs 94%), but **B needs patience**: 42% of B's winner PnL arrives after hour 3 vs A −13% (A winners are already past their peak at hour 3).
- **Concurrency:** no-overlap expectancy +0.41R vs same-direction overlap +0.28R, opposite +0.35R — overlap mildly dilutes profit quality (consistent with R2's downside finding).
- **Episode ranks (12h):** profit delivery is rank-flat — time to MFE 4h across ranks, capture 88–96%. Later ranks deliver as cleanly as the first; R2's tail-risk skew is not accompanied by slower/uglier profit delivery.
- **Winner tails:** best 1% → 5.5% of positive PnL; best 5% → 17%; best 10% → 28%. Excluding the best 5% leaves expectancy **+0.20R** (vs +0.35R full) — the alpha is not a tiny-winner-tail artifact.
- **Temporal:** stable — median MFE 0.74/0.65/0.69R, capture 90/96/96%, winner-tail5 share 17.5/17.7/17.9% across sel/val/OOS.

### Bugs caught during R3 build

- **Delivery-curve denominator inflation (6×):** `final_net_R` is repeated once per path bar, so the long-frame sum inflated the %-of-final denominator; the exit bar read 0.156 instead of ~0.92. Fixed by deduplicating per event; locked by a regression test (exit-bar ratio must equal finals-weighted full-window share).
- Report/decision Q12 selected the N=28 share row instead of the N=845 ex-best-5% row (NaN expectancy); fixed by selecting on the non-null exclusion value.

### HYPOTHESIS_ONLY (no execution change)

1. Late-hold capital efficiency: by hour 5, 88% of final PnL is earned with only +0.03R remaining — a profit-lock/time-decay concept.
2. +1R trades never finish negative (n=306) — a partial/breakeven-lock concept after strong delivery.
3. Winners give back a median 8% of peak — a trailing/exit-smoothing concept (needs R4 risk context).

`r4_static_frontier_cleared = true` — but **R4 does NOT start until human review** (per brief's FINAL STOP). No TP, early exit, trailing, breakeven, partial, family weighting, sizing, or alpha modification.

## R2 — Loss Anatomy ✅ COMPLETE

**Commit:** `CR-RISK-R2-LOSS-ANATOMY` (pushed) · Tests: 18 new (`tests/test_risk_r2.py`) · 248/248 repo-wide · deterministic (byte-identical) · inputs hash-frozen (`R2_INPUT_HASH_MANIFEST.json`)

### Key findings

- **Winner/loser MAE separation is stark:** winners' median MAE −0.09R (95% never go below −0.57R); losers' median −0.88R. Worst winner MAE ≈ −0.59R → **MAE ≤ −1R ⇒ 0% recovery** (134 trades breached, none recovered).
- **Failure speed:** losers breach −0.5R by median 2h, −1R by 3h (p75 4h); 40% of losers reach −1R. Classes: FAST (reveal ≤2h, n=158, median loss −0.86R) are worse than SLOW (n=103, −0.32R) — 11% of FAST recover after −0.5R breach, 0% of SLOW.
- **Recovery surface:** MAE ∈ [−0.75,−1.00)R → ~2–5% recovery at any age; MAE ∈ [−0.5,−0.75)R → 30–43% (age-dependent); remaining expectancy turns negative below −0.75R by 2–3h. Broad cliff zone = HYPOTHESIS_ONLY.
- **Tails:** worst 1% (9 trades) carry 10% of total losses (100% FAST failures); worst 10% carry 60% of losses and **92% of the historical max drawdown**; worst 1% = 45% of worst-24h loss.
- **Concurrency:** entry with 0 existing: +0.38R, P(<-1R) 11%; entry with 2+: +0.25R, P(<-1R) 6% (n=16, small). Same-direction overlap raises P(<-1R) to 16% vs 9% no-overlap.
- **Episode ranks (12h):** later ranks carry mildly higher downside — P(<-1R) 11% → 17% rank 4+; p95 loss −1.7R → −2.2R. Independence holds on expectancy, weakens on tails.
- **Family:** B has worse median MAE (−0.26R vs −0.22R) and P(<-1R) (14% vs 10%); A has the worst extreme (−3.66R vs −3.31R).
- **Temporal:** stable — median MAE −0.22/−0.20/−0.28R, P(<-1R) 14%/9%/11%, tail5 share 38/42/34% across sel/val/OOS.
- **Streaks:** max 10 consecutive losing trades (block-bootstrap p95: 11, max 13); max 6 negative days; worst 24h window −153 bps.

### M5 note

The committed M5 feed differs from the frozen H1 panel (p95 |diff| 22 bps — different feed). R2 refuses to mix it: paths are hourly from the frozen H1 panel only; the brief's 30m/60m age sub-bins are structurally unavailable and documented as such. 15-min failure-speed resolution is a Phase-9+ option with a reconciled feed.

## R1.1 — Episode-metric repair ✅ COMPLETE

**Commit:** `CR-RISK-R1.1-EPISODE-METRIC-REPAIR` · **Root cause:** `_decision()` computed
`sum(n_events)/n_total` = 1.0 for every interval (clusters partition all events), instead of
the documented metric. **Fix:** canonical `multi_event_share()` = share of raw events in
≥2-event clusters; used by the decision builder; definition recorded in the JSON.
Corrected values: 0.5h **0.0** · 1h **0.0** · 2h **14.5%** · 3h **23.9%** · 6h **52.9%** · 12h **71.5%**
(match the report/CSV narrative exactly). 4 regression tests added (≤1h = 0 by construction;
6h/12h reproduce artifacts; decision JSON cannot silently emit all-1.0).
Verdict: **R1_CONCLUSIONS_UNCHANGED** — the field was display-only; ledger, returns, 1R,
concurrency, heat, and clustering memberships untouched. (Note: 3h rank-2 already showed a
−4.4 bps dip in the R1 conditional table — unchanged by this repair.) → proceed to R2.

## R1 — Exposure Truth & Portfolio Heat ✅ COMPLETE

**Commit:** `32374cc0` (`CR-RISK-R1-EXPOSURE-TRUTH`) — pushed to GitHub (`45149ee1..32374cc0`), synced to `Desktop\projects\larger-lab` · Tests: 19 new (`tests/test_risk_r1.py`) · 226/226 repo-wide · deterministic (byte-identical re-run) · inputs hash-frozen (`R1_INPUT_HASH_MANIFEST.json`)

### Key findings

- **Unit reconciliation:** 1R = 10×√6 = **24.4949 bps** (one-sigma hold move of the vol-normalized position). A: +9.63 bps = **+0.393R** (win 0.639, worst −3.66R) · B: +7.54 bps = **+0.308R** (win 0.614, worst −3.31R). Entry/exit prices reproduce frozen grid returns to float tolerance (tested).
- **Concurrency:** max **3** simultaneous positions (never 4+); 565h with 2, 20h with 3; in-market 4,735h (18.9%). Opposite-direction (A long vs B short) overlap 228h; same-direction 367h (A+A 156, B+B 211). Max gross exposure 18.2 vol-normalized units.
- **Portfolio heat:** each open position commits 24.49 bps at entry, decaying 10×√rem. Gross heat in-market: median 20, p90 32.4, p99 44.5, max 58.6 bps. Portfolio CAE max 74.9 bps; max unrealized +187 bps.
- **Episodes:** events are ≥1h apart by construction (no clusters at ≤1h). At 6h/12h intervals 53%/71% of events sit in multi-event clusters (max size 5/10), but conditional expectancy is **flat across within-cluster rank** (12h: 8.6 / 8.4 / 7.5 / 10.1 bps) → clustered events behave **independent, not duplicated**. No size change made.

### R1 batches

1. ✅ Orient: sealed trades (890), grids, frozen H1 panel, M5, module conventions
2. ✅ R1.1 event-risk ledger — unit mapping (market → pos → PnL → R → account %) + prices
3. ✅ R1.2 concurrency map + R1.3 portfolio heat (gross/net, rolling distributions)
4. ✅ R1.4 routing episode clustering + conditional 1st/2nd/3rd expectancy
5. ✅ Orchestrator + runner: input hashes, 11 outputs, report, decision
6. ✅ Tests + full suite + determinism
7. ✅ Commit `CR-RISK-R1-EXPOSURE-TRUTH`, push, sync, report — STOP for review

## R1 unit mapping (frozen definitions)

- market return: `mkt_bps = dir × (log P_exit − log P_entry) × 1e4`  (frozen Phase-7 window convention)
- position: `pos = TARGET_VOL / rv` (TARGET_VOL = 10 bps/h; clamped to 1.0 when rv missing)
- PnL: `pnl_bps = mkt_bps × pos`;  net: `net_bps = pnl_bps − cost_bps × pos`
- **1R = TARGET_VOL × √hold** = 24.4949 bps (one-sigma move over the hold for the vol-normalized position)
- `r_multiple = net_bps / 1R`;  `account_return_pct = r_multiple × RISK_PER_R_PCT` (1.0% per R reference)

## Principles

- Risk measured at **portfolio level** (open positions, overlaps, gross/net, clusters, CAE) — never `risk_per_trade` alone.
- **Ruin defined explicitly** per event (DD ≥ 10/20/30/40/50%, loss ≥ 50/75%, technical ruin) — R4.
- Aggressive models allowed; no rejection for large max DD; report the full distribution.
- No optimization by headline return; evaluate CAGR, DD percentiles, recovery, positive-month/year rates, ES, ruin probs.
