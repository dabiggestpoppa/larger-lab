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
| `CR-RISK-R1-EXPOSURE-TRUTH` | R1: event-risk ledger, concurrency map, portfolio heat, episode clustering | ✅ Complete — 226/226 tests |
| `CR-RISK-R2-LOSS-ANATOMY` | R2: winner/loser MAE, failure speed, recovery surface, tail attribution | ⏳ Blocked on R1 review |
| `CR-RISK-R3-PROFIT-ANATOMY` | R3: MFE distributions, time-to-MFE, giveback, remaining expectancy | ⏳ |
| `CR-RISK-R4-STATIC-FRONTIER` | R4: fixed-fractional ladder, DD probability map, ruin defs, full-press envelopes | ⏳ |
| `CR-RISK-BLOCK1-FOUNDATION-SEAL` | Master report + RM-S0..S4 profile library | ⏳ |

`block_2_cleared = false` until human review after the Block-I seal. No R5-R9, Kelly, hybrid sizing,
deploy, or MT5.

## R1 — Exposure Truth & Portfolio Heat ✅ COMPLETE

**Commit:** `CR-RISK-R1-EXPOSURE-TRUTH` (pushed) · Tests: 19 new (`tests/test_risk_r1.py`) · 226/226 repo-wide · deterministic (byte-identical re-run) · inputs hash-frozen (`R1_INPUT_HASH_MANIFEST.json`)

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
