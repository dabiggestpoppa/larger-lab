# R1 — Exposure Truth & Portfolio Heat (CR-RISK-BLOCK1)

**Task:** CR-RISK-BLOCK1-R1-EXPOSURE-TRUTH · **Base:** 7bc1c024 (sealed baseline) · Phase-8 overlay preserved as negative result (95fb6f20)

## 1. Unit reconciliation (R1.1)

```
market_return_bps: dir * (log P_exit - log P_entry) * 1e4
position_unit: pos = TARGET_VOL / rv   (TARGET_VOL = 10 bps/h; clamp >= 1.0 when rv missing)
pnl_bps: mkt_bps * pos
net_pnl_bps: pnl_bps - cost_bps * pos   (cost = 2*one_way spread+comm + signed swap)
risk_unit_1R_bps: TARGET_VOL * sqrt(hold_h)  = 10 * sqrt(6) = 24.4949 for hold=6h
r_multiple: net_pnl_bps / risk_unit_bps
account_return_pct: r_multiple * RISK_PER_R_PCT   (RISK_PER_R_PCT = 1.0 reference)
  mkt_bps: basis points of price (pair return)
  pos: unitless vol-normalized notional
  pnl_bps: basis points of notional per vol-normalized position
  1R: basis points of PnL (one-sigma hold move)
  account_return: percent of account equity (at reference 1% per R)
parameters: {'TARGET_VOL': 10.0, 'RISK_PER_R_PCT': 1.0, 'pair': 'USDJPY'}
```

- **1R = TARGET_VOL × √hold = 10 × √6 = 24.4949 bps** of PnL for the vol-normalized position — a one-sigma move over the full hold.
- `r_multiple = net_pnl_bps / 1R`; `account_return_pct = r_multiple × 1.0%` (reference 1% per R; the account-leverage parameter is swept in R4).
- Entry/exit prices are read from the frozen H1 panel with the exact Phase-7 window convention; `price_return_bps` reproduces the grid's `gross_return_bps` to float tolerance (unit-tested).

## 2. Ledger

- Events: **890** (A: 432, B: 458) · splits: {'inner_sel': 461, 'RELATIONSHIP_CONFIRMED_OOS': 280, 'inner_val': 149}
- Family A: expectancy +9.633 bps = +0.393R · win 0.639 · median R +0.405 · worst R -3.655 · best R +7.283
- Family B: expectancy +7.539 bps = +0.308R · win 0.614 · median R +0.357 · worst R -3.313 · best R +6.383

## 3. Concurrency (R1.2)

- Max concurrent positions: **3** · mean (in-market) 1.13 · median 1 · p90 2 · p99 2
- In-market hours: 4735 of 25112 (18.9%)
- Hours with 2 positions: 565 · 3: 20 · 4+: 0
- Overlap hours — same-direction: 367 · opposite-direction: 228 · A+A: 156 · B+B: 211 · A+B: 228
- Exposure — max gross 18.19 · max |net| 18.19 · gross p90 1.15 · gross p99 4.04
- Opposite positions do NOT cancel economically; gross and net are tracked separately.

## 4. Portfolio heat (R1.3)

- Heat = aggregate live account-risk commitment. Each open position commits `10×√rem` bps (24.49 bps at entry), decaying to zero at exit.
- gross heat (all_hours): median 0.0 · p75 0.0 · p90 20.0 · p95 22.4 · p99 37.3 · max 58.6 bps
- gross heat (in_market): median 20.0 · p75 24.5 · p90 32.4 · p95 38.6 · p99 44.5 · max 58.6 bps
- |net heat| (all hours): median 0.0 · p90 17.3 · p99 32.4 bps
- portfolio CAE (all hours): median 0.0 · p90 0.0 · p95 5.5 · p99 23.2 bps
- Rolling 1/3/6/12/24h heat distributions in R1_HEAT_DISTRIBUTIONS.csv.

## 5. Routing episode clustering (R1.4)

