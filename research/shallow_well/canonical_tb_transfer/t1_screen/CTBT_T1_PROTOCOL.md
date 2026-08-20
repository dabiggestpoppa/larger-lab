# CTBT T1 PROTOCOL

## SW-CTBT-T1-CANONICAL-TB-TRANSFER-MECHANISM-SCREEN

### Purpose

Determine whether the canonical AUD_GBP_NZD TB mechanism transfers to four structurally similar FX triangles.

### Reference

AUD_GBP_NZD

### Challengers

1. EUR_GBP_JPY
2. CHF_GBP_JPY
3. EUR_GBP_USD
4. GBP_NZD_USD

### Frozen Contract Parameters

| Parameter | Value |
|---|---|
| Rolling Z lookback | 200 bars (causal, population std, current excluded) |
| Entry Z control | 2.5 |
| Entry Z primary | 3.0 |
| Exit family | E1 (signed overshoot ±0.25) |
| Stop | z6 structural invalidation (6.0) |
| Weight | W2 exact-neutral |
| Session | London (03:00-12:00 EST) |
| Hard exit | 12:00 EST (noon) |
| Min time to exit | 120 minutes |
| Concurrency | 1 active basket per candidate |
| Reentry | Deterministic after close, no cooldown |

### Cost Model

| Leg | Spread (pips) | Commission (pips) | Total (pips) |
|---|---|---|---|
| GBPAUD | 1.5 | 0.7 | 2.2 |
| GBPNZD | 2.5 | 0.7 | 3.2 |
| AUDNZD | 2.0 | 0.7 | 2.7 |
| **Canonical basket RT** | | | **16.2** |

| Leg | Spread | Commission | Total |
|---|---|---|---|
| EURGBP | 1.0 | 0.5 | 1.5 |
| EURJPY | 1.0 | 0.5 | 1.5 |
| GBPJPY | 1.5 | 0.6 | 2.1 |
| **C1 basket RT** | | | **10.2** |

| Leg | Spread | Commission | Total |
|---|---|---|---|
| GBPCHF | 1.5 | 0.6 | 2.1 |
| GBPJPY | 1.5 | 0.6 | 2.1 |
| CHFJPY | 1.5 | 0.6 | 2.1 |
| **C2 basket RT** | | | **12.6** |

| Leg | Spread | Commission | Total |
|---|---|---|---|
| EURGBP | 1.0 | 0.5 | 1.5 |
| EURUSD | 0.8 | 0.4 | 1.2 |
| GBPUSD | 1.0 | 0.5 | 1.5 |
| **C3 basket RT** | | | **8.4** |

| Leg | Spread | Commission | Total |
|---|---|---|---|
| GBPNZD | 2.5 | 0.7 | 3.2 |
| GBPUSD | 1.0 | 0.5 | 1.5 |
| NZDUSD | 1.2 | 0.5 | 1.7 |
| **C4 basket RT** | | | **12.8** |

### Data Windows

| Triangle | Window | Source |
|---|---|---|
| AUD_GBP_NZD | 2020-01-01 to 2024-12-31 | _fetched.csv (283K bars) |
| EUR_GBP_JPY | 2020-01-01 to 2024-12-31 | _fetched.csv (345K bars) |
| CHF_GBP_JPY | 2020-01-01 to 2024-12-31 | _fetched.csv (345K bars) |
| EUR_GBP_USD | 2023-01-01 to 2024-12-31 | EURGBP fetched + EURUSD M5 + GBPUSD fetched (144K bars) |
| GBP_NZD_USD | 2020-01-01 to 2024-12-31 | _fetched.csv (177K bars) |

Note: EUR_GBP_USD uses a shorter window because EURUSD PRO data only covers 2023-2025.

### Basis Formulas

All bases follow the canonical orientation for alphabetically sorted currencies A < B < C:
basis = +ln(A/B) - ln(A/C) + ln(B/C)

| Triangle | Basis |
|---|---|
| AUD_GBP_NZD | +ln(GBPAUD) - ln(GBPNZD) + ln(AUDNZD) |
| EUR_GBP_JPY | +ln(EURGBP) - ln(EURJPY) + ln(GBPJPY) |
| CHF_GBP_JPY | +ln(GBPCHF) + ln(GBPJPY) - ln(CHFJPY) |
| EUR_GBP_USD | +ln(EURGBP) - ln(EURUSD) + ln(GBPUSD) |
| GBP_NZD_USD | +ln(GBPNZD) - ln(GBPUSD) + ln(NZDUSD) |

### Hard Pass Gate (z3.0 primary)

A. net EV > 0 after executable cost
B. PF_net >= 1.20
C. completed_events >= 50
D. gross-edge / cost ratio >= 1.50
E. break-even cost multiple >= 1.50
F. no single year > 60% of total net PnL
G. at least 3 calendar years net positive (where sample permits)
H. z3 mechanism quality not materially worse than z2.5
I. no obvious rollover/spread artifact
J. no data/microstructure invalidation

### Monotonicity Test

delta_EV, delta_PF, delta_tail, delta_cost_ratio between z3.0 and z2.5.
Classification: MONOTONIC_STRONG, MONOTONIC_ACCEPTABLE, NON_MONOTONIC, MECHANISM_COLLAPSE.
Advancement requires MONOTONIC_STRONG or MONOTONIC_ACCEPTABLE.
