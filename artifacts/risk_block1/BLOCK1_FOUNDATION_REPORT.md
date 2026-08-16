# CR-RISK-BLOCK1-FOUNDATION — SEAL REPORT

## 1. Executive summary

Block I mapped the sealed EUR->JPY capital-routing strategy (890 events, A 432 /
B 458, 2023-07 -> 2026-05) from exposure truth through static risk frontiers.
The edge is abnormally strong per unit of risk: 0.35R expected per event, winners
retain 92% of peak MFE, and even f=5% keeps P(DD>=40%) at ~1.4% under 10k-path
block bootstrap. The binding constraints are (a) edge retention (below ~50% of
historical edge the strategy stops compounding) and (b) real overlap on the
downside (worst day -5.6% at f=1% vs -3.7% sequential). No best size is selected;
Block II sizing/allocation research remains locked.

## 2. Risk-unit truth

1R = 24.4949 bps (TARGET_VOL x sqrt(hold)) - an expected-move unit, NOT a stop.
account_return ~= trade_return_R x f. Historical extremes: A worst -3.66R, B worst
-3.31R. See BLOCK1_RISK_UNIT_LOCK.md.

## 3. Exposure truth

Max 3 concurrent positions; 2-position overlap 565h, 3-position 20h; opposing
overlap 228h is NOT riskless (gross heat up to ~1.9R during opposing overlap).
Worst portfolio CAE 3.06R = -3.1% account at f=1%. Overlap-exact hourly paths are
authoritative (R4) because overlap materially worsens worst-day risk.

## 4. Loss anatomy

Winners' median MAE -0.09R (95% above -0.57R); losers' median -0.88R. Zero
recovery after -1R (observation). Losers breach -0.5R by 2h, -1R by 3h; FAST
failures are the deep ones. Worst 10% of trades carry ~60% of losses / ~92% of
max DD. B is worse on typical downside; A holds the deepest single trade.

## 5. Profit anatomy

Winners' median MFE +1.07R, peak at hour 5; ~70% of final PnL earned by hour 3,
88% by hour 4. Winners retain 92% of peak; +1R reached by 54.9% of winners with
0% failure. LATE_DELIVERY is the money-maker; NOT_YET_DELIVERED the core loser.
Winner tail is not dominant (best 5% = 17% of positive PnL).

## 6. Static risk frontier

See BLOCK1_STATIC_FRONTIER.csv (R4 landmarks preserved exactly). Historical max
DD is near-linear in f (7.6-10.5% per 1% f); resampled p95 DD accelerates at
high f (59.4% at f=5%).

## 7. Edge degradation

f=1% expected CAGR: 190% -> 75% -> 5% -> -37% as edge falls 100/75/50/25%;
p95 DD: 15% -> 20% -> 43% -> 83%. Classification: EDGE-FULL/ROBUST/FRAGILE/BROKEN.
Edge retention is the binding constraint.

## 8. Tail / streak stress

Worst-5% amplification 2x raises max DD 10.2% -> 16.0% at f=1%; p99-loss cluster
-> 17.6%. 10-streak of median losers = 6.3% DD at f=1% (27.2% at f=5%).
Historical / resampled / synthetic paths are kept distinct.

## 9. Family risk

B is capital-limiting under static equal-f risk at every tested f (higher solo
max DD). Descriptive result only.

## 10. RM-S0..S4 profile library

Non-overlapping bands derived from historical-max-DD breakpoints (<=5/10/20/30/>30%):
- **RM-S0 PRESERVATION** f 0.05-0.40%
- **RM-S1 CONSERVATIVE** f 0.50-0.75%
- **RM-S2 BALANCED** f 1.00-2.00%
- **RM-S3 GROWTH** f 2.50-3.00%
- **RM-S4 FULL-PRESS RESEARCH** f 4.00-5.00% (RESEARCH ONLY)

See BLOCK1_RM_PROFILE_LIBRARY.md/.csv.

## 11. Account / prop translation

See BLOCK1_ACCOUNT_TRANSLATION.csv and BLOCK1_PROP_CONSTRAINT_MAP.csv. No prop
size recommended without a defined constraint.

## 12. Known vs hypothesis vs unknown

See BLOCK1_EVIDENCE_STATUS_MATRIX.csv. Frontier/overlap/edge-degradation/family
results VALIDATED; stop/exit concepts HYPOTHESIS_ONLY; dynamic sizing, Kelly,
family allocation NOT TESTED.

## 13. Practical trader interpretation

- **f=0.5%**: ~71% CAGR historically, 5.2% max DD, worst day -2.8%. 1R = $50 on
  $10k; a -3R trade costs -$150.
- **f=1%**: ~190% CAGR, 10.2% max DD, worst day -5.6%; 1R = $100 on $10k; -3R =
  -$300; A-worst -3.66R = -$366.
- **A -3R trade at any f costs ~3 x f of the account.**
- **2-3 overlapping positions** commit 2-3 x f gross; worst portfolio CAE at
  f=1% is -3.1% of the account.
- **Expected DD**: ~10% historical at f=1% vs p95 ~15% under tail resampling.
- **f=5% is not "safe"** even though technical ruin was zero in the tested
  historical-resampling framework: p95 resampled DD is 59.4%, P(DD>=10%) 31%,
  P(DD>=50%) 0.3%, and a 15-streak of median losers costs 39%.
- **Edge degradation matters more than headline CAGR**: at 50% edge f=1% is a
  5% CAGR with 43% p95 DD.
- **Static sizing is the foundation, not the engine**: it ignores family
  quality, episodes, heat, and drawdown state - those are Block II.

## 14. Block-II research queue

See BLOCK2_RESEARCH_QUEUE.md (R5 family allocation -> R6 episode/heat sizing ->
R7 DD-adaptive -> R8 Kelly -> R9 hybrid). None authorized by this seal.

## 15. Explicit stop condition

`block1_foundation_sealed = true`, `block_2_cleared = false`. No R5-R9, no Kelly,
no dynamic/family/cluster/DD sizing, no deployment, no MT5 until human review.