- interval 0.5h: 890 clusters · 890 singletons · events in multi clusters 0 (0.0%) · max cluster size 1
- interval 1h: 890 clusters · 890 singletons · events in multi clusters 0 (0.0%) · max cluster size 1
- interval 2h: 824 clusters · 761 singletons · events in multi clusters 129 (14.5%) · max cluster size 3
- interval 3h: 775 clusters · 677 singletons · events in multi clusters 213 (23.9%) · max cluster size 4
- interval 6h: 614 clusters · 419 singletons · events in multi clusters 471 (52.9%) · max cluster size 5
- interval 12h: 482 clusters · 254 singletons · events in multi clusters 636 (71.5%) · max cluster size 10

### Conditional expectancy by within-cluster rank

| interval | rank | N | mean bps | win | vs rank1 |
|---|---|---|---|---|---|
| 0.5h | 1 | 890 | +8.56 | 0.626 |  |
| 1h | 1 | 890 | +8.56 | 0.626 |  |
| 2h | 1 | 824 | +8.61 | 0.626 |  |
| 2h | 2 | 63 | +8.07 | 0.619 | -0.55 |
| 2h | 3 | 3 | +2.82 | 0.667 | -5.79 |
| 3h | 1 | 775 | +8.92 | 0.627 |  |
| 3h | 2 | 98 | +4.56 | 0.602 | -4.36 |
| 3h | 3 | 16 | +15.08 | 0.688 | +6.16 |
| 3h | 4+ | 1 | +9.84 | 1.000 | +0.91 |
| 6h | 1 | 614 | +9.14 | 0.635 |  |
| 6h | 2 | 195 | +7.00 | 0.585 | -2.14 |
| 6h | 3 | 64 | +7.74 | 0.656 | -1.40 |
| 6h | 4+ | 17 | +8.37 | 0.647 | -0.77 |
| 12h | 1 | 482 | +8.61 | 0.631 |  |
| 12h | 2 | 228 | +8.35 | 0.610 | -0.25 |
| 12h | 3 | 96 | +7.46 | 0.594 | -1.14 |
| 12h | 4+ | 84 | +10.06 | 0.679 | +1.46 |

### Independence vs duplication verdict

- **0.5h:** later ranks consistent with rank 1 (or too small to judge) (rank-1 expectancy +8.56 bps)
- **1.0h:** later ranks consistent with rank 1 (or too small to judge) (rank-1 expectancy +8.56 bps)
- **2.0h:** later ranks consistent with rank 1 (or too small to judge) (rank-1 expectancy +8.61 bps)
- **3.0h:** later ranks differ materially (rank-1 expectancy +8.92 bps)
- **6.0h:** later ranks consistent with rank 1 (or too small to judge) (rank-1 expectancy +9.14 bps)
- **12.0h:** later ranks consistent with rank 1 (or too small to judge) (rank-1 expectancy +8.61 bps)

## 6. Checkpoint answers

- **Unit reconciliation:** ledger reproduces the sealed baseline (A 9.633 / B 7.539 bps vol-normalized expectancy across dev+OOS) and adds R-multiples on the explicit 24.49 bps 1R unit.
- **Max concurrency:** 3 simultaneous positions; median in-market 1.
- **Portfolio heat:** median gross heat 0.0 bps, p99 37.3 bps; portfolio CAE p99 23.2 bps.
- **Clustered events:** see §5 verdicts — whether clustered signals are independent or duplicated is a descriptive finding feeding R4 episode risk and Block-II models; no sizing change made.

## 7. Inputs frozen

- `P7_5_TRADES.csv` (sealed P0 book): ad19e08f16aeb65c…
- `routing_events.parquet` (Phase 5 frozen): de08df601a008e0e… (matches seal)
- `h1_strict_common_panel.parquet` (Phase 3 frozen): a0da64a3b0cd8976… (matches seal)
- Deterministic: greedy clustering, no random sampling; byte-identical outputs tested.

## 8. STOP

R1 checkpoint complete. R2 (Loss Anatomy) does NOT start until human review of this evidence. No stops, no filters, no sizing change, no alpha modification.