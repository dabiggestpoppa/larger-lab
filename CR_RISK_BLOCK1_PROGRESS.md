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
| `CR-RISK-R3-PROFIT-ANATOMY` | R3: MFE distributions, time-to-MFE, giveback, remaining expectancy | ⏳ Blocked on R2 review |
| `CR-RISK-R4-STATIC-FRONTIER` | R4: fixed-fractional ladder, DD probability map, ruin defs, full-press envelopes | ⏳ |
| `CR-RISK-BLOCK1-FOUNDATION-SEAL` | Master report + RM-S0..S4 profile library | ⏳ |

`block_2_cleared = false` until human review after the Block-I seal. No R5-R9, Kelly, hybrid sizing,
deploy, or MT5.

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
